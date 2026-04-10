#!/usr/bin/env python3
"""
Comprehensive test suite for the Polymarket Autonomous Trading Agent.
Tests all major components without requiring API keys.
"""
import sys, os, json, logging

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '/home/ubuntu/polyterm')
sys.path.insert(0, '/home/ubuntu/Kronos')
logging.basicConfig(level=logging.WARNING)

PASS = 0
FAIL = 0

def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  [PASS] {name}")
        PASS += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        FAIL += 1

# ─────────────────────────────────────────────────────────────
print("\n=== 1. Context Manager ===")
# ─────────────────────────────────────────────────────────────
from agent.context_manager import (
    estimate_tokens, ContextWindowTracker, AgentHandoffManager,
    AgentState, build_context_system
)

config = {
    'llm': {'model': 'gpt-4.1-mini', 'max_tokens': 4096},
    'agent': {'context_handoff_threshold': 0.56, 'agent_id': 'test_agent'},
    'strategy': {'ensemble_weights': {'mispricing_hunter': 0.35}},
    'learning': {'performance_log': 'logs/trades.jsonl'}
}

def test_context_init():
    tracker, handoff_mgr, state = build_context_system(config, 'test_agent_init')
    assert tracker.stats.max_tokens > 0
    assert abs(tracker.stats.handoff_threshold - 0.56) < 0.01
    assert state.generation >= 0  # fresh state starts at 0, increments on handoff

def test_context_tracking():
    tracker, _, _ = build_context_system(config, 'test_agent_2')
    msgs = [{'role': 'system', 'content': 'You are a trading agent.'}]
    for i in range(5):
        msgs.append({'role': 'user', 'content': f'Analyse market {i}: ' + 'x' * 50})
        msgs.append({'role': 'assistant', 'content': f'Analysis {i}: ' + 'y' * 100})
    tracker.add_messages(msgs)
    assert tracker.utilisation_pct >= 0
    stats = tracker.get_stats()
    assert 'utilisation_pct' in stats

def test_agent_state():
    state = AgentState(agent_id='test', generation=1, task_description='test task')
    state.add_decision({'action': 'BUY_YES', 'market_id': 'm1', 'edge': 0.05, 'confidence': 0.7})
    assert len(state.decision_log) == 1
    prompt = state.to_handoff_prompt()
    assert 'generation' in prompt.lower() or 'Generation' in prompt

test("Context manager init", test_context_init)
test("Context tracking", test_context_tracking)
test("Agent state", test_agent_state)

# ─────────────────────────────────────────────────────────────
print("\n=== 2. Self-Learning Engine ===")
# ─────────────────────────────────────────────────────────────
from learning.self_learning import (
    OutcomeTracker, PerformanceScorer, WeightAdapter, ThresholdTuner,
    TradeRecord, StrategyPerformance
)
import numpy as np

def make_trades(n=30):
    trades = []
    for i in range(n):
        win = (i % 3 != 0)
        rec = TradeRecord(
            trade_id=f'trade_{i}',
            market_id=f'market_{i}',
            market_title=f'Test Market {i}',
            strategy='mispricing_hunter' if i % 2 == 0 else 'momentum_follower',
            action='BUY_YES',
            entry_price=0.45,
            position_size=50.0,
            entry_time='2024-01-01T00:00:00',
            edge_estimate=0.05,
            confidence=0.70,
            model_predicted_price=0.55,
            exit_price=0.80 if win else 0.20,
            pnl=20.0 if win else -30.0,
            pnl_pct=0.40 if win else -0.60,
            resolved=True,
            resolution_time='2024-02-01T00:00:00',
            outcome='WIN' if win else 'LOSS',
        )
        trades.append(rec)
    return trades

def test_scorer():
    trades = make_trades(30)
    scorer = PerformanceScorer()
    perfs = scorer.score(trades)
    portfolio = scorer.portfolio_metrics(trades)
    assert 'win_rate' in portfolio
    assert 0 < portfolio['win_rate'] < 1
    assert 'sharpe_ratio' in portfolio
    assert 'mispricing_hunter' in perfs

