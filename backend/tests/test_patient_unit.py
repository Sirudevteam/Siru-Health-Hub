import pytest
from app.fhir.schemas import PatientCreate, HumanName

def test_valid_patient_schema(sample_patient):
    patient = PatientCreate(**sample_patient)
    assert patient.resourceType == "Patient"
    assert patient.gender == "male"
    assert patient.name[0].family == "Kumar"

def test_invalid_gender(sample_patient):
    sample_patient["gender"] = "invalid"
    with pytest.raises(ValueError, match="Invalid gender"):
        PatientCreate(**sample_patient)

def test_invalid_birth_date(sample_patient):
    sample_patient["birthDate"] = "1995/05/10"
    with pytest.raises(ValueError, match="Invalid birthDate format"):
        PatientCreate(**sample_patient)

def test_missing_resource_type_is_defaulted():
    patient = PatientCreate(gender="male")
    assert patient.resourceType == "Patient"

def test_human_name_schema():
    name = HumanName(family="Doe", given=["John", "Jane"])
    assert name.family == "Doe"
    assert "John" in name.given
