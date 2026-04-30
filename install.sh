#!/usr/bin/env bash

# SentryTop v1.0.0 Installation Script
# This script handles dependency checking and environment setup.

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
  echo -e "${RED}[!] Please run this script as root (sudo ./install.sh)${NC}"
  exit 1
fi

echo -e "\n${GREEN}[1/3] Checking dependencies...${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install missing dependencies (Debian/Ubuntu)
DEPS=("gcc" "make" "python3" "python3-pip")
for DEP in "${DEPS[@]}"; do
    if ! command_exists "$DEP"; then
        echo -e "${RED}[!] Missing $DEP. Attempting to install...${NC}"
        if command_exists apt-get; then
            apt-get update && apt-get install -y "$DEP"
        else
            echo -e "${RED}[!] Cannot automatically install $DEP. Please install manually.${NC}"
        fi
    fi
done

# Python requirements
echo -e "\n${GREEN}[2/3] Installing Python TUI dependencies...${NC}"
pip3 install -r requirements.txt --quiet || pip3 install rich psutil --quiet

echo -e "\n${GREEN}[3/3] Setting up environment...${NC}"
# Fix permissions
chmod +x scripts/sentrytop
chmod +x ui/sentrytop_cli.py

# Create global symlink
ln -sf "$(pwd)/ui/sentrytop_cli.py" /usr/local/bin/sentrytop

echo -e "\n${GREEN}[✔] Installation Complete!${NC}"
echo -e "Launch the real-time EDR interface: ${CYAN}sudo sentrytop${NC}"
echo -e "Launch the offline demo: ${CYAN}python3 ui/sentrytop_cli.py --mock${NC}"
echo -e "${CYAN}=================================================${NC}"
