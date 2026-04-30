#!/usr/bin/env bash

# SentryTop v1.0.0 Installation Script
# This script handles dependency checking, compilation, and systemd setup.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}        Installing SentryTop EDR Agent           ${NC}"
echo -e "${CYAN}=================================================${NC}"

# Check for root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[!] Please run this script as root (sudo bash install.sh)${NC}"
  exit 1
fi

echo -e "\n${GREEN}[1/5] Checking dependencies...${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install missing dependencies (Debian/Ubuntu focused for this script)
DEPS=("gcc" "make" "python3" "python3-pip")
for DEP in "${DEPS[@]}"; do
    if ! command_exists "$DEP"; then
        echo -e "${RED}[!] Missing $DEP. Attempting to install...${NC}"
        if command_exists apt-get; then
            apt-get update && apt-get install -y "$DEP"
        else
            echo -e "${RED}[!] Cannot automatically install $DEP. Please install manually.${NC}"
            exit 1
        fi
    fi
done

# Python requirements
echo -e "\n${GREEN}[2/5] Installing Python dependencies...${NC}"
pip3 install -r requirements.txt || pip3 install rich psutil

echo -e "\n${GREEN}[3/5] Setting up environment...${NC}"
# Assuming the user ran curl | bash, we need to clone the repo if not in it
if [ ! -f "sentrytop_cli.py" ]; then
    echo "Cloning repository to /opt/sentrytop..."
    git clone https://github.com/Link-rm-rf/sentrytop.git /opt/sentrytop || echo "Directory exists, pulling latest..." && cd /opt/sentrytop && git pull
else
    echo "Running from local directory. Copying files to /opt/sentrytop..."
    mkdir -p /opt/sentrytop
    cp -r ./* /opt/sentrytop/
fi

cd /opt/sentrytop
chmod +x scripts/sentrytop
chmod +x sentrytop_cli.py

echo -e "\n${GREEN}[4/5] Creating global symlinks...${NC}"
ln -sf /opt/sentrytop/sentrytop_cli.py /usr/local/bin/sentrytop

echo -e "\n${GREEN}[5/5] Configuring systemd service...${NC}"
cat <<EOF > /etc/systemd/system/sentrytop.service
[Unit]
Description=SentryTop EDR Sensor
After=network.target

[Service]
Type=simple
User=root
ExecStart=/opt/sentrytop/scripts/sentrytop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
# systemctl enable sentrytop
# systemctl start sentrytop

echo -e "\n${GREEN}[✔] Installation Complete!${NC}"
echo -e "You can now run the interactive console by typing: ${CYAN}sudo sentrytop${NC}"
echo -e "To start the background collector service: ${CYAN}sudo systemctl start sentrytop${NC}"
echo -e "${CYAN}=================================================${NC}"
