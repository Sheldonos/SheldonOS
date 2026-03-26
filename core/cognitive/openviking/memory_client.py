"""
SheldonOS — OpenViking Memory Client
Unified L0/L1/L2 memory filesystem for all SheldonOS agents.
Every agent reads and writes through this client — it is the single source of truth for agent state.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.cognitive.openviking")


class MemoryTier(Enum):
    L0 = "L0"  # Working memory — active session context (fast, ephemeral)
    L1 = "L1"  # Episodic memory — recent task history (medium-term)
    L2 = "L2"  # Long-term archive — all past knowledge (persistent)


@dataclass
class MemoryEntry:
    """A single memory entry in the OpenViking filesystem."""
    key: str
    value: Any
    tier: MemoryTier
    namespace: str
    tags: List[str]
    created_at: str
    ttl_seconds: Optional[int] = None  # None = permanent


class OpenVikingClient:
    """
    Client for the OpenViking context database.
    Implements the L0/L1/L2 tiered memory architecture with semantic search.

    Installation: pip install openviking
    Config: OPENVIKING_API_URL, OPENVIKING_EMBEDDING_MODEL
    """

    BASE_URL = os.getenv("OPENVIKING_API_URL", "http://localhost:8766")
    EMBEDDING_MODEL = os.getenv("OPENVIKING_EMBEDDING_MODEL", "text-embedding-3-small")

    def __init__(self, namespace: str = "global"):
        self.namespace = namespace
        self._session_cache: Dict[str, Any] = {}  # L0 in-process cache
        logger.info(f"OpenViking client initialized | namespace={namespace}")

    # ─── Write Operations ─────────────────────────────────────────────────────
    async def write(self, key: str, value: Any, tier: MemoryTier = MemoryTier.L1,
                    tags: List[str] = None, ttl_seconds: int = None) -> bool:
        """Write a value to the specified memory tier."""
        if tier == MemoryTier.L0:
            self._session_cache[key] = value
            return True

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/api/memory/write",
                    json={
                        "namespace": self.namespace,
                        "key": key,
                        "value": value,
                        "tier": tier.value,
                        "tags": tags or [],
                        "ttl_seconds": ttl_seconds,
                    },
                    timeout=10.0,
                )
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"OpenViking write failed for key '{key}': {e}")
            # Fallback: write to local filesystem
            self._local_write(key, value, tier)
            return False

    def _local_write(self, key: str, value: Any, tier: MemoryTier):
        """Fallback local filesystem write when OpenViking API is unavailable."""
        import json
        base_path = Path(os.getenv("OPENVIKING_LOCAL_PATH", "/tmp/sheldon_memory"))
        tier_path = base_path / self.namespace / tier.value
        tier_path.mkdir(parents=True, exist_ok=True)
        safe_key = key.replace("/", "_").replace(":", "_")
        (tier_path / f"{safe_key}.json").write_text(
            json.dumps({"key": key, "value": value}, default=str)
        )

    # ─── Read Operations ──────────────────────────────────────────────────────
    async def read(self, key: str, tier: MemoryTier = MemoryTier.L1) -> Optional[Any]:
        """Read a value from the specified memory tier."""
        if tier == MemoryTier.L0:
            return self._session_cache.get(key)

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.BASE_URL}/api/memory/read",
                    params={"namespace": self.namespace, "key": key, "tier": tier.value},
                    timeout=10.0,
                )
            if resp.status_code == 200:
                return resp.json().get("value")
        except Exception as e:
            logger.warning(f"OpenViking read failed for key '{key}': {e}")
        return None

    async def search(self, query: str, tier: MemoryTier = MemoryTier.L1,
                     top_k: int = 5, tags: List[str] = None) -> List[MemoryEntry]:
        """Semantic search across the memory tier using embeddings."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/api/memory/search",
                    json={
                        "namespace": self.namespace,
                        "query": query,
                        "tier": tier.value,
                        "top_k": top_k,
                        "tags": tags or [],
                    },
                    timeout=15.0,
                )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                return [MemoryEntry(**r) for r in results]
        except Exception as e:
            logger.warning(f"OpenViking search failed: {e}")
        return []

    async def archive_to_l2(self, key: str):
        """Promote an L1 entry to L2 long-term archive."""
        value = await self.read(key, MemoryTier.L1)
        if value:
            await self.write(key, value, MemoryTier.L2)
            logger.debug(f"Archived '{key}' to L2")

    # ─── Session Management ───────────────────────────────────────────────────
    def clear_l0(self):
        """Clear the L0 working memory at the end of a session."""
        count = len(self._session_cache)
        self._session_cache.clear()
        logger.debug(f"Cleared L0 working memory ({count} entries)")

    async def extract_long_term_knowledge(self, session_summary: str):
        """
        At the end of a session, extract important knowledge from L1 and promote to L2.
        This implements OpenViking's automatic session management feature.
        """
        await self.write(
            key=f"session_summary_{id(self)}",
            value=session_summary,
            tier=MemoryTier.L2,
            tags=["session_summary", self.namespace],
        )
        self.clear_l0()
        logger.info(f"Session knowledge extracted to L2 for namespace '{self.namespace}'")


# ─── Global Memory Bus ────────────────────────────────────────────────────────
# All agents share a single global memory bus instance per namespace
_memory_clients: Dict[str, OpenVikingClient] = {}


def get_memory_client(namespace: str) -> OpenVikingClient:
    """Get or create a memory client for the given namespace."""
    if namespace not in _memory_clients:
        _memory_clients[namespace] = OpenVikingClient(namespace=namespace)
    return _memory_clients[namespace]
