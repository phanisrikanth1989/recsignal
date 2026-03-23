"""JWT token utilities for SSO-style authentication."""
from __future__ import annotations

import hashlib
import hmac
import json
import base64
import time
from typing import Optional

from app.core.config import get_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 28800  # 8 hours


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_access_token(data: dict, expires_seconds: int = ACCESS_TOKEN_EXPIRE_SECONDS) -> str:
    settings = get_settings()
    header = _b64url_encode(json.dumps({"alg": ALGORITHM, "typ": "JWT"}).encode())
    payload_data = {**data, "exp": int(time.time()) + expires_seconds}
    payload = _b64url_encode(json.dumps(payload_data).encode())
    signature = hmac.new(settings.SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    sig = _b64url_encode(signature)
    return f"{header}.{payload}.{sig}"


def decode_access_token(token: str) -> Optional[dict]:
    settings = get_settings()
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected = hmac.new(settings.SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        actual = _b64url_decode(sig)
        if not hmac.compare_digest(expected, actual):
            return None
        data = json.loads(_b64url_decode(payload))
        if data.get("exp", 0) < time.time():
            return None
        return data
    except Exception:
        return None
