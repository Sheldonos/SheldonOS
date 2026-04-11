"""
Notification Manager
====================
Sends alerts to the user via multiple channels so they never miss a trade
event even when away from their computer.

Supported channels:
  - Telegram Bot    (recommended — works on mobile)
  - Discord Webhook (works on desktop/mobile)
  - Desktop notify  (macOS/Linux — via plyer or notify-send)
  - Log file        (always active — fallback)

Each notification has a level: info | success | warning | critical
Critical notifications are sent to ALL active channels simultaneously.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("daemon.notifier")


class NotificationManager:
    """
    Multi-channel notification dispatcher.
    Thread-safe. Non-blocking (dispatches in background thread).
    """

    def __init__(self, config: Dict[str, Any]):
        notif_cfg = config.get("notifications", {})

        # Telegram
        self._tg_token = notif_cfg.get("telegram_bot_token") or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._tg_chat_id = notif_cfg.get("telegram_chat_id") or os.getenv("TELEGRAM_CHAT_ID", "")
        self._tg_enabled = bool(self._tg_token and self._tg_chat_id)

        # Discord
        self._discord_webhook = notif_cfg.get("discord_webhook_url") or \
                                 os.getenv("DISCORD_WEBHOOK_URL", "")
        self._discord_enabled = bool(self._discord_webhook)

        # Desktop
        self._desktop_enabled = notif_cfg.get("desktop_notifications", True)

        # Level filtering
        self._min_level = notif_cfg.get("min_level", "info")
        self._level_order = {"info": 0, "success": 1, "warning": 2, "critical": 3}

        active = []
        if self._tg_enabled:    active.append("Telegram")
        if self._discord_enabled: active.append("Discord")
        if self._desktop_enabled: active.append("Desktop")
        active.append("Log")

        logger.info("NotificationManager initialized. Active channels: %s", ", ".join(active))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(
        self,
        title: str,
        body: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Send a notification. Non-blocking — dispatches in a daemon thread.
        """
        if self._level_order.get(level, 0) < self._level_order.get(self._min_level, 0):
            return

        thread = threading.Thread(
            target=self._dispatch,
            args=(title, body, level, data),
            daemon=True,
        )
        thread.start()

    def send_sync(
        self,
        title: str,
        body: str,
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ):
        """Synchronous version — blocks until all channels have been attempted."""
        self._dispatch(title, body, level, data)

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, title: str, body: str, level: str, data: Optional[Dict]):
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        full_message = f"[{timestamp}] {title}\n{body}"

        # Always log
        log_fn = {
            "info": logger.info,
            "success": logger.info,
            "warning": logger.warning,
            "critical": logger.critical,
        }.get(level, logger.info)
        log_fn("NOTIFICATION | %s | %s", title, body)

        # Telegram
        if self._tg_enabled:
            try:
                self._send_telegram(title, body, level, timestamp)
            except Exception as exc:
                logger.debug("Telegram notification failed: %s", exc)

        # Discord
        if self._discord_enabled:
            try:
                self._send_discord(title, body, level, timestamp, data)
            except Exception as exc:
                logger.debug("Discord notification failed: %s", exc)

        # Desktop
        if self._desktop_enabled:
            try:
                self._send_desktop(title, body, level)
            except Exception as exc:
                logger.debug("Desktop notification failed: %s", exc)

    # ------------------------------------------------------------------
    # Channel implementations
    # ------------------------------------------------------------------

    def _send_telegram(self, title: str, body: str, level: str, timestamp: str):
        """Send a Telegram message via Bot API."""
        level_emoji = {
            "info": "ℹ️", "success": "✅", "warning": "⚠️", "critical": "🚨"
        }.get(level, "📢")

        text = (
            f"{level_emoji} *{self._escape_md(title)}*\n"
            f"_{timestamp}_\n\n"
            f"{self._escape_md(body)}"
        )

        url = f"https://api.telegram.org/bot{self._tg_token}/sendMessage"
        payload = {
            "chat_id": self._tg_chat_id,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()

    def _send_discord(
        self,
        title: str,
        body: str,
        level: str,
        timestamp: str,
        data: Optional[Dict],
    ):
        """Send a Discord embed via webhook."""
        color_map = {
            "info": 0x5865F2,      # Discord blurple
            "success": 0x57F287,   # Green
            "warning": 0xFEE75C,   # Yellow
            "critical": 0xED4245,  # Red
        }
        embed = {
            "title": title,
            "description": body,
            "color": color_map.get(level, 0x5865F2),
            "footer": {"text": f"Polymarket Sniper • {timestamp}"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if data:
            fields = []
            for k, v in list(data.items())[:6]:
                fields.append({
                    "name": k.replace("_", " ").title(),
                    "value": str(v)[:100],
                    "inline": True,
                })
            embed["fields"] = fields

        payload = {
            "username": "Polymarket Sniper 🎯",
            "embeds": [embed],
        }
        resp = requests.post(self._discord_webhook, json=payload, timeout=10)
        resp.raise_for_status()

    def _send_desktop(self, title: str, body: str, level: str):
        """Send a desktop notification (macOS/Linux)."""
        import platform
        system = platform.system()

        if system == "Darwin":
            # macOS — use osascript
            import subprocess
            script = f'display notification "{body}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)

        elif system == "Linux":
            # Linux — use notify-send
            import subprocess
            urgency = "critical" if level == "critical" else "normal"
            subprocess.run(
                ["notify-send", "-u", urgency, title, body],
                capture_output=True, timeout=5,
            )

    @staticmethod
    def _escape_md(text: str) -> str:
        """Escape special characters for Telegram MarkdownV2."""
        special = r"\_*[]()~`>#+-=|{}.!"
        for char in special:
            text = text.replace(char, f"\\{char}")
        return text

    def test(self):
        """Send a test notification to all active channels."""
        self.send_sync(
            title="🎯 Polymarket Sniper — Test Notification",
            body="If you see this, notifications are working correctly!",
            level="success",
        )
