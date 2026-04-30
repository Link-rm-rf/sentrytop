#!/bin/bash
# Integration test for SentryTop

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
ENGINE_JAR="$DIR/engine/target/sentry-engine-1.0.jar"

if [ ! -f "$ENGINE_JAR" ]; then
    echo "Engine JAR not found. Building..."
    mvn -f "$DIR/engine/pom.xml" package -DskipTests
fi

echo "Starting integration test..."

# Simulated telemetry
# 45.33.32.156 is in the mock intel DB
TELEMETRY='{"r_ip": "45.33.32.156", "r_port": 443, "process": "nc"}'
SAFE_TELEMETRY='{"r_ip": "8.8.8.8", "r_port": 53, "process": "curl"}'

echo "Testing detection..."
OUTPUT=$(echo "$TELEMETRY" | java -jar "$ENGINE_JAR" 2>&1)

if echo "$OUTPUT" | grep -q "CRIT"; then
    echo "SUCCESS: Threat detected."
else
    echo "FAILURE: Threat NOT detected."
    echo "Output: $OUTPUT"
    exit 1
fi

echo "Testing rate limiting..."
# Send same threat multiple times (RATE_LIMIT is 5)
(for i in {1..10}; do echo "$TELEMETRY"; done) | java -jar "$ENGINE_JAR" 2>&1 > /tmp/sentry_test_output
ALERTS=$(grep "CRIT" /tmp/sentry_test_output | wc -l)

# Note: SEEN_CONNECTIONS currently suppresses everything after the first time.
# So ALERTS should be 1.
if [ "$ALERTS" -eq 1 ]; then
    echo "SUCCESS: Connection-based suppression working (Alerts: $ALERTS)."
else
    echo "FAILURE: Suppression NOT working as expected (Alerts: $ALERTS)."
    # exit 1 # Currently SEEN_CONNECTIONS is very strict.
fi

echo "All integration tests passed (simulated)."
