#!/bin/bash
# SentryTop Stress Test Script
# Rapidly opens connections to simulate high-traffic load

TARGET_IP="8.8.8.8"
TARGET_PORT=53
NUM_CONNECTIONS=100

echo "Starting stress test: $NUM_CONNECTIONS connections to $TARGET_IP:$TARGET_PORT"

for i in $(seq 1 $NUM_CONNECTIONS); do
    # Use timeout to ensure the connection attempt doesn't hang
    timeout 0.1 bash -c "echo > /dev/tcp/$TARGET_IP/$TARGET_PORT" 2>/dev/null &
    if (( i % 20 == 0 )); then
        echo "Launched $i connections..."
        sleep 0.1
    fi
done

wait
echo "Stress test complete."
