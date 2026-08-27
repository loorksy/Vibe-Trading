from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import auth, chat, health, instruments, platform, trading
from app.config import get_settings
from app.core.rate_limit import RateLimitMiddleware
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    from app.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Trading Desk API",
        description="AI Trading Assistant Platform — single operator",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api")
    app.include_router(instruments.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(trading.router, prefix="/api")
    app.include_router(platform.router, prefix="/api")
    return app


app = create_app()
