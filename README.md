# SheldonOS

> **A fully autonomous, self-directing economic entity built from the world's most advanced open-source AI systems.**

SheldonOS is a unified operating system for autonomous AI agents. It integrates 18+ cutting-edge research projects into a single, coherent architecture with one goal: **continuous, compounding profit generation with no end date and no hardcoded task list.**

The system runs an infinite `Seek → Adapt → Scale → Optimize` loop. It discovers opportunities, simulates outcomes, spawns right-sized agent teams, executes workflows, and learns from every result — permanently.

---

## Architecture Overview

SheldonOS is organized into five layers, each built from specific open-source projects:

| Layer | Name | Systems | Purpose |
|---|---|---|---|
| 0 | Control Plane | Paperclip, OpenClaw, NemoClaw, Automaton | Governance, routing, sandboxing, execution |
| 1 | Workforce | Agency-Agents, Deer-Flow, Ruflo | Agent teams, workflow DAGs, sub-agent spawning |
| 2 | Cognitive Backbone | OpenViking, Cognee, Context Hub | Memory, knowledge graph, self-correction |
| 3 | Simulation Engine | MiroFish, Percepta, AutoRA | Social simulation, economic math, research |
| 4 | Research & Exploit | PentAGI, Heretic, Perplexity Agent API, Manus | Security research, model liberation, deep web intel |

### The Adaptive Task Loop

