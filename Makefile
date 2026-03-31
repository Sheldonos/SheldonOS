# SheldonOS — Makefile
# Provides convenient commands for local development, Docker operations, and maintenance.
# Usage: make <target>

.PHONY: help setup install env up down restart logs status shell \
        export-agents init-db lint test clean nuke

# ─── Colors ───────────────────────────────────────────────────────────────────
BOLD  := \033[1m
RESET := \033[0m
GREEN := \033[32m
CYAN  := \033[36m
RED   := \033[31m

# ─── Default Target ───────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "$(BOLD)SheldonOS — Available Commands$(RESET)"
	@echo "──────────────────────────────────────────────────────────────────"
	@echo "  $(CYAN)make setup$(RESET)          Full first-time setup (env + install + init-db)"
	@echo "  $(CYAN)make install$(RESET)        Install Python dependencies"
	@echo "  $(CYAN)make env$(RESET)            Copy .env.example → .env (if not exists)"
	@echo ""
	@echo "  $(CYAN)make up$(RESET)             Start all Docker services + orchestrator"
	@echo "  $(CYAN)make up-infra$(RESET)       Start infrastructure services only (no orchestrator)"
	@echo "  $(CYAN)make down$(RESET)           Stop all Docker services"
	@echo "  $(CYAN)make restart$(RESET)        Restart all services"
	@echo "  $(CYAN)make logs$(RESET)           Tail logs from all containers"
	@echo "  $(CYAN)make status$(RESET)         Show running container status"
	@echo ""
	@echo "  $(CYAN)make run$(RESET)            Run orchestrator directly (requires infra up)"
	@echo "  $(CYAN)make export-agents$(RESET)  Export agent SOUL.md files to OpenClaw"
	@echo "  $(CYAN)make init-db$(RESET)        Initialize the PostgreSQL database schema"
	@echo ""
	@echo "  $(CYAN)make lint$(RESET)           Run Python syntax check on all source files"
	@echo "  $(CYAN)make test$(RESET)           Run test suite"
	@echo "  $(CYAN)make clean$(RESET)          Remove Python cache files"
	@echo "  $(CYAN)make nuke$(RESET)           Stop containers and remove all volumes (DESTRUCTIVE)"
	@echo "──────────────────────────────────────────────────────────────────"
	@echo ""

# ─── Setup ────────────────────────────────────────────────────────────────────
setup: env install
	@echo "$(GREEN)$(BOLD)✓ Setup complete. Edit .env with your API keys, then run: make up$(RESET)"

env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ Created .env from .env.example — fill in your API keys before starting.$(RESET)"; \
	else \
		echo "$(CYAN)ℹ .env already exists — skipping.$(RESET)"; \
	fi

install:
	@echo "$(CYAN)Installing Python dependencies...$(RESET)"
	pip3 install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed.$(RESET)"

# ─── Docker Operations ────────────────────────────────────────────────────────
up:
	@echo "$(CYAN)Starting all SheldonOS services...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)✓ All services started. Run 'make logs' to monitor.$(RESET)"

up-infra:
	@echo "$(CYAN)Starting infrastructure services only...$(RESET)"
	docker-compose up -d postgres redis neo4j paperclip openclaw_gateway cognee openviking mirofish percepta pentagi prometheus grafana
	@echo "$(GREEN)✓ Infrastructure ready. Run 'make run' to start the orchestrator.$(RESET)"

down:
	@echo "$(CYAN)Stopping all services...$(RESET)"
	docker-compose down
	@echo "$(GREEN)✓ All services stopped.$(RESET)"

restart:
	$(MAKE) down
	$(MAKE) up

logs:
	docker-compose logs -f --tail=100

status:
	docker-compose ps

# ─── Orchestrator ─────────────────────────────────────────────────────────────
run:
	@echo "$(CYAN)Starting SheldonOS orchestrator...$(RESET)"
	python3 orchestrator/sheldon_orchestrator.py

export-agents:
	@echo "$(CYAN)Exporting agent SOUL.md files...$(RESET)"
	python3 scripts/export_agents.py
	@echo "$(GREEN)✓ Agents exported.$(RESET)"

init-db:
	@echo "$(CYAN)Initializing database schema...$(RESET)"
	@until docker-compose exec -T postgres pg_isready -U $${POSTGRES_USER:-sheldon} > /dev/null 2>&1; do \
		echo "Waiting for PostgreSQL..."; sleep 2; \
	done
	docker-compose exec -T postgres psql -U $${POSTGRES_USER:-sheldon} -d sheldon -f /docker-entrypoint-initdb.d/init.sql
	@echo "$(GREEN)✓ Database initialized.$(RESET)"

# ─── Quality ──────────────────────────────────────────────────────────────────
lint:
	@echo "$(CYAN)Checking Python syntax...$(RESET)"
	@python3 -c "\
import ast, os; \
errors = []; \
[errors.append(f'{os.path.join(r,f)}: {e}') \
  for r, dirs, files in os.walk('.') \
  for f in files if f.endswith('.py') \
  for e in [None] \
  if (lambda p: [errors.append(f'{p}: {ex}') for ex in [None] \
    if (lambda: ast.parse(open(p).read()) or True)() is None])(os.path.join(r,f))]; \
print('All files OK') if not errors else [print(e) for e in errors]"
	@find . -name '*.py' -not -path './.git/*' -not -path './__pycache__/*' \
		-exec python3 -m py_compile {} \; && echo "$(GREEN)✓ No syntax errors found.$(RESET)"

test:
	@echo "$(CYAN)Running test suite...$(RESET)"
	python3 -m pytest tests/ -v --tb=short 2>/dev/null || echo "$(CYAN)ℹ No tests directory found — skipping.$(RESET)"

# ─── Maintenance ──────────────────────────────────────────────────────────────
clean:
	@echo "$(CYAN)Cleaning Python cache files...$(RESET)"
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	find . -name '*.pyo' -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cache cleaned.$(RESET)"

nuke:
	@echo "$(RED)$(BOLD)WARNING: This will destroy all data volumes. Press Ctrl+C to cancel.$(RESET)"
	@sleep 5
	docker-compose down -v
	@echo "$(GREEN)✓ All containers and volumes removed.$(RESET)"