def test_weight_adapter():
    trades = make_trades(30)
    scorer = PerformanceScorer()
    perfs = scorer.score(trades)
    adapter = WeightAdapter(config)
    weights = {'mispricing_hunter': 0.35, 'momentum_follower': 0.25, 'arbitrage_scanner': 0.20, 'whale_follower': 0.20}
    new_weights = adapter.adapt(weights, perfs, min_trades_required=5)
    assert abs(sum(new_weights.values()) - 1.0) < 0.01, f"Weights don't sum to 1: {sum(new_weights.values())}"
    assert all(v > 0 for v in new_weights.values())

def test_threshold_tuner():
    trades = make_trades(30)
    tuner = ThresholdTuner()
    new_edge, new_conf = tuner.tune(trades, 0.03, 0.60)
    assert 0.01 <= new_edge <= 0.15
    assert 0.50 <= new_conf <= 0.85

test("Performance scorer", test_scorer)
test("Weight adapter", test_weight_adapter)
test("Threshold tuner", test_threshold_tuner)

# ─────────────────────────────────────────────────────────────
print("\n=== 3. Trading Strategies ===")
# ─────────────────────────────────────────────────────────────
from strategies.strategies import (
    MispricingHunterStrategy, MomentumFollowerStrategy,
    ArbitrageScannerStrategy, WhaleFollowerStrategy,
    EnsembleStrategy, KellyCriterion, TradeAction, TradeSignal
)

strat_config = {
    'risk': {
        'min_edge_threshold': 0.03,
        'min_confidence': 0.60,
        'kelly_fraction': 0.25,
        'max_bankroll_per_trade': 0.05
    },
    'strategy': {
        'ensemble_weights': {
            'mispricing_hunter': 0.35,
            'momentum_follower': 0.25,
            'arbitrage_scanner': 0.20,
            'whale_follower': 0.20
        }
    }
}

market = {
    'id': 'test_market',
    'question': 'Will BTC exceed 100k?',
    'liquidity': 50000,
    'volume24hr': 10000
}
forecast_bull = {
    'current_price': 0.42,
    'predicted_price': 0.58,
    'direction': 'bullish',
    'confidence': 0.72,
    'uncertainty_std': 0.05,
    'model': 'statistical_fallback'
}
risk = {'overall_grade': 'B', 'overall_score': 75}

def test_mispricing():
    strat = MispricingHunterStrategy(strat_config)
    sig = strat.evaluate(market, forecast_bull, risk)
    assert sig is not None
    assert sig.action == TradeAction.BUY_YES
    assert sig.edge > 0.03
    assert 0 < sig.confidence <= 1.0

def test_momentum():
    strat = MomentumFollowerStrategy(strat_config)
    signals = {
        'direction': 'bullish',
        'confidence': 0.68,
        'probability_change': 8.0,
        'signal_summary': {'bullish': 4, 'bearish': 1}
    }
    sig = strat.evaluate(market, forecast_bull, signals, risk)
    # May or may not fire depending on thresholds — just check no crash
    if sig:
        assert sig.action in (TradeAction.BUY_YES, TradeAction.BUY_NO)

def test_ensemble():
    mispricing = MispricingHunterStrategy(strat_config)
    momentum = MomentumFollowerStrategy(strat_config)
    ensemble = EnsembleStrategy(strat_config)
    sig1 = mispricing.evaluate(market, forecast_bull, risk)
    signals_data = {
        'direction': 'bullish', 'confidence': 0.68,
        'probability_change': 8.0, 'signal_summary': {'bullish': 4, 'bearish': 1}
    }
    sig2 = momentum.evaluate(market, forecast_bull, signals_data, risk)
    all_sigs = [s for s in [sig1, sig2] if s is not None]
    final = ensemble.combine(all_sigs)
    if final:
        assert final.action in (TradeAction.BUY_YES, TradeAction.BUY_NO)
        assert 0 < final.confidence <= 1.0

def test_kelly():
    # KellyCriterion is a static utility class
    fraction = KellyCriterion.calculate(
        p_win=0.60,
        b_odds=1.22,  # 1/0.45 - 1
        kelly_fraction=0.25,
        max_fraction=0.05,
    )
    assert 0 <= fraction <= 0.05  # bounded by max_fraction

test("Mispricing Hunter strategy", test_mispricing)
test("Momentum Follower strategy", test_momentum)
test("Ensemble strategy", test_ensemble)
test("Kelly Criterion sizing", test_kelly)

# ─────────────────────────────────────────────────────────────
print("\n=== 4. Backtesting Engine ===")
# ─────────────────────────────────────────────────────────────
from backtesting.backtest_engine import (
    PortfolioSimulator, MetricsCalculator, BacktestTrade
)

