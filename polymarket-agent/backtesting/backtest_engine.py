"""
Backtesting Engine
==================
Simulates the full trading agent pipeline on historical Polymarket data.
Supports walk-forward validation, Monte Carlo simulation, and
per-strategy attribution analysis.

Architecture:
  BacktestEngine
    ├── HistoricalDataLoader   — loads price history from CLOB API or cache
    ├── SignalSimulator        — replays signals using historical prices
    ├── PortfolioSimulator     — tracks bankroll, positions, P&L
    ├── MetricsCalculator      — computes Sharpe, drawdown, win rate, etc.
    └── BacktestReporter       — generates JSON + Markdown reports
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
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("polymarket.backtest")


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BacktestTrade:
    trade_id: str
    market_id: str
    market_title: str
    strategy: str
    action: str
    entry_price: float
    exit_price: float
    position_size: float
    entry_time: str
    exit_time: str
    edge_estimate: float
    confidence: float
    pnl: float
    pnl_pct: float
    outcome: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BacktestResult:
    """Full backtest result."""
    start_date: str
    end_date: str
    initial_bankroll: float
    final_bankroll: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    total_pnl_pct: float
    win_rate: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    avg_trade_pnl: float
    avg_winning_trade: float
    avg_losing_trade: float
    profit_factor: float
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    strategy_breakdown: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["trades"] = [t.to_dict() for t in self.trades]
        return d

    def to_summary(self) -> str:
        """Compact text summary for logging and reports."""
        return (
            f"Backtest [{self.start_date} → {self.end_date}]\n"
            f"  Bankroll    : ${self.initial_bankroll:.0f} → ${self.final_bankroll:.2f} "
            f"({self.total_pnl_pct:+.1%})\n"
            f"  Trades      : {self.total_trades} ({self.win_rate:.0%} win rate)\n"
            f"  Sharpe      : {self.sharpe_ratio:.3f}\n"
            f"  Max DD      : {self.max_drawdown:.1%}\n"
            f"  Calmar      : {self.calmar_ratio:.3f}\n"
            f"  Profit Fac  : {self.profit_factor:.3f}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Historical Data Loader
# ──────────────────────────────────────────────────────────────────────────────

class HistoricalDataLoader:
    """
    Loads and caches historical price data from Polymarket CLOB API.
    Falls back to synthetic data generation for testing.
    """

    CACHE_DIR = "data/price_cache"

    def __init__(self, data_client: Any, config: Dict[str, Any]):
        self.data_client = data_client
        self.config = config
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def load_market_history(
        self,
        market_id: str,
        token_id: str,
        start_date: str,
        end_date: str,
        resample_hours: int = 1,
    ) -> pd.DataFrame:
        """
        Load OHLCV price history for a market token.
        Returns DataFrame with columns: [timestamp, open, high, low, close, volume].
        """
        cache_key = f"{token_id}_{start_date}_{end_date}_{resample_hours}h"
        cache_path = os.path.join(self.CACHE_DIR, f"{cache_key}.parquet")

        # Try cache first
        if os.path.exists(cache_path):
            try:
                df = pd.read_parquet(cache_path)
                logger.debug("Loaded %d rows from cache: %s", len(df), cache_key)
                return df
            except Exception:
                pass

        # Fetch from API
        try:
            raw = self.data_client.get_price_history(
                token_id=token_id,
                interval="max",
                fidelity=resample_hours * 3600,
            )
            if not raw:
                return self._generate_synthetic_data(start_date, end_date, resample_hours)

            from models.kronos_adapter import price_history_to_ohlcv
            df = price_history_to_ohlcv(raw, resample_minutes=resample_hours * 60)

            if df.empty:
                return self._generate_synthetic_data(start_date, end_date, resample_hours)

            # Filter date range
            df["timestamps"] = pd.to_datetime(df["timestamps"])
            df = df[(df["timestamps"] >= start_date) & (df["timestamps"] <= end_date)]

            # Cache
            try:
                df.to_parquet(cache_path, index=False)
            except Exception:
                pass

            return df

        except Exception as exc:
            logger.warning("Failed to load history for %s: %s — using synthetic", token_id, exc)
            return self._generate_synthetic_data(start_date, end_date, resample_hours)

    def _generate_synthetic_data(
        self,
        start_date: str,
        end_date: str,
        resample_hours: int = 1,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Generate synthetic binary market price data for testing."""
        np.random.seed(seed)
        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)
        periods = int((end - start).total_seconds() / (resample_hours * 3600))
        if periods < 10:
            periods = 100

        timestamps = pd.date_range(start=start, periods=periods, freq=f"{resample_hours}h")

        # Simulate a binary market: starts at 0.5, drifts toward resolution
        price = 0.5
        prices = []
        for i in range(periods):
            # Drift toward resolution in final 20%
            if i > periods * 0.8:
                drift = 0.01 if price > 0.5 else -0.01
            else:
                drift = np.random.normal(0, 0.005)
            noise = np.random.normal(0, 0.01)
            price = float(np.clip(price + drift + noise, 0.02, 0.98))
            prices.append(price)

        prices = np.array(prices)
        df = pd.DataFrame({
            "timestamps": timestamps,
            "open": prices,
            "high": np.minimum(prices + np.abs(np.random.normal(0, 0.005, periods)), 0.99),
            "low": np.maximum(prices - np.abs(np.random.normal(0, 0.005, periods)), 0.01),
            "close": prices,
            "volume": np.ones(periods),
        })
        return df


