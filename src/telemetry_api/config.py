"""Runtime configuration, read from environment variables.

    DATABASE_URL   SQLAlchemy URL (default: local SQLite file)
    API_KEY        if set, write endpoints require a matching X-API-Key header;
                   if unset, the API is open (handy for local dev and tests)
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_key: str | None


def get_settings() -> Settings:
    # read fresh from the environment each call so tests can override it
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./telemetry.db"),
        api_key=os.environ.get("API_KEY") or None,
    )
