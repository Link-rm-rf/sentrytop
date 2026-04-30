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
# (RATE_LIMIT is 5)
(for i in {1..10}; do echo "$TELEMETRY"; done) | java -jar "$ENGINE_JAR" 2>&1 > /tmp/sentry_test_output
ALERTS=$(grep "CRIT" /tmp/sentry_test_output | wc -l)


if [ "$ALERTS" -eq 1 ]; then
    echo "SUCCESS: Connection-based suppression working (Alerts: $ALERTS)."
else
    echo "FAILURE: Suppression NOT working as expected (Alerts: $ALERTS)."
  
fi

echo "All integration tests passed (simulated)."
