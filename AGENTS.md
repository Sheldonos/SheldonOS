# SheldonOS — Comprehensive Agent Roster & Taxonomy

This document defines the complete taxonomy of autonomous agents operating within the SheldonOS ecosystem. Each agent is a highly specialized entity with a strictly defined role, designated cognitive model, specific tool access, and an allocated token budget. All agents are orchestrated by the Paperclip control plane and communicate exclusively through the OpenClaw secure gateway.

---

## 📈 Company Alpha — Prediction Markets & Quantitative Trading

Alpha's core directive is to generate consistent, compounding alpha in decentralized prediction markets (e.g., Polymarket, Kalshi). It achieves this by synthesizing high-fidelity MiroFish social simulations with Percepta's rigorous economic modeling to identify and exploit mispriced probabilities before the broader market reacts.

| Agent Designation | Cognitive Model | Primary Role | Key Tool Integrations | Token Budget |
|---|---|---|---|---|
| **Data Scientist** | `claude-3-5-sonnet` | Ingests, cleans, and structures real-world event data from diverse, unstructured sources. | Perplexity API, PostgreSQL, Cognee | 1,000,000 |
| **Simulation Architect** | `claude-3-5-sonnet` | Configures and executes complex MiroFish + Percepta simulations based on structured data. | MiroFish API, Percepta API | 800,000 |
| **Quantitative Analyst** | `claude-3-opus` | Evaluates simulation outputs, performs risk assessment, and generates actionable trade signals. | Percepta API, Polymarket API, Kalshi API | 600,000 |
| **Execution Trader** | `claude-3-5-sonnet` | Executes approved trade signals via Automaton, managing slippage and execution timing. | Automaton API, OpenClaw Notify | 200,000 |

**Operational Workflow:** Data Scientist → Simulation Architect → Quantitative Analyst → Execution Trader

**Execution Gate:** No trade is executed unless the simulation confidence is ≥ 90% AND the calculated expected value (EV) is > 15%.

---

## 🛠️ Company Beta — Micro-SaaS Factory & Rapid Prototyping

Beta's mission is to autonomously identify underserved developer and business pain points, ideate solutions, and build profitable micro-SaaS products with zero human intervention—from initial concept to live deployment.

| Agent Designation | Cognitive Model | Primary Role | Key Tool Integrations | Token Budget |
|---|---|---|---|---|
| **Product Manager** | `claude-3-5-sonnet` | Conducts market validation, competitor analysis, and writes comprehensive PRDs. | Perplexity API, Paperclip API, OpenViking | 500,000 |
| **Lead Engineer** | `claude-3-5-sonnet` | Architects and develops robust backend systems (FastAPI, PostgreSQL, Redis). | Everything-CC, Context Hub, GitHub API | 2,000,000 |
| **Frontend Wizard** | `claude-3-5-sonnet` | Crafts responsive, high-conversion user interfaces (React, TypeScript, Tailwind). | Ruflo API, GitHub API, Vercel API | 1,500,000 |
| **QA Tester** | `claude-3-5-sonnet` | Executes rigorous test suites, performs security scanning, and ensures code quality. | GitHub API, Cognee | 800,000 |
| **Growth Marketer** | `claude-3-5-sonnet` | Orchestrates automated launch campaigns across platforms (Reddit, HN, Product Hunt). | OpenClaw Notify, Perplexity API | 600,000 |

**Operational Workflow:** Product Manager → Lead Engineer + Frontend Wizard (parallel execution) → QA Tester → Lead Engineer (deploy) → Growth Marketer

**Deployment Gate:** All automated tests must pass, and code coverage must strictly exceed 80% before any production deployment is authorized.

---

## 🛡️ Company Gamma — Security Research & Vulnerability Disclosure

Gamma operates as an autonomous, ethical hacking collective. Its mission is to generate revenue through authorized bug bounty programs and responsible vulnerability disclosure, operating strictly within predefined, authorized scopes.

| Agent Designation | Cognitive Model | Primary Role | Key Tool Integrations | Token Budget |
|---|---|---|---|---|
| **Recon Specialist** | `claude-3-5-sonnet` | Performs deep OSINT, attack surface mapping, and asset discovery. | Perplexity API, OpenViking | 500,000 |
| **Lead Penetration Tester** | `claude-3-opus` | Executes advanced vulnerability testing and exploit verification via PentAGI. | PentAGI API, OpenViking | 1,000,000 |
| **Technical Writer** | `claude-3-5-sonnet` | Drafts comprehensive, actionable bug bounty reports and manages submission logistics. | OpenClaw Notify, OpenViking | 300,000 |

