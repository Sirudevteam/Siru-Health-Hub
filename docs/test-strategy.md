# Siru HealthHub — Quality Engineering & Test Strategy

> **Specification:** HL7 FHIR R4 (4.0.1) | **Version:** 2.0 (Enterprise Release) | **Coverage:** 87 Automated Tests Across 7 Suites

---

## 1. Executive QA Strategy & Objectives

The Siru HealthHub testing architecture is engineered to validate clinical correctness, HL7 FHIR R4 structural conformity, zero-trust security boundaries, revenue cycle calculation integrity, and high-concurrency availability.

### Core Objectives
1. **Clinical & FHIR Compliance**: Strict schema validation using `fhir.resources` ensuring all patient, diagnostic, and billing entities conform to HL7 FHIR 4.0.1.
2. **Data & Reference Integrity**: Cross-resource linking verification (`Patient` ↔ `Encounter` ↔ `Observation` ↔ `Condition` ↔ `MedicationRequest` ↔ `Claim`).
3. **Zero-Trust Security & RBAC**: Automated authorization boundary testing across `ADMIN`, `DOCTOR`, `NURSE`, and `PATIENT` roles, with instantaneous Redis token revocation.
4. **Payer Financial Math Accuracy**: 100% mathematical precision on insurance adjudication (90% insurer benefit / 10% patient copay) and automated policy denial triggers.
5. **Continuous Quality Gate**: Every commit and pull request must achieve a 100% green pass in GitHub Actions before deployment.
6. **High Concurrency Performance**: Validated latency under concurrent multi-persona traffic using Locust benchmarks.

---

## 2. Test Pyramid & Scope

```
                               ┌──────────────────┐
                               │  Performance &   │  Locust concurrency load suite
                               │   Stress Tests   │  (p95 < 25ms under load)
                              /└──────────────────┘\
                             /                      \
                            /  ┌──────────────────┐  \
                           /   │  E2E Lifecycle   │   \  Full patient journey &
                          /    │ & Audit Trails   │    \ HIPAA audit verification
                         /     └──────────────────┘     \
                        /                                \
                       /    ┌──────────────────────────┐  \  77 automated tests
                      /     │  FHIR, Claims & Security │   \ (API, RBAC, Claims,
                     /      │  API Test Suites         │    \ Compliance, EDI 270)
                    /       └──────────────────────────┘     \
                   /                                          \
                  /     ┌───────────────────────────────────┐  \  Fast schema &
                 /      │        Backend Unit Tests         │   \ validator checks
                /       │     (Pydantic, Model layer)       │    \ (< 0.05s)
               /─────────────────────────────────────────────\    \
              └────────────────── 87 Total Tests ───────────────────┘
```

---

## 3. Comprehensive Test Suites Breakdown

| Suite Identifier | Directory Path | Test Count | Scope & Focus |
|---|---|---|---|
| **Patient API Suite** | `qa/api-tests/test_patient.py` | 20 | Full CRUD, fuzzy/exact name search, pagination, negative inputs, FHIR headers, data integrity. |
| **Phase 2 Resource Suite** | `qa/api-tests/test_phase2_fhir_suite.py` | 11 | Practitioners, encounters, vital observations, ICD-10 conditions, prescriptions, appointments, cross-resource links. |
| **Coverage & Eligibility** | `qa/claims-tests/test_coverage_and_eligibility.py` | 6 | Policy models, real-time EDI 270/271 eligibility verification, active and expired status checks, patient isolation. |
| **Claims & Adjudication** | `qa/claims-tests/test_claims_adjudication.py` | 10 | Claims auto-adjudication, 90/10 math integrity, auto-denial on expired coverage, zero-amount rejection (422), billing RBAC. |
| **FHIR Compliance Suite** | `qa/fhir-tests/test_fhir_compliance.py` | 7 | Official HL7 FHIR R4 structural validation using `fhir.resources` for Patient, Bundle, CapabilityStatement, and OperationOutcome. |
| **Integration & Lifecycle** | `qa/integration-tests/test_patient_lifecycle.py` | 2 | End-to-end patient journey: register → examine → update → search → delete → verify audit trail. |
| **Authentication Suite** | `qa/security-tests/test_authentication.py` | 6 | OAuth2/JWT logins, invalid passwords (401), missing auth headers, malformed tokens, expired tokens, Redis instantaneous revocation. |
| **RBAC Authorization** | `qa/security-tests/test_rbac_authorization.py` | 8 | Granular role isolation: Admin superuser, Doctor prescription/diagnosis, Nurse vital signs, Patient self-record isolation. |
| **Observability & Audit** | `qa/audit-tests/test_audit_and_metrics.py` | 8 | Prometheus metrics format, HIPAA audit log user attribution, action filters, admin-only access guards, analytics summary KPIs. |
| **Backend Unit Suite** | `backend/tests/test_patient_unit.py` | 5 | Fast Pydantic model validation and error raising. |
| **TOTAL** | | **87 Tests** | **100% Automated Pass** |

---

## 4. Test Execution & Automation Tooling

| Tool | Version | Purpose |
|---|---|---|
| **pytest** | 8.3.3 | Core test runner, parameterization, and lifecycle fixtures. |
| **pytest-asyncio** | 0.24.0 | Async test support for FastAPI and SQLAlchemy 2.x asyncpg. |
| **requests** | 2.32.3 | Live HTTP client simulating real client agents and mobile apps. |
| **fhir.resources** | 7.1.0 | Official HL7 FHIR R4 schema parser and structural validator. |
| **Locust** | 2.42.1 | Distributed user simulation and concurrency load benchmarking. |
| **Ruff** | Latest | High-speed Python linter for critical syntax and runtime safety. |
| **GitHub Actions** | Ubuntu 22.04 | Automated CI/CD execution for backend unit tests and QA integration suites. |

---

## 5. Continuous Integration (CI/CD) Quality Gates

The platform enforces two automated workflows on every `push` and `pull_request` to `main` and `develop`:

1. **`Backend CI` (`.github/workflows/backend-ci.yml`)**:
   - Provisions isolated PostgreSQL 15 and Redis 7 service containers.
   - Executes backend unit test suite.
   - Enforces critical syntax and runtime linting via Ruff (`--select E9,F63,F7,F82`).
2. **`QA API Tests` (`.github/workflows/qa-ci.yml`)**:
   - Provisions clean PostgreSQL 15 and Redis 7 service containers.
   - Boots the FastAPI server and executes the automated database seeder.
   - Polls `/health` endpoint until the server is fully ready.
   - Executes all 82 QA API tests across the 6 integration test suites.

---

## 6. Performance Benchmarking Criteria (Locust)

- **Target Response Time**: p95 latency < 50ms for cached/indexed FHIR queries.
- **Target Throughput**: Minimum 50 requests per second per container under local emulation.
- **Failure Threshold**: **0.00% HTTP 5xx errors**.
- **User Scenarios**:
  - `PatientUser`: Authenticates, checks active coverage, reads medical timeline.
  - `DoctorUser`: Authenticates, searches patient records, checks observations.
  - `BillingStaffUser`: Authenticates, verifies EDI 270/271 eligibility, submits claims, inspects EOB.
