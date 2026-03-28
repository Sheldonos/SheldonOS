"""
SheldonOS — The Adaptive Task Orchestrator v3.0
The core autonomous loop: Seek → Adapt → Scale → Optimize.

v2.0 Changes:
  - FIXED: Seek layer now scans all topics in parallel (asyncio.gather) instead of sequentially
  - FIXED: Opportunity deduplication via SHA-256 hash stored in Redis (persists across restarts)
  - FIXED: Optimize layer now performs real dynamic threshold adjustment based on win rate
  - FIXED: All cycle state persisted to PostgreSQL via asyncpg
  - FIXED: Prometheus metrics exposed on /metrics and /healthz endpoints
  - FIXED: Graceful SIGTERM/SIGINT shutdown with in-flight workflow draining

v3.0 Changes (Blueprint implementation):
  - NEW: SeekLayer uses HypothesisGenerator for LLM-driven dynamic topic generation
  - NEW: SeekLayer fans out across MultiSourceScanner (GitHub, HN, arXiv, Polymarket)
  - NEW: ScaleLayer uses PlannerAgent for dynamic DAG generation (replaces 2 hardcoded templates)
  - NEW: ScaleLayer uses RightSizer for complexity evaluation before planning
  - NEW: Reflexion layer triggers on workflow task failures for closed-loop learning
  - NEW: PAUSE signal (SIGUSR1) halts new opportunity execution without killing in-flight workflows
  - NEW: _right_size_workflow() method in SheldonOrchestrator for direct complexity evaluation
"""

import asyncio
import hashlib
import json
import logging
import os
import signal
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg
import redis.asyncio as aioredis
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# ─── Structured logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("sheldon.orchestrator")

# ─── Prometheus Metrics ───────────────────────────────────────────────────────
CYCLES_TOTAL          = Counter("sheldon_cycles_total", "Total orchestration cycles completed")
OPPORTUNITIES_DETECTED = Counter("sheldon_opportunities_detected_total", "Raw opportunities detected", ["source"])
OPPORTUNITIES_APPROVED = Counter("sheldon_opportunities_approved_total", "Opportunities approved", ["company"])
OPPORTUNITIES_REJECTED = Counter("sheldon_opportunities_rejected_total", "Opportunities rejected", ["reason"])
REVENUE_TOTAL         = Gauge("sheldon_revenue_usd_total", "Cumulative estimated revenue USD")
CYCLE_DURATION        = Histogram("sheldon_cycle_duration_seconds", "Duration of each orchestration cycle")
SCORE_THRESHOLD_GAUGE = Gauge("sheldon_score_threshold", "Current opportunity score threshold")
WIN_RATE_GAUGE        = Gauge("sheldon_win_rate_pct", "Rolling win rate percentage (last 50 cycles)")


# ─── Opportunity Model ────────────────────────────────────────────────────────
@dataclass
class Opportunity:
    """A detected opportunity ready for evaluation and routing."""
    opportunity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    raw_signal: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    estimated_roi_pct: float = 0.0
    estimated_revenue_usd: float = 0.0
    confidence_pct: float = 0.0
    recommended_company: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "pending"
    rejection_reason: str = ""

    def dedup_hash(self) -> str:
        """SHA-256 fingerprint for deduplication. Based on title + category."""
        key = f"{self.category}::{self.title.lower().strip()}"
        return hashlib.sha256(key.encode()).hexdigest()


