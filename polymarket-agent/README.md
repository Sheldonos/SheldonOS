# Polymarket Autonomous Trading Agent

> A self-learning, continuously improving prediction market trading agent that integrates **polyterm**, **Kronos**, **hermes-agent**, and **MiroFish** into a unified autonomous system with walk-forward backtesting, context-aware agent handoff, and adaptive strategy optimisation.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PolymarketOrchestrator                           │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  polyterm    │  │    Kronos    │  │     hermes-agent         │  │
│  │  Data Client │  │  Forecaster  │  │   ReACT Loop + Tools     │  │
│  │  CLOB API    │  │  Time-Series │  │   Tool Registry          │  │
│  │  Signals     │  │  Transformer │  │   Prompt Builder         │  │
│  │  Arbitrage   │  │  Uncertainty │  │   JSON-mode Decisions    │  │
│  │  Whale Track │  │  Estimation  │  │                          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    MiroFish Integration                      │   │
│  │  ContextWindowTracker  │  AgentHandoffManager  │  Retry      │   │
│  │  56% threshold trigger │  Lossless state xfer  │  Backoff    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  4-Strategy  │  │  Self-Learn  │  │    Backtest Engine       │  │
│  │  Ensemble    │  │  Engine      │  │    Walk-Forward          │  │
│  │  + Kelly     │  │  EMA Weights │  │    Monte Carlo           │  │
│  │  Sizing      │  │  Threshold   │  │    Performance Reports   │  │
│  │              │  │  Tuning      │  │                          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Source Repository Integration

