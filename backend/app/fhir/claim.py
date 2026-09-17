# ==============================================================================
# Siru HealthHub — FHIR Claim & ClaimResponse Router
# Handles healthcare claims submission, automated payer adjudication, and
# Explanation of Benefits (EOB) / ClaimResponse retrieval.
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import uuid

from app.database.session import get_db
from app.database.models import (
    Claim as ClaimModel,
    ClaimResponse as ClaimResponseModel,
    Coverage as CoverageModel,
    User as UserModel
)
from app.auth.dependencies import get_current_user, require_role, verify_patient_access
from app.rcm.adjudication import adjudicate_claim

router = APIRouter()


def _clean_ref(ref_obj: Optional[dict], prefix: str) -> Optional[str]:
    if not ref_obj or not isinstance(ref_obj, dict):
        return None
    r = ref_obj.get("reference", "")
    return r.replace(f"{prefix}/", "") if r else None


# ─── Claim Endpoints ──────────────────────────────────────────────────────────

@router.post("/Claim", status_code=status.HTTP_201_CREATED)
async def submit_claim(
    payload: dict,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN", "DOCTOR"))
):
    """Submit a healthcare claim. Automatically triggers the Payer Adjudication Engine."""
    claim_id = payload.get("id") or f"CLM{uuid.uuid4().hex[:8].upper()}"
    payload["id"] = claim_id
    payload["resourceType"] = "Claim"

    now_iso = datetime.utcnow().isoformat() + "Z"
    payload["meta"] = {"versionId": "1", "lastUpdated": now_iso}

    patient_id = _clean_ref(payload.get("patient"), "Patient")
    provider_id = _clean_ref(payload.get("provider"), "Practitioner")

    # Extract coverage
    insurance_list = payload.get("insurance", [])
    coverage_id = None
    if insurance_list and len(insurance_list) > 0:
        coverage_id = _clean_ref(insurance_list[0].get("coverage"), "Coverage")

    # Extract total
    total_val = 0.0
    total_obj = payload.get("total")
    if isinstance(total_obj, dict):
        total_val = float(total_obj.get("value", 0.0))
    elif isinstance(total_obj, (int, float)):
        total_val = float(total_obj)

    if total_val <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "invalid",
                    "diagnostics": f"Claim total must be greater than zero. Received: {total_val}"
                }]
            }
        )

    # Fetch coverage if referenced
    coverage_dict = None
    if coverage_id:
        cov_res = await db.execute(select(CoverageModel).where(CoverageModel.id == coverage_id))
        cov_record = cov_res.scalars().first()
        if cov_record:
            coverage_dict = cov_record.fhir_json
    elif patient_id:
        # Fallback to patient's active coverage
        cov_res = await db.execute(
            select(CoverageModel)
            .where(CoverageModel.patient_id == patient_id, CoverageModel.status == "active")
        )
        cov_record = cov_res.scalars().first()
        if cov_record:
            coverage_id = cov_record.id
            coverage_dict = cov_record.fhir_json

    # Run Payer Adjudication Engine
    adj_result = adjudicate_claim(payload, coverage_dict, claim_id)

    # Save Claim
    claim_rec = ClaimModel(
        id=claim_id,
        patient_id=patient_id,
        provider_id=provider_id,
        coverage_id=coverage_id,
        status=payload.get("status", "active"),
        use=payload.get("use", "claim"),
        total_amount=total_val,
        fhir_json=payload
    )
    db.add(claim_rec)

    # Save ClaimResponse
    cr_rec = ClaimResponseModel(
        id=adj_result["id"],
        claim_id=claim_id,
        patient_id=patient_id,
        insurer_id=_clean_ref(adj_result["claim_response_fhir"].get("insurer"), "Organization"),
        status="active",
        outcome=adj_result["outcome"],
        disposition=adj_result["disposition"],
        total_submitted=adj_result["total_submitted"],
        total_benefit=adj_result["total_benefit"],
        total_patient_paid=adj_result["total_patient_paid"],
        fhir_json=adj_result["claim_response_fhir"]
    )
    db.add(cr_rec)

    await db.commit()
    await db.refresh(claim_rec)

    response.headers["Location"] = f"/fhir/Claim/{claim_id}"
    return {
        **claim_rec.fhir_json,
        "_adjudication": {
            "claimResponseId": cr_rec.id,
            "outcome": adj_result["outcome"],
            "disposition": adj_result["disposition"],
            "totalBenefit": adj_result["total_benefit"],
            "patientCopay": adj_result["total_patient_paid"]
        }
    }


