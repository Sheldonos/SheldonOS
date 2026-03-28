"""
SheldonOS — Ruflo Right-Sizer v3.0
Implements the Right-Sizing Protocol for dynamic agent team composition.

Before executing any workflow, the RightSizer evaluates the complexity of the
opportunity and returns a sizing recommendation that the PlannerAgent uses to
build the optimal DAG.

This prevents over-engineering simple tasks (e.g., checking a prediction market
price) and under-resourcing complex ones (e.g., building a full SaaS product).

Reference: Blueprint §3.5 — Level 5, Recursive Agent Spawning (Right-Sizing)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.workforce.ruflo")

# ─── Configuration ────────────────────────────────────────────────────────────
DYNAMIC_PLANNING_ENABLED: bool = os.getenv("DYNAMIC_PLANNING_ENABLED", "true").lower() == "true"
MAX_PARALLEL_SUBAGENTS: int = int(os.getenv("MAX_PARALLEL_SUBAGENTS", "5"))


class RightSizer:
    """
    Evaluates opportunity complexity and recommends the optimal agent team
    configuration for workflow execution.

    Usage:
        sizer = RightSizer()
        sizing = await sizer.evaluate(opportunity)
        # sizing["complexity_score"] → 1-10
        # sizing["recommended_team_size"] → int
        # sizing["parallelizable_subtasks"] → list of str
        # sizing["sequential_subtasks"] → list of str
        # sizing["estimated_token_budget"] → int
    """

    SIZING_SYSTEM_PROMPT = """
You are the SheldonOS Right-Sizer. Your job is to evaluate the complexity of an
opportunity and recommend the optimal agent team configuration for executing it.

Complexity scale:
  1-3: Simple (single agent, single action — e.g., check a price, read a page)
  4-6: Moderate (2-3 agents, sequential workflow — e.g., research + write + publish)
  7-9: Complex (4-5 agents, parallel subtasks — e.g., full SaaS build)
  10:  Extreme (5+ agents, multi-phase — e.g., novel protocol exploit + deployment)

Return a JSON object with exactly these keys:
  - complexity_score: integer 1-10
  - recommended_team_size: integer (max {max_agents})
  - parallelizable_subtasks: array of strings (tasks that can run in parallel)
  - sequential_subtasks: array of strings (tasks that must run in order)
  - estimated_token_budget: integer (total tokens to allocate across all agents)
  - rationale: string (one sentence explaining the sizing decision)
"""

    def __init__(self) -> None:
        from core.llm.llm_provider import get_llm_provider, LLMConfig, LLMMessage
        self.llm = get_llm_provider()
        self.LLMConfig = LLMConfig
        self.LLMMessage = LLMMessage

    async def evaluate(self, opportunity: Any) -> Dict[str, Any]:
        """
        Evaluate the complexity of an opportunity and return a sizing recommendation.

        Args:
            opportunity: An Opportunity dataclass instance

        Returns:
            Dict with complexity_score, recommended_team_size, parallelizable_subtasks,
            sequential_subtasks, estimated_token_budget, rationale
        """
        if not DYNAMIC_PLANNING_ENABLED:
            return self._default_sizing(opportunity)

        model = os.getenv("ECONOMY_AGENT_MODEL", "claude-3-5-haiku-20241022")

        user_message = (
            f"Opportunity: {opportunity.description[:600]}\n"
            f"Category: {opportunity.category}\n"
            f"Estimated Revenue: ${getattr(opportunity, 'estimated_revenue_usd', 0):.0f}\n"
            f"Score: {getattr(opportunity, 'score', 0):.1f}/100\n\n"
            f"Evaluate complexity and recommend the optimal agent team configuration."
        )

        try:
            response = await self.llm.complete(
                messages=[self.LLMMessage(role="user", content=user_message)],
                config=self.LLMConfig(
                    model=model,
                    max_tokens=512,
                    system_prompt=self.SIZING_SYSTEM_PROMPT.format(
                        max_agents=MAX_PARALLEL_SUBAGENTS
                    ),
                ),
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            sizing = json.loads(content)

            # Enforce the max parallel agents cap
            if sizing.get("recommended_team_size", 0) > MAX_PARALLEL_SUBAGENTS:
                sizing["recommended_team_size"] = MAX_PARALLEL_SUBAGENTS

            logger.info(
                f"[RightSizer] {opportunity.title[:40]} → "
                f"complexity={sizing.get('complexity_score')}/10 | "
                f"team={sizing.get('recommended_team_size')} agents | "
                f"{sizing.get('rationale', '')[:80]}"
            )
            return sizing

        except json.JSONDecodeError as e:
            logger.warning(f"[RightSizer] JSON parse error: {e} — using default sizing")
            return self._default_sizing(opportunity)
        except Exception as e:
            logger.warning(f"[RightSizer] Evaluation failed: {e} — using default sizing")
            return self._default_sizing(opportunity)

    def _default_sizing(self, opportunity: Any) -> Dict[str, Any]:
        """
        Return a sensible default sizing based on opportunity category.
        Used when LLM evaluation is disabled or fails.
        """
        category_defaults: Dict[str, Dict[str, Any]] = {
            "prediction_market": {
                "complexity_score": 4,
                "recommended_team_size": 3,
                "parallelizable_subtasks": ["Ingest Data", "Research Event"],
                "sequential_subtasks": ["Run Simulation", "Analyze Signal", "Execute Trade"],
                "estimated_token_budget": 30000,
                "rationale": "Prediction market: moderate complexity, sequential simulation required.",
            },
            "saas": {
                "complexity_score": 7,
                "recommended_team_size": 5,
                "parallelizable_subtasks": ["Build Backend", "Build Frontend"],
                "sequential_subtasks": ["Market Validation", "Write PRD", "QA Testing", "Deploy"],
                "estimated_token_budget": 100000,
                "rationale": "SaaS build: high complexity, parallel frontend/backend development.",
            },
            "bug_bounty": {
                "complexity_score": 6,
                "recommended_team_size": 3,
                "parallelizable_subtasks": ["Reconnaissance", "Vulnerability Scan"],
                "sequential_subtasks": ["Scope Validation", "Exploit Development", "Report Writing"],
                "estimated_token_budget": 50000,
                "rationale": "Bug bounty: moderate-high complexity, scope validation mandatory first.",
            },
            "research": {
                "complexity_score": 3,
                "recommended_team_size": 2,
                "parallelizable_subtasks": [],
                "sequential_subtasks": ["Research", "Synthesize", "Publish"],
                "estimated_token_budget": 20000,
                "rationale": "Research: low-moderate complexity, sequential workflow.",
            },
            "arbitrage": {
                "complexity_score": 5,
                "recommended_team_size": 2,
                "parallelizable_subtasks": ["Market Analysis", "Risk Assessment"],
                "sequential_subtasks": ["Execute Trade"],
                "estimated_token_budget": 25000,
                "rationale": "Arbitrage: moderate complexity, parallel analysis before execution.",
            },
        }
        return category_defaults.get(
            getattr(opportunity, "category", "saas"),
            {
                "complexity_score": 5,
                "recommended_team_size": 3,
                "parallelizable_subtasks": [],
                "sequential_subtasks": ["Research", "Execute", "Report"],
                "estimated_token_budget": 40000,
                "rationale": "Unknown category: using moderate defaults.",
            },
        )


# ─── Module-level singleton ───────────────────────────────────────────────────
_sizer: Optional[RightSizer] = None


def get_right_sizer() -> RightSizer:
    """Return the module-level RightSizer singleton."""
    global _sizer
    if _sizer is None:
        _sizer = RightSizer()
    return _sizer
