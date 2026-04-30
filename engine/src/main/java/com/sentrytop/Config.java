package com.sentrytop;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class Config {
    @JsonProperty("polling_interval_ms")
    public int pollingIntervalMs;
    
    @JsonProperty("intel_db_path")
    public String intelDbPath;
    
    @JsonProperty("rate_limit")
    public int rateLimit;
    
    @JsonProperty("log_level")
    public String logLevel;

    @JsonProperty("suspicious_ports")
    public List<Integer> suspiciousPorts;
}
