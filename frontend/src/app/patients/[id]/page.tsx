import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  getPatient,
  getPatientEncounters,
  getPatientObservations,
  getPatientConditions,
  getPatientMedications,
  getPatientAppointments,
  getPatientCoverages,
  getPatientClaims,
  getPatientClaimResponses,
} from '@/lib/api';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { InsuranceBillingCard } from '@/components/patient/InsuranceBillingCard';
import type {
  FHIRPatient,
  HumanName,
  ContactPoint,
  Address,
  FHIREncounter,
  FHIRObservation,
  FHIRCondition,
  FHIRMedicationRequest,
  FHIRAppointment,
  FHIRCoverage,
  FHIRClaim,
  FHIRClaimResponse,
} from '@/types/fhir';


// ─── Helpers ────────────────────────────────────────────────────────────────

function getDisplayName(patient: FHIRPatient): string {
  const n = patient.name?.[0];
  if (!n) return 'Unknown Patient';
  if (n.text) return n.text;
  return [n.given?.join(' '), n.family].filter(Boolean).join(' ') || 'Unknown Patient';
}

function genderVariant(g?: string): 'blue' | 'green' | 'yellow' | 'gray' {
  if (g === 'male')   return 'blue';
  if (g === 'female') return 'green';
  if (g === 'other')  return 'yellow';
  return 'gray';
}

function formatAddress(addr: Address): string {
  return [
    addr.line?.join(', '),
    addr.city,
    addr.state,
    addr.postalCode,
    addr.country,
  ].filter(Boolean).join(', ');
}

