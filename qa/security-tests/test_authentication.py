# ==============================================================================
# Siru HealthHub — Authentication QA Suite
# Tests OAuth2/JWT login, expired tokens, malformed tokens, and Redis revocation.
# ==============================================================================

import pytest
import requests
import time
from datetime import datetime, timedelta
from jose import jwt

def _url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


@pytest.mark.security
def test_valid_login_returns_jwt_tokens(base_url):
    """Test standard JSON login returns valid access and refresh tokens."""
    res = requests.post(
        _url(base_url, "/auth/login"),
        json={"username": "admin", "password": "admin123"},
        timeout=10
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["role"] == "ADMIN"
    assert body["username"] == "admin"


@pytest.mark.security
def test_invalid_password_returns_401(base_url):
    """Wrong credentials must be rejected with 401 Unauthorized."""
    res = requests.post(
        _url(base_url, "/auth/login"),
        json={"username": "admin", "password": "wrongpassword!"},
        timeout=10
    )
    assert res.status_code == 401
    assert "Invalid" in res.json().get("detail", "")


@pytest.mark.security
def test_missing_auth_header_returns_401(base_url):
    """Protected endpoints require Bearer token, returning 401 when absent."""
    res = requests.get(_url(base_url, "/fhir/Patient/P1001"), timeout=10)
    assert res.status_code == 401
    assert "Missing Bearer token" in res.json().get("detail", "")


@pytest.mark.security
def test_malformed_token_returns_401(base_url):
    """Malformed token string must return 401 Unauthorized."""
    headers = {"Authorization": "Bearer this-is-not-a-valid-jwt-token-string"}
    res = requests.get(_url(base_url, "/fhir/Patient/P1001"), headers=headers, timeout=10)
    assert res.status_code == 401


@pytest.mark.security
def test_expired_token_returns_401(base_url):
    """Tokens with past expiration timestamps must be rejected."""
    # Fabricate a token that expired 10 minutes ago
    expired_payload = {
        "sub": "admin",
        "role": "ADMIN",
        "exp": datetime.utcnow() - timedelta(minutes=10),
        "type": "access"
    }
    expired_token = jwt.encode(expired_payload, "change-me-in-production", algorithm="HS256")
    headers = {"Authorization": f"Bearer {expired_token}"}

    res = requests.get(_url(base_url, "/fhir/Patient/P1001"), headers=headers, timeout=10)
    assert res.status_code == 401
    assert "expired" in res.json().get("detail", "").lower()


@pytest.mark.security
def test_logout_revokes_token_in_redis_instantaneously(base_url):
    """Calling /auth/logout must blacklist token in Redis, rendering it 401 immediately."""
    # 1. Login fresh session
    login_res = requests.post(
        _url(base_url, "/auth/login"),
        json={"username": "nurse.lakshmi", "password": "nurse123"},
        timeout=10
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check token works
    me_res = requests.get(_url(base_url, "/auth/me"), headers=headers, timeout=10)
    assert me_res.status_code == 200

    # 3. Call logout
    logout_res = requests.post(_url(base_url, "/auth/logout"), headers=headers, timeout=10)
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "ok"

    # 4. Attempt to use revoked token -> must fail with 401
    revoked_check = requests.get(_url(base_url, "/auth/me"), headers=headers, timeout=10)
    assert revoked_check.status_code == 401
    assert "revoked" in revoked_check.json().get("detail", "").lower()

