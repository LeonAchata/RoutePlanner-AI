from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API keys. They default to empty so the app can boot (and serve /health)
    # even when misconfigured; requests fail with a clear 503 instead.
    openai_api_key: str = ""
    google_maps_api_key: str = ""

    # LLM
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_timeout_seconds: float = 30.0

    # Google Maps
    geocoding_language: str = "es"
    default_country: str = "PE"
    maps_timeout_seconds: float = 10.0

    # Route limits. 25 stops is the waypoint ceiling of the Directions API.
    max_stops: int = Field(default=25, ge=2, le=25)

    # App
    app_name: str = "RoutePlanner AI"
    debug: bool = False
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def missing_keys(self) -> list[str]:
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.google_maps_api_key:
            missing.append("GOOGLE_MAPS_API_KEY")
        return missing


@lru_cache
def get_settings() -> Settings:
    return Settings()