// ─── Page ───────────────────────────────────────────────────────────────────

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function PatientDetailPage({ params }: PageProps) {
  const { id } = await params;
  let patient: FHIRPatient;
  let encounters: FHIREncounter[] = [];
  let observations: FHIRObservation[] = [];
  let conditions: FHIRCondition[] = [];
  let medications: FHIRMedicationRequest[] = [];
  let appointments: FHIRAppointment[] = [];
  let coverages: FHIRCoverage[] = [];
  let claims: FHIRClaim[] = [];
  let claimResponses: FHIRClaimResponse[] = [];

  try {
    patient = await getPatient(id);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '';
    if (msg.includes('404') || msg.toLowerCase().includes('not found')) {
      notFound();
    }
    return (
      <div className="max-w-5xl mx-auto px-6 py-8">
        <Card className="border-red-200 bg-red-50">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="font-medium text-red-800">Error loading patient</p>
              <p className="text-sm text-red-600 mt-0.5">{msg || 'An unexpected error occurred.'}</p>
            </div>
          </div>
          <div className="mt-4">
            <Link href="/patients" className="btn-secondary text-sm">← Back to Patients</Link>
          </div>
        </Card>
      </div>
    );
  }

  // Fetch clinical relationship resources in parallel
  try {
    const [encRes, obsRes, condRes, medRes, aptRes, covRes, clmRes, crRes] = await Promise.all([
      getPatientEncounters(id),
      getPatientObservations(id),
      getPatientConditions(id),
      getPatientMedications(id),
      getPatientAppointments(id),
      getPatientCoverages(id),
      getPatientClaims(id),
      getPatientClaimResponses(id),
    ]);
    encounters = (encRes.entry || []).map((e: any) => e.resource);
    observations = (obsRes.entry || []).map((e: any) => e.resource);
    conditions = (condRes.entry || []).map((e: any) => e.resource);
    medications = (medRes.entry || []).map((e: any) => e.resource);
    appointments = (aptRes.entry || []).map((e: any) => e.resource);
    coverages = (covRes.entry || []).map((e: any) => e.resource);
    claims = (clmRes.entry || []).map((e: any) => e.resource);
    claimResponses = (crRes.entry || []).map((e: any) => e.resource);
  } catch (err) {
    console.error('Error fetching clinical resources for patient', err);
  }

  const displayName = getDisplayName(patient);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">

      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/" className="hover:text-emerald-600 transition-colors">Home</Link>
        <span>›</span>
        <Link href="/patients" className="hover:text-emerald-600 transition-colors">Patients</Link>
        <span>›</span>
        <span className="text-gray-900 font-medium truncate max-w-xs">{displayName}</span>
      </nav>

      {/* Patient header */}
      <Card className="bg-gradient-to-r from-emerald-50 via-teal-50 to-cyan-50 border-emerald-200">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-shrink-0 w-16 h-16 rounded-full bg-emerald-600 flex items-center justify-center text-white text-2xl font-bold shadow-sm">
            {displayName.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-gray-900">{displayName}</h1>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <Badge variant={genderVariant(patient.gender)}>
                {patient.gender ? patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1) : 'Unknown'}
              </Badge>
              <Badge variant={patient.active !== false ? 'green' : 'gray'}>
                {patient.active !== false ? 'Active Patient' : 'Inactive'}
              </Badge>
              {patient.birthDate && (
                <span className="text-sm text-gray-600">DOB: {patient.birthDate}</span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-1 font-mono">FHIR ID: {patient.id}</p>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <Link href="/patients" className="btn-secondary text-sm">← Back to List</Link>
          </div>
        </div>
      </Card>

      {/* ─── Clinical Summary Section (Phase 2) ───────────────────────────── */}
      <div className="border-t border-gray-200 pt-2">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
          Clinical Summary & EHR Records
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Vitals / Observations */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <span className="text-rose-500">❤️</span>
                Vitals & Observations ({observations.length})
              </h3>
            </div>
            {observations.length > 0 ? (
              <div className="space-y-2.5">
                {observations.map((obs) => {
                  const val = obs.valueString || (obs.valueQuantity ? `${obs.valueQuantity.value} ${obs.valueQuantity.unit || ''}` : 'Recorded');
                  return (
                    <div key={obs.id} className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900 text-sm">{obs.code?.text || 'Observation'}</p>
                        <p className="text-xs text-gray-500">
                          {obs.effectiveDateTime ? new Date(obs.effectiveDateTime).toLocaleDateString() : 'Recent'}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="inline-block font-mono font-bold text-sm text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded">
                          {val}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic py-2">No vitals or observations recorded yet.</p>
            )}
          </Card>

          {/* Active Diagnoses / Conditions */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <span className="text-amber-500">🩺</span>
                Diagnoses & Conditions ({conditions.length})
              </h3>
            </div>
            {conditions.length > 0 ? (
              <div className="space-y-2.5">
                {conditions.map((cond) => {
                  const icd = cond.code?.coding?.[0]?.code;
                  return (
                    <div key={cond.id} className="p-3 bg-amber-50/50 rounded-lg border border-amber-100 flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900 text-sm">{cond.code?.text || 'Diagnosis'}</p>
                        {icd && <p className="text-xs text-amber-700 font-mono">ICD-10: {icd}</p>}
                      </div>
                      <div>
                        <Badge variant="yellow">Active</Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic py-2">No active conditions reported.</p>
            )}
          </Card>

          {/* Active Medications */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <span className="text-blue-500">💊</span>
                Prescriptions & Medications ({medications.length})
              </h3>
            </div>
            {medications.length > 0 ? (
              <div className="space-y-2.5">
                {medications.map((med) => {
                  const dosage = med.dosageInstruction?.[0]?.text;
                  return (
                    <div key={med.id} className="p-3 bg-blue-50/40 rounded-lg border border-blue-100 space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-gray-900 text-sm">{med.medicationCodeableConcept?.text || 'Medication'}</p>
                        <Badge variant="blue">{med.status || 'Active'}</Badge>
                      </div>
                      {dosage && <p className="text-xs text-gray-600">{dosage}</p>}
                      {med.requester?.display && (
                        <p className="text-xs text-gray-400">Prescribed by {med.requester.display}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic py-2">No active prescriptions.</p>
            )}
          </Card>

          {/* Hospital Encounters & Appointments */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
                <span className="text-indigo-500">🏥</span>
                Encounters & Consultations ({encounters.length})
              </h3>
            </div>
            {encounters.length > 0 ? (
              <div className="space-y-2.5">
                {encounters.map((enc) => {
                  const reason = enc.reasonCode?.[0]?.text || 'Consultation';
                  const doc = enc.participant?.[0]?.individual?.display || 'Staff Physician';
                  return (
                    <div key={enc.id} className="p-3 bg-indigo-50/30 rounded-lg border border-indigo-100 flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900 text-sm">{reason}</p>
                        <p className="text-xs text-gray-500">{doc} • Class: {enc.class?.code || 'AMB'}</p>
                      </div>
                      <div>
                        <Badge variant="green">{enc.status || 'Finished'}</Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic py-2">No recorded encounters.</p>
            )}

            {/* Upcoming Appointments subsection */}
            {appointments.length > 0 && (
              <div className="mt-4 pt-3 border-t border-gray-100">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Upcoming Appointment</p>
                {appointments.map((apt) => (
                  <div key={apt.id} className="p-2.5 bg-emerald-50 rounded border border-emerald-100 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-emerald-900">{apt.description || 'Consultation'}</p>
                      <p className="text-xs text-emerald-700">
                        {apt.start ? new Date(apt.start).toLocaleString() : 'Scheduled'}
                      </p>
                    </div>
                    <Badge variant="green">{apt.status || 'Booked'}</Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>

        </div>
      </div>

      {/* ─── Insurance, Eligibility & Claims RCM (Phase 4) ──────────────── */}
      <InsuranceBillingCard
        patientId={id}
        initialCoverages={coverages}
        initialClaims={claims}
        initialClaimResponses={claimResponses}
      />

      {/* ─── Demographics Grid ───────────────────────────────────────────── */}
      <div className="border-t border-gray-200 pt-2">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Demographics & Contact Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Basic Info */}
          <Card>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Profile Data</h3>
            <dl className="space-y-2.5 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Patient ID</dt>
                <dd className="font-mono text-gray-800 text-xs">{patient.id ?? '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Gender</dt>
                <dd className="text-gray-800 capitalize">{patient.gender ?? '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Birth Date</dt>
                <dd className="text-gray-800">{patient.birthDate ?? '—'}</dd>
              </div>
              {patient.meta?.versionId && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">FHIR Meta Version</dt>
                  <dd className="font-mono text-gray-800 text-xs">v{patient.meta.versionId}</dd>
                </div>
              )}
            </dl>
          </Card>

          {/* Names */}
          <Card>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Name Details</h3>
            {patient.name && patient.name.length > 0 ? (
              <div className="space-y-2">
                {patient.name.map((n: HumanName, i: number) => (
                  <div key={i} className="text-sm bg-gray-50 rounded p-2.5 space-y-1">
                    {n.family && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Family</span>
                        <span className="text-gray-800 font-medium">{n.family}</span>
                      </div>
                    )}
                    {n.given && n.given.length > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Given</span>
                        <span className="text-gray-800 font-medium">{n.given.join(', ')}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">No name records</p>
            )}
          </Card>

        </div>
      </div>

      {/* Raw FHIR JSON */}
      <Card>
        <details className="group">
          <summary className="cursor-pointer flex items-center justify-between text-base font-semibold text-gray-900 list-none">
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              Raw FHIR Resource JSON
            </span>
            <svg className="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </summary>
          <div className="mt-4">
            <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 text-xs overflow-x-auto leading-relaxed">
              {JSON.stringify(patient, null, 2)}
            </pre>
          </div>
        </details>
      </Card>
    </div>
  );
}
