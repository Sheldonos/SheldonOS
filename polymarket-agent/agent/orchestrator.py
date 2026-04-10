"""
Main Orchestrator Agent
=======================
Ties together all components into a single autonomous trading agent:
  - PolymarketDataClient  (polyterm)
  - KronosForecastAdapter (Kronos)
  - LLMClient             (hermes-agent pattern)
  - ReACTAgent            (hermes-agent + MiroFish ReACT loop)
  - ContextWindowTracker  (56 % handoff)
  - AgentHandoffManager   (lossless context transfer)
  - EnsembleStrategy      (4-strategy ensemble)
  - SelfLearningEngine    (continuous improvement)
  - BacktestEngine        (walk-forward validation)

The orchestrator runs an infinite loop:
  1. Scan markets → score risk → generate signals
  2. ReACT agent evaluates each opportunity
  3. Execute (or simulate) trades
  4. Monitor open positions for resolution
  5. Run learning cycle every N hours
  6. Auto-handoff when context window hits 56 %
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── Path setup ────────────────────────────────────────────────────────────────
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BASE)
sys.path.insert(0, "/home/ubuntu/polyterm")
sys.path.insert(0, "/home/ubuntu/Kronos")
sys.path.insert(0, "/home/ubuntu/hermes-agent")

from config import load_config
from utils.polymarket_client import PolymarketDataClient
from models.kronos_adapter import KronosForecastAdapter
from agent.llm_client import LLMClient
from agent.react_agent import ReACTAgent, ToolRegistry, Tool
from agent.context_manager import build_context_system
from strategies.strategies import (
    MispricingHunterStrategy,
    MomentumFollowerStrategy,
    ArbitrageScannerStrategy,
    WhaleFollowerStrategy,
    EnsembleStrategy,
    TradeAction,
)
from learning.self_learning import SelfLearningEngine, TradeRecord
from backtesting.backtest_engine import BacktestEngine

logger = logging.getLogger("polymarket.orchestrator")


# ──────────────────────────────────────────────────────────────────────────────
# Tool definitions (hermes-agent pattern)
# ──────────────────────────────────────────────────────────────────────────────

def _build_tool_registry(
    data_client: PolymarketDataClient,
    kronos: KronosForecastAdapter,
    learning_engine: SelfLearningEngine,
) -> ToolRegistry:
    """Register all agent tools following hermes-agent's tool system."""
    registry = ToolRegistry()

    def tool_get_market_signals(market_id: str) -> str:
        signals = data_client.get_market_signals(market_id)
        return json.dumps(signals or {"error": "no signals"}, default=str)

    def tool_get_price_history(token_id: str, interval: str = "1d") -> str:
        history = data_client.get_price_history(token_id, interval=interval)
        return json.dumps({"count": len(history), "sample": history[-5:] if history else []}, default=str)

    def tool_kronos_forecast(token_id: str, market_id: str = "") -> str:
        history = data_client.get_price_history(token_id)
        forecast = kronos.forecast(history, market_id=market_id)
        return json.dumps(forecast or {"error": "forecast failed"}, default=str)

    def tool_get_order_book(token_id: str) -> str:
        ob = data_client.get_order_book(token_id)
        spread = data_client.calculate_spread(ob)
        return json.dumps({"spread": spread, "book_depth": len(ob.get("bids", []))}, default=str)

    def tool_scan_arbitrage(min_spread: float = 0.025) -> str:
        arb_opps = data_client.scan_arbitrage(min_spread=min_spread, limit=10)
        return json.dumps(arb_opps[:5], default=str)

    def tool_get_performance_summary() -> str:
        summary = learning_engine.get_performance_summary()
        return json.dumps(summary, default=str)

    def tool_score_market_risk(market_id: str) -> str:
        market = data_client.get_market_detail(market_id)
        if market is None:
            return json.dumps({"error": "market not found"})
        risk = data_client.score_market_risk(market)
        return json.dumps(risk, default=str)

    registry.register(Tool(
        name="get_market_signals",
        description="Get polyterm multi-factor trading signals for a market",
        parameters={"market_id": {"type": "string", "description": "Polymarket market ID"}},
        handler=tool_get_market_signals,
    ))
    registry.register(Tool(
        name="kronos_forecast",
        description="Get Kronos time-series price forecast for a market token",
        parameters={
            "token_id": {"type": "string", "description": "CLOB token ID"},
            "market_id": {"type": "string", "description": "Market ID for logging"},
        },
        handler=tool_kronos_forecast,
    ))
    registry.register(Tool(
        name="get_order_book",
        description="Get order book spread and depth for a market token",
        parameters={"token_id": {"type": "string", "description": "CLOB token ID"}},
        handler=tool_get_order_book,
    ))
    registry.register(Tool(
        name="scan_arbitrage",
        description="Scan for NegRisk arbitrage opportunities",
        parameters={"min_spread": {"type": "number", "description": "Minimum spread threshold"}},
        handler=tool_scan_arbitrage,
    ))
    registry.register(Tool(
        name="get_performance_summary",
        description="Get current agent performance metrics",
        parameters={},
        handler=tool_get_performance_summary,
    ))
    registry.register(Tool(
        name="score_market_risk",
        description="Get risk assessment for a market",
        parameters={"market_id": {"type": "string", "description": "Market ID"}},
        handler=tool_score_market_risk,
    ))

    return registry


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

