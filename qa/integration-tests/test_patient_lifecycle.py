# ==============================================================================
# Siru HealthHub — Patient Lifecycle Integration Test Suite
# End-to-end tests that exercise the complete Patient CRUD lifecycle in sequence.
# ==============================================================================

import pytest
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url(base_url: str, path: str) -> str:
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
# End-to-End Lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_complete_patient_lifecycle(base_url):
    """Full end-to-end lifecycle: Create → Read → Update → Search → Delete → Verify.

    This is the primary integration test for the Patient resource. It walks
    through every operation in realistic order, ensuring each step succeeds
    and that data flows correctly between them.

    Steps:
        1. POST  — create patient (201)
        2. GET   — read back by ID (200, data matches)
        3. PUT   — update birthDate (200, new value returned)
        4. GET   — verify update persisted (200, updated field shown)
        5. GET?  — search by family name (found in bundle)
        6. DELETE — soft-delete patient (204, no body)
        7. GET   — verify gone (404)
        8. GET?  — verify no longer in search results
    """
    patient_id = None
    family_name = "LifecycleTest"

    payload = {
        "resourceType": "Patient",
        "name": [{"use": "official", "family": family_name, "given": ["E2E"]}],
        "gender": "female",
        "birthDate": "1988-07-22",
        "telecom": [{"system": "phone", "value": "+91-9000000099", "use": "mobile"}],
    }

    # ------------------------------------------------------------------
    # Step 1: Create
    # ------------------------------------------------------------------
    create_resp = requests.post(
        _url(base_url, "/fhir/Patient"),
        json=payload,
        headers=_headers(),
        timeout=30,
    )
    assert create_resp.status_code == 201, (
        f"[Step 1] Create failed: {create_resp.status_code} — {create_resp.text}"
    )
    created = create_resp.json()
    patient_id = created["id"]
    assert patient_id, "[Step 1] Server must assign a non-empty id"

    try:
        # ------------------------------------------------------------------
        # Step 2: Read back
        # ------------------------------------------------------------------
        read_resp = requests.get(
            _url(base_url, f"/fhir/Patient/{patient_id}"),
            headers=_headers(),
            timeout=30,
        )
        assert read_resp.status_code == 200, (
            f"[Step 2] Read failed: {read_resp.status_code} — {read_resp.text}"
        )
        read_body = read_resp.json()
        assert read_body["id"] == patient_id, "[Step 2] ID mismatch"
        assert read_body["name"][0]["family"] == family_name, (
            f"[Step 2] Family name mismatch: {read_body['name'][0]['family']!r}"
        )
        assert read_body["birthDate"] == "1988-07-22", (
            f"[Step 2] birthDate mismatch: {read_body.get('birthDate')!r}"
        )

        # ------------------------------------------------------------------
        # Step 3: Update
        # ------------------------------------------------------------------
        updated_payload = dict(payload)
        updated_payload["id"] = patient_id
        updated_payload["birthDate"] = "1989-08-30"  # changed

        put_resp = requests.put(
            _url(base_url, f"/fhir/Patient/{patient_id}"),
            json=updated_payload,
            headers=_headers(),
            timeout=30,
        )
        assert put_resp.status_code == 200, (
            f"[Step 3] Update failed: {put_resp.status_code} — {put_resp.text}"
        )
        updated_body = put_resp.json()
        assert updated_body["birthDate"] == "1989-08-30", (
            f"[Step 3] Updated birthDate not reflected in PUT response"
        )

        # ------------------------------------------------------------------
        # Step 4: Verify update persisted
        # ------------------------------------------------------------------
        verify_resp = requests.get(
            _url(base_url, f"/fhir/Patient/{patient_id}"),
            headers=_headers(),
            timeout=30,
        )
        assert verify_resp.status_code == 200, (
            f"[Step 4] Verify read failed: {verify_resp.status_code}"
        )
        assert verify_resp.json()["birthDate"] == "1989-08-30", (
            f"[Step 4] Updated birthDate not persisted in GET after PUT"
        )

        # ------------------------------------------------------------------
        # Step 5: Search by name
        # ------------------------------------------------------------------
        search_resp = requests.get(
            _url(base_url, "/fhir/Patient"),
            params={"name": family_name},
            headers=_headers(),
            timeout=30,
        )
        assert search_resp.status_code == 200, (
            f"[Step 5] Search failed: {search_resp.status_code}"
        )
        search_body = search_resp.json()
        assert search_body.get("total", 0) >= 1, (
            f"[Step 5] Patient not found in search by name={family_name!r}"
        )
        ids_in_bundle = [
            e["resource"]["id"]
            for e in search_body.get("entry", [])
            if "resource" in e
        ]
        assert patient_id in ids_in_bundle, (
            f"[Step 5] Created patient {patient_id} not found in search results: {ids_in_bundle}"
        )

        # ------------------------------------------------------------------
        # Step 6: Delete
        # ------------------------------------------------------------------
        del_resp = requests.delete(
            _url(base_url, f"/fhir/Patient/{patient_id}"),
            headers=_headers(),
            timeout=30,
        )
        assert del_resp.status_code == 204, (
            f"[Step 6] Delete failed: {del_resp.status_code} — {del_resp.text}"
        )

        # ------------------------------------------------------------------
        # Step 7: Verify deletion (GET → 404)
        # ------------------------------------------------------------------
        gone_resp = requests.get(
            _url(base_url, f"/fhir/Patient/{patient_id}"),
            headers=_headers(),
            timeout=30,
        )
        assert gone_resp.status_code == 404, (
            f"[Step 7] Expected 404 after delete, got {gone_resp.status_code}"
        )

        # ------------------------------------------------------------------
        # Step 8: Verify not in search results
        # ------------------------------------------------------------------
        post_delete_search = requests.get(
            _url(base_url, "/fhir/Patient"),
            params={"name": family_name},
            headers=_headers(),
            timeout=30,
        )
        assert post_delete_search.status_code == 200
        post_body = post_delete_search.json()
        remaining_ids = [
            e["resource"]["id"]
            for e in post_body.get("entry", [])
            if "resource" in e
        ]
        assert patient_id not in remaining_ids, (
            f"[Step 8] Deleted patient {patient_id} still appears in search results"
        )

        # Mark as already cleaned up
        patient_id = None

    finally:
        # Safety cleanup in case test fails mid-way
        if patient_id:
            requests.delete(
                _url(base_url, f"/fhir/Patient/{patient_id}"),
                headers=_headers(),
                timeout=10,
            )


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_audit_trail_exists(base_url):
    """Verify that successive operations on a Patient are tracked via meta.versionId.

    A FHIR server that supports versioning must increment (or change) the
    versionId each time a resource is updated. This acts as a lightweight
    audit-trail proxy: if versionId changes after a PUT, the server is
    recording history.
    """
    payload = {
        "resourceType": "Patient",
        "name": [{"use": "official", "family": "AuditTrail", "given": ["Test"]}],
        "gender": "unknown",
        "birthDate": "2000-01-01",
    }
    patient_id = None
    try:
        # Create
        create_resp = requests.post(
            _url(base_url, "/fhir/Patient"),
            json=payload,
            headers=_headers(),
            timeout=30,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        patient_id = created["id"]
        v1 = created.get("meta", {}).get("versionId")

        # Update
        updated = dict(payload)
        updated["id"] = patient_id
        updated["birthDate"] = "2001-02-02"
        put_resp = requests.put(
            _url(base_url, f"/fhir/Patient/{patient_id}"),
            json=updated,
            headers=_headers(),
            timeout=30,
        )
        assert put_resp.status_code == 200
        v2 = put_resp.json().get("meta", {}).get("versionId")

        # versionId must be present after each operation
        assert v1 is not None, "meta.versionId must be set on creation"
        assert v2 is not None, "meta.versionId must be set after update"
        # versionId should change to reflect a new version
        assert v1 != v2, (
            f"meta.versionId should change after update: create={v1!r}, update={v2!r}"
        )
    finally:
        if patient_id:
            requests.delete(
                _url(base_url, f"/fhir/Patient/{patient_id}"),
                headers=_headers(),
                timeout=10,
            )
