-- =============================================================
-- Siru HealthHub Database Initialization
-- Runs automatically when the PostgreSQL container starts
-- for the first time (via docker-entrypoint-initdb.d)
-- =============================================================

-- ── Extensions ────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- for LIKE / ILIKE query optimization

-- ── Patients Table ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    id              VARCHAR(64)  PRIMARY KEY,
    family_name     VARCHAR(255),
    given_name      VARCHAR(255),
    gender          VARCHAR(32),
    birth_date      DATE,
    active          BOOLEAN      NOT NULL DEFAULT TRUE,
    fhir_json       JSONB        NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Indexes for FHIR search parameters
CREATE INDEX IF NOT EXISTS idx_patients_family_name ON patients USING gin (family_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_patients_given_name  ON patients USING gin (given_name  gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_patients_birth_date  ON patients (birth_date);
CREATE INDEX IF NOT EXISTS idx_patients_gender      ON patients (gender);
CREATE INDEX IF NOT EXISTS idx_patients_active      ON patients (active);
CREATE INDEX IF NOT EXISTS idx_patients_fhir_json   ON patients USING gin (fhir_json);

-- ── Audit Logs Table ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGSERIAL    PRIMARY KEY,
    user_id         VARCHAR(64),
    action          VARCHAR(32)  NOT NULL,
    resource_type   VARCHAR(64),
    resource_id     VARCHAR(64),
    timestamp       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    result          VARCHAR(16)  NOT NULL DEFAULT 'SUCCESS',
    ip_address      VARCHAR(64),
    http_method     VARCHAR(16),
    path            VARCHAR(512),
    status_code     INTEGER,
    details         JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource  ON audit_logs (resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user      ON audit_logs (user_id);

-- ── Auto-update updated_at Trigger ────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ── Seed Data: Sample Patients ────────────────────────────────
INSERT INTO patients (id, family_name, given_name, gender, birth_date, active, fhir_json)
VALUES (
    'P1001',
    'Kumar',
    'Arun',
    'male',
    '1995-05-10',
    TRUE,
    '{
        "resourceType": "Patient",
        "id": "P1001",
        "meta": {
            "versionId": "1",
            "lastUpdated": "2026-09-16T00:00:00Z"
        },
        "active": true,
        "name": [{"family": "Kumar", "given": ["Arun"]}],
        "gender": "male",
        "birthDate": "1995-05-10"
    }'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO patients (id, family_name, given_name, gender, birth_date, active, fhir_json)
VALUES (
    'P1002',
    'Devi',
    'Priya',
    'female',
    '1988-11-22',
    TRUE,
    '{
        "resourceType": "Patient",
        "id": "P1002",
        "meta": {
            "versionId": "1",
            "lastUpdated": "2026-09-16T00:00:00Z"
        },
        "active": true,
        "name": [{"family": "Devi", "given": ["Priya"]}],
        "gender": "female",
        "birthDate": "1988-11-22"
    }'
) ON CONFLICT (id) DO NOTHING;
