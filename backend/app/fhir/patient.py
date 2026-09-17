from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.sql import func
from datetime import datetime, date
import uuid
import json

from app.database.session import get_db
from app.database.models import Patient as PatientModel, User as UserModel
from app.fhir.schemas import PatientCreate, PatientUpdate, PatientResponse, Bundle, BundleEntry
from app.fhir.search import get_patient_search_params, PatientSearchParams
from app.auth.dependencies import get_current_user, require_role, verify_patient_access
from app.config import settings

router = APIRouter()

def _extract_names(names):
    family_name = None
    given_name = None
    if names and len(names) > 0:
        family_name = names[0].family
        if names[0].given and len(names[0].given) > 0:
            given_name = " ".join(names[0].given)
    return family_name, given_name

def _error_response(status_code: int, code: str, msg: str):
    return JSONResponse(
        status_code=status_code,
        content={
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": code,
                "diagnostics": msg
            }]
        },
        headers={"Content-Type": "application/fhir+json"}
    )

@router.post("/Patient", status_code=201)
async def create_patient(
    patient: PatientCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    patient_id = patient.id or f"P{uuid.uuid4().hex[:8].upper()}"
    
    patient_dict = patient.model_dump(exclude_none=True)
    patient_dict["id"] = patient_id
    patient_dict["meta"] = {
        "versionId": "1",
        "lastUpdated": datetime.utcnow().isoformat() + "Z"
    }
    
    family_name, given_name = _extract_names(patient.name)
    b_date = None
    if patient.birthDate:
        b_date = date.fromisoformat(patient.birthDate)

    new_patient = PatientModel(
        id=patient_id,
        family_name=family_name,
        given_name=given_name,
        gender=patient.gender,
        birth_date=b_date,
        active=patient.active if patient.active is not None else True,
        fhir_json=patient_dict
    )
    db.add(new_patient)
    await db.commit()
    
    response = JSONResponse(content=patient_dict, status_code=201)
    response.headers["Location"] = f"{settings.FHIR_BASE_URL}/Patient/{patient_id}"
    return response

@router.get("/Patient/{id}")
async def get_patient(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    verify_patient_access(id, current_user)
    stmt = select(PatientModel).where(PatientModel.id == id)
    result = await db.execute(stmt)
    patient = result.scalars().first()
    if not patient:
        return _error_response(404, "not-found", f"Patient/{id} not found")
    return JSONResponse(content=patient.fhir_json)

@router.put("/Patient/{id}")
async def update_patient(
    id: str,
    patient: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    stmt = select(PatientModel).where(PatientModel.id == id)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    if not existing:
        return _error_response(404, "not-found", f"Patient/{id} not found")
    
    patient_dict = patient.model_dump(exclude_none=True)
    patient_dict["id"] = id
    
    old_version = int(existing.fhir_json.get("meta", {}).get("versionId", "0"))
    patient_dict["meta"] = {
        "versionId": str(old_version + 1),
        "lastUpdated": datetime.utcnow().isoformat() + "Z"
    }

    family_name, given_name = _extract_names(patient.name)
    b_date = None
    if patient.birthDate:
        b_date = date.fromisoformat(patient.birthDate)
        
    existing.family_name = family_name
    existing.given_name = given_name
    existing.gender = patient.gender
    existing.birth_date = b_date
    existing.active = patient.active if patient.active is not None else True
    existing.fhir_json = patient_dict

    await db.commit()
    return JSONResponse(content=patient_dict)

@router.delete("/Patient/{id}", status_code=204)
async def delete_patient(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    stmt = select(PatientModel).where(PatientModel.id == id)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    if not existing:
        return _error_response(404, "not-found", f"Patient/{id} not found")

    await db.delete(existing)
    await db.commit()
    return Response(status_code=204)

@router.get("/Patient")
async def search_patient(
    request: Request,
    params: PatientSearchParams = Depends(get_patient_search_params),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    stmt = select(PatientModel)
    
    filters = []
    if current_user.role == "PATIENT":
        filters.append(PatientModel.id == (current_user.patient_id or ""))

    if params.family:
        filters.append(PatientModel.family_name.ilike(f"%{params.family}%"))
    if params.given:
        filters.append(PatientModel.given_name.ilike(f"%{params.given}%"))
    if params.name:
        filters.append(or_(
            PatientModel.family_name.ilike(f"%{params.name}%"),
            PatientModel.given_name.ilike(f"%{params.name}%")
        ))
    if params.gender:
        filters.append(PatientModel.gender == params.gender)
    if params.birthdate:
        try:
            b_date = date.fromisoformat(params.birthdate)
            filters.append(PatientModel.birth_date == b_date)
        except ValueError:
            pass
    if params.active is not None:
        filters.append(PatientModel.active == params.active)
        
    if filters:
        stmt = stmt.where(and_(*filters))
        
    if params._sort:
        if params._sort == "family":
            stmt = stmt.order_by(PatientModel.family_name.asc())
        elif params._sort == "-family":
            stmt = stmt.order_by(PatientModel.family_name.desc())
        elif params._sort == "birthdate":
            stmt = stmt.order_by(PatientModel.birth_date.asc())
        elif params._sort == "-birthdate":
            stmt = stmt.order_by(PatientModel.birth_date.desc())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.limit(params._count).offset(params._offset)
    result = await db.execute(stmt)
    patients = result.scalars().all()

    entries = []
    base_url = str(request.url).split('?')[0]
    for p in patients:
        entries.append(BundleEntry(
            fullUrl=f"{base_url}/{p.id}",
            resource=PatientResponse(**p.fhir_json)
        ))

    bundle = Bundle(
        total=total,
        link=[{"relation": "self", "url": str(request.url)}],
        entry=entries
    )

    return JSONResponse(
        content=bundle.model_dump(exclude_none=True),
        headers={"Content-Type": "application/fhir+json"}
    )
