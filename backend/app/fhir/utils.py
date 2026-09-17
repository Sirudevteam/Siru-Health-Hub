from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


def clean_reference_id(ref: Optional[str]) -> Optional[str]:
    """Extract ID from reference like 'Patient/P1001' -> 'P1001' or 'P1001' -> 'P1001'."""
    if not ref:
        return None
    ref_str = str(ref).strip()
    if "/" in ref_str:
        return ref_str.split("/")[-1]
    return ref_str


def error_outcome(status_code: int, code: str, diagnostics: str) -> JSONResponse:
    """Return standard FHIR OperationOutcome response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": code,
                "diagnostics": diagnostics
            }]
        },
        headers={"Content-Type": "application/fhir+json"}
    )


def generate_meta(version_id: str = "1") -> Dict[str, str]:
    return {
        "versionId": version_id,
        "lastUpdated": datetime.utcnow().isoformat() + "Z"
    }


def build_bundle(entries: List[Dict[str, Any]], total: int, self_url: str) -> Dict[str, Any]:
    bundle_entries = []
    for item in entries:
        res_type = item.get("resourceType", "Resource")
        res_id = item.get("id", "")
        bundle_entries.append({
            "fullUrl": f"{self_url}/{res_type}/{res_id}" if not res_id.startswith("http") else res_id,
            "resource": item
        })
    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "searchset",
        "total": total,
        "link": [{"relation": "self", "url": self_url}],
        "entry": bundle_entries
    }

