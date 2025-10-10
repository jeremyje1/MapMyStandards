"""
A3E Core Configuration and Settings

Environment-aware configuration management for the A3E system.
Supports development, staging, and production environments.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
import json

from pydantic import AliasChoices, BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


class Settings(BaseSettings):
    """A3E Application Settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "A3E - Autonomous Accreditation & Audit Engine"
    version: str = "0.1.0"
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        validation_alias=AliasChoices("RAILWAY_ENVIRONMENT", "ENVIRONMENT"),
    )
    debug: bool = False

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Database Configuration
    database_url: str = "sqlite:///./a3e.db"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_init_retries: int = 10
    database_init_backoff: float = 3.0
    allow_start_without_db: bool = True

    # Vector Database (Milvus) Configuration
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection_prefix: str = "a3e"

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 3600  # 1 hour default

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # AWS Bedrock Configuration
    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-5-sonnet-20240620-v1:0",
        validation_alias=AliasChoices("BEDROCK_MODEL_ID", "BEDROCK_MODEL_CLAUDE"),
    )
    bedrock_model_embed: str = "text-embed-1"
    bedrock_max_tokens: int = 4096

    # LLM Configuration
    openai_api_key: Optional[str] = None
    openai_embed_model: str = "text-embedding-3-large"
    openai_json_model: str = "gpt-4.1-mini"
    anthropic_api_key: Optional[str] = None

    # Agent Configuration
    agent_max_rounds: int = 3
    agent_temperature: float = 0.1
    citation_threshold: float = 0.85

    # ETL Configuration
    airbyte_server_host: str = "localhost"
    airbyte_server_port: int = 8000
    airbyte_username: str = "airbyte"
    airbyte_password: str = "password"

    # Document Processing
    max_file_size_mb: int = 100
    data_dir: str = "/app/data"
    supported_file_types: str = "pdf,docx,xlsx,csv,txt,md"

    # Security
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    # Public URLs (used in emails/static links)
    PUBLIC_APP_URL: str = "https://platform.mapmystandards.ai"
    PUBLIC_API_URL: str = "https://api.mapmystandards.ai"

    # Email Configuration (Postmark)
    POSTMARK_SERVER_TOKEN: Optional[str] = None
    POSTMARK_API_KEY: Optional[str] = None  # Alternative name
    EMAIL_FROM: str = "support@mapmystandards.ai"
    EMAIL_FROM_NAME: str = "MapMyStandards A³E"
    ADMIN_NOTIFICATION_EMAIL: str = "info@northpathstrategies.org"

    # Payment Configuration (Stripe)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    # Google Drive Integration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "https://platform.mapmystandards.ai/api/v1/integrations/google/callback"

    # Canvas LMS Integration
    CANVAS_CLIENT_ID: Optional[str] = None
    CANVAS_CLIENT_SECRET: Optional[str] = None
    CANVAS_ACCESS_TOKEN: Optional[str] = None
    CANVAS_API_BASE: str = "https://canvas.instructure.com/api/v1"

    # Banner SIS Integration
    BANNER_ETHOS_TOKEN: Optional[str] = None
    BANNER_DB_HOST: Optional[str] = None
    BANNER_DB_USER: Optional[str] = None
    BANNER_DB_PASSWORD: Optional[str] = None
    BANNER_DB_URL: Optional[str] = None

    # SharePoint/Microsoft Integration
    MS_CLIENT_ID: Optional[str] = None
    MS_CLIENT_SECRET: Optional[str] = None
    MS_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None  # Alias for MS_CLIENT_ID
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_COLLEGE_MONTHLY: str = Field(
        default="",
        validation_alias=AliasChoices("STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY", "STRIPE_PRICE_COLLEGE_MONTHLY"),
    )
    STRIPE_PRICE_COLLEGE_YEARLY: str = Field(
        default="",
        validation_alias=AliasChoices("STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL", "STRIPE_PRICE_COLLEGE_YEARLY"),
    )
    STRIPE_PRICE_MULTI_CAMPUS_MONTHLY: str = Field(
        default="",
        validation_alias=AliasChoices("STRIPE_PRICE_ID_INSTITUTION_MONTHLY", "STRIPE_PRICE_MULTI_CAMPUS_MONTHLY"),
    )
    STRIPE_PRICE_MULTI_CAMPUS_YEARLY: str = Field(
        default="",
        validation_alias=AliasChoices("STRIPE_PRICE_ID_INSTITUTION_ANNUAL", "STRIPE_PRICE_MULTI_CAMPUS_YEARLY"),
    )

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour

    # Monitoring
    sentry_dsn: Optional[str] = None
    prometheus_enabled: bool = False

    # Feature Flags
    enable_graphql: bool = True
    enable_real_time_processing: bool = True
    enable_batch_processing: bool = True
    enable_auto_evidence_mapping: bool = True
    feature_flags: Dict[str, bool] = Field(default_factory=dict, validation_alias="FEATURE_FLAGS")

    @field_validator("feature_flags", mode="before")
    @classmethod
    def parse_feature_flags(cls, value):
        default_flags = {
            "standards_graph": True,
            "evidence_mapper": True,
            "evidence_trust_score": True,
            "gap_risk_predictor": True,
            "crosswalkx": True,
            "citeguard": True,
        }
        if value is None or value == "":
            return default_flags
        if isinstance(value, dict):
            merged = default_flags.copy()
            merged.update({k: bool(v) for k, v in value.items()})
            return merged
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    merged = default_flags.copy()
                    merged.update({k: bool(v) for k, v in parsed.items()})
                    return merged
            except json.JSONDecodeError:
                pass
        # Fallback to defaults if parsing fails
        return default_flags

    @model_validator(mode="after")
    def apply_environment_feature_defaults(cls, values: "Settings") -> "Settings":
        if values.environment == Environment.PRODUCTION and os.getenv("FEATURE_FLAGS") in (None, ""):
            values.feature_flags = {key: False for key in values.feature_flags.keys()}
        return values

    def is_feature_enabled(self, flag: str) -> bool:
        return bool(self.feature_flags.get(flag, False))
    
    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v

