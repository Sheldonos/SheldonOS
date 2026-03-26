"""
SheldonOS — Research & Exploit Engine
Integrates PentAGI (autonomous pentesting), Heretic (model liberation),
and the Perplexity Agent API (deep web research) for asymmetric value generation.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.research")


# ─── Perplexity Agent API Client ──────────────────────────────────────────────
class PerplexityResearchClient:
    """
    Client for the Perplexity Agent API.
    Used by all agents for deep, multi-source web research.
    This replaces manual headless browser orchestration.

    Docs: https://docs.perplexity.ai/docs/agent-api/quickstart
    """

    API_URL = "https://api.perplexity.ai"
    API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

    async def research(self, query: str, focus: str = "internet",
                       return_citations: bool = True) -> Dict[str, Any]:
        """
        Conduct deep web research using the Perplexity Agent API.
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
        except Exception as e:
            logger.error(f"Perplexity research failed: {e}")
        return {"answer": "", "citations": [], "error": str(e) if 'e' in dir() else "unknown"}

    async def monitor_stream(self, topics: List[str]) -> List[Dict[str, Any]]:
        """
        Monitor multiple topics simultaneously for the Epsilon Scout daemon.
        Returns a list of signals with relevance scores.
        """
        signals = []
        for topic in topics:
            result = await self.research(
                query=f"Latest developments and opportunities related to: {topic}. "
                      f"Focus on actionable signals, new projects, and market movements.",
                focus="internet",
            )
            if result.get("answer"):
                signals.append({
                    "topic": topic,
                    "summary": result["answer"][:500],
                    "citations": result.get("citations", [])[:3],
                    "timestamp": datetime.utcnow().isoformat(),
                })
        return signals


# ─── PentAGI Client ───────────────────────────────────────────────────────────
@dataclass
class PentestTarget:
    """A bug bounty target with authorized scope."""
    target_id: str
    domain: str
    program_name: str
    program_url: str
    authorized_scope: List[str]  # e.g., ["*.example.com", "api.example.com"]
    excluded_scope: List[str]
    max_severity: str = "critical"  # The highest severity to test for
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class VulnerabilityFinding:
    """A discovered vulnerability ready for bug bounty submission."""
    finding_id: str
    target_id: str
    title: str
    vulnerability_class: str  # OWASP category
    cvss_score: float
    severity: str  # critical | high | medium | low | informational
    description: str
    proof_of_concept: str
    affected_endpoint: str
    remediation: str
    discovered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class PentAGIClient:
    """
    Client for the PentAGI autonomous penetration testing engine.
    All testing is conducted within NemoClaw's sandbox.
    Strictly respects authorized scope.
    """

    BASE_URL = os.getenv("PENTAGI_API_URL", "http://localhost:8769")

    async def start_assessment(self, target: PentestTarget) -> Optional[str]:
        """Start an autonomous security assessment for a target."""
        logger.info(f"[PentAGI] Starting assessment for {target.domain} ({target.program_name})")

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
                    return [VulnerabilityFinding(**f) for f in findings_data]
        except Exception as e:
            logger.error(f"[PentAGI] Failed to get findings: {e}")
        return []

    def estimate_bounty(self, finding: VulnerabilityFinding) -> float:
        """Estimate the expected bug bounty payout for a finding."""
        bounty_ranges = {
            "critical": 10000.0,
            "high": 3000.0,
            "medium": 500.0,
            "low": 100.0,
            "informational": 0.0,
        }
        return bounty_ranges.get(finding.severity, 0.0)


# ─── Heretic Model Liberation ─────────────────────────────────────────────────
class HereticClient:
    """
    Client for the Heretic model liberation tool.
    Temporarily removes safety alignment from local models for authorized research tasks.
    IMPORTANT: Only used for PentAGI security research and AutoRA scientific discovery.
    All outputs are sandboxed within NemoClaw.
    """

    HERETIC_CLI = os.getenv("HERETIC_CLI_PATH", "/usr/local/bin/heretic")

    def decensor_model(self, model_path: str, output_path: str,
                       task_context: str = "security_research") -> bool:
        """
        Generate a temporary decensored model for a specific research task.
        The decensored model is scoped to the NemoClaw sandbox and deleted after use.
        """
        import subprocess
        logger.warning(
            f"[Heretic] Generating decensored model for task: {task_context}. "
            f"This model will be deleted after use."
        )
        try:
            result = subprocess.run(
                [self.HERETIC_CLI, "decensor", "--model", model_path, "--output", output_path,
                 "--task", task_context, "--sandbox", "nemoclaw"],
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode == 0:
                logger.info(f"[Heretic] Decensored model generated at {output_path}")
                return True
            else:
                logger.error(f"[Heretic] Decensor failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"[Heretic] Error: {e}")
            return False

    def cleanup_model(self, model_path: str):
        """Delete the decensored model after use."""
        import os as _os
        try:
            _os.remove(model_path)
            logger.info(f"[Heretic] Cleaned up decensored model: {model_path}")
        except Exception as e:
            logger.warning(f"[Heretic] Cleanup failed: {e}")


# ─── Manus.im External Execution Client ──────────────────────────────────────
class ManusClient:
    """
    Client for delegating complex browser-based tasks to Manus.im.
    Used when the Perplexity Agent API cannot handle a task (e.g., multi-step form submission,
    dynamic web app interaction, or authenticated session management).
    """

    API_URL = os.getenv("MANUS_API_URL", "https://api.manus.im")
    API_KEY = os.getenv("MANUS_API_KEY", "")

    async def execute_browser_task(self, task_description: str,
                                    url: str = None) -> Dict[str, Any]:
        """Delegate a browser-based task to Manus.im for execution."""
        if not self.API_KEY:
            logger.warning("MANUS_API_KEY not set — external execution unavailable")
            return {"status": "unavailable", "error": "API key not configured"}

        logger.info(f"[Manus] Delegating browser task: {task_description[:60]}")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.API_URL}/v1/tasks",
                    headers={"Authorization": f"Bearer {self.API_KEY}"},
                    json={"task": task_description, "url": url, "timeout": 300},
                    timeout=310.0,
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.error(f"[Manus] Task execution failed: {e}")
        return {"status": "failed", "error": str(e) if 'e' in dir() else "unknown"}
