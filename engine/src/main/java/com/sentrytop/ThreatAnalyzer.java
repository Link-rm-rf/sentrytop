package com.sentrytop;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.Logger;
import java.util.logging.Level;

/**
 * ThreatAnalyzer: The core correlation engine of SentryTop.
 * 
 * Logic:
 * 1. Parses JSON telemetry into structured events.
 * 2. Deduplicates connections to minimize redundant alerting.
 * 3. Evaluates events against Threat Intel (Static Match), Suspicious Ports (Policy), 
 *    and Behavioral Patterns (Anomaly Detection).
 * 4. Implements rate limiting per-IP to prevent log flooding during active attacks.
 */
public class ThreatAnalyzer {
    private static final Logger logger = Logger.getLogger(ThreatAnalyzer.class.getName());
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final IntelDb intelDb;
    private final Config config;
    private final Set<String> seenConnections = ConcurrentHashMap.newKeySet();
    private final Map<String, AtomicInteger> alertCounts = new ConcurrentHashMap<>();
    private long lastCleanupTime = System.currentTimeMillis();

    private final AtomicLong processedEvents = new AtomicLong(0);
    private final AtomicLong alertsTriggered = new AtomicLong(0);

    private final BehavioralAnalyzer behavioralAnalyzer = new BehavioralAnalyzer();

    public ThreatAnalyzer(IntelDb intelDb, Config config) {
        this.intelDb = intelDb;
        this.config = config;
    }

    public void analyze(String jsonPayload) {
        // Periodic cleanup of seen connections (every 1 hour)
        long now = System.currentTimeMillis();
        if (now - lastCleanupTime > 3600000) {
            seenConnections.clear();
            lastCleanupTime = now;
        }

        try {
            processedEvents.incrementAndGet();
            JsonNode root = objectMapper.readTree(jsonPayload);
            String ip = root.path("r_ip").asText(null);
            int port = root.path("r_port").asInt(0);
            String proc = root.path("process").asText(null);

            if (ip == null || proc == null) return;

            ip = sanitize(ip);
            proc = sanitize(proc);

            String connectionId = proc + "->" + ip + ":" + port;

            if (seenConnections.add(connectionId)) {
                boolean suspicious = false;
                if (intelDb.maliciousIps != null && intelDb.maliciousIps.containsKey(ip)) {
                    reportThreat(proc, ip, port, intelDb.maliciousIps.get(ip));
                    suspicious = true;
                }
                
                List<Integer> suspPorts = intelDb.suspiciousPorts != null ? intelDb.suspiciousPorts : config.suspiciousPorts;
                if (suspPorts.contains(port)) {
                    reportSuspiciousPort(proc, ip, port);
                    suspicious = true;
                }

                if (behavioralAnalyzer.isAnomaly(connectionId)) {
                    reportBeaconing(proc, ip, port);
                    suspicious = true;
                }

                // New: Reverse Shell Detection
                if (isShell(proc) && isSuspiciousShellParent(proc)) {
                    reportReverseShell(proc, ip, port);
                    suspicious = true;
                }

                // New: Suspicious Process Spawning
                if (isSuspiciousTool(proc) && isSuspiciousToolParent(proc)) {
                    reportSuspiciousSpawning(proc, ip, port);
                    suspicious = true;
                }

                if (!suspicious) {
                    logger.info("New safe connection: " + connectionId + " [" + IntelEnricher.getGeoInfo(ip) + "]");
                }
            } else if (behavioralAnalyzer.isAnomaly(connectionId)) {
                reportBeaconing(proc, ip, port);
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error parsing telemetry", e);
        }
    }

    private boolean isShell(String proc) {
        String p = proc.toLowerCase();
        return p.startsWith("bash") || p.startsWith("sh") || p.startsWith("dash") || p.startsWith("zsh");
    }

    private boolean isSuspiciousShellParent(String proc) {
        // Example: bash [Parent: sshd(1234)]
        if (!proc.contains("[Parent: ")) return true; // No parent info is suspicious for a shell
        String parent = proc.substring(proc.indexOf("[Parent: ") + 9).toLowerCase();
        return !parent.contains("sshd") && !parent.contains("tmux") && 
               !parent.contains("screen") && !parent.contains("login") && !parent.contains("systemd");
    }

    private boolean isSuspiciousTool(String proc) {
        String p = proc.toLowerCase();
        return p.startsWith("curl") || p.startsWith("wget") || p.startsWith("nc") || p.startsWith("netcat");
    }

    private boolean isSuspiciousToolParent(String proc) {
        if (!proc.contains("[Parent: ")) return true;
        String parent = proc.substring(proc.indexOf("[Parent: ") + 9).toLowerCase();
        return !parent.contains("bash") && !parent.contains("sh") && 
               !parent.contains("cron") && !parent.contains("systemd");
    }

    private String sanitize(String input) {
        // Simple manual cleaning instead of regex
        StringBuilder sb = new StringBuilder();
        for (char c : input.toCharArray()) {
            if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || 
                c == '.' || c == '-' || c == '_' || c == '/' || c == ' ' || c == '(' || c == ')' || c == '[' || c == ']' || c == ':') {
                sb.append(c);
            }
        }
        return sb.toString();
    }

