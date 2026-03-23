"""Simple retry wrapper."""

from __future__ import annotations

import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


def retry(
    func: Callable[[], bool],
    max_retries: int = 3,
    delay_seconds: int = 10,
) -> bool:
    """Retry a function up to max_retries times with delay between attempts."""
    for attempt in range(1, max_retries + 1):
        if func():
            return True
        if attempt < max_retries:
            logger.warning("Attempt %d/%d failed, retrying in %ds...", attempt, max_retries, delay_seconds)
            time.sleep(delay_seconds)
    logger.error("All %d attempts failed", max_retries)
    return False
