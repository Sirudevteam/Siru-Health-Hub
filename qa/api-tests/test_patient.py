# ==============================================================================
# Siru HealthHub — Patient API Test Suite
# Tests FHIR Patient CRUD operations against the live API
# ==============================================================================

import pytest
import requests
import json
import re
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_url(base_url: str, path: str) -> str:
    """Concatenate base URL and path safely."""
    return base_url.rstrip("/") + "/" + path.lstrip("/")


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



# ---------------------------------------------------------------------------
# Health & Metadata
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_api_health_check(base_url):
    """Validate that the /health endpoint returns HTTP 200 with status 'ok'.

    This is the canary test — if it fails all other tests are meaningless
    because the API is not reachable.
    """
    url = _build_url(base_url, "/health")
    response = requests.get(url, headers=_headers(), timeout=30)

    assert response.status_code == 200, (
        f"Expected 200 from /health, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert body.get("status") == "ok", (
        f"Expected status='ok', got: {body}"
    )


@pytest.mark.smoke
def test_fhir_capability_statement(base_url):
    """Validate that /fhir/metadata returns a valid FHIR CapabilityStatement.

    According to FHIR R4 spec, every server MUST expose a capability statement
    at /metadata with resourceType=CapabilityStatement and fhirVersion=4.0.1.
    """
    url = _build_url(base_url, "/fhir/metadata")
    response = requests.get(url, headers=_headers(), timeout=30)

    assert response.status_code == 200, (
        f"Expected 200 from /fhir/metadata, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert body.get("resourceType") == "CapabilityStatement", (
        f"Expected resourceType=CapabilityStatement, got: {body.get('resourceType')}"
    )
    assert body.get("fhirVersion") == "4.0.1", (
        f"Expected fhirVersion=4.0.1, got: {body.get('fhirVersion')}"
    )


# ---------------------------------------------------------------------------
# CREATE (POST)
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_create_patient_success_201(base_url, sample_patient_data, created_patient_ids):
    """POST /fhir/Patient with a valid FHIR Patient body must return 201 Created.

    Verifies:
    - HTTP 201 status
    - Response body has resourceType=Patient
    - Response body has a non-empty id assigned by the server
    - Response body has meta.lastUpdated set
    - Location header is present pointing to the new resource
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.post(url, json=sample_patient_data, headers=_headers(), timeout=30)

    assert response.status_code == 201, (
        f"Expected 201 Created, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert body.get("resourceType") == "Patient"
    assert body.get("id"), "Response must contain a non-empty 'id'"
    assert body.get("meta", {}).get("lastUpdated"), "meta.lastUpdated must be set"
    assert "Location" in response.headers, "Location header must be present on 201"

    created_patient_ids.append(body["id"])


def test_create_patient_returns_fhir_meta(base_url, sample_patient_data, created_patient_ids):
    """POST /fhir/Patient must return FHIR meta block with versionId and lastUpdated.

    FHIR R4 requires servers to populate meta.versionId and meta.lastUpdated
    on every created/updated resource.
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.post(url, json=sample_patient_data, headers=_headers(), timeout=30)

    assert response.status_code == 201
    body = response.json()
    meta = body.get("meta", {})
    assert meta.get("versionId"), "meta.versionId must be populated on creation"
    assert meta.get("lastUpdated"), "meta.lastUpdated must be populated on creation"

    created_patient_ids.append(body["id"])


# ---------------------------------------------------------------------------
# READ (GET by ID)
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_get_patient_by_id_200(base_url, sample_patient_data, created_patient_ids):
    """GET /fhir/Patient/{id} for a known patient must return 200 with correct data.

    Verifies the round-trip: create a patient, immediately fetch it by the
    server-assigned ID and confirm the family name matches.
    """
    # Create
    create_url = _build_url(base_url, "/fhir/Patient")
    create_resp = requests.post(create_url, json=sample_patient_data, headers=_headers(), timeout=30)
    assert create_resp.status_code == 201
    patient_id = create_resp.json()["id"]
    created_patient_ids.append(patient_id)

    # Read
    get_url = _build_url(base_url, f"/fhir/Patient/{patient_id}")
    response = requests.get(get_url, headers=_headers(), timeout=30)

    assert response.status_code == 200, (
        f"Expected 200 for GET /fhir/Patient/{patient_id}, got {response.status_code}"
    )
    body = response.json()
    assert body.get("resourceType") == "Patient"
    assert body.get("id") == patient_id
    # Verify family name persisted
    expected_family = sample_patient_data["name"][0]["family"]
    actual_family = body["name"][0]["family"]
    assert actual_family == expected_family, (
        f"Family name mismatch: expected {expected_family!r}, got {actual_family!r}"
    )


