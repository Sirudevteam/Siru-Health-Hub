# Siru HealthHub — Master Test Plan

> **Specification:** HL7 FHIR R4 (4.0.1) | **Version:** 2.0 (Enterprise Release) | **Total Test Cases:** 87

---

## 1. Test Scope & Overview

This document outlines the master test plan for Siru HealthHub, covering functional, compliance, security, financial calculation, and observability verification.

### System Components Under Test
- **FastAPI FHIR R4 Async Server** (Port 8000)
- **Nginx TLS Reverse Proxy** (Port 443 / 80)
- **Redis 7 Session & Blacklist Layer** (Port 6379)
- **PostgreSQL 15 Data Store** (Port 5432)
- **Next.js 15 Patient & Administrative Web Portal** (Port 3000)
- **Payer Claims Auto-Adjudication Engine**
- **Prometheus Metrics Exporter & HIPAA Audit Logger**

---

## 2. Test Environment Matrix

| Environment | Host URL | Description |
|---|---|---|
| **Local Docker** | `http://localhost:8000` / `https://localhost` | Multi-container stack managed by `docker-compose.yml` |
| **CI/CD Pipeline** | GitHub Actions Ubuntu 22.04 | Ephemeral PostgreSQL 15 & Redis 7 container services |
| **Frontend Portal** | `http://localhost:3000` | Next.js 15 App Router |

---

## 3. Entry & Exit Criteria

### Entry Criteria
- [x] Docker Compose stack is running and healthy (`postgres`, `redis`, `backend`, `frontend`, `nginx`).
- [x] Backend returns `HTTP 200 { "status": "ok" }` on `/health`.
- [x] Test dependencies installed (`pip install -r qa/requirements.txt`).
- [x] Environment configured with valid `BASE_URL`.

### Exit Criteria
- [x] **100% Pass Rate**: All 87 test cases pass cleanly with zero failures.
- [x] **Zero P0 / P1 Defects**: No critical data corruption, authentication bypass, or crash bugs.
- [x] **100% FHIR Spec Compliance**: All FHIR resources parse cleanly through `fhir.resources`.
- [x] **Continuous Gate**: Both GitHub Actions workflows (`Backend CI`, `QA API Tests`) report green status.

---

## 4. Master Test Case Matrix

### 1. Patient CRUD & Search Suite (`qa/api-tests/test_patient.py`)
| Test ID | Test Case Name | Target | Expected Result | Priority |
|---|---|---|---|---|
| `TC-PAT-001` | Health Check | `GET /health` | HTTP 200, status "ok" | P0 |
| `TC-PAT-002` | CapabilityStatement | `GET /fhir/metadata` | HTTP 200, FHIR 4.0.1 | P0 |
| `TC-PAT-003` | Create Patient Valid | `POST /fhir/Patient` | HTTP 201, ID generated, Location header | P0 |
| `TC-PAT-004` | Return FHIR Meta Block | `POST /fhir/Patient` | HTTP 201, `meta.versionId` & `meta.lastUpdated` | P1 |
| `TC-PAT-005` | Read Patient By ID | `GET /fhir/Patient/{id}` | HTTP 200, returned JSON matches created data | P0 |
| `TC-PAT-006` | Read Nonexistent Patient | `GET /fhir/Patient/{404}` | HTTP 404, FHIR OperationOutcome returned | P1 |
| `TC-PAT-007` | Update Patient | `PUT /fhir/Patient/{id}` | HTTP 200, updated fields persisted | P1 |
| `TC-PAT-008` | Soft Delete Patient | `DELETE /fhir/Patient/{id}` | HTTP 204, subsequent GET returns 404 | P1 |
| `TC-PAT-009` | Reject Invalid JSON Body | `POST /fhir/Patient` | HTTP 400 / 422 rejected | P2 |
| `TC-PAT-010` | Reject Invalid ResourceType | `POST /fhir/Patient` | HTTP 422 with validation error | P1 |
| `TC-PAT-011` | Reject Invalid Gender Code | `POST /fhir/Patient` | HTTP 422 with validation error | P1 |
| `TC-PAT-012` | Reject Invalid BirthDate | `POST /fhir/Patient` | HTTP 422 with ISO date error | P1 |
| `TC-PAT-013` | Search Patients Returns Bundle | `GET /fhir/Patient` | HTTP 200, FHIR searchset Bundle | P0 |
| `TC-PAT-014` | Search Patients By Name | `GET /fhir/Patient?name=` | HTTP 200, matches in Bundle entry | P1 |
| `TC-PAT-015` | Search Patients By Gender | `GET /fhir/Patient?gender=` | HTTP 200, filtered results match | P1 |
| `TC-PAT-016` | Search Pagination Count | `GET /fhir/Patient?_count=1` | HTTP 200, max 1 record in entries | P1 |
| `TC-PAT-017` | Search Empty Results | `GET /fhir/Patient?name=XYZ` | HTTP 200, total = 0, empty bundle | P2 |
| `TC-PAT-018` | Validate FHIR Content-Type | `GET /fhir/Patient` | Response Content-Type is json/fhir+json | P2 |
| `TC-PAT-019` | Reject Unsupported HTTP Method | `PATCH /fhir/Patient` | HTTP 405 Method Not Allowed | P2 |
| `TC-PAT-020` | Full Round-Trip Data Integrity | `POST -> GET /fhir/Patient` | Exact character-for-character field match | P0 |

