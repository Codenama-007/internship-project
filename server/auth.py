import hmac
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import Cookie, HTTPException, Response

load_dotenv(Path(__file__).resolve().parent / ".env")

# shortcut: dev secret fallback + plaintext password in .env, for single-admin local demo;
# replace with a hashed password + forced SECRET_KEY before any real deployment.
SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me-only-for-local-demos-0123456789")
PASSWORD = os.getenv("BROKER_PASSWORD", "broker123")
COOKIE = "bd_session"
MAX_AGE = 7 * 24 * 3600


def check_password(candidate: str) -> bool:
    return hmac.compare_digest(candidate, PASSWORD)


def issue_token() -> str:
    return jwt.encode(
        {"sub": "broker", "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        SECRET,
        algorithm="HS256",
    )


def is_valid(token: str | None) -> bool:
    if not token:
        return False
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])["sub"] == "broker"
    except jwt.PyJWTError:
        return False


def set_session(response: Response) -> None:
    response.set_cookie(
        COOKIE, issue_token(), httponly=True, samesite="lax", max_age=MAX_AGE, path="/"
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/")


def current_user(bd_session: str | None = Cookie(default=None)) -> str:
    """Depends() guard: every admin route re-verifies the JWT, not just the proxy."""
    if not is_valid(bd_session):
        raise HTTPException(status_code=401, detail="Not logged in")
    return "broker"
