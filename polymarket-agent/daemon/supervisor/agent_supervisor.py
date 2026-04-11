"""
Hierarchical Agent Supervisor
==============================
Manages a fleet of specialized sub-agents, each targeting a specific market
category. Implements the hierarchical architecture pattern with:

  Master Supervisor
    ├── CryptoSniperAgent     (BTC/ETH price markets)
    ├── SoccerSniperAgent     (UEFA, La Liga, EPL)
    ├── SportsSniperAgent     (NBA, NFL, MLB, Tennis)
    ├── GeopoliticalAgent     (Politics, World events)
    └── TechSniperAgent       (Tech, Science, Niche)

Each sub-agent:
  - Has its own market scanner with category-specific filters
  - Has its own opportunity queue
  - Shares the global bankroll (with allocation limits per agent)
  - Reports performance back to the supervisor
  - Is automatically restarted if it crashes

The supervisor also manages context window tracking and agent handoffs,
ensuring no agent exceeds 56% of its context window before handing off
its state to a fresh instance.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("daemon.supervisor")


# ---------------------------------------------------------------------------
# Sub-agent definition
# ---------------------------------------------------------------------------

@dataclass
class SubAgentSpec:
    """Configuration for a specialized sub-agent."""
    name: str
    categories: List[str]
    bankroll_allocation: float   # fraction of total bankroll (0-1)
    min_sniper_score: float = 60.0
    scan_interval_seconds: int = 60
    max_concurrent_positions: int = 3
    enabled: bool = True
    description: str = ""


# Default fleet configuration
DEFAULT_AGENT_FLEET: List[SubAgentSpec] = [
    SubAgentSpec(
        name="CryptoSniper",
        categories=["crypto", "bitcoin", "ethereum", "defi"],
        bankroll_allocation=0.25,
        min_sniper_score=65.0,
        scan_interval_seconds=30,   # faster scan for crypto
        max_concurrent_positions=2,
        description="BTC/ETH price markets and crypto events",
    ),
    SubAgentSpec(
        name="SoccerSniper",
        categories=["soccer", "football", "uefa", "champions-league", "premier-league"],
        bankroll_allocation=0.30,
        min_sniper_score=62.0,
        scan_interval_seconds=60,
        max_concurrent_positions=3,
        description="European soccer — reachingthesky & KeyTransporter archetype",
    ),
    SubAgentSpec(
        name="SportsSniper",
        categories=["sports", "nba", "nfl", "mlb", "tennis", "esports"],
        bankroll_allocation=0.20,
        min_sniper_score=65.0,
        scan_interval_seconds=90,
        max_concurrent_positions=2,
        description="North American sports and esports",
    ),
    SubAgentSpec(
        name="GeopoliticalSniper",
        categories=["politics", "world", "geopolitics", "elections"],
        bankroll_allocation=0.15,
        min_sniper_score=70.0,   # higher bar for geopolitical
        scan_interval_seconds=120,
        max_concurrent_positions=1,
        description="Geopolitical events — insider pattern detection",
    ),
    SubAgentSpec(
        name="TechSniper",
        categories=["tech", "science", "ai", "business"],
        bankroll_allocation=0.10,
        min_sniper_score=68.0,
        scan_interval_seconds=120,
        max_concurrent_positions=1,
        description="Tech and niche markets — 0xafEe archetype",
    ),
]


# ---------------------------------------------------------------------------
# Sub-agent runtime state
# ---------------------------------------------------------------------------

@dataclass
class SubAgentState:
    spec: SubAgentSpec
    status: str = "stopped"          # stopped | starting | running | crashed | handoff
    scanner_thread: Optional[threading.Thread] = None
    executor_thread: Optional[threading.Thread] = None
    opportunity_queue: queue.Queue = field(default_factory=lambda: queue.Queue(maxsize=50))
    start_time: Optional[str] = None
    restart_count: int = 0
    last_error: Optional[str] = None
    context_tokens_used: int = 0
    context_max_tokens: int = 128_000
    handoff_threshold: float = 0.56   # 56% context window triggers handoff
    positions_opened: int = 0
    positions_won: int = 0
    positions_lost: int = 0
    total_pnl: float = 0.0

    @property
    def context_pct(self) -> float:
        return self.context_tokens_used / self.context_max_tokens

    @property
    def needs_handoff(self) -> bool:
        return self.context_pct >= self.handoff_threshold

    @property
    def win_rate(self) -> float:
        total = self.positions_won + self.positions_lost
        return self.positions_won / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.spec.name,
            "categories": self.spec.categories,
            "status": self.status,
            "bankroll_allocation": self.spec.bankroll_allocation,
            "restart_count": self.restart_count,
            "context_pct": round(self.context_pct * 100, 1),
            "needs_handoff": self.needs_handoff,
            "positions_opened": self.positions_opened,
            "win_rate": round(self.win_rate, 3),
            "total_pnl": round(self.total_pnl, 2),
            "start_time": self.start_time,
            "last_error": self.last_error,
        }


# ---------------------------------------------------------------------------
# Supervisor
# ---------------------------------------------------------------------------

class AgentSupervisor:
    """
    Master supervisor that manages the fleet of specialized sub-agents.
    Implements health monitoring, automatic restart, and context handoffs.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        data_client,
        kronos_adapter,
        notifier,
        learning_engine,
        bankroll_getter: Callable[[], float],
        bankroll_setter: Callable[[float], None],
        agent_fleet: Optional[List[SubAgentSpec]] = None,
    ):
        self.cfg = config
        self.data_client = data_client
        self.kronos = kronos_adapter
        self.notifier = notifier
        self.learning = learning_engine
        self.bankroll_getter = bankroll_getter
        self.bankroll_setter = bankroll_setter

        # Build fleet from config or defaults
        fleet_cfg = config.get("daemon", {}).get("agent_fleet", [])
        if fleet_cfg:
            self.fleet = [SubAgentSpec(**spec) for spec in fleet_cfg]
        else:
            self.fleet = agent_fleet or DEFAULT_AGENT_FLEET

        # Filter to enabled agents only
        self.fleet = [a for a in self.fleet if a.enabled]

        # Runtime state per agent
        self._agents: Dict[str, SubAgentState] = {
            spec.name: SubAgentState(spec=spec)
            for spec in self.fleet
        }

        # Supervisor control
        self._stop_event = threading.Event()
        self._supervisor_thread: Optional[threading.Thread] = None
        self._health_check_interval = config.get("daemon", {}).get(
            "supervisor", {}).get("health_check_interval_seconds", 30)
        self._max_restarts = config.get("daemon", {}).get(
            "supervisor", {}).get("max_restarts_per_agent", 10)

        # Shared opportunity queue (all agents feed into this)
        self.global_opportunity_queue: queue.Queue = queue.Queue(maxsize=200)

        logger.info(
            "AgentSupervisor initialized with %d agents: %s",
            len(self.fleet),
            [a.name for a in self.fleet],
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Start all sub-agents and the supervisor health monitor."""
        logger.info("Starting agent fleet...")
        for spec in self.fleet:
            self._start_agent(spec.name)
            time.sleep(2)  # stagger starts to avoid API rate limits

        self._stop_event.clear()
        self._supervisor_thread = threading.Thread(
            target=self._supervisor_loop,
            name="AgentSupervisor",
            daemon=True,
        )
        self._supervisor_thread.start()
        logger.info("AgentSupervisor started. Fleet active.")

        self.notifier.send(
            title="🚀 Polymarket Sniper Daemon Started",
            body=(
                f"Fleet: {len(self.fleet)} agents active\n"
                f"Bankroll: ${self.bankroll_getter():,.2f}\n"
                f"Mode: {self.cfg.get('daemon', {}).get('execution', {}).get('mode', 'dry_run').upper()}"
            ),
            level="success",
        )

    def stop(self):
        """Stop all sub-agents and the supervisor."""
        logger.info("Stopping agent fleet...")
        self._stop_event.set()

        for name, state in self._agents.items():
            self._stop_agent(name)

        if self._supervisor_thread:
            self._supervisor_thread.join(timeout=30)

        logger.info("AgentSupervisor stopped.")
        self.notifier.send(
            title="⛔ Polymarket Sniper Daemon Stopped",
            body=f"Final bankroll: ${self.bankroll_getter():,.2f}",
            level="warning",
        )

    # ------------------------------------------------------------------
    # Agent lifecycle management
    # ------------------------------------------------------------------

    def _start_agent(self, name: str):
        """Start a single sub-agent."""
        state = self._agents.get(name)
        if not state:
            logger.error("Unknown agent: %s", name)
            return

        if state.status == "running":
            logger.debug("Agent %s already running", name)
            return

        logger.info("Starting agent: %s (categories: %s)",
                    name, state.spec.categories)

        # Build agent-specific config overlay
        agent_cfg = self._build_agent_config(state.spec)

        # Import here to avoid circular imports
        from daemon.core.market_scanner import MarketScanner
        from daemon.execution.executor import ExecutionEngine

        # Each agent gets its own bankroll slice
        def agent_bankroll_getter():
            total = self.bankroll_getter()
            return total * state.spec.bankroll_allocation

        def agent_bankroll_setter(new_val: float):
            # Scale back to total bankroll
            total = self.bankroll_getter()
            allocated = total * state.spec.bankroll_allocation
            delta = new_val - allocated
            self.bankroll_setter(total + delta)

        # Create scanner and executor for this agent
        scanner = MarketScanner(
            config=agent_cfg,
            data_client=self.data_client,
            kronos_adapter=self.kronos,
            opportunity_queue=state.opportunity_queue,
            bankroll_getter=agent_bankroll_getter,
        )

        executor = ExecutionEngine(
            config=agent_cfg,
            opportunity_queue=state.opportunity_queue,
            notifier=self.notifier,
            learning_engine=self.learning,
            bankroll_getter=agent_bankroll_getter,
            bankroll_setter=agent_bankroll_setter,
            data_client=self.data_client,
        )

        scanner.start()
        executor.start()

        # Store references for health monitoring
        state.scanner_thread = scanner._thread
        state.executor_thread = executor._thread
        state.status = "running"
        state.start_time = datetime.now(timezone.utc).isoformat()

        # Store scanner/executor on state for later access
        state._scanner = scanner
        state._executor = executor

        logger.info("Agent %s started successfully", name)

    def _stop_agent(self, name: str):
        """Stop a single sub-agent."""
        state = self._agents.get(name)
        if not state or state.status != "running":
            return

        try:
            if hasattr(state, "_scanner"):
                state._scanner.stop()
            if hasattr(state, "_executor"):
                state._executor.stop()
        except Exception as exc:
            logger.warning("Error stopping agent %s: %s", name, exc)

        state.status = "stopped"
        logger.info("Agent %s stopped", name)

    def _restart_agent(self, name: str):
        """Stop and restart a crashed agent."""
        state = self._agents.get(name)
        if not state:
            return

        if state.restart_count >= self._max_restarts:
            logger.error("Agent %s exceeded max restarts (%d). Disabling.",
                         name, self._max_restarts)
            state.status = "disabled"
            self.notifier.send(
                title=f"⛔ Agent {name} Disabled",
                body=f"Exceeded {self._max_restarts} restarts. Manual intervention required.",
                level="critical",
            )
            return

        logger.warning("Restarting agent %s (attempt %d)", name, state.restart_count + 1)
        self._stop_agent(name)
        time.sleep(5)
        state.restart_count += 1
        self._start_agent(name)

    def _perform_context_handoff(self, name: str):
        """
        Perform a context handoff for an agent that has hit 56% context usage.
        Saves the agent's state, stops it, and starts a fresh instance with
        the compressed state injected.
        """
        state = self._agents.get(name)
        if not state:
            return

        logger.info(
            "Context handoff triggered for %s (%.1f%% of context window used)",
            name, state.context_pct * 100,
        )

        # Capture current state summary
        handoff_summary = {
            "agent": name,
            "handoff_time": datetime.now(timezone.utc).isoformat(),
            "context_pct_at_handoff": state.context_pct,
            "positions_opened": state.positions_opened,
            "win_rate": state.win_rate,
            "total_pnl": state.total_pnl,
            "open_positions": state._executor.get_open_positions()
            if hasattr(state, "_executor") else [],
        }

        self.notifier.send(
            title=f"🔄 Context Handoff: {name}",
            body=(
                f"Context at {state.context_pct:.1%}. Handing off to fresh instance.\n"
                f"Preserving {len(handoff_summary['open_positions'])} open positions."
            ),
            level="info",
        )

        # Stop current instance
        state.status = "handoff"
        self._stop_agent(name)

        # Reset context counter
        state.context_tokens_used = 0

        # Restart with handoff summary injected
        time.sleep(3)
        self._start_agent(name)

        logger.info("Context handoff complete for %s", name)

    # ------------------------------------------------------------------
    # Supervisor health monitor loop
    # ------------------------------------------------------------------

    def _supervisor_loop(self):
        """Continuously monitor agent health and trigger restarts/handoffs."""
        logger.info("Supervisor health monitor started")
        while not self._stop_event.is_set():
            try:
                self._health_check()
            except Exception as exc:
                logger.error("Supervisor health check error: %s", exc, exc_info=True)
            time.sleep(self._health_check_interval)
        logger.info("Supervisor health monitor stopped")

    def _health_check(self):
        """Check health of all agents and take corrective action."""
        for name, state in self._agents.items():
            if state.status == "disabled":
                continue

            # Check if threads are alive
            scanner_alive = (state.scanner_thread is not None and
                             state.scanner_thread.is_alive())
            executor_alive = (state.executor_thread is not None and
                              state.executor_thread.is_alive())

            if state.status == "running" and (not scanner_alive or not executor_alive):
                logger.warning("Agent %s threads died unexpectedly. Restarting.", name)
                state.status = "crashed"
                state.last_error = "Thread died unexpectedly"
                self._restart_agent(name)
                continue

            # Check context window usage
            if state.status == "running" and state.needs_handoff:
                self._perform_context_handoff(name)

    # ------------------------------------------------------------------
    # Config builder
    # ------------------------------------------------------------------

    def _build_agent_config(self, spec: SubAgentSpec) -> Dict[str, Any]:
        """Build an agent-specific config overlay from the global config."""
        import copy
        cfg = copy.deepcopy(self.cfg)

        # Override scanner settings
        cfg.setdefault("daemon", {}).setdefault("scanner", {}).update({
            "scan_interval_seconds": spec.scan_interval_seconds,
            "categories": spec.categories,
        })

        # Override execution settings
        cfg["daemon"].setdefault("execution", {}).update({
            "max_concurrent_positions": spec.max_concurrent_positions,
            "min_sniper_score": spec.min_sniper_score,
        })

        # Override sniper settings
        cfg.setdefault("sniper", {}).update({
            "min_sniper_score": spec.min_sniper_score,
        })

        return cfg

    # ------------------------------------------------------------------
    # Public state access
    # ------------------------------------------------------------------

    def get_fleet_status(self) -> List[Dict[str, Any]]:
        return [state.to_dict() for state in self._agents.values()]

    def get_agent_stats(self, name: str) -> Optional[Dict[str, Any]]:
        state = self._agents.get(name)
        if not state:
            return None
        stats = state.to_dict()
        if hasattr(state, "_executor"):
            stats["execution"] = state._executor.get_stats()
        if hasattr(state, "_scanner"):
            stats["scanner"] = state._scanner.get_stats()
        return stats

    def update_context_tokens(self, agent_name: str, tokens_used: int):
        """Called by agent's LLM client to update context token count."""
        state = self._agents.get(agent_name)
        if state:
            state.context_tokens_used = tokens_used