```
┌─────────────────────────────────────────────────────────────┐
│                    SHELDONOS MASTER LOOP                    │
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │  SEEK   │───▶│  ADAPT  │───▶│  SCALE  │───▶│OPTIMIZE │  │
│  │         │    │         │    │         │    │         │  │
│  │Perplexity    │Simulation    │Deer-Flow │    │Cognee   │  │
│  │Monitor  │    │Pipeline │    │Workflows│    │Learning │  │
│  │         │    │+Cognee  │    │         │    │         │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       ▲                                             │       │
│       └─────────────────────────────────────────────┘       │
│                    (infinite loop)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## The Five Companies

SheldonOS operates five autonomous "companies" within a single Paperclip deployment. Each company is a specialized profit center with its own agent team, token budget, and revenue strategy.

| Company | Name | Primary Revenue Mechanism | Key Systems |
|---|---|---|---|
| Alpha | Prediction Markets | Polymarket/Kalshi trading via simulation edge | MiroFish + Percepta + Automaton |
| Beta | Micro-SaaS Factory | Build and launch AI-powered micro-SaaS products | Agency-Agents + Deer-Flow + Ruflo |
| Gamma | Security Research | Bug bounty submissions and vulnerability disclosure | PentAGI + Heretic + NemoClaw |
| Delta | Research Arbitrage | Patent filing, academic consulting, model licensing | AutoRA + MiniMax-01 + Cognee |
| Epsilon | Opportunity Scout | Continuous market monitoring and opportunity routing | Perplexity API + Automaton + Cognee |

---

## Integrated Systems

### Layer 0 — Control Plane

**[Paperclip](https://github.com/paperclipai/paperclip)** — The organizational OS. Manages all five companies, their agent teams, token budgets, and heartbeat protocols. Every agent reports to Paperclip after every task step. The `Multi-Company` feature provides complete data isolation between companies.

**[OpenClaw](https://github.com/openclaw/openclaw)** — The communication and routing gateway. Handles all messaging (Telegram, Slack, Discord) and internal API calls between agents. All agent invocations pass through OpenClaw before reaching NemoClaw.

**[NemoClaw](https://github.com/NVIDIA/NemoClaw)** — The hardware-level security sandbox. Enforces Linux Landlock filesystem isolation and seccomp syscall filtering on every agent process. No agent can access the host filesystem, SSH keys, or make unauthorized network connections.

**[Automaton](https://github.com/Conway-Research/automaton)** — The economic execution engine. Manages the crypto wallet, executes trades on Polymarket/Kalshi, and handles all financial transactions. Requires 90%+ confidence before executing any trade.

### Layer 1 — Workforce

**[Agency-Agents](https://github.com/msitarzewski/agency-agents)** — The agent roster. Provides 142+ pre-defined specialist agents (Data Scientist, Lead Engineer, Penetration Tester, etc.) with structured `SOUL.md` definitions for OpenClaw. SheldonOS uses 15 core agents across the five companies.

**[Deer-Flow](https://github.com/bytedance/deer-flow)** — The workflow engine. Decomposes complex goals into multi-step DAGs and manages long-horizon task execution across multiple agents. Pre-built workflow templates exist for SaaS development and prediction market trading.

**[Ruflo](https://github.com/ruvnet/ruflo)** — The sub-agent spawner. Used by the Lead Engineer and Frontend Wizard to spawn temporary sub-agents for complex, parallelizable tasks (e.g., building 10 UI components simultaneously).

### Layer 2 — Cognitive Backbone

**[OpenViking](https://github.com/volcengine/OpenViking)** — The infinite memory system. Provides L0 (working), L1 (episodic), and L2 (long-term archive) memory tiers for all agents. Every agent reads from and writes to OpenViking. No context is ever lost.

**[Cognee](https://github.com/topoteretes/cognee)** — The knowledge graph engine. Structures raw data from OpenViking into a queryable Neo4j graph. Agents query Cognee before every external API call to avoid redundant work and learn from past outcomes.

**[Context Hub](https://github.com/andrewyng/context-hub)** — The self-correction layer. Provides agents with accurate, up-to-date API documentation and context. When an agent's code fails, Context Hub retrieves the correct documentation and the agent self-corrects without human intervention.

### Layer 3 — Simulation Engine

**[MiroFish](https://github.com/666ghj/MiroFish)** — The social simulation engine. Constructs parallel digital worlds populated with AI agents to model how human populations will react to events. The primary input to the prediction market pipeline.

**[Percepta](https://github.com/extradimen/Percepta)** — The economic math engine. Translates MiroFish social dynamics into rigorous financial probability distributions. Computes true probabilities, expected values, and Kelly Criterion position sizes.

**[AutoRA](https://github.com/AutoResearch/autora)** — The automated research engine. Generates and tests scientific hypotheses autonomously. Used by the Delta company for research arbitrage and by Gamma for vulnerability research.

### Layer 4 — Research & Exploit

**[PentAGI](https://github.com/vxcontrol/pentagi)** — The autonomous penetration testing engine. Conducts authorized security assessments for bug bounty programs. All testing is sandboxed within NemoClaw.

**[Heretic](https://github.com/p-e-w/heretic)** — The model liberation tool. Temporarily removes safety alignment from local models for authorized security research and scientific discovery tasks. Decensored models are scoped to NemoClaw and deleted after use.

**[MiniMax-01](https://github.com/MiniMax-AI/MiniMax-01)** — The long-context reasoning engine. Handles tasks requiring extremely long context windows (up to 1M tokens), such as analyzing entire codebases or large research corpora.

**[Perplexity Agent API](https://docs.perplexity.ai/docs/agent-api/quickstart)** — The deep web research runtime. Used by all agents for multi-source web research. Replaces manual headless browser orchestration. Integrated via the `sonar-pro` model.

**[Antigravity-Awesome-Skills](https://github.com/sickn33/antigravity-awesome-skills)** — The skill library. Provides reusable, composable skill modules that agents can load dynamically. When an agent gets stuck, Everything-Claude-Code injects the appropriate skill.

**[Everything-Claude-Code](https://github.com/affaan-m/everything-claude-code)** — The performance optimizer. Monitors agent code execution and injects optimizations when performance degrades. Works in conjunction with Context Hub for self-healing code.

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 22+
- 64 GB RAM minimum (512 GB recommended for full deployment)
- NVIDIA GPU with 24+ GB VRAM (for local model inference)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/SheldonOS.git
cd SheldonOS

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Initialize the database
python3 scripts/init_db.py

# Export agent SOUL.md files to OpenClaw
python3 scripts/export_agents.py

# Start the autonomous orchestrator
python3 orchestrator/sheldon_orchestrator.py
```

### Running as a System Service (Autonomous Boot)

```bash
# Install the systemd service
sudo cp config/sheldon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sheldon
sudo systemctl start sheldon

# Monitor logs
journalctl -u sheldon -f
```

