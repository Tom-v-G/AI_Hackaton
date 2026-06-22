from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DE_LEKBAK_", env_file=".env", extra="ignore")

    app_name: str = "De Lekbak Viral CVE Dashboard"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://de_lekbak:de_lekbak@localhost:5432/de_lekbak"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False
    bluesky_enabled: bool = True
    bluesky_poll_interval_seconds: int = 300
    bluesky_search_terms: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "CVE",
            "CVE-",
            "vulnerability",
            "exploit",
            "0day",
            "RCE",
            "PoC",
            "critical vulnerability",
        ]
    )
    bluesky_like_weight: float = 1.0
    bluesky_reply_weight: float = 1.5
    bluesky_repost_weight: float = 2.0
    bluesky_quote_weight: float = 2.0

    @field_validator("bluesky_search_terms", mode="before")
    @classmethod
    def parse_bluesky_search_terms(cls, value: object) -> object:
        if isinstance(value, str):
            return [term.strip() for term in value.split(",") if term.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
