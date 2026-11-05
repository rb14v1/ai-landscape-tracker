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
    crawler_config_path: str

    # Optional overrides for values in the YAML config (env takes precedence)
    crawler_output_path: Optional[str] = None
    crawler_delay_between_requests: Optional[float] = None
    crawler_max_retries: Optional[int] = None
    crawler_backfill_enabled: Optional[bool] = None
    crawler_backfill_start_date: Optional[str] = None

    # Request timeout in seconds for outbound HTTP fetches
    crawler_timeout_seconds: int

    # HTTP session retry strategy (urllib3 Retry)
    crawler_http_retry_total: int
    crawler_http_backoff_factor: float

    # Source endpoint URLs (referenced from config.yaml via url_setting / rss_url_setting)
    source_anthropic_url: str
    source_cursor_url: str
    source_github_copilot_url: str
    source_github_copilot_rss_url: str
    source_openai_url: str
    source_openai_rss_url: str
    source_google_deepmind_url: str

    # Port for the liveness probe HTTP server
    health_port: int

    # Port for the Prometheus /metrics HTTP server
    metrics_port: int = 8000


def get_settings() -> Settings:
    """Load and validate settings from the environment.

    Raises pydantic.ValidationError on startup if any value is invalid.
    """
    return Settings()
