"""Minimal Phase 1 Backtester Worker service loop."""

import time

import structlog

from backtester.config import load_settings


def main() -> None:
    """Start the worker and remain available for future job polling."""
    load_settings()
    logger = structlog.get_logger()
    logger.info("backtester_started")
    while True:
        time.sleep(30)


if __name__ == "__main__":
    main()
