"""Central configuration loaded from env, YAML and defaults."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict, sources


class DatabaseSettings(BaseModel):
    """Database and vector store connection options."""

    postgres_uri: str = "postgresql://user:password@localhost:5432/axon_db"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    redis_url: str = "redis://localhost:6379/0"


class LlmSettings(BaseModel):
    """LLM configuration."""

    default_local_model: str = "qwen3:8b"
    qwen_agent_generate_cfg: dict[str, Any] | None = None


class AppConfig(BaseModel):
    """Application-level options."""

    mcp_mode: bool = False
    mcp_log_path: str = "mcp_traffic.json"
    api_token: str | None = None
    rate_limit_per_minute: int = 60
    proactive_scan_minutes: int = 30


class Settings(BaseSettings):
    """Load configuration from environment, YAML, then defaults."""

    database: DatabaseSettings = DatabaseSettings()  # type: ignore[misc]
    llm: LlmSettings = LlmSettings()  # type: ignore[misc]
    app: AppConfig = AppConfig()  # type: ignore[misc]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        yaml_file="config/settings.yaml",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: sources.PydanticBaseSettingsSource,
        env_settings: sources.PydanticBaseSettingsSource,
        dotenv_settings: sources.PydanticBaseSettingsSource,
        file_secret_settings: sources.PydanticBaseSettingsSource,
    ) -> tuple[sources.PydanticBaseSettingsSource, ...]:
        yaml_source = sources.YamlConfigSettingsSource(settings_cls)
        return (
            env_settings,
            dotenv_settings,
            yaml_source,
            init_settings,
            file_secret_settings,
        )


# Singleton instance imported elsewhere
settings = Settings()
