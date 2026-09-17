# Siru HealthHub — Complete API Documentation

> **Specification:** HL7 FHIR R4 (4.0.1) | **Version:** 2.0 (Production Release) | **Security:** OAuth2 Bearer JWT + RBAC

---

## 1. Overview & Base URLs

Siru HealthHub provides an asynchronous RESTful API implementing the HL7 FHIR R4 standard, healthcare revenue cycle management (RCM), and HIPAA audit observability.

| Environment | Base URL | Description |
|---|---|---|
| **Local Docker (TLS)** | `https://localhost` | Nginx TLS Reverse Proxy (Self-signed or CA cert) |
| **Local Backend Direct** | `http://localhost:8000` | Direct FastAPI Uvicorn listener (Dev / Testing) |
| **Frontend Portal** | `http://localhost:3000` | Next.js 15 App Router web client |

All clinical and insurance endpoints follow standard FHIR resource URL conventions (`/fhir/{ResourceType}`).

---

## 2. Authentication & Authorization

All endpoints (except `/health`, `/fhir/metadata`, and `/auth/login`) require a valid Bearer JWT access token.

```http
Authorization: Bearer <access_token>
```

### Pre-Seeded Test Credentials

| Username | Password | Role | Permissions |
|---|---|---|---|
| `admin` | `admin123` | `ADMIN` | Superuser: All FHIR resources, HIPAA Audit Logs (`/audit/logs`), Analytics (`/analytics/summary`), Metrics (`/metrics`). |
| `doctor.sharma` | `doctor123` | `DOCTOR` | Clinical Doctor: Read/Write Patients, Encounters, Observations, Prescribe (`MedicationRequest`), Diagnose (`Condition`), Submit Claims (`Claim`). |
| `nurse.lakshmi` | `nurse123` | `NURSE` | Nursing Staff: Read Patients, Encounters; Record Vitals (`Observation`). Forbidden from Prescribing or Diagnosing. |
| `patient.arun` | `patient123` | `PATIENT` | Patient Portal User: Strictly isolated to own records (`P1001`), own coverage (`COV1001`), and own claims. |

### Authentication Endpoints

#### `POST /auth/login`
Authenticates a user and issues short-lived access and refresh JWT tokens.

- **Request Body (JSON)**:
  ```json
  {
    "username": "doctor.sharma",
    "password": "doctor123"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "refresh_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "role": "DOCTOR",
    "username": "doctor.sharma"
  }
  ```

#### `GET /auth/me`
Retrieves identity and role information for the currently authenticated session.

#### `POST /auth/logout`
Revokes the current token instantaneously across all nodes by recording its unique ID in Redis with an auto-expiring TTL.

---

## 3. FHIR Clinical Resources Catalog

### A. Patient (`/fhir/Patient`)
- `GET /fhir/Patient`: Search patients with bundle pagination (`name`, `family`, `given`, `birthdate`, `gender`, `_count`, `_offset`, `_sort`).
- `POST /fhir/Patient`: Register a new patient. Auto-assigns logical ID `P{hex}`.
- `GET /fhir/Patient/{id}`: Fetch single patient resource.
- `PUT /fhir/Patient/{id}`: Replace or update patient details.
- `DELETE /fhir/Patient/{id}`: Soft-delete patient (`active = false`).

### B. Practitioner (`/fhir/Practitioner`)
- `GET /fhir/Practitioner`: Search licensed healthcare professionals.
- `POST /fhir/Practitioner`: Register medical personnel with qualifications.
- `GET /fhir/Practitioner/{id}`: Retrieve practitioner profile (e.g., `PR1001` Dr. Rajesh Sharma).

### C. Organization (`/fhir/Organization`)
- `GET /fhir/Organization`: Search healthcare facilities and payer organizations.
- `POST /fhir/Organization`: Create facility or insurer.
- `GET /fhir/Organization/{id}`: E.g., `ORG1001` (Apollo City Hospital) or `ORG_PAYER_1` (Star Health Insurance).

### D. Encounter (`/fhir/Encounter`)
- `GET /fhir/Encounter?patient={id}`: List all inpatient, outpatient, and ambulatory visits for a patient.
- `POST /fhir/Encounter`: Record new medical encounter linking patient and practitioner.

