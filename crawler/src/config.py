"""
Agentic AI Landscape Tracker - Runtime settings

All runtime configuration is read from environment variables (optionally
loaded from a .env file) and validated on startup with pydantic-settings.
See ../.env.example for the full list of supported variables.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven crawler settings, validated at construction time."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_ignore_empty=True,
        extra='ignore',
    )

    # Path to the YAML file describing sources and default crawler behaviour
    crawler_config_path: str = '../config.yaml'

    # Optional overrides for values in the YAML config (env takes precedence)
    crawler_output_path: Optional[str] = None
    crawler_delay_between_requests: Optional[float] = None
    crawler_max_retries: Optional[int] = None
    crawler_timeout: Optional[int] = None
    crawler_backfill_enabled: Optional[bool] = None
    crawler_backfill_start_date: Optional[str] = None

    # Port for the liveness probe HTTP server
    health_port: int = 8080


def get_settings() -> Settings:
    """Load and validate settings from the environment.

    Raises pydantic.ValidationError on startup if any value is invalid.
    """
    return Settings()
