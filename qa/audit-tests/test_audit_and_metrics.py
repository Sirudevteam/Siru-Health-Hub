# ==============================================================================
# Siru HealthHub — HIPAA Audit Logs & Prometheus Observability QA Suite
# Tests audit trail fidelity, user identity capture, RBAC log protection,
# Prometheus metrics scrape outputs, and financial/clinical analytics APIs.
# ==============================================================================

import pytest
import requests
import time
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


# ─── 1. Prometheus Metrics Scrape ─────────────────────────────────────────────

@pytest.mark.audit
def test_prometheus_metrics_endpoint_200(base_url):
    """GET /metrics must return HTTP 200 with standard Prometheus OpenMetrics text."""
    res = requests.get(_url(base_url, "/metrics"))
    assert res.status_code == 200
    text = res.text
    assert "http_requests_total" in text
    assert "fhir_resources_count" in text
    assert "HELP" in text or "TYPE" in text


# ─── 2. Audit Trail User Identity & Fidelity ─────────────────────────────────

@pytest.mark.audit
def test_audit_log_captures_authenticated_user_identity(base_url):
    """Actions performed with Bearer token must record user_id in the audit trail."""
    # 1. Doctor Sharma accesses patient Arun
    doc_headers = _headers(base_url, "doctor.sharma", "doctor123")
    res = requests.get(_url(base_url, "/fhir/Patient/P1001"), headers=doc_headers)
    assert res.status_code == 200

    time.sleep(0.5)  # Allow async audit task to commit

    # 2. Admin queries audit logs for doctor.sharma
    admin_headers = _headers(base_url, "admin", "admin123")
    audit_res = requests.get(
        _url(base_url, "/audit/logs?user_id=doctor.sharma&limit=5"),
        headers=admin_headers
    )
    assert audit_res.status_code == 200
    body = audit_res.json()
    assert body["total"] >= 1
    found_users = [entry["user_id"] for entry in body["logs"]]
    assert any("doctor.sharma" in u for u in found_users)


# ─── 3. Audit Log Access Control (Restricted to ADMIN) ────────────────────────

@pytest.mark.audit
@pytest.mark.security
def test_audit_logs_restricted_to_admin_403_for_doctor(base_url):
    """Doctor role is forbidden from reading the security audit trail."""
    doc_headers = _headers(base_url, "doctor.sharma", "doctor123")
    res = requests.get(_url(base_url, "/audit/logs"), headers=doc_headers)
    assert res.status_code == 403


@pytest.mark.audit
@pytest.mark.security
def test_audit_logs_restricted_to_admin_403_for_nurse(base_url):
    """Nurse role is forbidden from reading the security audit trail."""
    nurse_headers = _headers(base_url, "nurse.lakshmi", "nurse123")
    res = requests.get(_url(base_url, "/audit/logs"), headers=nurse_headers)
    assert res.status_code == 403


@pytest.mark.audit
@pytest.mark.security
def test_audit_logs_restricted_to_admin_403_for_patient(base_url):
    """Patient role is forbidden from reading the security audit trail."""
    patient_headers = _headers(base_url, "patient.arun", "patient123")
    res = requests.get(_url(base_url, "/audit/logs"), headers=patient_headers)
    assert res.status_code == 403


# ─── 4. Audit Log Query Filters & Stats ────────────────────────────────────────

@pytest.mark.audit
def test_audit_filter_by_action(base_url):
    """Admin can filter audit logs by action type (CREATE, READ, etc.)."""
    admin_headers = _headers(base_url, "admin", "admin123")
    res = requests.get(_url(base_url, "/audit/logs?action=CREATE&limit=10"), headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert "logs" in body
    for log in body["logs"]:
        assert log["action"] == "CREATE"


@pytest.mark.audit
def test_audit_stats_endpoint(base_url):
    """GET /audit/stats provides high-level security event metrics."""
    admin_headers = _headers(base_url, "admin", "admin123")
    res = requests.get(_url(base_url, "/audit/stats"), headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_events" in data
    assert "success_count" in data
    assert "unauthorized_401_count" in data
    assert "forbidden_403_count" in data
    assert "actions_distribution" in data


# ─── 5. Analytics & RCM Summary ───────────────────────────────────────────────

@pytest.mark.audit
def test_analytics_summary_kpis(base_url):
    """GET /analytics/summary returns aggregated financial and clinical KPIs."""
    res = requests.get(_url(base_url, "/analytics/summary"))
    assert res.status_code == 200
    data = res.json()

    # Financial section
    fin = data.get("financial", {})
    assert "totalClaimsCount" in fin
    assert "totalBilledAmount" in fin
    assert "cleanClaimRatePercent" in fin
    assert fin["totalBilledAmount"] >= 0.0

    # Clinical section
    clin = data.get("clinical", {})
    assert "totalPatients" in clin
    assert "totalEncounters" in clin
    assert "totalConditions" in clin
    assert clin["totalPatients"] >= 1

