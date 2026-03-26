"""
SheldonOS — The Adaptive Task Orchestrator
The core autonomous loop: Seek → Adapt → Scale → Optimize.
This is the brain of SheldonOS. It runs indefinitely with no hardcoded task list.
It continuously discovers opportunities, simulates outcomes, spawns right-sized teams,
and executes profit-generating workflows.
"""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.orchestrator")


# ─── Opportunity Model ────────────────────────────────────────────────────────
@dataclass
class Opportunity:
    """A detected opportunity ready for evaluation and routing."""
    opportunity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""           # github_trending | polymarket | hackernews | crypto | osint
    category: str = ""         # saas | prediction_market | bug_bounty | research | arbitrage
    title: str = ""
    description: str = ""
    raw_signal: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0         # 0-100 composite opportunity score
    estimated_roi_pct: float = 0.0
    estimated_revenue_usd: float = 0.0
    confidence_pct: float = 0.0
    recommended_company: str = ""  # alpha | beta | gamma | delta | epsilon
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"    # pending | approved | rejected | executing | complete


# ─── Seek Layer ───────────────────────────────────────────────────────────────
class SeekLayer:
    """
    Continuously monitors data streams for new revenue opportunities.
    Runs as a background daemon every SEEK_INTERVAL_SECONDS.
    """

    SEEK_INTERVAL = int(os.getenv("SEEK_INTERVAL_SECONDS", "1800"))  # 30 minutes

    MONITOR_TOPICS = [
        "new AI automation tools GitHub trending",
        "Polymarket unusual order book activity high volume",
        "Hacker News Show HN viral new product",
        "crypto mempool large transaction whale movement",
        "bug bounty program new high reward",
        "micro SaaS acquisition opportunity",
        "emerging AI research paper breakthrough",
        "regulatory arbitrage opportunity fintech",
        "open source project monetization gap",
        "API rate limit pain point developer community",
    ]

    def __init__(self):
        from core.research.research_engine import PerplexityResearchClient
        self.perplexity = PerplexityResearchClient()

    async def seek(self) -> List[Opportunity]:
        """Run a single seek cycle and return detected opportunities."""
        logger.info("[Seek] Starting opportunity scan cycle")
        signals = await self.perplexity.monitor_stream(self.MONITOR_TOPICS)
        opportunities = []

        for signal in signals:
            opp = self._parse_signal(signal)
            if opp:
                opportunities.append(opp)

        logger.info(f"[Seek] Detected {len(opportunities)} raw opportunities")
        return opportunities

    def _parse_signal(self, signal: Dict[str, Any]) -> Optional[Opportunity]:
        """Parse a raw signal into a structured Opportunity."""
        topic = signal.get("topic", "")
        summary = signal.get("summary", "")

        if not summary or len(summary) < 50:
            return None

        # Route to category based on topic keywords
        category = "saas"
        if "polymarket" in topic.lower() or "kalshi" in topic.lower() or "order book" in topic.lower():
            category = "prediction_market"
        elif "bug bounty" in topic.lower() or "vulnerability" in topic.lower():
            category = "bug_bounty"
        elif "research" in topic.lower() or "paper" in topic.lower():
            category = "research"
        elif "crypto" in topic.lower() or "mempool" in topic.lower():
            category = "arbitrage"

        return Opportunity(
            source="perplexity_monitor",
            category=category,
            title=topic,
            description=summary,
            raw_signal=signal,
        )


