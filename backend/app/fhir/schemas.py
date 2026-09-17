from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal
from datetime import date
import re
import uuid

class HumanName(BaseModel):
    use: Optional[str] = None  # usual | official | temp | nickname | anonymous | old | maiden
    text: Optional[str] = None
    family: Optional[str] = None
    given: Optional[List[str]] = None
    prefix: Optional[List[str]] = None
    suffix: Optional[List[str]] = None

class ContactPoint(BaseModel):
    system: Optional[str] = None  # phone | fax | email | pager | url | sms | other
    value: Optional[str] = None
    use: Optional[str] = None  # home | work | temp | old | mobile

class Address(BaseModel):
    use: Optional[str] = None
    type: Optional[str] = None
    text: Optional[str] = None
    line: Optional[List[str]] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None

class CodeableConcept(BaseModel):
    coding: Optional[List[dict]] = None
    text: Optional[str] = None

class PatientCreate(BaseModel):
    resourceType: Literal["Patient"] = "Patient"
    id: Optional[str] = None
    active: Optional[bool] = True
    name: Optional[List[HumanName]] = None
    telecom: Optional[List[ContactPoint]] = None
    gender: Optional[str] = None  # male | female | other | unknown
    birthDate: Optional[str] = None  # YYYY-MM-DD
    address: Optional[List[Address]] = None
    maritalStatus: Optional[CodeableConcept] = None
    communication: Optional[List[dict]] = None
    generalPractitioner: Optional[List[dict]] = None
    
    @model_validator(mode='after')
    def validate_gender(self):
        if self.gender and self.gender not in ['male', 'female', 'other', 'unknown']:
            raise ValueError(f"Invalid gender: {self.gender}. Must be male|female|other|unknown")
        return self
    
    @model_validator(mode='after')
    def validate_birth_date(self):
        if self.birthDate:
            try:
                date.fromisoformat(self.birthDate)
            except ValueError:
                raise ValueError(f"Invalid birthDate format: {self.birthDate}. Use YYYY-MM-DD")
        return self

class PatientUpdate(PatientCreate):
    pass

class PatientResponse(PatientCreate):
    id: str
    meta: Optional[dict] = None

class BundleEntry(BaseModel):
    fullUrl: str
    resource: PatientResponse

class Bundle(BaseModel):
    resourceType: Literal["Bundle"] = "Bundle"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "searchset"
    total: int
    link: Optional[List[dict]] = None
    entry: Optional[List[BundleEntry]] = None