# ──────────────────────────────────────────────────────────────────────────────
# Portfolio Simulator
# ──────────────────────────────────────────────────────────────────────────────

class PortfolioSimulator:
    """Simulates portfolio evolution through a sequence of backtest trades."""

    def __init__(self, initial_bankroll: float = 1000.0, transaction_cost: float = 0.002):
        self.initial_bankroll = initial_bankroll
        self.bankroll = initial_bankroll
        self.transaction_cost = transaction_cost
        self.equity_curve: List[float] = [initial_bankroll]
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        self.closed_trades: List[BacktestTrade] = []

    def open_position(
        self,
        trade_id: str,
        market_id: str,
        market_title: str,
        strategy: str,
        action: str,
        entry_price: float,
        kelly_fraction: float,
        edge_estimate: float,
        confidence: float,
        entry_time: str,
    ) -> Optional[float]:
        """Open a position. Returns position size in USDC or None if rejected."""
        # Apply transaction cost
        effective_price = entry_price * (1 + self.transaction_cost)
        if effective_price >= 1.0:
            return None

        position_size = self.bankroll * kelly_fraction
        if position_size < 1.0 or position_size > self.bankroll:
            return None

        self.bankroll -= position_size
        self.open_positions[trade_id] = {
            "trade_id": trade_id,
            "market_id": market_id,
            "market_title": market_title,
            "strategy": strategy,
            "action": action,
            "entry_price": effective_price,
            "position_size": position_size,
            "edge_estimate": edge_estimate,
            "confidence": confidence,
            "entry_time": entry_time,
        }
        return position_size

    def close_position(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: str,
    ) -> Optional[BacktestTrade]:
        """Close a position and record the trade."""
        pos = self.open_positions.pop(trade_id, None)
        if pos is None:
            return None

        # Apply transaction cost on exit
        effective_exit = exit_price * (1 - self.transaction_cost)

        action = pos["action"]
        entry_price = pos["entry_price"]
        position_size = pos["position_size"]

        if action == "BUY_YES":
            pnl_pct = (effective_exit - entry_price) / entry_price
        else:
            no_entry = 1.0 - entry_price
            no_exit = 1.0 - effective_exit
            pnl_pct = (no_exit - no_entry) / no_entry if no_entry > 0 else 0.0

        pnl = pnl_pct * position_size
        final_value = position_size + pnl
        self.bankroll += final_value

        outcome = "WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "PUSH")

        trade = BacktestTrade(
            trade_id=trade_id,
            market_id=pos["market_id"],
            market_title=pos["market_title"],
            strategy=pos["strategy"],
            action=action,
            entry_price=entry_price,
            exit_price=effective_exit,
            position_size=position_size,
            entry_time=pos["entry_time"],
            exit_time=exit_time,
            edge_estimate=pos["edge_estimate"],
            confidence=pos["confidence"],
            pnl=pnl,
            pnl_pct=pnl_pct,
            outcome=outcome,
        )
        self.closed_trades.append(trade)
        self.equity_curve.append(self.bankroll)
        return trade

    def reset(self) -> None:
        self.bankroll = self.initial_bankroll
        self.equity_curve = [self.initial_bankroll]
        self.open_positions = {}
        self.closed_trades = []


