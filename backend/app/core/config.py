from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    google_api_key: str = ""
    model_name: str = "gemini-2.0-flash"
    provider_order: str = "gemini,anthropic"
    app_name: str = "R.A.Z.A. Agent"
    memory_db_path: str = "raza_memory.db"
    max_memory_messages: int = 50
    recent_context_messages: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
