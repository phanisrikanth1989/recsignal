#!/usr/bin/env python3
"""
RecSignal Unix Server Monitoring Agent

Collects system metrics and sends them to the backend every 10 seconds (live monitoring).
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone

import yaml

import argparse

from collectors.system_metrics import collect_all
from services.http_client import send_metrics
from services.retry_service import retry

logger = logging.getLogger("recsignal-agent")


def load_config(config_path: str = None) -> dict:
    """Load agent configuration from YAML file."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def setup_logging(log_file: str | None = None) -> None:
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        try:
            handlers.append(logging.FileHandler(log_file))
        except (OSError, PermissionError):
            pass
    logging.basicConfig(level=logging.INFO, format=fmt, datefmt="%Y-%m-%dT%H:%M:%S", handlers=handlers)


def main():
    parser = argparse.ArgumentParser(description="RecSignal Unix Server Monitoring Agent")
    parser.add_argument("--config", default=None, help="Path to config.yaml (e.g. config/config_uat.yaml)")
    args = parser.parse_args()

    config = load_config(args.config)
    setup_logging(config.get("log_file"))

    backend_url = config["backend_url"]
    api_key = config.get("api_key")
    environment = config.get("environment", "prod")
    interval = config.get("interval_seconds", 10)  # 10 seconds default (live monitoring)
    mounts_include = config.get("mounts_include", ["/"])

    logger.info("RecSignal Agent starting (interval=%ds, backend=%s)", interval, backend_url)

    while True:
        try:
            # Collect metrics
            payload = collect_all(mounts_include)
            payload["environment"] = environment
            payload["collected_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(
                "Collected: cpu=%.1f%% mem=%.1f%% disk=%.1f%% load=%.4f mounts=%d",
                payload["cpu_percent"],
                payload["memory_percent"],
                payload["disk_percent_total"],
                payload["load_avg_1m"],
                len(payload["mounts"]),
            )

            # Send with retry
            retry(
                lambda: send_metrics(backend_url, payload, api_key),
                max_retries=3,
                delay_seconds=10,
            )

        except Exception:
            logger.exception("Error in collection cycle")

        logger.info("Sleeping %d seconds until next collection...", interval)
        time.sleep(interval)


if __name__ == "__main__":
    main()
