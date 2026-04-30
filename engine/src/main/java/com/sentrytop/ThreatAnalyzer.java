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
    private final Map<String, IntelEntry> intelDb;
    private final Config config;
    private final Set<String> seenConnections = ConcurrentHashMap.newKeySet();
    private final Map<String, AtomicInteger> alertCounts = new ConcurrentHashMap<>();

    private final AtomicLong processedEvents = new AtomicLong(0);
    private final AtomicLong alertsTriggered = new AtomicLong(0);

    private final BehavioralAnalyzer behavioralAnalyzer = new BehavioralAnalyzer();

    public ThreatAnalyzer(Map<String, IntelEntry> intelDb, Config config) {
        this.intelDb = intelDb;
        this.config = config;
    }

    public void analyze(String jsonPayload) {
        try {
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
                if (intelDb.containsKey(ip)) {
                    reportThreat(proc, ip, port, intelDb.get(ip));
                    suspicious = true;
                }
                
                if (config.suspiciousPorts.contains(port)) {
                    reportSuspiciousPort(proc, ip, port);
                    suspicious = true;
                }

                if (behavioralAnalyzer.isAnomaly(connectionId)) {
                    reportBeaconing(proc, ip, port);
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

    private String sanitize(String input) {
        return input.replaceAll("[^a-zA-Z0-9\\.\\-_/ \\(\\)\\[\\]\\:]", "");
    }

    private void reportThreat(String proc, String ip, int port, IntelEntry intel) {
        if (checkRateLimit(ip)) return;

        System.out.printf("\033[31m[CRIT]\033[0m Unauthorized Connection Detected!%n");
        System.out.printf("   └── Process  : %s%n", proc);
        System.out.printf("   └── Dest     : %s:%d [%s]%n", ip, port, IntelEnricher.getGeoInfo(ip));
        System.out.printf("   └── Category : %s (Confidence: %s)%n", intel.category, intel.confidence);
    }

    private void reportSuspiciousPort(String proc, String ip, int port) {
        if (checkRateLimit(ip)) return;

        System.out.printf("\033[33m[WARN]\033[0m Unusual Port Connection!%n");
        System.out.printf("   └── Process : %s%n", proc);
        System.out.printf("   └── Dest    : %s:%d [%s]%n", ip, port, IntelEnricher.getGeoInfo(ip));
    }

    private void reportBeaconing(String proc, String ip, int port) {
        if (checkRateLimit(ip + "_beacon")) return;

        System.out.printf("\033[35m[BEAC]\033[0m Potential Beaconing Detected!%n");
        System.out.printf("   └── Process : %s%n", proc);
        System.out.printf("   └── Dest    : %s:%d [%s]%n", ip, port, IntelEnricher.getGeoInfo(ip));
    }

    private boolean checkRateLimit(String key) {
        AtomicInteger count = alertCounts.computeIfAbsent(key, k -> new AtomicInteger(0));
        if (count.incrementAndGet() > config.rateLimit) {
            logger.warning("Rate limit exceeded for " + key + ". Suppressing further alerts.");
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
