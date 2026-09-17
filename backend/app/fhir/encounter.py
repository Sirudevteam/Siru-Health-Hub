from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import uuid

from app.database.session import get_db
from app.database.models import Encounter as EncounterModel, User as UserModel
from app.fhir.schemas_ext import EncounterCreate, EncounterResponse
from app.fhir.utils import error_outcome, generate_meta, build_bundle, clean_reference_id
from app.auth.dependencies import get_current_user, require_role, verify_patient_access
from app.config import settings

router = APIRouter()


def _extract_references(encounter: EncounterCreate):
    patient_id = clean_reference_id(encounter.subject.reference) if encounter.subject else None
    practitioner_id = None
    if encounter.participant:
        for p in encounter.participant:
            if p.individual and p.individual.reference:
                practitioner_id = clean_reference_id(p.individual.reference)
                break
    return patient_id, practitioner_id


@router.post("/Encounter", status_code=201)
async def create_encounter(
    encounter: EncounterCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR", "NURSE"))
):
    enc_id = encounter.id or f"ENC{uuid.uuid4().hex[:6].upper()}"
    e_dict = encounter.model_dump(exclude_none=True, by_alias=True)
    e_dict["id"] = enc_id
    e_dict["meta"] = generate_meta("1")

    pat_id, prac_id = _extract_references(encounter)
    enc_class = encounter.class_.code if encounter.class_ else None

    model = EncounterModel(
        id=enc_id,
        patient_id=pat_id,
        practitioner_id=prac_id,
        status=encounter.status,
        encounter_class=enc_class,
        fhir_json=e_dict
    )
    db.add(model)
    await db.commit()

    resp = JSONResponse(content=e_dict, status_code=201)
    resp.headers["Location"] = f"{settings.FHIR_BASE_URL}/Encounter/{enc_id}"
    return resp


@router.get("/Encounter/{id}")
async def get_encounter(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    stmt = select(EncounterModel).where(EncounterModel.id == id)
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        return error_outcome(404, "not-found", f"Encounter/{id} not found")

    if item.patient_id:
        verify_patient_access(item.patient_id, current_user)

    return JSONResponse(content=item.fhir_json)


@router.put("/Encounter/{id}")
async def update_encounter(
    id: str,
    encounter: EncounterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR", "NURSE"))
):
    stmt = select(EncounterModel).where(EncounterModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Encounter/{id} not found")

    e_dict = encounter.model_dump(exclude_none=True, by_alias=True)
    e_dict["id"] = id
    old_version = int(existing.fhir_json.get("meta", {}).get("versionId", "0"))
    e_dict["meta"] = generate_meta(str(old_version + 1))

    pat_id, prac_id = _extract_references(encounter)
    enc_class = encounter.class_.code if encounter.class_ else None

    existing.patient_id = pat_id
    existing.practitioner_id = prac_id
    existing.status = encounter.status
    existing.encounter_class = enc_class
    existing.fhir_json = e_dict

    await db.commit()
    return JSONResponse(content=e_dict)


@router.delete("/Encounter/{id}", status_code=204)
async def delete_encounter(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    stmt = select(EncounterModel).where(EncounterModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Encounter/{id} not found")

    await db.delete(existing)
    await db.commit()
    return JSONResponse(content={}, status_code=204)


@router.get("/Encounter")
async def search_encounters(
    request: Request,
    patient: str = Query(None),
    subject: str = Query(None),
    practitioner: str = Query(None),
    status: str = Query(None),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    query = select(EncounterModel)
    pat_filter = clean_reference_id(patient or subject)

    if current_user.role == "PATIENT":
        if pat_filter and pat_filter != current_user.patient_id:
            raise HTTPException(
                status_code=403,
                detail="Access forbidden: Patients can only access their own encounters."
            )
        pat_filter = current_user.patient_id

    if pat_filter:
        query = query.where(EncounterModel.patient_id == pat_filter)
    if practitioner:
        query = query.where(EncounterModel.practitioner_id == clean_reference_id(practitioner))
    if status:
        query = query.where(EncounterModel.status == status)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    items = (await db.execute(query.order_by(desc(EncounterModel.created_at)).offset(_offset).limit(_count))).scalars().all()
    entries = [i.fhir_json for i in items]

    return JSONResponse(content=build_bundle(entries, total, str(request.url).split("?")[0]))
