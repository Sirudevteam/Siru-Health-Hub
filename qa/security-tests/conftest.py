import pytest
import requests

def _get_token(base_url: str, username: str, password: str) -> str:
    url = f"{base_url.rstrip('/')}/auth/login"
    res = requests.post(url, json={"username": username, "password": password}, timeout=10)
    assert res.status_code == 200, f"Failed to login as {username}: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token(base_url: str) -> str:
    return _get_token(base_url, "admin", "admin123")


@pytest.fixture(scope="session")
def doctor_token(base_url: str) -> str:
    return _get_token(base_url, "doctor.sharma", "doctor123")


@pytest.fixture(scope="session")
def nurse_token(base_url: str) -> str:
    return _get_token(base_url, "nurse.lakshmi", "nurse123")


@pytest.fixture(scope="session")
def patient_token(base_url: str) -> str:
    return _get_token(base_url, "patient.arun", "patient123")


@pytest.fixture
def auth_header():
    def _header(token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/fhir+json"
        }
    return _header

