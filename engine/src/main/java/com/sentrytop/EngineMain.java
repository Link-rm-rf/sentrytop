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

    public static void main(String[] args) {
        setupLogging();
        
        Config config = loadConfig();
        IntelDb intelDb = loadIntelDb(config.intelDbPath);
        ThreatAnalyzer analyzer = new ThreatAnalyzer(intelDb, config);
        AuthLogMonitor authMonitor = new AuthLogMonitor();

        System.out.println("SentryTop v1.0.0 | Engine ACTIVE | Mode: Standalone EDR");
        System.out.println("=========================================================");
        
        if ("root".equals(System.getProperty("user.name"))) {
            logger.warning("Engine is running as ROOT. This is not recommended for security.");
        }

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in))) {
            String line;
            while ((line = reader.readLine()) != null) {
                analyzer.analyze(line);
                authMonitor.check();
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Fatal error in Engine main loop", e);
        }
    }

    private static Config loadConfig() {
        Config config = new Config();
        config.pollingIntervalMs = 1000;
        config.intelDbPath = "assets/intel_db.json";
        config.rateLimit = 5;
        config.suspiciousPorts = List.of(4444, 1337);

        try {
            File file = findFile("assets/config.json");
            if (file.exists()) {
                return mapper.readValue(file, Config.class);
            } else {
                logger.warning("config.json not found at " + file.getAbsolutePath() + ", using defaults.");
            }
        } catch (Exception e) {
            logger.warning("Error loading config.json: " + e.getMessage() + ". Using defaults.");
        }
        return config;
    }

    private static IntelDb loadIntelDb(String path) {
        try {
            File file = findFile(path);
            if (file.exists()) {
                IntelDb db = mapper.readValue(file, IntelDb.class);
                int ipCount = db.maliciousIps != null ? db.maliciousIps.size() : 0;
                int domainCount = db.malwareDomains != null ? db.malwareDomains.size() : 0;
                logger.info("Loaded " + ipCount + " IPs and " + domainCount + " domains from " + file.getAbsolutePath());
                return db;
            } else {
                logger.severe("Intel DB not found at " + file.getAbsolutePath());
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Could not load intel DB: " + e.getMessage(), e);
        }
        return new IntelDb();
    }

    private static File findFile(String path) {
        // Try CWD
        File file = new File(path);
        if (file.exists()) return file;

        // Try relative to JAR location if possible, or just check parent
        String root = System.getProperty("user.dir");
        file = new File(root, path);
        if (file.exists()) return file;

        // Fallback for /opt installation
        file = new File("/opt/sentrytop", path);
        if (file.exists()) return file;

        // Last resort fallback
        return new File(path);
    }

    private static void setupLogging() {
        System.setProperty("java.util.logging.SimpleFormatter.format",
                "[%1$tF %1$tT] [%4$-7s] %5$s %n");
    }
}
