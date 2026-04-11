"""
Polymarket Sniper Daemon — Main Entry Point
============================================
Starts the full autonomous trading daemon. This is the process that runs
24/7 in the background.

Usage:
  python daemon/daemon_main.py --mode dry_run   # safe testing
  python daemon/daemon_main.py --mode paper     # virtual money, real prices
  python daemon/daemon_main.py --mode live      # real money (requires API keys)

The daemon writes its state to data/daemon_state.json every 5 seconds.
The dashboard (python daemon/web/dashboard.py) reads this file and renders
the live TUI.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT.parent / "polyterm"))
sys.path.insert(0, str(_ROOT.parent / "Kronos"))
sys.path.insert(0, str(_ROOT.parent / "hermes-agent"))

from config import load_config
from daemon.notifications.notifier import NotificationManager
from daemon.supervisor.agent_supervisor import AgentSupervisor
from learning.self_learning import SelfLearningEngine

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(log_dir: str = "logs", level: str = "INFO"):
    import logging.handlers
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "daemon.log"),
        maxBytes=20 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(ch)

    return root


logger = logging.getLogger("daemon.main")


# ---------------------------------------------------------------------------
# State writer
# ---------------------------------------------------------------------------

class StateWriter:
    """
    Periodically writes the daemon's full state to a JSON file so the
    dashboard and external tools can read it without IPC.
    """

    def __init__(self, state_file: str, write_interval: int = 5):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.write_interval = write_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread = None
        self._state_getters = {}
        self._log_buffer = []
        self._log_lock = threading.Lock()

    def register_getter(self, key: str, getter_fn):
        self._state_getters[key] = getter_fn

    def add_log(self, level: str, message: str):
        with self._log_lock:
            self._log_buffer.append({
                "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                "level": level,
                "message": message[:200],
            })
            if len(self._log_buffer) > 100:
                self._log_buffer = self._log_buffer[-100:]

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._write_loop, name="StateWriter", daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _write_loop(self):
        while not self._stop_event.is_set():
            try:
                state = {}
                for key, getter in self._state_getters.items():
                    try:
                        state[key] = getter()
                    except Exception:
                        pass
                with self._log_lock:
                    state["recent_log"] = list(self._log_buffer[-20:])
                with open(self.state_file, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2, default=str)
            except Exception as exc:
                logger.debug("State write failed: %s", exc)
            time.sleep(self.write_interval)


# ---------------------------------------------------------------------------
# Log handler that feeds into StateWriter
# ---------------------------------------------------------------------------

class StateLogHandler(logging.Handler):
    def __init__(self, state_writer: StateWriter):
        super().__init__()
        self.state_writer = state_writer

    def emit(self, record: logging.LogRecord):
        try:
            self.state_writer.add_log(record.levelname, self.format(record))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Daemon
# ---------------------------------------------------------------------------

class PolymarketSniperDaemon:

    def __init__(self, config_path: str, mode: str):
        self.config_path = config_path
        self.mode = mode
        self.cfg = load_config(config_path)

        # Override mode from CLI
        self.cfg.setdefault("daemon", {}).setdefault("execution", {})["mode"] = mode

        # Bankroll state
        self._bankroll = float(
            self.cfg.get("trading", {}).get("initial_bankroll", 1000.0)
        )
        self._start_bankroll = self._bankroll
        self._bankroll_lock = threading.Lock()

        # Components
        self.notifier = NotificationManager(self.cfg)
        self.learning = SelfLearningEngine(self.cfg)
        self.state_writer = StateWriter(
            self.cfg.get("daemon", {}).get("state_file", "data/daemon_state.json")
        )

        # Import data client and Kronos adapter
        from utils.polymarket_client import PolymarketDataClient
        from models.kronos_adapter import KronosForecastAdapter
        self.data_client = PolymarketDataClient(self.cfg)
        self.kronos = KronosForecastAdapter(self.cfg)

        # Supervisor
        self.supervisor = AgentSupervisor(
            config=self.cfg,
            data_client=self.data_client,
            kronos_adapter=self.kronos,
            notifier=self.notifier,
            learning_engine=self.learning,
            bankroll_getter=self._get_bankroll,
            bankroll_setter=self._set_bankroll,
        )

        # Register state getters
        self._start_time = datetime.now(timezone.utc)
        self.state_writer.register_getter("mode", lambda: mode)
        self.state_writer.register_getter("status", lambda: "running")
        self.state_writer.register_getter("bankroll", self._get_bankroll)
        self.state_writer.register_getter("start_bankroll", lambda: self._start_bankroll)
        self.state_writer.register_getter("daily_pnl", lambda: 0.0)
        self.state_writer.register_getter("uptime_hours", self._get_uptime_hours)
        self.state_writer.register_getter("fleet_status", self.supervisor.get_fleet_status)
        self.state_writer.register_getter("recent_opportunities", self._get_recent_opps)
        self.state_writer.register_getter("scanner_stats", lambda: {})
        self.state_writer.register_getter("execution_stats", lambda: {})

        self._recent_opps = []
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Bankroll management
    # ------------------------------------------------------------------

    def _get_bankroll(self) -> float:
        with self._bankroll_lock:
            return self._bankroll

    def _set_bankroll(self, val: float):
        with self._bankroll_lock:
            self._bankroll = max(0.0, val)

    def _get_uptime_hours(self) -> float:
        delta = datetime.now(timezone.utc) - self._start_time
        return delta.total_seconds() / 3600

    def _get_recent_opps(self):
        return self._recent_opps[-10:]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        logger.info("=" * 60)
        logger.info("POLYMARKET SNIPER DAEMON STARTING")
        logger.info("Mode: %s | Bankroll: $%.2f", self.mode.upper(), self._bankroll)
        logger.info("=" * 60)

        # Start state writer
        self.state_writer.start()

        # Add log handler to feed dashboard
        state_handler = StateLogHandler(self.state_writer)
        state_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(state_handler)

        # Start supervisor (which starts all sub-agents)
        self.supervisor.start()

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        logger.info("Daemon fully started. Press Ctrl+C to stop.")

        # Keep main thread alive
        try:
            while not self._stop_event.is_set():
                time.sleep(5)
                self._run_learning_cycle()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        logger.info("Daemon shutting down...")
        self._stop_event.set()
        self.supervisor.stop()
        self.state_writer.stop()

        # Save learning state
        try:
            self.learning.save_checkpoint()
        except Exception:
            pass

        logger.info("Daemon stopped. Final bankroll: $%.2f", self._get_bankroll())

    def _handle_shutdown(self, signum, frame):
        logger.info("Received signal %d. Initiating graceful shutdown...", signum)
        self._stop_event.set()

    def _run_learning_cycle(self):
        """Run the self-learning cycle periodically."""
        try:
            self.learning.run_learning_cycle()
        except Exception as exc:
            logger.debug("Learning cycle error: %s", exc)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Sniper Daemon — Autonomous 24/7 Trading Agent"
    )
    parser.add_argument(
        "--mode",
        choices=["dry_run", "paper", "live"],
        default="dry_run",
        help="Execution mode (default: dry_run)",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to config file (default: config/config.yaml)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the live terminal dashboard instead of the daemon",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--test-notifications",
        action="store_true",
        help="Send a test notification to all configured channels and exit",
    )

    args = parser.parse_args()

    # Change to project root
    os.chdir(_ROOT)

    _setup_logging(level=args.log_level)

    if args.dashboard:
        from daemon.web.dashboard import Dashboard
        cfg = load_config(args.config)
        state_file = cfg.get("daemon", {}).get("state_file", "data/daemon_state.json")
        Dashboard(state_file=state_file).run()
        return

    if args.test_notifications:
        cfg = load_config(args.config)
        notifier = NotificationManager(cfg)
        notifier.test()
        print("Test notifications sent.")
        return

    daemon = PolymarketSniperDaemon(config_path=args.config, mode=args.mode)
    daemon.start()


if __name__ == "__main__":
    main()
