"""
Self-Learning Engine
====================
Continuously improves strategy weights, signal thresholds, and Kelly fractions
based on resolved trade outcomes. Integrates MiroFish's graph-memory pattern
for persistent knowledge accumulation across agent generations.

Learning mechanisms:
1. Outcome Tracker    — records every trade and its resolution
2. Performance Scorer — computes per-strategy win rate, Sharpe, edge accuracy
3. Weight Adapter     — adjusts ensemble weights via exponential moving average
4. Threshold Tuner    — tunes min_edge and min_confidence via Bayesian optimisation
5. Memory Compressor  — summarises old episodes into compact knowledge (MiroFish)
6. Persistence Layer  — JSONL append-only log + periodic JSON checkpoint
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("polymarket.self_learning")


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TradeRecord:
    """Single trade lifecycle record."""
    trade_id: str
    market_id: str
    market_title: str
    strategy: str
    action: str                  # BUY_YES / BUY_NO
    entry_price: float
    position_size: float         # fraction of bankroll
    entry_time: str
    edge_estimate: float
    confidence: float
    model_predicted_price: float
    # Filled on resolution
    exit_price: Optional[float] = None
    pnl: Optional[float] = None  # absolute P&L in USDC
    pnl_pct: Optional[float] = None
    resolved: bool = False
    resolution_time: Optional[str] = None
    outcome: Optional[str] = None  # WIN / LOSS / PUSH

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StrategyPerformance:
    """Aggregated performance metrics for one strategy."""
    strategy: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    total_pnl: float = 0.0
    total_edge_estimate: float = 0.0
    total_actual_edge: float = 0.0
    returns: List[float] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        settled = self.wins + self.losses
        return self.wins / settled if settled > 0 else 0.5

    @property
    def avg_pnl(self) -> float:
        return self.total_pnl / max(self.total_trades, 1)

    @property
    def sharpe_ratio(self) -> float:
        if len(self.returns) < 5:
            return 0.0
        arr = np.array(self.returns)
        std = np.std(arr)
        return float(np.mean(arr) / std * math.sqrt(252)) if std > 0 else 0.0

    @property
    def edge_accuracy(self) -> float:
        """How accurate were our edge estimates vs actual outcomes?"""
        if self.total_trades == 0:
            return 0.0
        return self.total_actual_edge / max(self.total_edge_estimate, 0.001)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "pushes": self.pushes,
            "win_rate": round(self.win_rate, 4),
            "total_pnl": round(self.total_pnl, 4),
            "avg_pnl": round(self.avg_pnl, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "edge_accuracy": round(self.edge_accuracy, 4),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Outcome Tracker
# ──────────────────────────────────────────────────────────────────────────────

class OutcomeTracker:
    """
    Append-only JSONL log of all trades.
    Supports fast lookup by trade_id and market_id.
    """

    def __init__(self, log_path: str = "logs/trades.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._trades: Dict[str, TradeRecord] = {}
        self._load_existing()

    def record_entry(self, record: TradeRecord) -> None:
        """Record a new trade entry."""
        self._trades[record.trade_id] = record
        self._append(record.to_dict())
        logger.info("Trade entry recorded: %s %s @ %.3f", record.action, record.market_id, record.entry_price)

    def record_resolution(
        self,
        trade_id: str,
        exit_price: float,
        outcome: str,
    ) -> Optional[TradeRecord]:
        """Mark a trade as resolved and compute P&L."""
        rec = self._trades.get(trade_id)
        if rec is None:
            logger.warning("Trade %s not found for resolution", trade_id)
            return None

        rec.exit_price = exit_price
        rec.resolved = True
        rec.resolution_time = datetime.utcnow().isoformat()
        rec.outcome = outcome

        # P&L calculation for binary prediction market
        if rec.action == "BUY_YES":
            rec.pnl_pct = (exit_price - rec.entry_price) / rec.entry_price
        else:  # BUY_NO
            no_entry = 1.0 - rec.entry_price
            no_exit = 1.0 - exit_price
            rec.pnl_pct = (no_exit - no_entry) / no_entry if no_entry > 0 else 0.0

        rec.pnl = rec.pnl_pct * rec.position_size

        self._append(rec.to_dict())
        logger.info("Trade resolved: %s outcome=%s pnl=%.4f", trade_id, outcome, rec.pnl)
        return rec

    def get_unresolved(self) -> List[TradeRecord]:
        return [r for r in self._trades.values() if not r.resolved]

    def get_resolved(self, since_days: int = 30) -> List[TradeRecord]:
        cutoff = (datetime.utcnow() - timedelta(days=since_days)).isoformat()
        return [
            r for r in self._trades.values()
            if r.resolved and (r.resolution_time or "") >= cutoff
        ]

    def get_all_resolved(self) -> List[TradeRecord]:
        return [r for r in self._trades.values() if r.resolved]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _append(self, record: Dict[str, Any]) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, default=str) + "\n")
        except Exception as exc:
            logger.error("Failed to append trade log: %s", exc)

    def _load_existing(self) -> None:
        if not os.path.exists(self.log_path):
            return
        try:
            with open(self.log_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        rec = TradeRecord(**{k: v for k, v in d.items() if k in TradeRecord.__dataclass_fields__})
                        self._trades[rec.trade_id] = rec
                    except Exception:
                        pass
            logger.info("Loaded %d existing trade records", len(self._trades))
        except Exception as exc:
            logger.error("Failed to load trade log: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Performance Scorer
# ──────────────────────────────────────────────────────────────────────────────

class PerformanceScorer:
    """Computes per-strategy and portfolio-level performance metrics."""

    def score(self, resolved_trades: List[TradeRecord]) -> Dict[str, StrategyPerformance]:
        """Return per-strategy StrategyPerformance objects."""
        perf: Dict[str, StrategyPerformance] = defaultdict(
            lambda: StrategyPerformance(strategy="unknown")
        )

        for rec in resolved_trades:
            sp = perf[rec.strategy]
            sp.strategy = rec.strategy
            sp.total_trades += 1

            if rec.outcome == "WIN":
                sp.wins += 1
            elif rec.outcome == "LOSS":
                sp.losses += 1
            else:
                sp.pushes += 1

            if rec.pnl is not None:
                sp.total_pnl += rec.pnl
                sp.returns.append(rec.pnl_pct or 0.0)

            sp.total_edge_estimate += rec.edge_estimate
            actual_edge = (rec.pnl_pct or 0.0)
            sp.total_actual_edge += actual_edge

        return dict(perf)

    def portfolio_metrics(self, resolved_trades: List[TradeRecord]) -> Dict[str, Any]:
        """Compute portfolio-level metrics."""
        if not resolved_trades:
            return {}

        pnls = [r.pnl or 0.0 for r in resolved_trades]
        pnl_pcts = [r.pnl_pct or 0.0 for r in resolved_trades]
        wins = sum(1 for r in resolved_trades if r.outcome == "WIN")
        total = len(resolved_trades)

        # Cumulative returns for Sharpe / drawdown
        cum = np.cumprod(1 + np.array(pnl_pcts))
        running_max = np.maximum.accumulate(cum)
        drawdowns = (running_max - cum) / np.maximum(running_max, 1e-9)
        max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        arr = np.array(pnl_pcts)
        sharpe = float(np.mean(arr) / np.std(arr) * math.sqrt(252)) if np.std(arr) > 0 else 0.0

        return {
            "total_trades": total,
            "win_rate": round(wins / total, 4) if total > 0 else 0.5,
            "total_pnl": round(sum(pnls), 4),
            "avg_pnl_pct": round(float(np.mean(pnl_pcts)), 4),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(max_dd, 4),
            "calmar_ratio": round(float(np.mean(pnl_pcts)) * 252 / max(max_dd, 0.001), 4),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Weight Adapter (EMA-based)
# ──────────────────────────────────────────────────────────────────────────────

class WeightAdapter:
    """
    Adjusts ensemble strategy weights using exponential moving average of
    per-strategy Sharpe ratios. Strategies that consistently outperform
    receive higher weights; underperformers are down-weighted.
    """

    def __init__(self, config: Dict[str, Any]):
        self.alpha = config.get("learning", {}).get("weight_ema_alpha", 0.1)
        self.min_weight = 0.05
        self.max_weight = 0.60

    def adapt(
        self,
        current_weights: Dict[str, float],
        strategy_perfs: Dict[str, StrategyPerformance],
        min_trades_required: int = 5,
    ) -> Dict[str, float]:
        """
        Compute new weights. Returns normalised weight dict.
        Only adapts strategies with enough trade history.
        """
        new_weights = dict(current_weights)

        # Compute Sharpe-based scores
        scores: Dict[str, float] = {}
        for strat, perf in strategy_perfs.items():
            if perf.total_trades < min_trades_required:
                scores[strat] = current_weights.get(strat, 0.25)
            else:
                # Combine Sharpe + win_rate for robustness
                sharpe_score = max(perf.sharpe_ratio, 0.0)
                wr_score = max(perf.win_rate - 0.5, 0.0) * 2  # 0 at 50%, 1 at 100%
                scores[strat] = 0.6 * sharpe_score + 0.4 * wr_score

        if not scores:
            return new_weights

        # Normalise scores to sum to 1
        total_score = sum(max(s, 0.01) for s in scores.values())
        target_weights = {
            strat: max(s, 0.01) / total_score
            for strat, s in scores.items()
        }

        # EMA blend: new = alpha * target + (1-alpha) * current
        for strat in set(list(current_weights.keys()) + list(target_weights.keys())):
            curr = current_weights.get(strat, 0.25)
            target = target_weights.get(strat, curr)
            blended = self.alpha * target + (1 - self.alpha) * curr
            new_weights[strat] = float(np.clip(blended, self.min_weight, self.max_weight))

        # Re-normalise to sum to 1
        total = sum(new_weights.values())
        new_weights = {k: v / total for k, v in new_weights.items()}

        logger.info("Strategy weights adapted: %s", {k: f"{v:.3f}" for k, v in new_weights.items()})
        return new_weights


# ──────────────────────────────────────────────────────────────────────────────
# Threshold Tuner (simple grid search)
# ──────────────────────────────────────────────────────────────────────────────

class ThresholdTuner:
    """
    Tunes min_edge and min_confidence thresholds by evaluating a grid of
    candidate values against historical trade outcomes.
    Selects the combination that maximises risk-adjusted return (Sharpe).
    """

    EDGE_CANDIDATES = [0.02, 0.03, 0.04, 0.05, 0.06, 0.08]
    CONF_CANDIDATES = [0.55, 0.60, 0.65, 0.70, 0.75]

    def tune(
        self,
        resolved_trades: List[TradeRecord],
        current_edge: float,
        current_conf: float,
    ) -> Tuple[float, float]:
        """
        Return the (min_edge, min_confidence) pair that maximises Sharpe
        on historical trades. Falls back to current values if insufficient data.
        """
        if len(resolved_trades) < 20:
            return current_edge, current_conf

        best_sharpe = -999.0
        best_edge = current_edge
        best_conf = current_conf

        for edge_thresh in self.EDGE_CANDIDATES:
            for conf_thresh in self.CONF_CANDIDATES:
                filtered = [
                    r for r in resolved_trades
                    if r.edge_estimate >= edge_thresh and r.confidence >= conf_thresh
                ]
                if len(filtered) < 5:
                    continue
                pnl_pcts = np.array([r.pnl_pct or 0.0 for r in filtered])
                std = np.std(pnl_pcts)
                if std == 0:
                    continue
                sharpe = float(np.mean(pnl_pcts) / std * math.sqrt(252))
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_edge = edge_thresh
                    best_conf = conf_thresh

        if best_edge != current_edge or best_conf != current_conf:
            logger.info(
                "Thresholds tuned: edge %.3f→%.3f conf %.3f→%.3f (Sharpe=%.3f)",
                current_edge, best_edge, current_conf, best_conf, best_sharpe,
            )
        return best_edge, best_conf


# ──────────────────────────────────────────────────────────────────────────────
# Self-Learning Engine (orchestrator)
# ──────────────────────────────────────────────────────────────────────────────

class SelfLearningEngine:
    """
    Orchestrates all learning components. Called after each batch of trades
    resolves to update the agent's strategy weights, thresholds, and state.

    Integration with MiroFish memory:
    - Compresses old trade episodes into a compact knowledge summary
    - Stores knowledge in a rolling JSON file (lightweight Zep alternative)
    """

    CHECKPOINT_PATH = "logs/learning_checkpoint.json"
    KNOWLEDGE_PATH = "logs/market_knowledge.jsonl"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        learning_cfg = config.get("learning", {})

        self.outcome_tracker = OutcomeTracker(
            log_path=learning_cfg.get("performance_log", "logs/trades.jsonl")
        )
        self.scorer = PerformanceScorer()
        self.weight_adapter = WeightAdapter(config)
        self.threshold_tuner = ThresholdTuner()

        self.min_trades_to_learn = learning_cfg.get("min_trades_to_learn", 10)
        self.learning_interval_hours = learning_cfg.get("learning_interval_hours", 6)
        self._last_learning_run: Optional[float] = None

        os.makedirs("logs", exist_ok=True)
        self._load_checkpoint()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_trade_entry(self, record: TradeRecord) -> None:
        self.outcome_tracker.record_entry(record)

    def record_trade_resolution(
        self, trade_id: str, exit_price: float, outcome: str
    ) -> Optional[TradeRecord]:
        return self.outcome_tracker.record_resolution(trade_id, exit_price, outcome)

    def maybe_learn(self, current_weights: Dict[str, float], current_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the learning cycle if enough time has passed and enough trades
        have resolved. Returns updated config dict.
        """
        now = time.time()
        interval_secs = self.learning_interval_hours * 3600

        if (self._last_learning_run is not None and
                now - self._last_learning_run < interval_secs):
            return current_config

        resolved = self.outcome_tracker.get_all_resolved()
        if len(resolved) < self.min_trades_to_learn:
            logger.debug("Not enough resolved trades to learn (%d < %d)", len(resolved), self.min_trades_to_learn)
            return current_config

        logger.info("Running learning cycle on %d resolved trades", len(resolved))
        self._last_learning_run = now

        # 1. Score strategies
        strategy_perfs = self.scorer.score(resolved)
        portfolio_metrics = self.scorer.portfolio_metrics(resolved)

        # 2. Adapt weights
        new_weights = self.weight_adapter.adapt(current_weights, strategy_perfs)

        # 3. Tune thresholds
        risk_cfg = current_config.get("risk", {})
        new_edge, new_conf = self.threshold_tuner.tune(
            resolved,
            risk_cfg.get("min_edge_threshold", 0.03),
            risk_cfg.get("min_confidence", 0.60),
        )

        # 4. Compress knowledge (MiroFish memory pattern)
        self._compress_knowledge(resolved[-50:], strategy_perfs, portfolio_metrics)

        # 5. Build updated config
        updated_config = dict(current_config)
        updated_config["strategy"] = dict(current_config.get("strategy", {}))
        updated_config["strategy"]["ensemble_weights"] = new_weights
        updated_config["risk"] = dict(current_config.get("risk", {}))
        updated_config["risk"]["min_edge_threshold"] = new_edge
        updated_config["risk"]["min_confidence"] = new_conf

        # 6. Persist checkpoint
        self._save_checkpoint({
            "timestamp": datetime.utcnow().isoformat(),
            "ensemble_weights": new_weights,
            "min_edge_threshold": new_edge,
            "min_confidence": new_conf,
            "portfolio_metrics": portfolio_metrics,
            "strategy_performance": {k: v.to_dict() for k, v in strategy_perfs.items()},
        })

        logger.info(
            "Learning cycle complete — win_rate=%.2f sharpe=%.3f max_dd=%.3f",
            portfolio_metrics.get("win_rate", 0),
            portfolio_metrics.get("sharpe_ratio", 0),
            portfolio_metrics.get("max_drawdown", 0),
        )
        return updated_config

    def get_performance_summary(self) -> Dict[str, Any]:
        """Return current performance summary for dashboard / reporting."""
        resolved = self.outcome_tracker.get_all_resolved()
        if not resolved:
            return {"message": "No resolved trades yet"}
        strategy_perfs = self.scorer.score(resolved)
        portfolio_metrics = self.scorer.portfolio_metrics(resolved)
        return {
            "portfolio": portfolio_metrics,
            "by_strategy": {k: v.to_dict() for k, v in strategy_perfs.items()},
            "total_resolved_trades": len(resolved),
            "unresolved_trades": len(self.outcome_tracker.get_unresolved()),
        }

    def check_pending_resolutions(self, data_client: Any) -> int:
        """
        Poll Polymarket for resolution of open positions.
        Returns count of newly resolved trades.
        """
        resolved_count = 0
        for rec in self.outcome_tracker.get_unresolved():
            try:
                market = data_client.get_market_detail(rec.market_id)
                if market is None:
                    continue
                is_resolved = market.get("closed", False) or market.get("resolved", False)
                if not is_resolved:
                    continue

                # Determine final price
                outcome_prices = market.get("outcomePrices")
                if isinstance(outcome_prices, str):
                    outcome_prices = json.loads(outcome_prices)
                if outcome_prices and len(outcome_prices) > 0:
                    final_yes_price = float(outcome_prices[0])
                else:
                    final_yes_price = float(market.get("lastTradePrice", 0.5) or 0.5)

                # Determine outcome
                if rec.action == "BUY_YES":
                    outcome = "WIN" if final_yes_price >= 0.95 else ("LOSS" if final_yes_price <= 0.05 else "PUSH")
                else:
                    outcome = "WIN" if final_yes_price <= 0.05 else ("LOSS" if final_yes_price >= 0.95 else "PUSH")

                self.record_trade_resolution(rec.trade_id, final_yes_price, outcome)
                resolved_count += 1
            except Exception as exc:
                logger.warning("Error checking resolution for %s: %s", rec.trade_id, exc)

        if resolved_count > 0:
            logger.info("Resolved %d pending trades", resolved_count)
        return resolved_count

    # ------------------------------------------------------------------
    # Knowledge compression (MiroFish memory pattern)
    # ------------------------------------------------------------------

    def _compress_knowledge(
        self,
        recent_trades: List[TradeRecord],
        strategy_perfs: Dict[str, StrategyPerformance],
        portfolio_metrics: Dict[str, Any],
    ) -> None:
        """
        Compress recent trade episodes into a compact knowledge entry.
        Stored as JSONL for lightweight retrieval (MiroFish graph-memory lite).
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "episode_count": len(recent_trades),
            "portfolio_snapshot": portfolio_metrics,
            "strategy_snapshot": {k: v.to_dict() for k, v in strategy_perfs.items()},
            "top_markets": self._extract_top_markets(recent_trades),
            "lessons": self._extract_lessons(strategy_perfs, portfolio_metrics),
        }
        try:
            with open(self.KNOWLEDGE_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
        except Exception as exc:
            logger.error("Failed to write knowledge entry: %s", exc)

    def _extract_top_markets(self, trades: List[TradeRecord]) -> List[Dict[str, Any]]:
        """Extract the most profitable market categories."""
        market_pnl: Dict[str, float] = defaultdict(float)
        for t in trades:
            market_pnl[t.market_title[:40]] += t.pnl or 0.0
        sorted_markets = sorted(market_pnl.items(), key=lambda x: x[1], reverse=True)
        return [{"title": k, "total_pnl": round(v, 4)} for k, v in sorted_markets[:5]]

    def _extract_lessons(
        self,
        strategy_perfs: Dict[str, StrategyPerformance],
        portfolio_metrics: Dict[str, Any],
    ) -> List[str]:
        """Generate human-readable lessons from performance data."""
        lessons = []
        for strat, perf in strategy_perfs.items():
            if perf.total_trades >= 5:
                if perf.win_rate > 0.60:
                    lessons.append(f"{strat} is performing well (WR={perf.win_rate:.0%})")
                elif perf.win_rate < 0.40:
                    lessons.append(f"{strat} is underperforming (WR={perf.win_rate:.0%}) — reduce weight")
        if portfolio_metrics.get("max_drawdown", 0) > 0.15:
            lessons.append("High drawdown detected — consider reducing position sizes")
        if portfolio_metrics.get("sharpe_ratio", 0) > 1.5:
            lessons.append("Strong risk-adjusted returns — strategy is working well")
        return lessons

    # ------------------------------------------------------------------
    # Checkpoint persistence
    # ------------------------------------------------------------------

    def _save_checkpoint(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.CHECKPOINT_PATH, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, default=str)
        except Exception as exc:
            logger.error("Failed to save checkpoint: %s", exc)

    def _load_checkpoint(self) -> None:
        if not os.path.exists(self.CHECKPOINT_PATH):
            return
        try:
            with open(self.CHECKPOINT_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            logger.info(
                "Loaded learning checkpoint from %s (timestamp=%s)",
                self.CHECKPOINT_PATH, data.get("timestamp", "?"),
            )
        except Exception as exc:
            logger.warning("Failed to load checkpoint: %s", exc)
