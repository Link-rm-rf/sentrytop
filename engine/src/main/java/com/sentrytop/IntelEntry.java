package com.sentrytop;

import com.fasterxml.jackson.annotation.JsonProperty;

public class IntelEntry {
    @JsonProperty("ip")
    public String ip;
    
    @JsonProperty("confidence")
    public String confidence;
    
    @JsonProperty("category")
    public String category;
}
