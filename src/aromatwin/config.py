from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

LOCAL_ENVIRONMENTS = frozenset({"development", "dev", "local", "test", "testing"})
DEFAULT_DEVELOPMENT_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
)


class Settings(BaseSettings):
    """Runtime configuration, loaded only from explicit AromaTwin environment variables."""

    model_config = SettingsConfigDict(env_prefix="AROMATWIN_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://aromatwin:aromatwin@localhost:5432/aromatwin"
    api_key: str | None = None
    admin_api_key: str | None = None
    private_api_key: str | None = None
    allowed_origins: Annotated[tuple[str, ...], NoDecode] = DEFAULT_DEVELOPMENT_ORIGINS
    enable_admin_console: bool = True
    enable_private_supplier_endpoints: bool = True
    log_level: str = "INFO"
    public_api_prefix: str = ""
    internal_api_prefix: str = ""

    @field_validator("environment", mode="before")
    @classmethod
    def normalise_environment(cls, value: object) -> str:
        return str(value).strip().lower()

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value

    @field_validator("public_api_prefix", "internal_api_prefix")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if value and not value.startswith("/"):
            raise ValueError("API prefixes must be empty or begin with '/'")
        return value

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.environment == "production":
            missing = []
            if self.enable_admin_console and not self.admin_api_key:
                missing.append("AROMATWIN_ADMIN_API_KEY")
            if self.enable_private_supplier_endpoints and not self.private_api_key:
                missing.append("AROMATWIN_PRIVATE_API_KEY")
            if missing:
                raise ValueError("Production requires configured secrets: " + ", ".join(missing))
            if "*" in self.allowed_origins:
                raise ValueError("Wildcard CORS origins are not permitted in production")
        return self

    @property
    def is_local(self) -> bool:
        return self.environment in LOCAL_ENVIRONMENTS


@lru_cache
def get_settings() -> Settings:
    return Settings()