# ──────────────────────────────────────────────────────────────────────────────
# Metrics Calculator
# ──────────────────────────────────────────────────────────────────────────────

class MetricsCalculator:
    """Computes comprehensive performance metrics from backtest trades."""

    def calculate(
        self,
        trades: List[BacktestTrade],
        equity_curve: List[float],
        initial_bankroll: float,
    ) -> Dict[str, Any]:
        if not trades:
            return {"error": "No trades to analyse"}

        pnl_pcts = np.array([t.pnl_pct for t in trades])
        pnls = np.array([t.pnl for t in trades])
        wins = [t for t in trades if t.outcome == "WIN"]
        losses = [t for t in trades if t.outcome == "LOSS"]

        # Sharpe (annualised, assuming daily rebalancing)
        sharpe = 0.0
        if len(pnl_pcts) >= 3 and np.std(pnl_pcts) > 0:
            sharpe = float(np.mean(pnl_pcts) / np.std(pnl_pcts) * math.sqrt(252))

        # Sortino (downside deviation only)
        downside = pnl_pcts[pnl_pcts < 0]
        sortino = 0.0
        if len(downside) >= 2 and np.std(downside) > 0:
            sortino = float(np.mean(pnl_pcts) / np.std(downside) * math.sqrt(252))

        # Max drawdown
        eq = np.array(equity_curve)
        running_max = np.maximum.accumulate(eq)
        drawdowns = (running_max - eq) / np.maximum(running_max, 1e-9)
        max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        # Profit factor
        gross_profit = float(np.sum(pnls[pnls > 0])) if np.any(pnls > 0) else 0.0
        gross_loss = float(np.abs(np.sum(pnls[pnls < 0]))) if np.any(pnls < 0) else 1e-9
        profit_factor = gross_profit / gross_loss

        final_bankroll = equity_curve[-1] if equity_curve else initial_bankroll
        total_pnl = final_bankroll - initial_bankroll
        total_pnl_pct = total_pnl / initial_bankroll

        # Calmar
        calmar = (total_pnl_pct / max_dd) if max_dd > 0 else 0.0

        # Strategy breakdown
        strategy_breakdown: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "trades": 0, "wins": 0, "total_pnl": 0.0, "win_rate": 0.0
        })
        for t in trades:
            sb = strategy_breakdown[t.strategy]
            sb["trades"] += 1
            if t.outcome == "WIN":
                sb["wins"] += 1
            sb["total_pnl"] += t.pnl
        for strat, sb in strategy_breakdown.items():
            sb["win_rate"] = sb["wins"] / sb["trades"] if sb["trades"] > 0 else 0.0
            sb["total_pnl"] = round(sb["total_pnl"], 4)

        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round(len(wins) / len(trades), 4),
            "total_pnl": round(total_pnl, 4),
            "total_pnl_pct": round(total_pnl_pct, 4),
            "initial_bankroll": initial_bankroll,
            "final_bankroll": round(final_bankroll, 4),
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4),
            "max_drawdown": round(max_dd, 4),
            "calmar_ratio": round(calmar, 4),
            "profit_factor": round(profit_factor, 4),
            "avg_trade_pnl": round(float(np.mean(pnls)), 4),
            "avg_winning_trade": round(float(np.mean([t.pnl for t in wins])), 4) if wins else 0.0,
            "avg_losing_trade": round(float(np.mean([t.pnl for t in losses])), 4) if losses else 0.0,
            "strategy_breakdown": dict(strategy_breakdown),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Backtest Engine
# ──────────────────────────────────────────────────────────────────────────────