class PolymarketOrchestrator:
    """
    Main autonomous trading agent orchestrator.
    Manages the full lifecycle: scan → signal → decide → execute → learn.
    """

    SYSTEM_PROMPT = """You are an expert Polymarket trading agent. Your goal is to identify
high-value prediction market opportunities with positive expected value.

You have access to tools for market analysis, price forecasting (Kronos), and
polyterm signal generation. Use them to gather evidence before making decisions.

Decision schema (respond with this JSON in your Final Answer):
{
  "action": "BUY_YES" | "BUY_NO" | "SKIP",
  "market_id": "<id>",
  "confidence": <0-1>,
  "edge": <0-1>,
  "suggested_kelly_fraction": <0-0.05>,
  "reasoning": "<concise explanation>",
  "key_risks": ["<risk1>", "<risk2>"]
}

Rules:
- Only trade when edge > 3% AND confidence > 60%
- Never risk more than 5% of bankroll on a single trade
- Prefer markets with grade A or B risk scores
- Be conservative — capital preservation is paramount"""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        self._setup_logging()

        logger.info("Initialising PolymarketOrchestrator...")

        # Core components
        self.data_client = PolymarketDataClient(self.config)
        self.kronos = KronosForecastAdapter(self.config)
        self.llm = LLMClient(self.config)
        self.learning_engine = SelfLearningEngine(self.config)

        # Strategies
        self.mispricing = MispricingHunterStrategy(self.config)
        self.momentum = MomentumFollowerStrategy(self.config)
        self.arbitrage = ArbitrageScannerStrategy(self.config)
        self.whale = WhaleFollowerStrategy(self.config)
        self.ensemble = EnsembleStrategy(self.config)

        # Tool registry
        self.tool_registry = _build_tool_registry(
            self.data_client, self.kronos, self.learning_engine
        )

        # ReACT agent with context tracking
        self.react_agent = ReACTAgent(
            config=self.config,
            llm_client=self.llm,
            tool_registry=self.tool_registry,
            agent_id="polymarket_trader_v1",
        )

        # Portfolio state
        agent_cfg = self.config.get("agent", {})
        self.bankroll = agent_cfg.get("initial_bankroll", 1000.0)
        self.simulation_mode = agent_cfg.get("simulation_mode", True)
        self.open_positions: Dict[str, Dict[str, Any]] = {}

        logger.info(
            "Orchestrator ready — bankroll=$%.0f simulation=%s",
            self.bankroll, self.simulation_mode,
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Run the autonomous trading loop indefinitely."""
        agent_cfg = self.config.get("agent", {})
        scan_interval = agent_cfg.get("scan_interval_minutes", 30) * 60
        max_concurrent = agent_cfg.get("max_concurrent_positions", 5)

        logger.info("Starting autonomous trading loop (Ctrl+C to stop)")

        cycle = 0
        while True:
            cycle += 1
            logger.info("=== Trading Cycle %d ===", cycle)

            try:
                # 1. Check pending resolutions
                resolved = self.learning_engine.check_pending_resolutions(self.data_client)
                if resolved > 0:
                    logger.info("Resolved %d positions", resolved)

                # 2. Run learning cycle if due
                current_weights = self.config.get("strategy", {}).get("ensemble_weights", {})
                self.config = self.learning_engine.maybe_learn(current_weights, self.config)

                # 3. Scan markets
                if len(self.open_positions) < max_concurrent:
                    markets = self.data_client.get_active_markets(
                        limit=self.config.get("polymarket", {}).get("max_markets_per_scan", 100),
                        min_liquidity=self.config.get("polymarket", {}).get("min_liquidity", 5000),
                        min_volume_24h=self.config.get("polymarket", {}).get("min_volume_24h", 1000),
                    )
                    logger.info("Scanning %d markets...", len(markets))

                    # 4. Evaluate each market
                    for market in markets:
                        if len(self.open_positions) >= max_concurrent:
                            break
                        self._evaluate_market(market)

                # 5. Log context stats
                ctx_stats = self.react_agent.get_context_stats()
                logger.info(
                    "Context: %.1f%% used (%d/%d tokens) | Handoffs: %d",
                    ctx_stats.get("utilisation_pct", 0),
                    ctx_stats.get("used_tokens", 0),
                    ctx_stats.get("max_tokens", 0),
                    ctx_stats.get("handoff_count", 0),
                )

                # 6. Update agent state
                self.react_agent.update_state({
                    "portfolio": {
                        "bankroll": self.bankroll,
                        "total_pnl": self.bankroll - self.config.get("agent", {}).get("initial_bankroll", 1000.0),
                    },
                    "open_positions": list(self.open_positions.values()),
                    "performance_metrics": self.learning_engine.get_performance_summary().get("portfolio", {}),
                    "strategy_weights": self.config.get("strategy", {}).get("ensemble_weights", {}),
                })

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully...")
                break
            except Exception as exc:
                logger.error("Cycle %d error: %s", cycle, exc, exc_info=True)

            logger.info("Sleeping %.0f seconds...", scan_interval)
            time.sleep(scan_interval)

    # ------------------------------------------------------------------
    # Market evaluation
    # ------------------------------------------------------------------

    def _evaluate_market(self, market: Dict[str, Any]) -> None:
        """Evaluate a single market and potentially open a position."""
        market_id = market.get("id", "")
        if not market_id or market_id in self.open_positions:
            return

        # Quick pre-filter: risk score
        risk_assessment = self.data_client.score_market_risk(market)
        if risk_assessment.get("overall_grade", "F") in ("D", "F"):
            return

        # Get token IDs
        yes_token_id, no_token_id = self.data_client.get_token_ids(market)
        if not yes_token_id:
            return

        # Get price history and Kronos forecast
        price_history = self.data_client.get_price_history(yes_token_id)
        forecast = self.kronos.forecast(price_history, market_id=market_id)
        if forecast is None:
            return

        # Get polyterm signals
        signals = self.data_client.get_market_signals(market_id)

        # Generate strategy signals
        strategy_signals = []
        sig = self.mispricing.evaluate(market, forecast, risk_assessment)
        if sig:
            strategy_signals.append(sig)
        sig = self.momentum.evaluate(market, forecast, signals, risk_assessment)
        if sig:
            strategy_signals.append(sig)

        if not strategy_signals:
            return

        # Ensemble decision
        ensemble_signal = self.ensemble.combine(strategy_signals)
        if ensemble_signal is None:
            return

        # ReACT agent final decision
        context = {
            "market_id": market_id,
            "market_title": market.get("question", ""),
            "current_price": forecast.get("current_price", 0.5),
            "forecast": forecast,
            "ensemble_signal": {
                "action": ensemble_signal.action.value,
                "edge": ensemble_signal.edge,
                "confidence": ensemble_signal.confidence,
                "reasoning": ensemble_signal.reasoning,
            },
            "risk_grade": risk_assessment.get("overall_grade", "C"),
            "portfolio": {
                "bankroll": self.bankroll,
                "open_positions": len(self.open_positions),
            },
        }

        decision = self.react_agent.run_task(
            task=f"Evaluate trade opportunity for: {market.get('question', '')[:80]}",
            system_prompt=self.SYSTEM_PROMPT,
            context=context,
        )

        # Execute decision
        action = decision.get("action", "SKIP")
        if action in ("BUY_YES", "BUY_NO"):
            self._execute_trade(market, forecast, decision, risk_assessment)

    # ------------------------------------------------------------------
    # Trade execution
    # ------------------------------------------------------------------

    def _execute_trade(
        self,
        market: Dict[str, Any],
        forecast: Dict[str, Any],
        decision: Dict[str, Any],
        risk_assessment: Dict[str, Any],
    ) -> None:
        """Execute (or simulate) a trade based on the agent's decision."""
        market_id = market.get("id", "")
        action = decision.get("action", "SKIP")
        kelly_fraction = float(decision.get("suggested_kelly_fraction", 0.02))
        kelly_fraction = min(kelly_fraction, self.config.get("risk", {}).get("max_bankroll_per_trade", 0.05))

        position_size = self.bankroll * kelly_fraction
        entry_price = forecast.get("current_price", 0.5)
        if action == "BUY_NO":
            entry_price = 1.0 - entry_price

        trade_id = f"trade_{market_id[:8]}_{int(time.time())}"

        # Record trade
        record = TradeRecord(
            trade_id=trade_id,
            market_id=market_id,
            market_title=market.get("question", "")[:80],
            strategy="ensemble",
            action=action,
            entry_price=entry_price,
            position_size=position_size,
            entry_time=datetime.utcnow().isoformat(),
            edge_estimate=float(decision.get("edge", 0)),
            confidence=float(decision.get("confidence", 0)),
            model_predicted_price=forecast.get("predicted_price", entry_price),
        )
        self.learning_engine.record_trade_entry(record)

        if not self.simulation_mode:
            # Real execution would go here via CLOB API
            logger.info("LIVE TRADE: %s %s @ %.3f size=$%.2f", action, market_id, entry_price, position_size)
        else:
            logger.info("SIM TRADE: %s %s @ %.3f size=$%.2f edge=%.2f%%",
                       action, market_id, entry_price, position_size, decision.get("edge", 0) * 100)

        # Track open position
        self.open_positions[market_id] = {
            "trade_id": trade_id,
            "market_id": market_id,
            "action": action,
            "entry_price": entry_price,
            "position_size": position_size,
            "entry_time": datetime.utcnow().isoformat(),
        }

        # Deduct from bankroll (simulation)
        self.bankroll -= position_size

    # ------------------------------------------------------------------
    # Backtesting
    # ------------------------------------------------------------------

    def run_backtest(
        self,
        start_date: str = "2024-01-01",
        end_date: str = "2024-12-31",
        n_markets: int = 20,
    ) -> Dict[str, Any]:
        """Run a historical backtest and return results."""
        logger.info("Starting backtest: %s → %s", start_date, end_date)

        markets = self.data_client.get_active_markets(limit=n_markets)
        if not markets:
            logger.warning("No markets available for backtest — using synthetic data")
            markets = [
                {
                    "id": f"synthetic_{i}",
                    "question": f"Synthetic Market {i}",
                    "liquidity": 10000,
                    "volume24hr": 5000,
                    "lastTradePrice": 0.5,
                    "clobTokenIds": json.dumps([f"token_{i}_yes", f"token_{i}_no"]),
                }
                for i in range(n_markets)
            ]

        engine = BacktestEngine(
            config=self.config,
            data_client=self.data_client,
            kronos_adapter=self.kronos,
            strategies=self.ensemble,
        )

        result = engine.run(
            markets=markets,
            start_date=start_date,
            end_date=end_date,
            walk_forward_windows=4,
        )

        mc_results = engine.run_monte_carlo(result, n_simulations=1000)

        return {
            "backtest": result.to_dict(),
            "monte_carlo": mc_results,
            "summary": result.to_summary(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _setup_logging(self) -> None:
        """Configure logging from config."""
        log_cfg = self.config.get("logging", {})
        level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
        log_dir = os.path.dirname(log_cfg.get("file", "logs/agent.log"))
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=level,
            format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_cfg.get("file", "logs/agent.log"), encoding="utf-8"),
            ],
        )
