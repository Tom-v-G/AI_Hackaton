from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


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


@lru_cache
def get_settings() -> Settings:
    return Settings()
