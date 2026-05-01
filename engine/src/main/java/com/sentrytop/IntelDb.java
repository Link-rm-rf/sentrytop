package com.sentrytop;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;
import java.util.List;

public class IntelDb {
    @JsonProperty("malicious_ips")
    public Map<String, MaliciousIp> maliciousIps;
    
    @JsonProperty("malware_domains")
    public Map<String, MalwareDomain> malwareDomains;
    
    @JsonProperty("suspicious_ports")
    public List<Integer> suspiciousPorts;
    
    @JsonProperty("last_updated")
    public String lastUpdated;

    public static class MaliciousIp {
        @JsonProperty("threat")
        public String threat;
        
        @JsonProperty("confidence")
        public double confidence;
        
        @JsonProperty("family")
        public String family;
    }

    public static class MalwareDomain {
        @JsonProperty("threat")
        public String threat;
        
        @JsonProperty("confidence")
        public double confidence;
    }
}
