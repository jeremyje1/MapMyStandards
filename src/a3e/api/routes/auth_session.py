"""Session-based authentication (Track A) with access + refresh cookies.

Implements:
  POST /api/auth/login { email, password, rememberMe }
  POST /api/auth/logout
  POST /api/auth/refresh
  POST /api/auth/register (simple – email/password only)

Password hashing: argon2 (argon2-cffi) preferred; falls back to bcrypt if needed.
Refresh tokens stored (hashed) in sqlite table auth_refresh_tokens for revocation & rotation.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, Depends, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import sqlite3
import os
import secrets
import hashlib
import logging
from typing import Optional
import jwt  # PyJWT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth-session"])

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("JWT_SECRET_KEY", "dev-secret-change"))
JWT_ALG = "HS256"
ACCESS_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
REFRESH_DAYS_REMEMBER = int(os.getenv("REFRESH_TOKEN_DAYS_REMEMBER", "30"))
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".mapmystandards.ai")

DB_PATH = os.getenv("AUTH_DB_PATH", "a3e_production.db")


def _conn():
    return sqlite3.connect(DB_PATH)


def _init_tables():
    try:
        c = _conn()
        cur = c.cursor()
        # Users table (id/user_id may already exist elsewhere – keep idempotent)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
            """
        )
        # Refresh tokens
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                revoked INTEGER DEFAULT 0
            )
            """
        )
        c.commit()
        c.close()
    except Exception as e:  # pragma: no cover
        logger.error(f"Auth table init failed: {e}")


_init_tables()


try:
    from argon2 import PasswordHasher  # type: ignore

    _ph = PasswordHasher()

    def hash_password(pw: str) -> str:
        return _ph.hash(pw)

    def verify_password(pw: str, hashed: str) -> bool:
        try:
            return _ph.verify(hashed, pw)
        except Exception:
            return False
except Exception:  # pragma: no cover - fallback
    import bcrypt

    def hash_password(pw: str) -> str:
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    def verify_password(pw: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(pw.encode(), hashed.encode())
        except Exception:
            return False


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: bool = False


class AuthSuccess(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class MeResponse(BaseModel):
    ok: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    exp: Optional[int] = None


def _issue_access_token(user_id: str, email: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=ACCESS_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": int(exp.timestamp()), "iat": int(now.timestamp())}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return token, exp


def _new_refresh_token(user_id: str, days: int) -> tuple[str, datetime]:
    raw = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(days=days)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    rec_id = f"rt_{secrets.token_hex(8)}"
    c = _conn()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO auth_refresh_tokens (id, user_id, token_hash, expires_at) VALUES (?,?,?,?)",
        (rec_id, user_id, token_hash, expires.isoformat()),
    )
    c.commit()
    c.close()
    return raw, expires


def _get_user_by_email(email: str):
    c = _conn()
    cur = c.cursor()
    cur.execute("SELECT user_id, email, password_hash, is_active FROM users WHERE email=?", (email.lower(),))
    row = cur.fetchone()
    c.close()
    if row:
        return {"user_id": row[0], "email": row[1], "password_hash": row[2], "is_active": row[3] == 1}
    return None


def _create_user(email: str, password: str) -> str:
    user_id = f"user_{secrets.token_hex(8)}"
    pw_hash = hash_password(password)
    c = _conn()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO users (id, user_id, email, password_hash) VALUES (?,?,?,?)",
        (user_id, user_id, email.lower(), pw_hash),
    )
    c.commit()
    c.close()
    return user_id


def _set_auth_cookies(resp: Response, access_token: str, access_exp: datetime, refresh_token: str, refresh_exp: datetime):
    secure = True
    # For cross-site requests from platform.mapmystandards.ai to api.mapmystandards.ai
    # we must use SameSite=None and Secure cookies.
    common = {"httponly": True, "secure": secure, "samesite": "none", "domain": COOKIE_DOMAIN, "path": "/"}
    resp.set_cookie("access_token", access_token, expires=access_exp, **common)
    resp.set_cookie("refresh_token", refresh_token, expires=refresh_exp, **common)


@router.post("/register", response_model=AuthSuccess)
async def register(req: RegisterRequest, response: Response):
    if _get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="User already exists")
    user_id = _create_user(req.email, req.password)
    access, aexp = _issue_access_token(user_id, req.email)
    refresh_days = REFRESH_DAYS
    refresh, rexp = _new_refresh_token(user_id, refresh_days)
    _set_auth_cookies(response, access, aexp, refresh, rexp)
    return AuthSuccess(access_token=access, expires_in=ACCESS_MINUTES * 60)


@router.post("/login", response_model=AuthSuccess)
async def login(req: LoginRequest, response: Response):
    # Demo shortcut: enable cookie-based session for demo accounts without DB user
    if req.email.lower() == "demo@example.com" and req.password == "demo123":
        access, aexp = _issue_access_token("demo_user", req.email.lower())
        refresh_days = REFRESH_DAYS_REMEMBER if req.rememberMe else REFRESH_DAYS
        refresh, rexp = _new_refresh_token("demo_user", refresh_days)
        _set_auth_cookies(response, access, aexp, refresh, rexp)
        return AuthSuccess(access_token=access, expires_in=ACCESS_MINUTES * 60)

    user = _get_user_by_email(req.email)
    if not user or not user["is_active"] or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access, aexp = _issue_access_token(user["user_id"], user["email"])
    refresh_days = REFRESH_DAYS_REMEMBER if req.rememberMe else REFRESH_DAYS
    refresh, rexp = _new_refresh_token(user["user_id"], refresh_days)
    _set_auth_cookies(response, access, aexp, refresh, rexp)
    return AuthSuccess(access_token=access, expires_in=ACCESS_MINUTES * 60)


class RefreshRequest(BaseModel):
    # Allow body or cookie usage; body optional
    refresh_token: Optional[str] = None


@router.post("/refresh", response_model=AuthSuccess)
async def refresh(request: Request, response: Response, body: Optional[RefreshRequest] = None):
    token = (body.refresh_token if body else None) or request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    c = _conn()
    cur = c.cursor()
    cur.execute(
        "SELECT id, user_id, expires_at, revoked FROM auth_refresh_tokens WHERE token_hash=?",
        (token_hash,),
    )
    row = cur.fetchone()
    if not row:
        c.close()
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    rec_id, user_id, expires_at, revoked = row
    if revoked == 1:
        c.close()
        raise HTTPException(status_code=401, detail="Token revoked")
    if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
        c.close()
        raise HTTPException(status_code=401, detail="Token expired")
    # Rotate: revoke old
    cur.execute("UPDATE auth_refresh_tokens SET revoked=1 WHERE id=?", (rec_id,))
    c.commit()
    c.close()
    # Need user email
    c2 = _conn()
    cur2 = c2.cursor()
    cur2.execute("SELECT email FROM users WHERE user_id=?", (user_id,))
    user_row = cur2.fetchone()
    c2.close()
    if not user_row:
        raise HTTPException(status_code=401, detail="User missing")
    email = user_row[0]
    access, aexp = _issue_access_token(user_id, email)
    # Use standard refresh life (don't auto-upgrade to remember)
    refresh_new, rexp = _new_refresh_token(user_id, REFRESH_DAYS)
    _set_auth_cookies(response, access, aexp, refresh_new, rexp)
    return AuthSuccess(access_token=access, expires_in=ACCESS_MINUTES * 60)


@router.post("/logout")
async def logout(response: Response, request: Request):
    # Best effort revoke refresh token provided in cookie
    token = request.cookies.get("refresh_token")
    if token:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            c = _conn()
            cur = c.cursor()
            cur.execute("UPDATE auth_refresh_tokens SET revoked=1 WHERE token_hash=?", (token_hash,))
            c.commit()
            c.close()
        except Exception:  # pragma: no cover
            pass
    for name in ("access_token", "refresh_token"):
        response.delete_cookie(name, domain=COOKIE_DOMAIN, path="/")
    return {"success": True}


@router.get("/me", response_model=MeResponse)
async def me(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return MeResponse(ok=False)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return MeResponse(ok=True, user_id=str(payload.get("sub")), email=payload.get("email"), exp=payload.get("exp"))
    except Exception:
        return MeResponse(ok=False)
