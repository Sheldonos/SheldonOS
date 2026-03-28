"""
SheldonOS — Context Hub Self-Corrector v3.0
Injects relevant Context Hub documentation into agent context on failure,
enabling agents to self-correct by consulting authoritative reference material.

When an agent fails, the SelfCorrector:
  1. Identifies the failure category (API error, logic error, scope violation, etc.)
  2. Retrieves the most relevant Context Hub documents for that category
  3. Returns a formatted context injection string for the next dispatch attempt

This complements the Reflexion layer: Reflexion generates lessons from past
failures, while the SelfCorrector provides authoritative reference material
to guide the correction.

Reference: Blueprint §5 — New Components Summary, self_corrector.py
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.cognitive.context_hub.self_corrector")

# ─── Failure Category → Context Hub Document Mapping ─────────────────────────
# Maps error patterns to the most relevant documentation categories.
_ERROR_TO_DOCS: Dict[str, List[str]] = {
    "scope": ["bug_bounty_scope_policy", "nemoclaw_sandbox_policy"],
    "api": ["api_integration_guide", "rate_limit_handling"],
    "trade": ["automaton_trade_execution", "risk_management_policy"],
    "timeout": ["agent_timeout_handling", "async_best_practices"],
    "json": ["llm_output_parsing", "json_schema_validation"],
    "auth": ["api_authentication_guide", "credential_management"],
    "deploy": ["deployment_runbook", "beta_deployment_guide"],
    "simulation": ["mirofish_simulation_guide", "percepta_api_docs"],
    "memory": ["openviking_memory_guide", "cognee_knowledge_graph_guide"],
    "default": ["general_troubleshooting", "agent_best_practices"],
}


class SelfCorrector:
    """
    Injects Context Hub documentation into agent context on failure.

    Usage:
        corrector = SelfCorrector()
        context_injection = await corrector.get_correction_context(
            failed_task=task,
            error=str(e),
        )
        # Prepend context_injection to the agent's next dispatch message
    """

    CORRECTION_HEADER = """
## Context Hub: Relevant Documentation for Self-Correction

The following reference material has been automatically retrieved because
a prior attempt at this task failed. Review it carefully before retrying.

"""

    def __init__(self) -> None:
        from core.cognitive.context_hub.context_hub import ContextHub
        self.context_hub = ContextHub()

    async def get_correction_context(
        self,
        failed_task: Any,
        error: str,
    ) -> str:
        """
        Retrieve and format relevant Context Hub documents for a failed task.

        Args:
            failed_task: A WorkflowTask instance with .name, .action fields
            error:       The error string from the failed attempt

        Returns:
            A formatted string to prepend to the agent's next dispatch message,
            or an empty string if no relevant documents are found.
        """
        error_lower = error.lower()
        task_action = getattr(failed_task, "action", "").lower()

        # Determine the most relevant document category
        doc_category = "default"
        for category, patterns in [
            ("scope", ["scope", "unauthorized", "out of scope", "forbidden"]),
            ("api", ["api", "http", "status code", "request failed", "connection"]),
            ("trade", ["trade", "execution", "wallet", "gas", "transaction"]),
            ("timeout", ["timeout", "timed out", "asyncio"]),
            ("json", ["json", "parse", "decode", "invalid format"]),
            ("auth", ["auth", "key", "token", "credential", "permission"]),
            ("deploy", ["deploy", "deployment", "docker", "kubernetes"]),
            ("simulation", ["simulation", "mirofish", "percepta", "confidence"]),
            ("memory", ["memory", "cognee", "openviking", "embedding"]),
        ]:
            if any(p in error_lower or p in task_action for p in patterns):
                doc_category = category
                break

        doc_names = _ERROR_TO_DOCS.get(doc_category, _ERROR_TO_DOCS["default"])
        logger.info(
            f"[SelfCorrector] Failure category='{doc_category}' | "
            f"fetching docs: {doc_names}"
        )

        # Retrieve documents from Context Hub
        doc_contents: List[str] = []
        for doc_name in doc_names:
            try:
                content = await self.context_hub.get_document(doc_name)
                if content:
                    doc_contents.append(f"### {doc_name}\n{content[:800]}")
            except Exception as e:
                logger.debug(f"[SelfCorrector] Doc '{doc_name}' unavailable: {e}")

        if not doc_contents:
            return ""

        return self.CORRECTION_HEADER + "\n\n".join(doc_contents)

    async def inject_into_dispatch(
        self,
        original_message: str,
        failed_task: Any,
        error: str,
    ) -> str:
        """
        Convenience method: prepend correction context to a dispatch message.

        Args:
            original_message: The original user message for the dispatch
            failed_task:      The failed WorkflowTask
            error:            The error string

        Returns:
            The original message with correction context prepended, or the
            original message unchanged if no context is available.
        """
        correction_context = await self.get_correction_context(failed_task, error)
        if not correction_context:
            return original_message
        return f"{correction_context}\n\n---\n\n{original_message}"


# ─── Module-level singleton ───────────────────────────────────────────────────
_corrector: Optional[SelfCorrector] = None


def get_self_corrector() -> SelfCorrector:
    """Return the module-level SelfCorrector singleton."""
    global _corrector
    if _corrector is None:
        _corrector = SelfCorrector()
    return _corrector
