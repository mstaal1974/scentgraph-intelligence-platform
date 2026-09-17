from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

LOCAL_ENVIRONMENTS = frozenset({"development", "dev", "local", "test", "testing"})
DEFAULT_DEVELOPMENT_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
)


class Settings(BaseSettings):
    """Runtime configuration, loaded only from explicit AromaTwin environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="AROMATWIN_", env_file=".env", extra="ignore", populate_by_name=True
    )

    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("AROMATWIN_ENV", "AROMATWIN_ENVIRONMENT"),
    )
    database_url: str = Field(
        default="postgresql+psycopg://aromatwin:aromatwin@localhost:5432/aromatwin",
        validation_alias=AliasChoices("DATABASE_URL", "AROMATWIN_DATABASE_URL"),
    )
    api_key: str | None = None
    admin_api_key: str | None = None
    private_api_key: str | None = None
    allowed_origins: Annotated[tuple[str, ...], NoDecode] = Field(
        default=DEFAULT_DEVELOPMENT_ORIGINS,
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "AROMATWIN_ALLOWED_ORIGINS"),
    )
    enable_admin_console: bool = True
    enable_private_supplier_endpoints: bool = True
    # Opt-in, local-only escape hatch. Authentication fails closed unless this is set
    # explicitly, so an unconfigured or half-configured deployment denies rather than allows.
    allow_insecure_local_auth: bool = False
    ai_allow_fallback: bool = True
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
    def validate_deployed_environment(self) -> "Settings":
        """Refuse to start a non-local environment that cannot authenticate its surfaces."""
        if self.is_local:
            return self
        missing = ["AROMATWIN_API_KEY"] if not self.api_key else []
        if self.enable_admin_console and not self.admin_api_key:
            missing.append("AROMATWIN_ADMIN_API_KEY")
        if self.enable_private_supplier_endpoints and not self.private_api_key:
            missing.append("AROMATWIN_PRIVATE_API_KEY")
        if missing:
            raise ValueError(
                f"Environment '{self.environment}' requires configured secrets: "
                + ", ".join(missing)
            )
        if "*" in self.allowed_origins:
            raise ValueError("Wildcard CORS origins are not permitted outside local environments")
        if self.allow_insecure_local_auth:
            raise ValueError(
                "AROMATWIN_ALLOW_INSECURE_LOCAL_AUTH is only permitted in local environments"
            )
        return self

    @property
    def is_local(self) -> bool:
        return self.environment in LOCAL_ENVIRONMENTS


@lru_cache
def get_settings() -> Settings:
    return Settings()
