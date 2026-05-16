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
    SUPABASE_STORAGE_BUCKET: str = Field(
        default="loan-evidence",
        description="Supabase storage bucket for multimodal crop evidence.",
    )
    RISK_REJECTION_THRESHOLD: float = Field(
        default=45.0,
        ge=0,
        le=100,
        description="Loans with calculated risk above this value are rejected.",
    )
    GEMINI_VISION_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Primary Gemini model for multimodal crop vision analysis.",
    )
    GEMINI_VISION_FALLBACK_MODELS: str = Field(
        default="",
        description="Optional comma-separated fallback vision models (leave empty to retry primary only).",
    )
    GEMINI_VISION_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Retries per model on transient Gemini/network errors.",
    )
    MOCK_VISION_ON_FAILURE: bool = Field(
        default=False,
        description="Hackathon/demo: synthesize vision scores when Gemini is unavailable.",
    )
    GEMINI_EMBEDDING_MODEL: str = Field(
        default="gemini-embedding-2",
        description="Gemini embedding model (must match seeded market_intelligence vectors).",
    )
    ELEVENLABS_API_KEY: Optional[SecretStr] = Field(
        default=None,
        description="ElevenLabs API key for voice agent sessions (server-side only).",
    )
    ELEVENLABS_AGENT_ID: Optional[str] = Field(
        default=None,
        description="ElevenLabs Agents agent_id for conversational intake on /apply.",
    )

    # Seylan Bank APIs via hackathon sandbox proxy (see Web API Manual for paths/payloads)
    SEYLAN_API_KEY: Optional[SecretStr] = Field(
        default=None,
        description="Hackathon team key sent as x-api-key on every sandbox request.",
    )
    SEYLAN_SANDBOX_BASE_URL: str = Field(
        default="http://34.21.206.87:3000",
        description="Sandbox base URL; same paths as Seylan manual, no direct bank calls.",
    )
    SEYLAN_USE_TEST_PREFIX: bool = Field(
        default=True,
        description="Use TEST-prefixed merchant credentials (TESTCURSOR5 / TCURSOR5op).",
    )
    SEYLAN_MID: str = Field(default="CURSOR5")
    SEYLAN_TEST_MID: str = Field(default="TESTCURSOR5")
    SEYLAN_MERCHANT_LOGIN_ID: str = Field(default="CURSOR5op")
    SEYLAN_TEST_MERCHANT_LOGIN_ID: str = Field(default="TCURSOR5op")
    SEYLAN_MERCHANT_LOGIN_PASS: Optional[SecretStr] = Field(default=None)
    SEYLAN_TEST_MERCHANT_LOGIN_PASS: Optional[SecretStr] = Field(default=None)
    SEYLAN_QR_INSTITUTION_ID: str = Field(default="1")
    SEYLAN_QR_CHANNEL_USER_ID: str = Field(default="MerchantAPI")
    SEYLAN_QR_CHANNEL_PASS: Optional[SecretStr] = Field(default=None)
    SEYLAN_QR_CHECKSUM_KEY: Optional[SecretStr] = Field(
        default=None,
        description="HMAC-SHA512 checksum key for QR Merchant APIs (Annexure 1).",
    )
    SEYLAN_QR_TRANSACTION_CURRENCY: str = Field(
        default="144",
        description="ISO numeric currency code (144 = LKR) for dynamic QR.",
    )
    SEYLAN_ACCOUNT_CATEGORY: str = Field(default="EXT")
    SEYLAN_SOURCE_ACCOUNT_NUMBER: str = Field(default="064000012548001")
    SEYLAN_INTERNAL_DESTINATION_ACCOUNT: str = Field(
        default="001213437904100",
        description="Sandbox test account for internal transfers (section 1.1).",
    )
    SEYLAN_CEFTS_DESTINATION_ACCOUNT: str = Field(default="12345678")
    SEYLAN_CEFTS_DESTINATION_BANK_CODE: str = Field(default="6990")
    SEYLAN_SOURCE_CUSTOMER_NAME: str = Field(default="Cursor Buildathon 5")
    SEYLAN_SOURCE_BANK_CODE: str = Field(default="6287")
    SEYLAN_DEFAULT_DESTINATION_NAME: str = Field(default="Agri-Lend Farmer")
    SEYLAN_CURRENCY_CODE: str = Field(default="LKR")
    SEYLAN_MOCK_BANKING: bool = Field(
        default=True,
        description="Use placeholder disbursement/QR responses until sandbox Posting is enabled.",
    )
    SEYLAN_FALLBACK_TO_MOCK_ON_ERROR: bool = Field(
        default=True,
        description="If live CEFTS fails (e.g. 401), fall back to mock instead of rejecting the loan.",
    )

    @field_validator(
        "OPENAI_API_KEY",
        "GOOGLE_GENAI_API_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "ELEVENLABS_API_KEY",
        "SEYLAN_API_KEY",
        "SEYLAN_MERCHANT_LOGIN_PASS",
        "SEYLAN_TEST_MERCHANT_LOGIN_PASS",
        "SEYLAN_QR_CHANNEL_PASS",
        "SEYLAN_QR_CHECKSUM_KEY",
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

    @property
    def elevenlabs_configured(self) -> bool:
        return self.ELEVENLABS_API_KEY is not None

    @property
    def seylan_configured(self) -> bool:
        return bool(self.SEYLAN_API_KEY and self.SEYLAN_SANDBOX_BASE_URL.strip())

    @property
    def seylan_disbursement_configured(self) -> bool:
        return (
            not self.SEYLAN_MOCK_BANKING
            and self.seylan_configured
            and bool(self.SEYLAN_SOURCE_ACCOUNT_NUMBER.strip())
        )

    @property
    def seylan_qr_configured(self) -> bool:
        return (
            self.seylan_configured
            and self.SEYLAN_QR_CHECKSUM_KEY is not None
            and self.SEYLAN_QR_CHANNEL_PASS is not None
            and self.seylan_merchant_login_pass is not None
        )

    @property
    def seylan_sandbox_base_url(self) -> str:
        return self.SEYLAN_SANDBOX_BASE_URL.rstrip("/")

    @property
    def seylan_merchant_mid(self) -> str:
        return self.SEYLAN_TEST_MID if self.SEYLAN_USE_TEST_PREFIX else self.SEYLAN_MID

    @property
    def seylan_merchant_login_id(self) -> str:
        if self.SEYLAN_USE_TEST_PREFIX:
            return self.SEYLAN_TEST_MERCHANT_LOGIN_ID
        return self.SEYLAN_MERCHANT_LOGIN_ID

    @property
    def seylan_merchant_login_pass(self) -> Optional[str]:
        secret = (
            self.SEYLAN_TEST_MERCHANT_LOGIN_PASS
            if self.SEYLAN_USE_TEST_PREFIX
            else self.SEYLAN_MERCHANT_LOGIN_PASS
        )
        if secret is None:
            return None
        return secret.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
