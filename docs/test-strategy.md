# Siru HealthHub — Test Strategy

> **Version:** 1.0 | **Date:** September 2026 | **Owner:** QA Team

---

## 1. Test Objectives & Scope

### Objectives
1. **Functional correctness** — Every FHIR API endpoint behaves per specification
2. **FHIR R4 compliance** — All responses are parseable as valid FHIR resources
3. **Data integrity** — Values written to the system are returned unchanged
4. **Error handling** — Invalid inputs are rejected with proper FHIR OperationOutcome responses
5. **Regression prevention** — Automated test suite gates every code change via CI/CD
6. **Performance baseline** — API handles target load without degradation

### In Scope (Phase 1)
- Patient CRUD API (`/fhir/Patient`)
- FHIR metadata endpoint (`/fhir/metadata`)
- Health check endpoint (`/health`)
- FHIR R4 structural compliance
- Data persistence and round-trip integrity
- Error response validation (4xx)

### Out of Scope (Phase 1)
- Authentication / Authorization flows (Phase 3)
- Observation, Condition, Encounter resources (Phase 2+)
- Performance/load testing at scale (Phase 4)
- Mobile application UI testing
- HIPAA compliance audit (Phase 6)

---

## 2. Test Pyramid

```
                        ┌───────────────────┐
                        │   Performance /   │  ← Fewest tests, highest cost
                        │    Load Tests     │     Locust, k6
                       /└───────────────────┘\
                      /                       \
                     /  ┌─────────────────┐    \
                    /   │  E2E / Lifecycle │     \
                   /    │  Integration    │      \
                  /     └─────────────────┘       \
                 /                                  \
                /    ┌──────────────────────────┐    \
               /     │  API Tests / FHIR Tests  │     \
              /      │  (pytest + requests)     │      \
             /       └──────────────────────────┘       \
            /                                            \
           /     ┌────────────────────────────────────┐   \
          /      │         Unit Tests                 │    \
         /       │  (pytest, service / model layer)   │     \
        /─────────────────────────────────────────────/      \
       └────────────────── Most tests ───────────────────────┘
```

---

## 3. Test Types

| Type | Description | Tool | Coverage Goal |
|------|-------------|------|---------------|
| **Unit** | Test individual functions, service methods, validators in isolation | pytest, unittest.mock | 80%+ line coverage |
| **Integration** | Test service interactions with the database (PatientService + PostgreSQL) | pytest, SQLAlchemy | All CRUD paths |
| **API** | Black-box HTTP tests against the live API | pytest + requests | All endpoints + status codes |
| **FHIR Compliance** | Structural validation of responses against FHIR R4 spec | fhir.resources | All resource types returned |
| **Security** | OWASP Top-10 scans, injection tests, header analysis | OWASP ZAP, bandit | Phase 3+ |
| **Performance** | Load/stress testing, latency benchmarks under concurrent users | Locust | Phase 4 |
| **Negative** | Verify graceful rejection of invalid inputs | pytest + requests | All validation boundaries |

---

## 4. Test Tools

| Tool | Version | Purpose |
|------|---------|--------|
| **pytest** | 8.3.3 | Test runner, fixture management, parameterization |
| **pytest-asyncio** | 0.24.0 | Async test support for future async endpoints |
| **requests** | 2.32.3 | HTTP client for API tests |
| **httpx** | 0.27.2 | Async HTTP client (future use) |
| **fhir.resources** | 7.1.0 | FHIR R4 structural validation |
| **allure-pytest** | 2.13.5 | Rich HTML test reports with steps, attachments, history |
| **python-dotenv** | 1.0.1 | Environment configuration management |
| **rich** | 13.9.1 | Enhanced terminal output during test runs |
| **Locust** | Latest | Load and performance testing (Phase 4) |
| **OWASP ZAP** | 2.14+ | Security scanning (Phase 3) |
| **Postman / Newman** | Latest | Manual + automated collection-based API tests |

---

## 5. Test Data Strategy

### Synthetic Data
All test data is **synthetic** — no real patient data is ever used in tests. Test patients use:
- Generic names: `Kumar`, `Searchable`, `TestIntegrity`, `LifecycleTest`
- Phone numbers with obvious test prefixes: `+91-9000000001`
- Non-real addresses: `123 Health Street, Chennai`

### Seed Data
For complex search and filter tests, a `conftest.py` session fixture creates a known data set at test-session start and cleans it up at teardown.

### Isolation
- Each test creates its own patient and cleans up (DELETE) in teardown
- `created_patient_ids` session-scoped list tracks all created resources
- Session teardown sends DELETE for all tracked IDs
- Tests are designed to be **order-independent** and **idempotent**

### Data Boundaries Tested
- Minimum valid patient: `resourceType + name + gender`
- Maximum field length boundaries
- Unicode names
- Edge-case dates: `0001-01-01`, `9999-12-31`

---

## 6. FHIR Compliance Approach

FHIR compliance is validated at two levels:

**Level 1 — Structural validation** (automated, every test run)
- `fhir.resources` library parses all API responses
- `Patient.model_validate()`, `Bundle.model_validate()`, `OperationOutcome.model_validate()`
- Raises `ValidationError` if response violates FHIR R4 schema

