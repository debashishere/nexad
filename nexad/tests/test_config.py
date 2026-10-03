"""Tests for core/config.py — seam S1: Settings validation.

Spec (issue 01):
  core/config.py uses pydantic-settings BaseSettings to load required env vars.
  Missing vars raise ValidationError at startup.

Required vars:
  DATABASE_URL, REDIS_URL, SLACK_WEBHOOK_URL, SLACK_SIGNING_SECRET,
  GOOGLE_ADS_DEVELOPER_TOKEN, AWS_REGION, AES_SECRET_KEY (32-byte hex)
"""

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ALL_REQUIRED = {
    "DATABASE_URL": "postgresql+asyncpg://nexad:nexad@localhost:5432/nexad",
    "REDIS_URL": "redis://localhost:6379/0",
    "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/T000/B000/xxxx",
    "SLACK_SIGNING_SECRET": "slack_signing_secret_example",
    "GOOGLE_ADS_DEVELOPER_TOKEN": "google_ads_dev_token_example",
    "AWS_REGION": "us-east-1",
    # 32 bytes = 64 hex chars
    "AES_SECRET_KEY": "a" * 64,
}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove all NexAd env vars from the real process env before each test.

    pydantic-settings reads from both the real env AND constructor kwargs.
    Without this, leftover vars from the developer's shell could make a
    'missing var' test pass even when the var is absent from kwargs.
    """
    for key in ALL_REQUIRED:
        monkeypatch.delenv(key, raising=False)


def _make_settings(overrides: dict | None = None):
    """Instantiate Settings, passing the given dict as constructor kwargs."""
    from nexad.core.config import Settings

    return Settings(**(overrides or {}))


# ---------------------------------------------------------------------------
# S1-A: Happy path — all required vars present
# ---------------------------------------------------------------------------


def test_settings_loads_all_required_vars():
    """Settings instantiates without error when all required env vars are present."""
    settings = _make_settings(ALL_REQUIRED)

    assert settings.DATABASE_URL == ALL_REQUIRED["DATABASE_URL"]
    assert settings.REDIS_URL == ALL_REQUIRED["REDIS_URL"]
    assert settings.SLACK_WEBHOOK_URL == ALL_REQUIRED["SLACK_WEBHOOK_URL"]
    assert settings.SLACK_SIGNING_SECRET == ALL_REQUIRED["SLACK_SIGNING_SECRET"]
    assert settings.GOOGLE_ADS_DEVELOPER_TOKEN == ALL_REQUIRED["GOOGLE_ADS_DEVELOPER_TOKEN"]
    assert settings.AWS_REGION == ALL_REQUIRED["AWS_REGION"]
    assert settings.AES_SECRET_KEY == ALL_REQUIRED["AES_SECRET_KEY"]


# ---------------------------------------------------------------------------
# S1-B: Missing var → ValidationError (fail-fast contract)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_var", list(ALL_REQUIRED.keys()))
def test_settings_raises_on_missing_required_var(missing_var):
    """Settings raises pydantic ValidationError when any single required var is absent."""
    env_without_var = {k: v for k, v in ALL_REQUIRED.items() if k != missing_var}

    with pytest.raises(ValidationError):
        _make_settings(env_without_var)
