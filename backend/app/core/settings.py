"""Centralized application settings for Echo Matrix."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Echo Matrix"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    database_url: str
    redis_url: str

    news_api_key: str = ""
    cryptopanic_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    whale_alert_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    binance_api_key: str = ""
    binance_api_secret: str = ""

    mt5_bridge_url: str = ""
    mt5_bridge_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
