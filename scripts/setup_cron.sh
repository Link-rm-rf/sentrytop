#!/bin/bash
# SentryTop Cron Installer

SCRIPT_PATH="/home/kura/sentrytop/scripts/update_intel_cron.sh"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: $SCRIPT_PATH not found."
    exit 1
fi

# Create a temporary crontab file
crontab -l > mycron 2>/dev/null

# Check if already installed
if grep -q "update_intel_cron.sh" mycron; then
    echo "Cron job already exists."
    rm mycron
    exit 0
fi

# Add the new cron job: Run at 00:00 every Sunday
echo "0 0 * * 0 $SCRIPT_PATH" >> mycron

# Install the new crontab
crontab mycron
rm mycron

echo "SentryTop weekly intel update scheduled (Sundays at 00:00)."
