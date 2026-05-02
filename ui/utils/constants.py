"""
SentryTop v1.1 - Core Constants
"""

import os

# Versioning
VERSION = "v1.1.0"

# Colors (Strict Palette)
COLOR_PRIMARY = "green"   # Normal text, primary elements
COLOR_ACCENT = "green"    # Selected items, informational
COLOR_CRITICAL = "red"   # CRITICAL threats only
COLOR_WARNING = "yellow" # Warnings
COLOR_BG = "black"      # Background

# Paths
DEFAULT_DB_PATH = "/opt/sentrytop/alerts.db"
DEFAULT_FIFO_PATH = "/opt/sentrytop/alerts.fifo"

def get_project_root() -> str:
    """Resolves the project root directory."""
    script_path = os.path.abspath(__file__)
    # Root is three levels up from ui/utils/constants.py
    return os.path.dirname(os.path.dirname(os.path.dirname(script_path)))

PROJECT_ROOT = get_project_root()

# UI Settings
REFRESH_RATE = 15  # FPS
LOG_LIMIT = 500
MAX_VISIBLE_LOGS = 22

# Threat Keywords
THREAT_KEYWORDS = ["[CRIT]", "[WARN]", "[BEAC]", "Unusual Port"]
SAFE_KEYWORDS = ["New safe connection"]

# Mode Keys
MODE_MENU = '0'
MODE_MONITOR = '1'
MODE_PROCESS = '2'
MODE_NETWORK = '3'
MODE_LOGS = '4'

# Protected Processes (Cannot be killed)
PROTECTED_PROCESSES = [
    "systemd", "sshd", "nginx", "init", "kernel", "python3", "bash", "zsh", 
    "dbus-daemon", "networkd-dispatcher", "systemd-resolved", "systemd-logind"
]
