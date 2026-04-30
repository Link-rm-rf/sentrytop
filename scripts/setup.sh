#!/bin/bash
# Setup script for SentryTop Production Hardening

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

echo "Setting up file permissions..."

# Assets (intel DB) should be readable but not writable by others
chmod 644 "$DIR/assets/intel_db.txt"

# Collector binary should be owned by root and executable
if [ -f "$DIR/collector/sentry_collector" ]; then
    sudo chown root:root "$DIR/collector/sentry_collector"
    sudo chmod 755 "$DIR/collector/sentry_collector"
fi

# Engine JAR should be readable
if [ -f "$DIR/engine/target/sentry-engine-1.0.jar" ]; then
    chmod 644 "$DIR/engine/target/sentry-engine-1.0.jar"
fi

# Ensure scripts are executable
chmod +x "$DIR/scripts/sentrytop"
chmod +x "$DIR/scripts/integration_test.sh"

echo "Setup complete."