class BacktestEngine:
    """
    Full backtesting engine for the Polymarket trading agent.
    Runs walk-forward validation across historical market data.
    """

    RESULTS_DIR = "backtesting/results"

    def __init__(
        self,
        config: Dict[str, Any],
        data_client: Any,
        kronos_adapter: Any,
        strategies: Any,
    ):
        self.config = config
        self.data_client = data_client
        self.kronos_adapter = kronos_adapter
        self.strategies = strategies

        bt_cfg = config.get("backtesting", {})
        self.initial_bankroll = bt_cfg.get("initial_bankroll", 1000.0)
        self.transaction_cost = bt_cfg.get("transaction_cost", 0.002)
        self.holding_period_hours = bt_cfg.get("holding_period_hours", 24)
        self.max_concurrent_positions = bt_cfg.get("max_concurrent_positions", 5)

        self.data_loader = HistoricalDataLoader(data_client, config)
        self.portfolio = PortfolioSimulator(self.initial_bankroll, self.transaction_cost)
        self.metrics_calc = MetricsCalculator()

        os.makedirs(self.RESULTS_DIR, exist_ok=True)
        logger.info("BacktestEngine initialised — bankroll=$%.0f", self.initial_bankroll)

    def run(
        self,
        markets: List[Dict[str, Any]],
        start_date: str = "2024-01-01",
        end_date: str = "2024-12-31",
        walk_forward_windows: int = 4,
    ) -> BacktestResult:
        """
        Run a walk-forward backtest across the given markets and date range.

        Args:
            markets: List of market dicts (from Polymarket API)
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            walk_forward_windows: Number of walk-forward windows

        Returns:
            BacktestResult with full trade history and metrics
        """
        logger.info(
            "Starting backtest: %d markets, %s → %s, %d WF windows",
            len(markets), start_date, end_date, walk_forward_windows,
        )
        self.portfolio.reset()

        # Split date range into walk-forward windows
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date)
        total_days = (end_dt - start_dt).days
        window_days = total_days // walk_forward_windows

        all_trades: List[BacktestTrade] = []

        for window_idx in range(walk_forward_windows):
            window_start = start_dt + timedelta(days=window_idx * window_days)
            window_end = window_start + timedelta(days=window_days)
            if window_end > end_dt:
                window_end = end_dt

            logger.info(
                "Walk-forward window %d/%d: %s → %s",
                window_idx + 1, walk_forward_windows,
                window_start.date(), window_end.date(),
            )

            window_trades = self._run_window(
                markets=markets,
                start_dt=window_start,
                end_dt=window_end,
            )
            all_trades.extend(window_trades)

        # Compute final metrics
        metrics = self.metrics_calc.calculate(
            all_trades, self.portfolio.equity_curve, self.initial_bankroll
        )

        result = BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_bankroll=self.initial_bankroll,
            final_bankroll=metrics["final_bankroll"],
            total_trades=metrics["total_trades"],
            winning_trades=metrics["winning_trades"],
            losing_trades=metrics["losing_trades"],
            total_pnl=metrics["total_pnl"],
            total_pnl_pct=metrics["total_pnl_pct"],
            win_rate=metrics["win_rate"],
            sharpe_ratio=metrics["sharpe_ratio"],
            sortino_ratio=metrics["sortino_ratio"],
            max_drawdown=metrics["max_drawdown"],
            calmar_ratio=metrics["calmar_ratio"],
            avg_trade_pnl=metrics["avg_trade_pnl"],
            avg_winning_trade=metrics["avg_winning_trade"],
            avg_losing_trade=metrics["avg_losing_trade"],
            profit_factor=metrics["profit_factor"],
            trades=all_trades,
            equity_curve=self.portfolio.equity_curve,
            strategy_breakdown=metrics.get("strategy_breakdown", {}),
        )

        logger.info("Backtest complete:\n%s", result.to_summary())
        self._save_result(result)
        return result

    def _run_window(
        self,
        markets: List[Dict[str, Any]],
        start_dt: pd.Timestamp,
        end_dt: pd.Timestamp,
    ) -> List[BacktestTrade]:
        """Run backtest for a single walk-forward window."""
        trades: List[BacktestTrade] = []
        risk_cfg = self.config.get("risk", {})
        min_edge = risk_cfg.get("min_edge_threshold", 0.03)
        min_conf = risk_cfg.get("min_confidence", 0.60)
        max_kelly = risk_cfg.get("max_bankroll_per_trade", 0.05)

        from strategies.strategies import (
            MispricingHunterStrategy, MomentumFollowerStrategy, EnsembleStrategy
        )
        mispricing = MispricingHunterStrategy(self.config)
        momentum = MomentumFollowerStrategy(self.config)
        ensemble = EnsembleStrategy(self.config)

        open_count = 0

        for market in markets[:50]:  # Limit to 50 markets per window
            if open_count >= self.max_concurrent_positions:
                break

            market_id = market.get("id", "")
            yes_token_id, _ = self.data_client.get_token_ids(market)
            if not yes_token_id:
                continue

            # Load historical data
            df = self.data_loader.load_market_history(
                market_id=market_id,
                token_id=yes_token_id,
                start_date=str(start_dt.date()),
                end_date=str(end_dt.date()),
            )
            if len(df) < 30:
                continue

            # Simulate signals at each time step (hourly)
            for i in range(30, len(df) - self.holding_period_hours):
                if open_count >= self.max_concurrent_positions:
                    break

                # Use data up to point i as "current"
                history_slice = [
                    {"t": int(row["timestamps"].timestamp()), "p": row["close"]}
                    for _, row in df.iloc[:i].iterrows()
                ]

                # Generate Kronos forecast
                forecast = self.kronos_adapter.forecast(history_slice, market_id)
                if forecast is None:
                    continue

                # Risk score (simplified for backtest)
                risk_assessment = {"overall_grade": "B", "overall_score": 70}

                # Generate strategy signals
                signals_list = []
                sig = mispricing.evaluate(market, forecast, risk_assessment)
                if sig:
                    signals_list.append(sig)
                sig = momentum.evaluate(market, forecast, None, risk_assessment)
                if sig:
                    signals_list.append(sig)

                if not signals_list:
                    continue

                # Ensemble decision
                final_signal = ensemble.combine(signals_list)
                if final_signal is None:
                    continue

                if final_signal.edge < min_edge or final_signal.confidence < min_conf:
                    continue

                # Simulate entry
                entry_price = forecast["current_price"]
                kelly_size = min(
                    final_signal.metadata.get("kelly_size", 0.02),
                    max_kelly,
                )
                entry_time = str(df.iloc[i]["timestamps"])
                trade_id = f"bt_{market_id[:8]}_{i}"

                pos_size = self.portfolio.open_position(
                    trade_id=trade_id,
                    market_id=market_id,
                    market_title=market.get("question", "")[:60],
                    strategy=final_signal.strategy,
                    action=final_signal.action.value,
                    entry_price=entry_price,
                    kelly_fraction=kelly_size,
                    edge_estimate=final_signal.edge,
                    confidence=final_signal.confidence,
                    entry_time=entry_time,
                )
                if pos_size is None:
                    continue

                open_count += 1

                # Simulate exit after holding period
                exit_idx = min(i + self.holding_period_hours, len(df) - 1)
                exit_price = float(df.iloc[exit_idx]["close"])
                exit_time = str(df.iloc[exit_idx]["timestamps"])

                trade = self.portfolio.close_position(trade_id, exit_price, exit_time)
                if trade:
                    trades.append(trade)
                    open_count -= 1

        return trades

    def _save_result(self, result: BacktestResult) -> None:
        """Save backtest result to JSON file."""
        filename = os.path.join(
            self.RESULTS_DIR,
            f"backtest_{result.start_date}_{result.end_date}_{int(time.time())}.json",
        )
        try:
            with open(filename, "w", encoding="utf-8") as fh:
                json.dump(result.to_dict(), fh, indent=2, default=str)
            logger.info("Backtest result saved to %s", filename)
        except Exception as exc:
            logger.error("Failed to save backtest result: %s", exc)

    def run_monte_carlo(
        self,
        result: BacktestResult,
        n_simulations: int = 1000,
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation by bootstrapping trade returns.
        Estimates distribution of outcomes.
        """
        if not result.trades:
            return {}

        returns = np.array([t.pnl_pct for t in result.trades])
        n_trades = len(returns)
        sim_final_values = []

        for _ in range(n_simulations):
            sampled = np.random.choice(returns, size=n_trades, replace=True)
            equity = self.initial_bankroll
            for r in sampled:
                equity *= (1 + r)
            sim_final_values.append(equity)

        sim_arr = np.array(sim_final_values)
        return {
            "n_simulations": n_simulations,
            "median_final_bankroll": round(float(np.median(sim_arr)), 2),
            "p5_final_bankroll": round(float(np.percentile(sim_arr, 5)), 2),
            "p95_final_bankroll": round(float(np.percentile(sim_arr, 95)), 2),
            "probability_of_profit": round(float(np.mean(sim_arr > self.initial_bankroll)), 4),
            "probability_of_ruin": round(float(np.mean(sim_arr < self.initial_bankroll * 0.5)), 4),
        }
