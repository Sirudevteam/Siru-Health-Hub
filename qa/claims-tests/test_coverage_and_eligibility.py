# ==============================================================================
# Siru HealthHub — Insurance Coverage & Real-Time Eligibility QA Suite
# Tests FHIR Coverage CRUD, real-time HIPAA 270/271 eligibility verification,
# policy status determination, and patient role access isolation.
# ==============================================================================

import pytest
import requests
import uuid

def _url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


_token_cache = {}

def _get_token(base_url: str, username: str = "admin", password: str = "admin123") -> str:
    if username in _token_cache:
        return _token_cache[username]
    try:
        r = requests.post(f"{base_url.rstrip('/')}/auth/login", json={"username": username, "password": password}, timeout=5)
        if r.status_code == 200:
            token = r.json().get("access_token")
            _token_cache[username] = token
            return token
    except Exception:
        pass
    return ""


def _headers(base_url: str = "http://localhost:8000", role_user: str = "admin", password: str = "admin123") -> dict:
    t = _get_token(base_url, role_user, password)
    h = {"Content-Type": "application/json", "Accept": "application/fhir+json"}
    if t:
        h["Authorization"] = f"Bearer {t}"
    return h


# ─── 1. Coverage Discovery & CRUD ─────────────────────────────────────────────

@pytest.mark.claims
def test_get_seeded_coverages(base_url):
    """Ensure seeded insurance policies are discoverable."""
    res = requests.get(_url(base_url, "/fhir/Coverage?patient=P1001"), headers=_headers(base_url))
    assert res.status_code == 200
    bundle = res.json()
    assert bundle.get("resourceType") == "Bundle"
    assert bundle.get("total", 0) >= 1
    ids = [e["resource"]["id"] for e in bundle.get("entry", [])]
    assert "COV1001" in ids


@pytest.mark.claims
def test_create_and_read_coverage(base_url):
    """Create a new insurance policy and verify by logical ID."""
    cov_id = f"COV-TEST-{uuid.uuid4().hex[:6].upper()}"
    new_cov = {
        "resourceType": "Coverage",
        "id": cov_id,
        "status": "active",
        "subscriberId": "TEST-SUB-99",
        "beneficiary": {"reference": "Patient/P1001"},
        "period": {"start": "2026-01-01", "end": "2026-12-31"},
        "payor": [{"reference": "Organization/ORG_PAYER_1", "display": "Star Health"}],
        "class": [{"type": {"coding": [{"code": "plan"}]}, "name": "Corporate Silver Care"}]
    }

    create_res = requests.post(_url(base_url, "/fhir/Coverage"), json=new_cov, headers=_headers(base_url))
    assert create_res.status_code == 201
    assert create_res.json()["id"] == cov_id

    read_res = requests.get(_url(base_url, f"/fhir/Coverage/{cov_id}"), headers=_headers(base_url))
    assert read_res.status_code == 200
    body = read_res.json()
    assert body["subscriberId"] == "TEST-SUB-99"
    assert body["status"] == "active"


# ─── 2. Real-Time Eligibility Verification (EDI 270/271 Simulation) ──────────

@pytest.mark.claims
def test_real_time_eligibility_check_active(base_url):
    """Verify active policy COV1001 returns eligible=true with benefit details."""
    res = requests.post(
        _url(base_url, "/fhir/Coverage/COV1001/eligibility-check"),
        headers=_headers(base_url)
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("eligible") is True
    assert body.get("status") == "Active Coverage"
    assert body.get("coinsuranceBenefit") == 90
    assert body.get("copayPercent") == 10
    assert body.get("inNetwork") is True
    assert "covered under plan" in body.get("disposition", "").lower()


@pytest.mark.claims
def test_real_time_eligibility_check_expired(base_url):
    """Verify cancelled/expired policy COV_EXPIRED returns eligible=false."""
    res = requests.post(
        _url(base_url, "/fhir/Coverage/COV_EXPIRED/eligibility-check"),
        headers=_headers(base_url)
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("eligible") is False
    assert "terminated" in body.get("disposition", "").lower() or "suspended" in body.get("disposition", "").lower() or "cancelled" in body.get("disposition", "").lower()


# ─── 3. Patient RBAC & Data Isolation ─────────────────────────────────────────

@pytest.mark.claims
@pytest.mark.security
def test_patient_can_view_own_coverage(base_url):
    """Patient Arun (P1001) can view his own insurance policy COV1001."""
    h = _headers(base_url, "patient.arun", "patient123")
    res = requests.get(_url(base_url, "/fhir/Coverage/COV1001"), headers=h)
    assert res.status_code == 200
    assert res.json()["id"] == "COV1001"


@pytest.mark.claims
@pytest.mark.security
def test_patient_forbidden_from_viewing_other_patient_coverage_403(base_url):
    """Patient Arun (P1001) is blocked with 403 when trying to view Priya's policy COV1002."""
    h = _headers(base_url, "patient.arun", "patient123")
    res = requests.get(_url(base_url, "/fhir/Coverage/COV1002"), headers=h)
    assert res.status_code == 403
    assert "forbidden" in res.text.lower() or "only access their own" in res.text.lower()

