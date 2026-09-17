# ==============================================================================
# Siru HealthHub — Claims Adjudication & RCM Rules QA Suite
# Tests healthcare claims submission, automated payer rules engine,
# Explanation of Benefits (EOB) ClaimResponse math, denial triggers, and RBAC.
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


# ─── 1. Seeded Claims Verification ────────────────────────────────────────────

@pytest.mark.claims
def test_get_seeded_claim_and_response(base_url):
    """Verify seeded claim CLM1001 and adjudicated response CR1001 exist."""
    res_claim = requests.get(_url(base_url, "/fhir/Claim/CLM1001"), headers=_headers(base_url))
    assert res_claim.status_code == 200
    assert res_claim.json()["id"] == "CLM1001"

    res_cr = requests.get(_url(base_url, "/fhir/ClaimResponse/CR1001"), headers=_headers(base_url))
    assert res_cr.status_code == 200
    cr_data = res_cr.json()
    assert cr_data["id"] == "CR1001"
    assert cr_data["outcome"] == "complete"


# ─── 2. Automated Adjudication Engine ─────────────────────────────────────────

@pytest.mark.claims
def test_submit_clean_claim_auto_adjudicates(base_url):
    """Submitting a valid claim automatically generates an approved ClaimResponse."""
    claim_id = f"CLM-TEST-{uuid.uuid4().hex[:6].upper()}"
    claim_payload = {
        "resourceType": "Claim",
        "id": claim_id,
        "status": "active",
        "type": {"coding": [{"code": "professional"}]},
        "use": "claim",
        "patient": {"reference": "Patient/P1001"},
        "provider": {"reference": "Practitioner/PR101"},
        "insurance": [{"sequence": 1, "focal": True, "coverage": {"reference": "Coverage/COV1001"}}],
        "item": [
            {
                "sequence": 1,
                "productOrService": {"coding": [{"code": "99213", "display": "Office Visit"}]},
                "unitPrice": {"value": 1500.0, "currency": "INR"},
                "quantity": {"value": 1}
            }
        ],
        "total": {"value": 1500.0, "currency": "INR"}
    }

    res = requests.post(_url(base_url, "/fhir/Claim"), json=claim_payload, headers=_headers(base_url))
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == claim_id
    assert "_adjudication" in body
    adj = body["_adjudication"]
    assert adj["outcome"] == "complete"
    assert adj["totalBenefit"] == 1350.0   # 90% of 1500
    assert adj["patientCopay"] == 150.0    # 10% of 1500

    # Verify ClaimResponse was saved in DB
    cr_id = adj["claimResponseId"]
    cr_res = requests.get(_url(base_url, f"/fhir/ClaimResponse/{cr_id}"), headers=_headers(base_url))
    assert cr_res.status_code == 200
    cr_body = cr_res.json()
    assert cr_body["outcome"] == "complete"
    assert cr_body["request"]["reference"] == f"Claim/{claim_id}"


@pytest.mark.claims
def test_adjudication_math_integrity(base_url):
    """Verify benefit + copay strictly equals total submitted amount."""
    claim_id = f"CLM-MATH-{uuid.uuid4().hex[:6].upper()}"
    submitted_amt = 4850.50
    claim_payload = {
        "resourceType": "Claim",
        "id": claim_id,
        "status": "active",
        "type": {"coding": [{"code": "professional"}]},
        "use": "claim",
        "patient": {"reference": "Patient/P1001"},
        "provider": {"reference": "Practitioner/PR101"},
        "insurance": [{"sequence": 1, "focal": True, "coverage": {"reference": "Coverage/COV1001"}}],
        "total": {"value": submitted_amt, "currency": "INR"}
    }

    res = requests.post(_url(base_url, "/fhir/Claim"), json=claim_payload, headers=_headers(base_url))
    assert res.status_code == 201
    adj = res.json()["_adjudication"]
    assert round(adj["totalBenefit"] + adj["patientCopay"], 2) == submitted_amt


@pytest.mark.claims
def test_claim_auto_denial_on_expired_coverage(base_url):
    """Claim submitted against cancelled/expired coverage COV_EXPIRED is auto-denied."""
    claim_id = f"CLM-DENY-{uuid.uuid4().hex[:6].upper()}"
    claim_payload = {
        "resourceType": "Claim",
        "id": claim_id,
        "status": "active",
        "type": {"coding": [{"code": "professional"}]},
        "use": "claim",
        "patient": {"reference": "Patient/P1001"},
        "provider": {"reference": "Practitioner/PR101"},
        "insurance": [{"sequence": 1, "focal": True, "coverage": {"reference": "Coverage/COV_EXPIRED"}}],
        "total": {"value": 2500.0, "currency": "INR"}
    }

    res = requests.post(_url(base_url, "/fhir/Claim"), json=claim_payload, headers=_headers(base_url))
    assert res.status_code == 201
    adj = res.json()["_adjudication"]
    assert adj["outcome"] == "error"
    assert adj["totalBenefit"] == 0.0
    assert adj["patientCopay"] == 2500.0
    assert "denied" in adj["disposition"].lower() or "cancelled" in adj["disposition"].lower()


