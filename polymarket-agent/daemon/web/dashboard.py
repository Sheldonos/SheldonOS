"""
Live Terminal Dashboard
=======================
A Rich-powered live TUI dashboard that displays the daemon's real-time state.
Runs in the foreground when the user wants to monitor the agent.
The daemon itself runs as a background process; the dashboard just reads
the shared state file and renders it.

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  POLYMARKET SNIPER DAEMON  •  [MODE]  •  [STATUS]       │
  ├──────────────────┬──────────────────────────────────────┤
  │  BANKROLL        │  PERFORMANCE SUMMARY                 │
  │  OPEN POSITIONS  │  RECENT OPPORTUNITIES                │
  ├──────────────────┴──────────────────────────────────────┤
  │  LIVE LOG FEED                                          │
  └─────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.columns import Columns
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Dashboard:
    """
    Live terminal dashboard. Reads state from the daemon's state file
    and renders it using Rich.
    """

    def __init__(self, state_file: str = "data/daemon_state.json"):
        self.state_file = Path(state_file)
        self.console = Console() if RICH_AVAILABLE else None
        self.refresh_rate = 2  # seconds

    def run(self):
        """Run the live dashboard. Blocks until Ctrl+C."""
        if not RICH_AVAILABLE:
            print("Rich not installed. Run: pip install rich")
            self._run_plain()
            return

        with Live(
            self._render(),
            console=self.console,
            refresh_per_second=1 / self.refresh_rate,
            screen=True,
        ) as live:
            try:
                while True:
                    time.sleep(self.refresh_rate)
                    live.update(self._render())
            except KeyboardInterrupt:
                pass

    def _run_plain(self):
        """Fallback plain-text dashboard."""
        while True:
            state = self._load_state()
            print("\033[2J\033[H")  # clear screen
            print("=" * 60)
            print("POLYMARKET SNIPER DAEMON")
            print("=" * 60)
            if state:
                print(json.dumps(state, indent=2))
            else:
                print("Daemon not running or state file not found.")
            time.sleep(self.refresh_rate)

    def _load_state(self) -> Optional[Dict[str, Any]]:
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def _render(self):
        state = self._load_state()
        if not state:
            return Panel(
                "[yellow]Waiting for daemon to start...[/yellow]\n"
                f"State file: {self.state_file}",
                title="[bold red]POLYMARKET SNIPER DAEMON[/bold red]",
                border_style="red",
            )

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="log", size=12),
        )
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        # ── Header ───────────────────────────────────────────────────
        mode = state.get("mode", "unknown").upper()
        status = state.get("status", "unknown")
        uptime = state.get("uptime_hours", 0)
        mode_color = {"DRY_RUN": "yellow", "PAPER": "cyan", "LIVE": "green"}.get(mode, "white")
        status_color = "green" if status == "running" else "red"

        header_text = Text()
        header_text.append("🎯 POLYMARKET SNIPER DAEMON  ", style="bold white")
        header_text.append(f"[{mode}]", style=f"bold {mode_color}")
        header_text.append(f"  [{status.upper()}]", style=f"bold {status_color}")
        header_text.append(f"  Uptime: {uptime:.1f}h", style="dim white")
        layout["header"].update(Panel(header_text, border_style=mode_color))

        # ── Left panel: Bankroll + Open Positions ────────────────────
        bankroll = state.get("bankroll", 0)
        start_bankroll = state.get("start_bankroll", 1000)
        pnl_total = bankroll - start_bankroll
        pnl_pct = (pnl_total / start_bankroll * 100) if start_bankroll > 0 else 0
        daily_pnl = state.get("daily_pnl", 0)

        pnl_color = "green" if pnl_total >= 0 else "red"
        daily_color = "green" if daily_pnl >= 0 else "red"

        bankroll_text = (
            f"[bold white]Bankroll:[/bold white] [bold green]${bankroll:,.2f}[/bold green]\n"
            f"[bold white]All-Time P&L:[/bold white] [{pnl_color}]${pnl_total:+,.2f} ({pnl_pct:+.1f}%)[/{pnl_color}]\n"
            f"[bold white]Today's P&L:[/bold white] [{daily_color}]${daily_pnl:+,.2f}[/{daily_color}]\n"
        )

        # Open positions table
        open_pos = state.get("open_positions", [])
        pos_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        pos_table.add_column("Market", max_width=30, no_wrap=True)
        pos_table.add_column("Side", width=5)
        pos_table.add_column("Entry", width=7)
        pos_table.add_column("Size", width=8)
        pos_table.add_column("Score", width=6)

        for pos in open_pos[:5]:
            side_color = "green" if pos.get("side") == "YES" else "red"
            pos_table.add_row(
                pos.get("market_title", "")[:30],
                f"[{side_color}]{pos.get('side', '')}[/{side_color}]",
                f"{pos.get('entry_price', 0):.3f}",
                f"${pos.get('size_usdc', 0):.0f}",
                f"{pos.get('sniper_score', 0):.0f}",
            )

        if not open_pos:
            pos_table.add_row("[dim]No open positions[/dim]", "", "", "", "")

        left_content = (
            bankroll_text + "\n[bold cyan]OPEN POSITIONS[/bold cyan]\n"
        )
        layout["left"].update(Panel(
            Text.from_markup(left_content) if not open_pos else
            Columns([Text.from_markup(bankroll_text), pos_table]),
            title="[bold]💰 PORTFOLIO[/bold]",
            border_style="green",
        ))

        # ── Right panel: Performance + Recent Opportunities ──────────
        exec_stats = state.get("execution_stats", {})
        scan_stats = state.get("scanner_stats", {})

        wins = exec_stats.get("wins", 0)
        losses = exec_stats.get("losses", 0)
        win_rate = exec_stats.get("win_rate", 0)
        total_scans = scan_stats.get("total_scans", 0)
        total_opps = scan_stats.get("total_opportunities_emitted", 0)

        perf_text = (
            f"[bold white]Win Rate:[/bold white] [bold green]{win_rate:.1%}[/bold green]  "
            f"[dim]({wins}W / {losses}L)[/dim]\n"
            f"[bold white]Scans:[/bold white] {total_scans}  "
            f"[bold white]Opportunities:[/bold white] {total_opps}\n"
            f"[bold white]Last Scan:[/bold white] {scan_stats.get('last_scan_time', 'N/A')}\n"
        )

        # Recent opportunities table
        recent_opps = state.get("recent_opportunities", [])
        opp_table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
        opp_table.add_column("Market", max_width=28, no_wrap=True)
        opp_table.add_column("Score", width=6)
        opp_table.add_column("Edge", width=6)
        opp_table.add_column("Side", width=5)
        opp_table.add_column("Archetype", width=14)

        for opp in recent_opps[:6]:
            score = opp.get("sniper_score", 0)
            score_color = "green" if score >= 75 else ("yellow" if score >= 60 else "red")
            side_color = "green" if opp.get("recommended_side") == "YES" else "red"
            opp_table.add_row(
                opp.get("market_title", "")[:28],
                f"[{score_color}]{score:.0f}[/{score_color}]",
                f"{opp.get('edge', 0):.3f}",
                f"[{side_color}]{opp.get('recommended_side', '')}[/{side_color}]",
                opp.get("archetype_match") or "generic",
            )

        if not recent_opps:
            opp_table.add_row("[dim]Scanning...[/dim]", "", "", "", "")

        right_content = perf_text + "\n[bold magenta]RECENT OPPORTUNITIES[/bold magenta]\n"
        layout["right"].update(Panel(
            Columns([Text.from_markup(right_content), opp_table]),
            title="[bold]📊 PERFORMANCE[/bold]",
            border_style="magenta",
        ))

        # ── Log feed ─────────────────────────────────────────────────
        log_entries = state.get("recent_log", [])
        log_text = Text()
        for entry in log_entries[-10:]:
            level = entry.get("level", "INFO")
            msg = entry.get("message", "")
            ts = entry.get("time", "")
            level_style = {
                "INFO": "dim white", "WARNING": "yellow",
                "ERROR": "red", "CRITICAL": "bold red",
            }.get(level, "white")
            log_text.append(f"[{ts}] ", style="dim")
            log_text.append(f"{level:<8}", style=level_style)
            log_text.append(f" {msg}\n", style="white")

        layout["log"].update(Panel(
            log_text if log_entries else Text("[dim]Waiting for log entries...[/dim]"),
            title="[bold]📋 LIVE LOG[/bold]",
            border_style="dim",
        ))

        return layout
