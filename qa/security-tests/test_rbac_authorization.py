# ==============================================================================
# Siru HealthHub — RBAC Authorization QA Suite
# Tests role permissions (ADMIN, DOCTOR, NURSE, PATIENT) and access control boundaries.
# ==============================================================================

import pytest
import requests
import uuid

def _url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


# ─── 1. Admin Role (Superuser) ────────────────────────────────────────────────

@pytest.mark.security
def test_admin_can_create_patient(base_url, admin_token, auth_header):
    """Admin has full authorization to create patients."""
    new_pat = {
        "resourceType": "Patient",
        "name": [{"family": "Raman", "given": ["Kavya"]}],
        "gender": "female",
        "birthDate": "1994-08-12"
    }
    res = requests.post(_url(base_url, "/fhir/Patient"), json=new_pat, headers=auth_header(admin_token))
    assert res.status_code == 201
    pat_id = res.json()["id"]

    # Clean up
    del_res = requests.delete(_url(base_url, f"/fhir/Patient/{pat_id}"), headers=auth_header(admin_token))
    assert del_res.status_code == 204


# ─── 2. Doctor Role ───────────────────────────────────────────────────────────

@pytest.mark.security
def test_doctor_allowed_to_prescribe_and_diagnose(base_url, doctor_token, auth_header, admin_token):
    """Doctors are authorized to diagnose (Condition) and prescribe (MedicationRequest)."""
    # Create Prescription
    med = {
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": "Atorvastatin 20mg"},
        "subject": {"reference": "Patient/P1001"}
    }
    res_med = requests.post(_url(base_url, "/fhir/MedicationRequest"), json=med, headers=auth_header(doctor_token))
    assert res_med.status_code == 201
    med_id = res_med.json()["id"]

    # Create Diagnosis
    cond = {
        "resourceType": "Condition",
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {"text": "Hyperlipidemia"},
        "subject": {"reference": "Patient/P1001"}
    }
    res_cond = requests.post(_url(base_url, "/fhir/Condition"), json=cond, headers=auth_header(doctor_token))
    assert res_cond.status_code == 201
    cond_id = res_cond.json()["id"]

    # Cleanup with admin
    requests.delete(_url(base_url, f"/fhir/MedicationRequest/{med_id}"), headers=auth_header(admin_token))
    requests.delete(_url(base_url, f"/fhir/Condition/{cond_id}"), headers=auth_header(admin_token))


# ─── 3. Nurse Role (Clinical Boundaries) ─────────────────────────────────────

@pytest.mark.security
def test_nurse_forbidden_from_prescribing_403(base_url, nurse_token, auth_header):
    """Nurses attempting to create MedicationRequest must be rejected with 403 Forbidden."""
    med = {
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": "Morphine 10mg"},
        "subject": {"reference": "Patient/P1001"}
    }
    res = requests.post(_url(base_url, "/fhir/MedicationRequest"), json=med, headers=auth_header(nurse_token))
    assert res.status_code == 403
    assert "Access forbidden" in res.json().get("detail", "")


@pytest.mark.security
def test_nurse_forbidden_from_diagnosing_403(base_url, nurse_token, auth_header):
    """Nurses attempting to create Condition (Diagnosis) must be rejected with 403 Forbidden."""
    cond = {
        "resourceType": "Condition",
        "code": {"text": "Myocardial Infarction"},
        "subject": {"reference": "Patient/P1001"}
    }
    res = requests.post(_url(base_url, "/fhir/Condition"), json=cond, headers=auth_header(nurse_token))
    assert res.status_code == 403
    assert "Access forbidden" in res.json().get("detail", "")


@pytest.mark.security
def test_nurse_allowed_to_record_vitals_201(base_url, nurse_token, auth_header, admin_token):
    """Nurses ARE authorized to record clinical vitals (Observation)."""
    obs = {
        "resourceType": "Observation",
        "status": "final",
        "category": [{"coding": [{"code": "vital-signs"}]}],
        "code": {"text": "Respiratory Rate"},
        "subject": {"reference": "Patient/P1001"},
        "valueQuantity": {"value": 16, "unit": "/min"}
    }
    res = requests.post(_url(base_url, "/fhir/Observation"), json=obs, headers=auth_header(nurse_token))
    assert res.status_code == 201
    obs_id = res.json()["id"]

    # Cleanup with admin
    requests.delete(_url(base_url, f"/fhir/Observation/{obs_id}"), headers=auth_header(admin_token))


# ─── 4. Patient Role (Data Privacy & Least Privilege) ─────────────────────────

@pytest.mark.security
def test_patient_can_read_own_records_200(base_url, patient_token, auth_header):
    """Patient Arun (P1001) is authorized to view his own record."""
    res = requests.get(_url(base_url, "/fhir/Patient/P1001"), headers=auth_header(patient_token))
    assert res.status_code == 200
    assert res.json()["id"] == "P1001"


@pytest.mark.security
def test_patient_forbidden_from_reading_other_patients_403(base_url, patient_token, auth_header):
    """Patient Arun (P1001) attempting to access Priya Devi (P1002) is rejected with 403 Forbidden."""
    res = requests.get(_url(base_url, "/fhir/Patient/P1002"), headers=auth_header(patient_token))
    assert res.status_code == 403
    assert "Access forbidden" in res.json().get("detail", "")


@pytest.mark.security
def test_patient_forbidden_from_prescribing_403(base_url, patient_token, auth_header):
    """Patients cannot prescribe medications for themselves or others."""
    med = {
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": "Antibiotics"},
        "subject": {"reference": "Patient/P1001"}
    }
    res = requests.post(_url(base_url, "/fhir/MedicationRequest"), json=med, headers=auth_header(patient_token))
    assert res.status_code == 403

