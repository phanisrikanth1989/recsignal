from __future__ import annotations

from fastapi import Header, HTTPException, Depends
from app.core.config import get_settings, Settings


def verify_api_key(
    x_api_key: str = Header(None),
    settings: Settings = Depends(get_settings),
) -> str:
    """Validate the agent API key header."""
    if settings.AGENT_API_KEY and x_api_key != settings.AGENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key
