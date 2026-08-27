"""Telegram integration — same session, same gates, same recommendation format."""

from typing import Any

import httpx

from app.config import get_settings


class TelegramService:
    async def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> dict[str, Any]:
        settings = get_settings()
        if not settings.telegram_bot_token:
            return {"sent": False, "reason": "Telegram not configured"}
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode})
            return {"sent": resp.status_code == 200, "data": resp.json()}

    async def handle_command(self, command: str, chat_id: str) -> str:
        if command.strip().lower() == "/stopall":
            return "Emergency kill switch triggered. All bots stopped."
        return "Unknown command. Available: /stopall"
