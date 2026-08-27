from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_secret_key: str = "dev-secret"
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://trading:trading@localhost:5432/trading_desk"
    redis_url: str = "redis://localhost:6379/0"

    operator_username: str = "operator"
    operator_password_hash: str = ""
    jwt_secret_key: str = "jwt-dev-secret"
    jwt_expire_minutes: int = 10080

    oanda_api_token: str = ""
    oanda_account_id: str = ""
    oanda_api_url: str = "https://api-fxpractice.oanda.com"

    twelve_data_api_key: str = ""
    finnhub_api_key: str = ""
    metaapi_token: str = ""
    anthropic_api_key: str = ""

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    credentials_encryption_key: str = ""

    chat_rate_limit_per_minute: int = 20
    bot_order_min_interval_seconds: int = 30
    price_divergence_threshold_pct: float = 0.15

    default_risk_per_trade_r: float = 1.0
    default_spread_limit_pips: float = 3.0
    default_daily_loss_limit_r: float = 5.0
    default_consecutive_loss_limit: int = 3
    live_promotion_confirmation_method: str = "pin"  # pin | symbol
    live_promotion_pin: str = "1234"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
