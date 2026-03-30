"""
Centralized application configuration.

Loads settings from environment variables and .env file.
All configurable values are defined here to avoid scattered env access.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "sqlite:///./nuria.db"

    # --- OpenRouter ---
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout: int = 30  # seconds


# Singleton instance used across the application
settings = Settings()