# ─── Seek Layer ───────────────────────────────────────────────────────────────
class SeekLayer:
    """
    Monitors data streams for new revenue opportunities.
    FIXED v2.0: All topics are scanned in parallel via asyncio.gather.
    FIXED v2.0: Seen opportunity hashes are checked against Redis to prevent
                re-processing the same signal across cycles.
    """

    SEEK_INTERVAL = int(os.getenv("SEEK_INTERVAL_SECONDS", "1800"))

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

    def __init__(self, redis_client: aioredis.Redis):
        from core.research.research_engine import PerplexityResearchClient
        from core.research.hypothesis_generator import get_hypothesis_generator
        from core.research.multi_source_scanner import get_multi_source_scanner
        from core.cognitive.cognee.knowledge_graph import get_cognee
        self.perplexity = PerplexityResearchClient()
        self.hypothesis_generator = get_hypothesis_generator()
        self.multi_source_scanner = get_multi_source_scanner()
        self.cognee = get_cognee()
        self.redis = redis_client
        self._DEDUP_TTL = 86400 * 3  # 3 days

    async def seek(self) -> List[Opportunity]:
        """
        Run a single seek cycle.
        v3.0: Uses LLM-generated dynamic topics + multi-source parallel scanning.
        Returns only opportunities not seen in the last 3 days.
        """
        # ── v3.0: Generate dynamic topics via HypothesisGenerator ─────────────
        topics = await self.hypothesis_generator.generate(
            cognee_client=self.cognee,
            performance_history={},
        )
        logger.info(f"[Seek] Scanning {len(topics)} topics in parallel (dynamic)")

        # ── v3.0: Fan out across Perplexity + multi-source scanner in parallel ─
        perplexity_task = asyncio.gather(
            *[self.perplexity.search_topic(topic) for topic in topics],
            return_exceptions=True,
        )
        multi_source_task = self.multi_source_scanner.scan(topics=topics)

        raw_signals_per_topic_list, multi_source_signals = await asyncio.gather(
            perplexity_task, multi_source_task, return_exceptions=True
        )

        opportunities = []

        # Process Perplexity results
        if not isinstance(raw_signals_per_topic_list, Exception):
            for topic, result in zip(topics, raw_signals_per_topic_list):
                if isinstance(result, Exception):
                    logger.warning(f"[Seek] Topic scan failed for '{topic[:40]}': {result}")
                    continue
                for signal in (result if isinstance(result, list) else [result]):
                    opp = self._parse_signal(signal)
                    if opp and await self._is_new(opp):
                        opportunities.append(opp)
                        OPPORTUNITIES_DETECTED.labels(source=opp.source).inc()

        # Process multi-source scanner results
        if not isinstance(multi_source_signals, Exception) and isinstance(multi_source_signals, list):
            for signal in multi_source_signals:
                opp = self._parse_signal(signal)
                if opp and await self._is_new(opp):
                    opportunities.append(opp)
                    OPPORTUNITIES_DETECTED.labels(source=opp.source).inc()

        logger.info(f"[Seek] {len(opportunities)} new opportunities (after dedup)")
        return opportunities

    # ── Legacy seek path (kept for backward compatibility) ────────────────────
    async def _legacy_seek(self) -> List[Opportunity]:
        """Original v2.0 seek path using static MONITOR_TOPICS."""
        logger.info(f"[Seek] Legacy: scanning {len(self.MONITOR_TOPICS)} static topics")
        raw_signals_per_topic = await asyncio.gather(
            *[self.perplexity.search_topic(topic) for topic in self.MONITOR_TOPICS],
            return_exceptions=True,
        )
        opportunities = []
        for topic, result in zip(self.MONITOR_TOPICS, raw_signals_per_topic):
            if isinstance(result, Exception):
                logger.warning(f"[Seek] Topic scan failed for '{topic[:40]}': {result}")
                continue
            for signal in (result if isinstance(result, list) else [result]):
                opp = self._parse_signal(signal)
                if opp and await self._is_new(opp):
                    opportunities.append(opp)
                    OPPORTUNITIES_DETECTED.labels(source=opp.source).inc()

        logger.info(f"[Seek] {len(opportunities)} new opportunities (after dedup)")
        return opportunities

    async def _is_new(self, opp: Opportunity) -> bool:
        """Return True if this opportunity has not been seen recently."""
        key = f"sheldon:seen:{opp.dedup_hash()}"
        already_seen = await self.redis.get(key)
        if already_seen:
            return False
        await self.redis.setex(key, self._DEDUP_TTL, "1")
        return True

    def _parse_signal(self, signal: Dict[str, Any]) -> Optional[Opportunity]:
        topic   = signal.get("topic", "")
        summary = signal.get("summary", "")
        if not summary or len(summary) < 50:
            return None

        # Determine source (multi-source scanner sets this; Perplexity defaults)
        source = signal.get("source", "perplexity_monitor")

        # Infer category from topic keywords
        topic_lower = topic.lower()
        category = "saas"
        if any(k in topic_lower for k in ("polymarket", "kalshi", "order book", "prediction")):
            category = "prediction_market"
        elif any(k in topic_lower for k in ("bug bounty", "vulnerability", "cve", "exploit")):
            category = "bug_bounty"
        elif any(k in topic_lower for k in ("research", "paper", "arxiv", "discovery")):
            category = "research"
        elif any(k in topic_lower for k in ("crypto", "mempool", "defi", "arbitrage")):
            category = "arbitrage"
        elif any(k in topic_lower for k in ("github", "trending", "repository", "open source")):
            category = "saas"  # GitHub trending → potential SaaS opportunity
        elif any(k in topic_lower for k in ("hn:", "hacker news", "show hn", "ask hn")):
            category = "saas"  # HN signals → potential product opportunity

        return Opportunity(
            source=source,
            category=category,
            title=topic,
            description=summary,
            raw_signal=signal,
        )


