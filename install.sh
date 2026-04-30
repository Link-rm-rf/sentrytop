#!/bin/bash
set -e

echo "=================================================="
echo "  SentryTop EDR - Professional Installer"
echo "=================================================="

if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run as root (sudo ./install.sh)"
  exit 1
fi

INSTALL_DIR="/opt/sentrytop"
BIN_PATH="/usr/local/bin/sentrytop"

# Cleanup old instances
systemctl stop sentrytop 2>/dev/null || true
pkill -f sentry_collector 2>/dev/null || true
pkill -f sentrytop_cli.py 2>/dev/null || true

echo "[1/4] Installing system dependencies..."
apt-get update -qq
apt-get install -y python3-venv python3-dev gcc make openjdk-21-jdk maven >/dev/null

echo "[2/4] Deploying files to $INSTALL_DIR..."
# Force remove old files to prevent corruption (like bash wrappers in ui/)
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"

# Compile components
(cd "$INSTALL_DIR/collector" && make clean && make all >/dev/null)
if [ -f "$INSTALL_DIR/engine/pom.xml" ]; then
    (cd "$INSTALL_DIR/engine" && mvn clean package -DskipTests >/dev/null)
fi

# Permissions
chmod +x "$INSTALL_DIR/scripts/sentrytop"
chmod +x "$INSTALL_DIR/ui/sentrytop_cli.py"
chmod +x "$INSTALL_DIR/collector/sentry_collector"

# Ensure log exists and is writable by root
touch "$INSTALL_DIR/sentrytop_cli.log"
chmod 644 "$INSTALL_DIR/sentrytop_cli.log"

echo "[3/4] Setting up Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/venv/bin/pip" install rich psutil --quiet

echo "[4/4] Creating command wrapper..."
rm -f "$BIN_PATH"
cat << 'EOF' > "$BIN_PATH"
#!/bin/bash
export NOSUDO=1
source /opt/sentrytop/venv/bin/activate
exec python3 /opt/sentrytop/ui/sentrytop_cli.py "$@"
EOF
chmod +x "$BIN_PATH"

echo "=================================================="
echo "✓ Installation Complete!"
echo "✓ Run: sudo sentrytop"
echo "=================================================="
