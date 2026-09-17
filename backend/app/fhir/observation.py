from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from datetime import datetime
import uuid

from app.database.session import get_db
from app.database.models import Observation as ObservationModel, User as UserModel
from app.fhir.schemas_ext import ObservationCreate, ObservationResponse
from app.fhir.utils import error_outcome, generate_meta, build_bundle, clean_reference_id
from app.auth.dependencies import get_current_user, require_role, verify_patient_access
from app.config import settings

router = APIRouter()


def _extract_obs_details(obs: ObservationCreate):
    patient_id = clean_reference_id(obs.subject.reference) if obs.subject else None
    encounter_id = clean_reference_id(obs.encounter.reference) if obs.encounter else None
    
    category = None
    if obs.category and len(obs.category) > 0:
        c = obs.category[0]
        if c.coding and len(c.coding) > 0:
            category = c.coding[0].get("code") or c.coding[0].get("display")
        elif c.text:
            category = c.text

    code = None
    if obs.code:
        if obs.code.coding and len(obs.code.coding) > 0:
            code = obs.code.coding[0].get("code")
        if not code and obs.code.text:
            code = obs.code.text

    val_num = obs.valueQuantity.value if obs.valueQuantity else None
    val_str = obs.valueString if obs.valueString else None

    eff_dt = None
    if obs.effectiveDateTime:
        try:
            eff_dt = datetime.fromisoformat(obs.effectiveDateTime.replace("Z", "+00:00"))
        except Exception:
            pass

    return patient_id, encounter_id, category, code, val_num, val_str, eff_dt


@router.post("/Observation", status_code=201)
async def create_observation(
    observation: ObservationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR", "NURSE"))
):
    obs_id = observation.id or f"OBS{uuid.uuid4().hex[:6].upper()}"
    o_dict = observation.model_dump(exclude_none=True)
    o_dict["id"] = obs_id
    o_dict["meta"] = generate_meta("1")

    pat_id, enc_id, cat, code, val_num, val_str, eff_dt = _extract_obs_details(observation)

    model = ObservationModel(
        id=obs_id,
        patient_id=pat_id,
        encounter_id=enc_id,
        category=cat,
        code=code,
        value_numeric=val_num,
        value_string=val_str,
        effective_datetime=eff_dt,
        fhir_json=o_dict
    )
    db.add(model)
    await db.commit()

    resp = JSONResponse(content=o_dict, status_code=201)
    resp.headers["Location"] = f"{settings.FHIR_BASE_URL}/Observation/{obs_id}"
    return resp


@router.get("/Observation/{id}")
async def get_observation(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    stmt = select(ObservationModel).where(ObservationModel.id == id)
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        return error_outcome(404, "not-found", f"Observation/{id} not found")

    if item.patient_id:
        verify_patient_access(item.patient_id, current_user)

    return JSONResponse(content=item.fhir_json)


@router.put("/Observation/{id}")
async def update_observation(
    id: str,
    observation: ObservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR", "NURSE"))
):
    stmt = select(ObservationModel).where(ObservationModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Observation/{id} not found")

    o_dict = observation.model_dump(exclude_none=True)
    o_dict["id"] = id
    old_version = int(existing.fhir_json.get("meta", {}).get("versionId", "0"))
    o_dict["meta"] = generate_meta(str(old_version + 1))

    pat_id, enc_id, cat, code, val_num, val_str, eff_dt = _extract_obs_details(observation)

    existing.patient_id = pat_id
    existing.encounter_id = enc_id
    existing.category = cat
    existing.code = code
    existing.value_numeric = val_num
    existing.value_string = val_str
    existing.effective_datetime = eff_dt
    existing.fhir_json = o_dict

    await db.commit()
    return JSONResponse(content=o_dict)


@router.delete("/Observation/{id}", status_code=204)
async def delete_observation(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    stmt = select(ObservationModel).where(ObservationModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Observation/{id} not found")

    await db.delete(existing)
    await db.commit()
    return JSONResponse(content={}, status_code=204)


@router.get("/Observation")
async def search_observations(
    request: Request,
    patient: str = Query(None),
    subject: str = Query(None),
    encounter: str = Query(None),
    category: str = Query(None),
    code: str = Query(None),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    query = select(ObservationModel)
    pat_filter = clean_reference_id(patient or subject)

    if current_user.role == "PATIENT":
        if pat_filter and pat_filter != current_user.patient_id:
            raise HTTPException(
                status_code=403,
                detail="Access forbidden: Patients can only access their own observations."
            )
        pat_filter = current_user.patient_id

    if pat_filter:
        query = query.where(ObservationModel.patient_id == pat_filter)
    if encounter:
        query = query.where(ObservationModel.encounter_id == clean_reference_id(encounter))
    if category:
        query = query.where(ObservationModel.category.ilike(f"%{category}%"))
    if code:
        query = query.where(ObservationModel.code.ilike(f"%{code}%"))

    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    items = (await db.execute(query.order_by(desc(ObservationModel.created_at)).offset(_offset).limit(_count))).scalars().all()
    entries = [i.fhir_json for i in items]

    return JSONResponse(content=build_bundle(entries, total, str(request.url).split("?")[0]))