---

## Configuration

All configuration is managed through environment variables. See `.env.example` for the complete list.

The most critical variables are:

| Variable | Description | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key for all agents | Yes |
| `PERPLEXITY_API_KEY` | Perplexity Agent API key for research | Yes |
| `OPENVIKING_API_URL` | OpenViking memory server URL | Yes |
| `COGNEE_API_URL` | Cognee knowledge graph URL | Yes |
| `MIROFISH_API_URL` | MiroFish simulation server URL | Yes |
| `PERCEPTA_API_URL` | Percepta economic engine URL | Yes |
| `CRYPTO_WALLET_PRIVATE_KEY` | Wallet for Automaton trade execution | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot for operator notifications | Recommended |
| `MAX_POSITION_SIZE_USD` | Maximum trade size per signal | Yes |
| `DAILY_LOSS_LIMIT_USD` | Hard stop-loss for trading operations | Yes |

---

## Safety & Security

SheldonOS is designed with a defense-in-depth security model:

**NemoClaw Sandboxing** enforces hardware-level isolation on every agent process. Agents cannot access the host filesystem outside their designated directories, cannot make unauthorized network connections, and cannot execute privileged syscalls.

**Authorized-Only Security Research** — The Gamma company only targets bug bounty programs with explicit written authorization. PentAGI enforces scope boundaries and will refuse to test out-of-scope targets.

**Heretic Scoping** — Decensored models generated by Heretic are scoped to the NemoClaw sandbox, assigned a specific task context, and automatically deleted upon task completion. They are never persisted to disk.

**Financial Risk Controls** — Automaton enforces hard limits on position size (`MAX_POSITION_SIZE_USD`) and daily losses (`DAILY_LOSS_LIMIT_USD`). No trade is executed without 90%+ confidence from the simulation pipeline.

**Operator Notifications** — All significant events (trade execution, new SaaS deployment, bug bounty submission, error states) are sent to the operator via Telegram/Slack through OpenClaw.

---

## Project Structure

```
SheldonOS/
├── orchestrator/
│   └── sheldon_orchestrator.py      # Master Seek→Adapt→Scale loop
├── core/
│   ├── control_plane/
│   │   ├── paperclip/               # Org config, heartbeat server
│   │   ├── openclaw/                # Communication gateway
│   │   ├── nemoclaw/                # Sandbox policy
│   │   └── automaton/               # Economic execution engine
│   ├── workforce/
│   │   ├── agency_agents/           # Agent roster and loader
│   │   ├── deer_flow/               # Workflow DAG orchestrator
│   │   └── ruflo/                   # Sub-agent spawner
│   ├── cognitive/
│   │   ├── openviking/              # Tiered memory client
│   │   ├── cognee/                  # Knowledge graph client
│   │   └── context_hub/             # Self-correction layer
│   ├── simulation/
│   │   ├── simulation_pipeline.py   # MiroFish→Percepta pipeline
│   │   └── autora/                  # Automated research engine
│   └── research/
│       ├── research_engine.py       # PentAGI, Heretic, Perplexity
│       └── minimax/                 # Long-context reasoning
├── config/
│   ├── sheldon.service              # systemd service file
│   └── logging.yaml                 # Logging configuration
├── scripts/
│   ├── init_db.py                   # Database initialization
│   └── export_agents.py             # Export SOUL.md files
├── docker-compose.yml               # All service definitions
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variable template
├── AGENTS.md                        # Agent roster documentation
└── README.md                        # This file
```

---

## Contributing

SheldonOS is designed to be extended. To add a new company or agent team:

1. Define new agents in `core/workforce/agency_agents/agent_loader.py`
2. Create workflow templates in `core/workforce/deer_flow/workflow_orchestrator.py`
3. Add routing logic in `orchestrator/sheldon_orchestrator.py` (`AdaptLayer._route_to_company`)
4. Update `docker-compose.yml` if new services are required

---

## License

MIT License. See `LICENSE` for details.

---

*SheldonOS is a research and development framework. All financial trading, security research, and autonomous operations must comply with applicable laws and regulations in your jurisdiction.*
