from typing import Any, Optional

import httpx

from app.config import get_settings


class FinnhubService:
    async def get_news(self, category: str = "forex") -> list[dict[str, Any]]:
        settings = get_settings()
        if not settings.finnhub_api_key:
            return []
        url = "https://finnhub.io/api/v1/news"
        params = {"category": category, "token": settings.finnhub_api_key}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            items = resp.json()
        ranked = sorted(items, key=lambda x: x.get("datetime", 0), reverse=True)
        return [
            {
                "headline": n.get("headline"),
                "summary": n.get("summary"),
                "source": n.get("source"),
                "datetime": n.get("datetime"),
                "url": n.get("url"),
                "impact": self._estimate_impact(n),
            }
            for n in ranked[:50]
        ]

    async def get_economic_calendar(self) -> list[dict[str, Any]]:
        settings = get_settings()
        if not settings.finnhub_api_key:
            return []
        from datetime import date, timedelta

        today = date.today()
        url = "https://finnhub.io/api/v1/calendar/economic"
        params = {
            "from": today.isoformat(),
            "to": (today + timedelta(days=7)).isoformat(),
            "token": settings.finnhub_api_key,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            data = resp.json()
        events = data.get("economicCalendar", [])
        return sorted(events, key=lambda e: self._impact_score(e.get("impact", "")), reverse=True)

    def _estimate_impact(self, item: dict) -> str:
        headline = (item.get("headline") or "").lower()
        if any(w in headline for w in ("fed", "ecb", "nfp", "cpi", "rate decision", "gdp")):
            return "high"
        if any(w in headline for w in ("pmi", "employment", "retail")):
            return "medium"
        return "low"

    def _impact_score(self, impact: str) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(impact.lower(), 0)