def test_portfolio_sim():
    sim = PortfolioSimulator(initial_bankroll=1000.0)
    pos = sim.open_position('t1', 'm1', 'Test', 'mispricing_hunter', 'BUY_YES', 0.45, 0.03, 0.05, 0.70, '2024-01-01')
    assert pos is not None and pos > 0
    assert sim.bankroll < 1000.0
    trade = sim.close_position('t1', 0.80, '2024-02-01')
    assert trade is not None
    assert trade.outcome == 'WIN'
    assert trade.pnl > 0
    assert sim.bankroll > 1000.0 - pos  # recovered some

def test_portfolio_loss():
    sim = PortfolioSimulator(initial_bankroll=1000.0)
    pos = sim.open_position('t2', 'm2', 'Test', 'momentum_follower', 'BUY_YES', 0.55, 0.03, 0.05, 0.65, '2024-01-01')
    trade = sim.close_position('t2', 0.10, '2024-02-01')
    assert trade.outcome == 'LOSS'
    assert trade.pnl < 0

def test_metrics_calc():
    sim = PortfolioSimulator(initial_bankroll=1000.0)
    for i in range(10):
        win = i % 3 != 0
        sim.open_position(f't{i}', f'm{i}', 'Test', 'mispricing_hunter', 'BUY_YES', 0.45, 0.02, 0.05, 0.70, '2024-01-01')
        sim.close_position(f't{i}', 0.80 if win else 0.15, '2024-02-01')
    calc = MetricsCalculator()
    metrics = calc.calculate(sim.closed_trades, sim.equity_curve, 1000.0)
    assert 'win_rate' in metrics
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics
    assert 'profit_factor' in metrics

test("Portfolio simulator (win)", test_portfolio_sim)
test("Portfolio simulator (loss)", test_portfolio_loss)
test("Metrics calculator", test_metrics_calc)

# ─────────────────────────────────────────────────────────────
print("\n=== 5. ReACT Agent (no LLM) ===")
# ─────────────────────────────────────────────────────────────
from agent.react_agent import ToolRegistry, Tool, ReACTAgent

def test_tool_registry():
    reg = ToolRegistry()
    reg.register(Tool(
        name="test_tool",
        description="A test tool",
        parameters={"x": {"type": "string"}},
        handler=lambda x: f"result: {x}",
    ))
    result = reg.execute("test_tool", {"x": "hello"})
    assert result == "result: hello"
    result_missing = reg.execute("nonexistent", {})
    assert "ERROR" in result_missing

def test_tool_parse():
    reg = ToolRegistry()
    agent = ReACTAgent.__new__(ReACTAgent)
    agent.tools = reg
    response = '<tool_call>{"name": "get_market_signals", "parameters": {"market_id": "abc123"}}</tool_call>'
    calls = agent._parse_tool_calls(response)
    assert len(calls) == 1
    assert calls[0]['name'] == 'get_market_signals'
    assert calls[0]['parameters']['market_id'] == 'abc123'

def test_final_answer_extraction():
    agent = ReACTAgent.__new__(ReACTAgent)
    response = 'Final Answer:\n```json\n{"action": "BUY_YES", "edge": 0.05, "confidence": 0.72}\n```'
    result = agent._extract_final_answer(response)
    assert result['action'] == 'BUY_YES'
    assert result['edge'] == 0.05

test("Tool registry", test_tool_registry)
test("Tool call parsing", test_tool_parse)
test("Final answer extraction", test_final_answer_extraction)

# ─────────────────────────────────────────────────────────────
print("\n=== 6. Config Loader ===")
# ─────────────────────────────────────────────────────────────
from config import load_config

def test_config_load():
    cfg = load_config('config/config.yaml')
    assert 'llm' in cfg
    assert 'polymarket' in cfg
    assert 'risk' in cfg
    assert 'strategy' in cfg
    assert 'learning' in cfg
    assert 'agent' in cfg
    assert cfg['risk']['min_edge_threshold'] > 0
    assert cfg['agent']['context_handoff_threshold'] == 0.56

test("Config loader", test_config_load)

# ─────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  Results: {PASS} passed, {FAIL} failed")
print(f"{'='*50}\n")
if FAIL > 0:
    sys.exit(1)
