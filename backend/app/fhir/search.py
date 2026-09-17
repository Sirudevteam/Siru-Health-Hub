from typing import Optional
from fastapi import Query
from dataclasses import dataclass

@dataclass
class PatientSearchParams:
    name: Optional[str] = None
    family: Optional[str] = None
    given: Optional[str] = None
    birthdate: Optional[str] = None
    gender: Optional[str] = None
    active: Optional[bool] = None
    _count: int = 20
    _offset: int = 0
    _sort: Optional[str] = None

def get_patient_search_params(
    name: Optional[str] = Query(None, alias="name"),
    family: Optional[str] = Query(None, alias="family"),
    given: Optional[str] = Query(None, alias="given"),
    birthdate: Optional[str] = Query(None, alias="birthdate"),
    gender: Optional[str] = Query(None, alias="gender"),
    active: Optional[bool] = Query(None, alias="active"),
    _count: int = Query(20, alias="_count", ge=1, le=100),
    _offset: int = Query(0, alias="_offset", ge=0),
    _sort: Optional[str] = Query(None, alias="_sort"),
) -> PatientSearchParams:
    return PatientSearchParams(
        name=name, family=family, given=given,
        birthdate=birthdate, gender=gender, active=active,
        _count=_count, _offset=_offset, _sort=_sort
    )
