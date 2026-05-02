#!/bin/bash
set -e

echo "----------------------------------------------------"
echo "  SENTRYTOP v2.0.0 - Installation Script            "
echo "  Professional-Grade SOC/EDR Terminal Platform      "
echo "----------------------------------------------------"

# Check for Rust/Cargo
if ! command -v cargo &> /dev/null; then
    echo "[!] Cargo not found. Installing Rust toolchain..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

echo "[1/3] Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq build-essential libsqlite3-dev

echo "[2/3] Building Unified Rust Agent..."
cd agent
cargo build --release
cd ..

echo "[3/3] Setting up system integration..."
INSTALL_DIR="/opt/sentrytop"
sudo mkdir -p "$INSTALL_DIR"
sudo cp agent/target/release/sentrytop-agent "$INSTALL_DIR/"
sudo ln -sf "$INSTALL_DIR/sentrytop-agent" /usr/local/bin/sentrytop

echo "----------------------------------------------------"
echo "[SUCCESS] SENTRYTOP v2.0.0 is now installed."
echo "[INFO] Run with: sudo sentrytop"
echo "----------------------------------------------------"
