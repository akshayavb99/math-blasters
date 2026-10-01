"""Application settings, read from the environment (or a local .env file)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # postgresql+psycopg://<user>:<password>@<host>:<port>/<database>
    database_url: str = "postgresql+psycopg://mathblasters:mathblasters@localhost:5433/mathblasters"

    # Comma-separated list of origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:5173"

    # Log-level
    log_level: str = "INFO"

    # Production-safe default; local HTTP development must explicitly opt out.
    cookie_secure: bool = True

    # Default rate limit for POST /api/completions
    completions_rate_limit: str = "20/minute"

    # Generated content manifest used to validate completion lesson slugs.
    content_manifest_path: str = "../content/manifest.json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