def test_get_patient_not_found_404(base_url):
    """GET /fhir/Patient/{nonexistent-id} must return 404 with OperationOutcome.

    The FHIR spec mandates that a server return an OperationOutcome resource
    (not a plain error string) when a resource is not found.
    """
    url = _build_url(base_url, "/fhir/Patient/NONEXISTENT-99999")
    response = requests.get(url, headers=_headers(), timeout=30)

    assert response.status_code == 404, (
        f"Expected 404 for nonexistent patient, got {response.status_code}"
    )
    body = response.json()
    assert body.get("resourceType") == "OperationOutcome", (
        f"Expected OperationOutcome on 404, got: {body.get('resourceType')}"
    )


# ---------------------------------------------------------------------------
# UPDATE (PUT)
# ---------------------------------------------------------------------------

def test_update_patient_200(base_url, sample_patient_data, created_patient_ids):
    """PUT /fhir/Patient/{id} with changed birthDate must return 200 with new data.

    Full-resource update per FHIR R4: the client sends the complete updated
    resource; the server stores it and echoes back the updated version.
    """
    # Create
    create_url = _build_url(base_url, "/fhir/Patient")
    create_resp = requests.post(create_url, json=sample_patient_data, headers=_headers(), timeout=30)
    assert create_resp.status_code == 201
    body = create_resp.json()
    patient_id = body["id"]
    created_patient_ids.append(patient_id)

    # Build update payload
    updated = dict(sample_patient_data)
    updated["id"] = patient_id
    updated["birthDate"] = "2000-12-31"

    # Update
    put_url = _build_url(base_url, f"/fhir/Patient/{patient_id}")
    response = requests.put(put_url, json=updated, headers=_headers(), timeout=30)

    assert response.status_code == 200, (
        f"Expected 200 on PUT, got {response.status_code}: {response.text}"
    )
    updated_body = response.json()
    assert updated_body.get("birthDate") == "2000-12-31", (
        f"Expected updated birthDate=2000-12-31, got {updated_body.get('birthDate')}"
    )


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def test_delete_patient_204(base_url, sample_patient_data):
    """DELETE /fhir/Patient/{id} must return 204 No Content, then GET → 404.

    Validates the full delete lifecycle: resource exists → delete succeeds with
    no body → resource no longer accessible.
    """
    # Create
    create_url = _build_url(base_url, "/fhir/Patient")
    create_resp = requests.post(create_url, json=sample_patient_data, headers=_headers(), timeout=30)
    assert create_resp.status_code == 201
    patient_id = create_resp.json()["id"]

    # Delete
    delete_url = _build_url(base_url, f"/fhir/Patient/{patient_id}")
    del_response = requests.delete(delete_url, headers=_headers(), timeout=30)
    assert del_response.status_code == 204, (
        f"Expected 204 on DELETE, got {del_response.status_code}: {del_response.text}"
    )
    assert del_response.text.strip() == "", "DELETE 204 response must have no body"

    # Verify gone
    get_response = requests.get(delete_url, headers=_headers(), timeout=30)
    assert get_response.status_code == 404, (
        f"Expected 404 after DELETE, got {get_response.status_code}"
    )


# ---------------------------------------------------------------------------
# Negative / Validation Tests
# ---------------------------------------------------------------------------