**Level 2 — Semantic validation** (planned, Phase 2)
- HAPI FHIR Validator integration
- Value set binding checks
- Profile conformance (HL7 AU Base Patient profile)

**Level 3 — Interoperability** (Phase 5)
- Cross-system exchange tests with HAPI FHIR reference server
- CDA / HL7 v2 import validation

---

## 7. Defect Management

| Severity | Definition | SLA (Fix) | Example |
|----------|------------|-----------|--------|
| **P0 — Critical** | API down, data loss, security breach | 4 hours | 500 on all endpoints |
| **P1 — High** | Core FHIR operation broken (POST/GET/PUT/DELETE) | 24 hours | Patient create returns 500 |
| **P2 — Medium** | Non-critical endpoint failure, bad error message | 72 hours | Wrong status code on validation error |
| **P3 — Low** | Documentation mismatch, minor UI inconsistency | Next sprint | Wrong field name in response example |

All defects are tracked in GitHub Issues with labels: `bug`, `severity:P0/P1/P2/P3`, `component:api/db/fhir`.

---

## 8. CI/CD Integration

```
GitHub PR Created
       │
       ▼
┌─────────────────────────────────┐
│  GitHub Actions — CI Pipeline   │
│                                 │
│  1. Lint (ruff, mypy)           │
│  2. Unit Tests (pytest)         │
│  3. Docker Compose Up           │
│  4. API Tests (pytest qa/)      │
│  5. FHIR Compliance Tests       │
│  6. Integration Tests           │
│  7. Allure Report Generated     │
│  8. Docker Compose Down         │
│                                 │
│  ✅ All pass → PR mergeable     │
│  ❌ Any fail → PR blocked       │
└─────────────────────────────────┘
       │
       ▼
   Merge to main
       │
       ▼
   Deploy to Staging
       │
       ▼
   Smoke Tests vs Staging
```

**Test run command:**
```bash
cd qa && pytest --tb=short -v --alluredir=allure-results
allure serve allure-results
```

---

## 9. Phase-by-Phase QA Plan

| Phase | Focus | Test Types | Coverage Goal | Exit Criteria |
|-------|-------|-----------|----------------|---------------|
| **Phase 1** | Patient CRUD, FHIR basics | API, FHIR Compliance, Integration, Negative | 90% endpoint coverage | All 20 TC pass, 0 P0/P1 defects |
| **Phase 2** | Observation, Condition, Search | API, Unit, FHIR Compliance | +30 test cases | New resources FHIR-compliant |
| **Phase 3** | Auth, RBAC, Security | Security (OWASP ZAP), Auth flow | 100% auth path coverage | No OWASP Top-10 vulnerabilities |
| **Phase 4** | Performance, Observability | Load (Locust), Stress, Endurance | 100 concurrent users at p95 < 500ms | Performance baseline established |
| **Phase 5** | AI features, DiagnosticReport | E2E, API, AI output validation | Full FHIR R4 resource coverage | All resources validate against spec |
| **Phase 6** | Compliance, Scale | Compliance audit, Penetration test | HIPAA / DPDPA controls mapped | Compliance certification obtained |

---

## 10. Sample Test Cases

| ID | Description | Type | Priority | Status |
|----|-------------|------|----------|--------|
| TC-001 | Health check returns 200 with status=ok | API (Smoke) | P0 | ✅ Automated |
| TC-002 | FHIR metadata returns CapabilityStatement | API (Smoke) | P0 | ✅ Automated |
| TC-003 | Create patient returns 201 with id and meta | API (Smoke) | P0 | ✅ Automated |
| TC-004 | Create patient response has meta.versionId | FHIR Compliance | P1 | ✅ Automated |
| TC-005 | GET patient by ID returns correct data | API | P0 | ✅ Automated |
| TC-006 | GET nonexistent patient returns 404 + OperationOutcome | API, FHIR | P1 | ✅ Automated |
| TC-007 | Update patient birthDate, verify persisted | API | P1 | ✅ Automated |
| TC-008 | Delete patient returns 204, then 404 on GET | API | P1 | ✅ Automated |
| TC-009 | Invalid JSON body returns 400/422 | Negative | P1 | ✅ Automated |
| TC-010 | Wrong resourceType returns 422 | Negative | P1 | ✅ Automated |
| TC-011 | Invalid gender returns 422 | Negative | P1 | ✅ Automated |
| TC-012 | Invalid birthDate returns 422 | Negative | P1 | ✅ Automated |
| TC-013 | List patients returns FHIR Bundle | API (Smoke) | P0 | ✅ Automated |
| TC-014 | Search by name returns matching patient | API | P1 | ✅ Automated |
| TC-015 | Search by gender filters correctly | API | P1 | ✅ Automated |
| TC-016 | _count=1 returns max 1 entry | API | P2 | ✅ Automated |
| TC-017 | Non-existent name search returns total=0 | API | P2 | ✅ Automated |
| TC-018 | Response Content-Type includes json | API | P2 | ✅ Automated |
| TC-019 | PATCH on collection returns 405 | Negative | P2 | ✅ Automated |
| TC-020 | Data round-trip integrity verified | API (Regression) | P1 | ✅ Automated |
