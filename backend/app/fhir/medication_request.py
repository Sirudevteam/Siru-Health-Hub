from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import uuid

from app.database.session import get_db
from app.database.models import MedicationRequest as MedicationRequestModel, User as UserModel
from app.fhir.schemas_ext import MedicationRequestCreate, MedicationRequestResponse
from app.fhir.utils import error_outcome, generate_meta, build_bundle, clean_reference_id
from app.auth.dependencies import get_current_user, require_role, verify_patient_access
from app.config import settings

router = APIRouter()


def _extract_med_details(med: MedicationRequestCreate):
    patient_id = clean_reference_id(med.subject.reference) if med.subject else None
    encounter_id = clean_reference_id(med.encounter.reference) if med.encounter else None
    
    code = None
    if med.medicationCodeableConcept:
        if med.medicationCodeableConcept.coding and len(med.medicationCodeableConcept.coding) > 0:
            code = med.medicationCodeableConcept.coding[0].get("code")
        if not code and med.medicationCodeableConcept.text:
            code = med.medicationCodeableConcept.text

    return patient_id, encounter_id, code


@router.post("/MedicationRequest", status_code=201)
async def create_medication_request(
    med_req: MedicationRequestCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR"))
):
    med_id = med_req.id or f"MED{uuid.uuid4().hex[:6].upper()}"
    m_dict = med_req.model_dump(exclude_none=True)
    m_dict["id"] = med_id
    m_dict["meta"] = generate_meta("1")

    pat_id, enc_id, med_code = _extract_med_details(med_req)

    model = MedicationRequestModel(
        id=med_id,
        patient_id=pat_id,
        encounter_id=enc_id,
        status=med_req.status,
        intent=med_req.intent,
        medication_code=med_code,
        fhir_json=m_dict
    )
    db.add(model)
    await db.commit()

    resp = JSONResponse(content=m_dict, status_code=201)
    resp.headers["Location"] = f"{settings.FHIR_BASE_URL}/MedicationRequest/{med_id}"
    return resp


@router.get("/MedicationRequest/{id}")
async def get_medication_request(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    stmt = select(MedicationRequestModel).where(MedicationRequestModel.id == id)
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        return error_outcome(404, "not-found", f"MedicationRequest/{id} not found")

    if item.patient_id:
        verify_patient_access(item.patient_id, current_user)

    return JSONResponse(content=item.fhir_json)


@router.put("/MedicationRequest/{id}")
async def update_medication_request(
    id: str,
    med_req: MedicationRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR"))
):
    stmt = select(MedicationRequestModel).where(MedicationRequestModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"MedicationRequest/{id} not found")

    m_dict = med_req.model_dump(exclude_none=True)
    m_dict["id"] = id
    old_version = int(existing.fhir_json.get("meta", {}).get("versionId", "0"))
    m_dict["meta"] = generate_meta(str(old_version + 1))

    pat_id, enc_id, med_code = _extract_med_details(med_req)

    existing.patient_id = pat_id
    existing.encounter_id = enc_id
    existing.status = med_req.status
    existing.intent = med_req.intent
    existing.medication_code = med_code
    existing.fhir_json = m_dict

    await db.commit()
    return JSONResponse(content=m_dict)


@router.delete("/MedicationRequest/{id}", status_code=204)
async def delete_medication_request(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    stmt = select(MedicationRequestModel).where(MedicationRequestModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"MedicationRequest/{id} not found")

    await db.delete(existing)
    await db.commit()
    return JSONResponse(content={}, status_code=204)


@router.get("/MedicationRequest")
async def search_medication_requests(
    request: Request,
    patient: str = Query(None),
    subject: str = Query(None),
    encounter: str = Query(None),
    status: str = Query(None),
    intent: str = Query(None),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    query = select(MedicationRequestModel)
    pat_filter = clean_reference_id(patient or subject)

    if current_user.role == "PATIENT":
        if pat_filter and pat_filter != current_user.patient_id:
            raise HTTPException(
                status_code=403,
                detail="Access forbidden: Patients can only access their own prescriptions."
            )
        pat_filter = current_user.patient_id

    if pat_filter:
        query = query.where(MedicationRequestModel.patient_id == pat_filter)
    if encounter:
        query = query.where(MedicationRequestModel.encounter_id == clean_reference_id(encounter))
    if status:
        query = query.where(MedicationRequestModel.status == status)
    if intent:
        query = query.where(MedicationRequestModel.intent == intent)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    items = (await db.execute(query.order_by(desc(MedicationRequestModel.created_at)).offset(_offset).limit(_count))).scalars().all()
    entries = [i.fhir_json for i in items]

    return JSONResponse(content=build_bundle(entries, total, str(request.url).split("?")[0]))
