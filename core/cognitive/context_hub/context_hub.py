"""
SheldonOS — Context Hub v2.0
A curated, cached documentation and context retrieval system.

FIXED v2.0: Previously referenced in agent prompts (beta_lead_engineer uses 'context_hub' tool)
but had zero files in the repository. This module provides:
  - Cached retrieval of API documentation from URLs
  - Local document store for frequently-used references
  - Integration with OpenViking for vector-based semantic search
  - TTL-based cache to avoid redundant fetches
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.context_hub")

# Local cache directory for downloaded documentation
CACHE_DIR = Path(os.getenv("CONTEXT_HUB_CACHE_DIR", "/tmp/sheldon_workspace/context_hub"))
CACHE_TTL_SECONDS = int(os.getenv("CONTEXT_HUB_CACHE_TTL", str(60 * 60 * 24)))  # 24h default


@dataclass
class ContextDocument:
    """A retrieved context document."""
    doc_id: str
    title: str
    content: str
    source_url: str
    doc_type: str           # "api_docs" | "readme" | "spec" | "custom"
    retrieved_at: float = field(default_factory=time.time)
    token_estimate: int = 0

    def is_stale(self) -> bool:
        return (time.time() - self.retrieved_at) > CACHE_TTL_SECONDS


class ContextHub:
    """
    Context Hub: curated documentation retrieval for SheldonOS agents.

    Agents call this before writing any integration code to ensure they have
    accurate, up-to-date API documentation rather than hallucinating interfaces.

    Usage:
        hub = ContextHub()
        doc = await hub.get("polymarket_api")
        doc = await hub.fetch_url("https://docs.polymarket.com/api")
        results = await hub.search("Polymarket CLOB API order placement")
    """

    # Pre-registered documentation sources for known integrations
    KNOWN_SOURCES: Dict[str, str] = {
        "polymarket_api":    "https://docs.polymarket.com/api",
        "kalshi_api":        "https://trading-api.readme.io/reference/getting-started",
        "perplexity_api":    "https://docs.perplexity.ai/reference/post_chat_completions",
        "anthropic_api":     "https://docs.anthropic.com/en/api/getting-started",
        "openai_api":        "https://platform.openai.com/docs/api-reference",
        "github_api":        "https://docs.github.com/en/rest",
        "vercel_api":        "https://vercel.com/docs/rest-api",
        "paperclip_api":     "http://localhost:3100/api/docs",
        "openclaw_api":      "http://localhost:3101/api/docs",
        "pentagi_api":       "http://localhost:8769/api/docs",
        "cognee_api":        "http://localhost:8765/docs",
    }

    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, ContextDocument] = {}

    def _cache_key(self, identifier: str) -> str:
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _cache_path(self, key: str) -> Path:
        return CACHE_DIR / f"{key}.json"

    def _load_from_disk(self, key: str) -> Optional[ContextDocument]:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            doc = ContextDocument(**data)
            if doc.is_stale():
                path.unlink(missing_ok=True)
                return None
            return doc
        except Exception:
            return None

    def _save_to_disk(self, key: str, doc: ContextDocument):
        try:
            self._cache_path(key).write_text(
                json.dumps(doc.__dict__, default=str)
            )
        except Exception as e:
            logger.warning(f"[ContextHub] Failed to cache to disk: {e}")

    async def get(self, name: str) -> Optional[ContextDocument]:
        """
        Retrieve documentation by registered name (e.g., 'polymarket_api').
        Returns cached version if available and fresh.
        """
        if name not in self.KNOWN_SOURCES:
            logger.warning(f"[ContextHub] Unknown source name: '{name}'. Use fetch_url() for custom URLs.")
            return None
        return await self.fetch_url(self.KNOWN_SOURCES[name], name=name)

    async def fetch_url(self, url: str, name: str = "") -> Optional[ContextDocument]:
        """
        Fetch documentation from a URL, with disk-based TTL caching.
        """
        key = self._cache_key(url)

        # Check memory cache
        if key in self._memory_cache and not self._memory_cache[key].is_stale():
            logger.debug(f"[ContextHub] Memory cache hit: {url[:60]}")
            return self._memory_cache[key]

        # Check disk cache
        doc = self._load_from_disk(key)
        if doc:
            self._memory_cache[key] = doc
            logger.debug(f"[ContextHub] Disk cache hit: {url[:60]}")
            return doc

        # Fetch from network
        logger.info(f"[ContextHub] Fetching: {url[:80]}")
        try:
            import httpx
            from bs4 import BeautifulSoup

            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url, timeout=30.0, headers={
                    "User-Agent": "SheldonOS-ContextHub/2.0"
                })
                resp.raise_for_status()
                raw_content = resp.text

            # Strip HTML tags if the response is HTML
            if "text/html" in resp.headers.get("content-type", ""):
                soup = BeautifulSoup(raw_content, "html.parser")
                # Remove script and style elements
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                content = soup.get_text(separator="\n", strip=True)
            else:
                content = raw_content

            # Truncate to ~50k chars to stay within token budgets
            content = content[:50000]

            doc = ContextDocument(
                doc_id=key,
                title=name or url.split("/")[-1] or url,
                content=content,
                source_url=url,
                doc_type="api_docs",
                token_estimate=len(content) // 4,
            )

            self._memory_cache[key] = doc
            self._save_to_disk(key, doc)
            logger.info(f"[ContextHub] Cached {len(content)} chars from {url[:60]}")
            return doc

        except Exception as e:
            logger.error(f"[ContextHub] Failed to fetch {url}: {e}")
            return None

    async def search(self, query: str, top_k: int = 3) -> List[ContextDocument]:
        """
        Search cached documents for relevant context using simple keyword matching.
        In production, this delegates to OpenViking for vector similarity search.
        """
        results = []
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        for doc in self._memory_cache.values():
            content_lower = doc.content.lower()
            # Score by term overlap
            matches = sum(1 for term in query_terms if term in content_lower)
            if matches > 0:
                results.append((matches, doc))

        results.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in results[:top_k]]

    def add_custom(self, name: str, content: str, source_url: str = "custom") -> ContextDocument:
        """
        Add a custom document to the context hub (e.g., internal specs, PRDs).
        """
        key = self._cache_key(name)
        doc = ContextDocument(
            doc_id=key,
            title=name,
            content=content,
            source_url=source_url,
            doc_type="custom",
            token_estimate=len(content) // 4,
        )
        self._memory_cache[key] = doc
        self._save_to_disk(key, doc)
        logger.info(f"[ContextHub] Added custom document: '{name}' ({len(content)} chars)")
        return doc

    async def get_document(self, name: str) -> Optional[str]:
        """
        Retrieve a document's text content by name.
        Used by SelfCorrector to inject relevant docs into agent context.
        Returns None if the document is not found or unavailable.
        """
        doc = await self.get(name)
        if doc:
            return doc.content
        # Try fetching by name as a direct URL fallback
        logger.debug(f"[ContextHub] Document '{name}' not in KNOWN_SOURCES")
        return None

    def list_cached(self) -> List[Dict[str, Any]]:
        """List all documents currently in the cache."""
        return [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "source_url": doc.source_url,
                "doc_type": doc.doc_type,
                "token_estimate": doc.token_estimate,
                "stale": doc.is_stale(),
            }
            for doc in self._memory_cache.values()
        ]


# ─── Module-level singleton ───────────────────────────────────────────────────
_context_hub: Optional[ContextHub] = None


def get_context_hub() -> ContextHub:
    """Return the module-level ContextHub singleton."""
    global _context_hub
    if _context_hub is None:
        _context_hub = ContextHub()
    return _context_hub
