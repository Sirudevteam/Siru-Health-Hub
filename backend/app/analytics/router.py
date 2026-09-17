# ==============================================================================
# Siru HealthHub — Analytics & RCM Executive Intelligence Router
# Aggregates financial billing metrics, clinical distributions, and operational
# security counters for hospital executives and revenue cycle managers.
# ==============================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database.session import get_db
from app.database.models import (
    Patient, Encounter, Observation, Condition, MedicationRequest,
    Coverage, Claim, ClaimResponse, AuditLog
)

router = APIRouter(prefix="/analytics", tags=["Analytics & RCM"])


@router.get("/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    """Retrieve combined financial, clinical, and compliance analytics KPIs."""
    # ── 1. Financial & Claims RCM KPIs ──────────────────────────────────────
    total_claims = (await db.execute(select(func.count(Claim.id)))).scalar() or 0
    total_billed = (await db.execute(select(func.sum(Claim.total_amount)))).scalar() or 0.0

    total_responses = (await db.execute(select(func.count(ClaimResponse.id)))).scalar() or 0
    total_benefit = (await db.execute(select(func.sum(ClaimResponse.total_benefit)))).scalar() or 0.0
    total_copay = (await db.execute(select(func.sum(ClaimResponse.total_patient_paid)))).scalar() or 0.0

    approved_claims = (await db.execute(
        select(func.count(ClaimResponse.id)).where(ClaimResponse.outcome == "complete")
    )).scalar() or 0
    denied_claims = (await db.execute(
        select(func.count(ClaimResponse.id)).where(ClaimResponse.outcome == "error")
    )).scalar() or 0

    clean_claim_rate = round((approved_claims / total_responses * 100), 1) if total_responses > 0 else 100.0
    denial_rate = round((denied_claims / total_responses * 100), 1) if total_responses > 0 else 0.0

    # ── 2. Clinical Population Health KPIs ──────────────────────────────────
    total_patients = (await db.execute(select(func.count(Patient.id)))).scalar() or 0
    total_encounters = (await db.execute(select(func.count(Encounter.id)))).scalar() or 0
    total_observations = (await db.execute(select(func.count(Observation.id)))).scalar() or 0
    total_conditions = (await db.execute(select(func.count(Condition.id)))).scalar() or 0
    total_medications = (await db.execute(select(func.count(MedicationRequest.id)))).scalar() or 0
    total_coverages = (await db.execute(select(func.count(Coverage.id)))).scalar() or 0

    # Top Diagnoses
    top_conditions_res = await db.execute(
        select(Condition.code, func.count(Condition.id))
        .where(Condition.code.isnot(None))
        .group_by(Condition.code)
        .order_by(desc(func.count(Condition.id)))
        .limit(5)
    )
    top_conditions = [{"code": row[0], "count": row[1]} for row in top_conditions_res.all()]

    # ── 3. Compliance & Security Incident Counters ───────────────────────────
    total_audit_logs = (await db.execute(select(func.count(AuditLog.id)))).scalar() or 0
    unauthorized_401 = (await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.status_code == 401)
    )).scalar() or 0
    forbidden_403 = (await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.status_code == 403)
    )).scalar() or 0

    return {
        "financial": {
            "totalClaimsCount": total_claims,
            "totalBilledAmount": round(float(total_billed), 2),
            "totalInsurerBenefit": round(float(total_benefit), 2),
            "totalPatientCopay": round(float(total_copay), 2),
            "approvedCount": approved_claims,
            "deniedCount": denied_claims,
            "cleanClaimRatePercent": clean_claim_rate,
            "denialRatePercent": denial_rate
        },
        "clinical": {
            "totalPatients": total_patients,
            "totalEncounters": total_encounters,
            "totalObservations": total_observations,
            "totalConditions": total_conditions,
            "totalMedications": total_medications,
            "totalCoverages": total_coverages,
            "topConditions": top_conditions
        },
        "security": {
            "totalAuditEvents": total_audit_logs,
            "unauthorized401Count": unauthorized_401,
            "forbidden403Count": forbidden_403,
            "systemStatus": "Operational"
        }
    }

