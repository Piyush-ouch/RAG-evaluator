"""
Application Configuration

Centralized, type-safe configuration using Pydantic Settings.
All values are sourced from environment variables with sensible defaults.
The config object is created once and reused via lru_cache.
"""

from __future__ import annotations

import enum
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, enum.Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings are grouped by concern for readability.
    All secrets have empty defaults to avoid accidental commits.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------
    app_name: str = "RAG Evaluator"
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    app_debug: bool = True
    app_version: str = "0.1.0"
    secret_key: str = "change-me-to-a-random-64-char-string"
    encryption_key: str = "change-me-to-a-fernet-key"
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    cors_origins: list[str] = ["http://localhost:3000"]

    # ---------------------------------------------------------
    # Server
    # ---------------------------------------------------------
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_workers: int = 4
    backend_log_level: str = "info"

    # ---------------------------------------------------------
    # Database (PostgreSQL)
    # ---------------------------------------------------------
    database_url: str = "postgresql+asyncpg://rageval:rageval_password@localhost:5432/rageval"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False

    # ---------------------------------------------------------
    # Redis
    # ---------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_db: int = 1
    redis_celery_db: int = 2

    # ---------------------------------------------------------
    # Object Storage (S3 / MinIO)
    # ---------------------------------------------------------
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_bucket_name: str = "rageval-storage"
    s3_region: str = "us-east-1"

    # ---------------------------------------------------------
    # Celery
    # ---------------------------------------------------------
    celery_broker_url: str = "redis://localhost:6379/2"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_always_eager: bool = False

    # ---------------------------------------------------------
    # JWT Authentication
    # ---------------------------------------------------------
    jwt_secret_key: str = "change-me-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # ---------------------------------------------------------
    # OAuth — Google
    # ---------------------------------------------------------
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ---------------------------------------------------------
    # OAuth — GitHub
    # ---------------------------------------------------------
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/v1/auth/github/callback"

    # ---------------------------------------------------------
    # AI Providers (platform-level defaults)
    # ---------------------------------------------------------
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_ai_api_key: str = ""
    groq_api_key: str = ""
    deepseek_api_key: str = ""
    openrouter_api_key: str = ""
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-02-01"
    ollama_base_url: str = "http://localhost:11434"

    # ---------------------------------------------------------
    # Email
    # ---------------------------------------------------------
    email_provider: str = "smtp"
    email_from_address: str = "noreply@rageval.dev"
    email_from_name: str = "RAG Evaluator"

    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    sendgrid_api_key: str = ""
    ses_region: str = "us-east-1"
    resend_api_key: str = ""

    # ---------------------------------------------------------
    # Stripe Billing
    # ---------------------------------------------------------
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_free_monthly: str = ""
    stripe_price_pro_monthly: str = ""
    stripe_price_pro_annual: str = ""
    stripe_price_enterprise_monthly: str = ""
    stripe_price_enterprise_annual: str = ""
    stripe_price_usage_metered: str = ""

    # ---------------------------------------------------------
    # Observability
    # ---------------------------------------------------------
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "rageval-backend"
    sentry_dsn: str = ""
    loki_url: str = "http://localhost:3100"

    # ---------------------------------------------------------
    # Rate Limiting
    # ---------------------------------------------------------
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_burst: int = 10

    # ---------------------------------------------------------
    # Computed Properties
    # ---------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnvironment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnvironment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.celery_task_always_eager

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the cached application settings singleton.

    Using lru_cache ensures the Settings object is created once
    (reading env vars and .env file) and reused for the lifetime
    of the process.
    """
    return Settings()
