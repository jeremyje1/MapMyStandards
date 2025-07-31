"""
A3E Core Configuration and Settings

Environment-aware configuration management for the A3E system.
Supports development, staging, and production environments.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
from enum import Enum
import os


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


class Settings(BaseSettings):
    """A3E Application Settings"""
    
    # Application
    app_name: str = "A3E - Autonomous Accreditation & Audit Engine"
    version: str = "0.1.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = "/api/v1"
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
    # Vector Database (Milvus) Configuration
    milvus_host: str = Field(default="localhost", env="MILVUS_HOST")
    milvus_port: int = Field(default=19530, env="MILVUS_PORT")
    milvus_collection_prefix: str = Field(default="a3e", env="MILVUS_COLLECTION_PREFIX")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")  # 1 hour default
    
    # AWS Configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    # AWS Bedrock Configuration
    bedrock_region: str = Field(default="us-east-1", env="BEDROCK_REGION")
    bedrock_model_id: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", env="BEDROCK_MODEL_ID")
    bedrock_max_tokens: int = Field(default=4096, env="BEDROCK_MAX_TOKENS")
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Agent Configuration
    agent_max_rounds: int = Field(default=3, env="AGENT_MAX_ROUNDS")
    agent_temperature: float = Field(default=0.1, env="AGENT_TEMPERATURE")
    citation_threshold: float = Field(default=0.85, env="CITATION_THRESHOLD")
    
    # ETL Configuration
    airbyte_server_host: str = Field(default="localhost", env="AIRBYTE_SERVER_HOST")
    airbyte_server_port: int = Field(default=8000, env="AIRBYTE_SERVER_PORT")
    airbyte_username: str = Field(default="airbyte", env="AIRBYTE_USERNAME")
    airbyte_password: str = Field(default="password", env="AIRBYTE_PASSWORD")
    
    # Document Processing
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    supported_file_types: List[str] = Field(
        default=["pdf", "docx", "xlsx", "csv", "txt", "md"],
        env="SUPPORTED_FILE_TYPES"
    )
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    prometheus_enabled: bool = Field(default=False, env="PROMETHEUS_ENABLED")
    
    # Feature Flags
    enable_graphql: bool = Field(default=True, env="ENABLE_GRAPHQL")
    enable_real_time_processing: bool = Field(default=True, env="ENABLE_REAL_TIME_PROCESSING")
    enable_batch_processing: bool = Field(default=True, env="ENABLE_BATCH_PROCESSING")
    enable_auto_evidence_mapping: bool = Field(default=True, env="ENABLE_AUTO_EVIDENCE_MAPPING")
    
    @validator("environment", pre=True)
    def validate_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    @validator("cors_origins", pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("supported_file_types", pre=True)
    def validate_supported_file_types(cls, v):
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    @property
    def milvus_uri(self) -> str:
        return f"http://{self.milvus_host}:{self.milvus_port}"
    
    @property
    def database_config(self) -> Dict[str, Any]:
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "echo": self.is_development,
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
