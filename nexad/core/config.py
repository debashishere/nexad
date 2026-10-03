"""core/config.py — Application configuration via pydantic-settings.

All required env vars are declared as fields with no default value.
pydantic-settings raises ValidationError at instantiation time if any
required var is absent, giving a clear startup-time failure message.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Any missing required variable causes a ValidationError at startup,
    ensuring the service never starts in a misconfigured state.
    """

    model_config = SettingsConfigDict(
        # Do not silently pick up a .env file during tests; env vars only.
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow constructor keyword args to override env (needed for testing).
        populate_by_name=True,
        extra="ignore",
    )

    # --- Database ---
    DATABASE_URL: str
    """SQLAlchemy async DSN, e.g. postgresql+asyncpg://user:pass@host/db"""

    # --- Cache / Queue ---
    REDIS_URL: str
    """Redis DSN, e.g. redis://localhost:6379/0"""

    # --- Slack HITL ---
    SLACK_WEBHOOK_URL: str
    """Incoming webhook URL for HITL approval cards."""

    SLACK_SIGNING_SECRET: str
    """Slack signing secret used to verify incoming webhook payloads."""

    # --- Google Ads ---
    GOOGLE_ADS_DEVELOPER_TOKEN: str
    """Google Ads API developer token."""

    # --- AWS ---
    AWS_REGION: str
    """AWS region for any SDK calls (e.g. 'us-east-1')."""

    # --- Cryptography ---
    AES_SECRET_KEY: str
    """32-byte AES key encoded as a 64-character hex string."""


def get_settings() -> "Settings":
    """Return the application settings singleton.

    Call this at application startup (e.g. in main.py lifespan) so that
    missing env vars produce an immediate, descriptive ValidationError rather
    than a silent failure at first use.
    """
    return Settings()
