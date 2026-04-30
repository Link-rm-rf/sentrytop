#!/bin/bash
# SentryTop Installation Script
set -e

INSTALL_DIR="/opt/sentrytop"
SERVICE_FILE="/etc/systemd/system/sentrytop.service"

echo "=== SentryTop Installation ==="

# 1. Check for root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# 2. Build components
echo "Building components..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
make -C "$DIR/collector"
cd "$DIR/engine" && mvn clean package -DskipTests
cd "$DIR"

# 3. Create install directory
echo "Creating $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR/collector"
mkdir -p "$INSTALL_DIR/engine/target"
mkdir -p "$INSTALL_DIR/assets"

# 4. Copy files
cp "$DIR/collector/sentry_collector" "$INSTALL_DIR/collector/"
cp "$DIR/engine/target/sentry-engine-1.0.jar" "$INSTALL_DIR/engine/target/"
cp -r "$DIR/assets/"* "$INSTALL_DIR/assets/"

# 5. Setup systemd service
echo "Installing systemd service..."
cat <<EOF > $SERVICE_FILE
[Unit]
Description=SentryTop EDR Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/bin/bash -c "$INSTALL_DIR/collector/sentry_collector 1 | /usr/bin/java -jar $INSTALL_DIR/engine/target/sentry-engine-1.0.jar"
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sentrytop

echo "Installation complete!"
echo "Start SentryTop with: systemctl start sentrytop"
echo "Monitor logs with: journalctl -u sentrytop -f"
