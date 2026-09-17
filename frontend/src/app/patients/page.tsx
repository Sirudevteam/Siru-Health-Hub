import Link from 'next/link';
import { getPatients } from '@/lib/api';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import type { FHIRBundle, FHIRPatient, HumanName } from '@/types/fhir';
import {
  FiUsers,
  FiUserPlus,
  FiSearch,
  FiAlertCircle,
  FiChevronLeft,
  FiChevronRight,
  FiArrowRight
} from 'react-icons/fi';

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
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <FiUsers className="w-6 h-6" />
            </div>
            Patient Registry
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {total > 0 ? `${total} patient${total !== 1 ? 's' : ''} enrolled in enterprise master patient index (MPI)` : 'No patients found'}
          </p>
        </div>
        <Link
          href="/patients/new"
          className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors shadow-sm self-start sm:self-auto"
        >
          <FiUserPlus className="w-4 h-4" />
          Register Patient
        </Link>
      </div>

      {/* Search / Filter bar */}
      <Card className="p-4">
        <form method="GET" action="/patients" className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs font-semibold text-gray-700 mb-1">Search by Name</label>
            <div className="relative">
              <input
                name="name"
                type="text"
                placeholder="e.g. Arun Kumar"
                defaultValue={sp.name ?? ''}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="min-w-[150px]">
            <label className="block text-xs font-semibold text-gray-700 mb-1">Gender</label>
            <select
              name="gender"
              defaultValue={sp.gender ?? ''}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="">All Genders</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="block text-xs font-semibold text-gray-700 mb-1">Date of Birth</label>
            <input
              name="birthdate"
              type="date"
              defaultValue={sp.birthdate ?? ''}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold transition"
            >
              <FiSearch className="w-4 h-4" /> Search
            </button>
            <Link
              href="/patients"
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-semibold transition"
            >
              Clear
            </Link>
          </div>
        </form>
      </Card>

      {/* Error state */}
      {error && (
        <Card className="border-rose-200 bg-rose-50">
          <div className="flex items-center gap-3">
            <FiAlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <div>
              <p className="font-medium text-rose-800">Failed to load patients</p>
              <p className="text-sm text-rose-600 mt-0.5">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Empty state */}
      {!error && patients.length === 0 && (
        <Card className="text-center py-16">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
            <FiUsers className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No patients found</h3>
          <p className="text-gray-500 mb-6 text-sm max-w-md mx-auto">
            {Object.values(sp).some(Boolean)
              ? 'No patient records match the specified filters. Try broadening your criteria.'
              : 'The patient registry is currently empty. Begin by enrolling your first patient.'}
          </p>
          <Link
            href="/patients/new"
            className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition shadow-sm"
          >
            <FiUserPlus className="w-4 h-4" /> Register First Patient
          </Link>
        </Card>
      )}

      {/* Table */}
      {!error && patients.length > 0 && (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50/80 border-b border-gray-200">
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
                    <tr key={patient.id} className="hover:bg-gray-50/80 transition-colors">
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
                          className="inline-flex items-center gap-1 text-emerald-600 hover:text-emerald-800 font-semibold text-sm transition-colors group"
                        >
                          View
                          <FiArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
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
            <span className="text-xs text-gray-600">
              Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total} patients
            </span>
            <div className="flex items-center gap-2">
              {hasPrev ? (
                <Link
                  href={buildUrl({ _offset: Math.max(0, offset - PAGE_SIZE).toString() })}
                  className="inline-flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 transition"
                >
                  <FiChevronLeft className="w-3.5 h-3.5" /> Previous
                </Link>
              ) : (
                <button disabled className="inline-flex items-center gap-1 px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-semibold text-gray-400 bg-gray-100 opacity-50 cursor-not-allowed">
                  <FiChevronLeft className="w-3.5 h-3.5" /> Previous
                </button>
              )}
              {hasNext ? (
                <Link
                  href={buildUrl({ _offset: (offset + PAGE_SIZE).toString() })}
                  className="inline-flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 transition"
                >
                  Next <FiChevronRight className="w-3.5 h-3.5" />
                </Link>
              ) : (
                <button disabled className="inline-flex items-center gap-1 px-3 py-1.5 border border-gray-200 rounded-lg text-xs font-semibold text-gray-400 bg-gray-100 opacity-50 cursor-not-allowed">
                  Next <FiChevronRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
