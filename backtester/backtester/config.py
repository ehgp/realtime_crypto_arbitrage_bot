"""Backtester Worker environment configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings sourced exclusively from environment variables."""

    worker_database_url: str | None
    environment: str


def load_settings() -> Settings:
    """Load settings and fail fast for missing production requirements."""
    environment = os.getenv("ENVIRONMENT", "development")
    worker_database_url = os.getenv("WORKER_DATABASE_URL")
    if environment == "production" and not worker_database_url:
        raise RuntimeError("Missing required environment variable: WORKER_DATABASE_URL")
    return Settings(worker_database_url, environment)
