"""Run: server/.venv/Scripts/python.exe server/test_auth.py

Regression tests for the login -> /api/me flow. The deployed client sends the token
from the login body as a Bearer header; the cookie path still works same-site.
"""

import os
from datetime import datetime, timedelta, timezone

# COOKIE_SECURE=1 drops the cookie in TestClient because it talks plain http.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/brokerdesk_test"
)
os.environ["COOKIE_SECURE"] = "0"

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from auth import PASSWORD, SECRET  # noqa: E402


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main_test() -> None:
    with TestClient(main.app) as c:
        assert c.get("/api/me").status_code == 401, "no credentials must be rejected"
        assert c.post("/api/login", json={"password": "wrong"}).status_code == 401

        res = c.post("/api/login", json={"password": PASSWORD})
        assert res.status_code == 200, res.text
        token = res.json().get("token")
        assert token, "login must return a token for the cross-site client"

        # the actual bug: cookie is not sent cross-site, header must work
        r = c.get("/api/me", headers=bearer(token))
        assert r.status_code == 200 and r.json() == {"user": "broker"}, r.text

        # same-site cookie path still works
        assert c.get("/api/me").status_code == 200

        assert c.get("/api/me", headers=bearer("garbage")).status_code == 401
        c.cookies.clear()
        assert c.get("/api/me", cookies={"bd_session": "garbage"}).status_code == 401

        expired = jwt.encode(
            {"sub": "broker", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            SECRET,
            algorithm="HS256",
        )
        assert c.get("/api/me", headers=bearer(expired)).status_code == 401
        wrong_claim = jwt.encode(
            {"sub": "someone", "exp": datetime.now(timezone.utc) + timedelta(days=1)},
            SECRET,
            algorithm="HS256",
        )
        assert c.get("/api/me", headers=bearer(wrong_claim)).status_code == 401

        c.cookies.clear()
        assert c.get("/api/me", headers=bearer(token), cookies={"bd_session": "stale"}).status_code == 200, (
            "a stale cookie must not shadow a valid bearer token"
        )

        # logout clears the cookie
        assert c.post("/api/login", json={"password": PASSWORD}).status_code == 200
        assert c.get("/api/me").status_code == 200
        assert c.post("/api/logout").status_code == 200
        assert c.get("/api/me").status_code == 401, "logout must clear the cookie"
    print("ALL AUTH CHECKS PASSED")


if __name__ == "__main__":
    main_test()
