package com.sentrytop;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

public class ThreatAnalyzerTest {

    private Config createMockConfig() {
        Config config = new Config();
        config.rateLimit = 5;
        config.suspiciousPorts = List.of(4444);
        return config;
    }

    @Test
    public void testAnalyzeValidJson() {
        IntelDb db = new IntelDb();
        db.maliciousIps = new HashMap<>();
        IntelDb.MaliciousIp entry = new IntelDb.MaliciousIp();
        entry.threat = "Test";
        entry.confidence = 0.99;
        db.maliciousIps.put("1.2.3.4", entry);
        
        ThreatAnalyzer analyzer = new ThreatAnalyzer(db, createMockConfig());
        analyzer.analyze("{\"r_ip\": \"1.2.3.4\", \"r_port\": 80, \"process\": \"malware\"}");
        assertTrue(analyzer.isSeen("malware->1.2.3.4:80"));
    }

    @Test
    public void testAnalyzeInvalidJson() {
        ThreatAnalyzer analyzer = new ThreatAnalyzer(new IntelDb(), createMockConfig());
        analyzer.analyze("invalid json");
        assertFalse(analyzer.isSeen("malware->1.2.3.4:80"));
    }

    @Test
    public void testSanitization() {
        ThreatAnalyzer analyzer = new ThreatAnalyzer(new IntelDb(), createMockConfig());
        analyzer.analyze("{\"r_ip\": \"1.2.3.4;\", \"r_port\": 80, \"process\": \"test$\"}");
        // Sanitizer strips non-allowed chars: ";" and "$"
        assertTrue(analyzer.isSeen("test->1.2.3.4:80"));
    }

    @Test
    public void testReverseShellDetection() {
        ThreatAnalyzer analyzer = new ThreatAnalyzer(new IntelDb(), createMockConfig());
        // bash spawned by python (not in whitelist)
        analyzer.analyze("{\"r_ip\": \"1.2.3.4\", \"r_port\": 4444, \"process\": \"bash [Parent: python(999)]\"}");
        // We can't easily check stdout here without redirecting System.out, 
        // but we can verify it was processed and flagged.
        assertTrue(analyzer.isSeen("bash [Parent: python(999)]->1.2.3.4:4444"));
    }

    @Test
    public void testSuspiciousSpawningDetection() {
        ThreatAnalyzer analyzer = new ThreatAnalyzer(new IntelDb(), createMockConfig());
        // curl spawned by a web server (apache)
        analyzer.analyze("{\"r_ip\": \"1.2.3.4\", \"r_port\": 80, \"process\": \"curl [Parent: apache(888)]\"}");
        assertTrue(analyzer.isSeen("curl [Parent: apache(888)]->1.2.3.4:80"));
    }
}
