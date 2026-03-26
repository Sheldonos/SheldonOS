"""
SheldonOS — Research & Exploit Engine v2.0
Integrates PentAGI (autonomous pentesting), Heretic (model liberation),
and the Perplexity Agent API (deep web research) for asymmetric value generation.

v2.0 Changes:
  - FIXED: Added search_topic() method so the orchestrator's parallel Seek can call it
    per-topic rather than the old sequential monitor_stream() loop.
  - FIXED: monitor_stream() now calls search_topic() in parallel via asyncio.gather.
  - FIXED: PentAGIClient.start_assessment() validates authorized_scope before submission
    to prevent out-of-scope testing.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.research")


# ─── Perplexity Agent API Client ──────────────────────────────────────────────
class PerplexityResearchClient:
    """
    Client for the Perplexity Agent API.
    Used by all agents for deep, multi-source web research.
    Docs: https://docs.perplexity.ai/docs/agent-api/quickstart
    """

    API_URL = "https://api.perplexity.ai"
    API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

    async def research(self, query: str, focus: str = "internet",
                       return_citations: bool = True) -> Dict[str, Any]:
        """
        Conduct deep web research using the Perplexity sonar-pro model.
        focus: internet | academic | news | finance
        """
        if not self.API_KEY:
            logger.warning("PERPLEXITY_API_KEY not set — research unavailable")
            return {"answer": "", "citations": [], "error": "API key not configured"}

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.API_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "sonar-pro",
                        "messages": [{"role": "user", "content": query}],
                        "search_domain_filter": [],
                        "return_citations": return_citations,
                        "search_recency_filter": "month",
                    },
                    timeout=60.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "answer": data["choices"][0]["message"]["content"],
                        "citations": data.get("citations", []),
                        "model": data.get("model", "sonar-pro"),
                    }
                else:
                    logger.warning(f"Perplexity API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Perplexity research failed: {e}")
            return {"answer": "", "citations": [], "error": str(e)}

        return {"answer": "", "citations": [], "error": "unknown"}

    async def search_topic(self, topic: str) -> List[Dict[str, Any]]:
        """
        FIXED v2.0: Per-topic search method called by the parallel Seek layer.
        Returns a list of signal dicts (may be empty if no useful result).
        This is the method the orchestrator's asyncio.gather calls per topic.
        """
        result = await self.research(
            query=(
                f"Latest developments and opportunities related to: {topic}. "
                f"Focus on actionable signals, new projects, and market movements."
            ),
            focus="internet",
        )
        if result.get("answer") and len(result["answer"]) >= 50:
            return [{
                "topic": topic,
                "summary": result["answer"][:500],
                "citations": result.get("citations", [])[:3],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }]
        return []

    async def monitor_stream(self, topics: List[str]) -> List[Dict[str, Any]]:
        """
        FIXED v2.0: Now runs all topic searches in parallel via asyncio.gather.
        Previously this was a sequential for-loop — at 10 topics × 60s timeout
        it could take up to 10 minutes per cycle. Now all topics run concurrently.
        """
        results = await asyncio.gather(
            *[self.search_topic(topic) for topic in topics],
            return_exceptions=True,
        )
        signals = []
        for topic, result in zip(topics, results):
            if isinstance(result, Exception):
                logger.warning(f"[Research] Topic '{topic[:40]}' failed: {result}")
            elif isinstance(result, list):
                signals.extend(result)
        return signals


# ─── PentAGI Client ───────────────────────────────────────────────────────────
@dataclass
class PentestTarget:
    """A bug bounty target with authorized scope."""
    target_id: str
    domain: str
    program_name: str
    program_url: str
    authorized_scope: List[str]   # e.g., ["*.example.com", "api.example.com"]
    excluded_scope: List[str]
    max_severity: str = "critical"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class VulnerabilityFinding:
    """A discovered vulnerability ready for bug bounty submission."""
    finding_id: str
    target_id: str
    title: str
    vulnerability_class: str  # OWASP category
    cvss_score: float
    severity: str             # critical | high | medium | low | informational
    description: str
    proof_of_concept: str
    affected_endpoint: str
    remediation: str
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PentAGIClient:
    """
    Client for the PentAGI autonomous penetration testing engine.
    All testing is conducted within NemoClaw's sandbox.
    FIXED v2.0: Validates authorized_scope before submission to prevent out-of-scope testing.
    """

    BASE_URL = os.getenv("PENTAGI_API_URL", "http://localhost:8769")

    def _validate_scope(self, target: PentestTarget) -> None:
        """
        FIXED v2.0: Enforce that authorized_scope is non-empty and does not contain
        wildcard-only entries that could authorize unrestricted scanning.
        Raises ValueError if scope is invalid.
        """
        if not target.authorized_scope:
            raise ValueError(
                f"PentAGI: authorized_scope is empty for target {target.domain}. "
                "Testing cannot proceed without an explicit scope definition."
            )
        for entry in target.authorized_scope:
            if entry.strip() in ("*", "*.*", "*.*.*"):
                raise ValueError(
                    f"PentAGI: Wildcard-only scope entry '{entry}' is not permitted. "
                    "Provide explicit domain patterns (e.g., '*.example.com')."
                )

    async def start_assessment(self, target: PentestTarget) -> Optional[str]:
        """Start an autonomous security assessment for a target."""
        # FIXED v2.0: scope validation before any network call
        self._validate_scope(target)

        logger.info(f"[PentAGI] Starting assessment for {target.domain} ({target.program_name})")
        logger.info(f"[PentAGI] Authorized scope: {target.authorized_scope}")

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/api/assessment/start",
                    json={
                        "target_id": target.target_id,
                        "domain": target.domain,
                        "authorized_scope": target.authorized_scope,
                        "excluded_scope": target.excluded_scope,
                        "max_severity": target.max_severity,
                    },
                    timeout=30.0,
                )
                if resp.status_code == 200:
                    return resp.json().get("assessment_id")
                else:
                    logger.error(f"[PentAGI] start_assessment returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"[PentAGI] Failed to start assessment: {e}")
        return None

    async def get_findings(self, assessment_id: str) -> List[VulnerabilityFinding]:
        """Retrieve all findings from a completed assessment."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.BASE_URL}/api/assessment/{assessment_id}/findings",
                    timeout=30.0,
                )
                if resp.status_code == 200:
                    findings_data = resp.json().get("findings", [])
                    return [
                        VulnerabilityFinding(
                            finding_id=f.get("id", ""),
                            target_id=assessment_id,
                            title=f.get("title", ""),
                            vulnerability_class=f.get("class", "Unknown"),
                            cvss_score=float(f.get("cvss_score", 0.0)),
                            severity=f.get("severity", "informational"),
                            description=f.get("description", ""),
                            proof_of_concept=f.get("proof_of_concept", ""),
                            affected_endpoint=f.get("endpoint", ""),
                            remediation=f.get("remediation", ""),
                        )
                        for f in findings_data
                    ]
        except Exception as e:
            logger.error(f"[PentAGI] Failed to get findings: {e}")
        return []

    async def submit_bug_bounty_report(self, finding: VulnerabilityFinding,
                                       platform_api_url: str, api_key: str) -> Dict[str, Any]:
        """
        Submit a bug bounty report to the platform's API.
        Supports HackerOne, Bugcrowd, and Intigriti report formats.
        """
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{platform_api_url}/reports",
                    headers={"Authorization": f"Token {api_key}"},
                    json={
                        "title": finding.title,
                        "vulnerability_information": (
                            f"## Description\n{finding.description}\n\n"
                            f"## Proof of Concept\n{finding.proof_of_concept}\n\n"
                            f"## Impact\nCVSS Score: {finding.cvss_score} ({finding.severity})\n\n"
                            f"## Remediation\n{finding.remediation}"
                        ),
                        "severity": finding.severity,
                        "weakness": {"name": finding.vulnerability_class},
                    },
                    timeout=30.0,
                )
                return resp.json()
        except Exception as e:
            logger.error(f"[PentAGI] Bug bounty submission failed: {e}")
            return {"error": str(e)}