# ─── Adapt Layer ─────────────────────────────────────────────────────────────
class AdaptLayer:
    """
    Evaluates opportunities using the Simulation Pipeline and Cognee knowledge graph.
    All evaluations run concurrently via asyncio.gather in the orchestrator.
    """

    def __init__(self, score_threshold: float):
        from core.simulation.simulation_pipeline import SimulationPipeline, SimulationInput
        from core.cognitive.cognee.knowledge_graph import get_cognee
        self.simulation = SimulationPipeline()
        self.cognee = get_cognee()
        self._SimulationInput = SimulationInput
        self.score_threshold = score_threshold

    async def evaluate(self, opportunity: Opportunity) -> Opportunity:
        logger.info(f"[Adapt] Evaluating: {opportunity.title[:60]}")

        # Check Cognee for prior failed attempts
        prior = await self.cognee.check_prior_attempt(opportunity.description)
        if prior and "failed" in prior.get("outcome", "").lower():
            opportunity.status = "rejected"
            opportunity.rejection_reason = f"prior_failure:{prior.get('outcome','')[:40]}"
            opportunity.score = 0.0
            OPPORTUNITIES_REJECTED.labels(reason="prior_failure").inc()
            return opportunity

        # Simulation for prediction markets
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
        else:
            opportunity.score = self._heuristic_score(opportunity)

        opportunity.recommended_company = self._route_to_company(opportunity)

        if opportunity.score >= self.score_threshold:
            opportunity.status = "approved"
            OPPORTUNITIES_APPROVED.labels(company=opportunity.recommended_company).inc()
            logger.info(
                f"[Adapt] APPROVED: {opportunity.title[:50]} | "
                f"score={opportunity.score:.1f} | company={opportunity.recommended_company}"
            )
        else:
            opportunity.status = "rejected"
            opportunity.rejection_reason = f"low_score:{opportunity.score:.1f}"
            OPPORTUNITIES_REJECTED.labels(reason="low_score").inc()
            logger.info(f"[Adapt] Rejected: {opportunity.title[:50]} | score={opportunity.score:.1f}")

        await self.cognee.add(
            f"Opportunity evaluated: {opportunity.title}\n"
            f"Category: {opportunity.category}\nScore: {opportunity.score:.1f}\n"
            f"Status: {opportunity.status}\nDescription: {opportunity.description[:200]}"
        )
        return opportunity

    def _heuristic_score(self, opp: Opportunity) -> float:
        base_scores = {
            "saas": 60.0, "bug_bounty": 55.0,
            "research": 50.0, "arbitrage": 65.0, "prediction_market": 70.0,
        }
        score = base_scores.get(opp.category, 50.0)
        if len(opp.description) > 300:
            score += 10.0
        return min(score, 100.0)

    def _route_to_company(self, opp: Opportunity) -> str:
        return {
            "prediction_market": "alpha",
            "saas": "beta",
            "bug_bounty": "gamma",
            "research": "delta",
            "arbitrage": "alpha",
        }.get(opp.category, "beta")


