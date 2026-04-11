# Polymarket Sniper Daemon: Setup & Operations Guide

This guide covers the installation, configuration, and operation of the autonomous 24/7 Polymarket Sniper Daemon. The daemon is designed to run locally on your machine (macOS or Linux) or on a VPS, continuously scanning markets and executing high-confidence bets based on the whale archetypes identified in the intelligence report.

## 1. Installation

The daemon includes a one-command installer that handles dependencies, repository cloning, environment configuration, and system service registration.

Open your terminal and run:

```bash
git clone https://github.com/Sheldonos/SheldonOS.git
cd SheldonOS/polymarket-agent
chmod +x install.sh
./install.sh
```

The installer will prompt you for:
*   **Execution Mode:** Choose `dry_run` (safe logging), `paper` (virtual money), or `live` (real money).
*   **Starting Bankroll:** Your initial capital in USDC.
*   **API Keys:** Polymarket keys (if live) and OpenAI key (for LLM reasoning).
*   **Notifications:** Telegram Bot Token and Chat ID (highly recommended).

## 2. Architecture Overview

The daemon operates using a hierarchical agent architecture to maximize throughput and isolate risk:

*   **AgentSupervisor:** The master controller. It manages a fleet of 5 specialized sub-agents, monitors their health, and handles context window handoffs (triggering at 56% usage to prevent token exhaustion).
*   **Sub-Agents:**
    *   `CryptoSniper`: Scans BTC/ETH price markets every 30s.
    *   `SoccerSniper`: Hunts for the `reachingthesky` and `KeyTransporter` archetypes.
    *   `SportsSniper`: Covers NBA, NFL, MLB, and esports.
    *   `GeopoliticalSniper`: Hunts for the "insider" pattern in world events.
    *   `TechSniper`: Covers niche markets (like the Google Search predictor).
*   **SniperScorer:** The core intelligence engine. It scores every market (0-100) based on mispricing, liquidity, price velocity, whale accumulation signals, and Kronos time-series forecasts.
*   **ExecutionEngine:** Enforces strict risk controls (daily loss limits, max concurrent positions, Kelly fraction caps) before executing trades.

## 3. Operating the Daemon

The installer creates three convenience scripts in the `polymarket-agent` directory:

### Start the Daemon
```bash
./sniper-start
```
*Note: If you installed it as a system service during setup, it is already running in the background.*

### View the Live Dashboard
```bash
./sniper-dashboard
```
This launches a rich terminal UI showing your live bankroll, open positions, recent opportunities, and a live log feed. You can leave this running in a terminal window while the daemon operates in the background.

### Check Status
```bash
./sniper-status
```
Prints a quick summary of the daemon's current state, uptime, and the health of all sub-agents.

## 4. Risk Management & Configuration

All risk parameters are defined in `config/config.yaml` under the `daemon` section. **Review these before running in LIVE mode.**

Key safeguards currently active:
*   **Daily Loss Limit:** Trading halts automatically if daily P&L drops below -20% of your bankroll.
*   **Max Bet Cap:** No single bet will exceed $500 USDC, regardless of the Kelly fraction, to prevent slippage in thin markets.
*   **Re-score Gate:** If the price drifts by more than 5¢ between scoring and execution, the trade is aborted.
*   **Bankroll Floor:** The daemon will stop trading if your bankroll falls below $100 USDC.

To modify these settings, edit `config/config.yaml` and restart the daemon.

## 5. Notifications

If configured during installation, the daemon will send push notifications to your phone via Telegram or Discord.

*   **INFO:** Routine updates (e.g., context handoffs).
*   **SUCCESS:** Winning trades and profit updates.
*   **WARNING:** Losing trades or minor errors.
*   **CRITICAL:** Daily loss limits hit or agent crashes.

You can test your notification setup by running:
```bash
python3 daemon/daemon_main.py --test-notifications
```