### 2. Clinical EHR Suite (`qa/api-tests/test_phase2_fhir_suite.py`)
| Test ID | Test Case Name | Target | Expected Result | Priority |
|---|---|---|---|---|
| `TC-EHR-001` | Get Seeded Practitioners | `GET /fhir/Practitioner` | HTTP 200, Bundle includes Dr. Sharma | P1 |
| `TC-EHR-002` | Create & Read Practitioner | `POST /fhir/Practitioner` | HTTP 201, Practitioner persists | P1 |
| `TC-EHR-003` | Get Seeded Organizations | `GET /fhir/Organization` | HTTP 200, Bundle includes Central Hospital | P1 |
| `TC-EHR-004` | Get Encounters by Reference | `GET /fhir/Encounter?patient` | HTTP 200, encounters linked to `P1001` | P1 |
| `TC-EHR-005` | Create Linked Encounter | `POST /fhir/Encounter` | HTTP 201, links patient & practitioner | P1 |
| `TC-EHR-006` | Get Patient Vitals Observations | `GET /fhir/Observation?category` | HTTP 200, retrieves BP, Heart Rate, Temp | P0 |
| `TC-EHR-007` | Create Numeric Observation | `POST /fhir/Observation` | HTTP 201, persists SpO2 Quantity & unit | P1 |
| `TC-EHR-008` | Get Patient Conditions | `GET /fhir/Condition?patient` | HTTP 200, active clinical diagnoses | P0 |
| `TC-EHR-009` | Create Condition with ICD-10 | `POST /fhir/Condition` | HTTP 201, persists ICD-10 coding | P1 |
| `TC-EHR-010` | Get MedicationRequests | `GET /fhir/MedicationRequest` | HTTP 200, retrieves patient prescriptions | P0 |
| `TC-EHR-011` | Full Clinical Relationship Chain | Cross-resource traversal | HTTP 200 across Patient → Encounter → Obs | P0 |

