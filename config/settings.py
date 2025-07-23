# axon/config/settings.py

from pydantic import BaseModel, ValidationError
import yaml


# Use Pydantic's BaseModel for structured data
class DatabaseSettings(BaseModel):
    postgres_uri: str
    qdrant_host: str
    qdrant_port: int


class LlmSettings(BaseModel):
    default_local_model: str
    qwen_agent_generate_cfg: dict | None = None


class AppConfig(BaseModel):
    """Application-level options."""

    mcp_mode: bool = False
    mcp_log_path: str = "mcp_traffic.json"
    api_token: str | None = None
    rate_limit_per_minute: int = 60
    proactive_scan_minutes: int = 30


class AppSettings(BaseModel):
    database: DatabaseSettings
    llm: LlmSettings
    app: AppConfig = AppConfig()


def load_settings() -> AppSettings:
    """Loads settings from the YAML file and validates them."""
    try:
        with open("config/settings.yaml", "r") as f:
            config_data = yaml.safe_load(f)

        # Validate the loaded data against our Pydantic models
        return AppSettings(**config_data)
    except FileNotFoundError:
        print("ERROR: config/settings.yaml not found.")
        raise
    except ValidationError as e:
        print(f"ERROR: Configuration validation failed: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while loading settings: {e}")
        raise


# Create a single instance that will be imported by other parts of the app
settings = load_settings()