@pytest.mark.claims
@pytest.mark.negative
def test_zero_amount_claim_rejected_422(base_url):
    """Claim with total amount <= 0 must be rejected with 422."""
    claim_payload = {
        "resourceType": "Claim",
        "status": "active",
        "use": "claim",
        "patient": {"reference": "Patient/P1001"},
        "total": {"value": 0.0, "currency": "INR"}
    }
    res = requests.post(_url(base_url, "/fhir/Claim"), json=claim_payload, headers=_headers(base_url))
    assert res.status_code == 422


# ─── 3. RBAC & Role Enforcement on Claims ─────────────────────────────────────

@pytest.mark.claims
@pytest.mark.security
def test_doctor_allowed_to_submit_claim(base_url):
    """Doctor role (doctor.sharma) is authorized to submit billing claims."""
    h = _headers(base_url, "doctor.sharma", "doctor123")
    claim_payload = {
        "resourceType": "Claim",
        "status": "active",
        "use": "claim",
        "patient": {"reference": "Patient/P1001"},
        "provider": {"reference": "Practitioner/PR101"},
        "insurance": [{"sequence": 1, "focal": True, "coverage": {"reference": "Coverage/COV1001"}}],
        "total": {"value": 800.0, "currency": "INR"}
    }
    res = requests.post(_url(base_url, "/fhir/Claim"), json=claim_payload, headers=h)
    assert res.status_code == 201


@pytest.mark.claims
@pytest.mark.security
def test_nurse_forbidden_from_submitting_claim_403(base_url):
    """Nurse role (nurse.lakshmi) is blocked with 403 from submitting billing claims."""
    h = _headers(base_url, "nurse.lakshmi", "nurse123")
    claim_payload = {
        "resourceType": "Claim",
        "status": "active",
        "use": "claim",
        "patient": {"reference": "Patient/P1001"},
        "total": {"value": 500.0, "currency": "INR"}
    }
    res = requests.post(_url(base_url, "/fhir/Claim"), json=claim_payload, headers=h)
    assert res.status_code == 403


@pytest.mark.claims
@pytest.mark.security
def test_patient_forbidden_from_submitting_claim_403(base_url):
    """Patient role (patient.arun) is blocked with 403 from submitting claims."""
    h = _headers(base_url, "patient.arun", "patient123")
    claim_payload = {
        "resourceType": "Claim",
        "status": "active",
        "use": "claim",
        "patient": {"reference": "Patient/P1001"},
        "total": {"value": 500.0, "currency": "INR"}
    }
    res = requests.post(_url(base_url, "/fhir/Claim"), json=claim_payload, headers=h)
    assert res.status_code == 403


@pytest.mark.claims
@pytest.mark.security
def test_patient_can_view_own_claim_and_response_200(base_url):
    """Patient Arun (P1001) can view his own claim and adjudication response."""
    h = _headers(base_url, "patient.arun", "patient123")
    res_claim = requests.get(_url(base_url, "/fhir/Claim/CLM1001"), headers=h)
    assert res_claim.status_code == 200

    res_cr = requests.get(_url(base_url, "/fhir/ClaimResponse/CR1001"), headers=h)
    assert res_cr.status_code == 200


@pytest.mark.claims
@pytest.mark.security
def test_patient_forbidden_from_viewing_other_patient_claims_403(base_url):
    """Patient Arun (P1001) cannot view claims for Priya Devi (P1002)."""
    # Create claim for Priya first
    admin_h = _headers(base_url, "admin", "admin123")
    clm_priya_id = f"CLM-PRIYA-{uuid.uuid4().hex[:4].upper()}"
    requests.post(_url(base_url, "/fhir/Claim"), json={
        "resourceType": "Claim",
        "id": clm_priya_id,
        "status": "active",
        "use": "claim",
        "patient": {"reference": "Patient/P1002"},
        "insurance": [{"sequence": 1, "focal": True, "coverage": {"reference": "Coverage/COV1002"}}],
        "total": {"value": 1200.0, "currency": "INR"}
    }, headers=admin_h)

    # Patient Arun tries to read Priya's claim
    arun_h = _headers(base_url, "patient.arun", "patient123")
    res = requests.get(_url(base_url, f"/fhir/Claim/{clm_priya_id}"), headers=arun_h)
    assert res.status_code == 403

