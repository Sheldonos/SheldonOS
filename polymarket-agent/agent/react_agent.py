"""
ReACT Agent Loop
================
Implements the core Reason → Act → Observe loop for the Polymarket trading
agent, integrating:
  - MiroFish ReACT pattern (tool-calling with conflict detection, max iterations)
  - MiroFish retry/backoff for all LLM calls
  - Context window tracking with automatic 56 % handoff
  - hermes-agent tool registry pattern
  - Structured JSON-mode responses for trade decisions

The agent operates in two modes:
  1. SCAN   — discover and score markets, generate signals
  2. DECIDE — evaluate signals, size positions, execute (or simulate) trades
"""

from __future__ import annotations

import json
import logging
import re
import time
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .context_manager import (
    AgentState,
    AgentHandoffManager,
    ContextWindowTracker,
    _retry_call,
    build_context_system,
)

logger = logging.getLogger("polymarket.react_agent")


# ──────────────────────────────────────────────────────────────────────────────
# Tool registry (hermes-agent pattern)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., str]


class ToolRegistry:
    """Lightweight tool registry following hermes-agent's tool system."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, params: Dict[str, Any]) -> str:
        tool = self.get(name)
        if tool is None:
            return f"[ERROR] Unknown tool: {name}"
        try:
            return tool.handler(**params)
        except Exception as exc:
            logger.error("Tool %s failed: %s", name, exc)
            return f"[ERROR] Tool {name} raised: {exc}"


# ──────────────────────────────────────────────────────────────────────────────
# ReACT loop
# ──────────────────────────────────────────────────────────────────────────────

class ReACTAgent:
    """
    ReACT (Reason + Act) agent loop with:
    - MiroFish-style iteration cap and conflict detection
    - Context window tracking + automatic handoff at 56 %
    - Structured JSON trade decisions
    - Full audit trail via structured logging
    """

    MAX_ITERATIONS = 8          # max reasoning steps per task
    MAX_TOOL_CALLS = 5          # max tool calls per task (MiroFish pattern)
    CONFLICT_RETRY_LIMIT = 2    # max consecutive tool+final-answer conflicts

    def __init__(
        self,
        config: Dict[str, Any],
        llm_client: Any,
        tool_registry: ToolRegistry,
        agent_id: str = "polymarket_trader",
    ):
        self.config = config
        self.llm = llm_client
        self.tools = tool_registry
        self.agent_id = agent_id

        # Build context management system
        self.tracker, self.handoff_manager, self.state = build_context_system(
            config=config,
            agent_id=agent_id,
            llm_client=llm_client,
            task_description="Polymarket autonomous trading agent",
        )

        # Conversation messages (shared with tracker)
        self._messages: List[Dict[str, str]] = []
        self._tool_calls_made: int = 0
        self._conflict_retries: int = 0

        logger.info("ReACTAgent initialised — agent_id=%s gen=%d", agent_id, self.state.generation)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_task(
        self,
        task: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a single ReACT task (e.g., 'analyse market X and decide trade').
        Returns a structured result dict.
        """
        self._tool_calls_made = 0
        self._conflict_retries = 0

        # Build initial messages
        messages = self._build_initial_messages(system_prompt, task, context)
        self._messages = messages
        self.tracker.add_messages(messages)

        result = self._react_loop(task)

        # Record decision in state
        if result.get("action") not in (None, "SKIP"):
            self.state.add_decision({
                "timestamp": datetime.utcnow().isoformat(),
                "task": task[:80],
                "action": result.get("action"),
                "market_id": result.get("market_id", ""),
                "edge": result.get("edge", 0),
                "confidence": result.get("confidence", 0),
            })

        return result

    def update_state(self, updates: Dict[str, Any]) -> None:
        """Update agent state (portfolio, metrics, weights)."""
        for key, val in updates.items():
            if hasattr(self.state, key):
                setattr(self.state, key, val)
        self.state.updated_at = datetime.utcnow().isoformat()

    def get_context_stats(self) -> Dict[str, Any]:
        return self.tracker.get_stats()

    # ------------------------------------------------------------------
    # ReACT loop (MiroFish-inspired)
    # ------------------------------------------------------------------

    def _react_loop(self, task: str) -> Dict[str, Any]:
        """
        Core ReACT iteration loop.
        Each iteration: call LLM → parse response → execute tool OR extract answer.
        Mirrors MiroFish's _generate_section_react pattern.
        """
        for iteration in range(self.MAX_ITERATIONS):
            logger.debug("ReACT iteration %d/%d — tokens=%.1f%%",
                         iteration + 1, self.MAX_ITERATIONS, self.tracker.utilisation_pct)

            # ── LLM call with retry (MiroFish retry pattern) ──
            try:
                response = _retry_call(
                    self._call_llm,
                    self._messages,
                    max_retries=3,
                    base_delay=1.0,
                    backoff_factor=2.0,
                )
            except Exception as exc:
                logger.error("LLM call failed after retries: %s", exc)
                return {"action": "SKIP", "reasoning": f"LLM error: {exc}"}

            if response is None:
                logger.warning("LLM returned None on iteration %d", iteration + 1)
                if iteration < self.MAX_ITERATIONS - 1:
                    self._messages.append({"role": "assistant", "content": "(empty response)"})
                    self._messages.append({"role": "user", "content": "Please continue your analysis."})
                    continue
                break

            # Update context tracker
            self.tracker.add_single_message("assistant", response)

            # Parse tool calls and final answer
            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)
            has_final = "Final Answer:" in response or "```json" in response

            # ── Conflict detection (MiroFish pattern) ──
            if has_tool_calls and has_final:
                self._conflict_retries += 1
                logger.warning("Tool+FinalAnswer conflict on iteration %d (count=%d)",
                               iteration + 1, self._conflict_retries)
                if self._conflict_retries <= self.CONFLICT_RETRY_LIMIT:
                    self._messages.append({"role": "assistant", "content": response})
                    self._messages.append({
                        "role": "user",
                        "content": (
                            "[FORMAT ERROR] Do not mix tool calls and Final Answer in one reply. "
                            "Either call a tool OR provide your Final Answer — not both."
                        ),
                    })
                    self.tracker.add_messages(self._messages)
                    continue
                # Too many conflicts — force final answer extraction
                has_tool_calls = False

            # ── Execute tool calls ──
            if has_tool_calls and self._tool_calls_made < self.MAX_TOOL_CALLS:
                for call in tool_calls[:1]:  # one tool per iteration (MiroFish)
                    if self._tool_calls_made >= self.MAX_TOOL_CALLS:
                        break
                    tool_result = self.tools.execute(call["name"], call.get("parameters", {}))
                    self._tool_calls_made += 1
                    logger.debug("Tool %s called (total=%d)", call["name"], self._tool_calls_made)

                    self._messages.append({"role": "assistant", "content": response})
                    self._messages.append({
                        "role": "user",
                        "content": f"[TOOL RESULT: {call['name']}]\n{tool_result[:2000]}",
                    })
                    self.tracker.add_messages(self._messages)
                continue

            # ── Extract final answer ──
            if has_final or not has_tool_calls:
                return self._extract_final_answer(response)

            # ── Force conclusion if tool budget exhausted ──
            if self._tool_calls_made >= self.MAX_TOOL_CALLS:
                self._messages.append({"role": "assistant", "content": response})
                self._messages.append({
                    "role": "user",
                    "content": "Tool call budget exhausted. Provide your Final Answer now.",
                })
                self.tracker.add_messages(self._messages)

        # Fallback if loop exhausted
        logger.warning("ReACT loop exhausted without final answer for task: %s", task[:60])
        return {"action": "SKIP", "reasoning": "ReACT loop exhausted"}

    # ------------------------------------------------------------------
    # Message construction
    # ------------------------------------------------------------------

    def _build_initial_messages(
        self,
        system_prompt: str,
        task: str,
        context: Optional[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Build the initial message list, prepending handoff context if available."""
        messages = []

        # System prompt
        full_system = system_prompt
        if self.state.conversation_summary:
            full_system = (
                f"{system_prompt}\n\n"
                f"=== RESUMED FROM HANDOFF (generation {self.state.generation}) ===\n"
                f"{self.state.to_handoff_prompt()}\n"
                "=== END HANDOFF CONTEXT ==="
            )
        messages.append({"role": "system", "content": full_system})

        # Tool descriptions
        tools_desc = json.dumps(self.tools.list_tools(), indent=2)
        messages.append({
            "role": "user",
            "content": (
                f"Available tools:\n```json\n{tools_desc}\n```\n\n"
                "Use tools by outputting:\n"
                "<tool_call>\n{\"name\": \"tool_name\", \"parameters\": {...}}\n</tool_call>\n\n"
                "When done, output:\nFinal Answer:\n```json\n{...}\n```"
            ),
        })

        # Task + context
        if context:
            ctx_str = json.dumps(context, indent=2, default=str)
            messages.append({
                "role": "user",
                "content": f"Context:\n```json\n{ctx_str}\n```\n\nTask: {task}",
            })
        else:
            messages.append({"role": "user", "content": f"Task: {task}"})

        return messages

    # ------------------------------------------------------------------
    # Parsing helpers (MiroFish pattern)
    # ------------------------------------------------------------------

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        calls = []
        # Pattern 1: <tool_call>{...}</tool_call>
        for match in re.finditer(r"<tool_call>(.*?)</tool_call>", response, re.DOTALL):
            try:
                calls.append(json.loads(match.group(1).strip()))
            except json.JSONDecodeError:
                pass
        # Pattern 2: [TOOL_CALL] name(params)
        for match in re.finditer(r"\[TOOL_CALL\]\s+(\w+)\(([^)]*)\)", response):
            try:
                params = json.loads(match.group(2)) if match.group(2).strip() else {}
                calls.append({"name": match.group(1), "parameters": params})
            except json.JSONDecodeError:
                calls.append({"name": match.group(1), "parameters": {}})
        return calls

    def _extract_final_answer(self, response: str) -> Dict[str, Any]:
        """Extract structured JSON from Final Answer block."""
        # Try ```json block
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try Final Answer: {...}
        fa_match = re.search(r"Final Answer:\s*(\{.*\})", response, re.DOTALL)
        if fa_match:
            try:
                return json.loads(fa_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try any JSON object in response
        obj_match = re.search(r"\{[^{}]*\"action\"[^{}]*\}", response, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback: return raw response wrapped
        return {"action": "SKIP", "reasoning": response[:500], "raw": True}

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------

    def _call_llm(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call the LLM with the current message list."""
        llm_cfg = self.config.get("llm", {})
        try:
            client = self.llm._get_client()
            resp = client.chat.completions.create(
                model=self.llm.model,
                messages=messages,
                max_tokens=llm_cfg.get("max_tokens", 4096),
                temperature=llm_cfg.get("temperature", 0.1),
            )
            content = resp.choices[0].message.content or ""
            # Strip <think> tags (MiroFish pattern for chain-of-thought models)
            content = re.sub(r"<think>[\s\S]*?</think>", "", content).strip()
            return content
        except Exception as exc:
            raise exc