### 3. Coverage & Real-Time Eligibility (`qa/claims-tests/test_coverage_and_eligibility.py`)
| Test ID | Test Case Name | Target | Expected Result | Priority |
|---|---|---|---|---|
| `TC-COV-001` | Get Seeded Coverages | `GET /fhir/Coverage` | HTTP 200, active insurance policies | P1 |
| `TC-COV-002` | Create & Read Coverage | `POST /fhir/Coverage` | HTTP 201, subscriber ID & group persists | P1 |
| `TC-COV-003` | Real-Time Eligibility (Active) | `POST /eligibility-check` | HTTP 200, `eligible: true`, 90% benefit | P0 |
| `TC-COV-004` | Real-Time Eligibility (Expired) | `POST /eligibility-check` | HTTP 200, `eligible: false`, expired status | P0 |
| `TC-COV-005` | Patient Reads Own Coverage | `GET /fhir/Coverage` | HTTP 200 for authenticated patient | P1 |
| `TC-COV-006` | Patient Forbidden Other Coverage| `GET /fhir/Coverage/{other}`| HTTP 403 Forbidden | P0 |

### 4. Claims & Adjudication Rules Engine (`qa/claims-tests/test_claims_adjudication.py`)
| Test ID | Test Case Name | Target | Expected Result | Priority |
|---|---|---|---|---|
| `TC-CLM-001` | Get Seeded Claim & Response | `GET /fhir/Claim` | HTTP 200, claim & EOB response retrieved | P1 |
| `TC-CLM-002` | Clean Claim Auto-Adjudication | `POST /fhir/Claim` | HTTP 201, auto-generates `ClaimResponse` | P0 |
| `TC-CLM-003` | Adjudication Math Integrity | `POST /fhir/Claim` | Exactly 90% insurer paid, 10% copay | P0 |
| `TC-CLM-004` | Auto-Denial Expired Policy | `POST /fhir/Claim` | HTTP 201, ClaimResponse outcome: `error` | P0 |
| `TC-CLM-005` | Zero Amount Claim Rejection | `POST /fhir/Claim` | HTTP 422 rejected | P1 |
| `TC-CLM-006` | Doctor Allowed to Bill | `POST /fhir/Claim` | HTTP 201 for doctor role | P1 |
| `TC-CLM-007` | Nurse Forbidden to Bill | `POST /fhir/Claim` | HTTP 403 Forbidden for nurse | P1 |
| `TC-CLM-008` | Patient Forbidden to Bill | `POST /fhir/Claim` | HTTP 403 Forbidden for patient | P1 |
| `TC-CLM-009` | Patient Views Own Claim & EOB | `GET /fhir/Claim/{own}` | HTTP 200 for patient | P1 |
| `TC-CLM-010` | Patient Blocked Other Claims | `GET /fhir/Claim/{other}` | HTTP 403 Forbidden | P0 |

### 5. Authentication, Redis Blacklist & RBAC (`qa/security-tests/`)
| Test ID | Test Case Name | Target | Expected Result | Priority |
|---|---|---|---|---|
| `TC-SEC-001` | Valid Login Issues JWTs | `POST /auth/login` | HTTP 200, access & refresh tokens | P0 |
| `TC-SEC-002` | Invalid Password Rejected | `POST /auth/login` | HTTP 401 Unauthorized | P0 |
| `TC-SEC-003` | Missing Auth Header Blocked | `GET /fhir/Patient/P1001`| HTTP 401 Unauthorized | P0 |
| `TC-SEC-004` | Malformed JWT Rejected | `GET /fhir/Patient/P1001`| HTTP 401 Unauthorized | P0 |
| `TC-SEC-005` | Expired JWT Rejected | `GET /fhir/Patient/P1001`| HTTP 401 Unauthorized | P0 |
| `TC-SEC-006` | Instant Redis Token Revocation| `POST /auth/logout` | Token immediately rejected with 401 | P0 |
| `TC-SEC-007` | Admin Superuser Permissions | `POST /fhir/Patient` | HTTP 201 for admin | P0 |
| `TC-SEC-008` | Doctor Prescribes & Diagnoses | `POST /fhir/Condition` | HTTP 201 for doctor | P0 |
| `TC-SEC-009` | Nurse Blocked Prescriptions | `POST /MedicationRequest`| HTTP 403 Forbidden | P0 |
| `TC-SEC-010` | Nurse Blocked Diagnoses | `POST /fhir/Condition` | HTTP 403 Forbidden | P0 |
| `TC-SEC-011` | Nurse Allowed Vitals | `POST /fhir/Observation` | HTTP 201 for nurse | P0 |
| `TC-SEC-012` | Patient Reads Own Records | `GET /fhir/Patient/P1001` | HTTP 200 for owner | P0 |
| `TC-SEC-013` | Patient Blocked Other Records | `GET /fhir/Patient/P1002` | HTTP 403 Forbidden | P0 |
| `TC-SEC-014` | Patient Blocked Prescribing | `POST /MedicationRequest`| HTTP 403 Forbidden | P0 |

