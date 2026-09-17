from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any, Dict, Literal
from datetime import datetime
import uuid
from app.fhir.schemas import HumanName, ContactPoint, Address, CodeableConcept


class Reference(BaseModel):
    reference: Optional[str] = None  # e.g., "Patient/P1001"
    type: Optional[str] = None
    display: Optional[str] = None


class Coding(BaseModel):
    system: Optional[str] = None
    version: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class Period(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class Quantity(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class ResourceBundle(BaseModel):
    resourceType: Literal["Bundle"] = "Bundle"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "searchset"
    total: int
    link: Optional[List[dict]] = None
    entry: Optional[List[dict]] = None


# ─── Practitioner ────────────────────────────────────────────────────────────

class PractitionerCreate(BaseModel):
    resourceType: Literal["Practitioner"] = "Practitioner"
    id: Optional[str] = None
    active: Optional[bool] = True
    name: Optional[List[HumanName]] = None
    telecom: Optional[List[ContactPoint]] = None
    gender: Optional[str] = None
    qualification: Optional[List[dict]] = None

    @model_validator(mode="after")
    def validate_gender(self):
        if self.gender and self.gender not in ["male", "female", "other", "unknown"]:
            raise ValueError(f"Invalid gender: {self.gender}. Must be male|female|other|unknown")
        return self


class PractitionerResponse(PractitionerCreate):
    id: str
    meta: Optional[dict] = None


# ─── Organization ────────────────────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    resourceType: Literal["Organization"] = "Organization"
    id: Optional[str] = None
    active: Optional[bool] = True
    name: Optional[str] = None
    type: Optional[List[CodeableConcept]] = None
    telecom: Optional[List[ContactPoint]] = None
    address: Optional[List[Address]] = None


class OrganizationResponse(OrganizationCreate):
    id: str
    meta: Optional[dict] = None


# ─── Encounter ───────────────────────────────────────────────────────────────

class EncounterParticipant(BaseModel):
    individual: Optional[Reference] = None
    type: Optional[List[CodeableConcept]] = None


class EncounterClass(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class EncounterCreate(BaseModel):
    resourceType: Literal["Encounter"] = "Encounter"
    id: Optional[str] = None
    status: str = "finished"  # planned | arrived | triaged | in-progress | onleave | finished | cancelled
    class_: Optional[EncounterClass] = Field(default=None, alias="class")
    subject: Reference  # e.g. {"reference": "Patient/P1001"}
    participant: Optional[List[EncounterParticipant]] = None
    period: Optional[Period] = None
    reasonCode: Optional[List[CodeableConcept]] = None
    serviceProvider: Optional[Reference] = None

    model_config = {"populate_by_name": True}


class EncounterResponse(EncounterCreate):
    id: str
    meta: Optional[dict] = None


# ─── Observation ─────────────────────────────────────────────────────────────

class ObservationComponent(BaseModel):
    code: CodeableConcept
    valueQuantity: Optional[Quantity] = None
    valueString: Optional[str] = None


class ObservationCreate(BaseModel):
    resourceType: Literal["Observation"] = "Observation"
    id: Optional[str] = None
    status: str = "final"  # registered | preliminary | final | amended
    category: Optional[List[CodeableConcept]] = None  # vital-signs, laboratory, etc.
    code: CodeableConcept
    subject: Reference  # e.g. {"reference": "Patient/P1001"}
    encounter: Optional[Reference] = None
    effectiveDateTime: Optional[str] = None
    valueQuantity: Optional[Quantity] = None
    valueString: Optional[str] = None
    component: Optional[List[ObservationComponent]] = None


class ObservationResponse(ObservationCreate):
    id: str
    meta: Optional[dict] = None


# ─── Condition ───────────────────────────────────────────────────────────────

class ConditionCreate(BaseModel):
    resourceType: Literal["Condition"] = "Condition"
    id: Optional[str] = None
    clinicalStatus: Optional[CodeableConcept] = None  # active | recurrence | relapse | inactive | remission | resolved
    verificationStatus: Optional[CodeableConcept] = None  # unconfirmed | provisional | differential | confirmed | refuted | entered-in-error
    category: Optional[List[CodeableConcept]] = None
    code: CodeableConcept  # ICD-10 or SNOMED
    subject: Reference
    encounter: Optional[Reference] = None
    onsetDateTime: Optional[str] = None
    recordedDate: Optional[str] = None


class ConditionResponse(ConditionCreate):
    id: str
    meta: Optional[dict] = None


# ─── MedicationRequest ───────────────────────────────────────────────────────

class MedicationRequestCreate(BaseModel):
    resourceType: Literal["MedicationRequest"] = "MedicationRequest"
    id: Optional[str] = None
    status: str = "active"  # active | on-hold | cancelled | completed | stopped | draft
    intent: str = "order"   # proposal | plan | order | original-order | reflex-order
    medicationCodeableConcept: CodeableConcept
    subject: Reference
    encounter: Optional[Reference] = None
    authoredOn: Optional[str] = None
    requester: Optional[Reference] = None
    dosageInstruction: Optional[List[dict]] = None


class MedicationRequestResponse(MedicationRequestCreate):
    id: str
    meta: Optional[dict] = None


# ─── Appointment ─────────────────────────────────────────────────────────────

class AppointmentParticipant(BaseModel):
    actor: Reference
    required: Optional[str] = "required"
    status: Optional[str] = "accepted"  # accepted | declined | tentative | needs-action


class AppointmentCreate(BaseModel):
    resourceType: Literal["Appointment"] = "Appointment"
    id: Optional[str] = None
    status: str = "booked"  # proposed | pending | booked | arrived | fulfilled | cancelled | noshow
    serviceType: Optional[List[CodeableConcept]] = None
    description: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    participant: List[AppointmentParticipant]


class AppointmentResponse(AppointmentCreate):
    id: str
    meta: Optional[dict] = None

