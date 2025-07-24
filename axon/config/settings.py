from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pydantic import BaseModel, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict, sources


class ConfigError(RuntimeError):
    """Raised when configuration validation fails."""

    def __init__(self, error: ValidationError) -> None:
        super().__init__(str(error))
        self.error = error


ROOT_DIR = Path(__file__).resolve().parents[2]
EXAMPLE_PATH = ROOT_DIR / "config" / "settings.example.yaml"
LOCAL_PATH = ROOT_DIR / "config" / "settings.yaml"


def _yaml_source(
    path: Path, settings_cls: type[BaseSettings]
) -> sources.PydanticBaseSettingsSource:
    if not path.exists():
        return sources.InitSettingsSource(settings_cls, {})
    return sources.YamlConfigSettingsSource(settings_cls, path)


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"


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
    log_level: LogLevel = LogLevel.info


class Settings(BaseSettings):
    """Global application settings."""

    database: DatabaseSettings
    llm: LlmSettings = LlmSettings()
    app: AppConfig = AppConfig()

    example_path: ClassVar[Path] = EXAMPLE_PATH
    local_path: ClassVar[Path] = LOCAL_PATH

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AXON_",
        extra="forbid",
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
        example = _yaml_source(cls.example_path, settings_cls)
        local = _yaml_source(cls.local_path, settings_cls)
        return (
            env_settings,
            local,
            example,
            init_settings,
            dotenv_settings,
            file_secret_settings,
        )

    def pretty_dump(self, mask_secrets: bool = True) -> str:
        """Dump settings as YAML with optional secret redaction."""

        def mask(value: Any) -> Any:
            if isinstance(value, SecretStr):
                return "***" if mask_secrets else value.get_secret_value()
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, dict):
                return {k: mask(v) for k, v in value.items()}
            if isinstance(value, list):
                return [mask(v) for v in value]
            return value

        data = mask(self.model_dump())
        return yaml.safe_dump(data, sort_keys=False)

    @classmethod
    def dump_example(cls, path: str | Path) -> None:
        path = Path(path)
        with open(cls.example_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)


_settings_cache: Settings | None = None


def get_settings() -> Settings:
    """Return cached Settings instance."""
    global _settings_cache
    if _settings_cache is None:
        try:
            _settings_cache = Settings()  # type: ignore[call-arg]
        except ValidationError as exc:  # pragma: no cover - validation
            raise ConfigError(exc) from exc
    return _settings_cache


def reload_settings(
    *, example_file: str | Path | None = None, local_file: str | Path | None = None
) -> None:
    """Clear the cache so the next call to :func:`get_settings` reloads."""
    global _settings_cache
    Settings.example_path = Path(example_file) if example_file is not None else EXAMPLE_PATH
    Settings.local_path = Path(local_file) if local_file is not None else LOCAL_PATH
    _settings_cache = None


def validate_or_die() -> Settings:
    """Validate configuration and exit with errors if invalid."""
    try:
        return get_settings()
    except ConfigError as exc:  # pragma: no cover - validation
        print("Invalid configuration:")
        for err in exc.error.errors():
            loc = ".".join(str(p) for p in err["loc"])
            print(f"- {loc}: {err['msg']}")
        raise SystemExit(1)


def schema_json() -> str:
    """Return the JSON schema for the settings."""
    return json.dumps(Settings.model_json_schema(), indent=2)


# Backwards compatibility for old imports
settings = get_settings()
