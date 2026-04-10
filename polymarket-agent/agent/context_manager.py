"""
Context Window Tracker & Agent Handoff System
==============================================
Tracks token usage across the agent conversation loop and triggers an
automatic, lossless handoff to a fresh agent instance when context
utilisation reaches the configured threshold (default 56%).

Design principles (drawn from hermes-agent + MiroFish patterns):
- Token counting is lightweight: 4 chars ≈ 1 token (cl100k heuristic)
- Context is serialised as a structured "handoff packet" before the swap
- The incoming agent receives a compressed summary + full state dict so
  it can resume exactly where the previous agent left off
- Rotating file logs (MiroFish logger pattern) capture every handoff
- Retry/backoff (MiroFish retry pattern) guards the handoff LLM call
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import threading
import random
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Logging (MiroFish-style rotating file + console)
# ──────────────────────────────────────────────────────────────────────────────

def _build_logger(name: str, log_dir: str = "logs") -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fmt_detail = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fmt_simple = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")

    fh = RotatingFileHandler(
        os.path.join(log_dir, "context_manager.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt_detail)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt_simple)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


logger = _build_logger("polymarket.context_manager")


# ──────────────────────────────────────────────────────────────────────────────
# Token estimation (lightweight, no external dependency)
# ──────────────────────────────────────────────────────────────────────────────

_CHARS_PER_TOKEN = 4  # cl100k_base heuristic


def estimate_tokens(text: str) -> int:
    """Rough token count: 4 characters ≈ 1 token (cl100k heuristic)."""
    return max(1, len(text) // _CHARS_PER_TOKEN)


def estimate_messages_tokens(messages: List[Dict[str, str]]) -> int:
    """Estimate total tokens for a list of chat messages."""
    total = 0
    for msg in messages:
        total += estimate_tokens(msg.get("content", ""))
        total += 4  # per-message overhead (role + delimiters)
    total += 2  # priming tokens
    return total


# ──────────────────────────────────────────────────────────────────────────────
# Retry / backoff (MiroFish retry pattern, adapted)
# ──────────────────────────────────────────────────────────────────────────────

def _retry_call(
    func: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    exceptions: Tuple = (Exception,),
    **kwargs,
) -> Any:
    """Call *func* with exponential back-off on failure (MiroFish pattern)."""
    delay = base_delay
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as exc:
            last_exc = exc
            if attempt == max_retries:
                logger.error("API call failed after %d retries: %s", max_retries, exc)
                raise
            jittered = min(delay, max_delay) * (0.5 + random.random())
            logger.warning("Attempt %d failed: %s — retrying in %.1fs", attempt + 1, exc, jittered)
            time.sleep(jittered)
            delay *= backoff_factor
    raise last_exc  # type: ignore[misc]


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ContextStats:
    """Live token-usage snapshot."""
    used_tokens: int = 0
    max_tokens: int = 128_000
    handoff_threshold: float = 0.56  # trigger at 56 %
    handoff_count: int = 0
    last_handoff_at: Optional[str] = None

    @property
    def utilisation(self) -> float:
        return self.used_tokens / max(self.max_tokens, 1)

    @property
    def should_handoff(self) -> bool:
        return self.utilisation >= self.handoff_threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "used_tokens": self.used_tokens,
            "max_tokens": self.max_tokens,
            "utilisation_pct": round(self.utilisation * 100, 2),
            "handoff_threshold_pct": round(self.handoff_threshold * 100, 2),
            "should_handoff": self.should_handoff,
            "handoff_count": self.handoff_count,
            "last_handoff_at": self.last_handoff_at,
        }


@dataclass
class AgentState:
    """
    Serialisable snapshot of everything the agent needs to resume work.
    This is the "handoff packet" passed between agent instances.
    """
    # Identity
    agent_id: str = ""
    generation: int = 0          # increments on each handoff

    # Task context
    task_description: str = ""
    current_phase: str = ""
    phase_progress: Dict[str, Any] = field(default_factory=dict)

    # Portfolio & trading state
    portfolio: Dict[str, Any] = field(default_factory=dict)
    open_positions: List[Dict[str, Any]] = field(default_factory=list)
    pending_signals: List[Dict[str, Any]] = field(default_factory=list)

    # Strategy weights (self-learning)
    strategy_weights: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

    # Memory: recent decisions (compressed, last N)
    decision_log: List[Dict[str, Any]] = field(default_factory=list)
    MAX_DECISION_LOG = 20

    # Conversation summary (compressed by outgoing agent)
    conversation_summary: str = ""

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_decision(self, decision: Dict[str, Any]) -> None:
        self.decision_log.append(decision)
        if len(self.decision_log) > self.MAX_DECISION_LOG:
            self.decision_log = self.decision_log[-self.MAX_DECISION_LOG:]
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentState":
        obj = cls()
        for k, v in d.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj

    def to_handoff_prompt(self) -> str:
        """
        Render a compact, human-readable handoff prompt that the incoming
        agent receives as its first system message.
        """
        lines = [
            "=== AGENT HANDOFF PACKET ===",
            f"Generation : {self.generation}",
            f"Task       : {self.task_description}",
            f"Phase      : {self.current_phase}",
            "",
            "--- Conversation Summary ---",
            self.conversation_summary or "(none)",
            "",
            "--- Portfolio Snapshot ---",
            f"  Bankroll         : {self.portfolio.get('bankroll', 'N/A')}",
            f"  Open Positions   : {len(self.open_positions)}",
            f"  Total P&L        : {self.portfolio.get('total_pnl', 'N/A')}",
            "",
            "--- Strategy Weights ---",
        ]
        for strat, w in self.strategy_weights.items():
            lines.append(f"  {strat:<25} : {w:.3f}")
        lines += [
            "",
            "--- Recent Decisions (last 5) ---",
        ]
        for d in self.decision_log[-5:]:
            lines.append(
                f"  [{d.get('timestamp','?')}] {d.get('action','?')} "
                f"market={d.get('market_id','?')} edge={d.get('edge','?')}"
            )
        lines += [
            "",
            "--- Performance ---",
            f"  Win Rate  : {self.performance_metrics.get('win_rate', 'N/A')}",
            f"  Sharpe    : {self.performance_metrics.get('sharpe_ratio', 'N/A')}",
            f"  Max DD    : {self.performance_metrics.get('max_drawdown', 'N/A')}",
            "=== END HANDOFF PACKET ===",
        ]
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Context Window Tracker
# ──────────────────────────────────────────────────────────────────────────────

class ContextWindowTracker:
    """
    Tracks token usage for a single agent conversation and fires the
    handoff callback when utilisation crosses the threshold.

    Usage
    -----
    tracker = ContextWindowTracker(config, on_handoff_needed=my_callback)
    tracker.add_messages(messages)          # after each LLM turn
    tracker.update_from_response(response)  # after receiving completion
    """

    def __init__(
        self,
        config: Dict[str, Any],
        on_handoff_needed: Optional[Callable[["ContextWindowTracker"], None]] = None,
        log_dir: str = "logs",
    ):
        llm_cfg = config.get("llm", {})
        # Model context limits (tokens)
        _model_limits: Dict[str, int] = {
            "gpt-4.1-mini": 128_000,
            "gpt-4o": 128_000,
            "gpt-4o-mini": 128_000,
            "gpt-4-turbo": 128_000,
            "claude-opus-4": 200_000,
            "claude-3-5-sonnet": 200_000,
            "gemini-2.5-flash": 1_000_000,
            "gemini-2.0-flash": 1_000_000,
        }
        model = llm_cfg.get("model", "gpt-4.1-mini")
        max_ctx = _model_limits.get(model, 128_000)

        self.stats = ContextStats(
            max_tokens=max_ctx,
            handoff_threshold=config.get("agent", {}).get("context_handoff_threshold", 0.56),
        )
        self._messages: List[Dict[str, str]] = []
        self._lock = threading.Lock()
        self._on_handoff_needed = on_handoff_needed
        self._handoff_triggered = False
        self._log_dir = log_dir
        logger.info(
            "ContextWindowTracker initialised — model=%s max_ctx=%d threshold=%.0f%%",
            model, max_ctx, self.stats.handoff_threshold * 100,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_messages(self, messages: List[Dict[str, str]]) -> None:
        """Ingest a batch of messages and update token count."""
        with self._lock:
            self._messages = messages
            self.stats.used_tokens = estimate_messages_tokens(messages)
            self._check_threshold()

    def add_single_message(self, role: str, content: str) -> None:
        """Append one message and update token count."""
        with self._lock:
            self._messages.append({"role": role, "content": content})
            self.stats.used_tokens = estimate_messages_tokens(self._messages)
            self._check_threshold()

    def update_from_response(self, response_text: str, usage: Optional[Dict] = None) -> None:
        """
        Update token count from an LLM completion response.
        Prefers the `usage` dict (exact counts) over the heuristic estimate.
        """
        with self._lock:
            if usage:
                self.stats.used_tokens = usage.get("total_tokens", self.stats.used_tokens)
            else:
                self.stats.used_tokens += estimate_tokens(response_text)
            self._check_threshold()

    def reset(self, keep_system: bool = True) -> None:
        """Reset after a successful handoff."""
        with self._lock:
            if keep_system:
                self._messages = [m for m in self._messages if m.get("role") == "system"]
            else:
                self._messages = []
            self.stats.used_tokens = estimate_messages_tokens(self._messages)
            self._handoff_triggered = False
        logger.info("Context window reset — tokens now %d", self.stats.used_tokens)

    @property
    def utilisation_pct(self) -> float:
        return self.stats.utilisation * 100

    @property
    def messages(self) -> List[Dict[str, str]]:
        return list(self._messages)

    def get_stats(self) -> Dict[str, Any]:
        return self.stats.to_dict()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _check_threshold(self) -> None:
        """Called under lock. Fires handoff callback once per threshold crossing."""
        if self.stats.should_handoff and not self._handoff_triggered:
            self._handoff_triggered = True
            logger.warning(
                "Context threshold reached: %.1f%% used (%d / %d tokens) — initiating handoff",
                self.utilisation_pct, self.stats.used_tokens, self.stats.max_tokens,
            )
            if self._on_handoff_needed:
                # Fire in a separate thread so the LLM call doesn't block the main loop
                threading.Thread(
                    target=self._on_handoff_needed,
                    args=(self,),
                    daemon=True,
                ).start()


# ──────────────────────────────────────────────────────────────────────────────
# Agent Handoff Manager
# ──────────────────────────────────────────────────────────────────────────────

class AgentHandoffManager:
    """
    Orchestrates the handoff between agent instances.

    Workflow
    --------
    1. Outgoing agent calls `prepare_handoff(state, tracker)`.
    2. Manager compresses the conversation history into a summary via LLM
       (MiroFish ReACT-style summarisation prompt).
    3. Manager serialises the full AgentState to a JSON file (audit trail).
    4. Manager returns the handoff packet (prompt + state dict) for the
       incoming agent to bootstrap from.
    5. Incoming agent calls `resume_from_handoff(packet)` to restore state.
    """

    HANDOFF_DIR = "logs/handoffs"

    def __init__(self, config: Dict[str, Any], llm_client: Any = None):
        self.config = config
        self.llm_client = llm_client  # optional — used for summarisation
        os.makedirs(self.HANDOFF_DIR, exist_ok=True)
        self._handoff_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Outgoing agent side
    # ------------------------------------------------------------------

    def prepare_handoff(
        self,
        state: AgentState,
        tracker: ContextWindowTracker,
    ) -> Dict[str, Any]:
        """
        Compress conversation history, update state, persist to disk,
        and return the handoff packet for the incoming agent.
        """
        with self._handoff_lock:
            logger.info("Preparing handoff — generation %d → %d", state.generation, state.generation + 1)

            # 1. Compress conversation history
            summary = self._compress_history(tracker.messages, state)
            state.conversation_summary = summary

            # 2. Increment generation counter
            state.generation += 1
            state.updated_at = datetime.utcnow().isoformat()

            # 3. Update tracker stats
            tracker.stats.handoff_count += 1
            tracker.stats.last_handoff_at = state.updated_at

            # 4. Persist handoff packet to disk (audit trail)
            packet = {
                "handoff_id": f"handoff_{state.agent_id}_gen{state.generation}_{int(time.time())}",
                "timestamp": state.updated_at,
                "generation": state.generation,
                "context_stats": tracker.get_stats(),
                "state": state.to_dict(),
                "handoff_prompt": state.to_handoff_prompt(),
            }
            self._persist_handoff(packet)

            logger.info(
                "Handoff packet prepared — id=%s gen=%d summary_len=%d",
                packet["handoff_id"], state.generation, len(summary),
            )
            return packet

    # ------------------------------------------------------------------
    # Incoming agent side
    # ------------------------------------------------------------------

    def resume_from_handoff(self, packet: Dict[str, Any]) -> Tuple[AgentState, str]:
        """
        Restore AgentState from a handoff packet.
        Returns (restored_state, handoff_prompt_for_system_message).
        """
        state = AgentState.from_dict(packet["state"])
        handoff_prompt = packet.get("handoff_prompt", state.to_handoff_prompt())
        logger.info(
            "Resuming from handoff — id=%s gen=%d",
            packet.get("handoff_id", "?"), state.generation,
        )
        return state, handoff_prompt

    def load_latest_handoff(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load the most recent handoff packet for a given agent_id."""
        pattern = f"handoff_{agent_id}_gen"
        files = sorted(
            [f for f in Path(self.HANDOFF_DIR).glob(f"{pattern}*.json")],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not files:
            return None
        try:
            with open(files[0], "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logger.error("Failed to load handoff file %s: %s", files[0], exc)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compress_history(
        self,
        messages: List[Dict[str, str]],
        state: AgentState,
    ) -> str:
        """
        Compress conversation history into a concise summary.
        Uses LLM if available (MiroFish ReACT pattern), otherwise
        falls back to extracting the last N assistant messages.
        """
        if not messages:
            return "(no conversation history)"

        # Fallback: extract last 5 assistant messages
        assistant_msgs = [m["content"] for m in messages if m.get("role") == "assistant"]
        fallback_summary = "\n---\n".join(assistant_msgs[-5:]) if assistant_msgs else "(none)"

        if self.llm_client is None:
            return fallback_summary

        # Build compression prompt (MiroFish-style)
        history_text = "\n".join(
            f"[{m.get('role','?').upper()}]: {m.get('content','')[:500]}"
            for m in messages[-30:]  # last 30 messages
        )
        system_prompt = (
            "You are a context compression specialist for a Polymarket trading agent. "
            "Summarise the conversation history below into a compact, information-dense "
            "paragraph (max 300 words) that captures: current trading phase, key decisions "
            "made, markets analysed, signals observed, and any unresolved tasks. "
            "Preserve all numerical values and market IDs exactly."
        )
        user_msg = f"Conversation history to compress:\n\n{history_text}"

        try:
            summary = _retry_call(
                self.llm_client.reason,
                system_prompt,
                user_msg,
                max_retries=2,
                base_delay=1.0,
            )
            return summary or fallback_summary
        except Exception as exc:
            logger.warning("LLM compression failed, using fallback: %s", exc)
            return fallback_summary

    def _persist_handoff(self, packet: Dict[str, Any]) -> None:
        """Write handoff packet to disk as JSON."""
        filename = os.path.join(self.HANDOFF_DIR, f"{packet['handoff_id']}.json")
        try:
            with open(filename, "w", encoding="utf-8") as fh:
                json.dump(packet, fh, indent=2, default=str)
            logger.debug("Handoff persisted to %s", filename)
        except Exception as exc:
            logger.error("Failed to persist handoff: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Convenience factory
# ──────────────────────────────────────────────────────────────────────────────

def build_context_system(
    config: Dict[str, Any],
    agent_id: str,
    llm_client: Any = None,
    task_description: str = "Polymarket autonomous trading",
) -> Tuple[ContextWindowTracker, AgentHandoffManager, AgentState]:
    """
    Factory that wires together a ContextWindowTracker, AgentHandoffManager,
    and an initial AgentState.

    The tracker's `on_handoff_needed` callback is pre-wired to the manager
    so handoffs happen automatically when the 56 % threshold is crossed.

    Returns
    -------
    tracker, handoff_manager, initial_state
    """
    handoff_manager = AgentHandoffManager(config, llm_client=llm_client)

    # Check if we are resuming from a previous handoff
    existing_packet = handoff_manager.load_latest_handoff(agent_id)
    if existing_packet:
        state, _ = handoff_manager.resume_from_handoff(existing_packet)
        logger.info("Resumed existing agent state — generation %d", state.generation)
    else:
        state = AgentState(
            agent_id=agent_id,
            task_description=task_description,
            strategy_weights=config.get("strategy", {}).get("ensemble_weights", {}),
        )
        logger.info("Created fresh agent state for agent_id=%s", agent_id)

    def _on_handoff(tracker: ContextWindowTracker) -> None:
        """Callback: compress + persist state, then reset tracker."""
        try:
            packet = handoff_manager.prepare_handoff(state, tracker)
            # Inject handoff prompt as new system message for the incoming agent
            handoff_prompt = packet["handoff_prompt"]
            tracker.reset(keep_system=False)
            tracker.add_single_message("system", handoff_prompt)
            logger.info("Handoff complete — context reset, new system message injected")
        except Exception as exc:
            logger.error("Handoff callback failed: %s", exc)

    tracker = ContextWindowTracker(
        config,
        on_handoff_needed=_on_handoff,
        log_dir=config.get("learning", {}).get("performance_log", "logs/performance.jsonl").rsplit("/", 1)[0],
    )

    return tracker, handoff_manager, state
