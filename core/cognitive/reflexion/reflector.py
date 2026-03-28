"""
SheldonOS — Reflexion Layer v3.0
Implements the Reflexion framework for verbal reinforcement learning on agent failures.

When an agent fails a task, the ReflectorAgent:
  1. Retrieves the prior attempt context from Cognee
  2. Calls an LLM to generate a verbal critique ("LESSON: ...")
  3. Stores the lesson in the agent's L1 episodic memory via OpenViking
  4. Future invocations of that agent automatically receive the lesson as context

This creates a genuine closed-loop learning system: agents that fail at a task
will receive their own past lessons on the next attempt, progressively improving
their success rate without any human intervention.

Reference:
  Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning,"
  arXiv:2303.11366, 2023.
  Blueprint §3.4 — Level 4, Closed-Loop Self-Improvement.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger("sheldon.cognitive.reflexion")

# ─── Configuration ────────────────────────────────────────────────────────────
REFLEXION_ENABLED: bool = os.getenv("REFLEXION_ENABLED", "true").lower() == "true"
REFLEXION_TRIGGER_THRESHOLD: int = int(os.getenv("REFLEXION_TRIGGER_THRESHOLD", "2"))


class ReflectorAgent:
    """
    Implements the Reflexion framework for verbal reinforcement learning.

    Analyzes task failures and generates actionable lessons for future attempts.
    Lessons are stored in the agent's L1 episodic memory so they are
    automatically injected into future dispatches.

    Usage:
        reflector = ReflectorAgent()
        lesson = await reflector.reflect(
            failed_task=task,
            agent_id="beta_lead_engineer",
            memory_client=memory_client,
            cognee_client=cognee_client,
        )
    """

    REFLECTION_PROMPT = """
An AI agent attempted a task and failed. Your job is to analyze the failure and
generate a single, actionable lesson that will help the agent succeed on the
next attempt.

Agent: {agent_id}
Task: {task_name}
Action attempted: {action}
Error received: {error}
Prior context (from knowledge graph): {prior_context}

Provide your reflection as a single paragraph starting with "LESSON:".
Focus on what to do differently, not just what went wrong.
Be specific, concrete, and actionable. Maximum 3 sentences.
"""

    LESSON_INJECTION_PROMPT = """
Before attempting this task, review the following lessons from prior failures:

{lessons}

Apply these lessons proactively. Do not repeat the same mistakes.
"""

    def __init__(self) -> None:
        from core.llm.llm_provider import get_llm_provider, LLMConfig, LLMMessage
        self.llm = get_llm_provider()
        self.LLMConfig = LLMConfig
        self.LLMMessage = LLMMessage

    async def reflect(
        self,
        failed_task: Any,
        agent_id: str,
        memory_client: Any,
        cognee_client: Any,
    ) -> str:
        """
        Generate a verbal reflection on a failed task and store it in memory.

        Args:
            failed_task: A WorkflowTask instance with .name, .action, .error fields
            agent_id:    The ID of the agent that failed
            memory_client: OpenViking memory client for L1 storage
            cognee_client: Cognee knowledge graph client for prior context

        Returns:
            The generated lesson string (starts with "LESSON:")
        """
        if not REFLEXION_ENABLED:
            logger.debug("[Reflexion] Disabled via REFLEXION_ENABLED=false")
            return ""

        task_name = getattr(failed_task, "name", "Unknown Task")
        action = getattr(failed_task, "action", "unknown")
        error = getattr(failed_task, "error", "unknown error")

        logger.info(
            f"[Reflexion] Reflecting on failure | agent={agent_id} | "
            f"task={task_name[:40]} | error={str(error)[:80]}"
        )

        # ── Retrieve prior context from Cognee ───────────────────────────────
        prior_context = {}
        try:
            prior_context = await cognee_client.check_prior_attempt(action) or {}
        except Exception as e:
            logger.warning(f"[Reflexion] Cognee prior context unavailable: {e}")

        # ── Check failure count threshold ─────────────────────────────────────
        failure_count = prior_context.get("failure_count", 0)
        if failure_count < REFLEXION_TRIGGER_THRESHOLD - 1:
            logger.info(
                f"[Reflexion] Failure count ({failure_count + 1}) below threshold "
                f"({REFLEXION_TRIGGER_THRESHOLD}) — skipping reflection"
            )
            return ""

        # ── Generate verbal reflection via LLM ───────────────────────────────
        model = os.getenv("DEFAULT_AGENT_MODEL", "claude-3-5-sonnet-20241022")

        try:
            response = await self.llm.complete(
                messages=[
                    self.LLMMessage(
                        role="user",
                        content=self.REFLECTION_PROMPT.format(
                            agent_id=agent_id,
                            task_name=task_name,
                            action=action,
                            error=str(error)[:500],
                            prior_context=str(prior_context)[:300],
                        ),
                    )
                ],
                config=self.LLMConfig(model=model, max_tokens=256),
            )
            lesson = response.content.strip()
        except Exception as e:
            logger.error(f"[Reflexion] LLM reflection failed: {e}")
            return ""

        if not lesson.startswith("LESSON:"):
            lesson = f"LESSON: {lesson}"

        logger.info(f"[Reflexion] Generated lesson for {agent_id}: {lesson[:120]}")

        # ── Store lesson in agent's L1 episodic memory ───────────────────────
        try:
            await memory_client.store(
                agent_id=agent_id,
                memory_type="L1",
                content=lesson,
                tags=["reflection", "lesson", action, task_name],
            )
            logger.info(f"[Reflexion] Lesson stored in {agent_id}'s L1 memory")
        except Exception as e:
            logger.warning(f"[Reflexion] Memory store failed: {e}")

        # ── Also log to Cognee knowledge graph ───────────────────────────────
        try:
            await cognee_client.log_outcome(
                task_description=f"{agent_id}:{action}",
                outcome=f"failed:{error[:100]}",
                metadata={"lesson": lesson, "failure_count": failure_count + 1},
            )
        except Exception as e:
            logger.warning(f"[Reflexion] Cognee log failed: {e}")

        return lesson

    async def get_lessons_for_agent(
        self,
        agent_id: str,
        action: str,
        memory_client: Any,
    ) -> str:
        """
        Retrieve all stored lessons for an agent+action combination and format
        them as a context injection string for the next dispatch.

        Returns an empty string if no lessons exist or memory is unavailable.
        """
        if not REFLEXION_ENABLED:
            return ""

        try:
            memories = await memory_client.retrieve(
                agent_id=agent_id,
                memory_type="L1",
                tags=["lesson", action],
                limit=5,
            )
            if not memories:
                return ""

            lessons_text = "\n".join(
                f"- {m.get('content', '')}" for m in memories
            )
            return self.LESSON_INJECTION_PROMPT.format(lessons=lessons_text)
        except Exception as e:
            logger.warning(f"[Reflexion] Failed to retrieve lessons for {agent_id}: {e}")
            return ""


# ─── Module-level singleton ───────────────────────────────────────────────────
_reflector: Optional[ReflectorAgent] = None


def get_reflector() -> ReflectorAgent:
    """Return the module-level ReflectorAgent singleton."""
    global _reflector
    if _reflector is None:
        _reflector = ReflectorAgent()
    return _reflector
