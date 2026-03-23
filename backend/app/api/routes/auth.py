"""Authentication routes — mock SSO login for development."""
from __future__ import annotations

import hashlib
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.core.auth import create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ── Mock SSO user store (replace with real LDAP / SAML / OIDC in production) ──
MOCK_USERS = {
    "phani": {
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "display_name": "Phani Kumar",
        "email": "phani.kumar@company.com",
        "role": "admin",
    },
    "john.doe": {
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "display_name": "John Doe",
        "email": "john.doe@company.com",
        "role": "viewer",
    },
    "admin": {
        "password_hash": hashlib.sha256("admin".encode()).hexdigest(),
        "display_name": "Admin User",
        "email": "admin@company.com",
        "role": "admin",
    },
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserInfo(BaseModel):
    username: str
    display_name: str
    email: str
    role: str


def get_current_user(request: Request) -> dict:
    """Extract and validate the Bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header[7:]
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    user = MOCK_USERS.get(body.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if hashlib.sha256(body.password.encode()).hexdigest() != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "sub": body.username,
        "display_name": user["display_name"],
        "email": user["email"],
        "role": user["role"],
    }
    token = create_access_token(token_data)
    return LoginResponse(
        access_token=token,
        user={
            "username": body.username,
            "display_name": user["display_name"],
            "email": user["email"],
            "role": user["role"],
        },
    )


@router.get("/me", response_model=UserInfo)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserInfo(
        username=current_user["sub"],
        display_name=current_user["display_name"],
        email=current_user["email"],
        role=current_user["role"],
    )


@router.post("/logout")
def logout():
    """Client-side logout — just acknowledge. Token invalidation is client-side."""
    return {"message": "Logged out successfully"}
