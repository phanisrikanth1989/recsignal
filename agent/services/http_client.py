"""HTTP client for sending metrics to backend."""

from __future__ import annotations

import logging
import requests

logger = logging.getLogger(__name__)


def send_metrics(backend_url: str, payload: dict, api_key: str | None = None, timeout: int = 30) -> bool:
    """Send metrics payload to backend. Returns True on success."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        resp = requests.post(backend_url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        logger.info("Metrics sent successfully: %s", resp.json())
        return True
    except requests.exceptions.RequestException as e:
        logger.error("Failed to send metrics: %s", e)
        return False
