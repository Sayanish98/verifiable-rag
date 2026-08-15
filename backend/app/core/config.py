from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Document Intelligence Platform"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    vector_db_path: str = "vector_db"
    upload_dir: str = "uploads"
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    llm_model: str = "gemini-2.5-flash"
    mongodb_url: str | None = Field(default=None, alias="MONGODB_URL")
    mongodb_database: str = Field(default="verifiable_rag", alias="MONGODB_DATABASE")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    query_cache_ttl_seconds: int = 300
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    rate_limit_per_minute: int = 60
    langgraph_checkpointer: str = Field(default="memory", alias="LANGGRAPH_CHECKPOINTER")
    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str | None = Field(default=None, alias="LANGFUSE_HOST")
    otel_exporter_otlp_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    prometheus_metrics_enabled: bool = Field(default=True, alias="PROMETHEUS_METRICS_ENABLED")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
