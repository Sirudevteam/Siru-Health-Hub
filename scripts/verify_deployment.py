#!/usr/bin/env python3
"""
==============================================================================
Siru HealthHub — Production Deployment & Health Verification Tool
Runs comprehensive end-to-end smoke tests against all running microservices:
1. Nginx TLS Reverse Proxy (Port 80/443)
2. FastAPI FHIR Backend API (Port 8000)
3. FHIR R4 CapabilityStatement & Schema
4. PostgreSQL Database Persistence
5. Redis Token Revocation & Session Layer
6. Next.js 15 Frontend Dashboard & Admin Views (Port 3000)
7. Prometheus Observability Scrape (/metrics)
8. Executive Financial & Clinical Analytics (/analytics/summary)
==============================================================================
"""

import sys
import time
import urllib3
import requests

# Set stdout to UTF-8 if supported
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Disable insecure HTTPS warnings for self-signed development certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PASSED = "[PASS]"
FAILED = "[FAIL]"

def print_header(title: str):
    print(f"\n=== {title} ===")

def run_check(name: str, check_fn):
    try:
        start = time.time()
        success, detail = check_fn()
        elapsed_ms = int((time.time() - start) * 1000)
        if success:
            print(f"  {PASSED} {name:<45} [{elapsed_ms:>3}ms] - {detail}")
            return True
        else:
            print(f"  {FAILED} {name:<45} [{elapsed_ms:>3}ms] - {detail}")
            return False
    except Exception as e:
        print(f"  {FAILED} {name:<45} - Exception: {str(e)}")
        return False

