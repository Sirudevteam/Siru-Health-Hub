'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { getApiBase } from '@/lib/api';

interface AnalyticsData {
  financial: {
    totalClaimsCount: number;
    totalBilledAmount: number;
    totalInsurerBenefit: number;
    totalPatientCopay: number;
    approvedCount: number;
    deniedCount: number;
    cleanClaimRatePercent: number;
    denialRatePercent: number;
  };
  clinical: {
    totalPatients: number;
    totalEncounters: number;
    totalObservations: number;
    totalConditions: number;
    totalMedications: number;
    totalCoverages: number;
    topConditions: Array<{ code: string; count: number }>;
  };
  security: {
    totalAuditEvents: number;
    unauthorized401Count: number;
    forbidden403Count: number;
    systemStatus: string;
  };
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const base = getApiBase();
      const res = await fetch(`${base}/analytics/summary`);
      if (!res.ok) throw new Error('Failed to fetch analytics summary');
      const json = await res.json();
      setData(json);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error loading analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <nav className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <Link href="/" className="hover:text-emerald-600 transition">Home</Link>
            <span>›</span>
            <span className="text-gray-900 font-medium">Executive Analytics</span>
          </nav>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <span>📈</span> Executive RCM & Clinical Intelligence
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time revenue cycle performance, clinical population census, and system health metrics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="/metrics"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition border"
          >
            📊 Prometheus /metrics
          </a>
          <button
            onClick={fetchAnalytics}
            className="px-3 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded transition"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs">
          {error}
        </div>
      )}

      {loading && !data ? (
        <div className="p-12 text-center text-gray-500 text-sm">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-3"></div>
          Aggregating enterprise healthcare metrics...
        </div>
      ) : data ? (
        <div className="space-y-8">
          {/* ── 1. Financial RCM Metrics ─────────────────────────────────── */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <span>💰</span> Revenue Cycle Management (RCM) Performance
              </h2>
              <span className="text-xs bg-emerald-50 text-emerald-700 font-medium px-2.5 py-0.5 rounded-full border border-emerald-200">
                Live Claims Adjudication
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="border-l-4 border-l-blue-600">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Claims Value</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  ₹{data.financial.totalBilledAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">{data.financial.totalClaimsCount} claims submitted</p>
              </Card>

              <Card className="border-l-4 border-l-emerald-600">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Insurer Reimbursement</p>
                <p className="text-2xl font-bold text-emerald-600 mt-1">
                  ₹{data.financial.totalInsurerBenefit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-emerald-700 font-medium mt-0.5">Paid by Payer policies (90%)</p>
              </Card>

              <Card className="border-l-4 border-l-amber-600">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Patient Copay Balance</p>
                <p className="text-2xl font-bold text-amber-600 mt-1">
                  ₹{data.financial.totalPatientCopay.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">Coinsurance & Deductibles</p>
              </Card>

              <Card className="border-l-4 border-l-purple-600">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Clean Claim Rate</p>
                <p className="text-2xl font-bold text-purple-600 mt-1">
                  {data.financial.cleanClaimRatePercent}%
                </p>
                <p className="text-xs text-gray-400 mt-0.5">{data.financial.denialRatePercent}% denial rate</p>
              </Card>
            </div>
          </div>

          {/* ── 2. Clinical Population Health ─────────────────────────────── */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <span>🏥</span> Clinical Population Health & Volume
              </h2>
              <span className="text-xs bg-blue-50 text-blue-700 font-medium px-2.5 py-0.5 rounded-full border border-blue-200">
                FHIR R4 Database
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <Card className="text-center p-4">
                <p className="text-xs text-gray-500 font-medium">Patients</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{data.clinical.totalPatients}</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-xs text-gray-500 font-medium">Encounters</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{data.clinical.totalEncounters}</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-xs text-gray-500 font-medium">Observations</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{data.clinical.totalObservations}</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-xs text-gray-500 font-medium">Diagnoses</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{data.clinical.totalConditions}</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-xs text-gray-500 font-medium">Prescriptions</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{data.clinical.totalMedications}</p>
              </Card>
              <Card className="text-center p-4">
                <p className="text-xs text-gray-500 font-medium">Coverages</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{data.clinical.totalCoverages}</p>
              </Card>
            </div>
          </div>

          {/* ── 3. Visual Distributions & Security Overview ────────────────── */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Top Diagnoses */}
            <Card>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center justify-between">
                <span>Top Clinical Diagnoses (ICD-10)</span>
                <span className="text-xs text-gray-400 font-normal">Active Patient Conditions</span>
              </h3>
              {data.clinical.topConditions.length === 0 ? (
                <p className="text-xs text-gray-400 italic">No diagnoses recorded.</p>
              ) : (
                <div className="space-y-3">
                  {data.clinical.topConditions.map((cond, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="font-medium text-gray-800">{cond.code}</span>
                        <span className="font-mono text-gray-500">{cond.count} patient{cond.count > 1 ? 's' : ''}</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-emerald-600 h-2 rounded-full"
                          style={{ width: `${Math.min(100, (cond.count / Math.max(1, data.clinical.totalConditions)) * 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Claims Adjudication Distribution */}
            <Card>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center justify-between">
                <span>Claims Adjudication Outcome Ratio</span>
                <span className="text-xs text-gray-400 font-normal">Payer Decision Engine</span>
              </h3>

              <div className="space-y-4 pt-2">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                    <span className="text-gray-700 font-medium">Approved Claims</span>
                  </div>
                  <span className="font-mono font-bold text-emerald-600">{data.financial.approvedCount}</span>
                </div>

                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                    <span className="text-gray-700 font-medium">Denied Claims (Expired Policy)</span>
                  </div>
                  <span className="font-mono font-bold text-rose-600">{data.financial.deniedCount}</span>
                </div>

                {/* Ratio Bar */}
                <div className="w-full h-4 bg-gray-100 rounded-full overflow-hidden flex">
                  <div
                    className="bg-emerald-500 h-full"
                    style={{ width: `${data.financial.cleanClaimRatePercent}%` }}
                    title={`Approved: ${data.financial.cleanClaimRatePercent}%`}
                  ></div>
                  <div
                    className="bg-rose-500 h-full"
                    style={{ width: `${data.financial.denialRatePercent}%` }}
                    title={`Denied: ${data.financial.denialRatePercent}%`}
                  ></div>
                </div>

                <div className="pt-2 border-t text-xs text-gray-500 flex justify-between">
                  <span>HIPAA Audit Events: <strong className="text-gray-800">{data.security.totalAuditEvents}</strong></span>
                  <span>403 Blocks: <strong className="text-rose-600">{data.security.forbidden403Count}</strong></span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
}

