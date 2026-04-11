"""
Autonomous Execution Engine
============================
Consumes SniperOpportunity objects from the queue and executes trades on
Polymarket via the CLOB API.

Modes:
  DRY_RUN  — logs everything, executes nothing (safe for testing)
  PAPER    — simulates fills against real prices, tracks virtual P&L
  LIVE     — submits real orders via the CLOB API (requires API key + wallet)

Risk controls applied before every execution:
  1. Daily loss limit     — halt if daily P&L < -max_daily_loss_pct
  2. Max concurrent bets  — never hold more than N open positions
  3. Max single bet       — hard cap in USDC
  4. Duplicate check      — never bet on the same market twice while open
  5. Confidence gate      — re-score at execution time (price may have moved)
  6. Bankroll floor       — never bet below minimum bankroll threshold
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from daemon.core.sniper_scorer import SniperOpportunity

logger = logging.getLogger("daemon.executor")


class ExecutionMode(str, Enum):
    DRY_RUN = "dry_run"
    PAPER   = "paper"
    LIVE    = "live"


@dataclass
class Position:
    """An open or closed position."""
    position_id: str
    market_id: str
    market_title: str
    side: str                    # YES or NO
    entry_price: float
    size_usdc: float
    shares: float
    sniper_score: float
    archetype_match: Optional[str]
    opened_at: str
    mode: str
    status: str = "open"         # open | closed | cancelled
    exit_price: Optional[float] = None
    pnl_usdc: Optional[float] = None
    pnl_pct: Optional[float] = None
    closed_at: Optional[str] = None
    resolution: Optional[str] = None  # WIN | LOSS | PUSH

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExecutionEngine:
    """
    Pulls opportunities from the queue and executes them according to
    the configured mode and risk controls.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        opportunity_queue: queue.Queue,
        notifier,               # NotificationManager
        learning_engine,        # SelfLearningEngine
        bankroll_getter: Callable[[], float],
        bankroll_setter: Callable[[float], None],
        data_client,            # PolymarketDataClient
    ):
        self.cfg = config
        self.opp_queue = opportunity_queue
        self.notifier = notifier
        self.learning = learning_engine
        self.bankroll_getter = bankroll_getter
        self.bankroll_setter = bankroll_setter
        self.data_client = data_client

        exec_cfg = config.get("daemon", {}).get("execution", {})
        mode_str = exec_cfg.get("mode", "dry_run")
        self.mode = ExecutionMode(mode_str)

        # Risk controls
        self.max_daily_loss_pct = exec_cfg.get("max_daily_loss_pct", 0.20)
        self.max_concurrent_positions = exec_cfg.get("max_concurrent_positions", 5)
        self.max_bet_usdc = exec_cfg.get("max_bet_usdc", 500.0)
        self.min_bankroll_floor = exec_cfg.get("min_bankroll_floor", 100.0)
        self.min_sniper_score = exec_cfg.get("min_sniper_score", 60.0)
        self.re_score_threshold = exec_cfg.get("re_score_threshold", 0.05)  # price drift tolerance

        # State
        self._open_positions: Dict[str, Position] = {}  # market_id -> Position
        self._closed_positions: List[Position] = []
        self._daily_pnl: float = 0.0
        self._daily_reset_date: str = datetime.now(timezone.utc).date().isoformat()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Persistence
        self._positions_file = Path(config.get("daemon", {}).get(
            "positions_file", "data/positions.jsonl"))
        self._positions_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_positions()

        logger.info("ExecutionEngine initialized in %s mode", self.mode.value.upper())

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._execution_loop,
            name="ExecutionEngine",
            daemon=True,
        )
        self._thread.start()
        logger.info("ExecutionEngine started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=15)
        logger.info("ExecutionEngine stopped")

    # ------------------------------------------------------------------
    # Execution loop
    # ------------------------------------------------------------------

    def _execution_loop(self):
        logger.info("Execution loop started in %s mode", self.mode.value.upper())
        while not self._stop_event.is_set():
            try:
                opp: SniperOpportunity = self.opp_queue.get(timeout=2.0)
                self._process_opportunity(opp)
                self.opp_queue.task_done()
            except queue.Empty:
                # Check for position resolutions while idle
                self._check_resolutions()
                self._reset_daily_pnl_if_needed()
            except Exception as exc:
                logger.error("Execution loop error: %s", exc, exc_info=True)

    # ------------------------------------------------------------------
    # Opportunity processing
    # ------------------------------------------------------------------

    def _process_opportunity(self, opp: SniperOpportunity):
        """Apply all risk checks and execute if approved."""
        market_id = opp.market_id

        # ── Risk Gate 1: Daily loss limit ────────────────────────────
        bankroll = self.bankroll_getter()
        if self._daily_pnl < -(bankroll * self.max_daily_loss_pct):
            logger.warning("Daily loss limit hit (%.2f). Skipping %s",
                           self._daily_pnl, market_id)
            self.notifier.send(
                title="⛔ Daily Loss Limit Hit",
                body=f"Daily P&L: ${self._daily_pnl:.2f}. Trading halted for today.",
                level="critical",
            )
            return

        # ── Risk Gate 2: Bankroll floor ──────────────────────────────
        if bankroll < self.min_bankroll_floor:
            logger.warning("Bankroll below floor ($%.2f). Skipping.", bankroll)
            return

        # ── Risk Gate 3: Max concurrent positions ────────────────────
        with self._lock:
            open_count = len(self._open_positions)
        if open_count >= self.max_concurrent_positions:
            logger.info("Max concurrent positions (%d) reached. Queuing %s.",
                        self.max_concurrent_positions, market_id)
            return

        # ── Risk Gate 4: Duplicate check ─────────────────────────────
        with self._lock:
            if market_id in self._open_positions:
                logger.debug("Already have open position in %s", market_id)
                return

        # ── Risk Gate 5: Sniper score gate ───────────────────────────
        if opp.sniper_score < self.min_sniper_score:
            logger.debug("Score %.1f below threshold %.1f", opp.sniper_score, self.min_sniper_score)
            return

        # ── Risk Gate 6: Re-score (check price hasn't moved) ─────────
        try:
            live_price = self._get_live_price(market_id)
            if live_price and abs(live_price - opp.current_price) > self.re_score_threshold:
                logger.info("Price drifted %.3f → %.3f for %s. Skipping stale opportunity.",
                            opp.current_price, live_price, market_id)
                return
        except Exception:
            pass  # If we can't re-price, proceed with original score

        # ── Compute final bet size ────────────────────────────────────
        bet_size = min(opp.recommended_size_usdc, self.max_bet_usdc, bankroll * 0.04)
        if bet_size < 5.0:
            logger.debug("Bet size $%.2f too small. Skipping.", bet_size)
            return

        # ── Execute ───────────────────────────────────────────────────
        self._execute(opp, bet_size)

    def _execute(self, opp: SniperOpportunity, bet_size: float):
        """Execute the trade in the configured mode."""
        position_id = str(uuid.uuid4())[:8]
        shares = bet_size / opp.current_price if opp.recommended_side == "YES" \
                 else bet_size / (1 - opp.current_price)

        position = Position(
            position_id=position_id,
            market_id=opp.market_id,
            market_title=opp.market_title,
            side=opp.recommended_side,
            entry_price=opp.current_price if opp.recommended_side == "YES" \
                        else 1 - opp.current_price,
            size_usdc=bet_size,
            shares=shares,
            sniper_score=opp.sniper_score,
            archetype_match=opp.archetype_match,
            opened_at=datetime.now(timezone.utc).isoformat(),
            mode=self.mode.value,
        )

        if self.mode == ExecutionMode.LIVE:
            success = self._submit_live_order(opp, bet_size)
            if not success:
                logger.error("Live order submission failed for %s", opp.market_id)
                return
        elif self.mode == ExecutionMode.PAPER:
            # Deduct from virtual bankroll
            new_bankroll = self.bankroll_getter() - bet_size
            self.bankroll_setter(new_bankroll)
            logger.info("[PAPER] Executed %s %s @ %.3f | size=$%.2f | score=%.1f",
                        position.side, opp.market_title[:50],
                        position.entry_price, bet_size, opp.sniper_score)
        else:  # DRY_RUN
            logger.info("[DRY RUN] Would execute %s %s @ %.3f | size=$%.2f | score=%.1f",
                        position.side, opp.market_title[:50],
                        position.entry_price, bet_size, opp.sniper_score)

        # Register position
        with self._lock:
            self._open_positions[opp.market_id] = position
        self._persist_position(position)

        # Notify user
        archetype_label = f"[{opp.archetype_match.upper()}] " if opp.archetype_match else ""
        self.notifier.send(
            title=f"{'🎯' if self.mode == ExecutionMode.LIVE else '📋'} "
                  f"{'LIVE' if self.mode == ExecutionMode.LIVE else self.mode.value.upper()} BET PLACED",
            body=(
                f"{archetype_label}{opp.market_title[:80]}\n"
                f"Side: {opp.recommended_side} @ {opp.current_price:.3f} | "
                f"Size: ${bet_size:.2f} | Score: {opp.sniper_score:.1f} | "
                f"Edge: {opp.edge:.3f}"
            ),
            level="info",
            data=opp.to_dict(),
        )

        # Register with self-learning engine
        try:
            from learning.self_learning import TradeRecord
            record = TradeRecord(
                trade_id=position_id,
                market_id=opp.market_id,
                market_title=opp.market_title,
                strategy=opp.archetype_match or "sniper",
                action=f"BUY_{opp.recommended_side}",
                entry_price=position.entry_price,
                position_size=bet_size / self.bankroll_getter(),
                entry_time=position.opened_at,
                edge_estimate=opp.edge,
                confidence=opp.confidence,
                model_predicted_price=opp.model_probability,
            )
            self.learning.record_trade(record)
        except Exception as exc:
            logger.debug("Learning record failed: %s", exc)

    def _submit_live_order(self, opp: SniperOpportunity, bet_size: float) -> bool:
        """Submit a real order to Polymarket CLOB."""
        try:
            result = self.data_client.place_order(
                market_id=opp.market_id,
                side=opp.recommended_side,
                size_usdc=bet_size,
                price=opp.current_price if opp.recommended_side == "YES"
                      else 1 - opp.current_price,
            )
            logger.info("Live order submitted: %s", result)
            return True
        except Exception as exc:
            logger.error("Live order failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Position resolution monitoring
    # ------------------------------------------------------------------

    def _check_resolutions(self):
        """Check if any open positions have resolved."""
        with self._lock:
            open_ids = list(self._open_positions.keys())

        for market_id in open_ids:
            try:
                market = self.data_client.get_market(market_id)
                if not market:
                    continue
                resolved = market.get("resolved", False) or market.get("closed", False)
                if resolved:
                    self._close_position(market_id, market)
            except Exception as exc:
                logger.debug("Resolution check failed for %s: %s", market_id, exc)

    def _close_position(self, market_id: str, market_data: Dict[str, Any]):
        """Close a resolved position and compute P&L."""
        with self._lock:
            position = self._open_positions.pop(market_id, None)
        if not position:
            return

        # Determine outcome
        resolution_outcome = market_data.get("resolutionOutcome", "")
        winner = str(resolution_outcome).upper()

        if winner == position.side:
            # WIN: shares settle at $1.00
            pnl = position.shares * (1.0 - position.entry_price)
            resolution = "WIN"
        elif winner in ("YES", "NO") and winner != position.side:
            # LOSS: shares go to $0
            pnl = -position.size_usdc
            resolution = "LOSS"
        else:
            pnl = 0.0
            resolution = "PUSH"

        position.exit_price = 1.0 if resolution == "WIN" else 0.0
        position.pnl_usdc = round(pnl, 4)
        position.pnl_pct = round(pnl / position.size_usdc * 100, 2)
        position.closed_at = datetime.now(timezone.utc).isoformat()
        position.resolution = resolution
        position.status = "closed"

        self._closed_positions.append(position)
        self._persist_position(position)

        # Update bankroll (paper/live modes)
        if self.mode in (ExecutionMode.PAPER, ExecutionMode.LIVE):
            new_bankroll = self.bankroll_getter() + position.size_usdc + pnl
            self.bankroll_setter(new_bankroll)
            self._daily_pnl += pnl

        # Update learning engine
        try:
            self.learning.record_resolution(
                trade_id=position.position_id,
                exit_price=position.exit_price,
                pnl=pnl,
                outcome=resolution,
            )
        except Exception:
            pass

        # Notify
        emoji = "✅" if resolution == "WIN" else ("❌" if resolution == "LOSS" else "➖")
        self.notifier.send(
            title=f"{emoji} Position {resolution}: {position.market_title[:50]}",
            body=(
                f"Side: {position.side} | P&L: ${pnl:+.2f} ({position.pnl_pct:+.1f}%)\n"
                f"Bankroll: ${self.bankroll_getter():.2f}"
            ),
            level="success" if resolution == "WIN" else "warning",
        )

        logger.info(
            "%s CLOSED: %s | %s | P&L=$%+.2f (%.1f%%)",
            resolution, position.market_title[:60], position.side,
            pnl, position.pnl_pct,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist_position(self, position: Position):
        try:
            with open(self._positions_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(position.to_dict()) + "\n")
        except Exception as exc:
            logger.debug("Position persist failed: %s", exc)

    def _load_positions(self):
        """Load open positions from disk on startup."""
        if not self._positions_file.exists():
            return
        try:
            with open(self._positions_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("status") == "open":
                        pos = Position(**data)
                        self._open_positions[pos.market_id] = pos
            logger.info("Loaded %d open positions from disk", len(self._open_positions))
        except Exception as exc:
            logger.warning("Failed to load positions: %s", exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_live_price(self, market_id: str) -> Optional[float]:
        try:
            market = self.data_client.get_market(market_id)
            if market:
                from daemon.core.sniper_scorer import SniperScorer
                scorer = SniperScorer(self.cfg)
                return scorer._extract_yes_price(market)
        except Exception:
            pass
        return None

    def _reset_daily_pnl_if_needed(self):
        today = datetime.now(timezone.utc).date().isoformat()
        if today != self._daily_reset_date:
            logger.info("Daily P&L reset (was $%.2f)", self._daily_pnl)
            self._daily_pnl = 0.0
            self._daily_reset_date = today

    # ------------------------------------------------------------------
    # Public state access
    # ------------------------------------------------------------------

    def get_open_positions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [p.to_dict() for p in self._open_positions.values()]

    def get_closed_positions(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._closed_positions[-100:]]

    def get_stats(self) -> Dict[str, Any]:
        closed = self._closed_positions
        wins = [p for p in closed if p.resolution == "WIN"]
        losses = [p for p in closed if p.resolution == "LOSS"]
        total_pnl = sum(p.pnl_usdc or 0 for p in closed)
        return {
            "mode": self.mode.value,
            "open_positions": len(self._open_positions),
            "closed_positions": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / max(1, len(wins) + len(losses)),
            "total_pnl_usdc": round(total_pnl, 2),
            "daily_pnl_usdc": round(self._daily_pnl, 2),
            "bankroll": round(self.bankroll_getter(), 2),
        }
