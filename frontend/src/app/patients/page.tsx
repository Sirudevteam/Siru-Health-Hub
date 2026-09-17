import Link from 'next/link';
import { getPatients } from '@/lib/api';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import type { FHIRBundle, FHIRPatient, HumanName } from '@/types/fhir';

// ─── Helpers ───────────────────────────────────────────────────────────────

function formatName(name?: HumanName[]): string {
  if (!name || name.length === 0) return 'Unknown';
  const n = name[0];
  if (n.text) return n.text;
  const given = n.given?.join(' ') ?? '';
  const family = n.family ?? '';
  return [given, family].filter(Boolean).join(' ') || 'Unknown';
}

function formatGender(gender?: string): { label: string; variant: 'blue' | 'green' | 'yellow' | 'gray' } {
  switch (gender) {
    case 'male':    return { label: 'Male',    variant: 'blue' };
    case 'female':  return { label: 'Female',  variant: 'green' };
    case 'other':   return { label: 'Other',   variant: 'yellow' };
    default:        return { label: 'Unknown', variant: 'gray' };
  }
}

const PAGE_SIZE = 20;

// ─── Page ──────────────────────────────────────────────────────────────────

interface SearchParamsShape {
  name?: string;
  gender?: string;
  birthdate?: string;
  _offset?: string;
}

interface PageProps {
  searchParams?: Promise<SearchParamsShape>;
}

export default async function PatientsPage({ searchParams }: PageProps) {
  const sp: SearchParamsShape = (await searchParams) ?? {};
  const offset = parseInt(sp._offset ?? '0', 10);
  const params: Record<string, string> = {
    _count: PAGE_SIZE.toString(),
    _offset: offset.toString(),
  };
  if (sp.name)      params['name']      = sp.name;
  if (sp.gender)    params['gender']    = sp.gender;
  if (sp.birthdate) params['birthdate'] = sp.birthdate;

  let bundle: FHIRBundle | null = null;
  let error: string | null = null;

  try {
    bundle = await getPatients(params);
  } catch (e: unknown) {
    error = e instanceof Error ? e.message : 'Failed to load patients';
  }

  const patients: FHIRPatient[] = bundle?.entry?.map((e) => e.resource) ?? [];
  const total = bundle?.total ?? 0;
  const hasPrev = offset > 0;
  const hasNext = offset + PAGE_SIZE < total;

  // Build search param URL helpers
  const buildUrl = (overrides: Record<string, string | undefined>) => {
    const base: Record<string, string> = {};
    if (sp.name)      base.name      = sp.name;
    if (sp.gender)    base.gender    = sp.gender;
    if (sp.birthdate) base.birthdate = sp.birthdate;
    const merged = { ...base, ...overrides };
    const clean = Object.fromEntries(
      Object.entries(merged).filter(([, v]) => v !== undefined && v !== '') as [string, string][]
    );
    const qs = new URLSearchParams(clean).toString();
    return `/patients${qs ? '?' + qs : ''}`;
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
          <p className="text-sm text-gray-500 mt-1">
            {total > 0 ? `${total} patient${total !== 1 ? 's' : ''} registered` : 'No patients found'}
          </p>
        </div>
        <Link href="/patients/new" className="btn-primary self-start sm:self-auto">
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Register Patient
        </Link>
      </div>

      {/* Search / Filter bar */}
      <Card className="p-4">
        <form method="GET" action="/patients" className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[160px]">
            <label className="form-label">Search by Name</label>
            <input
              name="name"
              type="text"
              placeholder="e.g. Arun Kumar"
              defaultValue={sp.name ?? ''}
              className="form-input"
            />
          </div>
          <div className="min-w-[140px]">
            <label className="form-label">Gender</label>
            <select name="gender" defaultValue={sp.gender ?? ''} className="form-input">
              <option value="">All genders</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="form-label">Date of Birth</label>
            <input
              name="birthdate"
              type="date"
              defaultValue={sp.birthdate ?? ''}
              className="form-input"
            />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">Search</button>
            <Link href="/patients" className="btn-secondary">Clear</Link>
          </div>
        </form>
      </Card>

      {/* Error state */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="font-medium text-red-800">Failed to load patients</p>
              <p className="text-sm text-red-600 mt-0.5">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Empty state */}
      {!error && patients.length === 0 && (
        <Card className="text-center py-16">
          <svg className="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">No patients found</h3>
          <p className="text-gray-500 mb-6">
            {Object.values(searchParams ?? {}).some(Boolean)
              ? 'No patients match your search criteria. Try adjusting your filters.'
              : 'Your patient registry is empty. Get started by registering a new patient.'}
          </p>
          <Link href="/patients/new" className="btn-primary">Register First Patient</Link>
        </Card>
      )}

      {/* Table */}
      {!error && patients.length > 0 && (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 text-xs uppercase tracking-wide">ID</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 text-xs uppercase tracking-wide">Name</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 text-xs uppercase tracking-wide">Gender</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 text-xs uppercase tracking-wide">Date of Birth</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 text-xs uppercase tracking-wide">Status</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600 text-xs uppercase tracking-wide">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {patients.map((patient) => {
                  const g = formatGender(patient.gender);
                  return (
                    <tr key={patient.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-gray-500 max-w-[120px] truncate">
                        {patient.id ?? '—'}
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {formatName(patient.name)}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={g.variant}>{g.label}</Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {patient.birthDate ?? '—'}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={patient.active !== false ? 'green' : 'gray'}>
                          {patient.active !== false ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/patients/${patient.id}`}
                          className="inline-flex items-center gap-1 text-emerald-600 hover:text-emerald-800 font-medium text-sm transition-colors"
                        >
                          View
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                          </svg>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-3">
            <span className="text-sm text-gray-600">
              Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total} patients
            </span>
            <div className="flex items-center gap-2">
              {hasPrev ? (
                <Link
                  href={buildUrl({ _offset: Math.max(0, offset - PAGE_SIZE).toString() })}
                  className="btn-secondary text-sm px-3 py-1.5"
                >
                  ← Previous
                </Link>
              ) : (
                <button disabled className="btn-secondary text-sm px-3 py-1.5 opacity-40 cursor-not-allowed">← Previous</button>
              )}
              {hasNext ? (
                <Link
                  href={buildUrl({ _offset: (offset + PAGE_SIZE).toString() })}
                  className="btn-secondary text-sm px-3 py-1.5"
                >
                  Next →
                </Link>
              ) : (
                <button disabled className="btn-secondary text-sm px-3 py-1.5 opacity-40 cursor-not-allowed">Next →</button>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
