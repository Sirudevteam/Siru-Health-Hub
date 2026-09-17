from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.database.session import get_db
from app.database.models import Organization as OrganizationModel
from app.fhir.schemas_ext import OrganizationCreate, OrganizationResponse
from app.fhir.utils import error_outcome, generate_meta, build_bundle
from app.config import settings

router = APIRouter()


@router.post("/Organization", status_code=201)
async def create_organization(
    org: OrganizationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    org_id = org.id or f"ORG{uuid.uuid4().hex[:6].upper()}"
    o_dict = org.model_dump(exclude_none=True)
    o_dict["id"] = org_id
    o_dict["meta"] = generate_meta("1")

    model = OrganizationModel(
        id=org_id,
        name=org.name,
        active=org.active if org.active is not None else True,
        fhir_json=o_dict
    )
    db.add(model)
    await db.commit()

    resp = JSONResponse(content=o_dict, status_code=201)
    resp.headers["Location"] = f"{settings.FHIR_BASE_URL}/Organization/{org_id}"
    return resp


@router.get("/Organization/{id}")
async def get_organization(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(OrganizationModel).where(OrganizationModel.id == id)
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        return error_outcome(404, "not-found", f"Organization/{id} not found")
    return JSONResponse(content=item.fhir_json)


@router.put("/Organization/{id}")
async def update_organization(
    id: str,
    org: OrganizationCreate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OrganizationModel).where(OrganizationModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Organization/{id} not found")

    o_dict = org.model_dump(exclude_none=True)
    o_dict["id"] = id
    old_version = int(existing.fhir_json.get("meta", {}).get("versionId", "0"))
    o_dict["meta"] = generate_meta(str(old_version + 1))

    existing.name = org.name
    existing.active = org.active if org.active is not None else True
    existing.fhir_json = o_dict

    await db.commit()
    return JSONResponse(content=o_dict)


@router.delete("/Organization/{id}", status_code=204)
async def delete_organization(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(OrganizationModel).where(OrganizationModel.id == id)
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if not existing:
        return error_outcome(404, "not-found", f"Organization/{id} not found")

    await db.delete(existing)
    await db.commit()
    return JSONResponse(content={}, status_code=204)


@router.get("/Organization")
async def search_organizations(
    request: Request,
    name: str = Query(None),
    active: bool = Query(None),
    _count: int = Query(20, ge=1, le=100),
    _offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(OrganizationModel)
    if name:
        query = query.where(OrganizationModel.name.ilike(f"%{name}%"))
    if active is not None:
        query = query.where(OrganizationModel.active == active)

    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    items = (await db.execute(query.offset(_offset).limit(_count))).scalars().all()
    entries = [i.fhir_json for i in items]

    return JSONResponse(content=build_bundle(entries, total, str(request.url).split("?")[0]))

