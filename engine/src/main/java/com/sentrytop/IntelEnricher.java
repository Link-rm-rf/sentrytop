package com.sentrytop;

import java.util.*;

public class IntelEnricher {
    private static final Map<String, String> GEO_DB = Map.of(
        "45.33.32.156", "US (New Jersey)",
        "185.199.108.153", "US (GitHub)",
        "8.8.8.8", "US (Google)",
        "0:0:0:0:0:0:0:1", "Localhost (IPv6)",
        "::1", "Localhost (IPv6)"
    );

    public static String getGeoInfo(String ip) {
        return GEO_DB.getOrDefault(ip, "Unknown Location");
    }
}
