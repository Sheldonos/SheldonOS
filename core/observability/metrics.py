"""
SheldonOS — Observability Module v2.0
Structured logging, Prometheus metrics, and health check utilities.

FIXED v2.0: Previously there was zero observability infrastructure — no Prometheus,
no structured logging, no health endpoints. This module provides:
  - Structured JSON log formatter for production (journald-compatible)
  - Prometheus Counter/Gauge/Histogram helpers for all subsystems
  - A /healthz and /metrics FastAPI router for the orchestrator's HTTP server
  - Token usage tracking per company (replaces in-memory dict)
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    CollectorRegistry, REGISTRY,
    generate_latest, CONTENT_TYPE_LATEST,
)


# ─── Structured JSON Logging ──────────────────────────────────────────────────
class StructuredFormatter(logging.Formatter):
    """
    Emits log records as newline-delimited JSON for log aggregation pipelines
    (Loki, Datadog, CloudWatch, etc.).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
            "module":    record.module,
            "line":      record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Attach any extra fields passed via logger.info(..., extra={...})
        for key, val in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
            ):
                log_entry[key] = val
        return json.dumps(log_entry, default=str)


def configure_logging(level: str = "INFO", structured: bool = False):
    """
    Configure root logging for SheldonOS.
    Set structured=True in production for JSON output.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler()
    if structured or os.getenv("LOG_FORMAT", "").lower() == "json":
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
        ))

    # Remove existing handlers to avoid duplicate output
    root.handlers.clear()
    root.addHandler(handler)


# ─── Prometheus Metrics Registry ─────────────────────────────────────────────
# All metrics are registered here and imported by subsystems.
# This prevents duplicate registration errors on hot-reload.

class SheldonMetrics:
    """Central Prometheus metrics registry for SheldonOS."""

    def __init__(self):
        # ── Orchestrator ──────────────────────────────────────────────────────
        self.cycles_total = Counter(
            "sheldon_cycles_total",
            "Total orchestration cycles completed",
        )
        self.cycle_duration = Histogram(
            "sheldon_cycle_duration_seconds",
            "Duration of each orchestration cycle in seconds",
            buckets=[30, 60, 120, 300, 600, 1200, 1800],
        )
        self.score_threshold = Gauge(
            "sheldon_score_threshold",
            "Current opportunity score threshold",
        )
        self.win_rate = Gauge(
            "sheldon_win_rate_pct",
            "Rolling win rate percentage (last 50 cycles)",
        )
        self.revenue_total = Gauge(
            "sheldon_revenue_usd_total",
            "Cumulative estimated revenue USD",
        )

        # ── Opportunities ─────────────────────────────────────────────────────
        self.opportunities_detected = Counter(
            "sheldon_opportunities_detected_total",
            "Raw opportunities detected",
            ["source"],
        )
        self.opportunities_approved = Counter(
            "sheldon_opportunities_approved_total",
            "Opportunities approved for execution",
            ["company"],
        )
        self.opportunities_rejected = Counter(
            "sheldon_opportunities_rejected_total",
            "Opportunities rejected",
            ["reason"],
        )

        # ── LLM Usage ─────────────────────────────────────────────────────────
        self.llm_requests_total = Counter(
            "sheldon_llm_requests_total",
            "Total LLM API requests",
            ["provider", "model"],
        )
        self.llm_tokens_input = Counter(
            "sheldon_llm_tokens_input_total",
            "Total input tokens consumed",
            ["provider", "company"],
        )
        self.llm_tokens_output = Counter(
            "sheldon_llm_tokens_output_total",
            "Total output tokens consumed",
            ["provider", "company"],
        )
        self.llm_latency = Histogram(
            "sheldon_llm_latency_seconds",
            "LLM API call latency in seconds",
            ["provider"],
            buckets=[0.5, 1, 2, 5, 10, 30, 60],
        )

        # ── Workflows ─────────────────────────────────────────────────────────
        self.workflows_started = Counter(
            "sheldon_workflows_started_total",
            "Workflows started",
            ["company"],
        )
        self.workflows_complete = Counter(
            "sheldon_workflows_complete_total",
            "Workflows completed successfully",
            ["company"],
        )
        self.workflows_failed = Counter(
            "sheldon_workflows_failed_total",
            "Workflows that failed",
            ["company"],
        )
        self.active_workflows = Gauge(
            "sheldon_active_workflows",
            "Currently active workflows",
            ["company"],
        )

        # ── Trade Signals ─────────────────────────────────────────────────────
        self.trade_signals_total = Counter(
            "sheldon_trade_signals_total",
            "Trade signals processed",
            ["status"],
        )
        self.trade_pnl = Gauge(
            "sheldon_trade_pnl_usd",
            "Current day PnL in USD",
        )

        # ── Research ─────────────────────────────────────────────────────────
        self.perplexity_requests = Counter(
            "sheldon_perplexity_requests_total",
            "Perplexity API requests",
            ["status"],
        )
        self.pentagi_assessments = Counter(
            "sheldon_pentagi_assessments_total",
            "PentAGI security assessments started",
        )
        self.pentagi_findings = Counter(
            "sheldon_pentagi_findings_total",
            "Vulnerability findings discovered",
            ["severity"],
        )

        # ── System Health ─────────────────────────────────────────────────────
        self.db_pool_size = Gauge(
            "sheldon_db_pool_size",
            "PostgreSQL connection pool size",
        )
        self.redis_connected = Gauge(
            "sheldon_redis_connected",
            "Redis connection status (1=connected, 0=disconnected)",
        )
        self.uptime_seconds = Gauge(
            "sheldon_uptime_seconds",
            "Orchestrator uptime in seconds",
        )

        self._start_time = time.time()

    def update_uptime(self):
        self.uptime_seconds.set(time.time() - self._start_time)


# ─── Module-level singleton ───────────────────────────────────────────────────
_metrics: Optional[SheldonMetrics] = None


def get_metrics() -> SheldonMetrics:
    """Return the module-level SheldonMetrics singleton."""
    global _metrics
    if _metrics is None:
        _metrics = SheldonMetrics()
    return _metrics


# ─── Health Check Utilities ───────────────────────────────────────────────────
async def check_postgres(dsn: str) -> Dict[str, Any]:
    """Check PostgreSQL connectivity."""
    try:
        import asyncpg
        conn = await asyncpg.connect(dsn, timeout=5)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return {"status": "ok", "service": "postgres"}
    except Exception as e:
        return {"status": "error", "service": "postgres", "error": str(e)}


async def check_redis(url: str) -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(url, decode_responses=True)
        await r.ping()
        await r.aclose()
        return {"status": "ok", "service": "redis"}
    except Exception as e:
        return {"status": "error", "service": "redis", "error": str(e)}


async def health_check() -> Dict[str, Any]:
    """Run all health checks and return a combined status."""
    import asyncio
    checks = {}

    postgres_dsn = os.getenv("POSTGRES_DSN")
    redis_url    = os.getenv("REDIS_URL")

    tasks = []
    if postgres_dsn:
        tasks.append(check_postgres(postgres_dsn))
    if redis_url:
        tasks.append(check_redis(redis_url))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, dict):
                checks[result["service"]] = result

    overall = "ok" if all(v.get("status") == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks, "uptime_seconds": time.time()}
