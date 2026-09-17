```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗██╗██████╗ ██╗   ██╗    ██╗  ██╗███████╗ █████╗    ║
║   ██╔════╝██║██╔══██╗██║   ██║    ██║  ██║██╔════╝██╔══██╗   ║
║   ███████╗██║██████╔╝██║   ██║    ███████║█████╗  ███████║   ║
║   ╚════██║██║██╔══██╗██║   ██║    ██╔══██║██╔══╝  ██╔══██║   ║
║   ███████║██║██║  ██║╚██████╔╝    ██║  ██║███████╗██║  ██║   ║
║   ╚══════╝╚═╝╚═╝  ╚═╝ ╚═════╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ║
║                                                               ║
║              H E A L T H   H U B                             ║
║       Enterprise FHIR R4 Healthcare & Claims Platform        ║
╚═══════════════════════════════════════════════════════════════╝
```

[![Backend CI](https://github.com/Sirudevteam/Siru-Health-Hub/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Sirudevteam/Siru-Health-Hub/actions/workflows/backend-ci.yml)
[![QA API Tests](https://github.com/Sirudevteam/Siru-Health-Hub/actions/workflows/qa-ci.yml/badge.svg)](https://github.com/Sirudevteam/Siru-Health-Hub/actions/workflows/qa-ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-87%2F87%20Passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Overview

**Siru HealthHub** is an enterprise-grade, end-to-end **HL7 FHIR R4-compliant** healthcare platform built for hospital networks, clinical providers, and health insurance payers. The platform combines a high-performance async REST API, real-time insurance eligibility (EDI 270/271) & automated claims adjudication, role-based access control (RBAC) with instantaneous Redis token revocation, HIPAA-compliant audit logging, Prometheus observability, and an executive Next.js 15 patient and administrative portal.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 CLIENT LAYER                                    │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐   │
│   │  Patient / Provider │   │  Compliance Officer │   │  Prometheus Scraper │   │
│   │  Next.js 15 App     │   │  Admin Portal       │   │  / Datadog Agent    │   │
│   │  (:3000)            │   │  (/admin/audit)     │   │  (:443 /metrics)    │   │
│   └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘   │
└──────────────┼─────────────────────────┼─────────────────────────┼──────────────┘
               │                         │                         │
               ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      REVERSE PROXY & SECURITY GATEWAY (Nginx)                   │
│   - TLS 1.2 / 1.3 Termination (Port 443 -> Internal Services)                   │
│   - Automatic HTTP (Port 80) -> HTTPS (Port 443) Redirection                    │
│   - Security Headers (HSTS, X-Content-Type-Options, X-Frame-Options, CSP)       │
│   - Reverse Proxy Routing:                                                      │
│       * `/fhir/*`, `/auth/*`, `/audit/*`, `/analytics/*`, `/metrics` -> Backend │
│       * `/` and all other web paths -> Next.js Frontend                         │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │ Internal Network                          │
                   ▼                                           ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│       NEXT.js 15 FRONTEND CONTAINER  │    │     FASTAPI ASYNC BACKEND CONTAINER  │
│ - App Router + React 18 + TypeScript │    │ - Python 3.11 + Uvicorn Async Server │
│ - EHR Vitals & Condition Tracker     │    │ - Pydantic v2 + fhir.resources       │
│ - 270/271 Real-Time Eligibility UI   │    │ - Observability & Audit Middlewares  │
│ - Claims Submission & EOB Viewer     │    │ - Claims Auto-Adjudication Engine    │
│ - Admin Audit Explorer & Analytics   │    │ - OAuth2 / JWT Auth & RBAC Guards    │
└──────────────────────────────────────┘    └──────────────────┬───────────────────┘
                                                               │
                                       ┌───────────────────────┴──────────────────┐
                                       ▼                                          ▼
                   ┌──────────────────────────────────────┐   ┌──────────────────────────────────┐
                   │    REDIS 7 DISTRIBUTED CACHE LAYER   │   │  POSTGRESQL 15 RELATIONAL STORE  │
                   │ - Instant Token Revocation (Logout)  │   │ - JSONB FHIR Resource Storage    │
                   │ - Ephemeral Expiration TTLs          │   │ - GIN Trigram & B-Tree Indexes   │
                   │ - High-speed Session Validation      │   │ - Complete HIPAA AuditLog Store  │
                   └──────────────────────────────────────┘   └──────────────────────────────────┘
```

---

## Key Features

1. **Complete HL7 FHIR R4 Suite**: 10 interconnected clinical and financial resources:
   - `Patient`, `Practitioner`, `Organization`, `Encounter`, `Observation`, `Condition`, `MedicationRequest`, `Appointment`, `Coverage`, `Claim`, and `ClaimResponse`.
2. **Revenue Cycle Management (RCM) & Adjudication**:
   - **EDI 270/271 Simulation**: Real-time insurance eligibility checks (`/fhir/Coverage/{id}/eligibility-check`).
   - **Claims Adjudication Rules Engine**: Automatic calculation of 90% insurer reimbursement / 10% patient copay, with instant auto-denial triggers for expired policies (`COV_EXPIRED`).
3. **Zero-Trust Security & RBAC**:
   - OAuth 2.0 / JWT Bearer authentication with bcrypt password hashing.
   - Granular RBAC enforcement (`ADMIN`, `DOCTOR`, `NURSE`, `PATIENT`).
   - **Instantaneous Redis Blacklisting**: Revokes tokens immediately on logout via distributed Redis cache.
4. **HIPAA Audit Logging & Compliance**:
   - Every read, create, update, and search is logged to PostgreSQL with timestamp, actor user ID, HTTP status, and IP address.
   - Searchable **Audit Log Explorer UI** (`/admin/audit`).
5. **Observability & Executive Analytics**:
   - **Prometheus Metrics** (`/metrics`): Request rate counters, HTTP duration histograms, FHIR resource gauges.
   - **Executive Analytics Dashboard** (`/admin/analytics`): Live KPI cards for total billed revenue, insurer reimbursements, clean claim rates, denial percentages, and population census.
6. **Production Packaging & Tooling**:
   - Automated deployment health verifier (`scripts/verify_deployment.py`).
   - Automated database backup & restore utilities (`scripts/backup_db.sh` & `scripts/restore_db.sh`).
   - GitHub Actions CI/CD workflows for backend unit testing and full QA suite execution.

---

## Pre-Seeded Test Credentials

| Username | Password | Role | Permissions |
|---|---|---|---|
| `admin` | `admin123` | `ADMIN` | Superuser: All FHIR resources, HIPAA Audit Logs (`/audit/logs`), Analytics (`/analytics/summary`), Metrics (`/metrics`). |
| `doctor.sharma` | `doctor123` | `DOCTOR` | Clinical Doctor: Read/Write Patients, Encounters, Observations, Prescribe (`MedicationRequest`), Diagnose (`Condition`), Submit Claims (`Claim`). |
| `nurse.lakshmi` | `nurse123` | `NURSE` | Nursing Staff: Read Patients, Encounters; Record Vitals (`Observation`). Forbidden from Prescribing or Diagnosing. |
| `patient.arun` | `patient123` | `PATIENT` | Patient Portal User: Strictly isolated to own records (`P1001`), own coverage (`COV1001`), and own claims. |

---

## Quick Start

### 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) (≥ 24.x)
- Python 3.11+
- OpenSSL (for TLS certificate generation)

### 2. Generate TLS Certificates
```bash
# Linux / macOS / WSL
bash docker/nginx/generate-certs.sh

# Windows PowerShell
.\docker\nginx\generate-certs.ps1
```

### 3. Configure Environment
```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

### 4. Start Multi-Container Stack
```bash
docker compose up -d --build
```

### 5. Verify Deployment Health
```bash
python scripts/verify_deployment.py
```

### 6. Access Applications
- **Patient & Provider Portal**: [http://localhost:3000](http://localhost:3000)
- **Executive Analytics Dashboard**: [http://localhost:3000/admin/analytics](http://localhost:3000/admin/analytics)
- **HIPAA Audit Log Explorer**: [http://localhost:3000/admin/audit](http://localhost:3000/admin/audit)
- **FHIR R4 Metadata (TLS)**: [https://localhost/fhir/metadata](https://localhost/fhir/metadata)
- **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## Automated QA Testing Suite

Siru HealthHub includes **87 automated tests** spanning 6 QA test suites and backend unit tests.

```powershell
# Run the complete QA integration and contract suite (82 tests)
python -m pytest qa/ -v

# Run backend unit tests (5 tests)
python -m pytest backend/tests/ -v
```

### Test Coverage Breakdown
| Test Suite | Directory | Tests | Focus |
|---|---|---|---|
| **Patient API Tests** | `qa/api-tests/test_patient.py` | 20 | CRUD, pagination, validation, negative paths, data integrity. |
| **Phase 2 Resource Suite** | `qa/api-tests/test_phase2_fhir_suite.py` | 11 | Practitioners, encounters, vitals, prescriptions, diagnoses, cross-resource links. |
| **Claims & Adjudication** | `qa/claims-tests/test_claims_adjudication.py` | 10 | Auto-adjudication, financial math integrity, auto-denials, billing RBAC. |
| **Coverage & Eligibility** | `qa/claims-tests/test_coverage_and_eligibility.py` | 6 | EDI 270/271 real-time eligibility checks, policy dates, patient isolation. |
| **FHIR Compliance** | `qa/fhir-tests/test_fhir_compliance.py` | 7 | Structural validation against official HL7 FHIR specification via `fhir.resources`. |
| **Integration & Lifecycle** | `qa/integration-tests/test_patient_lifecycle.py` | 2 | End-to-end patient lifecycle and audit trail verification. |
| **Authentication QA** | `qa/security-tests/test_authentication.py` | 6 | OAuth2/JWT logins, invalid passwords, expired/malformed tokens, Redis revocation. |
| **RBAC Authorization** | `qa/security-tests/test_rbac_authorization.py` | 8 | Role boundaries across Admin, Doctor, Nurse, and Patient personas. |
| **Observability & Audit** | `qa/audit-tests/test_audit_and_metrics.py` | 8 | Prometheus metrics format, HIPAA audit attribution, admin-only restrictions, analytics KPIs. |
| **Backend Unit Tests** | `backend/tests/test_patient_unit.py` | 5 | Pydantic schema validation. |
| **Total Automated Tests** | | **87 / 87 Passed (100%)** | |

---

## Performance & Load Benchmarks (Locust)

```powershell
locust -f qa/performance-tests/locustfile.py --headless -u 10 -r 5 --run-time 15s --host http://localhost:8000
```
- **Concurrency**: 10 simultaneous users across Patient, Doctor, and Billing personas.
- **HTTP Failure Rate**: **0.00%**
- **Median Latency**:
  - `GET /fhir/Patient/{id}`: 6 ms
  - `GET /fhir/Claim?patient`: 10 ms
  - `GET /analytics/summary`: 12 ms
  - `GET /metrics`: 8 ms

---

## Database Backup & Restore

```bash
# Backup PostgreSQL to timestamped archive
bash scripts/backup_db.sh          # Linux / Bash
powershell -File scripts/backup_db.ps1   # Windows PowerShell

# Restore database from dump
bash scripts/restore_db.sh ./backups/siru_fhir_backup_20260917_115408.sql
powershell -File scripts/restore_db.ps1 -BackupFile .\backups\siru_fhir_backup_20260917_115408.sql
```

---

## Project Structure

```
Siru Health Hub/
├── .github/workflows/          # CI/CD Workflows (backend-ci.yml, qa-ci.yml)
├── backend/                    # FastAPI Async Backend
│   ├── app/
│   │   ├── analytics/          # Executive RCM & Clinical Analytics Router
│   │   ├── audit/              # HIPAA Audit Middleware & Query Router
│   │   ├── auth/               # OAuth2 / JWT Auth, Password Hashing & Redis Blacklist
│   │   ├── database/           # SQLAlchemy 2.x Async Engine & Models
│   │   ├── fhir/               # 10 FHIR Resource Routers & Schemas
│   │   ├── observability/      # Prometheus Metrics Middleware & Exporter
│   │   ├── rcm/                # Claims Adjudication Rules Engine
│   │   └── main.py             # FastAPI Application Entrypoint
│   ├── tests/                  # Backend Unit Tests
│   └── Dockerfile              # Multi-stage Python 3.11 Runtime
├── docker/
│   ├── nginx/                  # Nginx TLS Reverse Proxy Configuration & Certs
│   └── postgres/               # PostgreSQL Initialization & Realistic Clinical Seeding
├── frontend/                   # Next.js 15 App Router Frontend
│   └── src/
│       ├── app/                # Pages: Dashboard, Patients, Clinical EHR, Admin Analytics, Audit Explorer
│       ├── components/         # Reusable UI Components (Cards, Badges, Timelines, Billing)
│       └── lib/                # API Client & Utilities
├── qa/                         # Automated QA & Compliance Test Suites
│   ├── api-tests/              # Patient & Resource Relationship Tests
│   ├── audit-tests/            # HIPAA Audit & Prometheus Metrics Tests
│   ├── claims-tests/           # Eligibility & Claims Adjudication Tests
│   ├── fhir-tests/             # HL7 FHIR Specification Validation
│   ├── integration-tests/      # End-to-End Lifecycle Tests
│   ├── performance-tests/      # Locust Concurrency Benchmarks
│   └── security-tests/         # Authentication & RBAC Tests
├── scripts/                    # Operational Scripts (Backup, Restore, Verification)
├── docs/                       # Architecture, API Documentation, Deployment Guide
├── docker-compose.yml          # Multi-Container Orchestration (Postgres, Redis, Backend, Frontend, Nginx)
├── .env.example                # Development Environment Variables
└── .env.production.example     # Production Hardened Environment Template
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
