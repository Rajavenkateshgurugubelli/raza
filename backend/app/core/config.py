from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str = "mock_key_if_none"
    model_name: str = "claude-3-5-haiku-20241022"
    app_name: str = "R.A.Z.A. Agent"
    memory_db_path: str = "raza_memory.db"
    max_memory_messages: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
