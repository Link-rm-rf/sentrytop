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
        IntelEntry entry = new IntelEntry();
        entry.ip = "1.2.3.4";
        entry.category = "Test";
        entry.confidence = "high";
        
        ThreatAnalyzer analyzer = new ThreatAnalyzer(Map.of("1.2.3.4", entry), createMockConfig());
        analyzer.analyze("{\"r_ip\": \"1.2.3.4\", \"r_port\": 80, \"process\": \"malware\"}");
        assertTrue(analyzer.isSeen("malware->1.2.3.4:80"));
    }

    @Test
    public void testAnalyzeInvalidJson() {
        ThreatAnalyzer analyzer = new ThreatAnalyzer(new HashMap<>(), createMockConfig());
        analyzer.analyze("invalid json");
        assertFalse(analyzer.isSeen("malware->1.2.3.4:80"));
    }

    @Test
    public void testSanitization() {
        ThreatAnalyzer analyzer = new ThreatAnalyzer(new HashMap<>(), createMockConfig());
        analyzer.analyze("{\"r_ip\": \"1.2.3.4;\", \"r_port\": 80, \"process\": \"test$\"}");
        // Sanitizer strips non-allowed chars: ";" and "$"
        assertTrue(analyzer.isSeen("test->1.2.3.4:80"));
    }
}
