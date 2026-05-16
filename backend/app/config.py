from functools import lru_cache
from typing import Optional

from pydantic import Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _empty_to_none(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    if isinstance(value, SecretStr) and not value.get_secret_value().strip():
        return None
    return value


def _strip_secret(value: object) -> object:
    value = _empty_to_none(value)
    if value is None:
        return None
    if isinstance(value, SecretStr):
        return value.get_secret_value().strip()
    if isinstance(value, str):
        return value.strip()
    return value


class Settings(BaseSettings):
    """Validated environment configuration for all external service credentials."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    OPENAI_API_KEY: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key (required for Phase 2+ agents).",
    )
    GOOGLE_GENAI_API_KEY: Optional[SecretStr] = Field(
        default=None,
        description="Google GenAI API key for Gemini vision analysis.",
    )
    SUPABASE_URL: Optional[HttpUrl] = Field(
        default=None,
        description="Supabase project URL (https://<project-ref>.supabase.co).",
    )
    SUPABASE_SERVICE_ROLE_KEY: Optional[SecretStr] = Field(
        default=None,
        description="Supabase service role key for server-side data mutations.",
    )

    @field_validator(
        "OPENAI_API_KEY",
        "GOOGLE_GENAI_API_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        mode="before",
    )
    @classmethod
    def normalize_optional_secrets(cls, value: object) -> object:
        return _strip_secret(value)

    @field_validator("SUPABASE_URL", mode="before")
    @classmethod
    def normalize_supabase_url(cls, value: object) -> object:
        value = _empty_to_none(value)
        if isinstance(value, str):
            return value.strip()
        return value

    @property
    def supabase_configured(self) -> bool:
        return self.SUPABASE_URL is not None and self.SUPABASE_SERVICE_ROLE_KEY is not None

    @property
    def openai_configured(self) -> bool:
        return self.OPENAI_API_KEY is not None

    @property
    def google_genai_configured(self) -> bool:
        return self.GOOGLE_GENAI_API_KEY is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
