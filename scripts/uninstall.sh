#!/bin/bash
# SentryTop Uninstallation Script
set -e

INSTALL_DIR="/opt/sentrytop"
SERVICE_FILE="/etc/systemd/system/sentrytop.service"

echo "=== SentryTop Uninstallation ==="

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

echo "Stopping and disabling service..."
systemctl stop sentrytop || true
systemctl disable sentrytop || true

if [ -f "$SERVICE_FILE" ]; then
    rm "$SERVICE_FILE"
    systemctl daemon-reload
fi

if [ -d "$INSTALL_DIR" ]; then
    echo "Removing $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
fi

echo "Uninstallation complete!"
