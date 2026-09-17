# ==============================================================================
# Siru HealthHub — Prometheus Scrape Router & Middleware
# Handles GET /metrics and updates Prometheus gauges and counters in real time.
# ==============================================================================

from fastapi import APIRouter, Response, Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, func
import time
import re

from app.database.session import AsyncSessionLocal
from app.database.models import (
    Patient, Practitioner, Encounter, Observation, Condition,
    MedicationRequest, Appointment, Coverage, Claim, ClaimResponse
)
from app.observability.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    FHIR_RESOURCES_COUNT,
    generate_latest,
    CONTENT_TYPE_LATEST
)

router = APIRouter(tags=["Observability"])


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Measures latency and increments HTTP request counters for Prometheus."""
    async def dispatch(self, request: Request, call_next):
        # Normalize endpoint path to prevent high metric cardinality
        path = request.url.path
        normalized_endpoint = path
        # Normalize UUIDs or IDs like /fhir/Patient/P1001 -> /fhir/Patient/{id}
        normalized_endpoint = re.sub(r"/(P\w+|PR\w+|ORG\w+|ENC\w+|OBS\w+|COND\w+|MED\w+|APT\w+|COV\w+|CLM\w+|CR\w+|[0-9a-fA-F\-]{8,})", "/{id}", normalized_endpoint)

        start_time = time.time()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.time() - start_time
            if not path.startswith("/metrics"):
                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method=request.method,
                    endpoint=normalized_endpoint
                ).observe(duration)
                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    endpoint=normalized_endpoint,
                    status_code=str(status_code)
                ).inc()


@router.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus OpenMetrics scrape endpoint."""
    # Update resource gauges from DB
    try:
        async with AsyncSessionLocal() as session:
            counts = {
                "Patient": (await session.execute(select(func.count(Patient.id)))).scalar() or 0,
                "Practitioner": (await session.execute(select(func.count(Practitioner.id)))).scalar() or 0,
                "Encounter": (await session.execute(select(func.count(Encounter.id)))).scalar() or 0,
                "Observation": (await session.execute(select(func.count(Observation.id)))).scalar() or 0,
                "Condition": (await session.execute(select(func.count(Condition.id)))).scalar() or 0,
                "MedicationRequest": (await session.execute(select(func.count(MedicationRequest.id)))).scalar() or 0,
                "Appointment": (await session.execute(select(func.count(Appointment.id)))).scalar() or 0,
                "Coverage": (await session.execute(select(func.count(Coverage.id)))).scalar() or 0,
                "Claim": (await session.execute(select(func.count(Claim.id)))).scalar() or 0,
                "ClaimResponse": (await session.execute(select(func.count(ClaimResponse.id)))).scalar() or 0,
            }
            for res_type, cnt in counts.items():
                FHIR_RESOURCES_COUNT.labels(resource_type=res_type).set(cnt)
    except Exception:
        pass

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

