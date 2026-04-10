#!/usr/bin/env python3
"""
Synthetic Backtest Runner
=========================
Runs a full walk-forward backtest using synthetic Polymarket-like data.
Does not require API keys — useful for strategy validation and CI.

Generates:
  - backtesting/results/synthetic_backtest_results.json
  - backtesting/results/synthetic_backtest_report.md
  - backtesting/results/equity_curve.png
"""
import sys, os, json, math, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '/home/ubuntu/polyterm')
sys.path.insert(0, '/home/ubuntu/Kronos')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime, timedelta

from backtesting.backtest_engine import PortfolioSimulator, MetricsCalculator, BacktestTrade
from strategies.strategies import (
    MispricingHunterStrategy, MomentumFollowerStrategy, EnsembleStrategy,
    KellyCriterion, TradeAction
)
from learning.self_learning import PerformanceScorer, WeightAdapter, ThresholdTuner

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

INITIAL_BANKROLL = 1000.0
N_MARKETS = 30
N_PERIODS = 500          # hourly candles per market
WALK_FORWARD_WINDOWS = 4
TRANSACTION_COST = 0.002
HOLDING_HOURS = 24
MAX_CONCURRENT = 3       # strict limit — never exceed 3 open at once
MIN_EDGE = 0.04          # tighter edge filter
MIN_CONF = 0.65          # tighter confidence filter
MAX_KELLY = 0.03         # max 3% per trade to preserve bankroll

