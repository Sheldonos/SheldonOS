"""
SheldonOS — Cognee Knowledge Graph Client
Structures raw data from OpenViking into a queryable knowledge graph.
Connects concepts, entities, and past outcomes to enable intelligent decision-making.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.cognitive.cognee")


@dataclass
class KnowledgeNode:
    """A node in the Cognee knowledge graph."""
    node_id: str
    entity_type: str   # e.g., "opportunity", "agent", "outcome", "market_event"
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class KnowledgeEdge:
    """A directed edge in the Cognee knowledge graph."""
    source_id: str
    target_id: str
    relationship: str  # e.g., "CAUSED", "PRECEDED", "SIMILAR_TO", "GENERATED_REVENUE"
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


class CogneeClient:
    """
    Client for the Cognee knowledge graph engine.
    Provides add, cognify (structure), and search operations.

    Installation: pip install cognee
    Config: COGNEE_API_URL, LLM_API_KEY
    """

    BASE_URL = os.getenv("COGNEE_API_URL", "http://localhost:8765")

    def __init__(self):
        logger.info("Cognee knowledge graph client initialized")

    async def add(self, data: Any, dataset_name: str = "sheldon_global") -> bool:
        """
        Add raw data to Cognee for processing.
        Cognee will automatically extract entities and relationships.
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/api/v1/add",
                    json={"data": data if isinstance(data, str) else str(data),
                          "dataset_name": dataset_name},
                    timeout=30.0,
                )
            success = resp.status_code == 200
            if success:
                logger.debug(f"Added data to Cognee dataset '{dataset_name}'")
            return success
        except Exception as e:
            logger.warning(f"Cognee add failed: {e}")
            return False

    async def cognify(self, dataset_name: str = "sheldon_global") -> bool:
        """
        Trigger Cognee's cognify process to structure the added data into the knowledge graph.
        This extracts entities, builds relationships, and updates the Neo4j graph.
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/api/v1/cognify",
                    json={"dataset_name": dataset_name},
                    timeout=120.0,
                )
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Cognee cognify failed: {e}")
            return False

    async def search(self, query: str, search_type: str = "INSIGHTS",
                     top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search the knowledge graph for relevant insights.
        search_type: INSIGHTS | CHUNKS | GRAPH_COMPLETION | CODE
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/api/v1/search",
                    json={"query": query, "search_type": search_type, "top_k": top_k},
                    timeout=30.0,
                )
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except Exception as e:
            logger.warning(f"Cognee search failed: {e}")
        return []

    async def check_prior_attempt(self, opportunity_description: str) -> Optional[Dict[str, Any]]:
        """
        Check if a similar opportunity was previously attempted.
        Returns the prior outcome if found, None otherwise.
        Critical: agents must call this before starting any new task.
        """
        results = await self.search(
            query=f"previous attempt similar to: {opportunity_description}",
            search_type="INSIGHTS",
            top_k=3,
        )
        if results:
            logger.info(f"Found {len(results)} prior attempts for: {opportunity_description[:50]}...")
            return results[0]
        return None

    async def record_outcome(self, task_id: str, company_id: str, description: str,
                              outcome: str, revenue_usd: float = 0.0,
                              lessons_learned: str = "") -> bool:
        """
        Record the outcome of a completed task to the knowledge graph.
        This is the primary mechanism for the entity to learn from experience.
        """
        data = (
            f"Task ID: {task_id}\n"
            f"Company: {company_id}\n"
            f"Description: {description}\n"
            f"Outcome: {outcome}\n"
            f"Revenue Generated: ${revenue_usd:.2f}\n"
            f"Lessons Learned: {lessons_learned}\n"
        )
        await self.add(data, dataset_name=f"outcomes_{company_id}")
        await self.cognify(dataset_name=f"outcomes_{company_id}")
        logger.info(f"[{company_id}] Outcome recorded: {outcome} | revenue=${revenue_usd:.2f}")
        return True

    async def get_best_performing_strategies(
        self, company_id: str = "all", top_k: int = 5, limit: int = 0
    ) -> List[Dict]:
        """
        Query the knowledge graph for the highest-revenue strategies.
        Accepts optional `limit` kwarg (alias for top_k) for v3.0 HypothesisGenerator
        compatibility.
        Used by the Adapt layer and HypothesisGenerator to prioritize similar opportunities.
        """
        effective_k = limit if limit > 0 else top_k
        query = (
            f"highest revenue strategies for company {company_id}"
            if company_id != "all"
            else "highest revenue strategies across all companies"
        )
        return await self.search(
            query=query,
            search_type="INSIGHTS",
            top_k=effective_k,
        )

    async def log_outcome(
        self,
        task_description: str,
        outcome: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log a task outcome to the knowledge graph.
        Used by the Reflexion layer to record failure lessons.
        Thin wrapper around record_outcome for v3.0 compatibility.
        """
        data = (
            f"Task: {task_description}\n"
            f"Outcome: {outcome}\n"
            f"Metadata: {str(metadata or {})}\n"
        )
        await self.add(data, dataset_name="reflexion_outcomes")
        logger.info(f"[Cognee] Logged outcome: {outcome[:60]}")
        return True

    async def ingest_from_openviking(self, namespace: str, tier: str = "L2"):
        """
        Pull data from OpenViking L2 archive and ingest into Cognee.
        This keeps the knowledge graph synchronized with long-term memory.
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{os.getenv('OPENVIKING_API_URL', 'http://localhost:8766')}/api/memory/export",
                    params={"namespace": namespace, "tier": tier},
                    timeout=30.0,
                )
            if resp.status_code == 200:
                data = resp.json()
                await self.add(str(data), dataset_name=f"openviking_{namespace}")
                logger.info(f"Ingested OpenViking {tier} data from namespace '{namespace}' into Cognee")
        except Exception as e:
            logger.warning(f"OpenViking → Cognee sync failed: {e}")


# ─── Global Cognee Instance ───────────────────────────────────────────────────
_cognee_client: Optional[CogneeClient] = None


def get_cognee() -> CogneeClient:
    """Get the global Cognee client instance."""
    global _cognee_client
    if _cognee_client is None:
        _cognee_client = CogneeClient()
    return _cognee_client
