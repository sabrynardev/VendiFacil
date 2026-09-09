from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VendiFácil API"
    database_url: str = "sqlite:///./marketpulse.db"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720
    backend_cors_origins_raw: str = "http://localhost:5173"
    seed_admin_email: str = "admin@marketpulse.dev"
    seed_admin_password: str = "admin123"
    auto_seed: bool = True
    intelligence_default_window_days: int = 30
    intelligence_safety_stock_days: int = 2
    intelligence_purchase_horizon_days: int = 7
    intelligence_cost_alert_percent: float = 5.0
    intelligence_stopped_days: int = 30
    intelligence_assistant_enabled: bool = True
    ai_provider: str = "disabled"
    ai_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def backend_cors_origins(self) -> list[str]:
        return [item.strip() for item in self.backend_cors_origins_raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