STRAT_CONFIG = {
    'risk': {
        'min_edge_threshold': MIN_EDGE,
        'min_confidence': MIN_CONF,
        'kelly_fraction': 0.25,
        'max_bankroll_per_trade': MAX_KELLY,
    },
    'strategy': {
        'ensemble_weights': {
            'mispricing_hunter': 0.35,
            'momentum_follower': 0.25,
            'arbitrage_scanner': 0.20,
            'whale_follower': 0.20,
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Synthetic market generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_market(market_idx: int, n_periods: int, seed: int) -> dict:
    """Generate a synthetic binary prediction market with realistic price dynamics."""
    np.random.seed(seed)

    # Market metadata
    categories = ['crypto', 'politics', 'sports', 'economics', 'science']
    cat = categories[market_idx % len(categories)]
    question = f"Will {cat.title()} Event {market_idx} resolve YES?"

    # Price simulation: Brownian motion with mean-reversion toward resolution
    price = np.random.uniform(0.3, 0.7)
    prices = [price]
    resolution_direction = 1 if np.random.random() > 0.45 else 0  # 55% YES rate

    for i in range(1, n_periods):
        # Drift toward resolution in final 30%
        if i > n_periods * 0.70:
            target = 0.85 if resolution_direction == 1 else 0.15
            drift = (target - price) * 0.03
        else:
            drift = np.random.normal(0, 0.003)

        # Occasional regime shifts (news events)
        if np.random.random() < 0.01:
            drift += np.random.choice([-0.08, 0.08])

        noise = np.random.normal(0, 0.008)
        price = float(np.clip(price + drift + noise, 0.02, 0.98))
        prices.append(price)

    prices = np.array(prices)
    timestamps = pd.date_range(start='2024-01-01', periods=n_periods, freq='1h')

    # Simulate volume (higher near resolution)
    base_volume = np.random.uniform(5000, 50000)
    volume_mult = np.linspace(1.0, 3.0, n_periods)
    volumes = base_volume * volume_mult * np.random.uniform(0.5, 1.5, n_periods)

    return {
        'id': f'synthetic_{market_idx:03d}',
        'question': question,
        'category': cat,
        'liquidity': float(np.random.uniform(10000, 100000)),
        'volume24hr': float(np.random.uniform(2000, 20000)),
        'lastTradePrice': float(prices[-1]),
        'resolution': resolution_direction,
        'prices': prices,
        'volumes': volumes,
        'timestamps': timestamps,
    }


def price_to_forecast(prices: np.ndarray, idx: int) -> dict:
    """Generate a Kronos-like forecast from price history."""
    if idx < 20:
        return None

    history = prices[:idx]
    current = float(history[-1])

    # Statistical forecast: weighted moving average + momentum
    weights = np.exp(np.linspace(-2, 0, min(60, len(history))))
    weights /= weights.sum()
    wma = float(np.dot(history[-len(weights):], weights))

    # Momentum
    short_ma = float(np.mean(history[-5:]))
    long_ma = float(np.mean(history[-20:]))
    momentum = (short_ma - long_ma) / max(long_ma, 0.01)

    # Predicted price
    predicted = float(np.clip(current + momentum * 0.3 + (wma - current) * 0.2, 0.02, 0.98))

    # Uncertainty from recent volatility
    vol = float(np.std(history[-20:]))
    confidence = float(np.clip(1.0 - vol * 10, 0.50, 0.92))

    direction = 'bullish' if predicted > current else 'bearish'

    return {
        'current_price': current,
        'predicted_price': predicted,
        'direction': direction,
        'confidence': confidence,
        'uncertainty_std': vol,
        'model': 'statistical_wma',
        'horizon_hours': HOLDING_HOURS,
    }


def price_to_signals(prices: np.ndarray, volumes: np.ndarray, idx: int) -> dict:
    """Generate polyterm-like signals from price/volume history."""
    if idx < 20:
        return {}

    history = prices[:idx]
    vol_history = volumes[:idx]

    short_ma = float(np.mean(history[-5:]))
    long_ma = float(np.mean(history[-20:]))
    price_change = (history[-1] - history[-5]) / max(history[-5], 0.01) * 100

    vol_change = float(np.mean(vol_history[-5:]) / max(np.mean(vol_history[-20:]), 1) - 1)

    bullish_count = sum([
        short_ma > long_ma,
        price_change > 2,
        vol_change > 0.2,
    ])
    bearish_count = 3 - bullish_count

    direction = 'bullish' if bullish_count > bearish_count else 'bearish'
    conf = 0.55 + abs(bullish_count - bearish_count) * 0.10

    return {
        'direction': direction,
        'confidence': conf,
        'probability_change': price_change,
        'signal_summary': {'bullish': bullish_count, 'bearish': bearish_count},
        'volume_change_pct': vol_change * 100,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Backtest runner
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest():
    print("\n" + "="*65)
    print("  POLYMARKET AGENT — SYNTHETIC WALK-FORWARD BACKTEST")
    print("="*65)
    print(f"  Markets          : {N_MARKETS}")
    print(f"  Periods/market   : {N_PERIODS} hours")
    print(f"  Walk-fwd windows : {WALK_FORWARD_WINDOWS}")
    print(f"  Initial bankroll : ${INITIAL_BANKROLL:,.0f}")
    print(f"  Min edge         : {MIN_EDGE:.0%}")
    print(f"  Min confidence   : {MIN_CONF:.0%}")
    print(f"  Max Kelly        : {MAX_KELLY:.0%}")
    print("="*65 + "\n")

    # Generate synthetic markets
    print("Generating synthetic markets...")
    markets = [generate_market(i, N_PERIODS, seed=42+i) for i in range(N_MARKETS)]

    # Strategy objects
    mispricing = MispricingHunterStrategy(STRAT_CONFIG)
    momentum_strat = MomentumFollowerStrategy(STRAT_CONFIG)
    ensemble = EnsembleStrategy(STRAT_CONFIG)

    # Portfolio simulator
    portfolio = PortfolioSimulator(INITIAL_BANKROLL, TRANSACTION_COST)
    all_trades = []

    # Walk-forward windows
    window_size = N_PERIODS // WALK_FORWARD_WINDOWS

    for window_idx in range(WALK_FORWARD_WINDOWS):
        w_start = window_idx * window_size
        w_end = min(w_start + window_size, N_PERIODS)
        print(f"  Window {window_idx+1}/{WALK_FORWARD_WINDOWS}: periods {w_start}–{w_end}")

        open_count = 0
        window_trades = []
        # Track pending exits: {trade_id: (market, exit_idx, exit_price, exit_time)}
        pending_exits: dict = {}

        # Iterate time steps across all markets simultaneously
        for i in range(max(w_start, 30), w_end):
            # First: close any positions whose holding period has expired
            to_close = [tid for tid, info in pending_exits.items() if info['exit_idx'] <= i]
            for tid in to_close:
                info = pending_exits.pop(tid)
                trade = portfolio.close_position(tid, info['exit_price'], info['exit_time'])
                if trade:
                    window_trades.append(trade)
                    open_count -= 1

            # Then: scan for new opportunities if under position limit
            if open_count >= MAX_CONCURRENT:
                continue

            for market in markets:
                if open_count >= MAX_CONCURRENT:
                    break

                prices = market['prices']
                volumes = market['volumes']
                timestamps = market['timestamps']

                if i >= len(prices) - HOLDING_HOURS:
                    continue

                # Skip if already have a position in this market
                if any(info['market_id'] == market['id'] for info in pending_exits.values()):
                    continue

                forecast = price_to_forecast(prices, i)
                if forecast is None:
                    continue

                signals_data = price_to_signals(prices, volumes, i)
                risk = {'overall_grade': 'B', 'overall_score': 72}

                # Generate signals
                sigs = []
                s1 = mispricing.evaluate(market, forecast, risk)
                if s1:
                    sigs.append(s1)
                s2 = momentum_strat.evaluate(market, forecast, signals_data, risk)
                if s2:
                    sigs.append(s2)

                if not sigs:
                    continue

                final_sig = ensemble.combine(sigs)
                if final_sig is None:
                    continue

                if final_sig.edge < MIN_EDGE or final_sig.confidence < MIN_CONF:
                    continue

                # Kelly sizing
                p_win = final_sig.confidence
                entry_price = forecast['current_price']
                b_odds = (1.0 / entry_price - 1.0) if final_sig.action == TradeAction.BUY_YES else (1.0 / (1.0 - entry_price) - 1.0)
                kelly_frac = KellyCriterion.calculate(p_win, max(b_odds, 0.01), 0.25, MAX_KELLY)

                trade_id = f"bt_{market['id']}_{i}"
                entry_time = str(timestamps[i])

                pos_size = portfolio.open_position(
                    trade_id=trade_id,
                    market_id=market['id'],
                    market_title=market['question'][:60],
                    strategy=final_sig.strategy,
                    action=final_sig.action.value,
                    entry_price=entry_price,
                    kelly_fraction=kelly_frac,
                    edge_estimate=final_sig.edge,
                    confidence=final_sig.confidence,
                    entry_time=entry_time,
                )
                if pos_size is None:
                    continue

                open_count += 1

                # Schedule exit
                exit_idx = min(i + HOLDING_HOURS, len(prices) - 1)
                pending_exits[trade_id] = {
                    'market_id': market['id'],
                    'exit_idx': exit_idx,
                    'exit_price': float(prices[exit_idx]),
                    'exit_time': str(timestamps[exit_idx]),
                }

        # Close any remaining open positions at end of window
        for tid, info in list(pending_exits.items()):
            trade = portfolio.close_position(tid, info['exit_price'], info['exit_time'])
            if trade:
                window_trades.append(trade)
                open_count -= 1
        pending_exits.clear()

        all_trades.extend(window_trades)
        print(f"    → {len(window_trades)} trades executed")

        # Adaptive learning between windows
        if window_idx < WALK_FORWARD_WINDOWS - 1 and len(window_trades) >= 5:
            _adapt_thresholds(window_trades)

    # Final metrics
    calc = MetricsCalculator()
    metrics = calc.calculate(all_trades, portfolio.equity_curve, INITIAL_BANKROLL)

    # Monte Carlo
    mc = _monte_carlo(all_trades, INITIAL_BANKROLL, n_sims=1000)

    # Strategy breakdown
    scorer = PerformanceScorer()
    from learning.self_learning import TradeRecord
    trade_records = [
        TradeRecord(
            trade_id=t.trade_id, market_id=t.market_id, market_title=t.market_title,
            strategy=t.strategy, action=t.action, entry_price=t.entry_price,
            position_size=t.position_size, entry_time=t.entry_time,
            edge_estimate=t.edge_estimate, confidence=t.confidence,
            model_predicted_price=t.entry_price,
            exit_price=t.exit_price, pnl=t.pnl, pnl_pct=t.pnl_pct,
            resolved=True, resolution_time=t.exit_time, outcome=t.outcome,
        )
        for t in all_trades
    ]
    strategy_perfs = scorer.score(trade_records)

    return metrics, mc, all_trades, portfolio.equity_curve, strategy_perfs


def _adapt_thresholds(trades):
    """Simulate adaptive threshold tuning between windows."""
    from learning.self_learning import TradeRecord
    records = [
        TradeRecord(
            trade_id=t.trade_id, market_id=t.market_id, market_title=t.market_title,
            strategy=t.strategy, action=t.action, entry_price=t.entry_price,
            position_size=t.position_size, entry_time=t.entry_time,
            edge_estimate=t.edge_estimate, confidence=t.confidence,
            model_predicted_price=t.entry_price,
            exit_price=t.exit_price, pnl=t.pnl, pnl_pct=t.pnl_pct,
            resolved=True, resolution_time=t.exit_time, outcome=t.outcome,
        )
        for t in trades
    ]
    tuner = ThresholdTuner()
    new_edge, new_conf = tuner.tune(records, MIN_EDGE, MIN_CONF)
    # (In live agent, these would be written back to config)
    return new_edge, new_conf


def _monte_carlo(trades, initial_bankroll, n_sims=1000):
    if not trades:
        return {}
    returns = np.array([t.pnl_pct for t in trades])
    n = len(returns)
    finals = []
    for _ in range(n_sims):
        sampled = np.random.choice(returns, size=n, replace=True)
        equity = initial_bankroll
        for r in sampled:
            equity *= (1 + r)
        finals.append(equity)
    arr = np.array(finals)
    return {
        'n_simulations': n_sims,
        'median_final_bankroll': round(float(np.median(arr)), 2),
        'p5_final_bankroll': round(float(np.percentile(arr, 5)), 2),
        'p95_final_bankroll': round(float(np.percentile(arr, 95)), 2),
        'probability_of_profit': round(float(np.mean(arr > initial_bankroll)), 4),
        'probability_of_ruin': round(float(np.mean(arr < initial_bankroll * 0.5)), 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Visualisation
# ─────────────────────────────────────────────────────────────────────────────

def generate_charts(metrics, mc, trades, equity_curve, strategy_perfs, out_dir):
    """Generate comprehensive performance charts."""
    os.makedirs(out_dir, exist_ok=True)

    fig = plt.figure(figsize=(18, 14))
    fig.patch.set_facecolor('#0d1117')
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

    GOLD = '#FFD700'
    GREEN = '#00FF88'
    RED = '#FF4444'
    BLUE = '#4488FF'
    GRAY = '#888888'
    BG = '#161b22'
    TEXT = '#e6edf3'

    def style_ax(ax, title):
        ax.set_facecolor(BG)
        ax.set_title(title, color=GOLD, fontsize=11, fontweight='bold', pad=8)
        ax.tick_params(colors=GRAY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#30363d')
        ax.grid(True, color='#21262d', linewidth=0.5, alpha=0.7)

    # 1. Equity curve
    ax1 = fig.add_subplot(gs[0, :2])
    eq = np.array(equity_curve)
    x = np.arange(len(eq))
    ax1.fill_between(x, INITIAL_BANKROLL, eq,
                     where=eq >= INITIAL_BANKROLL, alpha=0.2, color=GREEN)
    ax1.fill_between(x, INITIAL_BANKROLL, eq,
                     where=eq < INITIAL_BANKROLL, alpha=0.2, color=RED)
    ax1.plot(x, eq, color=GREEN, linewidth=1.5, label='Portfolio Value')
    ax1.axhline(INITIAL_BANKROLL, color=GRAY, linestyle='--', linewidth=0.8, label='Initial Capital')
    ax1.set_xlabel('Trade #', color=GRAY, fontsize=8)
    ax1.set_ylabel('Bankroll (USDC)', color=GRAY, fontsize=8)
    ax1.legend(fontsize=8, facecolor=BG, labelcolor=TEXT)
    style_ax(ax1, 'Portfolio Equity Curve')

    # 2. Drawdown
    ax2 = fig.add_subplot(gs[0, 2])
    running_max = np.maximum.accumulate(eq)
    drawdown = (running_max - eq) / np.maximum(running_max, 1e-9) * 100
    ax2.fill_between(x, 0, -drawdown, color=RED, alpha=0.6)
    ax2.set_xlabel('Trade #', color=GRAY, fontsize=8)
    ax2.set_ylabel('Drawdown (%)', color=GRAY, fontsize=8)
    style_ax(ax2, 'Drawdown')

    # 3. P&L distribution
    ax3 = fig.add_subplot(gs[1, 0])
    pnl_pcts = [t.pnl_pct * 100 for t in trades]
    wins = [p for p in pnl_pcts if p > 0]
    losses = [p for p in pnl_pcts if p <= 0]
    if wins:
        ax3.hist(wins, bins=20, color=GREEN, alpha=0.7, label='Wins')
    if losses:
        ax3.hist(losses, bins=20, color=RED, alpha=0.7, label='Losses')
    ax3.axvline(0, color=GRAY, linestyle='--', linewidth=0.8)
    ax3.set_xlabel('P&L (%)', color=GRAY, fontsize=8)
    ax3.legend(fontsize=7, facecolor=BG, labelcolor=TEXT)
    style_ax(ax3, 'P&L Distribution')

    # 4. Strategy performance
    ax4 = fig.add_subplot(gs[1, 1])
    strat_names = list(strategy_perfs.keys())
    strat_wr = [strategy_perfs[s].win_rate * 100 for s in strat_names]
    colors = [GREEN if wr > 55 else (GOLD if wr > 50 else RED) for wr in strat_wr]
    bars = ax4.barh(strat_names, strat_wr, color=colors, alpha=0.8)
    ax4.axvline(50, color=GRAY, linestyle='--', linewidth=0.8)
    ax4.set_xlabel('Win Rate (%)', color=GRAY, fontsize=8)
    for bar, wr in zip(bars, strat_wr):
        ax4.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                 f'{wr:.1f}%', va='center', color=TEXT, fontsize=7)
    style_ax(ax4, 'Strategy Win Rates')

    # 5. Monte Carlo distribution
    ax5 = fig.add_subplot(gs[1, 2])
    np.random.seed(42)
    returns = np.array([t.pnl_pct for t in trades])
    mc_finals = []
    for _ in range(500):
        sampled = np.random.choice(returns, size=len(returns), replace=True)
        eq_mc = INITIAL_BANKROLL
        for r in sampled:
            eq_mc *= (1 + r)
        mc_finals.append(eq_mc)
    mc_arr = np.array(mc_finals)
    ax5.hist(mc_arr, bins=40, color=BLUE, alpha=0.7, edgecolor='none')
    ax5.axvline(INITIAL_BANKROLL, color=GOLD, linestyle='--', linewidth=1, label='Initial')
    ax5.axvline(float(np.median(mc_arr)), color=GREEN, linestyle='-', linewidth=1.5, label='Median')
    ax5.axvline(float(np.percentile(mc_arr, 5)), color=RED, linestyle=':', linewidth=1, label='P5')
    ax5.set_xlabel('Final Bankroll (USDC)', color=GRAY, fontsize=8)
    ax5.legend(fontsize=7, facecolor=BG, labelcolor=TEXT)
    style_ax(ax5, 'Monte Carlo (500 sims)')

    # 6. Key metrics summary
    ax6 = fig.add_subplot(gs[2, :])
    ax6.axis('off')
    ax6.set_facecolor(BG)

    kpis = [
        ('Total Trades', str(metrics['total_trades'])),
        ('Win Rate', f"{metrics['win_rate']:.1%}"),
        ('Total P&L', f"${metrics['total_pnl']:+.2f}"),
        ('Return', f"{metrics['total_pnl_pct']:+.1%}"),
        ('Sharpe', f"{metrics['sharpe_ratio']:.3f}"),
        ('Sortino', f"{metrics['sortino_ratio']:.3f}"),
        ('Max DD', f"{metrics['max_drawdown']:.1%}"),
        ('Calmar', f"{metrics['calmar_ratio']:.3f}"),
        ('Profit Factor', f"{metrics['profit_factor']:.3f}"),
        ('MC P(Profit)', f"{mc.get('probability_of_profit', 0):.1%}"),
    ]

    n_kpis = len(kpis)
    col_w = 1.0 / n_kpis
    for j, (label, value) in enumerate(kpis):
        x_pos = (j + 0.5) * col_w
        color = GREEN if 'P&L' in label or 'Return' in label else GOLD
        if 'P&L' in label and metrics['total_pnl'] < 0:
            color = RED
        ax6.text(x_pos, 0.75, label, ha='center', va='center',
                 color=GRAY, fontsize=9, transform=ax6.transAxes)
        ax6.text(x_pos, 0.35, value, ha='center', va='center',
                 color=color, fontsize=14, fontweight='bold', transform=ax6.transAxes)

    ax6.set_title('Key Performance Indicators', color=GOLD, fontsize=11,
                  fontweight='bold', pad=8)
    for spine in ax6.spines.values():
        spine.set_edgecolor('#30363d')

    fig.suptitle(
        'Polymarket Autonomous Trading Agent — Synthetic Walk-Forward Backtest',
        color=TEXT, fontsize=14, fontweight='bold', y=0.98
    )

    chart_path = os.path.join(out_dir, 'backtest_dashboard.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Chart saved: {chart_path}")
    return chart_path


# ─────────────────────────────────────────────────────────────────────────────
# Report generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(metrics, mc, trades, strategy_perfs, out_dir):
    """Generate a Markdown performance report."""
    os.makedirs(out_dir, exist_ok=True)

    lines = [
        "# Polymarket Autonomous Trading Agent — Backtest Report",
        "",
        f"> **Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"> **Mode**: Synthetic Walk-Forward Backtest ({WALK_FORWARD_WINDOWS} windows)  ",
        f"> **Markets**: {N_MARKETS} synthetic binary prediction markets  ",
        f"> **Period**: {N_PERIODS} hourly candles per market",
        "",
        "---",
        "",
        "## Portfolio Performance",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Initial Bankroll | ${INITIAL_BANKROLL:,.2f} |",
        f"| Final Bankroll | ${metrics['final_bankroll']:,.2f} |",
        f"| Total P&L | ${metrics['total_pnl']:+,.2f} |",
        f"| Total Return | {metrics['total_pnl_pct']:+.2%} |",
        f"| Total Trades | {metrics['total_trades']} |",
        f"| Win Rate | {metrics['win_rate']:.2%} |",
        f"| Winning Trades | {metrics['winning_trades']} |",
        f"| Losing Trades | {metrics['losing_trades']} |",
        f"| Avg Trade P&L | ${metrics['avg_trade_pnl']:+.4f} |",
        f"| Avg Winning Trade | ${metrics['avg_winning_trade']:+.4f} |",
        f"| Avg Losing Trade | ${metrics['avg_losing_trade']:+.4f} |",
        "",
        "## Risk-Adjusted Metrics",
        "",
        "| Metric | Value | Interpretation |",
        "|--------|-------|----------------|",
        f"| Sharpe Ratio | {metrics['sharpe_ratio']:.4f} | {'Excellent' if metrics['sharpe_ratio'] > 2 else 'Good' if metrics['sharpe_ratio'] > 1 else 'Moderate'} |",
        f"| Sortino Ratio | {metrics['sortino_ratio']:.4f} | Downside risk-adjusted |",
        f"| Max Drawdown | {metrics['max_drawdown']:.2%} | {'Low' if metrics['max_drawdown'] < 0.10 else 'Moderate' if metrics['max_drawdown'] < 0.20 else 'High'} |",
        f"| Calmar Ratio | {metrics['calmar_ratio']:.4f} | Return / Max DD |",
        f"| Profit Factor | {metrics['profit_factor']:.4f} | Gross profit / Gross loss |",
        "",
        "## Monte Carlo Simulation (1,000 runs)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Median Final Bankroll | ${mc.get('median_final_bankroll', 0):,.2f} |",
        f"| 5th Percentile | ${mc.get('p5_final_bankroll', 0):,.2f} |",
        f"| 95th Percentile | ${mc.get('p95_final_bankroll', 0):,.2f} |",
        f"| Probability of Profit | {mc.get('probability_of_profit', 0):.2%} |",
        f"| Probability of Ruin (>50% loss) | {mc.get('probability_of_ruin', 0):.2%} |",
        "",
        "## Strategy Breakdown",
        "",
        "| Strategy | Trades | Win Rate | Total P&L | Sharpe |",
        "|----------|--------|----------|-----------|--------|",
    ]

    for strat, perf in strategy_perfs.items():
        lines.append(
            f"| {strat} | {perf.total_trades} | {perf.win_rate:.2%} | "
            f"${perf.total_pnl:+.4f} | {perf.sharpe_ratio:.3f} |"
        )

    lines += [
        "",
        "## Architecture Overview",
        "",
        "The agent integrates four source repositories into a unified pipeline:",
        "",
        "| Component | Source | Role |",
        "|-----------|--------|------|",
        "| **polyterm** | NYTEMODEONLY/polyterm | Market data, CLOB API, signals, arbitrage scanner, whale tracker |",
        "| **Kronos** | shiyu-coder/Kronos | Time-series price forecasting (transformer-based) |",
        "| **hermes-agent** | NousResearch/hermes-agent | Tool-calling ReACT loop, prompt builder, agent lifecycle |",
        "| **MiroFish** | 666ghj/MiroFish | Context window tracking, agent handoff, graph memory, retry logic |",
        "",
        "## Self-Learning Mechanisms",
        "",
        "1. **Outcome Tracker** — Append-only JSONL log of every trade and its resolution",
        "2. **Performance Scorer** — Per-strategy win rate, Sharpe, edge accuracy",
        "3. **Weight Adapter** — EMA-based ensemble weight adaptation (α=0.10)",
        "4. **Threshold Tuner** — Grid-search optimisation of min_edge and min_confidence",
        "5. **Knowledge Compressor** — MiroFish-inspired episode compression into rolling JSONL",
        "",
        "## Context Window Management",
        "",
        "The agent monitors token utilisation continuously. When usage reaches **56%** of the",
        "model's context window, an automatic handoff is triggered:",
        "",
        "1. Outgoing agent compresses conversation history into a structured handoff packet",
        "2. Packet includes: portfolio state, open positions, strategy weights, recent decisions,",
        "   and a natural-language summary of key findings",
        "3. Incoming agent (new instance) receives the packet as its first system message",
        "4. Generation counter increments; full context is preserved losslessly",
        "",
        "---",
        "",
        f"*Report generated by Polymarket Autonomous Trading Agent v1.0*",
    ]

    report_path = os.path.join(out_dir, 'backtest_report.md')
    with open(report_path, 'w') as fh:
        fh.write('\n'.join(lines))
    print(f"  Report saved: {report_path}")
    return report_path


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

    metrics, mc, trades, equity_curve, strategy_perfs = run_backtest()

    print("\n" + "="*65)
    print("  BACKTEST RESULTS")
    print("="*65)
    print(f"  Total Trades     : {metrics['total_trades']}")
    print(f"  Win Rate         : {metrics['win_rate']:.2%}")
    print(f"  Total P&L        : ${metrics['total_pnl']:+.2f}")
    print(f"  Total Return     : {metrics['total_pnl_pct']:+.2%}")
    print(f"  Sharpe Ratio     : {metrics['sharpe_ratio']:.4f}")
    print(f"  Sortino Ratio    : {metrics['sortino_ratio']:.4f}")
    print(f"  Max Drawdown     : {metrics['max_drawdown']:.2%}")
    print(f"  Calmar Ratio     : {metrics['calmar_ratio']:.4f}")
    print(f"  Profit Factor    : {metrics['profit_factor']:.4f}")
    print(f"\n  Monte Carlo (1000 sims):")
    print(f"  Median Final     : ${mc.get('median_final_bankroll', 0):,.2f}")
    print(f"  P5 / P95         : ${mc.get('p5_final_bankroll', 0):,.2f} / ${mc.get('p95_final_bankroll', 0):,.2f}")
    print(f"  P(Profit)        : {mc.get('probability_of_profit', 0):.2%}")
    print(f"  P(Ruin)          : {mc.get('probability_of_ruin', 0):.2%}")
    print("="*65)

    print("\nGenerating charts and report...")
    chart_path = generate_charts(metrics, mc, trades, equity_curve, strategy_perfs, OUT_DIR)
    report_path = generate_report(metrics, mc, trades, strategy_perfs, OUT_DIR)

    # Save JSON results
    results_json = {
        'timestamp': datetime.utcnow().isoformat(),
        'config': {
            'n_markets': N_MARKETS,
            'n_periods': N_PERIODS,
            'walk_forward_windows': WALK_FORWARD_WINDOWS,
            'initial_bankroll': INITIAL_BANKROLL,
            'min_edge': MIN_EDGE,
            'min_confidence': MIN_CONF,
            'max_kelly': MAX_KELLY,
        },
        'metrics': metrics,
        'monte_carlo': mc,
        'strategy_breakdown': {k: v.to_dict() for k, v in strategy_perfs.items()},
    }
    json_path = os.path.join(OUT_DIR, 'synthetic_backtest_results.json')
    with open(json_path, 'w') as fh:
        json.dump(results_json, fh, indent=2, default=str)
    print(f"  JSON saved: {json_path}")
    print("\nDone.")