def main():
    print("=================================================================")
    print("      Siru HealthHub — Production Deployment Health Verifier     ")
    print("=================================================================")

    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    proxy_url = "https://localhost"
    
    results = []

    # ── 1. Backend Core Checks ────────────────────────────────────────────────
    print_header("1. Backend API & Database Service")
    
    def check_health():
        r = requests.get(f"{backend_url}/health", timeout=5)
        if r.status_code == 200 and r.json().get("status") == "ok":
            return True, f"Status: OK (Service: {r.json().get('service')})"
        return False, f"HTTP {r.status_code}: {r.text}"
    results.append(run_check("Backend Health Check (/health)", check_health))

    def check_capability():
        r = requests.get(f"{backend_url}/fhir/metadata", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("resourceType") == "CapabilityStatement" and data.get("fhirVersion") == "4.0.1":
                return True, f"FHIR R4 CapabilityStatement (version: {data.get('fhirVersion')})"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("FHIR R4 CapabilityStatement", check_capability))

    # ── 2. Security, Authentication & Redis Layer ────────────────────────────
    print_header("2. Security, Authentication & Redis Layer")

    token = None
    def check_auth_login():
        nonlocal token
        r = requests.post(f"{backend_url}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=5)
        if r.status_code == 200:
            token = r.json().get("access_token")
            role = r.json().get("role")
            return True, f"JWT issued for role: {role}"
        return False, f"HTTP {r.status_code}: {r.text}"
    results.append(run_check("Admin OAuth2 / JWT Login", check_auth_login))

    def check_auth_me():
        if not token:
            return False, "Skipped: no token"
        r = requests.get(f"{backend_url}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if r.status_code == 200 and r.json().get("username") == "admin":
            return True, f"Identity validated: {r.json().get('email')}"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("Protected /auth/me Endpoint", check_auth_me))

    def check_redis_revocation():
        login_res = requests.post(f"{backend_url}/auth/login", json={"username": "doctor.sharma", "password": "doctor123"}, timeout=5)
        if login_res.status_code != 200:
            return False, f"Failed to login doctor: {login_res.text}"
        doc_token = login_res.json()["access_token"]
        
        logout_res = requests.post(f"{backend_url}/auth/logout", headers={"Authorization": f"Bearer {doc_token}"}, timeout=5)
        if logout_res.status_code != 200:
            return False, "Failed to logout doctor"
        
        reuse_res = requests.get(f"{backend_url}/auth/me", headers={"Authorization": f"Bearer {doc_token}"}, timeout=5)
        if reuse_res.status_code == 401 and "revoked" in reuse_res.text.lower():
            return True, "Revoked token rejected with 401 (Redis blacklist active)"
        return False, f"Unexpected response: {reuse_res.status_code}"
    results.append(run_check("Redis Token Revocation Verification", check_redis_revocation))

    # ── 3. Observability & Analytics ──────────────────────────────────────────
    print_header("3. Observability & Executive Analytics")

    def check_metrics():
        r = requests.get(f"{backend_url}/metrics", timeout=5)
        if r.status_code == 200 and "http_requests_total" in r.text:
            return True, "Prometheus metrics stream active (http_requests_total found)"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("Prometheus Scrape Endpoint (/metrics)", check_metrics))

    def check_analytics():
        if not token:
            return False, "Skipped: no token"
        r = requests.get(f"{backend_url}/analytics/summary", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            rcm = data.get("rcm", {})
            return True, f"RCM Total Billed: ${rcm.get('totalBilledAmount', 0):,.2f} USD | Clean Claim Rate: {rcm.get('cleanClaimRatePercent')}%"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("Executive Analytics API (/analytics/summary)", check_analytics))

    def check_audit_logs():
        if not token:
            return False, "Skipped: no token"
        r = requests.get(f"{backend_url}/audit/stats", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return True, f"HIPAA Logged Events: {data.get('total_events', 0)} ({data.get('success_rate_percent')}% success)"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("HIPAA Audit Log Statistics (/audit/stats)", check_audit_logs))

    # ── 4. Frontend Next.js 15 ────────────────────────────────────────────────
    print_header("4. Next.js 15 Frontend Portal")

    def check_frontend_home():
        r = requests.get(f"{frontend_url}/", timeout=5)
        if r.status_code == 200:
            return True, "Homepage rendered (HTTP 200)"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("Frontend Home Dashboard (/)", check_frontend_home))

    def check_frontend_analytics():
        r = requests.get(f"{frontend_url}/admin/analytics", timeout=5)
        if r.status_code == 200:
            return True, "Admin Analytics view rendered (HTTP 200)"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("Admin Analytics UI (/admin/analytics)", check_frontend_analytics))

    def check_frontend_audit():
        r = requests.get(f"{frontend_url}/admin/audit", timeout=5)
        if r.status_code == 200:
            return True, "Admin Audit Log Explorer rendered (HTTP 200)"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("Admin Audit Explorer UI (/admin/audit)", check_frontend_audit))

    # ── 5. Nginx TLS Reverse Proxy ────────────────────────────────────────────
    print_header("5. Nginx TLS Reverse Proxy")

    def check_proxy_tls():
        r = requests.get(f"{proxy_url}/health", verify=False, timeout=5)
        if r.status_code == 200 and r.json().get("status") == "ok":
            return True, "HTTPS TLS handshake successful, proxied to backend"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("Nginx TLS Reverse Proxy (https://localhost/health)", check_proxy_tls))

    def check_proxy_fhir():
        r = requests.get(f"{proxy_url}/fhir/metadata", verify=False, timeout=5)
        if r.status_code == 200 and r.json().get("resourceType") == "CapabilityStatement":
            return True, "HTTPS /fhir/* proxy routing validated"
        return False, f"HTTP {r.status_code}"
    results.append(run_check("Nginx TLS FHIR Metadata Route (https://localhost/fhir/metadata)", check_proxy_fhir))

    # ── Summary ───────────────────────────────────────────────────────────────
    print_header("Deployment Verification Summary")
    total_checks = len(results)
    passed_checks = sum(1 for r in results if r)
    failed_checks = total_checks - passed_checks

    if failed_checks == 0:
        print(f"\nALL {total_checks} PRODUCTION VERIFICATION CHECKS PASSED! Platform is healthy and ready.\n")
        return 0
    else:
        print(f"\n{failed_checks} OF {total_checks} CHECKS FAILED.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

