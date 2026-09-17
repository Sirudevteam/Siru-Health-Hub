# ==============================================================================
# Siru HealthHub — FHIR Compliance Test Suite
# Validates that API responses conform to the FHIR R4 resource specification
# using the fhir.resources library for structural validation.
# ==============================================================================

import re
import pytest
import requests
from fhir.resources.patient import Patient
from fhir.resources.bundle import Bundle
from fhir.resources.operationoutcome import OperationOutcome
from fhir.resources.capabilitystatement import CapabilityStatement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _validate_fhir(model_cls, data):
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    elif hasattr(model_cls, "parse_obj"):
        return model_cls.parse_obj(data)
    return model_cls(**data)


_admin_token_cache = None


def _headers(base_url: str = "http://localhost:8000") -> dict:
    global _admin_token_cache
    if not _admin_token_cache:
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=5,
            )
            if r.status_code == 200:
                _admin_token_cache = r.json().get("access_token")
        except Exception:
            pass
    h = {
        "Content-Type": "application/json",
        "Accept": "application/fhir+json",
    }
    if _admin_token_cache:
        h["Authorization"] = f"Bearer {_admin_token_cache}"
    return h



_SAMPLE_PATIENT = {
    "resourceType": "Patient",
    "name": [{"use": "official", "family": "Compliance", "given": ["Test"]}],
    "gender": "male",
    "birthDate": "1995-05-10",
}


# ---------------------------------------------------------------------------
# FHIR Resource Validation
# ---------------------------------------------------------------------------

@pytest.mark.fhir
def test_patient_resource_validates_against_fhir_spec(base_url, created_patient_ids):
    """Create a patient and validate the returned JSON against the FHIR R4 Patient spec.

    Uses fhir.resources Patient.model_validate() which raises ValidationError if
    the structure violates the FHIR specification. A clean parse confirms the
    server emits spec-compliant JSON.
    """
    # Create
    resp = requests.post(
        _url(base_url, "/fhir/Patient"),
        json=_SAMPLE_PATIENT,
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 201, f"Create failed: {resp.status_code} {resp.text}"
    patient_id = resp.json()["id"]
    created_patient_ids.append(patient_id)

    # Fetch by ID
    get_resp = requests.get(
        _url(base_url, f"/fhir/Patient/{patient_id}"),
        headers=_headers(),
        timeout=30,
    )
    assert get_resp.status_code == 200

    # Validate against FHIR R4 spec — must not raise
    patient_obj = _validate_fhir(Patient, get_resp.json())
    assert patient_obj is not None


@pytest.mark.fhir
def test_bundle_validates_against_fhir_spec(base_url):
    """GET /fhir/Patient and validate the response Bundle against the FHIR R4 spec.

    A search result set MUST be wrapped in a Bundle resource. Parsing with
    Bundle.model_validate() confirms the server's Bundle is spec-compliant.
    """
    resp = requests.get(
        _url(base_url, "/fhir/Patient"),
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 200

    bundle_obj = _validate_fhir(Bundle, resp.json())
    assert bundle_obj is not None


@pytest.mark.fhir
def test_capability_statement_validates(base_url):
    """GET /fhir/metadata and validate the CapabilityStatement against FHIR R4 spec.

    The FHIR conformance resource must itself be parseable by fhir.resources.
    """
    resp = requests.get(
        _url(base_url, "/fhir/metadata"),
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 200

    cs_obj = _validate_fhir(CapabilityStatement, resp.json())
    assert cs_obj is not None


@pytest.mark.fhir
def test_patient_required_fields_present(base_url, created_patient_ids):
    """Created patient response must contain resourceType, id, and meta.

    These are the three mandatory server-managed fields for any FHIR resource.
    Their absence indicates a server-side serialization bug.
    """
    resp = requests.post(
        _url(base_url, "/fhir/Patient"),
        json=_SAMPLE_PATIENT,
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 201
    body = resp.json()
    patient_id = body.get("id")
    created_patient_ids.append(patient_id)

    get_resp = requests.get(
        _url(base_url, f"/fhir/Patient/{patient_id}"),
        headers=_headers(),
        timeout=30,
    )
    assert get_resp.status_code == 200
    fetched = get_resp.json()

    assert fetched.get("resourceType") == "Patient", "resourceType must be 'Patient'"
    assert fetched.get("id") not in (None, ""), "id must be non-empty"
    assert fetched.get("meta") is not None, "meta block must be present"


@pytest.mark.fhir
def test_patient_gender_is_valid_fhir_code(base_url, created_patient_ids):
    """Patient gender must be one of the FHIR R4 AdministrativeGender codes.

    FHIR restricts gender to the set [male, female, other, unknown]. Any other
    value would indicate a valueset binding violation.
    """
    valid_genders = {"male", "female", "other", "unknown"}
    resp = requests.post(
        _url(base_url, "/fhir/Patient"),
        json=_SAMPLE_PATIENT,
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 201
    patient_id = resp.json()["id"]
    created_patient_ids.append(patient_id)

    get_resp = requests.get(
        _url(base_url, f"/fhir/Patient/{patient_id}"),
        headers=_headers(),
        timeout=30,
    )
    assert get_resp.status_code == 200
    gender = get_resp.json().get("gender")
    assert gender in valid_genders, (
        f"gender={gender!r} is not a valid FHIR AdministrativeGender code. "
        f"Must be one of {valid_genders}"
    )


@pytest.mark.fhir
def test_patient_birth_date_format(base_url, created_patient_ids):
    """Patient birthDate must match the FHIR date format YYYY-MM-DD.

    FHIR dates are restricted to ISO 8601 partial dates. The most specific
    form (YYYY-MM-DD) is verified here via regex.
    """
    resp = requests.post(
        _url(base_url, "/fhir/Patient"),
        json=_SAMPLE_PATIENT,
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 201
    patient_id = resp.json()["id"]
    created_patient_ids.append(patient_id)

    get_resp = requests.get(
        _url(base_url, f"/fhir/Patient/{patient_id}"),
        headers=_headers(),
        timeout=30,
    )
    assert get_resp.status_code == 200
    birth_date = get_resp.json().get("birthDate", "")
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    assert pattern.match(birth_date), (
        f"birthDate={birth_date!r} does not match YYYY-MM-DD format"
    )


@pytest.mark.fhir
def test_operation_outcome_on_not_found(base_url):
    """GET /fhir/Patient/{nonexistent-id} must return a valid FHIR OperationOutcome.

    Error responses from a FHIR server must themselves be valid FHIR resources.
    Parsing the 404 body with OperationOutcome.model_validate() proves this.
    """
    resp = requests.get(
        _url(base_url, "/fhir/Patient/DOES-NOT-EXIST-FHIR-TEST"),
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 404
    oo = _validate_fhir(OperationOutcome, resp.json())
    assert oo is not None
    assert len(oo.issue) >= 1, "OperationOutcome must have at least one issue"