    private void reportThreat(String proc, String ip, int port, IntelDb.MaliciousIp intel) {
        if (checkRateLimit(ip)) return;
        alertsTriggered.incrementAndGet();

        System.out.printf("\033[31m[CRIT]\033[0m Unauthorized Connection Detected!%n");
        System.out.printf("   └── Process  : %s%n", proc);
        System.out.printf("   └── Dest     : %s:%d [%s]%n", ip, port, IntelEnricher.getGeoInfo(ip));
        System.out.printf("   └── Category : %s (Confidence: %s)%n", intel.threat, intel.confidence);
        System.out.printf("   └── Family   : %s%n", intel.family);

        writeToFifo("MALICIOUS_CONNECTION", proc, ip, port, "CRITICAL", intel.threat);
    }

    private void reportReverseShell(String proc, String ip, int port) {
        if (checkRateLimit(proc + "_revshell")) return;
        alertsTriggered.incrementAndGet();

        System.out.printf("\033[31m[CRIT]\033[0m Potential Reverse Shell Detected!%n");
        System.out.printf("   └── Process : %s%n", proc);
        System.out.printf("   └── Dest    : %s:%d [%s]%n", ip, port, IntelEnricher.getGeoInfo(ip));
        System.out.printf("   └── Risk    : CRITICAL (Non-standard Shell Parent)%n");

        writeToFifo("REVERSE_SHELL", proc, ip, port, "CRITICAL", "Non-standard Shell Parent");
    }

    private void reportSuspiciousSpawning(String proc, String ip, int port) {
        if (checkRateLimit(proc + "_spawn")) return;
        alertsTriggered.incrementAndGet();

        System.out.printf("\033[33m[WARN]\033[0m Suspicious Process Spawning!%n");
        System.out.printf("   └── Process : %s%n", proc);
        System.out.printf("   └── Dest    : %s:%d [%s]%n", ip, port, IntelEnricher.getGeoInfo(ip));
        System.out.printf("   └── Info    : Tool spawned by unexpected parent%n");

        writeToFifo("SUSPICIOUS_SPAWN", proc, ip, port, "WARN", "Tool spawned by unexpected parent");
    }

    private void reportSuspiciousPort(String proc, String ip, int port) {
        if (checkRateLimit(ip)) return;

        System.out.printf("\033[33m[WARN]\033[0m Unusual Port Connection!%n");
        System.out.printf("   └── Process : %s%n", proc);
        System.out.printf("   └── Dest    : %s:%d [%s]%n", ip, port, IntelEnricher.getGeoInfo(ip));

        writeToFifo("SUSPICIOUS_PORT", proc, ip, port, "WARN", "Unusual port");
    }

    private void reportBeaconing(String proc, String ip, int port) {
        if (checkRateLimit(ip + "_beacon")) return;

        System.out.printf("\033[35m[BEAC]\033[0m Potential Beaconing Detected!%n");
        System.out.printf("   └── Process : %s%n", proc);
        System.out.printf("   └── Dest    : %s:%d [%s]%n", ip, port, IntelEnricher.getGeoInfo(ip));

        writeToFifo("BEACONING", proc, ip, port, "ALERT", "Potential Beaconing");
    }

    private String getFifoPath() {
        String path = "/opt/sentrytop/alerts.fifo";
        java.io.File f = new java.io.File(path);
        if (!f.exists()) {
            // Try relative to CWD for testing
            path = "alerts.fifo";
        }
        return path;
    }

    private void writeToFifo(String type, String proc, String ip, int port, String threat, String info) {
        try {
            int pid = extractPid(proc);
            Map<String, Object> alert = new HashMap<>();
            alert.put("timestamp", java.time.Instant.now().toString());
            alert.put("type", type);
            alert.put("pid", pid);
            alert.put("process", proc);
            alert.put("source_ip", ip);
            alert.put("port", port);
            alert.put("threat", threat);
            alert.put("info", info);

            String json = objectMapper.writeValueAsString(alert) + "\n";
            java.io.File fifo = new java.io.File(getFifoPath());
            if (fifo.exists()) {
                try (java.io.FileOutputStream fos = new java.io.FileOutputStream(fifo, true)) {
                    fos.write(json.getBytes());
                }
            }
        } catch (Exception e) {
            // Failure to write to FIFO should not crash engine
        }
    }

    private int extractPid(String proc) {
        int lastParen = proc.lastIndexOf('(');
        int lastCloseParen = proc.lastIndexOf(')');
        if (lastParen != -1 && lastCloseParen != -1 && lastCloseParen > lastParen + 1) {
            try {
                return Integer.parseInt(proc.substring(lastParen + 1, lastCloseParen));
            } catch (NumberFormatException e) {
                return -1;
            }
        }
        return -1;
    }

    private boolean checkRateLimit(String key) {
        AtomicInteger count = alertCounts.computeIfAbsent(key, k -> new AtomicInteger(0));
        int currentCount = count.incrementAndGet();
        if (currentCount > config.rateLimit) {
            // Only log the warning exactly ONCE when the limit is hit
            if (currentCount == config.rateLimit + 1) {
                logger.warning("Rate limit exceeded for " + key + ". Suppressing further alerts.");
            }
            return true;
        }
        return false;
    }
    
    // For testing
    public boolean isSeen(String connectionId) {
        return seenConnections.contains(connectionId);
    }

    public long getProcessedEvents() { return processedEvents.get(); }
    public long getAlertsTriggered() { return alertsTriggered.get(); }
    public int getSeenConnectionsCount() { return seenConnections.size(); }
}