### E. Observation (`/fhir/Observation`)
- `GET /fhir/Observation?patient={id}&category=vital-signs`: Retrieve recorded vital signs (BP, Heart Rate, Temperature, SpO2).
- `POST /fhir/Observation`: Record vital signs or quantitative laboratory test results.

### F. Condition (`/fhir/Condition`)
- `GET /fhir/Condition?patient={id}`: List active clinical diagnoses with ICD-10 and SNOMED-CT codes.
- `POST /fhir/Condition`: Record a clinical diagnosis (Doctors and Admins only).

### G. MedicationRequest (`/fhir/MedicationRequest`)
- `GET /fhir/MedicationRequest?patient={id}`: List patient active prescription orders.
- `POST /fhir/MedicationRequest`: Authorize a prescription order (Doctors and Admins only).

### H. Appointment (`/fhir/Appointment`)
- `GET /fhir/Appointment?patient={id}`: Retrieve scheduled and completed clinical consultations.
- `POST /fhir/Appointment`: Book an appointment linking patient, practitioner, and time slot.

---

## 4. Revenue Cycle Management (RCM) & Claims Adjudication

### A. Coverage (`/fhir/Coverage`)
- `GET /fhir/Coverage?patient={id}`: Retrieve active health insurance policies.
- `POST /fhir/Coverage`: Record new insurance coverage policy.
- `POST /fhir/Coverage/{id}/eligibility-check`: Real-time EDI 270/271 simulated eligibility verification.
  - **Sample Response (200 OK)**:
    ```json
    {
      "eligible": true,
      "status": "Active Coverage",
      "policyNumber": "SH-99281-01",
      "benefitPercent": 90.0,
      "copayPercent": 10.0,
      "deductibleRemaining": 5000.0,
      "inNetwork": true
    }
    ```

### B. Claim & ClaimResponse (`/fhir/Claim`)
- `POST /fhir/Claim`: Submit institutional or professional medical claim. Automatically executes the **Payer Adjudication Engine**:
  - Validates policy coverage and eligibility.
  - Calculates **90% Insurer Benefit** and **10% Patient Copay**.
  - Auto-denies expired or invalid policies (`COV_EXPIRED`).
  - Generates an adjudicated `ClaimResponse` resource with status `complete` and itemized payment breakdown.
- `GET /fhir/Claim?patient={id}`: Search submitted claims.
- `GET /fhir/Claim/{id}/response`: Retrieve the adjudicated `ClaimResponse` (Explanation of Benefits).

---

## 5. Observability, HIPAA Audit & Analytics

### A. Prometheus Metrics
- `GET /metrics`: Standard OpenMetrics text stream for Prometheus scrapers and Datadog agents.
  - `http_requests_total`: Request counts partitioned by method, path, and HTTP status.
  - `http_request_duration_seconds`: Histogram measuring execution latency.
  - `fhir_resources_count`: Gauge tracking total active resources in PostgreSQL.
  - `auth_events_total`: Authentication success and failure counters.

### B. HIPAA Audit API (`/audit/*`)
- `GET /audit/logs`: Filterable compliance query endpoint.
  - Query parameters: `user_id`, `action` (`CREATE`, `READ`, `UPDATE`, `DELETE`, `SEARCH`), `resource_type`, `result` (`SUCCESS`, `FAILURE`), `status_code`, `limit`, `offset`.
  - Restricted to: `ADMIN`.
- `GET /audit/stats`: Aggregated security and compliance metrics (total events, success rate %, breakdown by action and resource).

### C. Executive Analytics (`/analytics/summary`)
- `GET /analytics/summary`: Comprehensive hospital RCM and clinical performance KPI summary.
  - Financial Metrics: Total Billed Amount, Insurer Reimbursements, Patient Copays, Clean Claim Rate %, Denial Rate %.
  - Clinical Census: Total Patients, Practitioners, Encounters, and Claims.

---

## 6. Standard FHIR Error Handling

All non-2xx responses return a compliant HL7 FHIR `OperationOutcome`:

```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "not-found",
      "diagnostics": "Patient/NONEXISTENT-99999 not found"
    }
  ]
}
```
