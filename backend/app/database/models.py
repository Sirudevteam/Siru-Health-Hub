from __future__ import annotations

from sqlalchemy import String, Boolean, Date, BigInteger, Integer, Float, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP
from datetime import datetime, date
from typing import Optional
from app.database.session import Base


class Patient(Base):
    __tablename__ = "patients"

    id:          Mapped[str]            = mapped_column(String(64), primary_key=True)
    family_name: Mapped[Optional[str]]  = mapped_column(String(255), index=True, nullable=True)
    given_name:  Mapped[Optional[str]]  = mapped_column(String(255), index=True, nullable=True)
    gender:      Mapped[Optional[str]]  = mapped_column(String(32), nullable=True)
    birth_date:  Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active:      Mapped[bool]           = mapped_column(Boolean, default=True)
    fhir_json:   Mapped[dict]           = mapped_column(JSONB, nullable=False)
    created_at:  Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:  Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Practitioner(Base):
    __tablename__ = "practitioners"

    id:          Mapped[str]            = mapped_column(String(64), primary_key=True)
    family_name: Mapped[Optional[str]]  = mapped_column(String(255), index=True, nullable=True)
    given_name:  Mapped[Optional[str]]  = mapped_column(String(255), index=True, nullable=True)
    gender:      Mapped[Optional[str]]  = mapped_column(String(32), nullable=True)
    active:      Mapped[bool]           = mapped_column(Boolean, default=True)
    fhir_json:   Mapped[dict]           = mapped_column(JSONB, nullable=False)
    created_at:  Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:  Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Organization(Base):
    __tablename__ = "organizations"

    id:         Mapped[str]            = mapped_column(String(64), primary_key=True)
    name:       Mapped[Optional[str]]  = mapped_column(String(255), index=True, nullable=True)
    active:     Mapped[bool]           = mapped_column(Boolean, default=True)
    fhir_json:  Mapped[dict]           = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Encounter(Base):
    __tablename__ = "encounters"

    id:              Mapped[str]            = mapped_column(String(64), primary_key=True)
    patient_id:      Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    practitioner_id: Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    status:          Mapped[Optional[str]]  = mapped_column(String(32), index=True, nullable=True)
    encounter_class: Mapped[Optional[str]]  = mapped_column(String(32), nullable=True)
    fhir_json:       Mapped[dict]           = mapped_column(JSONB, nullable=False)
    created_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Observation(Base):
    __tablename__ = "observations"

    id:                 Mapped[str]            = mapped_column(String(64), primary_key=True)
    patient_id:         Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    encounter_id:       Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    category:           Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    code:               Mapped[Optional[str]]  = mapped_column(String(128), index=True, nullable=True)
    value_string:       Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)
    value_numeric:      Mapped[Optional[float]]= mapped_column(Float, nullable=True)
    effective_datetime: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    fhir_json:          Mapped[dict]           = mapped_column(JSONB, nullable=False)
    created_at:         Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:         Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Condition(Base):
    __tablename__ = "conditions"

    id:              Mapped[str]            = mapped_column(String(64), primary_key=True)
    patient_id:      Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    encounter_id:    Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    clinical_status: Mapped[Optional[str]]  = mapped_column(String(32), index=True, nullable=True)
    code:            Mapped[Optional[str]]  = mapped_column(String(128), index=True, nullable=True)
    fhir_json:       Mapped[dict]           = mapped_column(JSONB, nullable=False)
    created_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class MedicationRequest(Base):
    __tablename__ = "medication_requests"

    id:              Mapped[str]            = mapped_column(String(64), primary_key=True)
    patient_id:      Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    encounter_id:    Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    status:          Mapped[Optional[str]]  = mapped_column(String(32), index=True, nullable=True)
    intent:          Mapped[Optional[str]]  = mapped_column(String(32), nullable=True)
    medication_code: Mapped[Optional[str]]  = mapped_column(String(128), nullable=True)
    fhir_json:       Mapped[dict]           = mapped_column(JSONB, nullable=False)
    created_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Appointment(Base):
    __tablename__ = "appointments"

    id:              Mapped[str]            = mapped_column(String(64), primary_key=True)
    patient_id:      Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    practitioner_id: Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    status:          Mapped[Optional[str]]  = mapped_column(String(32), index=True, nullable=True)
    start_time:      Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    end_time:        Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    fhir_json:       Mapped[dict]           = mapped_column(JSONB, nullable=False)
    created_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id:            Mapped[int]           = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id:       Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action:        Mapped[str]           = mapped_column(String(32))
    resource_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resource_id:   Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    timestamp:     Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    result:        Mapped[str]           = mapped_column(String(16), default="SUCCESS")
    ip_address:    Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    http_method:   Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    path:          Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status_code:   Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details:       Mapped[Optional[dict]]= mapped_column(JSONB, nullable=True)


class User(Base):
    __tablename__ = "users"

    id:              Mapped[str]            = mapped_column(String(64), primary_key=True)
    username:        Mapped[str]            = mapped_column(String(64), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str]            = mapped_column(String(255), nullable=False)
    role:            Mapped[str]            = mapped_column(String(32), index=True, nullable=False)  # ADMIN | DOCTOR | NURSE | PATIENT
    patient_id:      Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    practitioner_id: Mapped[Optional[str]]  = mapped_column(String(64), index=True, nullable=True)
    active:          Mapped[bool]           = mapped_column(Boolean, default=True)
    created_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime]       = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Coverage(Base):
    __tablename__ = "coverages"

    id:            Mapped[str]           = mapped_column(String(64), primary_key=True)
    patient_id:    Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    payor_id:      Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    subscriber_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    status:        Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    plan_name:     Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fhir_json:     Mapped[dict]          = mapped_column(JSONB, nullable=False)
    created_at:    Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class Claim(Base):
    __tablename__ = "claims"

    id:           Mapped[str]           = mapped_column(String(64), primary_key=True)
    patient_id:   Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    provider_id:  Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    coverage_id:  Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    status:       Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    use:          Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    total_amount: Mapped[Optional[float]]= mapped_column(Float, nullable=True)
    fhir_json:    Mapped[dict]          = mapped_column(JSONB, nullable=False)
    created_at:   Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:   Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class ClaimResponse(Base):
    __tablename__ = "claim_responses"

    id:                 Mapped[str]           = mapped_column(String(64), primary_key=True)
    claim_id:           Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    patient_id:         Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    insurer_id:         Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    status:             Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    outcome:            Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    disposition:        Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_submitted:    Mapped[Optional[float]]= mapped_column(Float, nullable=True)
    total_benefit:      Mapped[Optional[float]]= mapped_column(Float, nullable=True)
    total_patient_paid: Mapped[Optional[float]]= mapped_column(Float, nullable=True)
    fhir_json:          Mapped[dict]          = mapped_column(JSONB, nullable=False)
    created_at:         Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:         Mapped[datetime]      = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


