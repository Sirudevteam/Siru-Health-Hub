# ==============================================================================
# Siru HealthHub — Root QA conftest
# Provides session-level fixtures shared across all test modules
# ==============================================================================

import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the base URL of the API under test."""
    return os.getenv("BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def admin_token(base_url: str) -> str:
    """Acquire admin JWT token for authenticated testing."""
    try:
        url = f"{base_url.rstrip('/')}/auth/login"
        res = requests.post(url, json={"username": "admin", "password": "admin123"}, timeout=10)
        if res.status_code == 200:
            return res.json().get("access_token", "")
    except Exception:
        pass
    return ""


@pytest.fixture(scope="session")
def api_client(base_url: str, admin_token: str) -> requests.Session:
    """Return a configured requests Session pointed at base_url with Admin JWT."""
    session = requests.Session()
    session.headers.update(
        {
            "Content-Type": "application/json",
            "Accept": "application/fhir+json",
        }
    )
    if admin_token:
        session.headers["Authorization"] = f"Bearer {admin_token}"

    session.base_url = base_url  # type: ignore[attr-defined]
    # Monkey-patch request so callers can use relative paths
    _original_request = session.request

    def _patched_request(method, url, **kwargs):
        if not url.startswith("http"):
            url = base_url.rstrip("/") + "/" + url.lstrip("/")
        kwargs.setdefault("timeout", 30)
        return _original_request(method, url, **kwargs)

    session.request = _patched_request  # type: ignore[method-assign]
    return session


@pytest.fixture
def sample_patient_data() -> dict:
    """Return a valid FHIR R4 Patient resource dict for use in tests."""
    return {
        "resourceType": "Patient",
        "name": [
            {
                "use": "official",
                "family": "Kumar",
                "given": ["Siru"],
            }
        ],
        "gender": "male",
        "birthDate": "1990-01-15",
        "telecom": [
            {
                "system": "phone",
                "value": "+91-9000000001",
                "use": "mobile",
            }
        ],
        "address": [
            {
                "use": "home",
                "line": ["123 Health Street"],
                "city": "Chennai",
                "state": "Tamil Nadu",
                "postalCode": "600001",
                "country": "IN",
            }
        ],
    }


@pytest.fixture(scope="session")
def created_patient_ids() -> list:
    """Session-scoped list that accumulates IDs of patients created during the
    test run so that teardown can delete them automatically."""
    ids: list = []
    yield ids
    # Teardown: attempt to delete every tracked patient
    # NOTE: requires base_url & session — build a fresh one for cleanup
    cleanup_url = os.getenv("BASE_URL", "http://localhost:8000")
    for pid in ids:
        try:
            requests.delete(
                f"{cleanup_url.rstrip('/')}/fhir/Patient/{pid}",
                timeout=10,
                headers={"Accept": "application/fhir+json"},
            )
        except Exception:  # noqa: BLE001
            pass
