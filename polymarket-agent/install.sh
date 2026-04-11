#!/usr/bin/env bash
# =============================================================================
# Polymarket Sniper Daemon — One-Command Installer
# =============================================================================
# Usage:
#   chmod +x install.sh && ./install.sh
#
# What this does:
#   1. Checks system requirements (Python 3.9+, git, pip)
#   2. Clones all required repositories (polyterm, Kronos, hermes-agent)
#   3. Installs all Python dependencies
#   4. Runs the .env configuration wizard
#   5. Installs the daemon as a system service (systemd on Linux, launchd on macOS)
#   6. Starts the daemon in dry_run mode
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

DAEMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$DAEMON_DIR")"
LOG_FILE="$DAEMON_DIR/logs/install.log"

mkdir -p "$DAEMON_DIR/logs" "$DAEMON_DIR/data"

print_header() {
    echo -e "\n${BOLD}${CYAN}============================================================${NC}"
    echo -e "${BOLD}${CYAN}  🎯 POLYMARKET SNIPER DAEMON — INSTALLER${NC}"
    echo -e "${BOLD}${CYAN}============================================================${NC}\n"
}

print_step() {
    echo -e "${BOLD}${BLUE}▶ $1${NC}"
}

print_ok() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}  ✗ $1${NC}"
}

# =============================================================================
# Step 1: System requirements check
# =============================================================================
print_header
print_step "Checking system requirements..."

# Python version
if ! command -v python3 &>/dev/null; then
    print_error "Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    print_error "Python 3.9+ required. Found: $PYTHON_VERSION"
    exit 1
fi
print_ok "Python $PYTHON_VERSION"

# pip
if ! command -v pip3 &>/dev/null; then
    print_error "pip3 not found. Please install pip."
    exit 1
fi
print_ok "pip3 found"

# git
if ! command -v git &>/dev/null; then
    print_error "git not found. Please install git."
    exit 1
fi
print_ok "git found"

# Detect OS
OS="$(uname -s)"
print_ok "OS: $OS"

# =============================================================================
# Step 2: Clone required repositories
# =============================================================================
print_step "Cloning required repositories..."

clone_if_missing() {
    local repo_url="$1"
    local target_dir="$2"
    local name="$3"

    if [ -d "$target_dir" ]; then
        print_ok "$name already cloned — pulling latest..."
        git -C "$target_dir" pull --quiet 2>/dev/null || true
    else
        echo -e "  Cloning $name..."
        git clone --quiet "$repo_url" "$target_dir" 2>&1 | tee -a "$LOG_FILE"
        print_ok "$name cloned"
    fi
}

clone_if_missing "https://github.com/NYTEMODEONLY/polyterm" "$PARENT_DIR/polyterm" "polyterm"
clone_if_missing "https://github.com/shiyu-coder/Kronos" "$PARENT_DIR/Kronos" "Kronos"
clone_if_missing "https://github.com/NousResearch/hermes-agent" "$PARENT_DIR/hermes-agent" "hermes-agent"

# =============================================================================
# Step 3: Install Python dependencies
# =============================================================================
print_step "Installing Python dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "$DAEMON_DIR/.venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "$DAEMON_DIR/.venv"
    print_ok "Virtual environment created"
fi

# Activate venv
source "$DAEMON_DIR/.venv/bin/activate"

# Upgrade pip
pip install --upgrade pip --quiet

# Install requirements
pip install -r "$DAEMON_DIR/requirements.txt" --quiet 2>&1 | tee -a "$LOG_FILE"
print_ok "Python dependencies installed"

# Install additional daemon dependencies
pip install rich requests python-dateutil pyyaml numpy 2>&1 | tee -a "$LOG_FILE" || true
print_ok "Daemon dependencies installed"

# =============================================================================
# Step 4: Configuration wizard
# =============================================================================
print_step "Running configuration wizard..."