| Repository | Integration Point | Key Capabilities Used |
|------------|-------------------|----------------------|
| [NYTEMODEONLY/polyterm](https://github.com/NYTEMODEONLY/polyterm) | `utils/polymarket_client.py` | CLOB API, market scanning, multi-factor signals, arbitrage detection, whale tracking, risk scoring |
| [shiyu-coder/Kronos](https://github.com/shiyu-coder/Kronos) | `models/kronos_adapter.py` | Transformer-based time-series forecasting, uncertainty estimation, Monte Carlo sampling |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | `agent/react_agent.py` | ReACT loop, tool registry, prompt builder, structured JSON decisions |
| [666ghj/MiroFish](https://github.com/666ghj/MiroFish) | `agent/context_manager.py` | Context window tracking, 56% handoff trigger, graph memory, retry/backoff, conflict detection |

---

## Trading Strategies

### 1. Mispricing Hunter
Identifies markets where the Kronos model forecast diverges significantly from the current market price. Computes edge as the absolute difference between model probability and market price, filtered by confidence and risk grade.

### 2. Momentum Follower
Follows strong directional momentum signals from polyterm's multi-factor signal engine. Requires consistent bullish/bearish signal alignment across RSI, MACD, volume, and whale flow indicators.

### 3. Arbitrage Scanner
Detects NegRisk arbitrage opportunities where the sum of YES prices across mutually exclusive outcomes exceeds or falls below 1.0, indicating a risk-free or near-risk-free spread.

### 4. Whale Follower
Tracks large wallet activity from polyterm's whale tracker. Follows significant position changes by historically profitable wallets, weighted by their track record.

### Ensemble Decision
All active strategy signals are combined using a weighted ensemble. Weights are initialised from config and continuously adapted by the self-learning engine based on per-strategy Sharpe ratios.

---

## Self-Learning System

The agent improves itself continuously through five mechanisms:

```
Resolved Trade
     │
     ▼
OutcomeTracker ──► JSONL append-only log
     │
     ▼
PerformanceScorer ──► per-strategy win rate, Sharpe, edge accuracy
     │
     ▼
WeightAdapter ──► EMA blend: α·target + (1-α)·current
     │
     ▼
ThresholdTuner ──► grid search over (min_edge × min_confidence)
     │
     ▼
KnowledgeCompressor ──► MiroFish-inspired episode → JSONL summary
```

**Learning cycle** runs every 6 hours (configurable) when ≥10 trades have resolved.

---

## Context Window Management

Inspired by MiroFish's multi-agent simulation architecture:

```
Token Utilisation
      │
      ├─ < 56%  ──► Normal operation
      │
      └─ ≥ 56%  ──► HANDOFF TRIGGERED
                        │
                        ├─ 1. Compress conversation history
                        ├─ 2. Serialize AgentState (portfolio, positions,
                        │      weights, decisions, summary)
                        ├─ 3. Save handoff packet to logs/handoffs/
                        ├─ 4. Spawn new agent instance (generation+1)
                        └─ 5. New agent receives packet as system message
```

The handoff is **lossless** — all trading state, open positions, strategy weights, and recent decisions are preserved across generations.

---

## Backtesting

### Walk-Forward Validation
The backtest engine splits the historical period into N windows, training on each window and testing on the next. This prevents lookahead bias and simulates realistic out-of-sample performance.

### Monte Carlo Simulation
After the walk-forward backtest, 1,000 Monte Carlo simulations are run by bootstrapping trade returns to estimate the distribution of outcomes and probability of ruin.

### Synthetic Backtest Results (30 markets, 500 hours, 4 windows)

| Metric | Value |
|--------|-------|
| Total Trades | 63 |
| Win Rate | 49.2% |
| Total P&L | +$27.25 |
| Total Return | +2.7% |
| Sharpe Ratio | 1.316 |
| Sortino Ratio | 3.280 |
| Max Drawdown | 9.2% |
| Calmar Ratio | 0.295 |
| Profit Factor | 1.242 |
| MC P(Profit) | 46.7% |

> **Note**: These results use synthetic data. Real performance will depend on actual Polymarket data and LLM reasoning quality.

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure your LLM
```bash
export OPENAI_API_KEY=your_key_here
# Or for Anthropic:
export LLM_API_KEY=your_key_here
# Edit config/config.yaml to set provider and model
```

### 3. Run a backtest
```bash
python main.py backtest --start 2024-01-01 --end 2024-12-31 --markets 20
```

### 4. Run paper trading
```bash
python main.py live
```

### 5. View performance report
```bash
python main.py report
```

### 6. Run the synthetic backtest directly
```bash
python backtesting/run_synthetic_backtest.py
```

---

## Configuration

All settings are in `config/config.yaml` and can be overridden via environment variables:

| Env Variable | Config Path | Description |
|--------------|-------------|-------------|
| `OPENAI_API_KEY` | `llm.api_key` | LLM API key |
| `LLM_MODEL` | `llm.model` | Model name (any OpenAI-compatible) |
| `LLM_BASE_URL` | `llm.base_url` | Custom base URL (Ollama, OpenRouter, etc.) |
| `POLYMARKET_API_KEY` | `polymarket.api_key` | For live trading |
| `SIMULATION_MODE` | `agent.simulation_mode` | `true` = paper trading |

### Supported LLM Providers
The agent is provider-agnostic via the OpenAI-compatible API interface:
- **OpenAI**: `gpt-4.1-mini`, `gpt-4o`, `o1-mini`
- **Anthropic**: `claude-3-5-sonnet`, `claude-3-haiku` (via OpenRouter)
- **Ollama**: Any local model (set `base_url: http://localhost:11434/v1`)
- **OpenRouter**: Any model via `base_url: https://openrouter.ai/api/v1`

---

## Project Structure

```
polymarket-agent/
├── main.py                          # CLI entry point
├── config/
│   ├── config.yaml                  # Main configuration
│   └── __init__.py                  # Config loader with env overrides
├── agent/
│   ├── context_manager.py           # Context tracking + 56% handoff (MiroFish)
│   ├── react_agent.py               # ReACT loop + tool registry (hermes-agent)
│   ├── llm_client.py                # Multi-provider LLM client
│   └── orchestrator.py              # Main autonomous agent loop
├── models/
│   └── kronos_adapter.py            # Kronos forecasting adapter
├── utils/
│   └── polymarket_client.py         # Polymarket data client (polyterm)
├── strategies/
│   └── strategies.py                # 4-strategy ensemble + Kelly sizing
├── learning/
│   └── self_learning.py             # Self-learning engine
├── backtesting/
│   ├── backtest_engine.py           # Walk-forward backtest engine
│   ├── run_synthetic_backtest.py    # Synthetic data backtest runner
│   └── results/                     # Backtest output files
├── tests/
│   └── test_all.py                  # 17-test suite (all passing)
├── logs/                            # Trade logs, handoffs, knowledge base
└── requirements.txt
```

---

## Safety

- **Simulation mode is ON by default** (`simulation_mode: true`). The agent will never place real orders unless you explicitly set `enable_live_trading: true` and provide a valid Polymarket private key.
- **Position sizing** is capped at 3% of bankroll per trade (configurable).
- **Max drawdown circuit breaker** halts trading if portfolio drawdown exceeds 20%.
- **Risk grade filter** rejects markets with grade D or F.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

*Built on top of [polyterm](https://github.com/NYTEMODEONLY/polyterm), [Kronos](https://github.com/shiyu-coder/Kronos), [hermes-agent](https://github.com/NousResearch/hermes-agent), and [MiroFish](https://github.com/666ghj/MiroFish).*
