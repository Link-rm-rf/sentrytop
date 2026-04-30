#!/usr/bin/env bash

# SentryTop v1.0.0 - PEP 668 Compliant Installer
# This script deploys SentryTop to /opt/sentrytop using a virtual environment.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

INSTALL_DIR="/opt/sentrytop"
WRAPPER_PATH="/usr/local/bin/sentrytop"

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}        Installing SentryTop EDR Agent           ${NC}"
echo -e "${CYAN}=================================================${NC}"

# Check for root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[!] Please run this script as root (sudo ./install.sh)${NC}"
  exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "\n${GREEN}[1/5] Checking system dependencies...${NC}"
DEPS=("gcc" "make" "python3" "python3-pip" "python3-venv")
for DEP in "${DEPS[@]}"; do
    if ! command_exists "$DEP" && ! dpkg -s "$DEP" >/dev/null 2>&1; then
        echo -e "${RED}[!] Missing $DEP. Attempting to install...${NC}"
        if command_exists apt-get; then
            apt-get update && apt-get install -y "$DEP"
        else
            echo -e "${RED}[!] Cannot automatically install $DEP. Please install manually.${NC}"
            exit 1
        fi
    fi
done

echo -e "\n${GREEN}[2/5] Setting up environment at $INSTALL_DIR...${NC}"
mkdir -p "$INSTALL_DIR"
cp -r ./* "$INSTALL_DIR/"
cd "$INSTALL_DIR"

# Ensure internal scripts are executable
chmod +x scripts/sentrytop
chmod +x ui/sentrytop_cli.py

echo -e "\n${GREEN}[3/5] Creating Python virtual environment...${NC}"
python3 -m venv "$INSTALL_DIR/venv"

echo -e "\n${GREEN}[4/5] Installing Python dependencies into venv...${NC}"
# Use the venv's pip to avoid PEP 668 issues
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install -r requirements.txt --quiet || "$INSTALL_DIR/venv/bin/pip" install rich psutil --quiet

echo -e "\n${GREEN}[5/5] Creating global wrapper and systemd service...${NC}"

# Create the /usr/local/bin wrapper
cat <<EOF > "$WRAPPER_PATH"
#!/bin/bash
# SentryTop Wrapper Script
# Activates venv and passes arguments to the TUI
export NOSUDO=1
exec "$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/ui/sentrytop_cli.py" "\$@"
EOF

chmod +x "$WRAPPER_PATH"

# Create the systemd service (pointing to the engine)
cat <<EOF > /etc/systemd/system/sentrytop.service
[Unit]
Description=SentryTop EDR Sensor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/scripts/sentrytop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo -e "\n${GREEN}[✔] Installation Complete!${NC}"
echo -e "Launch the real-time EDR interface: ${CYAN}sudo sentrytop${NC}"
echo -e "Launch the offline demo: ${CYAN}sentrytop --mock${NC}"
echo -e "Control the background service: ${CYAN}sudo systemctl status sentrytop${NC}"
echo -e "${CYAN}=================================================${NC}"