@pytest.mark.negative
def test_invalid_json_400(base_url):
    """POST /fhir/Patient with a non-JSON body must return 400 or 422.

    The server must reject malformed request bodies gracefully rather than
    crashing or returning 500.
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.post(
        url,
        data="not valid json at all",
        headers=_headers(),
        timeout=30,
    )
    assert response.status_code in (400, 422), (
        f"Expected 400 or 422 for invalid JSON body, got {response.status_code}"
    )


@pytest.mark.negative
@pytest.mark.parametrize(
    "invalid_field,invalid_value,label",
    [
        ("resourceType", "Elephant", "wrong_resource_type"),
        ("gender", "purple", "invalid_gender"),
        ("birthDate", "not-a-date", "invalid_birth_date"),
    ],
)
def test_invalid_field_returns_422(
    base_url, sample_patient_data, invalid_field, invalid_value, label
):
    """POST /fhir/Patient with invalid field values must return 422.

    Covers three cases via parametrize:
    - wrong resourceType ('Elephant') — not a recognised FHIR resource
    - invalid gender ('purple') — not in the allowed AdministrativeGender valueset
    - invalid birthDate ('not-a-date') — not a valid FHIR date string
    """
    payload = dict(sample_patient_data)
    payload[invalid_field] = invalid_value
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    assert response.status_code == 422, (
        f"[{label}] Expected 422 for {invalid_field}={invalid_value!r}, "
        f"got {response.status_code}: {response.text}"
    )


# Keep individual test names for readability / direct reference

@pytest.mark.negative
def test_invalid_resource_type_422(base_url, sample_patient_data):
    """POST /fhir/Patient with resourceType='Elephant' must be rejected with 422."""
    payload = dict(sample_patient_data)
    payload["resourceType"] = "Elephant"
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    assert response.status_code == 422


@pytest.mark.negative
def test_invalid_gender_422(base_url, sample_patient_data):
    """POST /fhir/Patient with gender='purple' must be rejected with 422."""
    payload = dict(sample_patient_data)
    payload["gender"] = "purple"
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    assert response.status_code == 422


@pytest.mark.negative
def test_invalid_birth_date_422(base_url, sample_patient_data):
    """POST /fhir/Patient with birthDate='not-a-date' must be rejected with 422."""
    payload = dict(sample_patient_data)
    payload["birthDate"] = "not-a-date"
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_search_patients_returns_bundle(base_url):
    """GET /fhir/Patient (no params) must return a FHIR Bundle with total and entry.

    The bundle may be empty but must still be a well-formed FHIR Bundle resource.
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.get(url, headers=_headers(), timeout=30)

    assert response.status_code == 200
    body = response.json()
    assert body.get("resourceType") == "Bundle", (
        f"Expected Bundle, got {body.get('resourceType')}"
    )
    assert "total" in body, "Bundle must include 'total' field"
    # 'entry' key may be absent when total==0; that is allowed by FHIR spec
    if body["total"] > 0:
        assert "entry" in body, "Bundle with total>0 must include 'entry'"


def test_search_by_name(base_url, created_patient_ids):
    """GET /fhir/Patient?name=Searchable must return bundle containing the matching patient.

    Creates a patient with family='Searchable', then queries by that name and
    confirms the bundle contains at least one entry with the expected name.
    """
    payload = {
        "resourceType": "Patient",
        "name": [{"use": "official", "family": "Searchable", "given": ["Test"]}],
        "gender": "female",
        "birthDate": "1992-03-20",
    }
    create_url = _build_url(base_url, "/fhir/Patient")
    create_resp = requests.post(create_url, json=payload, headers=_headers(), timeout=30)
    assert create_resp.status_code == 201
    created_patient_ids.append(create_resp.json()["id"])

    search_url = _build_url(base_url, "/fhir/Patient")
    response = requests.get(search_url, params={"name": "Searchable"}, headers=_headers(), timeout=30)
    assert response.status_code == 200
    body = response.json()
    assert body.get("total", 0) >= 1, "Search by name should return at least one result"
    entries = body.get("entry", [])
    families = [
        name["family"]
        for e in entries
        for name in e.get("resource", {}).get("name", [])
        if "family" in name
    ]
    assert "Searchable" in families, (
        f"Expected 'Searchable' in results, got families: {families}"
    )


