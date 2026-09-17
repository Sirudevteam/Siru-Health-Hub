from datetime import datetime, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.database.models import (
    Patient as PatientModel,
    Practitioner as PractitionerModel,
    Organization as OrganizationModel,
    Encounter as EncounterModel,
    Observation as ObservationModel,
    Condition as ConditionModel,
    MedicationRequest as MedicationRequestModel,
    Appointment as AppointmentModel,
    User as UserModel,
    Coverage as CoverageModel,
    Claim as ClaimModel,
    ClaimResponse as ClaimResponseModel
)
from app.auth.security import get_password_hash


async def seed_database():
    """Seed initial hospital and clinical demo records if not present."""
    async with AsyncSessionLocal() as session:
        # 0. Core Patients (P1001 & P1002)
        existing_p1001 = (await session.execute(select(PatientModel).where(PatientModel.id == "P1001"))).scalars().first()
        if not existing_p1001:
            p1 = PatientModel(
                id="P1001",
                family_name="Kumar",
                given_name="Arun",
                gender="male",
                birth_date=date(1995, 5, 10),
                active=True,
                fhir_json={
                    "resourceType": "Patient",
                    "id": "P1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "active": True,
                    "name": [{"family": "Kumar", "given": ["Arun"]}],
                    "gender": "male",
                    "birthDate": "1995-05-10"
                }
            )
            session.add(p1)

        existing_p1002 = (await session.execute(select(PatientModel).where(PatientModel.id == "P1002"))).scalars().first()
        if not existing_p1002:
            p2 = PatientModel(
                id="P1002",
                family_name="Devi",
                given_name="Priya",
                gender="female",
                birth_date=date(1988, 11, 22),
                active=True,
                fhir_json={
                    "resourceType": "Patient",
                    "id": "P1002",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "active": True,
                    "name": [{"family": "Devi", "given": ["Priya"]}],
                    "gender": "female",
                    "birthDate": "1988-11-22"
                }
            )
            session.add(p2)

        # 1. Organization
        existing_org = (await session.execute(select(OrganizationModel).where(OrganizationModel.id == "ORG101"))).scalars().first()
        if not existing_org:
            org = OrganizationModel(
                id="ORG101",
                name="Siru Central Hospital",
                active=True,
                fhir_json={
                    "resourceType": "Organization",
                    "id": "ORG101",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "name": "Siru Central Hospital",
                    "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov", "display": "Healthcare Provider"}]}],
                    "telecom": [{"system": "phone", "value": "+91-44-24567890", "use": "work"}],
                    "address": [{"line": ["100 Healthcare Boulevard"], "city": "Chennai", "state": "Tamil Nadu", "postalCode": "600001", "country": "India"}]
                }
            )
            session.add(org)

        # 2. Practitioners
        practitioners_data = [
            {
                "id": "PR101",
                "family_name": "Sharma",
                "given_name": "Rajesh",
                "gender": "male",
                "qualification": "Cardiologist",
                "fhir_json": {
                    "resourceType": "Practitioner",
                    "id": "PR101",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "active": True,
                    "name": [{"use": "official", "family": "Sharma", "given": ["Rajesh"], "prefix": ["Dr."]}],
                    "gender": "male",
                    "qualification": [{"code": {"text": "Cardiologist - MD, DM"}}]
                }
            },
            {
                "id": "PR102",
                "family_name": "Nair",
                "given_name": "Lakshmi",
                "gender": "female",
                "qualification": "Registered Staff Nurse",
                "fhir_json": {
                    "resourceType": "Practitioner",
                    "id": "PR102",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "active": True,
                    "name": [{"use": "official", "family": "Nair", "given": ["Lakshmi"]}],
                    "gender": "female",
                    "qualification": [{"code": {"text": "Staff Nurse - B.Sc Nursing"}}]
                }
            },
            {
                "id": "PR103",
                "family_name": "Sundaram",
                "given_name": "Kavitha",
                "gender": "female",
                "qualification": "Receptionist / Coordinator",
                "fhir_json": {
                    "resourceType": "Practitioner",
                    "id": "PR103",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "active": True,
                    "name": [{"use": "official", "family": "Sundaram", "given": ["Kavitha"]}],
                    "gender": "female",
                    "qualification": [{"code": {"text": "Patient Coordinator"}}]
                }
            }
        ]

        for p in practitioners_data:
            exists = (await session.execute(select(PractitionerModel).where(PractitionerModel.id == p["id"]))).scalars().first()
            if not exists:
                session.add(PractitionerModel(
                    id=p["id"],
                    family_name=p["family_name"],
                    given_name=p["given_name"],
                    gender=p["gender"],
                    active=True,
                    fhir_json=p["fhir_json"]
                ))

        # 3. Encounter
        existing_enc = (await session.execute(select(EncounterModel).where(EncounterModel.id == "ENC1001"))).scalars().first()
        if not existing_enc:
            enc = EncounterModel(
                id="ENC1001",
                patient_id="P1001",
                practitioner_id="PR101",
                status="finished",
                encounter_class="AMB",
                fhir_json={
                    "resourceType": "Encounter",
                    "id": "ENC1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "finished",
                    "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
                    "subject": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "participant": [{"individual": {"reference": "Practitioner/PR101", "display": "Dr. Rajesh Sharma"}}],
                    "period": {"start": "2026-09-16T10:00:00Z", "end": "2026-09-16T10:45:00Z"},
                    "reasonCode": [{"text": "Routine Cardiac Consultation & BP Check"}],
                    "serviceProvider": {"reference": "Organization/ORG101", "display": "Siru Central Hospital"}
                }
            )
            session.add(enc)

        # 4. Observations (Vitals)
        obs_data = [
            {
                "id": "OBS1001",
                "patient_id": "P1001",
                "encounter_id": "ENC1001",
                "category": "vital-signs",
                "code": "85354-9",
                "value_string": "120/80 mmHg",
                "fhir_json": {
                    "resourceType": "Observation",
                    "id": "OBS1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure systolic & diastolic"}], "text": "Blood Pressure"},
                    "subject": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "encounter": {"reference": "Encounter/ENC1001"},
                    "effectiveDateTime": "2026-09-16T10:15:00Z",
                    "valueString": "120/80 mmHg",
                    "component": [
                        {"code": {"coding": [{"code": "8480-6", "display": "Systolic"}], "text": "Systolic"}, "valueQuantity": {"value": 120, "unit": "mmHg"}},
                        {"code": {"coding": [{"code": "8462-4", "display": "Diastolic"}], "text": "Diastolic"}, "valueQuantity": {"value": 80, "unit": "mmHg"}}
                    ]
                }
            },
            {
                "id": "OBS1002",
                "patient_id": "P1001",
                "encounter_id": "ENC1001",
                "category": "vital-signs",
                "code": "8867-4",
                "value_numeric": 72.0,
                "fhir_json": {
                    "resourceType": "Observation",
                    "id": "OBS1002",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}], "text": "Heart Rate"},
                    "subject": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "encounter": {"reference": "Encounter/ENC1001"},
                    "effectiveDateTime": "2026-09-16T10:15:00Z",
                    "valueQuantity": {"value": 72.0, "unit": "beats/min", "system": "http://unitsofmeasure.org", "code": "/min"}
                }
            },
            {
                "id": "OBS1003",
                "patient_id": "P1001",
                "encounter_id": "ENC1001",
                "category": "vital-signs",
                "code": "8310-5",
                "value_numeric": 98.6,
                "fhir_json": {
                    "resourceType": "Observation",
                    "id": "OBS1003",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}], "text": "Body Temperature"},
                    "subject": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "encounter": {"reference": "Encounter/ENC1001"},
                    "effectiveDateTime": "2026-09-16T10:15:00Z",
                    "valueQuantity": {"value": 98.6, "unit": "degF", "system": "http://unitsofmeasure.org", "code": "[degF]"}
                }
            }
        ]

        for o in obs_data:
            exists = (await session.execute(select(ObservationModel).where(ObservationModel.id == o["id"]))).scalars().first()
            if not exists:
                session.add(ObservationModel(
                    id=o["id"],
                    patient_id=o["patient_id"],
                    encounter_id=o["encounter_id"],
                    category=o["category"],
                    code=o["code"],
                    value_string=o.get("value_string"),
                    value_numeric=o.get("value_numeric"),
                    fhir_json=o["fhir_json"]
                ))

        # 5. Condition (Diagnosis)
        existing_cond = (await session.execute(select(ConditionModel).where(ConditionModel.id == "CON1001"))).scalars().first()
        if not existing_cond:
            cond = ConditionModel(
                id="CON1001",
                patient_id="P1001",
                encounter_id="ENC1001",
                clinical_status="active",
                code="I10",
                fhir_json={
                    "resourceType": "Condition",
                    "id": "CON1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active", "display": "Active"}]},
                    "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed", "display": "Confirmed"}]},
                    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10", "display": "Essential (primary) hypertension"}], "text": "Essential Hypertension"},
                    "subject": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "encounter": {"reference": "Encounter/ENC1001"},
                    "onsetDateTime": "2025-05-10"
                }
            )
            session.add(cond)

        # 6. MedicationRequest (Prescription)
        existing_med = (await session.execute(select(MedicationRequestModel).where(MedicationRequestModel.id == "MED1001"))).scalars().first()
        if not existing_med:
            med = MedicationRequestModel(
                id="MED1001",
                patient_id="P1001",
                encounter_id="ENC1001",
                status="active",
                intent="order",
                medication_code="308136",
                fhir_json={
                    "resourceType": "MedicationRequest",
                    "id": "MED1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "308136", "display": "Amlodipine 5 MG Oral Tablet"}],
                        "text": "Amlodipine 5mg oral daily"
                    },
                    "subject": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "encounter": {"reference": "Encounter/ENC1001"},
                    "authoredOn": "2026-09-16",
                    "requester": {"reference": "Practitioner/PR101", "display": "Dr. Rajesh Sharma"},
                    "dosageInstruction": [{"text": "Take 1 tablet by mouth daily in the morning with water."}]
                }
            )
            session.add(med)

        # 7. Appointment
        existing_apt = (await session.execute(select(AppointmentModel).where(AppointmentModel.id == "APT1001"))).scalars().first()
        if not existing_apt:
            apt = AppointmentModel(
                id="APT1001",
                patient_id="P1001",
                practitioner_id="PR101",
                status="booked",
                start_time=datetime(2026, 9, 24, 10, 30),
                end_time=datetime(2026, 9, 24, 11, 0),
                fhir_json={
                    "resourceType": "Appointment",
                    "id": "APT1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "booked",
                    "description": "Cardiology Follow-up & Medication Review",
                    "start": "2026-09-24T10:30:00Z",
                    "end": "2026-09-24T11:00:00Z",
                    "participant": [
                        {"actor": {"reference": "Patient/P1001", "display": "Arun Kumar"}, "status": "accepted"},
                        {"actor": {"reference": "Practitioner/PR101", "display": "Dr. Rajesh Sharma"}, "status": "accepted"}
                    ]
                }
            )
            session.add(apt)

        # 8. Seed Role Users
        users_seed = [
            {
                "id": "USR_ADMIN",
                "username": "admin",
                "password": "admin123",
                "role": "ADMIN",
                "patient_id": None,
                "practitioner_id": None
            },
            {
                "id": "USR_DOCTOR",
                "username": "doctor.sharma",
                "password": "doctor123",
                "role": "DOCTOR",
                "patient_id": None,
                "practitioner_id": "PR101"
            },
            {
                "id": "USR_NURSE",
                "username": "nurse.lakshmi",
                "password": "nurse123",
                "role": "NURSE",
                "patient_id": None,
                "practitioner_id": "PR102"
            },
            {
                "id": "USR_PATIENT",
                "username": "patient.arun",
                "password": "patient123",
                "role": "PATIENT",
                "patient_id": "P1001",
                "practitioner_id": None
            }
        ]

        for u in users_seed:
            existing_user = (await session.execute(select(UserModel).where(UserModel.username == u["username"]))).scalars().first()
            if not existing_user:
                session.add(UserModel(
                    id=u["id"],
                    username=u["username"],
                    hashed_password=get_password_hash(u["password"]),
                    role=u["role"],
                    patient_id=u["patient_id"],
                    practitioner_id=u["practitioner_id"],
                    active=True
                ))

        # 9. Seed Payer Organizations
        existing_payer = (await session.execute(select(OrganizationModel).where(OrganizationModel.id == "ORG_PAYER_1"))).scalars().first()
        if not existing_payer:
            session.add(OrganizationModel(
                id="ORG_PAYER_1",
                name="Star Health & Allied Insurance",
                active=True,
                fhir_json={
                    "resourceType": "Organization",
                    "id": "ORG_PAYER_1",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "name": "Star Health & Allied Insurance",
                    "type": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "ins", "display": "Insurance Company"}]}],
                    "telecom": [{"system": "phone", "value": "+91-44-28288888", "use": "work"}],
                    "address": [{"line": ["1 New Tank Street, Valluvar Kottam High Rd"], "city": "Chennai", "state": "Tamil Nadu", "postalCode": "600034", "country": "India"}]
                }
            ))

        # 10. Seed Coverages
        coverages_seed = [
            {
                "id": "COV1001",
                "patient_id": "P1001",
                "payor_id": "ORG_PAYER_1",
                "subscriber_id": "SH-99281-01",
                "status": "active",
                "plan_name": "Star Comprehensive Health Plan",
                "fhir_json": {
                    "resourceType": "Coverage",
                    "id": "COV1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "active",
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "HIP", "display": "Health Insurance Policy"}], "text": "Comprehensive Health Plan"},
                    "subscriberId": "SH-99281-01",
                    "beneficiary": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "period": {"start": "2026-01-01", "end": "2026-12-31"},
                    "payor": [{"reference": "Organization/ORG_PAYER_1", "display": "Star Health & Allied Insurance"}],
                    "class": [{"type": {"coding": [{"code": "plan"}]}, "value": "GOLD-COMP-01", "name": "Star Comprehensive Gold"}],
                    "costToBeneficiary": [{"type": {"coding": [{"code": "copay"}]}, "valueMoney": {"value": 500.0, "currency": "USD"}}]
                }
            },
            {
                "id": "COV1002",
                "patient_id": "P1002",
                "payor_id": "ORG_PAYER_1",
                "subscriber_id": "SH-88123-02",
                "status": "active",
                "plan_name": "Star Family Health Optima",
                "fhir_json": {
                    "resourceType": "Coverage",
                    "id": "COV1002",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "active",
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "HIP", "display": "Health Insurance Policy"}], "text": "Family Health Optima"},
                    "subscriberId": "SH-88123-02",
                    "beneficiary": {"reference": "Patient/P1002", "display": "Priya Devi"},
                    "period": {"start": "2026-01-01", "end": "2026-12-31"},
                    "payor": [{"reference": "Organization/ORG_PAYER_1", "display": "Star Health & Allied Insurance"}]
                }
            },
            {
                "id": "COV_EXPIRED",
                "patient_id": "P1001",
                "payor_id": "ORG_PAYER_1",
                "subscriber_id": "SH-OLD-999",
                "status": "cancelled",
                "plan_name": "Legacy Basic Policy (Expired)",
                "fhir_json": {
                    "resourceType": "Coverage",
                    "id": "COV_EXPIRED",
                    "meta": {"versionId": "1", "lastUpdated": "2024-01-01T00:00:00Z"},
                    "status": "cancelled",
                    "type": {"coding": [{"code": "HIP"}], "text": "Legacy Basic Policy (Expired)"},
                    "subscriberId": "SH-OLD-999",
                    "beneficiary": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "period": {"start": "2023-01-01", "end": "2024-01-01"},
                    "payor": [{"reference": "Organization/ORG_PAYER_1", "display": "Star Health & Allied Insurance"}]
                }
            }
        ]

        for cov in coverages_seed:
            existing_cov = (await session.execute(select(CoverageModel).where(CoverageModel.id == cov["id"]))).scalars().first()
            if not existing_cov:
                session.add(CoverageModel(
                    id=cov["id"],
                    patient_id=cov["patient_id"],
                    payor_id=cov["payor_id"],
                    subscriber_id=cov["subscriber_id"],
                    status=cov["status"],
                    plan_name=cov["plan_name"],
                    fhir_json=cov["fhir_json"]
                ))

        # 11. Seed Claim & ClaimResponse
        existing_claim = (await session.execute(select(ClaimModel).where(ClaimModel.id == "CLM1001"))).scalars().first()
        if not existing_claim:
            session.add(ClaimModel(
                id="CLM1001",
                patient_id="P1001",
                provider_id="PR101",
                coverage_id="COV1001",
                status="active",
                use="claim",
                total_amount=3700.0,
                fhir_json={
                    "resourceType": "Claim",
                    "id": "CLM1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "active",
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "professional"}]},
                    "use": "claim",
                    "patient": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "created": "2026-09-17T09:00:00Z",
                    "provider": {"reference": "Practitioner/PR101", "display": "Dr. Rajesh Sharma"},
                    "facility": {"reference": "Organization/ORG101", "display": "Siru Central Hospital"},
                    "insurance": [{"sequence": 1, "focal": True, "coverage": {"reference": "Coverage/COV1001"}}],
                    "diagnosis": [{"sequence": 1, "diagnosisReference": {"reference": "Condition/COND101"}}],
                    "item": [
                        {
                            "sequence": 1,
                            "productOrService": {"coding": [{"system": "http://www.ama-assn.org/go/cpt", "code": "99214", "display": "Office Visit - Level 4"}]},
                            "unitPrice": {"value": 2500.0, "currency": "USD"},
                            "net": {"value": 2500.0, "currency": "USD"}
                        },
                        {
                            "sequence": 2,
                            "productOrService": {"coding": [{"system": "http://www.ama-assn.org/go/cpt", "code": "93000", "display": "Electrocardiogram, Routine ECG"}]},
                            "unitPrice": {"value": 1200.0, "currency": "USD"},
                            "net": {"value": 1200.0, "currency": "USD"}
                        }
                    ],
                    "total": {"value": 3700.0, "currency": "USD"}
                }
            ))

        existing_cr = (await session.execute(select(ClaimResponseModel).where(ClaimResponseModel.id == "CR1001"))).scalars().first()
        if not existing_cr:
            session.add(ClaimResponseModel(
                id="CR1001",
                claim_id="CLM1001",
                patient_id="P1001",
                insurer_id="ORG_PAYER_1",
                status="active",
                outcome="complete",
                disposition="Claim fully adjudicated and approved. Insurer paid 90% benefit.",
                total_submitted=3700.0,
                total_benefit=3330.0,
                total_patient_paid=370.0,
                fhir_json={
                    "resourceType": "ClaimResponse",
                    "id": "CR1001",
                    "meta": {"versionId": "1", "lastUpdated": "2026-09-17T00:00:00Z"},
                    "status": "active",
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "professional"}]},
                    "use": "claim",
                    "patient": {"reference": "Patient/P1001", "display": "Arun Kumar"},
                    "created": "2026-09-17T09:00:00Z",
                    "insurer": {"reference": "Organization/ORG_PAYER_1", "display": "Star Health & Allied Insurance"},
                    "request": {"reference": "Claim/CLM1001"},
                    "outcome": "complete",
                    "disposition": "Claim fully adjudicated and approved. Insurer paid 90% benefit.",
                    "total": [
                        {"category": {"coding": [{"code": "submitted"}]}, "amount": {"value": 3700.0, "currency": "USD"}},
                        {"category": {"coding": [{"code": "benefit"}]}, "amount": {"value": 3330.0, "currency": "USD"}},
                        {"category": {"coding": [{"code": "copay"}]}, "amount": {"value": 370.0, "currency": "USD"}}
                    ]
                }
            ))

        await session.commit()