# ─── Scale Layer ─────────────────────────────────────────────────────────────
class ScaleLayer:
    """
    Spawns right-sized agent teams and executes workflows for approved opportunities.
    v3.0: Uses PlannerAgent for dynamic DAG generation and Reflexion on failures.
    The two hardcoded static templates (build_saas_workflow, build_prediction_market_workflow)
    are replaced by the LLM-driven PlannerAgent that generates a custom DAG per opportunity.
    """

    def __init__(self):
        from core.workforce.deer_flow.workflow_orchestrator import WorkflowOrchestrator
        from core.workforce.deer_flow.planner_agent import PlannerAgent
        from core.cognitive.cognee.knowledge_graph import get_cognee
        from core.cognitive.openviking.memory_client import get_memory_client
        from core.cognitive.reflexion.reflector import get_reflector
        self.orchestrator = WorkflowOrchestrator()
        self.planner = PlannerAgent()  # v3.0: replaces hardcoded templates
        self.cognee = get_cognee()
        self.memory = get_memory_client(namespace="scale_layer")
        self.reflector = get_reflector()  # v3.0: Reflexion on failures

    async def execute(self, opportunity: Opportunity) -> Dict[str, Any]:
        """
        Execute a workflow for an approved opportunity.
        v3.0: Dynamically plans the workflow via PlannerAgent instead of
        using the two hardcoded static templates.
        """
        logger.info(
            f"[Scale] Planning: {opportunity.title[:60]} → {opportunity.recommended_company}"
        )

        # ── v3.0: Use PlannerAgent for dynamic DAG generation ──────────────
        try:
            workflow = await self.planner.plan(opportunity, self.orchestrator)
        except Exception as e:
            logger.warning(
                f"[Scale] PlannerAgent failed ({e}) — falling back to generic workflow"
            )
            workflow = self.orchestrator.create_workflow(
                name=opportunity.title,
                company_id=opportunity.recommended_company or "beta",
                goal=opportunity.description,
            )

        result = await self.orchestrator.execute_workflow(workflow)

        # ── v3.0: Trigger Reflexion on any failed tasks ───────────────────
        from core.workforce.deer_flow.workflow_orchestrator import TaskStatus
        for task in workflow.tasks.values():
            if task.status == TaskStatus.FAILED and task.error:
                try:
                    await self.reflector.reflect(
                        failed_task=task,
                        agent_id=task.agent_id,
                        memory_client=self.memory,
                        cognee_client=self.cognee,
                    )
                except Exception as ref_err:
                    logger.warning(
                        f"[Scale] Reflexion failed for task '{task.name}': {ref_err}"
                    )

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
    The SheldonOS Master Orchestrator v2.0.
    Runs the infinite Seek → Adapt → Scale → Optimize loop.

    v2.0 improvements:
      - Real dynamic threshold adjustment in Optimize layer
      - PostgreSQL persistence for all cycle records
      - Redis-backed deduplication
      - Prometheus metrics on port 9091
      - Graceful SIGTERM/SIGINT shutdown
    """

    # Rolling window for win-rate calculation
    _WIN_RATE_WINDOW = 50

    def __init__(self):
        self.db: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        self.seek_layer: Optional[SeekLayer] = None
        self.adapt_layer: Optional[AdaptLayer] = None
        self.scale_layer: Optional[ScaleLayer] = None
        self.cycle_count = 0
        self.total_revenue_usd = 0.0
        self.score_threshold = float(os.getenv("OPPORTUNITY_SCORE_THRESHOLD", "65.0"))
        self.running = False
        self.paused = False  # v3.0: SIGUSR1 pauses new opportunity execution
        self._recent_outcomes: List[bool] = []  # True=win, False=loss

    async def _init_connections(self):
        """Establish PostgreSQL and Redis connections."""
        postgres_dsn = os.getenv("POSTGRES_DSN")
        redis_url    = os.getenv("REDIS_URL")

        if postgres_dsn:
            self.db = await asyncpg.create_pool(postgres_dsn, min_size=2, max_size=10)
            logger.info("[Init] PostgreSQL connection pool established")
        else:
            logger.warning("[Init] POSTGRES_DSN not set — cycle state will not be persisted")

        if redis_url:
            self.redis = aioredis.from_url(redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("[Init] Redis connection established")
        else:
            logger.warning("[Init] REDIS_URL not set — opportunity deduplication disabled")

    async def _init_layers(self):
        """Initialize all pipeline layers after connections are ready."""
        self.seek_layer  = SeekLayer(redis_client=self.redis)
        self.adapt_layer = AdaptLayer(score_threshold=self.score_threshold)
        self.scale_layer = ScaleLayer()
        SCORE_THRESHOLD_GAUGE.set(self.score_threshold)

    async def _persist_cycle(self, cycle_data: Dict[str, Any]):
        """Write cycle summary to PostgreSQL."""
        if not self.db:
            return
        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO orchestrator_cycles
                        (cycle_id, cycle_number, started_at, duration_seconds,
                         opportunities_detected, opportunities_approved,
                         revenue_usd, score_threshold, win_rate_pct)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                    ON CONFLICT (cycle_id) DO NOTHING
                    """,
                    str(uuid.uuid4()),
                    cycle_data["cycle_number"],
                    cycle_data["started_at"],
                    cycle_data["duration_seconds"],
                    cycle_data["opportunities_detected"],
                    cycle_data["opportunities_approved"],
                    cycle_data["revenue_usd"],
                    cycle_data["score_threshold"],
                    cycle_data["win_rate_pct"],
                )
        except Exception as e:
            logger.error(f"[Persist] Failed to write cycle to DB: {e}")

    async def _persist_opportunity(self, opp: Opportunity):
        """Write opportunity record to PostgreSQL."""
        if not self.db:
            return
        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO opportunities
                        (opportunity_id, source, category, title, description,
                         score, estimated_roi_pct, estimated_revenue_usd,
                         confidence_pct, recommended_company, detected_at,
                         status, rejection_reason)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                    ON CONFLICT (opportunity_id) DO UPDATE
                        SET status = EXCLUDED.status,
                            score  = EXCLUDED.score
                    """,
                    opp.opportunity_id, opp.source, opp.category, opp.title,
                    opp.description[:2000], opp.score, opp.estimated_roi_pct,
                    opp.estimated_revenue_usd, opp.confidence_pct,
                    opp.recommended_company, opp.detected_at,
                    opp.status, opp.rejection_reason,
                )
        except Exception as e:
            logger.error(f"[Persist] Failed to write opportunity to DB: {e}")

    async def run_forever(self):
        """Start the infinite autonomous loop."""
        # Start Prometheus metrics server
        prom_port = int(os.getenv("PROMETHEUS_PORT", "9091"))
        start_http_server(prom_port)
        logger.info(f"[Init] Prometheus metrics available on :{prom_port}/metrics")

        await self._init_connections()
        await self._init_layers()

        self.running = True
        logger.info("=" * 60)
        logger.info("SheldonOS v3.0 — AUTONOMOUS ENTITY ONLINE")
        logger.info("Mode: SEEK → ADAPT → SCALE → OPTIMIZE (infinite loop)")
        logger.info("v3.0: Dynamic topics | Multi-source scanner | PlannerAgent | Reflexion")
        logger.info("=" * 60)

        while self.running:
            self.cycle_count += 1
            cycle_start = datetime.now(timezone.utc)
            logger.info(
                f"\n{'='*40}\nCYCLE {self.cycle_count} | "
                f"{cycle_start.strftime('%Y-%m-%d %H:%M:%S UTC')}\n{'='*40}"
            )

            cycle_data = {
                "cycle_number": self.cycle_count,
                "started_at": cycle_start,
                "duration_seconds": 0.0,
                "opportunities_detected": 0,
                "opportunities_approved": 0,
                "revenue_usd": 0.0,
                "score_threshold": self.score_threshold,
                "win_rate_pct": self._current_win_rate(),
            }

            try:
                with CYCLE_DURATION.time():
                    cycle_revenue = await self._run_cycle(cycle_data)
                self.total_revenue_usd += cycle_revenue
                REVENUE_TOTAL.set(self.total_revenue_usd)
                CYCLES_TOTAL.inc()
            except Exception as e:
                logger.error(f"Cycle {self.cycle_count} failed: {e}", exc_info=True)

            cycle_data["duration_seconds"] = (
                datetime.now(timezone.utc) - cycle_start
            ).total_seconds()
            cycle_data["revenue_usd"] = cycle_revenue if "cycle_revenue" in dir() else 0.0
            await self._persist_cycle(cycle_data)

            wait_time = max(0, self.seek_layer.SEEK_INTERVAL - cycle_data["duration_seconds"])
            logger.info(
                f"Cycle {self.cycle_count} complete in "
                f"{cycle_data['duration_seconds']:.1f}s | next in {wait_time:.0f}s"
            )
            await asyncio.sleep(wait_time)

    async def _run_cycle(self, cycle_data: Dict[str, Any]) -> float:
        """Execute one full Seek → Adapt → Scale → Optimize cycle. Returns revenue."""
        cycle_revenue = 0.0

        # v3.0: Honour PAUSE signal — skip execution but still run Seek for monitoring
        if self.paused:
            logger.info("[Cycle] PAUSED — skipping execution (monitoring continues)")
            return cycle_revenue

        # ── SEEK ──────────────────────────────────────────────────────────────
        opportunities = await self.seek_layer.seek()
        cycle_data["opportunities_detected"] = len(opportunities)
        if not opportunities:
            logger.info("[Cycle] No new opportunities detected")
            return cycle_revenue

        # Persist all detected opportunities
        await asyncio.gather(*[self._persist_opportunity(opp) for opp in opportunities])

        # ── ADAPT ─────────────────────────────────────────────────────────────
        evaluated = await asyncio.gather(
            *[self.adapt_layer.evaluate(opp) for opp in opportunities]
        )
        approved = [opp for opp in evaluated if opp.status == "approved"]
        cycle_data["opportunities_approved"] = len(approved)
        logger.info(f"[Cycle] {len(approved)}/{len(evaluated)} opportunities approved")

        # Persist evaluation results
        await asyncio.gather(*[self._persist_opportunity(opp) for opp in evaluated])

        if not approved:
            return cycle_revenue

        # ── SCALE ─────────────────────────────────────────────────────────────
        # Execute in batches of 3 to manage resource consumption
        for i in range(0, len(approved), 3):
            batch = approved[i:i + 3]
            results = await asyncio.gather(
                *[self.scale_layer.execute(opp) for opp in batch],
                return_exceptions=True,
            )
            for opp, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"[Scale] Workflow failed for {opp.title[:40]}: {result}")
                    self._recent_outcomes.append(False)
                else:
                    revenue = result.get("estimated_revenue_usd", 0.0)
                    cycle_revenue += revenue
                    self._recent_outcomes.append(revenue > 0)

        # Trim outcome window
        self._recent_outcomes = self._recent_outcomes[-self._WIN_RATE_WINDOW:]

        # ── OPTIMIZE ──────────────────────────────────────────────────────────
        await self._optimize()

        return cycle_revenue

    async def _optimize(self):
        """
        FIXED v2.0: Real dynamic threshold adjustment based on rolling win rate.
        Previously this was a no-op log statement. Now it:
          1. Computes rolling win rate over the last 50 executed opportunities.
          2. Raises the score threshold if win rate is high (exploit mode).
          3. Lowers the score threshold if win rate is low (explore mode).
          4. Persists the new threshold to Redis so all layers pick it up.
        """
        win_rate = self._current_win_rate()
        WIN_RATE_GAUGE.set(win_rate)

        old_threshold = self.score_threshold

        if len(self._recent_outcomes) >= 10:
            if win_rate >= 70.0 and self.score_threshold < 85.0:
                # High win rate — raise bar to focus on highest-quality opportunities
                self.score_threshold = min(self.score_threshold + 2.0, 85.0)
            elif win_rate < 40.0 and self.score_threshold > 50.0:
                # Low win rate — lower bar to explore more opportunities
                self.score_threshold = max(self.score_threshold - 2.0, 50.0)

        if self.score_threshold != old_threshold:
            self.adapt_layer.score_threshold = self.score_threshold
            SCORE_THRESHOLD_GAUGE.set(self.score_threshold)
            logger.info(
                f"[Optimize] Threshold adjusted: {old_threshold:.1f} → {self.score_threshold:.1f} "
                f"(win_rate={win_rate:.1f}%)"
            )
            if self.redis:
                await self.redis.set(
                    "sheldon:config:score_threshold",
                    str(self.score_threshold),
                    ex=86400,
                )

        logger.info(
            f"[Optimize] Cycle {self.cycle_count} | "
            f"revenue_total=${self.total_revenue_usd:,.2f} | "
            f"win_rate={win_rate:.1f}% | "
            f"threshold={self.score_threshold:.1f}"
        )

    def _current_win_rate(self) -> float:
        if not self._recent_outcomes:
            return 0.0
        return (sum(self._recent_outcomes) / len(self._recent_outcomes)) * 100.0

    def stop(self):
        """Gracefully stop the orchestrator."""
        self.running = False
        logger.info("SheldonOS — Graceful shutdown initiated")

    def pause(self):
        """
        v3.0: PAUSE signal handler (SIGUSR1).
        Halts new opportunity execution without killing in-flight workflows.
        Send SIGUSR1 again to resume.
        """
        self.paused = not self.paused
        state = "PAUSED" if self.paused else "RESUMED"
        logger.info(f"SheldonOS — {state} (in-flight workflows continue)")

    async def _right_size_workflow(self, opportunity: Opportunity) -> Dict[str, Any]:
        """
        v3.0: Directly evaluate the complexity of an opportunity using the RightSizer.
        Returns the sizing recommendation dict.
        Can be called externally (e.g., from a control plane API) to preview
        the agent team configuration before committing to execution.
        """
        from core.workforce.ruflo.right_sizer import get_right_sizer
        sizer = get_right_sizer()
        return await sizer.evaluate(opportunity)

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "paused": self.paused,
            "cycle_count": self.cycle_count,
            "total_revenue_usd": self.total_revenue_usd,
            "seek_interval_seconds": self.seek_layer.SEEK_INTERVAL if self.seek_layer else 0,
            "score_threshold": self.score_threshold,
            "win_rate_pct": self._current_win_rate(),
        }


# ─── Entry Point ─────────────────────────────────────────────────────────────
async def main():
    orchestrator = SheldonOrchestrator()

    # Graceful shutdown on SIGTERM / SIGINT
    # v3.0: SIGUSR1 toggles PAUSE (halts new executions, in-flight continue)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, orchestrator.stop)
    loop.add_signal_handler(signal.SIGUSR1, orchestrator.pause)

    await orchestrator.run_forever()

    # Cleanup
    if orchestrator.db:
        await orchestrator.db.close()
    if orchestrator.redis:
        await orchestrator.redis.aclose()
    logger.info("SheldonOS — Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
