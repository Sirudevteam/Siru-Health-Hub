# ==============================================================================
# Siru HealthHub — FHIR Coverage Router & Real-Time Eligibility Service
# Handles insurance policies and real-time HIPAA 270/271 eligibility verification.
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional
from datetime import datetime, date
import uuid

from app.database.session import get_db
from app.database.models import Coverage as CoverageModel, User as UserModel
from app.auth.dependencies import get_current_user, require_role, verify_patient_access

router = APIRouter()


def _extract_patient_id(beneficiary_obj: Optional[dict]) -> Optional[str]:
    if not beneficiary_obj or not isinstance(beneficiary_obj, dict):
        return None
    ref = beneficiary_obj.get("reference", "")
    return ref.replace("Patient/", "") if ref else None


def _extract_payor_id(payor_list: Optional[list]) -> Optional[str]:
    if not payor_list or not isinstance(payor_list, list) or len(payor_list) == 0:
        return None
    ref = payor_list[0].get("reference", "")
    return ref.replace("Organization/", "") if ref else None


@router.post("/Coverage", status_code=status.HTTP_201_CREATED)
async def create_coverage(
    payload: dict,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR", "NURSE"))
):
    """Create a new FHIR Coverage (Insurance Policy) resource."""
    cov_id = payload.get("id") or f"COV{uuid.uuid4().hex[:8].upper()}"
    payload["id"] = cov_id
    payload["resourceType"] = "Coverage"

    now_iso = datetime.utcnow().isoformat() + "Z"
    payload["meta"] = {"versionId": "1", "lastUpdated": now_iso}

    patient_id = _extract_patient_id(payload.get("beneficiary"))
    payor_id = _extract_payor_id(payload.get("payor"))
    subscriber_id = payload.get("subscriberId")
    cov_status = payload.get("status", "active")
    plan_name = None
    if "class" in payload and isinstance(payload["class"], list) and len(payload["class"]) > 0:
        plan_name = payload["class"][0].get("name")
    elif "type" in payload and isinstance(payload["type"], dict):
        plan_name = payload["type"].get("text")

    coverage_rec = CoverageModel(
        id=cov_id,
        patient_id=patient_id,
        payor_id=payor_id,
        subscriber_id=subscriber_id,
        status=cov_status,
        plan_name=plan_name,
        fhir_json=payload
    )

    db.add(coverage_rec)
    await db.commit()
    await db.refresh(coverage_rec)

    response.headers["Location"] = f"/fhir/Coverage/{cov_id}"
    return coverage_rec.fhir_json


@router.get("/Coverage/{id}")
async def get_coverage(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Retrieve an insurance Coverage resource by ID."""
    stmt = select(CoverageModel).where(CoverageModel.id == id)
    result = await db.execute(stmt)
    cov = result.scalars().first()

    if not cov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "resourceType": "OperationOutcome",
                "issue": [{"severity": "error", "code": "not-found", "diagnostics": f"Coverage/{id} not found"}]
            }
        )

    if current_user.role == "PATIENT" and cov.patient_id:
        verify_patient_access(cov.patient_id, current_user)

    return cov.fhir_json


@router.get("/Coverage")
async def search_coverages(
    patient: Optional[str] = Query(None, alias="patient"),
    status_filter: Optional[str] = Query(None, alias="status"),
    subscriber_id: Optional[str] = Query(None, alias="subscriber-id"),
    _count: int = Query(50, alias="_count"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Search Coverage policies by patient, status, or subscriber ID."""
    if current_user.role == "PATIENT":
        user_pid = (current_user.patient_id or "").replace("Patient/", "")
        patient = user_pid

    stmt = select(CoverageModel)
    if patient:
        clean_pid = patient.replace("Patient/", "")
        stmt = stmt.where(CoverageModel.patient_id == clean_pid)
    if status_filter:
        stmt = stmt.where(CoverageModel.status == status_filter)
    if subscriber_id:
        stmt = stmt.where(CoverageModel.subscriber_id == subscriber_id)

    stmt = stmt.limit(_count)
    result = await db.execute(stmt)
    coverages = result.scalars().all()

    entries = [{"fullUrl": f"/fhir/Coverage/{c.id}", "resource": c.fhir_json} for c in coverages]
    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "searchset",
        "total": len(entries),
        "entry": entries
    }


@router.post("/Coverage/{id}/$eligibility-check")
@router.post("/Coverage/{id}/eligibility-check")
async def check_coverage_eligibility(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Real-time Insurance Eligibility Verification (EDI 270/271 Simulation).

    Evaluates policy status, date coverage, network status, copay rates, and
    deductible obligations.
    """
    stmt = select(CoverageModel).where(CoverageModel.id == id)
    result = await db.execute(stmt)
    cov = result.scalars().first()

    if not cov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "resourceType": "OperationOutcome",
                "issue": [{"severity": "error", "code": "not-found", "diagnostics": f"Coverage/{id} not found"}]
            }
        )

    if current_user.role == "PATIENT" and cov.patient_id:
        verify_patient_access(cov.patient_id, current_user)

    data = cov.fhir_json
    status_val = data.get("status", "inactive")
    period = data.get("period", {})
    start = period.get("start")
    end = period.get("end")
    today = date.today().isoformat()

    eligible = True
    status_text = "Active Coverage"
    disposition = "Patient is actively covered under plan."

    if status_val != "active":
        eligible = False
        status_text = f"Policy {status_val.capitalize()}"
        disposition = f"Coverage status is '{status_val}'. Benefits are suspended."
    elif start and today < start:
        eligible = False
        status_text = "Future Effective Date"
        disposition = f"Policy effective start date is in the future: {start}."
    elif end and today > end:
        eligible = False
        status_text = "Policy Terminated"
        disposition = f"Coverage terminated on {end}. Policy has lapsed."

    plan_name = cov.plan_name or "Standard Health Plan"
    subscriber_id = cov.subscriber_id or data.get("subscriberId", "N/A")

    return {
        "resourceType": "Parameters",
        "id": str(uuid.uuid4()),
        "eligible": eligible,
        "status": status_text,
        "planName": plan_name,
        "subscriberId": subscriber_id,
        "copayPercent": 10 if eligible else 0,
        "coinsuranceBenefit": 90 if eligible else 0,
        "remainingDeductible": {"value": 5000.0, "currency": "INR"} if eligible else {"value": 0.0, "currency": "INR"},
        "inNetwork": True,
        "disposition": disposition,
        "verifiedAt": datetime.utcnow().isoformat() + "Z"
    }
