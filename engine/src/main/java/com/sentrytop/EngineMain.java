package com.sentrytop;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

public class EngineMain {
    private static final Set<String> MOCK_INTEL_DB = Set.of("45.33.32.156", "185.199.108.153");
    // This set acts as the "memory" to stop the spam
    private static final Set<String> SEEN_CONNECTIONS = ConcurrentHashMap.newKeySet();
    private static final ExecutorService vThreads = Executors.newVirtualThreadPerTaskExecutor();

    public static void main(String[] args) {
        System.out.println("SentryTop v1.0 | Engine ACTIVE | Mode: Standalone EDR");
        System.out.println("=========================================================");
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in))) {
            String line;
            while ((line = reader.readLine()) != null) {
                final String payload = line;
                vThreads.submit(() -> analyze(payload));
            }
        } catch (Exception e) { e.printStackTrace(); }
    }

    private static void analyze(String payload) {
        String ip = extract(payload, "\"r_ip\": \"");
        String proc = extract(payload, "\"process\": \"");
        
        if (ip != null && proc != null) {
            String connectionId = proc + "->" + ip;
            
            // Only alert if this is the FIRST time we see this connection
            if (SEEN_CONNECTIONS.add(connectionId)) {
                if (MOCK_INTEL_DB.contains(ip)) {
                    System.out.printf("\033[31m[CRIT]\033[0m Unauthorized Connection Detected!%n");
                    System.out.printf("   └── Process : %s%n   └── Dest IP : %s%n", proc, ip);
                    System.out.printf("   └── Remediate: sudo iptables -A OUTPUT -d %s -j DROP%n", ip);
                } else {
                    System.out.printf("\033[32m[ OK ]\033[0m New connection: %s -> %s%n", proc, ip);
                }
            }
        }
    }

    private static String extract(String json, String key) {
        int start = json.indexOf(key);
        if (start == -1) return null;
        start += key.length();
        return json.substring(start, json.indexOf("\"", start));
    }
}
