package com.sentrytop;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.logging.Logger;
import java.util.logging.Level;

public class EngineMain {
    private static final Logger logger = Logger.getLogger(EngineMain.class.getName());
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final ExecutorService vThreads = Executors.newVirtualThreadPerTaskExecutor();

    public static void main(String[] args) {
        setupLogging();
        
        Config config = loadConfig();
        Map<String, IntelEntry> intelDb = loadIntelDb(config.intelDbPath);
        ThreatAnalyzer analyzer = new ThreatAnalyzer(intelDb, config);

        System.out.println("SentryTop v1.0.0 | Engine ACTIVE | Mode: Standalone EDR");
        System.out.println("=========================================================");
        
        if ("root".equals(System.getProperty("user.name"))) {
            logger.warning("Engine is running as ROOT. This is not recommended for security.");
        }

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in))) {
            String line;
            while ((line = reader.readLine()) != null) {
                final String payload = line;
                vThreads.submit(() -> analyzer.analyze(payload));
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Fatal error in Engine main loop", e);
        } finally {
            vThreads.shutdown();
            try {
                if (!vThreads.awaitTermination(5, TimeUnit.SECONDS)) {
                    vThreads.shutdownNow();
                }
            } catch (InterruptedException e) {
                vThreads.shutdownNow();
            }
        }
    }

    private static void startMetricsMonitor(ThreatAnalyzer analyzer) {
        vThreads.submit(() -> {
            while (true) {
                try {
                    Thread.sleep(60000);
                    long events = analyzer.getProcessedEvents();
                    long alerts = analyzer.getAlertsTriggered();
                    int connections = analyzer.getSeenConnectionsCount();
                    long mem = (Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / 1024 / 1024;
                    
                    logger.info(String.format(
                        "METRICS: [Events: %d] [Alerts: %d] [Active Conn: %d] [Memory: %dMB]",
                        events, alerts, connections, mem
                    ));
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
    }

    private static Config loadConfig() {
        try {
            File file = findFile("assets/config.json");
            return mapper.readValue(file, Config.class);
        } catch (Exception e) {
            logger.warning("Could not load config.json, using defaults.");
            Config config = new Config();
            config.pollingIntervalMs = 1000;
            config.intelDbPath = "assets/intel_db.json";
            config.rateLimit = 5;
            config.suspiciousPorts = List.of(4444, 1337);
            return config;
        }
    }

    private static Map<String, IntelEntry> loadIntelDb(String path) {
        Map<String, IntelEntry> db = new HashMap<>();
        try {
            File file = findFile(path);
            List<IntelEntry> entries = mapper.readValue(file, mapper.getTypeFactory().constructCollectionType(List.class, IntelEntry.class));
            for (IntelEntry entry : entries) {
                db.put(entry.ip, entry);
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Could not load intel DB from " + path, e);
        }
        return db;
    }

    private static File findFile(String path) {
        File file = new File(path);
        if (!file.exists()) file = new File("../" + path);
        return file;
    }

    private static void setupLogging() {
        System.setProperty("java.util.logging.SimpleFormatter.format",
                "[%1$tF %1$tT] [%4$-7s] %5$s %n");
    }
}
