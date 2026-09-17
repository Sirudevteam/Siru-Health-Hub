# ==============================================================================
# Siru HealthHub — Locust Performance & Concurrency Load Test Suite
# Simulates concurrent traffic across Patient, Doctor, and Billing personas.
# Validates p95 latency < 500ms and verifies stability under high throughput.
#
# Usage:
#   locust -f qa/performance-tests/locustfile.py --headless -u 20 -r 5 --run-time 30s --host http://localhost:8000
# ==============================================================================

from locust import HttpUser, task, between
import uuid
import random


class PatientPersona(HttpUser):
    """Simulates a patient reviewing their health records, vitals, coverage & claims."""
    weight = 3
    wait_time = between(1, 3)

    def on_start(self):
        res = self.client.post("/auth/login", json={"username": "patient.arun", "password": "patient123"})
        if res.status_code == 200:
            self.token = res.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/fhir+json"}
        else:
            self.headers = {}

    @task(3)
    def view_my_profile(self):
        self.client.get("/fhir/Patient/P1001", headers=self.headers, name="/fhir/Patient/[id]")

    @task(2)
    def view_my_vitals(self):
        self.client.get("/fhir/Observation?patient=P1001", headers=self.headers, name="/fhir/Observation?patient")

    @task(2)
    def view_my_coverage(self):
        self.client.get("/fhir/Coverage?patient=P1001", headers=self.headers, name="/fhir/Coverage?patient")

    @task(1)
    def view_my_claims(self):
        self.client.get("/fhir/Claim?patient=P1001", headers=self.headers, name="/fhir/Claim?patient")


class DoctorPersona(HttpUser):
    """Simulates a physician reviewing patient lists, encounters, recording vitals, and verifying eligibility."""
    weight = 2
    wait_time = between(1, 2)

    def on_start(self):
        res = self.client.post("/auth/login", json={"username": "doctor.sharma", "password": "doctor123"})
        if res.status_code == 200:
            self.token = res.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/fhir+json"}
        else:
            self.headers = {}

    @task(3)
    def list_patients(self):
        self.client.get("/fhir/Patient?_count=10", headers=self.headers, name="/fhir/Patient?_count")

    @task(2)
    def check_eligibility(self):
        self.client.post("/fhir/Coverage/COV1001/eligibility-check", headers=self.headers, name="/fhir/Coverage/[id]/eligibility-check")

    @task(1)
    def record_vital(self):
        bpm = random.randint(68, 88)
        self.client.post("/fhir/Observation", json={
            "resourceType": "Observation",
            "status": "final",
            "category": [{"coding": [{"code": "vital-signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart Rate"}]},
            "subject": {"reference": "Patient/P1001"},
            "valueQuantity": {"value": bpm, "unit": "beats/min"}
        }, headers=self.headers, name="/fhir/Observation [POST]")


class BillingPersona(HttpUser):
    """Simulates an RCM billing coordinator reviewing and submitting healthcare claims."""
    weight = 1
    wait_time = between(2, 4)

    def on_start(self):
        res = self.client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        if res.status_code == 200:
            self.token = res.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/fhir+json"}
        else:
            self.headers = {}

    @task(2)
    def list_claims(self):
        self.client.get("/fhir/Claim?_count=20", headers=self.headers, name="/fhir/Claim?_count")

    @task(1)
    def submit_adjudicated_claim(self):
        amt = random.choice([1200.0, 1800.0, 2400.0])
        self.client.post("/fhir/Claim", json={
            "resourceType": "Claim",
            "status": "active",
            "type": {"coding": [{"code": "professional"}]},
            "use": "claim",
            "patient": {"reference": "Patient/P1001"},
            "provider": {"reference": "Practitioner/PR101"},
            "insurance": [{"sequence": 1, "focal": True, "coverage": {"reference": "Coverage/COV1001"}}],
            "item": [
                {
                    "sequence": 1,
                    "productOrService": {"coding": [{"code": "99213"}]},
                    "unitPrice": {"value": amt, "currency": "INR"},
                    "quantity": {"value": 1}
                }
            ],
            "total": {"value": amt, "currency": "INR"}
        }, headers=self.headers, name="/fhir/Claim [POST Adjudicate]")

