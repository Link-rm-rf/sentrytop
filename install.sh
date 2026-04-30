#!/bin/bash
set -e  # Exit on any error

echo "=================================================="
echo "  Installing SentryTop EDR Agent"
echo "=================================================="

# Check for root
if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run this script as root (sudo ./install.sh)"
  exit 1
fi

# Step 1: Check dependencies
echo "[1/5] Checking dependencies..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y python3-venv python3-dev gcc make openjdk-21-jdk maven

# Step 2: Create app directory
echo "[2/5] Creating SentryTop directory..."
mkdir -p /opt/sentrytop
cp -r . /opt/sentrytop/
cd /opt/sentrytop

# Compile Collector
echo "Building C Collector sensor..."
(cd collector && make clean && make all)

# Build Java Engine
if [ -f "engine/pom.xml" ]; then
    echo "Building Java Correlator engine..."
    (cd engine && mvn clean package -DskipTests)
fi

# Fix permissions
chmod +x scripts/sentrytop
chmod +x ui/sentrytop_cli.py
chmod +x collector/sentry_collector

# Step 3: Create virtual environment (VENV - this is key!)
echo "[3/5] Setting up Python virtual environment..."
python3 -m venv /opt/sentrytop/venv
source /opt/sentrytop/venv/bin/activate

# Step 4: Upgrade pip INSIDE venv
echo "[4/5] Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install rich psutil pexpect
fi

# Step 5: Create wrapper script
echo "[5/5] Creating command wrapper..."
cat > /usr/local/bin/sentrytop << 'EOF'
#!/bin/bash
source /opt/sentrytop/venv/bin/activate
export NOSUDO=1  # Prevent internal sudo checks if running as root or mock
exec python3 /opt/sentrytop/ui/sentrytop_cli.py "$@"
EOF
chmod +x /usr/local/bin/sentrytop

# Step 6: Create systemd service
echo "[6/6] Creating systemd service..."
cat > /etc/systemd/system/sentrytop.service << 'EOF'
[Unit]
Description=SentryTop EDR Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/sentrytop
ExecStart=/usr/local/bin/sentrytop
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload || true
systemctl enable sentrytop || true

echo "=================================================="
echo "✓ SentryTop installed successfully!"
echo "✓ Run: sudo sentrytop"
echo "✓ Or: sudo systemctl start sentrytop"
echo "=================================================="
