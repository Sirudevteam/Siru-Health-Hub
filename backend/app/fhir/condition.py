from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import uuid

from app.database.session import get_db
from app.database.models import Condition as ConditionModel, User as UserModel
from app.fhir.schemas_ext import ConditionCreate, ConditionResponse
from app.fhir.utils import error_outcome, generate_meta, build_bundle, clean_reference_id
from app.auth.dependencies import get_current_user, require_role, verify_patient_access
from app.config import settings

router = APIRouter()


def _extract_condition_details(cond: ConditionCreate):
    patient_id = clean_reference_id(cond.subject.reference) if cond.subject else None
    encounter_id = clean_reference_id(cond.encounter.reference) if cond.encounter else None
    
    clinical_status = None
    if cond.clinicalStatus:
        if cond.clinicalStatus.coding and len(cond.clinicalStatus.coding) > 0:
            clinical_status = cond.clinicalStatus.coding[0].get("code")
        elif cond.clinicalStatus.text:
            clinical_status = cond.clinicalStatus.text

    code = None
    if cond.code:
        if cond.code.coding and len(cond.code.coding) > 0:
            code = cond.code.coding[0].get("code")
        if not code and cond.code.text:
            code = cond.code.text

    return patient_id, encounter_id, clinical_status, code


@router.post("/Condition", status_code=201)
async def create_condition(
    condition: ConditionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR"))
):
    cond_id = condition.id or f"CON{uuid.uuid4().hex[:6].upper()}"
    c_dict = condition.model_dump(exclude_none=True)
    c_dict["id"] = cond_id
    c_dict["meta"] = generate_meta("1")

    pat_id, enc_id, clin_stat, code = _extract_condition_details(condition)

    model = ConditionModel(
        id=cond_id,
        patient_id=pat_id,
        encounter_id=enc_id,
        clinical_status=clin_stat,
        code=code,
        fhir_json=c_dict
    )
    db.add(model)
    await db.commit()

    resp = JSONResponse(content=c_dict, status_code=201)
    resp.headers["Location"] = f"{settings.FHIR_BASE_URL}/Condition/{cond_id}"
    return resp


@router.get("/Condition/{id}")
async def get_condition(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    stmt = select(ConditionModel).where(ConditionModel.id == id)
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        return error_outcome(404, "not-found", f"Condition/{id} not found")

    if item.patient_id:
        verify_patient_access(item.patient_id, current_user)

    return JSONResponse(content=item.fhir_json)


@router.put("/Condition/{id}")
async def update_condition(
    id: str,
    condition: ConditionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR"))
):
    stmt = select(ConditionModel).where(ConditionModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Condition/{id} not found")

    c_dict = condition.model_dump(exclude_none=True)
    c_dict["id"] = id
    old_version = int(existing.fhir_json.get("meta", {}).get("versionId", "0"))
    c_dict["meta"] = generate_meta(str(old_version + 1))

    pat_id, enc_id, clin_stat, code = _extract_condition_details(condition)

    existing.patient_id = pat_id
    existing.encounter_id = enc_id
    existing.clinical_status = clin_stat
    existing.code = code
    existing.fhir_json = c_dict

    await db.commit()
    return JSONResponse(content=c_dict)


@router.delete("/Condition/{id}", status_code=204)
async def delete_condition(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    stmt = select(ConditionModel).where(ConditionModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Condition/{id} not found")

    await db.delete(existing)
    await db.commit()
    return JSONResponse(content={}, status_code=204)


@router.get("/Condition")
async def search_conditions(
    request: Request,
    patient: str = Query(None),
    subject: str = Query(None),
    encounter: str = Query(None),
    clinical_status: str = Query(None, alias="clinical-status"),
    code: str = Query(None),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    query = select(ConditionModel)
    pat_filter = clean_reference_id(patient or subject)

    if current_user.role == "PATIENT":
        if pat_filter and pat_filter != current_user.patient_id:
            raise HTTPException(
                status_code=403,
                detail="Access forbidden: Patients can only access their own conditions."
            )
        pat_filter = current_user.patient_id

    if pat_filter:
        query = query.where(ConditionModel.patient_id == pat_filter)
    if encounter:
        query = query.where(ConditionModel.encounter_id == clean_reference_id(encounter))
    if clinical_status:
        query = query.where(ConditionModel.clinical_status == clinical_status)
    if code:
        query = query.where(ConditionModel.code.ilike(f"%{code}%"))

    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    items = (await db.execute(query.order_by(desc(ConditionModel.created_at)).offset(_offset).limit(_count))).scalars().all()
    entries = [i.fhir_json for i in items]

    return JSONResponse(content=build_bundle(entries, total, str(request.url).split("?")[0]))
