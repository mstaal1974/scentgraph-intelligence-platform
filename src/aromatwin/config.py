from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AROMATWIN_", env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://aromatwin:aromatwin@localhost:5432/aromatwin"


@lru_cache
def get_settings() -> Settings:
    return Settings()