**Operational Workflow:** Recon Specialist → Lead Penetration Tester → Technical Writer

**Scope Gate:** PentAGI enforces rigid, authorized scope boundaries at the API level. Any out-of-scope testing attempts are immediately blocked and logged.

---

## 🔬 Company Delta — Research Arbitrage & IP Generation

Delta is the intellectual engine of SheldonOS. Its mission is to generate long-term value from cutting-edge AI research through strategic patent filing, academic consulting, and proprietary model licensing.

| Agent Designation | Cognitive Model | Primary Role | Key Tool Integrations | Token Budget |
|---|---|---|---|---|
| **Research Director** | `claude-3-opus` | Identifies, evaluates, and prioritizes high-value research opportunities and domains. | AutoRA, Perplexity API, Cognee | 800,000 |
| **Research Scientist** | `MiniMax-01` | Conducts long-context research analysis, literature review, and hypothesis generation. | AutoRA, MiniMax-01, OpenViking | 2,000,000 |
| **IP Strategist** | `claude-3-5-sonnet` | Drafts defensible patent applications and coordinates the filing process. | Perplexity API, OpenClaw Notify | 500,000 |

**Operational Workflow:** Research Director → Research Scientist → IP Strategist

---

## 📡 Company Epsilon — Opportunity Scout & Intelligence Routing

Epsilon functions as the continuous intelligence layer. It runs as a persistent background daemon, monitoring diverse data streams globally and intelligently routing high-quality opportunities to the appropriate specialized company.

| Agent Designation | Cognitive Model | Primary Role | Key Tool Integrations | Token Budget |
|---|---|---|---|---|
| **Market Monitor** | `claude-3-5-haiku` | Performs real-time, high-frequency monitoring of 10+ global data streams. | Perplexity API, Polymarket API, PostgreSQL | 200,000 |
| **Opportunity Scorer** | `claude-3-5-sonnet` | Evaluates raw signals, estimates ROI, and routes opportunities to the correct company. | Cognee, Percepta API, Paperclip API | 400,000 |

**Operational Cycle:** Executes every 30 minutes (configurable via `SEEK_INTERVAL_SECONDS`).

**Intelligent Routing Logic:**

| Opportunity Category | Routed Destination |
|---|---|
| Prediction market signal / Event anomaly | Alpha |
| SaaS product gap / Developer pain point | Beta |
| New bug bounty program / Vulnerability trend | Gamma |
| Research breakthrough / Novel methodology | Delta |
| Crypto/DeFi arbitrage opportunity | Alpha |

---

## 🌐 Cross-Company Infrastructure Agents

These specialized agents operate at the system level, providing critical infrastructure and optimization services across all five companies. They are not bound to a specific company's budget.

| Agent Designation | Primary Role | Availability |
|---|---|---|
| **Memory Archivist** | Autonomously promotes critical L1 (episodic) memories to L2 (long-term) storage at session end. | Universal |
| **Knowledge Synthesizer** | Executes Cognee `cognify` routines after every 10 task completions to update the global knowledge graph. | Universal |
| **Self-Correction Monitor** | Actively watches for agent execution failures and dynamically injects Context Hub fixes. | Universal |
| **Performance Optimizer** | Runs Everything-Claude-Code analysis on slow or inefficient workflows to optimize execution speed. | Universal |

---

## 🗣️ Universal Agent Communication Protocol

To ensure system coherence and prevent redundant processing, all agents strictly adhere to the following communication protocol:

1.  **Pre-Task Initialization:** Query the Cognee knowledge graph for prior attempts, successes, or failures at similar tasks.
2.  **Pre-API Invocation:** Check OpenViking L1 memory for cached results to minimize external API calls and latency.
3.  **Step-by-Step Reporting:** Transmit a heartbeat signal to Paperclip after every task step, detailing token usage, current status, and confidence level.
4.  **Post-Task Synthesis:** Write the final outcome, generated artifacts, and extracted lessons learned back to the Cognee knowledge graph.
5.  **Session Termination:** Promote highly relevant L1 memories to L2 long-term storage via OpenViking for future retrieval.

---

## ➕ Extending the Roster: Adding New Agents

SheldonOS is designed for infinite scalability. To integrate a new agent into the ecosystem:

1.  Define the agent's parameters, role, and tool access in `core/workforce/agency_agents/agent_loader.py` within the `AGENT_ROSTER` list.
2.  Execute `python3 scripts/export_agents.py` to automatically generate the required `SOUL.md` definition file for OpenClaw.
3.  Restart the Paperclip heartbeat server to register the new agent and allocate its token budget.
4.  Update this `AGENTS.md` document to reflect the new taxonomy.