def test_search_by_gender(base_url):
    """GET /fhir/Patient?gender=male must return only male patients.

    Validates that the server-side gender filter is applied correctly and that
    no other genders leak into the result set.
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.get(url, params={"gender": "male"}, headers=_headers(), timeout=30)
    assert response.status_code == 200
    body = response.json()
    entries = body.get("entry", [])
    for entry in entries:
        patient = entry.get("resource", {})
        assert patient.get("gender") == "male", (
            f"Gender filter returned non-male patient: id={patient.get('id')}, "
            f"gender={patient.get('gender')}"
        )


def test_search_pagination_count(base_url):
    """GET /fhir/Patient?_count=1 must return a bundle with at most 1 entry.

    Verifies that the _count search parameter restricts the page size.
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.get(url, params={"_count": "1"}, headers=_headers(), timeout=30)
    assert response.status_code == 200
    body = response.json()
    entries = body.get("entry", [])
    assert len(entries) <= 1, (
        f"Expected at most 1 entry with _count=1, got {len(entries)}"
    )


def test_search_empty_result(base_url):
    """GET /fhir/Patient?name=ZZZ_NONEXISTENT_NAME_XYZ must return total=0.

    Confirms that searches with no matches return an empty Bundle (not 404).
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.get(
        url,
        params={"name": "ZZZ_NONEXISTENT_NAME_XYZ"},
        headers=_headers(),
        timeout=30,
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("total") == 0, (
        f"Expected total=0 for non-existent name, got total={body.get('total')}"
    )
    # entry key may be absent when total is 0
    entries = body.get("entry", [])
    assert len(entries) == 0, f"Expected no entries, got {len(entries)}"


# ---------------------------------------------------------------------------
# Content-Type & HTTP Method Tests
# ---------------------------------------------------------------------------

def test_fhir_content_type_header(base_url):
    """GET /fhir/Patient response Content-Type must indicate FHIR or JSON.

    FHIR servers should return 'application/fhir+json' or at minimum
    'application/json' to signal machine-readable structured data.
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.get(url, headers=_headers(), timeout=30)
    assert response.status_code == 200
    content_type = response.headers.get("Content-Type", "")
    assert "json" in content_type.lower() or "fhir" in content_type.lower(), (
        f"Expected JSON content-type, got: {content_type!r}"
    )


@pytest.mark.negative
def test_wrong_http_method_405(base_url):
    """PATCH /fhir/Patient (collection URL) must return 405 Method Not Allowed.

    PATCH is not defined on the collection endpoint; the server must reject it
    with 405 and ideally include an Allow header listing valid methods.
    """
    url = _build_url(base_url, "/fhir/Patient")
    response = requests.patch(url, json={}, headers=_headers(), timeout=30)
    assert response.status_code == 405, (
        f"Expected 405 Method Not Allowed for PATCH on collection, got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# Data Integrity
# ---------------------------------------------------------------------------

@pytest.mark.regression
def test_data_integrity(base_url, created_patient_ids):
    """Round-trip data integrity: POST then GET must return identical field values.

    Creates a patient with known, specific birthDate (1995-05-10) and family
    name (TestIntegrity), then GETs by the assigned ID and asserts exact equality.
    This protects against silent data corruption or field-level truncation.
    """
    payload = {
        "resourceType": "Patient",
        "name": [{"use": "official", "family": "TestIntegrity", "given": ["Integrity"]}],
        "gender": "male",
        "birthDate": "1995-05-10",
    }
    create_url = _build_url(base_url, "/fhir/Patient")
    create_resp = requests.post(create_url, json=payload, headers=_headers(), timeout=30)
    assert create_resp.status_code == 201
    patient_id = create_resp.json()["id"]
    created_patient_ids.append(patient_id)

    get_url = _build_url(base_url, f"/fhir/Patient/{patient_id}")
    get_resp = requests.get(get_url, headers=_headers(), timeout=30)
    assert get_resp.status_code == 200
    body = get_resp.json()

    assert body.get("birthDate") == "1995-05-10", (
        f"Data integrity failure: birthDate expected '1995-05-10', got {body.get('birthDate')!r}"
    )
    assert body["name"][0]["family"] == "TestIntegrity", (
        f"Data integrity failure: family expected 'TestIntegrity', "
        f"got {body['name'][0]['family']!r}"
    )
