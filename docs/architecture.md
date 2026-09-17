# Siru HealthHub — System Architecture

> **Version:** 2.0 (Production Release) | **Specification:** HL7 FHIR R4 (4.0.1) | **Status:** Enterprise Production Ready

---

## 1. Executive Summary

**Siru HealthHub** is a production-grade, end-to-end FHIR R4 healthcare platform built for hospital networks, clinical teams, and health insurance payers. The platform combines a high-performance async REST API, real-time insurance eligibility (EDI 270/271) & claims auto-adjudication, role-based access control (RBAC) with instantaneous Redis token revocation, HIPAA-compliant audit logging, Prometheus observability, and an executive Next.js 15 patient and administrative portal.

### Core Architectural Principles
- **HL7 FHIR R4 First**: All clinical and financial models conform strictly to FHIR R4 specifications (`fhir.resources` validation).
- **Asynchronous & Concurrent**: Built on Python 3.11 with FastAPI and SQLAlchemy 2.x asyncpg for high throughput with minimal latency.
- **Defense in Depth**: Zero-trust API design with bcrypt hashing, OAuth2 Bearer JWTs, Redis distributed token revocation, and granular RBAC.
- **Compliance & Traceability**: Every read, mutation, and failed authorization is recorded in indexed audit tables with acting user attribution and IP coordinates.
- **Enterprise Observability**: Native Prometheus latency histograms and counters alongside aggregated financial and clinical KPIs.

---

## 2. End-to-End System Topology

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 CLIENT LAYER                                    │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐   │
│   │  Patient / Provider │   │  Compliance Officer │   │  Prometheus Scraper │   │
│   │  Next.js 15 App     │   │  Admin Portal       │   │  / Datadog Agent    │   │
│   │  (Port 3000)        │   │  (/admin/audit)     │   │  (:443 /metrics)    │   │
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

## 3. Subsystem Deep Dives

### A. Clinical FHIR Ecosystem & Relationships
The backend models 10 standard HL7 FHIR R4 resources interconnected through strict reference linking:
1. **Patient**: Master patient demographic and clinical index.
2. **Practitioner**: Licensed medical staff (Physicians, Nurses, Specialists).
3. **Organization**: Hospitals, Clinics, and Payer Insurance entities.
4. **Encounter**: Inpatient, outpatient, and ambulatory care visits.
5. **Observation**: Vital signs (BP, HR, Temp, SpO2) and quantitative laboratory findings.
6. **Condition**: Diagnoses mapped to ICD-10 and SNOMED-CT terminologies.
7. **MedicationRequest**: Prescription orders with dosage instructions and intents.
8. **Appointment**: Scheduled visits with status and participant references.
9. **Coverage**: Insurance policies, group numbers, copay rates, and validity windows.
10. **Claim & ClaimResponse**: Institutional/professional billings and adjudicated explanation of benefits.

### B. Payer Adjudication & Real-Time Eligibility Engine
- **EDI 270/271 Simulation** (`POST /fhir/Coverage/{id}/eligibility-check`):
  Evaluates policy active status, effective date ranges, in-network coverage benefits, and deductible remaining balances.
- **Automated Claims Adjudication Engine** (`backend/app/rcm/adjudication.py`):
  Executes rule-based claims processing:
  - Validates active coverage and participating provider.
  - Automatically calculates itemized benefit math: **90% Insurer Reimbursement**, **10% Patient Copay**.
  - Triggers automated denials with strict error diagnostic codes for expired or cancelled policies (`COV_EXPIRED`).
  - Emits FHIR R4 compliant `ClaimResponse` records with item-level adjudication breakdowns.

### C. Security, Authentication & Redis Token Revocation
- **User Personas & Roles**:
  - `ADMIN`: Full superuser access to all resources, system metrics, HIPAA logs, and analytics.
  - `DOCTOR`: Authorized to prescribe medications, diagnose conditions, review patient charts, and submit claims.
  - `NURSE`: Authorized to record vital sign observations and view patient records; forbidden from diagnosing or prescribing.
  - `PATIENT`: Strictly constrained to their own personal FHIR records, coverages, and claim explanations.
- **Distributed Token Blacklisting**:
  When a user logs out via `POST /auth/logout`, the JWT's unique token ID (`jti`) is stored in Redis with a TTL matching the token's remaining lifetime. Every subsequent API request verifies whether the token exists in the Redis blacklist, achieving instantaneous global revocation without database roundtrips.

### D. Observability, HIPAA Audit & Analytics
- **Audit Middleware**:
  Intercepts all requests, extracts the acting user's JWT identity, client IP, action (`CREATE`, `READ`, `UPDATE`, `DELETE`, `SEARCH`), target resource, and HTTP status code. Logs are persisted to PostgreSQL `audit_logs` asynchronously via background tasks.
- **Prometheus Metrics**:
  Exposes `/metrics` in standard OpenMetrics format:
  - `http_requests_total`: Throughput counter labeled by method, endpoint, and status.
  - `http_request_duration_seconds`: High-resolution latency histogram.
  - `fhir_resources_count`: Gauge tracking total managed FHIR resources by type.
  - `auth_events_total`: Counter tracking successful and failed authentication events.
- **Executive RCM Analytics**:
  The `/analytics/summary` endpoint computes aggregated hospital performance metrics: Total Billed Volume, Total Insurer Paid, Total Patient Copay, Clean Claim Rate %, Denial Rate %, and Population Census.

---

## 4. Database Architecture & Indexing Strategy

PostgreSQL 15 is configured with both relational schema constraints and GIN-indexed JSONB for hybrid querying:

```sql
-- Patients table
CREATE TABLE patients (
    id              VARCHAR(64) PRIMARY KEY,
    family_name     VARCHAR(255),
    given_name      VARCHAR(255),
    gender          VARCHAR(32),
    birth_date      DATE,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    fhir_json       JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigram index for fuzzy patient name searches
CREATE INDEX idx_patients_family_name ON patients USING gin (family_name gin_trgm_ops);
CREATE INDEX idx_patients_given_name ON patients USING gin (given_name gin_trgm_ops);

-- JSONB index for deep FHIR document inspection
CREATE INDEX idx_patients_fhir_json ON patients USING gin (fhir_json);

-- Audit logs index for fast compliance filtering
CREATE INDEX idx_audit_logs_timestamp ON audit_logs (timestamp DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs (user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs (resource_type, resource_id);
```

---

## 5. Network & Port Configuration

| Service | Internal Host / Port | External Public Port | Protocol | Security |
|---|---|---|---|---|
| **Nginx Reverse Proxy** | `nginx:443` | `80` (Redirect), `443` (TLS) | HTTPS | TLS 1.2 / 1.3, Strict Headers |
| **FastAPI Backend** | `backend:8000` | Proxied via `/fhir/`, `/auth/` | HTTP (Internal) | Bearer JWT, Redis Blacklist |
| **Next.js Frontend** | `frontend:3000` | Proxied via `/` | HTTP (Internal) | Next.js App Router |
| **Redis 7** | `redis:6379` | `6379` (Local Dev only) | RESP | Isolated Docker Network |
| **PostgreSQL 15** | `postgres:5432` | `5432` (Local Dev only) | PostgreSQL Wire | Credentials, Volume Mount |
