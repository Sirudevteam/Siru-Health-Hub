from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database.session import engine, Base
from app.database.seed import seed_database
from app.fhir.patient import router as patient_router
from app.fhir.practitioner import router as practitioner_router
from app.fhir.organization import router as organization_router
from app.fhir.encounter import router as encounter_router
from app.fhir.observation import router as observation_router
from app.fhir.condition import router as condition_router
from app.fhir.medication_request import router as medication_request_router
from app.fhir.appointment import router as appointment_router
from app.fhir.coverage import router as coverage_router
from app.fhir.claim import router as claim_router
from app.fhir.capability import router as capability_router
from app.audit.middleware import AuditMiddleware
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.observability.router import router as metrics_router, ObservabilityMiddleware
from app.analytics.router import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed hospital simulation records
    try:
        await seed_database()
    except Exception as e:
        print(f"Warning: Seed database failed: {e}")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)
app.add_middleware(ObservabilityMiddleware)

# Auth and RBAC
app.include_router(auth_router)

# Observability & Metrics
app.include_router(metrics_router)

# Audit & Compliance Logs
app.include_router(audit_router)

# RCM & Clinical Analytics
app.include_router(analytics_router)

# FHIR resource routers
app.include_router(capability_router, prefix="/fhir", tags=["FHIR Metadata"])
app.include_router(patient_router, prefix="/fhir", tags=["Patient"])
app.include_router(practitioner_router, prefix="/fhir", tags=["Practitioner"])
app.include_router(organization_router, prefix="/fhir", tags=["Organization"])
app.include_router(encounter_router, prefix="/fhir", tags=["Encounter"])
app.include_router(observation_router, prefix="/fhir", tags=["Observation"])
app.include_router(condition_router, prefix="/fhir", tags=["Condition"])
app.include_router(medication_request_router, prefix="/fhir", tags=["MedicationRequest"])
app.include_router(appointment_router, prefix="/fhir", tags=["Appointment"])
app.include_router(coverage_router, prefix="/fhir", tags=["Coverage"])
app.include_router(claim_router, prefix="/fhir", tags=["Claim & Adjudication"])

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}

