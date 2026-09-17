'use client';

import React, { useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import type { FHIRCoverage, FHIRClaim, FHIRClaimResponse, EligibilityResult } from '@/types/fhir';
import { checkEligibility, submitClaim } from '@/lib/api';

interface InsuranceBillingCardProps {
  patientId: string;
  initialCoverages: FHIRCoverage[];
  initialClaims: FHIRClaim[];
  initialClaimResponses: FHIRClaimResponse[];
}

export function InsuranceBillingCard({
  patientId,
  initialCoverages,
  initialClaims,
  initialClaimResponses
}: InsuranceBillingCardProps) {
  const [coverages] = useState<FHIRCoverage[]>(initialCoverages);
  const [claims, setClaims] = useState<FHIRClaim[]>(initialClaims);
  const [claimResponses, setClaimResponses] = useState<FHIRClaimResponse[]>(initialClaimResponses);

  // Eligibility verification state
  const [checkingEligibility, setCheckingEligibility] = useState<string | null>(null);
  const [eligibilityResults, setEligibilityResults] = useState<Record<string, EligibilityResult>>({});
  const [eligibilityError, setEligibilityError] = useState<string | null>(null);

  // Claim submission form state
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [claimAmount, setClaimAmount] = useState('1500');
  const [serviceDesc, setServiceDesc] = useState('Outpatient Follow-Up Consultation');
  const [cptCode, setCptCode] = useState('99213');
  const [submittingClaim, setSubmittingClaim] = useState(false);
  const [submissionMessage, setSubmissionMessage] = useState<string | null>(null);

  const handleVerifyEligibility = async (covId: string) => {
    setCheckingEligibility(covId);
    setEligibilityError(null);
    try {
      const res = await checkEligibility(covId);
      setEligibilityResults((prev) => ({ ...prev, [covId]: res }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Eligibility check failed';
      setEligibilityError(msg);
    } finally {
      setCheckingEligibility(null);
    }
  };

  const handleNewClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingClaim(true);
    setSubmissionMessage(null);
    try {
      const activeCov = coverages.find((c) => c.status === 'active') || coverages[0];
      const claimPayload = {
        resourceType: 'Claim',
        status: 'active',
        type: { coding: [{ system: 'http://terminology.hl7.org/CodeSystem/claim-type', code: 'professional' }] },
        use: 'claim',
        patient: { reference: `Patient/${patientId}` },
        provider: { reference: 'Practitioner/PR101' },
        facility: { reference: 'Organization/ORG101' },
        insurance: activeCov ? [{ sequence: 1, focal: true, coverage: { reference: `Coverage/${activeCov.id}` } }] : [],
        item: [
          {
            sequence: 1,
            productOrService: { coding: [{ system: 'http://www.ama-assn.org/go/cpt', code: cptCode, display: serviceDesc }] },
            unitPrice: { value: parseFloat(claimAmount), currency: 'INR' },
            net: { value: parseFloat(claimAmount), currency: 'INR' }
          }
        ],
        total: { value: parseFloat(claimAmount), currency: 'INR' }
      };

      const res = await submitClaim(claimPayload);
      setClaims((prev) => [res, ...prev]);
      if (res._adjudication) {
        setSubmissionMessage(`Claim ${res.id} auto-adjudicated! Outcome: ${res._adjudication.outcome.toUpperCase()} (Benefit: ₹${res._adjudication.totalBenefit}, Copay: ₹${res._adjudication.patientCopay})`);
      } else {
        setSubmissionMessage(`Claim ${res.id} successfully submitted.`);
      }
      setShowClaimModal(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Claim submission failed';
      setSubmissionMessage(`Error: ${msg}`);
    } finally {
      setSubmittingClaim(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* ── 1. Active Insurance Policies ─────────────────────────────────── */}
      <Card className="border-l-4 border-l-blue-600">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-xl">💳</span>
            <h3 className="text-lg font-semibold text-gray-900">Health Insurance & Coverage</h3>
          </div>
          <span className="text-xs bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full font-medium border border-blue-200">
            FHIR Coverage (R4)
          </span>
        </div>

        {coverages.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No insurance policies on file for this patient.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {coverages.map((cov) => {
              const covId = cov.id || 'N/A';
              const result = eligibilityResults[covId];
              const isChecking = checkingEligibility === covId;

              return (
                <div key={covId} className="border border-gray-200 rounded-lg p-4 bg-gray-50/50 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-gray-900 text-sm">
                        {cov.class?.[0]?.name || cov.type?.text || 'Standard Insurance Plan'}
                      </h4>
                      <p className="text-xs text-gray-500">
                        {cov.payor?.[0]?.display || 'Insurance Provider'}
                      </p>
                    </div>
                    <Badge variant={cov.status === 'active' ? 'green' : 'red'}>
                      {cov.status.toUpperCase()}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-500">Subscriber ID:</span>
                      <p className="font-mono font-medium text-gray-800">{cov.subscriberId || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Valid Period:</span>
                      <p className="font-medium text-gray-800">
                        {cov.period?.start || 'N/A'} to {cov.period?.end || 'N/A'}
                      </p>
                    </div>
                  </div>

                  {/* Real-time Verification Action */}
                  <div className="pt-2 border-t border-gray-200">
                    <button
                      onClick={() => handleVerifyEligibility(covId)}
                      disabled={isChecking}
                      className="w-full text-xs font-medium px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded transition flex items-center justify-center gap-1.5 disabled:opacity-50"
                    >
                      {isChecking ? (
                        <>
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                          Verifying EDI 270/271...
                        </>
                      ) : (
                        <>
                          <span>⚡</span> Verify Real-Time Eligibility
                        </>
                      )}
                    </button>
                  </div>

                  {/* Real-Time Eligibility Result Card */}
                  {result && (
                    <div className={`p-3 rounded text-xs border ${result.eligible ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'}`}>
                      <div className="flex items-center justify-between font-semibold">
                        <span>{result.eligible ? '✓ Verified Eligible' : '✗ Ineligible / Inactive'}</span>
                        <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-white/80 border">
                          {result.status}
                        </span>
                      </div>
                      <p className="mt-1 text-[11px] opacity-90">{result.disposition}</p>
                      {result.eligible && (
                        <div className="mt-2 grid grid-cols-2 gap-1 text-[11px] pt-1.5 border-t border-emerald-200/60">
                          <div>Coinsurance Benefit: <span className="font-semibold">{result.coinsuranceBenefit}%</span></div>
                          <div>Patient Copay: <span className="font-semibold">{result.copayPercent}%</span></div>
                          <div>Deductible Remaining: <span className="font-semibold">₹{result.remainingDeductible?.value || 0}</span></div>
                          <div>Network: <span className="font-semibold">{result.inNetwork ? 'In-Network' : 'Out-of-Network'}</span></div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {eligibilityError && (
          <p className="mt-3 text-xs text-rose-600 bg-rose-50 p-2 rounded border border-rose-200">
            {eligibilityError}
          </p>
        )}
      </Card>

      {/* ── 2. Claims & Adjudication History ─────────────────────────────── */}
      <Card className="border-l-4 border-l-emerald-600">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-xl">📑</span>
            <h3 className="text-lg font-semibold text-gray-900">Healthcare Claims & RCM Adjudications</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full font-medium border border-emerald-200">
              Auto-Adjudication Engine
            </span>
            <button
              onClick={() => setShowClaimModal(true)}
              className="text-xs font-semibold px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded transition shadow-sm"
            >
              + Submit Claim
            </button>
          </div>
        </div>

        {submissionMessage && (
          <div className="mb-4 p-3 rounded text-xs bg-blue-50 border border-blue-200 text-blue-900 font-medium">
            {submissionMessage}
          </div>
        )}

        {claims.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No insurance claims submitted for this patient.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-gray-100 text-gray-600 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Claim ID</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Service Code</th>
                  <th className="py-2.5 px-3 text-right">Submitted</th>
                  <th className="py-2.5 px-3 text-right">Insurer Paid</th>
                  <th className="py-2.5 px-3 text-right">Patient Copay</th>
                  <th className="py-2.5 px-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {claims.map((clm) => {
                  const clmId = clm.id || 'N/A';
                  // Find matching ClaimResponse
                  const resp = claimResponses.find((r) => r.request?.reference?.includes(clmId));
                  const submittedAmt = clm.total?.value || 0;
                  const isComplete = resp?.outcome === 'complete';
                  const isDenied = resp?.outcome === 'error';

                  const benefitAmt = resp?.total?.find((t) => t.category?.coding?.[0]?.code === 'benefit')?.amount?.value ?? (isComplete ? roundTo2(submittedAmt * 0.9) : 0);
                  const copayAmt = resp?.total?.find((t) => t.category?.coding?.[0]?.code === 'copay')?.amount?.value ?? (isComplete ? roundTo2(submittedAmt - benefitAmt) : submittedAmt);

                  const serviceDisplay = clm.item?.[0]?.productOrService?.coding?.[0]?.display || clm.item?.[0]?.productOrService?.coding?.[0]?.code || 'Clinical Service';

                  return (
                    <tr key={clmId} className="hover:bg-gray-50 transition">
                      <td className="py-2.5 px-3 font-mono font-medium text-blue-600">{clmId}</td>
                      <td className="py-2.5 px-3 text-gray-600">{clm.created?.slice(0, 10) || '2026-09-17'}</td>
                      <td className="py-2.5 px-3 text-gray-800 font-medium">{serviceDisplay}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-semibold text-gray-900">₹{submittedAmt.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-semibold text-emerald-600">₹{benefitAmt.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-semibold text-amber-600">₹{copayAmt.toFixed(2)}</td>
                      <td className="py-2.5 px-3 text-center">
                        {isDenied ? (
                          <Badge variant="red">DENIED</Badge>
                        ) : isComplete ? (
                          <Badge variant="green">APPROVED (90%)</Badge>
                        ) : (
                          <Badge variant="blue">SUBMITTED</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ── Modal: Submit Healthcare Claim ───────────────────────────────── */}
      {showClaimModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h4 className="font-bold text-gray-900 text-base">Submit Healthcare Claim (RCM)</h4>
              <button
                onClick={() => setShowClaimModal(false)}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleNewClaim} className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-gray-700 mb-1">Service Description</label>
                <input
                  type="text"
                  value={serviceDesc}
                  onChange={(e) => setServiceDesc(e.target.value)}
                  className="w-full border rounded px-3 py-2 text-gray-900 font-medium"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-gray-700 mb-1">CPT Procedure Code</label>
                  <select
                    value={cptCode}
                    onChange={(e) => setCptCode(e.target.value)}
                    className="w-full border rounded px-2.5 py-2 text-gray-900"
                  >
                    <option value="99213">99213 - Office Visit L3</option>
                    <option value="99214">99214 - Office Visit L4</option>
                    <option value="93000">93000 - Electrocardiogram</option>
                    <option value="80053">80053 - Comprehensive Panel</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-gray-700 mb-1">Claim Amount (INR ₹)</label>
                  <input
                    type="number"
                    step="50"
                    value={claimAmount}
                    onChange={(e) => setClaimAmount(e.target.value)}
                    className="w-full border rounded px-3 py-2 text-gray-900 font-mono"
                    required
                  />
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 p-2.5 rounded text-blue-900 text-[11px] leading-relaxed">
                ℹ️ Submission automatically triggers the Payer Adjudication Engine to check coverage, calculate the 90% insurer reimbursement, and issue a FHIR <span className="font-mono font-semibold">ClaimResponse</span>.
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setShowClaimModal(false)}
                  className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingClaim}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium disabled:opacity-50"
                >
                  {submittingClaim ? 'Adjudicating...' : 'Submit & Adjudicate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function roundTo2(n: number): number {
  return Math.round(n * 100) / 100;
}

