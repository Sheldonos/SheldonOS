"""
Autonomous Market Scanner
=========================
Runs as a background thread, continuously polling Polymarket for new markets
and price updates. Feeds data to the SniperScorer and emits scored
opportunities to the execution queue.

Scan cycle:
  1. Fetch all active markets (Gamma API)
  2. For each market, fetch price history + whale data (CLOB / polyterm)
  3. Run Kronos forecast on top-volume markets
  4. Score all markets via SniperScorer
  5. Emit actionable opportunities to the execution queue
  6. Sleep for scan_interval seconds, then repeat

The scanner also maintains a deduplication cache so the same opportunity
is not emitted twice within the cooldown window.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from daemon.core.sniper_scorer import SniperScorer, SniperOpportunity

logger = logging.getLogger("daemon.market_scanner")


class MarketScanner:
    """
    Background market scanner. Emits SniperOpportunity objects to a queue.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        data_client,           # PolymarketDataClient
        kronos_adapter,        # KronosForecastAdapter
        opportunity_queue: queue.Queue,
        bankroll_getter: Callable[[], float],
    ):
        self.cfg = config
        self.data_client = data_client
        self.kronos = kronos_adapter
        self.opp_queue = opportunity_queue
        self.bankroll_getter = bankroll_getter

        scan_cfg = config.get("daemon", {}).get("scanner", {})
        self.scan_interval = scan_cfg.get("scan_interval_seconds", 60)
        self.max_markets_per_scan = scan_cfg.get("max_markets_per_scan", 300)
        self.kronos_top_n = scan_cfg.get("kronos_top_n_markets", 50)
        self.cooldown_seconds = scan_cfg.get("opportunity_cooldown_seconds", 300)
        self.categories = scan_cfg.get("categories", [
            "sports", "soccer", "crypto", "politics", "world", "tech"
        ])

        self.scorer = SniperScorer(config)

        # Deduplication: market_id -> last_emitted_timestamp
        self._emitted: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Stats
        self.stats = {
            "total_scans": 0,
            "total_markets_scanned": 0,
            "total_opportunities_emitted": 0,
            "last_scan_time": None,
            "last_scan_duration_s": 0.0,
            "errors": 0,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Start the background scanner thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Scanner already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._scan_loop,
            name="MarketScanner",
            daemon=True,
        )
        self._thread.start()
        logger.info("MarketScanner started (interval=%ds)", self.scan_interval)

    def stop(self):
        """Signal the scanner to stop after the current scan."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=30)
        logger.info("MarketScanner stopped")

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Main scan loop
    # ------------------------------------------------------------------

    def _scan_loop(self):
        logger.info("Scan loop started")
        while not self._stop_event.is_set():
            scan_start = time.time()
            try:
                self._run_scan()
                self.stats["total_scans"] += 1
                self.stats["last_scan_time"] = datetime.now(timezone.utc).isoformat()
                self.stats["last_scan_duration_s"] = round(time.time() - scan_start, 2)
                logger.info(
                    "Scan #%d complete in %.1fs | markets=%d | emitted=%d",
                    self.stats["total_scans"],
                    self.stats["last_scan_duration_s"],
                    self.stats["total_markets_scanned"],
                    self.stats["total_opportunities_emitted"],
                )
            except Exception as exc:
                self.stats["errors"] += 1
                logger.error("Scan loop error: %s", exc, exc_info=True)

            # Sleep in small increments so stop_event is checked promptly
            elapsed = time.time() - scan_start
            remaining = max(0, self.scan_interval - elapsed)
            self._interruptible_sleep(remaining)

        logger.info("Scan loop exited")

    def _run_scan(self):
        """Execute one full scan cycle."""
        bankroll = self.bankroll_getter()

        # ── 1. Fetch active markets ──────────────────────────────────
        try:
            markets = self.data_client.get_active_markets(
                limit=self.max_markets_per_scan,
                categories=self.categories,
                min_liquidity=self.cfg.get("sniper", {}).get("min_liquidity", 5_000),
                min_volume_24h=500.0,
            )
        except Exception as exc:
            logger.warning("Failed to fetch markets: %s", exc)
            markets = []

        if not markets:
            logger.debug("No markets returned from API")
            return

        self.stats["total_markets_scanned"] += len(markets)

        # ── 2. Fetch price histories (batch) ─────────────────────────
        price_histories: Dict[str, List[float]] = {}
        for market in markets[:self.kronos_top_n]:
            mid = market.get("id", "")
            tokens = market.get("tokens", [])
            if tokens and isinstance(tokens, list):
                token_id = tokens[0].get("token_id", "") if isinstance(tokens[0], dict) else ""
                if token_id:
                    try:
                        hist = self.data_client.get_price_history(token_id, interval="1h")
                        if hist:
                            price_histories[mid] = [float(h.get("p", h.get("price", 0.5)))
                                                    for h in hist[-24:]]
                    except Exception:
                        pass

        # ── 3. Kronos forecasts (top N markets by volume) ────────────
        kronos_forecasts: Dict[str, Dict] = {}
        top_markets = sorted(
            markets,
            key=lambda m: float(m.get("volume24hr", m.get("volume", 0)) or 0),
            reverse=True,
        )[:self.kronos_top_n]

        for market in top_markets:
            mid = market.get("id", "")
            ph = price_histories.get(mid, [])
            if len(ph) >= 5:
                try:
                    forecast = self.kronos.forecast(
                        price_history=ph,
                        market_metadata=market,
                    )
                    if forecast:
                        kronos_forecasts[mid] = forecast
                except Exception as exc:
                    logger.debug("Kronos forecast failed for %s: %s", mid, exc)

        # ── 4. Whale data ────────────────────────────────────────────
        whale_data: Dict[str, Dict] = {}
        try:
            whale_signals = self.data_client.get_whale_signals(
                market_ids=[m.get("id", "") for m in markets[:50]]
            )
            whale_data = whale_signals or {}
        except Exception as exc:
            logger.debug("Whale data fetch failed: %s", exc)

        # ── 5. Score all markets ─────────────────────────────────────
        opportunities = self.scorer.score_markets(
            markets=markets,
            bankroll_usdc=bankroll,
            kronos_forecasts=kronos_forecasts,
            whale_data=whale_data,
            price_histories=price_histories,
        )

        # ── 6. Emit actionable opportunities ─────────────────────────
        now = time.time()
        emitted_count = 0
        for opp in opportunities:
            if not opp.is_actionable:
                continue
            with self._lock:
                last_emitted = self._emitted.get(opp.market_id, 0)
                if now - last_emitted < self.cooldown_seconds:
                    continue
                self._emitted[opp.market_id] = now

            try:
                self.opp_queue.put_nowait(opp)
                emitted_count += 1
                self.stats["total_opportunities_emitted"] += 1
                logger.info(
                    "🎯 OPPORTUNITY: [%s] %s | score=%.1f | edge=%.3f | side=%s | size=$%.2f",
                    opp.archetype_match or "generic",
                    opp.market_title[:60],
                    opp.sniper_score,
                    opp.edge,
                    opp.recommended_side,
                    opp.recommended_size_usdc,
                )
            except queue.Full:
                logger.warning("Opportunity queue full — dropping %s", opp.market_id)

    def _interruptible_sleep(self, seconds: float):
        """Sleep in 1-second increments, checking stop_event each time."""
        end = time.time() + seconds
        while time.time() < end and not self._stop_event.is_set():
            time.sleep(min(1.0, end - time.time()))

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)