### 6. Observability & HIPAA Audit (`qa/audit-tests/test_audit_and_metrics.py`)
| Test ID | Test Case Name | Target | Expected Result | Priority |
|---|---|---|---|---|
| `TC-OBS-001` | Prometheus Metrics Stream | `GET /metrics` | HTTP 200, contains `http_requests_total` | P1 |
| `TC-OBS-002` | HIPAA User Attribution | `AuditMiddleware` | Every request logs acting user ID | P0 |
| `TC-OBS-003` | Audit Logs Blocked for Doctor | `GET /audit/logs` | HTTP 403 Forbidden | P1 |
| `TC-OBS-004` | Audit Logs Blocked for Nurse | `GET /audit/logs` | HTTP 403 Forbidden | P1 |
| `TC-OBS-005` | Audit Logs Blocked for Patient | `GET /audit/logs` | HTTP 403 Forbidden | P1 |
| `TC-OBS-006` | Filter Audit Logs By Action | `GET /audit/logs?action=`| HTTP 200, filtered action records | P1 |
| `TC-OBS-007` | HIPAA Security Summary Stats | `GET /audit/stats` | HTTP 200, total events & success % | P1 |
| `TC-OBS-008` | Executive RCM Analytics KPIs | `GET /analytics/summary` | HTTP 200, financial & clinical counts | P0 |

### 7. HL7 FHIR Specification Validation (`qa/fhir-tests/test_fhir_compliance.py`)
| Test ID | Test Case Name | Target | Expected Result | Priority |
|---|---|---|---|---|
| `TC-FHR-001` | Patient Structure Validates | `fhir.resources.Patient` | Model validates without error | P0 |
| `TC-FHR-002` | Search Bundle Validates | `fhir.resources.Bundle` | Bundle type and entries validate | P0 |
| `TC-FHR-003` | CapabilityStatement Validates | `fhir.resources.CS` | Validates FHIR 4.0.1 conformance | P0 |
| `TC-FHR-004` | Required Fields Present | `Patient.id, meta` | Mandatory fields populated | P0 |
| `TC-FHR-005` | Gender Code Conforms to Spec | `Patient.gender` | Restricted to `[male, female, other, unknown]` | P1 |
| `TC-FHR-006` | Birth Date ISO 8601 Format | `Patient.birthDate` | Matches `YYYY-MM-DD` | P1 |
| `TC-FHR-007` | OperationOutcome Validates | `fhir.resources.OO` | Validates FHIR error schema | P0 |

### 8. Backend Unit Tests (`backend/tests/test_patient_unit.py`)
| Test ID | Test Case Name | Target | Expected Result | Priority |
|---|---|---|---|---|
| `TC-UNT-001` | Valid Patient Schema | `PatientCreate` | Pydantic model parses valid dict | P1 |
| `TC-UNT-002` | Invalid Gender Rejection | `PatientCreate` | Raises ValueError on bad gender | P1 |
| `TC-UNT-003` | Invalid Birth Date Rejection | `PatientCreate` | Raises ValueError on bad date | P1 |
| `TC-UNT-004` | Default ResourceType | `PatientCreate` | Defaults to "Patient" when omitted | P2 |
| `TC-UNT-005` | HumanName Schema Parsing | `HumanName` | Validates family and given arrays | P2 |
