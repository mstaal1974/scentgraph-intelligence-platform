from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCENTGRAPH_", env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://scentgraph:scentgraph@localhost:5432/scentgraph"


@lru_cache
def get_settings() -> Settings:
    return Settings()
