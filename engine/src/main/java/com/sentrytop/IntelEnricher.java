package com.sentrytop;

import java.util.*;

public class IntelEnricher {
    private static final Map<String, String> GEO_DB = Map.of();

    public static String getGeoInfo(String ip) {
        return GEO_DB.getOrDefault(ip, "Unknown Location");
    }
}