# Singleton settings cache
_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    """Return a cached Settings instance (lazy-loaded)."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()  # type: ignore
    return _settings_instance

@property
def is_development(self: Settings) -> bool:  # type: ignore
    return self.environment == Environment.DEVELOPMENT

@property
def is_production(self: Settings) -> bool:  # type: ignore
    return self.environment == Environment.PRODUCTION

@property
def cors_origins_list(self: Settings) -> List[str]:  # type: ignore
    if isinstance(self.cors_origins, str):
        return [origin.strip() for origin in self.cors_origins.split(",")]
    return self.cors_origins

@property
def supported_file_types_list(self: Settings) -> List[str]:  # type: ignore
    if isinstance(self.supported_file_types, str):
        return [file_type.strip() for file_type in self.supported_file_types.split(",")]
    return self.supported_file_types

@property
def milvus_uri(self: Settings) -> str:  # type: ignore
    return f"http://{self.milvus_host}:{self.milvus_port}"

@property
def database_config(self: Settings) -> Dict[str, Any]:  # type: ignore
    return {
        "url": self.database_url,
        "pool_size": self.database_pool_size,
        "max_overflow": self.database_max_overflow,
        "echo": is_development.__get__(self, Settings)(),
    }


# Global settings instance
settings = Settings()

# Dynamically attach convenience properties that were previously misplaced
def _is_dev(self: Settings) -> bool:  # type: ignore
    return self.environment == Environment.DEVELOPMENT

def _is_prod(self: Settings) -> bool:  # type: ignore
    return self.environment == Environment.PRODUCTION

Settings.is_development = property(_is_dev)  # type: ignore
Settings.is_production = property(_is_prod)  # type: ignore
