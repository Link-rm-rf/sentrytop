package com.sentrytop;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * BehavioralAnalyzer: Detects high-frequency "beaconing" patterns.
 * 
 * It tracks the arrival times of connections for each unique process-destination pair.
 * 
 * Thread Safety:
 * - Uses ConcurrentHashMap for the top-level mapping.
 * - Uses Collections.synchronizedList for the timestamp window.
 * - High-concurrency is handled by Java Virtual Threads in the calling ThreatAnalyzer.
 */
public class BehavioralAnalyzer {
    private final Map<String, List<Long>> connectionTimestamps = new ConcurrentHashMap<>();
    private static final int WINDOW_SIZE = 10;
    private static final long THRESHOLD_MS = 1000; // 1 second average interval is "high frequency"

    public boolean isAnomaly(String connectionId) {
        long now = System.currentTimeMillis();
        List<Long> timestamps = connectionTimestamps.computeIfAbsent(connectionId, k -> Collections.synchronizedList(new ArrayList<>()));
        
        timestamps.add(now);
        if (timestamps.size() > WINDOW_SIZE) {
            timestamps.remove(0);
        }

        if (timestamps.size() == WINDOW_SIZE) {
            long duration = timestamps.get(WINDOW_SIZE - 1) - timestamps.get(0);
            long avg = duration / WINDOW_SIZE;
            return avg < THRESHOLD_MS;
        }
        
        return false;
    }
}
