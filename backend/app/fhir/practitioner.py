from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, func
import uuid

from app.database.session import get_db
from app.database.models import Practitioner as PractitionerModel
from app.fhir.schemas_ext import PractitionerCreate, PractitionerResponse
from app.fhir.utils import error_outcome, generate_meta, build_bundle
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


@router.post("/Practitioner", status_code=201)
async def create_practitioner(
    practitioner: PractitionerCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    pr_id = practitioner.id or f"PR{uuid.uuid4().hex[:6].upper()}"
    p_dict = practitioner.model_dump(exclude_none=True)
    p_dict["id"] = pr_id
    p_dict["meta"] = generate_meta("1")

    fam, giv = _extract_names(practitioner.name)
    model = PractitionerModel(
        id=pr_id,
        family_name=fam,
        given_name=giv,
        gender=practitioner.gender,
        active=practitioner.active if practitioner.active is not None else True,
        fhir_json=p_dict
    )
    db.add(model)
    await db.commit()

    resp = JSONResponse(content=p_dict, status_code=201)
    resp.headers["Location"] = f"{settings.FHIR_BASE_URL}/Practitioner/{pr_id}"
    return resp


@router.get("/Practitioner/{id}")
async def get_practitioner(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(PractitionerModel).where(PractitionerModel.id == id)
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        return error_outcome(404, "not-found", f"Practitioner/{id} not found")
    return JSONResponse(content=item.fhir_json)


@router.put("/Practitioner/{id}")
async def update_practitioner(
    id: str,
    practitioner: PractitionerCreate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PractitionerModel).where(PractitionerModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Practitioner/{id} not found")

    p_dict = practitioner.model_dump(exclude_none=True)
    p_dict["id"] = id
    old_version = int(existing.fhir_json.get("meta", {}).get("versionId", "0"))
    p_dict["meta"] = generate_meta(str(old_version + 1))

    fam, giv = _extract_names(practitioner.name)
    existing.family_name = fam
    existing.given_name = giv
    existing.gender = practitioner.gender
    existing.active = practitioner.active if practitioner.active is not None else True
    existing.fhir_json = p_dict

    await db.commit()
    return JSONResponse(content=p_dict)


@router.delete("/Practitioner/{id}", status_code=204)
async def delete_practitioner(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(PractitionerModel).where(PractitionerModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Practitioner/{id} not found")

    await db.delete(existing)
    await db.commit()
    return JSONResponse(content={}, status_code=204)


@router.get("/Practitioner")
async def search_practitioners(
    request: Request,
    name: str = Query(None),
    family: str = Query(None),
    given: str = Query(None),
    gender: str = Query(None),
    active: bool = Query(None),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(PractitionerModel)
    if name:
        query = query.where(
            or_(
                PractitionerModel.family_name.ilike(f"%{name}%"),
                PractitionerModel.given_name.ilike(f"%{name}%")
            )
        )
    if family:
        query = query.where(PractitionerModel.family_name.ilike(f"%{family}%"))
    if given:
        query = query.where(PractitionerModel.given_name.ilike(f"%{given}%"))
    if gender:
        query = query.where(PractitionerModel.gender == gender)
    if active is not None:
        query = query.where(PractitionerModel.active == active)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    items = (await db.execute(query.offset(_offset).limit(_count))).scalars().all()
    entries = [i.fhir_json for i in items]

    return JSONResponse(content=build_bundle(entries, total, str(request.url).split("?")[0]))