ENV_FILE="$DAEMON_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    print_warn ".env file already exists. Skipping wizard (delete .env to reconfigure)."
else
    echo ""
    echo -e "${BOLD}Please provide your configuration details.${NC}"
    echo -e "${YELLOW}Press Enter to skip optional fields.${NC}\n"

    # Execution mode
    echo -e "${BOLD}Execution Mode:${NC}"
    echo "  1) dry_run  — logs everything, executes nothing (SAFE — start here)"
    echo "  2) paper    — simulates trades with virtual money against real prices"
    echo "  3) live     — real money (requires Polymarket API key + wallet)"
    read -rp "Choose mode [1/2/3] (default: 1): " MODE_CHOICE
    case "$MODE_CHOICE" in
        2) EXEC_MODE="paper" ;;
        3) EXEC_MODE="live" ;;
        *) EXEC_MODE="dry_run" ;;
    esac

    # Starting bankroll
    read -rp "Starting bankroll in USDC (default: 1000): " BANKROLL
    BANKROLL="${BANKROLL:-1000}"

    # Telegram (optional)
    echo ""
    echo -e "${BOLD}Telegram Notifications (optional but recommended):${NC}"
    echo "  Create a bot at https://t.me/BotFather and get your chat ID from @userinfobot"
    read -rp "Telegram Bot Token (leave blank to skip): " TG_TOKEN
    read -rp "Telegram Chat ID (leave blank to skip): " TG_CHAT_ID

    # Discord (optional)
    echo ""
    echo -e "${BOLD}Discord Notifications (optional):${NC}"
    read -rp "Discord Webhook URL (leave blank to skip): " DISCORD_WEBHOOK

    # Polymarket API key (required for live mode)
    POLY_API_KEY=""
    POLY_PRIVATE_KEY=""
    if [ "$EXEC_MODE" = "live" ]; then
        echo ""
        echo -e "${BOLD}${RED}LIVE MODE — Polymarket API credentials required:${NC}"
        read -rp "Polymarket API Key: " POLY_API_KEY
        read -rsp "Polymarket Private Key (hidden): " POLY_PRIVATE_KEY
        echo ""
    fi

    # OpenAI API key
    echo ""
    echo -e "${BOLD}OpenAI API Key (for LLM reasoning):${NC}"
    read -rsp "OpenAI API Key (hidden, press Enter to skip): " OPENAI_KEY
    echo ""

    # Write .env file
    cat > "$ENV_FILE" << EOF
# Polymarket Sniper Daemon — Environment Configuration
# Generated by installer on $(date)

# Execution mode: dry_run | paper | live
EXECUTION_MODE=${EXEC_MODE}

# Starting bankroll (USDC)
INITIAL_BANKROLL=${BANKROLL}

# Polymarket API credentials (required for live mode)
POLYMARKET_API_KEY=${POLY_API_KEY}
POLYMARKET_PRIVATE_KEY=${POLY_PRIVATE_KEY}

# Notifications
TELEGRAM_BOT_TOKEN=${TG_TOKEN}
TELEGRAM_CHAT_ID=${TG_CHAT_ID}
DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK}

# LLM (OpenAI-compatible)
OPENAI_API_KEY=${OPENAI_KEY}

# Logging
LOG_LEVEL=INFO
EOF

    chmod 600 "$ENV_FILE"
    print_ok "Configuration saved to .env"
fi

# Load .env
set -a
source "$ENV_FILE"
set +a

# =============================================================================
# Step 5: Install as system service
# =============================================================================
print_step "Installing system service..."

VENV_PYTHON="$DAEMON_DIR/.venv/bin/python3"

if [ "$OS" = "Linux" ]; then
    # systemd service
    SERVICE_FILE="/etc/systemd/system/polymarket-sniper.service"
    EXEC_MODE_VAL="${EXECUTION_MODE:-dry_run}"

    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Polymarket Sniper Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=${DAEMON_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${VENV_PYTHON} daemon/daemon_main.py --mode ${EXEC_MODE_VAL} --config config/config.yaml
Restart=always
RestartSec=10
StandardOutput=append:${DAEMON_DIR}/logs/daemon.log
StandardError=append:${DAEMON_DIR}/logs/daemon_error.log

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable polymarket-sniper
    print_ok "systemd service installed and enabled"
    echo ""
    echo -e "${CYAN}  Service commands:${NC}"
    echo "    sudo systemctl start polymarket-sniper    # Start daemon"
    echo "    sudo systemctl stop polymarket-sniper     # Stop daemon"
    echo "    sudo systemctl status polymarket-sniper   # Check status"
    echo "    journalctl -u polymarket-sniper -f        # View logs"

elif [ "$OS" = "Darwin" ]; then
    # launchd plist
    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$PLIST_DIR/com.polymarket.sniper.plist"
    EXEC_MODE_VAL="${EXECUTION_MODE:-dry_run}"
    mkdir -p "$PLIST_DIR"

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.polymarket.sniper</string>
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_PYTHON}</string>
        <string>${DAEMON_DIR}/daemon/daemon_main.py</string>
        <string>--mode</string>
        <string>${EXEC_MODE_VAL}</string>
        <string>--config</string>
        <string>${DAEMON_DIR}/config/config.yaml</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${DAEMON_DIR}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>${DAEMON_DIR}:${PARENT_DIR}/polyterm:${PARENT_DIR}/Kronos:${PARENT_DIR}/hermes-agent</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${DAEMON_DIR}/logs/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>${DAEMON_DIR}/logs/daemon_error.log</string>
