from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime
import uuid

from app.database.session import get_db
from app.database.models import Appointment as AppointmentModel
from app.fhir.schemas_ext import AppointmentCreate, AppointmentResponse
from app.fhir.utils import error_outcome, generate_meta, build_bundle, clean_reference_id
from app.config import settings

router = APIRouter()


def _extract_appt_details(appt: AppointmentCreate):
    patient_id = None
    practitioner_id = None
    for p in appt.participant:
        if p.actor and p.actor.reference:
            ref = p.actor.reference
            if ref.startswith("Patient/") or "Patient" in (p.actor.type or ""):
                patient_id = clean_reference_id(ref)
            elif ref.startswith("Practitioner/") or "Practitioner" in (p.actor.type or ""):
                practitioner_id = clean_reference_id(ref)
            else:
                if not patient_id:
                    patient_id = clean_reference_id(ref)

    start_dt = None
    if appt.start:
        try:
            start_dt = datetime.fromisoformat(appt.start.replace("Z", "+00:00"))
        except Exception:
            pass

    end_dt = None
    if appt.end:
        try:
            end_dt = datetime.fromisoformat(appt.end.replace("Z", "+00:00"))
        except Exception:
            pass

    return patient_id, practitioner_id, start_dt, end_dt


@router.post("/Appointment", status_code=201)
async def create_appointment(
    appt: AppointmentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    apt_id = appt.id or f"APT{uuid.uuid4().hex[:6].upper()}"
    a_dict = appt.model_dump(exclude_none=True)
    a_dict["id"] = apt_id
    a_dict["meta"] = generate_meta("1")

    pat_id, prac_id, s_dt, e_dt = _extract_appt_details(appt)

    model = AppointmentModel(
        id=apt_id,
        patient_id=pat_id,
        practitioner_id=prac_id,
        status=appt.status,
        start_time=s_dt,
        end_time=e_dt,
        fhir_json=a_dict
    )
    db.add(model)
    await db.commit()

    resp = JSONResponse(content=a_dict, status_code=201)
    resp.headers["Location"] = f"{settings.FHIR_BASE_URL}/Appointment/{apt_id}"
    return resp


@router.get("/Appointment/{id}")
async def get_appointment(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AppointmentModel).where(AppointmentModel.id == id)
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        return error_outcome(404, "not-found", f"Appointment/{id} not found")
    return JSONResponse(content=item.fhir_json)


@router.put("/Appointment/{id}")
async def update_appointment(
    id: str,
    appt: AppointmentCreate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AppointmentModel).where(AppointmentModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Appointment/{id} not found")

    a_dict = appt.model_dump(exclude_none=True)
    a_dict["id"] = id
    old_version = int(existing.fhir_json.get("meta", {}).get("versionId", "0"))
    a_dict["meta"] = generate_meta(str(old_version + 1))

    pat_id, prac_id, s_dt, e_dt = _extract_appt_details(appt)

    existing.patient_id = pat_id
    existing.practitioner_id = prac_id
    existing.status = appt.status
    existing.start_time = s_dt
    existing.end_time = e_dt
    existing.fhir_json = a_dict

    await db.commit()
    return JSONResponse(content=a_dict)


@router.delete("/Appointment/{id}", status_code=204)
async def delete_appointment(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(AppointmentModel).where(AppointmentModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Appointment/{id} not found")

    await db.delete(existing)
    await db.commit()
    return JSONResponse(content={}, status_code=204)


@router.get("/Appointment")
async def search_appointments(
    request: Request,
    patient: str = Query(None),
    practitioner: str = Query(None),
    status: str = Query(None),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(AppointmentModel)
    if patient:
        query = query.where(AppointmentModel.patient_id == clean_reference_id(patient))
    if practitioner:
        query = query.where(AppointmentModel.practitioner_id == clean_reference_id(practitioner))
    if status:
        query = query.where(AppointmentModel.status == status)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    items = (await db.execute(query.order_by(desc(AppointmentModel.created_at)).offset(_offset).limit(_count))).scalars().all()
    entries = [i.fhir_json for i in items]

    return JSONResponse(content=build_bundle(entries, total, str(request.url).split("?")[0]))

