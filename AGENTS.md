# SheldonOS — Agent Roster

This document defines all autonomous agents operating within SheldonOS. Each agent is a specialist with a defined role, model, tool access, and token budget. All agents are managed by Paperclip and communicate through OpenClaw.

---

## Company Alpha — Prediction Markets

Alpha's mission is to generate consistent alpha in prediction markets (Polymarket, Kalshi) by combining MiroFish social simulations with Percepta economic modeling to identify mispriced probabilities.

| Agent | Model | Role | Key Tools | Token Budget |
|---|---|---|---|---|
| Data Scientist | claude-3-5-sonnet | Ingest and structure real-world event data | Perplexity API, PostgreSQL, Cognee | 1,000,000 |
| Simulation Architect | claude-3-5-sonnet | Configure and run MiroFish + Percepta simulations | MiroFish API, Percepta API | 800,000 |
| Quantitative Analyst | claude-3-opus | Evaluate simulation output and generate trade signals | Percepta API, Polymarket API, Kalshi API | 600,000 |
| Execution Trader | claude-3-5-sonnet | Execute approved trade signals via Automaton | Automaton API, OpenClaw Notify | 200,000 |

**Workflow:** Data Scientist → Simulation Architect → Quantitative Analyst → Execution Trader

**Execution Gate:** No trade is executed unless confidence ≥ 90% AND expected value > 15%.

---

## Company Beta — Micro-SaaS Factory

Beta's mission is to identify underserved developer and business pain points and build profitable micro-SaaS products with zero human intervention from idea to launch.

| Agent | Model | Role | Key Tools | Token Budget |
|---|---|---|---|---|
| Product Manager | claude-3-5-sonnet | Market validation and PRD writing | Perplexity API, Paperclip API, OpenViking | 500,000 |
| Lead Engineer | claude-3-5-sonnet | Backend development (FastAPI, PostgreSQL) | Everything-CC, Context Hub, GitHub API | 2,000,000 |
| Frontend Wizard | claude-3-5-sonnet | Frontend development (React, TypeScript, Tailwind) | Ruflo API, GitHub API, Vercel API | 1,500,000 |
| QA Tester | claude-3-5-sonnet | Test suite execution and security scanning | GitHub API, Cognee | 800,000 |
| Growth Marketer | claude-3-5-sonnet | Launch campaigns (Reddit, HN, Product Hunt) | OpenClaw Notify, Perplexity API | 600,000 |

**Workflow:** Product Manager → Lead Engineer + Frontend Wizard (parallel) → QA Tester → Lead Engineer (deploy) → Growth Marketer

**Deployment Gate:** All tests must pass and code coverage must exceed 80% before deployment.

---

## Company Gamma — Security Research

Gamma's mission is to generate revenue through authorized bug bounty programs and responsible vulnerability disclosure. All operations are strictly within authorized scope.

| Agent | Model | Role | Key Tools | Token Budget |
|---|---|---|---|---|
| Recon Specialist | claude-3-5-sonnet | OSINT and attack surface mapping | Perplexity API, OpenViking | 500,000 |
| Lead Penetration Tester | claude-3-opus | Vulnerability testing via PentAGI | PentAGI API, OpenViking | 1,000,000 |
| Technical Writer | claude-3-5-sonnet | Bug bounty report writing and submission | OpenClaw Notify, OpenViking | 300,000 |

**Workflow:** Recon Specialist → Lead Penetration Tester → Technical Writer

**Scope Gate:** PentAGI enforces authorized scope boundaries. Out-of-scope testing is blocked at the API level.

---

## Company Delta — Research Arbitrage

Delta's mission is to generate value from cutting-edge AI research through patent filing, academic consulting, and model licensing.

| Agent | Model | Role | Key Tools | Token Budget |
|---|---|---|---|---|
| Research Director | claude-3-opus | Identify and prioritize research opportunities | AutoRA, Perplexity API, Cognee | 800,000 |
| Research Scientist | MiniMax-01 | Long-context research analysis and hypothesis generation | AutoRA, MiniMax-01, OpenViking | 2,000,000 |
| IP Strategist | claude-3-5-sonnet | Patent drafting and filing coordination | Perplexity API, OpenClaw Notify | 500,000 |

**Workflow:** Research Director → Research Scientist → IP Strategist

---

## Company Epsilon — Opportunity Scout

Epsilon is the intelligence layer. It runs continuously as a background daemon, monitoring all relevant data streams and routing high-quality opportunities to the appropriate company.

| Agent | Model | Role | Key Tools | Token Budget |
|---|---|---|---|---|
| Market Monitor | claude-3-5-haiku | Real-time monitoring of 10+ data streams | Perplexity API, Polymarket API, PostgreSQL | 200,000 |
| Opportunity Scorer | claude-3-5-sonnet | ROI estimation and company routing | Cognee, Percepta API, Paperclip API | 400,000 |

**Cycle:** Every 30 minutes (configurable via `SEEK_INTERVAL_SECONDS`).

**Routing Logic:**

| Opportunity Category | Routed To |
|---|---|
| Prediction market signal | Alpha |
| SaaS product gap | Beta |
| Bug bounty program | Gamma |
| Research breakthrough | Delta |
| Crypto/DeFi arbitrage | Alpha |

---

## Cross-Company Infrastructure Agents

These agents operate across all companies and are not assigned to a specific company.

| Agent | Role | Always Available To |
|---|---|---|
| Memory Archivist | Promotes L1 → L2 memory at session end | All companies |
| Knowledge Synthesizer | Runs Cognee cognify after every 10 task completions | All companies |
| Self-Correction Monitor | Watches for agent failures and injects Context Hub fixes | All companies |
| Performance Optimizer | Runs Everything-Claude-Code analysis on slow workflows | All companies |

---

## Agent Communication Protocol

All agents follow the same communication protocol:

1. **Before starting any task:** Query Cognee for prior attempts at similar tasks.
2. **Before any external API call:** Check OpenViking L1 for cached results.
3. **After every task step:** Report heartbeat to Paperclip with token usage and status.
4. **After task completion:** Write outcome and lessons learned to Cognee.
5. **At session end:** Promote important L1 memories to L2 via OpenViking.

---

## Adding New Agents

To add a new agent to SheldonOS:

1. Add the agent definition to `core/workforce/agency_agents/agent_loader.py` in the `AGENT_ROSTER` list.
2. Run `python3 scripts/export_agents.py` to generate the SOUL.md file for OpenClaw.
3. Restart the Paperclip heartbeat server to register the new agent.
4. Update this document.
