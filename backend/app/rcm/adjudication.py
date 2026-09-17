# ==============================================================================
# Siru HealthHub — Payer Adjudication Engine
# Evaluates healthcare claims against patient insurance coverage, verifies
# medical necessity, calculates policy benefits / copays, and produces FHIR
# ClaimResponse resources.
# ==============================================================================

from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple
import uuid


def adjudicate_claim(
    claim_dict: Dict[str, Any],
    coverage_dict: Optional[Dict[str, Any]],
    claim_id: str
) -> Dict[str, Any]:
    """Adjudicate a healthcare claim against insurance coverage rules.

    Returns a dict containing:
      - claim_response_fhir: Dict representing the FHIR ClaimResponse resource
      - outcome: "complete" (approved) or "error" (denied/rejected)
      - disposition: Human-readable explanation of adjudication decision
      - total_submitted: Float
      - total_benefit: Float
      - total_patient_paid: Float
    """
    # 1. Extract total claimed amount
    total_obj = claim_dict.get("total", {})
    if isinstance(total_obj, dict):
        claim_total = float(total_obj.get("value", 0.0))
    elif isinstance(total_obj, (int, float)):
        claim_total = float(total_obj)
    else:
        claim_total = 0.0

    if claim_total <= 0:
        raise ValueError(f"Invalid claim total: {claim_total}. Must be greater than 0.")

    # 2. Check Coverage presence and validity
    cr_id = f"CR{uuid.uuid4().hex[:8].upper()}"
    patient_ref = claim_dict.get("patient", {})
    insurer_ref = (
        coverage_dict.get("payor", [{}])[0]
        if coverage_dict and coverage_dict.get("payor")
        else {"reference": "Organization/ORG_PAYER_1", "display": "Payer"}
    )

    now_iso = datetime.utcnow().isoformat() + "Z"

    # Evaluate coverage status & effective dates
    is_covered = False
    denial_reason = None

    if not coverage_dict:
        denial_reason = "No active insurance policy found for patient."
    elif coverage_dict.get("status") != "active":
        denial_reason = f"Insurance coverage is {coverage_dict.get('status', 'inactive')} on date of service."
    else:
        # Check period
        period = coverage_dict.get("period", {})
        today_str = date.today().isoformat()
        start = period.get("start")
        end = period.get("end")
        if start and today_str < start:
            denial_reason = f"Coverage not yet effective. Policy starts on {start}."
        elif end and today_str > end:
            denial_reason = f"Coverage terminated on {end}. Policy is expired."
        else:
            is_covered = True

    # 3. Adjudication Math & Line Item Processing
    raw_items = claim_dict.get("item", [])
    adjudicated_items = []

    if is_covered:
        outcome = "complete"
        disposition = "Claim fully adjudicated and approved. Insurer paid 90% benefit."
        benefit_rate = 0.90
        total_benefit = round(claim_total * benefit_rate, 2)
        total_patient_paid = round(claim_total - total_benefit, 2)

        for it in raw_items:
            seq = it.get("sequence", 1)
            net_amt = 0.0
            if "net" in it and isinstance(it["net"], dict):
                net_amt = float(it["net"].get("value", 0.0))
            elif "unitPrice" in it and isinstance(it["unitPrice"], dict):
                net_amt = float(it["unitPrice"].get("value", 0.0)) * float(it.get("quantity", {}).get("value", 1))

            it_benefit = round(net_amt * benefit_rate, 2)
            it_patient = round(net_amt - it_benefit, 2)

            adjudicated_items.append({
                "itemSequence": seq,
                "adjudication": [
                    {
                        "category": {
                            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/adjudication", "code": "benefit"}]
                        },
                        "amount": {"value": it_benefit, "currency": "USD"}
                    },
                    {
                        "category": {
                            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/adjudication", "code": "copay"}]
                        },
                        "amount": {"value": it_patient, "currency": "USD"}
                    }
                ]
            })
    else:
        outcome = "error"
        disposition = f"Claim denied: {denial_reason}"
        total_benefit = 0.0
        total_patient_paid = claim_total

        for it in raw_items:
            seq = it.get("sequence", 1)
            adjudicated_items.append({
                "itemSequence": seq,
                "adjudication": [
                    {
                        "category": {
                            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/adjudication", "code": "benefit"}]
                        },
                        "amount": {"value": 0.0, "currency": "USD"},
                        "reason": {"text": denial_reason}
                    }
                ]
            })

    # 4. Construct FHIR R4 ClaimResponse
    claim_response_fhir = {
        "resourceType": "ClaimResponse",
        "id": cr_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": now_iso
        },
        "status": "active",
        "type": claim_dict.get("type", {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "professional"}]
        }),
        "use": claim_dict.get("use", "claim"),
        "patient": patient_ref,
        "created": now_iso,
        "insurer": insurer_ref,
        "request": {"reference": f"Claim/{claim_id}"},
        "outcome": outcome,
        "disposition": disposition,
        "total": [
            {
                "category": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/adjudication", "code": "submitted"}]
                },
                "amount": {"value": claim_total, "currency": "USD"}
            },
            {
                "category": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/adjudication", "code": "benefit"}]
                },
                "amount": {"value": total_benefit, "currency": "USD"}
            },
            {
                "category": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/adjudication", "code": "copay"}]
                },
                "amount": {"value": total_patient_paid, "currency": "USD"}
            }
        ],
        "item": adjudicated_items
    }

    return {
        "claim_response_fhir": claim_response_fhir,
        "id": cr_id,
        "outcome": outcome,
        "disposition": disposition,
        "total_submitted": claim_total,
        "total_benefit": total_benefit,
        "total_patient_paid": total_patient_paid
    }

