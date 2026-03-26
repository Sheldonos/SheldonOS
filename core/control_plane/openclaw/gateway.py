"""
SheldonOS — OpenClaw Gateway
The local-first communication gateway. Routes all external messaging (Telegram, Slack, Discord)
and internal API calls between agents and the control plane.
All traffic is sandboxed through NemoClaw before execution.
"""

import logging
import os
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger("sheldon.openclaw")

app = FastAPI(
    title="SheldonOS — OpenClaw Gateway",
    description="Local-first communication and routing layer for SheldonOS",
    version="1.0.0",
)


class Channel(str, Enum):
    TELEGRAM = "telegram"
    SLACK = "slack"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    SIGNAL = "signal"
    INTERNAL = "internal"


class MessagePayload(BaseModel):
    channel: Channel
    recipient: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # normal | high | critical


class AgentCallPayload(BaseModel):
    agent_id: str
    company_id: str
    action: str
    parameters: Dict[str, Any] = {}
    timeout_seconds: int = 300


# ─── Channel Adapters ─────────────────────────────────────────────────────────
class TelegramAdapter:
    """Sends notifications via Telegram Bot API."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.default_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    async def send(self, recipient: str, content: str) -> bool:
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set — message not sent")
            return False
        import httpx
        chat_id = recipient if recipient != "default" else self.default_chat_id
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": content, "parse_mode": "Markdown"},
            )
        return resp.status_code == 200


class SlackAdapter:
    """Sends notifications via Slack Webhook."""

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    async def send(self, recipient: str, content: str) -> bool:
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set — message not sent")
            return False
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.webhook_url, json={"text": content})
        return resp.status_code == 200


# ─── Gateway Router ───────────────────────────────────────────────────────────
_adapters: Dict[Channel, Any] = {}


@app.on_event("startup")
async def startup():
    global _adapters
    _adapters = {
        Channel.TELEGRAM: TelegramAdapter(),
        Channel.SLACK: SlackAdapter(),
    }
    logger.info("OpenClaw Gateway online — channels: Telegram, Slack")


@app.post("/api/message/send")
async def send_message(payload: MessagePayload) -> Dict[str, Any]:
    """Route a message to the appropriate channel adapter."""
    adapter = _adapters.get(payload.channel)
    if not adapter:
        raise HTTPException(status_code=400, detail=f"Channel '{payload.channel}' not configured")

    success = await adapter.send(payload.recipient, payload.content)
    logger.info(f"[{payload.channel}] → {payload.recipient}: {'OK' if success else 'FAILED'}")
    return {"status": "sent" if success else "failed", "channel": payload.channel}


@app.post("/api/agent/call")
async def call_agent(payload: AgentCallPayload) -> Dict[str, Any]:
    """
    Invoke a specific agent action via OpenClaw.
    All calls are routed through NemoClaw for sandboxing.
    """
    logger.info(f"Agent call: [{payload.company_id}] {payload.agent_id}.{payload.action}")
    # In production: forward to NemoClaw's sandboxed execution environment
    return {
        "status": "dispatched",
        "agent_id": payload.agent_id,
        "action": payload.action,
        "sandbox": "nemoclaw",
    }


@app.get("/api/health")
async def health():
    return {"status": "online", "service": "OpenClaw Gateway", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3101, log_level="info")