# ─── Adapt Layer ─────────────────────────────────────────────────────────────
class AdaptLayer:
    """
    Evaluates opportunities using the Simulation Pipeline and Cognee knowledge graph.
    Scores each opportunity and routes approved ones to the Scale layer.
    """

    SCORE_THRESHOLD = float(os.getenv("OPPORTUNITY_SCORE_THRESHOLD", "65.0"))

    def __init__(self):
        from core.simulation.simulation_pipeline import SimulationPipeline, SimulationInput
        from core.cognitive.cognee.knowledge_graph import get_cognee
        self.simulation = SimulationPipeline()
        self.cognee = get_cognee()
        self._SimulationInput = SimulationInput

    async def evaluate(self, opportunity: Opportunity) -> Opportunity:
        """Score an opportunity and determine if it should be executed."""
        logger.info(f"[Adapt] Evaluating: {opportunity.title[:60]}")

        # Step 1: Check Cognee for prior attempts
        prior = await self.cognee.check_prior_attempt(opportunity.description)
        if prior:
            prior_outcome = prior.get("outcome", "unknown")
            if "failed" in prior_outcome.lower() or "loss" in prior_outcome.lower():
                logger.info(f"[Adapt] Skipping — similar opportunity previously failed: {prior_outcome[:50]}")
                opportunity.status = "rejected"
                opportunity.score = 0.0
                return opportunity

        # Step 2: Quick simulation for prediction market opportunities
        if opportunity.category == "prediction_market":
            sim_input = self._SimulationInput(
                event_description=opportunity.description,
                event_category="economics",
                time_horizon_days=7,
                population_size=5000,
                market_question=opportunity.title,
                current_market_odds=0.5,
            )
            sim_result = await self.simulation.run(sim_input)
            if sim_result.get("status") == "complete":
                rec = sim_result["recommendation"]
                opportunity.confidence_pct = rec.get("confidence_pct", 0.0)
                opportunity.estimated_roi_pct = rec.get("expected_value", 0.0) * 100
                opportunity.score = opportunity.confidence_pct * 0.7 + min(opportunity.estimated_roi_pct * 10, 30)

        # Step 3: Score other categories heuristically
        else:
            opportunity.score = self._heuristic_score(opportunity)

        # Step 4: Route to appropriate company
        opportunity.recommended_company = self._route_to_company(opportunity)

        # Step 5: Approve or reject
        if opportunity.score >= self.SCORE_THRESHOLD:
            opportunity.status = "approved"
            logger.info(
                f"[Adapt] APPROVED: {opportunity.title[:50]} | "
                f"score={opportunity.score:.1f} | company={opportunity.recommended_company}"
            )
        else:
            opportunity.status = "rejected"
            logger.info(f"[Adapt] Rejected: {opportunity.title[:50]} | score={opportunity.score:.1f}")

        # Always record to Cognee
        await self.cognee.add(
            f"Opportunity evaluated: {opportunity.title}\n"
            f"Category: {opportunity.category}\n"
            f"Score: {opportunity.score:.1f}\n"
            f"Status: {opportunity.status}\n"
            f"Description: {opportunity.description[:200]}"
        )

        return opportunity

    def _heuristic_score(self, opp: Opportunity) -> float:
        """Score an opportunity heuristically based on category and signal strength."""
        base_scores = {
            "saas": 60.0,
            "bug_bounty": 55.0,
            "research": 50.0,
            "arbitrage": 65.0,
            "prediction_market": 70.0,
        }
        score = base_scores.get(opp.category, 50.0)
        # Boost for longer, more detailed descriptions (proxy for signal quality)
        if len(opp.description) > 300:
            score += 10.0
        return min(score, 100.0)

    def _route_to_company(self, opp: Opportunity) -> str:
        """Route an opportunity to the appropriate company."""
        routing = {
            "prediction_market": "alpha",
            "saas": "beta",
            "bug_bounty": "gamma",
            "research": "delta",
            "arbitrage": "alpha",
        }
        return routing.get(opp.category, "beta")


