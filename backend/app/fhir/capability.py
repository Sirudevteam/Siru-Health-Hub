from fastapi import APIRouter
from datetime import date

router = APIRouter()

@router.get("/metadata")
async def get_capability_statement():
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": date.today().isoformat(),
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json", "application/fhir+json"],
        "rest": [{
            "mode": "server",
            "resource": [
                {
                    "type": "Patient",
                    "interaction": [
                        {"code": "read"}, {"code": "create"}, {"code": "update"}, {"code": "delete"}, {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "name", "type": "string"},
                        {"name": "family", "type": "string"},
                        {"name": "given", "type": "string"},
                        {"name": "birthdate", "type": "date"},
                        {"name": "gender", "type": "token"}
                    ]
                },
                {
                    "type": "Practitioner",
                    "interaction": [
                        {"code": "read"}, {"code": "create"}, {"code": "update"}, {"code": "delete"}, {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "name", "type": "string"},
                        {"name": "family", "type": "string"},
                        {"name": "given", "type": "string"},
                        {"name": "gender", "type": "token"}
                    ]
                },
                {
                    "type": "Organization",
                    "interaction": [
                        {"code": "read"}, {"code": "create"}, {"code": "update"}, {"code": "delete"}, {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "name", "type": "string"},
                        {"name": "active", "type": "token"}
                    ]
                },
                {
                    "type": "Encounter",
                    "interaction": [
                        {"code": "read"}, {"code": "create"}, {"code": "update"}, {"code": "delete"}, {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "patient", "type": "reference"},
                        {"name": "subject", "type": "reference"},
                        {"name": "practitioner", "type": "reference"},
                        {"name": "status", "type": "token"}
                    ]
                },
                {
                    "type": "Observation",
                    "interaction": [
                        {"code": "read"}, {"code": "create"}, {"code": "update"}, {"code": "delete"}, {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "patient", "type": "reference"},
                        {"name": "subject", "type": "reference"},
                        {"name": "encounter", "type": "reference"},
                        {"name": "category", "type": "token"},
                        {"name": "code", "type": "token"}
                    ]
                },
                {
                    "type": "Condition",
                    "interaction": [
                        {"code": "read"}, {"code": "create"}, {"code": "update"}, {"code": "delete"}, {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "patient", "type": "reference"},
                        {"name": "subject", "type": "reference"},
                        {"name": "encounter", "type": "reference"},
                        {"name": "clinical-status", "type": "token"},
                        {"name": "code", "type": "token"}
                    ]
                },
                {
                    "type": "MedicationRequest",
                    "interaction": [
                        {"code": "read"}, {"code": "create"}, {"code": "update"}, {"code": "delete"}, {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "patient", "type": "reference"},
                        {"name": "subject", "type": "reference"},
                        {"name": "encounter", "type": "reference"},
                        {"name": "status", "type": "token"},
                        {"name": "intent", "type": "token"}
                    ]
                },
                {
                    "type": "Appointment",
                    "interaction": [
                        {"code": "read"}, {"code": "create"}, {"code": "update"}, {"code": "delete"}, {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "patient", "type": "reference"},
                        {"name": "practitioner", "type": "reference"},
                        {"name": "status", "type": "token"}
                    ]
                }
            ]
        }]
    }
