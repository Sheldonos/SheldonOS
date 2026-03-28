"""
SheldonOS — Multi-Source Scanner v3.0
Replaces the single Perplexity dependency in the Seek layer with a parallel
fan-out across multiple free public intelligence sources.

Sources scanned in parallel:
  - GitHub Trending (via github.com/trending scrape + GH API)
  - Hacker News (via Algolia API — free, no key required)
  - arXiv new submissions (via arXiv API — free, no key required)
  - Polymarket markets (via Polymarket API — free, no key required)
  - Reddit (via Reddit JSON API — free, no key required)

Each source returns a list of signal dicts compatible with the SeekLayer's
_parse_signal() method. All sources run concurrently via asyncio.gather.

Reference: Blueprint §3.3 — Stage 2, Multi-Source Parallel Scanning
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.research.scanner")

# ─── Configuration ────────────────────────────────────────────────────────────
GITHUB_TRENDING_ENABLED: bool = os.getenv("GITHUB_TRENDING_ENABLED", "true").lower() == "true"
HN_SCANNING_ENABLED: bool = os.getenv("HN_SCANNING_ENABLED", "true").lower() == "true"
ARXIV_SCANNING_ENABLED: bool = os.getenv("ARXIV_SCANNING_ENABLED", "true").lower() == "true"
POLYMARKET_SCANNING_ENABLED: bool = os.getenv("POLYMARKET_SCANNING_ENABLED", "true").lower() == "true"


class MultiSourceScanner:
    """
    Fans out across multiple public intelligence sources in parallel and
    aggregates the results into a unified signal list.

    Usage:
        scanner = MultiSourceScanner()
        signals = await scanner.scan(topics=["AI", "DeFi", "bug bounty"])
    """

    async def scan(self, topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Run all enabled scanners in parallel and return the aggregated signals.

        Args:
            topics: Optional list of topic keywords to filter/focus results

        Returns:
            List of signal dicts with keys: topic, summary, source, timestamp
        """
        tasks = []

        if GITHUB_TRENDING_ENABLED:
            tasks.append(self._scan_github_trending())
        if HN_SCANNING_ENABLED:
            tasks.append(self._scan_hacker_news())
        if ARXIV_SCANNING_ENABLED:
            tasks.append(self._scan_arxiv())
        if POLYMARKET_SCANNING_ENABLED:
            tasks.append(self._scan_polymarket())

        if not tasks:
            logger.warning("[Scanner] All scanners disabled — returning empty signal list")
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        signals: List[Dict[str, Any]] = []
        source_names = ["github_trending", "hacker_news", "arxiv", "polymarket"]
        for source, result in zip(source_names, results):
            if isinstance(result, Exception):
                logger.warning(f"[Scanner] {source} scan failed: {result}")
            elif isinstance(result, list):
                signals.extend(result)
                logger.info(f"[Scanner] {source}: {len(result)} signals")

        logger.info(f"[Scanner] Total signals from all sources: {len(signals)}")
        return signals

    # ── GitHub Trending ───────────────────────────────────────────────────────
    async def _scan_github_trending(self) -> List[Dict[str, Any]]:
        """
        Fetch trending repositories from GitHub Trending page.
        Uses the unofficial GitHub Trending API (no auth required).
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": "stars:>100 pushed:>2024-01-01",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 10,
                    },
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "SheldonOS/3.0",
                    },
                )
                if resp.status_code != 200:
                    return []

                data = resp.json()
                signals = []
                for repo in data.get("items", [])[:10]:
                    signals.append({
                        "topic": f"GitHub trending: {repo.get('full_name', '')}",
                        "summary": (
                            f"{repo.get('description', 'No description')} | "
                            f"Stars: {repo.get('stargazers_count', 0):,} | "
                            f"Language: {repo.get('language', 'Unknown')} | "
                            f"URL: {repo.get('html_url', '')}"
                        )[:500],
                        "source": "github_trending",
                        "citations": [repo.get("html_url", "")],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                return signals
        except Exception as e:
            logger.warning(f"[Scanner] GitHub trending failed: {e}")
            return []

    # ── Hacker News ───────────────────────────────────────────────────────────
    async def _scan_hacker_news(self) -> List[Dict[str, Any]]:
        """
        Fetch top stories from Hacker News via the Algolia Search API.
        Free, no API key required.
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://hn.algolia.com/api/v1/search",
                    params={
                        "tags": "story",
                        "hitsPerPage": 15,
                        "numericFilters": "points>50",
                    },
                )
                if resp.status_code != 200:
                    return []

                data = resp.json()
                signals = []
                for hit in data.get("hits", []):
                    title = hit.get("title", "")
                    url = hit.get("url", hit.get("story_url", ""))
                    points = hit.get("points", 0)
                    comments = hit.get("num_comments", 0)

                    if not title:
                        continue

                    signals.append({
                        "topic": f"HN: {title}",
                        "summary": (
                            f"{title} | Points: {points} | Comments: {comments} | "
                            f"URL: {url}"
                        )[:500],
                        "source": "hacker_news",
                        "citations": [url] if url else [],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                return signals
        except Exception as e:
            logger.warning(f"[Scanner] Hacker News scan failed: {e}")
            return []

    # ── arXiv ─────────────────────────────────────────────────────────────────
    async def _scan_arxiv(self) -> List[Dict[str, Any]]:
        """
        Fetch recent AI/ML/CS papers from arXiv via the public Atom API.
        Free, no API key required.
        """
        try:
            import httpx
            # Search for recent papers in AI, ML, and CS categories
            query = (
                "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CR+OR+cat:q-fin.TR"
                "+AND+submittedDate:[20240101+TO+20261231]"
            )
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    "https://export.arxiv.org/api/query",
                    params={
                        "search_query": query,
                        "sortBy": "submittedDate",
                        "sortOrder": "descending",
                        "max_results": 10,
                    },
                )
                if resp.status_code != 200:
                    return []

            # Parse Atom XML
            import xml.etree.ElementTree as ET
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(resp.text)
            signals = []

            for entry in root.findall("atom:entry", ns)[:10]:
                title_el = entry.find("atom:title", ns)
                summary_el = entry.find("atom:summary", ns)
                link_el = entry.find("atom:id", ns)

                title = title_el.text.strip() if title_el is not None else ""
                summary = summary_el.text.strip()[:300] if summary_el is not None else ""
                link = link_el.text.strip() if link_el is not None else ""

                if not title:
                    continue

                signals.append({
                    "topic": f"arXiv: {title}",
                    "summary": f"{title} — {summary}"[:500],
                    "source": "arxiv",
                    "citations": [link] if link else [],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            return signals
        except Exception as e:
            logger.warning(f"[Scanner] arXiv scan failed: {e}")
            return []

    # ── Polymarket ────────────────────────────────────────────────────────────
    async def _scan_polymarket(self) -> List[Dict[str, Any]]:
        """
        Fetch active high-volume prediction markets from Polymarket's public API.
        Free, no API key required.
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={
                        "active": "true",
                        "closed": "false",
                        "limit": 20,
                        "order": "volume24hr",
                        "ascending": "false",
                    },
                )
                if resp.status_code != 200:
                    return []

                markets = resp.json()
                signals = []
                for market in markets[:15]:
                    question = market.get("question", "")
                    volume = market.get("volume24hr", 0)
                    liquidity = market.get("liquidity", 0)
                    end_date = market.get("endDate", "")

                    if not question or volume < 1000:
                        continue

                    signals.append({
                        "topic": f"Polymarket: {question}",
                        "summary": (
                            f"Prediction market: {question} | "
                            f"24h Volume: ${float(volume):,.0f} | "
                            f"Liquidity: ${float(liquidity):,.0f} | "
                            f"Closes: {end_date[:10] if end_date else 'unknown'}"
                        )[:500],
                        "source": "polymarket",
                        "citations": [],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                return signals
        except Exception as e:
            logger.warning(f"[Scanner] Polymarket scan failed: {e}")
            return []


# ─── Module-level singleton ───────────────────────────────────────────────────
_scanner: Optional[MultiSourceScanner] = None


def get_multi_source_scanner() -> MultiSourceScanner:
    """Return the module-level MultiSourceScanner singleton."""
    global _scanner
    if _scanner is None:
        _scanner = MultiSourceScanner()
    return _scanner