@router.get("/Claim/{id}")
async def get_claim(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Retrieve a healthcare Claim resource by ID."""
    stmt = select(ClaimModel).where(ClaimModel.id == id)
    result = await db.execute(stmt)
    claim = result.scalars().first()

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "resourceType": "OperationOutcome",
                "issue": [{"severity": "error", "code": "not-found", "diagnostics": f"Claim/{id} not found"}]
            }
        )

    if current_user.role == "PATIENT" and claim.patient_id:
        verify_patient_access(claim.patient_id, current_user)

    return claim.fhir_json


@router.get("/Claim")
async def search_claims(
    patient: Optional[str] = Query(None, alias="patient"),
    status_filter: Optional[str] = Query(None, alias="status"),
    _count: int = Query(50, alias="_count"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Search claims by patient or status."""
    if current_user.role == "PATIENT":
        user_pid = (current_user.patient_id or "").replace("Patient/", "")
        patient = user_pid

    stmt = select(ClaimModel)
    if patient:
        clean_pid = patient.replace("Patient/", "")
        stmt = stmt.where(ClaimModel.patient_id == clean_pid)
    if status_filter:
        stmt = stmt.where(ClaimModel.status == status_filter)

    stmt = stmt.limit(_count)
    result = await db.execute(stmt)
    claims = result.scalars().all()

    entries = [{"fullUrl": f"/fhir/Claim/{c.id}", "resource": c.fhir_json} for c in claims]
    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "searchset",
        "total": len(entries),
        "entry": entries
    }


# ─── ClaimResponse Endpoints ──────────────────────────────────────────────────

@router.get("/ClaimResponse/{id}")
async def get_claim_response(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Retrieve an adjudicated ClaimResponse resource by ID."""
    stmt = select(ClaimResponseModel).where(ClaimResponseModel.id == id)
    result = await db.execute(stmt)
    cr = result.scalars().first()

    if not cr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "resourceType": "OperationOutcome",
                "issue": [{"severity": "error", "code": "not-found", "diagnostics": f"ClaimResponse/{id} not found"}]
            }
        )

    if current_user.role == "PATIENT" and cr.patient_id:
        verify_patient_access(cr.patient_id, current_user)

    return cr.fhir_json


@router.get("/ClaimResponse")
async def search_claim_responses(
    patient: Optional[str] = Query(None, alias="patient"),
    claim: Optional[str] = Query(None, alias="claim"),
    outcome: Optional[str] = Query(None, alias="outcome"),
    _count: int = Query(50, alias="_count"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Search ClaimResponse adjudications by patient, claim ID, or outcome."""
    if current_user.role == "PATIENT":
        user_pid = (current_user.patient_id or "").replace("Patient/", "")
        patient = user_pid

    stmt = select(ClaimResponseModel)
    if patient:
        clean_pid = patient.replace("Patient/", "")
        stmt = stmt.where(ClaimResponseModel.patient_id == clean_pid)
    if claim:
        clean_cid = claim.replace("Claim/", "")
        stmt = stmt.where(ClaimResponseModel.claim_id == clean_cid)
    if outcome:
        stmt = stmt.where(ClaimResponseModel.outcome == outcome)

    stmt = stmt.limit(_count)
    result = await db.execute(stmt)
    records = result.scalars().all()

    entries = [{"fullUrl": f"/fhir/ClaimResponse/{r.id}", "resource": r.fhir_json} for r in records]
    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "searchset",
        "total": len(entries),
        "entry": entries
    }