# ─── Scale Layer ─────────────────────────────────────────────────────────────
class ScaleLayer:
    """
    Spawns right-sized agent teams and executes workflows for approved opportunities.
    Decommissions teams upon completion and archives outcomes to Cognee.
    """

    def __init__(self):
        from core.workforce.deer_flow.workflow_orchestrator import (
            WorkflowOrchestrator, build_saas_workflow, build_prediction_market_workflow
        )
        from core.cognitive.cognee.knowledge_graph import get_cognee
        self.orchestrator = WorkflowOrchestrator()
        self.cognee = get_cognee()
        self._build_saas = build_saas_workflow
        self._build_prediction = build_prediction_market_workflow

    async def execute(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Execute an approved opportunity by spawning and running the appropriate workflow."""
        logger.info(f"[Scale] Executing: {opportunity.title[:60]} → {opportunity.recommended_company}")

        # Select workflow template
        if opportunity.category == "prediction_market":
            workflow = self._build_prediction(
                self.orchestrator,
                {"event": opportunity.title, "description": opportunity.description}
            )
        elif opportunity.category == "saas":
            workflow = self._build_saas(
                self.orchestrator,
                {"name": opportunity.title, "description": opportunity.description}
            )
        else:
            # Generic workflow for other categories
            from core.workforce.deer_flow.workflow_orchestrator import Workflow
            workflow = self.orchestrator.create_workflow(
                name=opportunity.title,
                company_id=opportunity.recommended_company,
                goal=opportunity.description,
            )

        # Execute the workflow
        result = await self.orchestrator.execute_workflow(workflow)

        # Record outcome to Cognee
        revenue = result.get("estimated_revenue_usd", 0.0)
        await self.cognee.record_outcome(
            task_id=opportunity.opportunity_id,
            company_id=opportunity.recommended_company,
            description=opportunity.description,
            outcome=result.get("status", "unknown"),
            revenue_usd=revenue,
            lessons_learned=str(result),
        )

        opportunity.status = "complete"
        return result


# ─── The Master Orchestrator ──────────────────────────────────────────────────
class SheldonOrchestrator:
    """
    The SheldonOS Master Orchestrator.
    Runs the infinite Seek → Adapt → Scale → Optimize loop.
    This is the single entry point for the autonomous entity.
    """

    def __init__(self):
        self.seek_layer = SeekLayer()
        self.adapt_layer = AdaptLayer()
        self.scale_layer = ScaleLayer()
        self.cycle_count = 0
        self.total_revenue_usd = 0.0
        self.running = False

    async def run_forever(self):
        """Start the infinite autonomous loop. No end date. No hardcoded tasks."""
        self.running = True
        logger.info("=" * 60)
        logger.info("SheldonOS — AUTONOMOUS ENTITY ONLINE")
        logger.info("Mode: SEEK → ADAPT → SCALE → OPTIMIZE (infinite loop)")
        logger.info("=" * 60)

        while self.running:
            self.cycle_count += 1
            cycle_start = datetime.utcnow()
            logger.info(f"\n{'='*40}\nCYCLE {self.cycle_count} | {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*40}")

            try:
                await self._run_cycle()
            except Exception as e:
                logger.error(f"Cycle {self.cycle_count} failed: {e}", exc_info=True)

            # Wait before next cycle
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
            wait_time = max(0, self.seek_layer.SEEK_INTERVAL - cycle_duration)
            logger.info(f"Cycle {self.cycle_count} complete in {cycle_duration:.1f}s | next cycle in {wait_time:.0f}s")
            await asyncio.sleep(wait_time)

    async def _run_cycle(self):
        """Execute one full Seek → Adapt → Scale cycle."""

        # ── SEEK ──────────────────────────────────────────────────────────────
        opportunities = await self.seek_layer.seek()
        if not opportunities:
            logger.info("[Cycle] No opportunities detected this cycle")
            return

        # ── ADAPT ─────────────────────────────────────────────────────────────
        evaluated = await asyncio.gather(*[self.adapt_layer.evaluate(opp) for opp in opportunities])
        approved = [opp for opp in evaluated if opp.status == "approved"]
        logger.info(f"[Cycle] {len(approved)}/{len(evaluated)} opportunities approved")

        if not approved:
            return

        # ── SCALE ─────────────────────────────────────────────────────────────
        # Execute approved opportunities (up to 3 concurrently to manage resources)
        for i in range(0, len(approved), 3):
            batch = approved[i:i+3]
            results = await asyncio.gather(*[self.scale_layer.execute(opp) for opp in batch])
            for result in results:
                revenue = result.get("estimated_revenue_usd", 0.0)
                self.total_revenue_usd += revenue

        # ── OPTIMIZE ──────────────────────────────────────────────────────────
        await self._optimize()

    async def _optimize(self):
        """
        The optimization step: review performance, adjust thresholds, and improve the system.
        Called at the end of every cycle.
        """
        logger.info(f"[Optimize] Total revenue to date: ${self.total_revenue_usd:,.2f}")

        # Adjust opportunity score threshold based on recent performance
        # (In production: query Cognee for win rate and adjust dynamically)
        if self.cycle_count % 10 == 0:
            logger.info(f"[Optimize] Cycle {self.cycle_count} checkpoint — reviewing strategy performance")

    def stop(self):
        """Gracefully stop the orchestrator."""
        self.running = False
        logger.info("SheldonOS — Graceful shutdown initiated")

    def get_status(self) -> Dict[str, Any]:
        """Return the current status of the orchestrator."""
        return {
            "running": self.running,
            "cycle_count": self.cycle_count,
            "total_revenue_usd": self.total_revenue_usd,
            "seek_interval_seconds": self.seek_layer.SEEK_INTERVAL,
            "opportunity_score_threshold": self.adapt_layer.SCORE_THRESHOLD,
        }


# ─── Entry Point ─────────────────────────────────────────────────────────────
async def main():
    """Main entry point for SheldonOS."""
    orchestrator = SheldonOrchestrator()
    await orchestrator.run_forever()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    asyncio.run(main())
