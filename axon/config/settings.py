from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import yaml
from pydantic import BaseModel, SecretStr, ValidationError
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    sources,
)


class ConfigError(RuntimeError):
    """Raised when configuration validation fails."""


ROOT_DIR = Path(__file__).resolve().parents[2]
EXAMPLE_PATH = ROOT_DIR / "config" / "settings.example.yaml"
LOCAL_PATH = ROOT_DIR / "config" / "settings.yaml"


def _yaml_source(
    path: Path, settings_cls: type[BaseSettings]
) -> sources.PydanticBaseSettingsSource:
    if not path.exists():
        return sources.InitSettingsSource(settings_cls, {})
    return sources.YamlConfigSettingsSource(settings_cls, path)


class DatabaseSettings(BaseModel):
    """Database and vector store settings."""

    postgres_uri: str
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    redis_url: str | None = None


class LlmSettings(BaseModel):
    """LLM configuration."""

    default_local_model: str = "qwen3:8b"
    qwen_agent_generate_cfg: dict[str, Any] | None = None


class AppConfig(BaseModel):
    """Application-level options."""

    mcp_mode: bool = False
    mcp_log_path: str = "mcp_traffic.json"
    api_token: SecretStr | None = None
    rate_limit_per_minute: int = 60
    proactive_scan_minutes: int = 30


class Settings(BaseSettings):
    """Global application settings."""

    database: DatabaseSettings
    llm: LlmSettings = LlmSettings()
    app: AppConfig = AppConfig()

    example_path: ClassVar[Path] = EXAMPLE_PATH
    local_path: ClassVar[Path] = LOCAL_PATH

    model_config = SettingsConfigDict(env_nested_delimiter="__", env_prefix="AXON__")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: sources.PydanticBaseSettingsSource,
        env_settings: sources.PydanticBaseSettingsSource,
        dotenv_settings: sources.PydanticBaseSettingsSource,
        file_secret_settings: sources.PydanticBaseSettingsSource,
    ) -> tuple[sources.PydanticBaseSettingsSource, ...]:
        example = _yaml_source(cls.example_path, settings_cls)
        local = _yaml_source(cls.local_path, settings_cls)
        return (
            env_settings,
            dotenv_settings,
            local,
            example,
            init_settings,
            file_secret_settings,
        )

    @classmethod
    def load(
        cls,
        example_file: str | Path | None = None,
        local_file: str | Path | None = None,
    ) -> Settings:
        if example_file is not None:
            cls.example_path = Path(example_file)
        if local_file is not None:
            cls.local_path = Path(local_file)
        try:
            settings = cls()  # type: ignore[call-arg]
        except ValidationError as exc:  # pragma: no cover - validation
            raise ConfigError(str(exc)) from exc
        settings.print_summary()
        return settings

    def summary(self) -> str:
        data = self.model_dump()
        if data.get("app", {}).get("api_token"):
            data["app"]["api_token"] = "***"
        return yaml.safe_dump(data, sort_keys=False)

    def print_summary(self) -> None:
        print("Loaded configuration:\n" + self.summary())

    @classmethod
    def dump_example(cls, path: str | Path) -> None:
        path = Path(path)
        with open(cls.example_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)


# Singleton instance
settings = Settings.load()
