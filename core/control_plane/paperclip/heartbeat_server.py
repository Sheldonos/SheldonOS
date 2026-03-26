"""
SheldonOS — Paperclip Heartbeat Server
Manages the org chart, dispatches heartbeats to agents, and enforces budget policy.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("sheldon.paperclip")

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SheldonOS — Paperclip Control Plane",
    description="Master orchestrator for the SheldonOS autonomous entity",
    version="1.0.0",
)

# ─── Models ──────────────────────────────────────────────────────────────────
class HeartbeatPayload(BaseModel):
    company_id: str
    team_id: str
    agent_id: str
    task_id: Optional[str] = None
    tokens_used: int = 0
    status: str = "idle"  # idle | running | complete | failed
    result: Optional[Dict[str, Any]] = None


class BudgetStatus(BaseModel):
    company_id: str
    tokens_remaining: int
    tokens_used_today: int
    budget_pct_remaining: float
    throttled: bool


# ─── In-Memory State (replace with PostgreSQL in production) ─────────────────
_org_config: Dict = {}
_budget_ledger: Dict[str, Dict] = {}
_agent_registry: Dict[str, Dict] = {}
_task_queue: asyncio.Queue = asyncio.Queue()


def load_org_config(path: str = "org_config.yaml") -> Dict:
    """Load the Paperclip org configuration from YAML."""
    with open(path) as f:
        config = yaml.safe_load(f)
    logger.info(f"Loaded org config: {config['org']['name']} v{config['org']['version']}")
    return config


def initialize_budget_ledger(config: Dict) -> Dict[str, Dict]:
    """Initialize the budget ledger from the org config."""
    ledger = {}
    monthly_limit = config["budget"]["monthly_token_limit"]
    for company in config["companies"]:
        cid = company["id"]
        company_budget = company.get("monthly_budget_tokens", monthly_limit // len(config["companies"]))
        ledger[cid] = {
            "monthly_limit": company_budget,
            "tokens_used_month": 0,
            "tokens_used_today": 0,
            "last_reset": datetime.utcnow().isoformat(),
            "throttled": False,
        }
    logger.info(f"Budget ledger initialized for {len(ledger)} companies")
    return ledger


# ─── API Endpoints ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    global _org_config, _budget_ledger
    try:
        _org_config = load_org_config()
        _budget_ledger = initialize_budget_ledger(_org_config)
        asyncio.create_task(heartbeat_dispatcher())
        asyncio.create_task(budget_rebalancer())
        logger.info("SheldonOS Paperclip Control Plane is online.")
    except FileNotFoundError:
        logger.warning("org_config.yaml not found — running in demo mode")


@app.post("/api/heartbeat")
async def receive_heartbeat(payload: HeartbeatPayload):
    """Receive a heartbeat from an agent and update the budget ledger."""
    cid = payload.company_id
    if cid not in _budget_ledger:
        raise HTTPException(status_code=404, detail=f"Company '{cid}' not found in ledger")

    ledger = _budget_ledger[cid]

    # Deduct tokens
    ledger["tokens_used_month"] += payload.tokens_used
    ledger["tokens_used_today"] += payload.tokens_used

    # Check budget
    remaining = ledger["monthly_limit"] - ledger["tokens_used_month"]
    pct_remaining = (remaining / ledger["monthly_limit"]) * 100

    if pct_remaining <= 0:
        ledger["throttled"] = True
        logger.warning(f"[{cid}] Budget exhausted — agent {payload.agent_id} THROTTLED")
        return {"status": "throttled", "tokens_remaining": 0}

    if pct_remaining <= 15:  # Emergency reserve
        logger.warning(f"[{cid}] Budget at {pct_remaining:.1f}% — approaching reserve threshold")

    logger.info(
        f"[{cid}] Agent {payload.agent_id} heartbeat | "
        f"tokens_used={payload.tokens_used} | remaining={remaining:,} | status={payload.status}"
    )

    # If task completed, log to Cognee (via event bus)
    if payload.status == "complete" and payload.result:
        await _emit_to_cognee(cid, payload.agent_id, payload.result)

    return {
        "status": "ok",
        "tokens_remaining": remaining,
        "budget_pct_remaining": round(pct_remaining, 2),
        "throttled": ledger["throttled"],
    }


@app.get("/api/budget/{company_id}")
async def get_budget_status(company_id: str) -> BudgetStatus:
    """Get the current budget status for a company."""
    if company_id not in _budget_ledger:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")
    ledger = _budget_ledger[company_id]
    remaining = ledger["monthly_limit"] - ledger["tokens_used_month"]
    return BudgetStatus(
        company_id=company_id,
        tokens_remaining=remaining,
        tokens_used_today=ledger["tokens_used_today"],
        budget_pct_remaining=round((remaining / ledger["monthly_limit"]) * 100, 2),
        throttled=ledger["throttled"],
    )


@app.get("/api/org")
async def get_org_status():
    """Get the full org chart and budget status."""
    return {
        "org": _org_config.get("org", {}),
        "companies": [
            {
                "id": cid,
                "budget": _budget_ledger.get(cid, {}),
            }
            for cid in _budget_ledger
        ],
    }


@app.post("/api/spawn-team")
async def spawn_team(company_id: str, team_config: Dict[str, Any]):
    """Dynamically spawn a new agent team for a company (called by the Adapt layer)."""
    if company_id not in _budget_ledger:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")
    logger.info(f"[{company_id}] Spawning new team: {team_config.get('name', 'unnamed')}")
    # In production: persist to PostgreSQL and trigger OpenClaw to wake agents
    await _task_queue.put({"action": "spawn_team", "company_id": company_id, "config": team_config})
    return {"status": "queued", "team": team_config}


# ─── Background Tasks ─────────────────────────────────────────────────────────
async def heartbeat_dispatcher():
    """Continuously dispatch heartbeats to all active agents."""
    config = _org_config.get("heartbeat", {})
    interval = config.get("interval_seconds", 30)
    endpoint = config.get("endpoint", "http://localhost:3100/api/heartbeat")

    while True:
        await asyncio.sleep(interval)
        logger.debug("Heartbeat dispatcher tick")
        # In production: iterate over active agents and POST to their endpoints


async def budget_rebalancer():
    """Daily budget rebalancer — resets daily counters and rebalances across companies."""
    while True:
        await asyncio.sleep(86400)  # 24 hours
        for cid, ledger in _budget_ledger.items():
            ledger["tokens_used_today"] = 0
            if ledger["throttled"] and ledger["tokens_used_month"] < ledger["monthly_limit"]:
                ledger["throttled"] = False
                logger.info(f"[{cid}] Budget throttle lifted after daily reset")
        logger.info("Budget rebalancer: daily counters reset")


async def _emit_to_cognee(company_id: str, agent_id: str, result: Dict):
    """Emit a completed task result to the Cognee knowledge graph."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8765/api/cognee/ingest",
                json={"company_id": company_id, "agent_id": agent_id, "data": result},
                timeout=5.0,
            )
    except Exception as e:
        logger.warning(f"Failed to emit to Cognee: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3100, log_level="info")
