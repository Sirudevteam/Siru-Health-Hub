# ==============================================================================
# Siru HealthHub — HIPAA Audit Log API Router
# Provides queryable access to security and data access audit trails for
# compliance monitoring, incident analysis, and legal audit readiness.
# ==============================================================================

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional

from app.database.session import get_db
from app.database.models import AuditLog as AuditLogModel, User as UserModel
from app.auth.dependencies import require_role

router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


@router.get("/logs")
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user username"),
    action: Optional[str] = Query(None, description="CREATE, READ, UPDATE, DELETE, SEARCH"),
    resource_type: Optional[str] = Query(None, description="Patient, Encounter, Claim, etc."),
    result: Optional[str] = Query(None, description="SUCCESS or FAILURE"),
    status_code: Optional[int] = Query(None, description="HTTP status code"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    """Retrieve paginated audit logs with multi-parameter filtering. Strictly restricted to ADMIN."""
    query = select(AuditLogModel)

    if user_id:
        query = query.where(AuditLogModel.user_id == user_id)
    if action:
        query = query.where(AuditLogModel.action == action.upper())
    if resource_type:
        query = query.where(AuditLogModel.resource_type == resource_type)
    if result:
        query = query.where(AuditLogModel.result == result.upper())
    if status_code is not None:
        query = query.where(AuditLogModel.status_code == status_code)

    # Total count matching filters
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_query)).scalar() or 0

    # Paginated results ordered by timestamp descending
    query = query.order_by(desc(AuditLogModel.timestamp)).offset(offset).limit(limit)
    res = await db.execute(query)
    records = res.scalars().all()

    formatted_logs = [
        {
            "id": r.id,
            "user_id": r.user_id or "Anonymous / Unauthenticated",
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "result": r.result,
            "ip_address": r.ip_address or "127.0.0.1",
            "http_method": r.http_method,
            "path": r.path,
            "status_code": r.status_code
        }
        for r in records
    ]

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "logs": formatted_logs
    }


@router.get("/stats")
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN"))
):
    """Retrieve high-level compliance and security incident summary metrics."""
    total_events = (await db.execute(select(func.count(AuditLogModel.id)))).scalar() or 0
    success_count = (await db.execute(select(func.count(AuditLogModel.id)).where(AuditLogModel.result == "SUCCESS"))).scalar() or 0
    failure_count = (await db.execute(select(func.count(AuditLogModel.id)).where(AuditLogModel.result == "FAILURE"))).scalar() or 0

    # Security alerts: 401 Unauthorized & 403 Forbidden incidents
    unauthorized_401 = (await db.execute(select(func.count(AuditLogModel.id)).where(AuditLogModel.status_code == 401))).scalar() or 0
    forbidden_403 = (await db.execute(select(func.count(AuditLogModel.id)).where(AuditLogModel.status_code == 403))).scalar() or 0

    # Action distribution
    action_counts_res = await db.execute(
        select(AuditLogModel.action, func.count(AuditLogModel.id))
        .group_by(AuditLogModel.action)
        .order_by(desc(func.count(AuditLogModel.id)))
        .limit(10)
    )
    action_counts = {row[0]: row[1] for row in action_counts_res.all()}

    return {
        "total_events": total_events,
        "success_count": success_count,
        "failure_count": failure_count,
        "unauthorized_401_count": unauthorized_401,
        "forbidden_403_count": forbidden_403,
        "actions_distribution": action_counts
    }

