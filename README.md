# Autonomous Agent Orchestration Framework

**An advanced, open-source framework for building, deploying, and orchestrating autonomous economic agents.** This repository provides a robust, scalable, and extensible architecture for creating AI-powered systems that can independently execute complex workflows, from quantitative trading and security research to automated content creation and micro-SaaS development.

---

## Core Philosophy

This framework is built on three core principles:

1.  **Autonomy by Default:** Agents are designed to operate independently within a well-defined scope, executing a full **Seek → Adapt → Scale → Optimize** loop with minimal human intervention.
2.  **Local-First & Extensible:** The entire system can run locally on your hardware. It is designed for deep extensibility, allowing developers to add new agents, skills, and data sources with ease.
3.  **Provider-Agnostic AI:** The LLM abstraction layer allows you to use any major AI provider (Anthropic, OpenAI, Gemini) or any OpenAI-compatible endpoint, ensuring you are never locked into a single vendor.

---

## Key Features

- **Hierarchical Agent Architecture:** A multi-layered system of agents, sub-agents, and specialized teams for complex task decomposition.
- **Dynamic Workflow Orchestration:** Decompose high-level goals into multi-step execution graphs (DAGs) managed by a workflow engine.
- **Persistent Memory & Knowledge:** Integrates a tiered memory system and a knowledge graph to ensure agents learn from past experiences and avoid redundant work.
- **Advanced Simulation Engine:** Model complex social and economic dynamics to predict outcomes and identify high-EV opportunities before execution.
- **Robust Security Model:** Enforces hardware-level sandboxing, strict scoping, and financial risk controls for safe autonomous operation.
- **Full Observability:** Comes with pre-configured Prometheus and Grafana dashboards for monitoring system health, agent performance, and economic output.

---

## System Architecture

The framework is structured into five highly specialized layers, each leveraging best-in-class open-source projects to create a resilient and powerful ecosystem.

| Layer | Name | Primary Purpose |
|---|---|---|
| **0** | **Control Plane** | Governance, inter-agent routing, hardware-level sandboxing, and financial execution. |
| **1** | **Workforce** | Dynamic agent team assembly, workflow DAG orchestration, and parallel sub-agent spawning. |
| **2** | **Cognitive Backbone** | Infinite tiered memory, dynamic knowledge graph construction, and autonomous self-correction. |
| **3** | **Simulation Engine** | High-fidelity social simulation and rigorous economic probability modeling. |
| **4** | **Research & Exploit** | Deep web intelligence gathering, authorized security research, and long-context reasoning. |

---

## 🚀 Getting Started

This project uses Docker Compose to orchestrate all services. A `Makefile` is provided for convenience.

### Prerequisites

*   Docker and Docker Compose
*   Python 3.11+
*   64 GB RAM minimum (512 GB recommended for full, unconstrained deployment)
*   NVIDIA GPU with 24+ GB VRAM (for local model inference and simulation)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Run the setup command:**
    This will copy the environment file and install Python dependencies.
    ```bash
    make setup
    ```

3.  **Configure your environment:**
    Edit the newly created `.env` file with your API keys and desired configuration.
    ```bash
    nano .env
    ```

4.  **Start all services:**
    This will build and start all the required Docker containers in the background.
    ```bash
    make up
    ```

5.  **Monitor the logs:**
    ```bash
    make logs
    ```

---

## Usage with `make`

A `Makefile` provides commands for common operations:

| Command | Description |
|---|---|
| `make setup` | Runs the complete first-time setup (`env`, `install`). |
| `make up` | Starts all Docker services in detached mode. |
| `make down` | Stops and removes all Docker containers. |
| `make restart` | Restarts all services. |
| `make logs` | Tails the logs from all running containers. |
| `make status` | Shows the status of all running containers. |
| `make run` | Runs the main orchestrator script directly on the host (requires `make up-infra`). |
| `make export-agents` | Exports agent definitions for the control plane. |
| `make lint` | Checks all Python files for syntax errors. |
| `make nuke` | **DESTRUCTIVE.** Stops all containers and removes all associated data volumes. |

---

## 📁 Project Structure

```text
.
├── orchestrator/         # Master Seek→Adapt→Scale loop
├── core/                 # Core logic for all layers (control, workforce, cognitive, etc.)
├── config/               # Service configurations (Prometheus, Grafana, systemd)
├── docker/               # Dockerfiles for building local service images
├── scripts/              # Helper scripts (DB initialization, agent exports)
├── skills/               # Extensible skills that can be loaded by agents
├── docker-compose.yml    # Defines all services and their orchestration
├── requirements.txt      # Python dependencies
├── .env.example          # Template for environment variables
├── Makefile              # Convenience commands for development and operations
└── README.md             # This file
```

---

## 🤝 Contributing

This framework is designed for infinite extensibility. To add a new agent, skill, or workflow:

1.  Define new agents in `core/workforce/agency_agents/agent_loader.py`.
2.  Create new workflow templates in `core/workforce/deer_flow/workflow_orchestrator.py`.
3.  Add new skills in the `skills/` directory, following the existing structure.
4.  Update `docker-compose.yml` if new supporting services are required.

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

*Disclaimer: This is an advanced research and development framework. All financial trading, security research, and autonomous operations must strictly comply with applicable laws and regulations in your jurisdiction. The creators assume no liability for autonomous actions taken by the system.*
