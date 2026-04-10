#!/usr/bin/env python3
"""
Polymarket Autonomous Trading Agent
====================================
Main entry point. Supports three modes:
  - backtest   : Run historical walk-forward backtest
  - live       : Run autonomous live (or paper) trading loop
  - report     : Generate performance report from trade logs

Usage:
  python main.py backtest --start 2024-01-01 --end 2024-12-31
  python main.py live
  python main.py report
"""

import argparse
import json
import logging
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger("polymarket.main")


def cmd_backtest(args) -> None:
    """Run historical backtest."""
    from agent.orchestrator import PolymarketOrchestrator

    print(f"\n{'='*60}")
    print("  POLYMARKET AGENT — BACKTEST MODE")
    print(f"{'='*60}")
    print(f"  Period  : {args.start} → {args.end}")
    print(f"  Markets : {args.markets}")
    print(f"  Config  : {args.config}")
    print(f"{'='*60}\n")

    orchestrator = PolymarketOrchestrator(config_path=args.config)
    results = orchestrator.run_backtest(
        start_date=args.start,
        end_date=args.end,
        n_markets=args.markets,
    )

    print("\n" + results["summary"])
    print("\n--- Monte Carlo Simulation (1000 runs) ---")
    mc = results.get("monte_carlo", {})
    if mc:
        print(f"  Median final bankroll : ${mc.get('median_final_bankroll', 0):.2f}")
        print(f"  5th percentile        : ${mc.get('p5_final_bankroll', 0):.2f}")
        print(f"  95th percentile       : ${mc.get('p95_final_bankroll', 0):.2f}")
        print(f"  Probability of profit : {mc.get('probability_of_profit', 0):.1%}")
        print(f"  Probability of ruin   : {mc.get('probability_of_ruin', 0):.1%}")

    # Save full results
    os.makedirs("backtesting/results", exist_ok=True)
    out_path = f"backtesting/results/backtest_{args.start}_{args.end}.json"
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    print(f"\nFull results saved to: {out_path}")


def cmd_live(args) -> None:
    """Run live (or paper) trading loop."""
    from agent.orchestrator import PolymarketOrchestrator

    print(f"\n{'='*60}")
    print("  POLYMARKET AGENT — LIVE TRADING MODE")
    print(f"{'='*60}")
    print(f"  Config  : {args.config}")
    print(f"  Mode    : {'PAPER TRADING' if True else 'LIVE TRADING'}")
    print(f"{'='*60}\n")

    orchestrator = PolymarketOrchestrator(config_path=args.config)
    orchestrator.run()


def cmd_report(args) -> None:
    """Generate performance report from trade logs."""
    from learning.self_learning import SelfLearningEngine
    from config import load_config

    config = load_config(args.config)
    engine = SelfLearningEngine(config)
    summary = engine.get_performance_summary()

    print(f"\n{'='*60}")
    print("  POLYMARKET AGENT — PERFORMANCE REPORT")
    print(f"{'='*60}")

    portfolio = summary.get("portfolio", {})
    if portfolio:
        print(f"\n  Total Trades    : {portfolio.get('total_trades', 0)}")
        print(f"  Win Rate        : {portfolio.get('win_rate', 0):.1%}")
        print(f"  Total P&L       : ${portfolio.get('total_pnl', 0):.2f}")
        print(f"  Sharpe Ratio    : {portfolio.get('sharpe_ratio', 0):.3f}")
        print(f"  Max Drawdown    : {portfolio.get('max_drawdown', 0):.1%}")
        print(f"  Calmar Ratio    : {portfolio.get('calmar_ratio', 0):.3f}")
    else:
        print("\n  No resolved trades yet.")

    by_strategy = summary.get("by_strategy", {})
    if by_strategy:
        print("\n  --- Strategy Breakdown ---")
        for strat, perf in by_strategy.items():
            print(f"  {strat:<25} WR={perf.get('win_rate', 0):.0%} "
                  f"Trades={perf.get('total_trades', 0)} "
                  f"P&L=${perf.get('total_pnl', 0):.2f}")

    print(f"\n  Unresolved positions : {summary.get('unresolved_trades', 0)}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Autonomous Trading Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # backtest
    bt_parser = subparsers.add_parser("backtest", help="Run historical backtest")
    bt_parser.add_argument("--start", default="2024-01-01", help="Start date (YYYY-MM-DD)")
    bt_parser.add_argument("--end", default="2024-12-31", help="End date (YYYY-MM-DD)")
    bt_parser.add_argument("--markets", type=int, default=20, help="Number of markets to test")
    bt_parser.set_defaults(func=cmd_backtest)

    # live
    live_parser = subparsers.add_parser("live", help="Run live/paper trading loop")
    live_parser.set_defaults(func=cmd_live)

    # report
    rpt_parser = subparsers.add_parser("report", help="Generate performance report")
    rpt_parser.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
