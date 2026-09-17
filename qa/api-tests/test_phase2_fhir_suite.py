# ==============================================================================
# Siru HealthHub — Phase 2 FHIR Resource Suite & Relationship Tests
# Tests Practitioner, Organization, Encounter, Observation, Condition,
# MedicationRequest, Appointment, and FHIR cross-resource reference linking.
# ==============================================================================

import pytest
import requests
import uuid

def _url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")

_admin_token_cache = None

def _headers(base_url="http://localhost:8000") -> dict:
    global _admin_token_cache
    if not _admin_token_cache:
        try:
            r = requests.post(f"{base_url.rstrip('/')}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=5)
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


# ─── 1. Practitioner Tests ───────────────────────────────────────────────────

@pytest.mark.fhir
def test_get_seeded_practitioners(base_url):
    """Ensure seeded practitioners are discoverable."""
    res = requests.get(_url(base_url, "/fhir/Practitioner"), headers=_headers())
    assert res.status_code == 200
    bundle = res.json()
    assert bundle.get("resourceType") == "Bundle"
    assert bundle.get("total", 0) >= 1
    ids = [e["resource"]["id"] for e in bundle.get("entry", [])]
    assert any("PR" in pid for pid in ids)


@pytest.mark.fhir
def test_create_and_read_practitioner(base_url):
    """Test full create, read, and delete cycle for Practitioner."""
    new_pr = {
        "resourceType": "Practitioner",
        "name": [{"use": "official", "family": "Menon", "given": ["Karthik"]}],
        "gender": "male",
        "active": True
    }
    create_res = requests.post(_url(base_url, "/fhir/Practitioner"), json=new_pr, headers=_headers())
    assert create_res.status_code == 201
    pr_id = create_res.json()["id"]

    get_res = requests.get(_url(base_url, f"/fhir/Practitioner/{pr_id}"), headers=_headers())
    assert get_res.status_code == 200
    assert get_res.json()["name"][0]["family"] == "Menon"

    del_res = requests.delete(_url(base_url, f"/fhir/Practitioner/{pr_id}"), headers=_headers())
    assert del_res.status_code == 204


# ─── 2. Organization Tests ───────────────────────────────────────────────────

@pytest.mark.fhir
def test_get_seeded_organization(base_url):
    """Verify that Siru Central Hospital is queryable."""
    res = requests.get(_url(base_url, "/fhir/Organization/ORG101"), headers=_headers())
    assert res.status_code == 200
    org = res.json()
    assert org["resourceType"] == "Organization"
    assert "Siru Central Hospital" in org.get("name", "")


# ─── 3. Encounter & Reference Tests ──────────────────────────────────────────

@pytest.mark.fhir
def test_get_patient_encounters_by_reference(base_url):
    """Query encounters using FHIR reference search: ?patient=P1001."""
    res = requests.get(_url(base_url, "/fhir/Encounter"), params={"patient": "P1001"}, headers=_headers())
    assert res.status_code == 200
    bundle = res.json()
    assert bundle["resourceType"] == "Bundle"
    assert bundle["total"] >= 1
    enc = bundle["entry"][0]["resource"]
    assert "P1001" in enc["subject"]["reference"]


@pytest.mark.fhir
def test_create_encounter_with_patient_and_practitioner(base_url):
    """Create an encounter connecting a Patient and Practitioner."""
    enc_payload = {
        "resourceType": "Encounter",
        "status": "in-progress",
        "class": {"code": "AMB", "display": "Ambulatory"},
        "subject": {"reference": "Patient/P1001", "display": "Arun Kumar"},
        "participant": [{"individual": {"reference": "Practitioner/PR101", "display": "Dr. Rajesh Sharma"}}],
        "reasonCode": [{"text": "Follow-up Cardiology"}]
    }
    create_res = requests.post(_url(base_url, "/fhir/Encounter"), json=enc_payload, headers=_headers())
    assert create_res.status_code == 201
    enc_id = create_res.json()["id"]

    # Verify encounter search finds it
    search_res = requests.get(_url(base_url, "/fhir/Encounter"), params={"patient": "Patient/P1001"}, headers=_headers())
    assert search_res.status_code == 200
    found_ids = [e["resource"]["id"] for e in search_res.json()["entry"]]
    assert enc_id in found_ids

    # Cleanup
    requests.delete(_url(base_url, f"/fhir/Encounter/{enc_id}"), headers=_headers())


# ─── 4. Observation & Vitals Tests ───────────────────────────────────────────

@pytest.mark.fhir
def test_get_patient_vitals_observations(base_url):
    """Verify observation query for vital-signs linked to patient P1001."""
    res = requests.get(_url(base_url, "/fhir/Observation"), params={"patient": "P1001", "category": "vital-signs"}, headers=_headers())
    assert res.status_code == 200
    bundle = res.json()
    assert bundle["total"] >= 2  # Seeded BP, HR, Temp
    codes = [e["resource"]["code"].get("text") or (e["resource"]["code"].get("coding", [{}])[0].get("display", "")) for e in bundle["entry"]]
    assert any("Blood Pressure" in c for c in codes)


@pytest.mark.fhir
def test_create_numeric_observation(base_url):
    """Create a clinical observation with Quantity and link to Encounter."""
    obs_payload = {
        "resourceType": "Observation",
        "status": "final",
        "category": [{"coding": [{"code": "vital-signs"}]}],
        "code": {"text": "Oxygen Saturation SpO2", "coding": [{"code": "2708-6", "display": "SpO2"}]},
        "subject": {"reference": "Patient/P1001"},
        "encounter": {"reference": "Encounter/ENC1001"},
        "valueQuantity": {"value": 98.0, "unit": "%"}
    }
    res = requests.post(_url(base_url, "/fhir/Observation"), json=obs_payload, headers=_headers())
    assert res.status_code == 201
    obs_id = res.json()["id"]

    # Check search by encounter reference
    enc_search = requests.get(_url(base_url, "/fhir/Observation"), params={"encounter": "ENC1001"}, headers=_headers())
    assert enc_search.status_code == 200
    assert any(e["resource"]["id"] == obs_id for e in enc_search.json()["entry"])

    # Cleanup
    requests.delete(_url(base_url, f"/fhir/Observation/{obs_id}"), headers=_headers())


# ─── 5. Condition (Diagnoses) Tests ──────────────────────────────────────────

@pytest.mark.fhir
def test_get_patient_conditions(base_url):
    """Verify condition query returns active diagnoses for P1001."""
    res = requests.get(_url(base_url, "/fhir/Condition"), params={"patient": "P1001"}, headers=_headers())
    assert res.status_code == 200
    bundle = res.json()
    assert bundle["total"] >= 1
    cond = bundle["entry"][0]["resource"]
    assert "Hypertension" in cond["code"]["text"]


@pytest.mark.fhir
def test_create_condition_with_icd10(base_url):
    """Create a Condition with ICD-10 coding linked to Patient."""
    cond_payload = {
        "resourceType": "Condition",
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {
            "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "E11.9", "display": "Type 2 Diabetes"}],
            "text": "Type 2 Diabetes Mellitus"
        },
        "subject": {"reference": "Patient/P1001"}
    }
    res = requests.post(_url(base_url, "/fhir/Condition"), json=cond_payload, headers=_headers())
    assert res.status_code == 201
    cond_id = res.json()["id"]

    # Query with clinical-status filter
    search_res = requests.get(_url(base_url, "/fhir/Condition"), params={"patient": "P1001", "clinical-status": "active"}, headers=_headers())
    assert search_res.status_code == 200
    assert any(e["resource"]["id"] == cond_id for e in search_res.json()["entry"])

    # Cleanup
    requests.delete(_url(base_url, f"/fhir/Condition/{cond_id}"), headers=_headers())


# ─── 6. MedicationRequest Tests ──────────────────────────────────────────────

@pytest.mark.fhir
def test_get_patient_medication_requests(base_url):
    """Verify active prescriptions query for patient P1001."""
    res = requests.get(_url(base_url, "/fhir/MedicationRequest"), params={"patient": "P1001"}, headers=_headers())
    assert res.status_code == 200
    bundle = res.json()
    assert bundle["total"] >= 1
    med = bundle["entry"][0]["resource"]
    assert "Amlodipine" in med["medicationCodeableConcept"]["text"]


# ─── 7. Appointment Scheduling Tests ─────────────────────────────────────────

@pytest.mark.fhir
def test_get_patient_appointments(base_url):
    """Verify appointment query for patient P1001."""
    res = requests.get(_url(base_url, "/fhir/Appointment"), params={"patient": "P1001"}, headers=_headers())
    assert res.status_code == 200
    bundle = res.json()
    assert bundle["total"] >= 1
    apt = bundle["entry"][0]["resource"]
    assert apt["status"] == "booked"


# ─── 8. Full FHIR Relationship Tree Test ────────────────────────────────────

@pytest.mark.integration
def test_full_fhir_ecosystem_relationship_chain(base_url):
    """
    Validate the complete FHIR healthcare journey chain:
    Patient (P1001)
       │
       ├── Encounter (ENC1001) ── Practitioner (PR101)
       │       │
       │       ├── Observation (Vitals)
       │       ├── Condition (Diagnosis)
       │       └── MedicationRequest (Rx)
       │
       └── Appointment (APT1001)
    """
    # 1. Verify Patient exists
    p_res = requests.get(_url(base_url, "/fhir/Patient/P1001"), headers=_headers())
    assert p_res.status_code == 200

    # 2. Get Encounter for Patient
    enc_res = requests.get(_url(base_url, "/fhir/Encounter"), params={"patient": "P1001"}, headers=_headers())
    assert enc_res.status_code == 200
    encounters = enc_res.json()["entry"]
    assert len(encounters) >= 1
    enc_id = encounters[0]["resource"]["id"]

    # 3. Verify Observations linked to this Encounter
    obs_res = requests.get(_url(base_url, "/fhir/Observation"), params={"encounter": enc_id}, headers=_headers())
    assert obs_res.status_code == 200
    assert obs_res.json()["total"] >= 1

    # 4. Verify Condition linked to this Encounter
    cond_res = requests.get(_url(base_url, "/fhir/Condition"), params={"encounter": enc_id}, headers=_headers())
    assert cond_res.status_code == 200
    assert cond_res.json()["total"] >= 1

    # 5. Verify MedicationRequest linked to this Encounter
    med_res = requests.get(_url(base_url, "/fhir/MedicationRequest"), params={"encounter": enc_id}, headers=_headers())
    assert med_res.status_code == 200
    assert med_res.json()["total"] >= 1

