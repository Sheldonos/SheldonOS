"""
SheldonOS — Dynamic Hypothesis Generator v3.0
Replaces the hardcoded MONITOR_TOPICS list in SeekLayer with an LLM-driven
dynamic topic generation system.

Each seek cycle, the HypothesisGenerator:
  1. Queries Cognee for the top-performing past strategies
  2. Calls an LLM to generate a fresh list of search hypotheses informed by
     what has been profitable and current market conditions
  3. Falls back to the static MONITOR_TOPICS list if LLM generation fails

This allows the Seek layer to discover novel, out-of-distribution opportunities
that were never explicitly programmed into the system.

Reference: Blueprint §3.3 — Level 3, Autonomous Opportunity Sensing (Epsilon v3.0)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.research.hypothesis")

# ─── Configuration ────────────────────────────────────────────────────────────
DYNAMIC_TOPICS_ENABLED: bool = os.getenv("DYNAMIC_TOPICS_ENABLED", "true").lower() == "true"
DYNAMIC_TOPICS_COUNT: int = int(os.getenv("DYNAMIC_TOPICS_COUNT", "15"))

# ─── Static Fallback Topics ───────────────────────────────────────────────────
# Used when LLM generation fails or DYNAMIC_TOPICS_ENABLED=false.
# Mirrors the original MONITOR_TOPICS from SeekLayer.
STATIC_FALLBACK_TOPICS: List[str] = [
    "Polymarket Kalshi prediction market high volume event",
    "new DeFi protocol launch liquidity opportunity",
    "Hacker News Show HN viral new product",
    "crypto mempool large transaction whale movement",
    "bug bounty program new high reward",
    "micro SaaS acquisition opportunity",
    "emerging AI research paper breakthrough",
    "regulatory arbitrage opportunity fintech",
    "open source project monetization gap",
    "API rate limit pain point developer community",
    "new GitHub trending repository monetization",
    "arXiv preprint novel AI technique application",
    "Polymarket low-liquidity high-edge market",
    "HackerNews Ask HN unsolved developer problem",
    "DeFi yield farming new protocol launch",
]


class HypothesisGenerator:
    """
    Generates dynamic search hypotheses for the Seek layer using an LLM
    informed by past performance data from the Cognee knowledge graph.

    Usage:
        generator = HypothesisGenerator()
        topics = await generator.generate(cognee_client=cognee, performance_history={})
    """

    HYPOTHESIS_SYSTEM_PROMPT = """
You are the SheldonOS Opportunity Scout. Your job is to generate highly specific,
actionable search queries that are most likely to surface profitable opportunities
for an autonomous AI economic system.

The system operates across five domains:
  1. Prediction markets (Polymarket, Kalshi, Manifold)
  2. DeFi arbitrage and yield opportunities
  3. Bug bounty programs (HackerOne, Bugcrowd, Intigriti)
  4. Micro-SaaS product opportunities
  5. Research monetization (arXiv, patents, IP)

Generate queries that are:
  - Specific and actionable (not generic like "AI trends")
  - Likely to surface time-sensitive opportunities
  - Diverse across the five domains above
  - Informed by the profitable past strategies provided

Return a JSON object with a single key "queries" containing an array of
exactly {count} search query strings.
"""

    def __init__(self) -> None:
        from core.llm.llm_provider import get_llm_provider, LLMConfig, LLMMessage
        self.llm = get_llm_provider()
        self.LLMConfig = LLMConfig
        self.LLMMessage = LLMMessage

    async def generate(
        self,
        cognee_client: Any,
        performance_history: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Generate a fresh list of search topics for the current seek cycle.

        Args:
            cognee_client:       Cognee knowledge graph client
            performance_history: Optional dict of recent performance metrics

        Returns:
            List of search query strings (DYNAMIC_TOPICS_COUNT items on success,
            STATIC_FALLBACK_TOPICS on failure)
        """
        if not DYNAMIC_TOPICS_ENABLED:
            logger.info("[Hypothesis] Dynamic topics disabled — using static fallback")
            return STATIC_FALLBACK_TOPICS

        # ── Retrieve best-performing past strategies from Cognee ──────────────
        best_strategies: List[Dict[str, Any]] = []
        try:
            best_strategies = await cognee_client.get_best_performing_strategies(limit=5)
        except Exception as e:
            logger.warning(f"[Hypothesis] Could not retrieve strategies from Cognee: {e}")

        # ── Build the prompt ──────────────────────────────────────────────────
        strategies_text = (
            json.dumps(best_strategies, indent=2)
            if best_strategies
            else "No prior profitable strategies recorded yet."
        )

        perf_text = (
            json.dumps(performance_history, indent=2)
            if performance_history
            else "No performance history available."
        )

        user_message = (
            f"Current date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
            f"Top profitable past strategies:\n{strategies_text}\n\n"
            f"Recent performance metrics:\n{perf_text}\n\n"
            f"Generate {DYNAMIC_TOPICS_COUNT} search queries for the next seek cycle."
        )

        model = os.getenv("ECONOMY_AGENT_MODEL", "claude-3-5-haiku-20241022")

        try:
            response = await self.llm.complete(
                messages=[self.LLMMessage(role="user", content=user_message)],
                config=self.LLMConfig(
                    model=model,
                    max_tokens=1024,
                    system_prompt=self.HYPOTHESIS_SYSTEM_PROMPT.format(
                        count=DYNAMIC_TOPICS_COUNT
                    ),
                ),
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            data = json.loads(content)
            queries = data.get("queries", [])

            if not queries or len(queries) < 5:
                logger.warning(
                    f"[Hypothesis] LLM returned only {len(queries)} queries — "
                    "falling back to static topics"
                )
                return STATIC_FALLBACK_TOPICS

            logger.info(
                f"[Hypothesis] Generated {len(queries)} dynamic search topics "
                f"(model={response.model})"
            )
            return queries[:DYNAMIC_TOPICS_COUNT]

        except json.JSONDecodeError as e:
            logger.error(f"[Hypothesis] JSON parse error: {e} — using static fallback")
            return STATIC_FALLBACK_TOPICS
        except Exception as e:
            logger.error(f"[Hypothesis] Generation failed: {e} — using static fallback")
            return STATIC_FALLBACK_TOPICS


# ─── Module-level singleton ───────────────────────────────────────────────────
_generator: Optional[HypothesisGenerator] = None


def get_hypothesis_generator() -> HypothesisGenerator:
    """Return the module-level HypothesisGenerator singleton."""
    global _generator
    if _generator is None:
        _generator = HypothesisGenerator()
    return _generator
