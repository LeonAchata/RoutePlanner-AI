from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    openai_api_key: str
    google_maps_api_key: str
    
    # LLM Config
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    
    # App Config
    app_name: str = "Agente de Rutas Inteligente"
    debug: bool = False
    
    # Google Maps Config
    geocoding_language: str = "es"
    default_country: str = "PE"

@lru_cache
def get_settings() -> Settings:
    return Settings()