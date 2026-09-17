# Siru HealthHub — Test Plan (Phase 1)

> **Document:** Test Plan v1.0 | **Phase:** 1 — Foundation  
> **Date:** September 2026 | **Prepared by:** Siru QA Team

---

## 1. Test Scope

### In Scope
- REST API endpoints:
  - `GET /health`
  - `GET /fhir/metadata`
  - `POST /fhir/Patient`
  - `GET /fhir/Patient`
  - `GET /fhir/Patient/{id}`
  - `PUT /fhir/Patient/{id}`
  - `DELETE /fhir/Patient/{id}`
  - `GET /fhir/Patient?<search params>`
- FHIR R4 structural compliance
- HTTP status code correctness
- Request validation (400, 422 error paths)
- Data persistence and round-trip integrity
- Response header validation (Content-Type, Location)

### Out of Scope
- Authentication and authorization (Phase 3)
- Rate limiting (Phase 3)
- UI / Mobile application
- Observation, Condition, Medication resources (Phase 2+)
- Load and performance testing (Phase 4)
- HIPAA compliance (Phase 6)

---

## 2. Test Environment

| Environment | URL | Notes |
|-------------|-----|-------|
| Local Docker | `http://localhost:8000` | `docker compose up` |
| CI/CD (GitHub Actions) | Internal container network | Spun up per pipeline run |
| Staging | `https://api-staging.siru.health` | Post-merge deploy |

**Services required:**
```
API container:        localhost:8000
PostgreSQL container: localhost:5432
Nginx (optional):     localhost:80
```

**Environment variables:**
```env
BASE_URL=http://localhost:8000
DATABASE_URL=postgresql://postgres:password@localhost:5432/siruhealthhub
```

**Start test environment:**
```bash
docker compose up -d
cd qa && pip install -r requirements.txt
pytest --tb=short -v
```

---

## 3. Entry & Exit Criteria

### Entry Criteria
- [ ] Docker Compose stack is running (`api`, `db` services healthy)
- [ ] `GET /health` returns `200 { status: ok }`
- [ ] Test dependencies installed (`pip install -r qa/requirements.txt`)
- [ ] `.env` configured with correct `BASE_URL`

### Exit Criteria
- [ ] All 20 test cases (TC-001 to TC-020) executed
- [ ] Pass rate ≥ 95% (at most 1 non-critical failure)
- [ ] Zero P0 or P1 defects outstanding
- [ ] Allure test report generated and reviewed
- [ ] All FHIR compliance tests pass (fhir.resources validation)

---

## 4. Test Cases

| ID | Test Case Name | Precondition | Steps | Expected Result | Priority |
|----|----------------|--------------|-------|-----------------|----------|
| TC-001 | Health Check Returns 200 | API is running | GET `/health` | HTTP 200, body `{"status": "ok"}` | P0 |
| TC-002 | FHIR Capability Statement | API is running | GET `/fhir/metadata` | HTTP 200, `resourceType=CapabilityStatement`, `fhirVersion=4.0.1` | P0 |
| TC-003 | Create Patient — Success 201 | API is running | POST `/fhir/Patient` with valid Patient body | HTTP 201, `resourceType=Patient`, `id` set, `meta.lastUpdated` set, `Location` header present | P0 |
| TC-004 | Create Patient — FHIR Meta Fields | API is running | POST `/fhir/Patient` | Response has `meta.versionId` and `meta.lastUpdated` | P1 |
| TC-005 | Get Patient by ID — Success | Patient exists (from TC-003) | GET `/fhir/Patient/{id}` | HTTP 200, `resourceType=Patient`, correct `id`, matching `name.family` | P0 |
| TC-006 | Get Patient — Not Found 404 | No such patient | GET `/fhir/Patient/NONEXISTENT-99999` | HTTP 404, `resourceType=OperationOutcome` | P1 |
| TC-007 | Update Patient — birthDate | Patient exists | PUT `/fhir/Patient/{id}` with changed `birthDate` | HTTP 200, response shows new `birthDate` | P1 |
| TC-008 | Delete Patient — 204 + Verify 404 | Patient exists | DELETE `/fhir/Patient/{id}`, then GET same ID | DELETE → 204 no body; GET → 404 | P1 |
| TC-009 | Invalid JSON — 400 or 422 | API is running | POST `/fhir/Patient` with plain string body | HTTP 400 or 422 | P1 |
| TC-010 | Invalid resourceType — 422 | API is running | POST with `resourceType: Elephant` | HTTP 422 | P1 |
| TC-011 | Invalid Gender — 422 | API is running | POST with `gender: purple` | HTTP 422 | P1 |
| TC-012 | Invalid birthDate — 422 | API is running | POST with `birthDate: not-a-date` | HTTP 422 | P1 |
| TC-013 | Search — Returns FHIR Bundle | API is running | GET `/fhir/Patient` | HTTP 200, `resourceType=Bundle`, `total` field present | P0 |
| TC-014 | Search by Name | Patient with family=Searchable exists | GET `/fhir/Patient?name=Searchable` | Bundle contains entry with `name.family=Searchable` | P1 |
| TC-015 | Search by Gender — Filter Correct | Male patients exist | GET `/fhir/Patient?gender=male` | All entries have `gender=male` | P1 |
| TC-016 | Pagination — _count=1 | At least 1 patient exists | GET `/fhir/Patient?_count=1` | Bundle entry array has ≤ 1 item | P2 |
| TC-017 | Search Empty Result | No patient with name ZZZ... | GET `/fhir/Patient?name=ZZZ_NONEXISTENT_NAME_XYZ` | HTTP 200, `total=0`, empty/absent `entry` | P2 |
| TC-018 | Content-Type Header — JSON | API is running | GET `/fhir/Patient` | `Content-Type` response header contains `json` | P2 |
| TC-019 | Wrong HTTP Method — 405 | API is running | PATCH `/fhir/Patient` | HTTP 405 Method Not Allowed | P2 |
| TC-020 | Data Integrity — Round-trip | API is running | POST patient with DOB `1995-05-10`, family `TestIntegrity`; GET by ID | `birthDate==1995-05-10`, `name[0].family==TestIntegrity` exactly | P1 |

---

## 5. Risk & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API not running when tests execute | Medium | High | Add pre-test health check assertion that fails fast with clear message |
| Database state pollution between tests | Medium | Medium | Each test cleans up its own data; session teardown deletes tracked IDs |
| FHIR spec version drift (fhir.resources update) | Low | Medium | Pin `fhir.resources==7.1.0` in requirements.txt; review on each update |
| Flaky tests due to network timeouts | Low | Low | All requests use `timeout=30`; retry logic in CI pipeline |
| Soft-deleted patients appearing in search | Medium | High | Explicitly assert deleted patient IDs absent from post-delete search results |
| CI pipeline PostgreSQL startup race condition | Medium | Medium | Add `wait-for-it` healthcheck in docker-compose before tests run |
| Data type coercion masking integrity bugs | Low | High | TC-020 explicitly checks exact string equality for dates and names |
