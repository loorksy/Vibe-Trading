"""Redis-based rate limiting for chat/analysis endpoints."""

import time
from typing import Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    RATE_LIMITED_PATHS = {"/api/chat/message", "/api/recommendations/analyze", "/api/chat/stream"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path not in self.RATE_LIMITED_PATHS:
            return await call_next(request)

        settings = get_settings()
        client_id = request.client.host if request.client else "unknown"
        key = f"rate:{request.url.path}:{client_id}"

        try:
            import redis
            r = redis.from_url(settings.redis_url)
            now = int(time.time())
            window = 60
            limit = settings.chat_rate_limit_per_minute

            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window)
            _, _, count, _ = pipe.execute()

            if count > limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {limit} requests per minute",
                )
        except HTTPException:
            raise
        except Exception:
            pass  # fail open if Redis unavailable

        return await call_next(request)