</dict>
</plist>
EOF

    launchctl load "$PLIST_FILE" 2>/dev/null || true
    print_ok "launchd service installed"
    echo ""
    echo -e "${CYAN}  Service commands:${NC}"
    echo "    launchctl start com.polymarket.sniper    # Start daemon"
    echo "    launchctl stop com.polymarket.sniper     # Stop daemon"
    echo "    launchctl unload $PLIST_FILE             # Remove service"
fi

# =============================================================================
# Step 6: Create convenience scripts
# =============================================================================
print_step "Creating convenience scripts..."

# sniper-start
cat > "$DAEMON_DIR/sniper-start" << 'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/.venv/bin/activate" 2>/dev/null || true
source "$DIR/.env" 2>/dev/null || true
MODE="${EXECUTION_MODE:-dry_run}"
echo "Starting Polymarket Sniper Daemon in $MODE mode..."
python3 "$DIR/daemon/daemon_main.py" --mode "$MODE" "$@"
EOF
chmod +x "$DAEMON_DIR/sniper-start"

# sniper-dashboard
cat > "$DAEMON_DIR/sniper-dashboard" << 'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DIR/.venv/bin/activate" 2>/dev/null || true
python3 "$DIR/daemon/daemon_main.py" --dashboard "$@"
EOF
chmod +x "$DAEMON_DIR/sniper-dashboard"

# sniper-status
cat > "$DAEMON_DIR/sniper-status" << 'EOF'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_FILE="$DIR/data/daemon_state.json"
if [ -f "$STATE_FILE" ]; then
    python3 -c "
import json, sys
with open('$STATE_FILE') as f:
    s = json.load(f)
print(f\"Status: {s.get('status','unknown').upper()}\")
print(f\"Mode: {s.get('mode','unknown').upper()}\")
print(f\"Bankroll: \${s.get('bankroll',0):,.2f}\")
print(f\"Uptime: {s.get('uptime_hours',0):.1f}h\")
fleet = s.get('fleet_status', [])
print(f\"Agents: {len(fleet)} active\")
for a in fleet:
    print(f\"  {a['name']}: {a['status']} | context={a['context_pct']:.1f}% | pnl=\${a['total_pnl']:+.2f}\")
"
else
    echo "Daemon not running (state file not found)"
fi
EOF
chmod +x "$DAEMON_DIR/sniper-status"

print_ok "Convenience scripts created: sniper-start, sniper-dashboard, sniper-status"

# =============================================================================
# Done
# =============================================================================
echo ""
echo -e "${BOLD}${GREEN}============================================================${NC}"
echo -e "${BOLD}${GREEN}  ✅ INSTALLATION COMPLETE${NC}"
echo -e "${BOLD}${GREEN}============================================================${NC}"
echo ""
echo -e "${BOLD}Quick Start:${NC}"
echo -e "  ${CYAN}./sniper-start${NC}            # Start the daemon"
echo -e "  ${CYAN}./sniper-dashboard${NC}        # Open live terminal dashboard"
echo -e "  ${CYAN}./sniper-status${NC}           # Check daemon status"
echo ""
echo -e "${BOLD}Recommended first steps:${NC}"
echo "  1. Run in dry_run mode for 24h to verify everything works"
echo "  2. Switch to paper mode to test with real prices (virtual money)"
echo "  3. Only switch to live mode after reviewing paper trading results"
echo ""
echo -e "${YELLOW}  ⚠ IMPORTANT: Never run in live mode without reviewing the risk${NC}"
echo -e "${YELLOW}    management settings in config/config.yaml first.${NC}"
echo ""
