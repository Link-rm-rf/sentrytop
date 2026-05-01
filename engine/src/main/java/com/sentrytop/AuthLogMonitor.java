package com.sentrytop;

import java.io.*;
import java.util.*;
import java.util.regex.*;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.logging.Logger;

/**
 * AuthLogMonitor: Monitors /var/log/auth.log for SSH brute force attempts.
 */
public class AuthLogMonitor {
    private static final Logger logger = Logger.getLogger(AuthLogMonitor.class.getName());
    private static final String AUTH_LOG = "/var/log/auth.log";
    private static final int THRESHOLD = 5;
    private static final long WINDOW_SECONDS = 300; // 5 minutes

    private final Map<String, Integer> reportedIps = new HashMap<>();
    private long lastOffset = 0;
    private long lastRunTime = 0;

    public AuthLogMonitor() {
        File logFile = findLogFile();
        if (logFile != null) {
            lastOffset = logFile.length();
        }
    }

    public void check() {
        long now = System.currentTimeMillis();
        // Only run every 60 seconds
        if (now - lastRunTime < 60000) return;
        lastRunTime = now;

        try {
            detectBruteForce();
        } catch (Exception e) {
            logger.warning("Error in AuthLogMonitor: " + e.getMessage());
        }
    }

    private File findLogFile() {
        File logFile = new File(AUTH_LOG);
        if (logFile.exists()) return logFile;
        logFile = new File("/var/log/secure");
        if (logFile.exists()) return logFile;
        return null;
    }

    private void detectBruteForce() {
        File logFile = findLogFile();
        if (logFile == null) return;

        if (logFile.length() < lastOffset) {
            lastOffset = 0;
        }

        long nowSeconds = Instant.now().getEpochSecond();
        Map<String, Integer> failedAttempts = new HashMap<>();

        try (RandomAccessFile raf = new RandomAccessFile(logFile, "r")) {
            raf.seek(lastOffset);
            String line;
            while ((line = raf.readLine()) != null) {
                if (line.contains("Failed password")) {
                    long logTime = parseLogTime(line);
                    if (nowSeconds - logTime < WINDOW_SECONDS) {
                        String ip = extractIp(line);
                        if (ip != null) {
                            failedAttempts.put(ip, failedAttempts.getOrDefault(ip, 0) + 1);
                        }
                    }
                }
            }
            lastOffset = raf.getFilePointer();
        } catch (IOException e) {
            logger.warning("Could not read auth log: " + e.getMessage());
        }

        for (Map.Entry<String, Integer> entry : failedAttempts.entrySet()) {
            String ip = entry.getKey();
            int count = entry.getValue();
            if (count >= THRESHOLD) {
                if (!reportedIps.containsKey(ip) || reportedIps.get(ip) < count) {
                    reportBruteForce(ip, count);
                    reportedIps.put(ip, count);
                }
            }
        }
    }

    private long parseLogTime(String line) {
        try {
            if (line.length() < 15) return Instant.now().getEpochSecond();
            String datePart = line.substring(0, 15);
            int year = LocalDate.now().getYear();
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MMM d HH:mm:ss").withLocale(Locale.ENGLISH);
            LocalDateTime ldt = LocalDateTime.parse(datePart, formatter).withYear(year);
            return ldt.toEpochSecond(ZoneOffset.UTC);
        } catch (Exception e) {
            return Instant.now().getEpochSecond();
        }
    }

    private String extractIp(String line) {
        // Simple split instead of regex: ... from 1.2.3.4 port ...
        int fromIdx = line.indexOf(" from ");
        if (fromIdx == -1) return null;
        String rest = line.substring(fromIdx + 6);
        int spaceIdx = rest.indexOf(" ");
        if (spaceIdx == -1) return rest;
        return rest.substring(0, spaceIdx);
    }

    private void reportBruteForce(String ip, int count) {
        System.out.printf("\033[31m[CRIT]\033[0m SSH Brute Force Detected!%n");
        System.out.printf("   └── Source IP : %s%n", ip);
        System.out.printf("   └── Attempts  : %d (last 5 mins)%n", count);
        System.out.printf("   └── Target    : SSH Service (Port 22)%n");

        writeToFifo("SSH_BRUTE_FORCE", "sshd", ip, 22, "CRITICAL", count + " attempts in last 5 mins");
    }

    private void writeToFifo(String type, String proc, String ip, int port, String threat, String info) {
        try {
            Map<String, Object> alert = new HashMap<>();
            alert.put("timestamp", java.time.Instant.now().toString());
            alert.put("type", type);
            alert.put("pid", -1); // sshd parent pid is complex, keep -1 for now
            alert.put("process", proc);
            alert.put("source_ip", ip);
            alert.put("port", port);
            alert.put("threat", threat);
            alert.put("info", info);

            com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            String json = mapper.writeValueAsString(alert) + "\n";
            
            String path = "/opt/sentrytop/alerts.fifo";
            java.io.File fifo = new java.io.File(path);
            if (!fifo.exists()) {
                fifo = new java.io.File("alerts.fifo");
            }

            if (fifo.exists()) {
                try (java.io.FileOutputStream fos = new java.io.FileOutputStream(fifo, true)) {
                    fos.write(json.getBytes());
                }
            }
        } catch (Exception e) {
            // Failure to write to FIFO should not crash engine
        }
    }
}
