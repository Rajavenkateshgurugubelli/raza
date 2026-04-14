from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    google_api_key: str = "your_gemini_key_here"
    model_name: str = "gemini-2.0-flash"  # Latest fast model
    app_name: str = "R.A.Z.A. Agent"
    memory_db_path: str = "raza_memory.db"
    max_memory_messages: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
