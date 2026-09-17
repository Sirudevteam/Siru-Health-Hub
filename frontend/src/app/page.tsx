import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { getPatients } from '@/lib/api';
import type { FHIRBundle } from '@/types/fhir';

async function fetchPatientCount(): Promise<number | null> {
  try {
    const bundle: FHIRBundle = await getPatients({ _count: '1' });
    return bundle.total ?? 0;
  } catch {
    return null;
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default async function HomePage() {
  const patientCount = await fetchPatientCount();

  const stats = [
    {
      label: 'Total Patients',
      value: patientCount !== null ? patientCount.toString() : '—',
      sub: patientCount !== null ? 'Registered in system' : 'API unavailable',
      icon: (
        <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
    {
      label: 'FHIR Version',
      value: 'R4',
      sub: '4.0.1',
      icon: (
        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      label: 'API Status',
      value: patientCount !== null ? 'Online' : 'Offline',
      sub: patientCount !== null ? 'All systems operational' : 'Cannot reach backend',
      icon: (
        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      badge: patientCount !== null
        ? <Badge variant="green">Online</Badge>
        : <Badge variant="red">Offline</Badge>,
    },
    {
      label: 'Compliance',
      value: 'HL7',
      sub: 'FHIR R4 Standard',
      icon: (
        <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">

      {/* Hero */}
      <section className="text-center py-12 bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-2xl text-white shadow-xl">
        <div className="flex justify-center mb-4">
          <div className="bg-white/20 backdrop-blur rounded-full p-4">
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
        </div>
        <h1 className="text-4xl font-bold mb-3">Welcome to Siru HealthHub</h1>
        <p className="text-emerald-100 text-lg max-w-2xl mx-auto">
          A modern, FHIR R4-compliant healthcare patient portal. Manage patient records,
          search by demographics, and integrate seamlessly with HL7-compliant systems.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link href="/patients/new" className="btn-primary bg-white text-emerald-700 hover:bg-emerald-50 px-6 py-3 rounded-lg font-semibold shadow">
            Register Patient
          </Link>
          <Link href="/patients" className="btn-secondary border-white text-white hover:bg-emerald-700 px-6 py-3 rounded-lg font-semibold">
            View All Patients
          </Link>
        </div>
      </section>

      {/* Stats grid */}
      <section>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">System Overview</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <Card key={stat.label} className="flex items-start gap-4">
              <div className="flex-shrink-0 p-2 bg-gray-50 rounded-lg">
                {stat.icon}
              </div>
              <div className="min-w-0">
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-0.5">{stat.value}</p>
                <div className="mt-1">
                  {stat.badge ?? (
                    <span className="text-xs text-gray-500">{stat.sub}</span>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Quick Actions */}
      <section>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link href="/patients/new" className="group">
            <Card className="h-full hover:shadow-lg hover:border-emerald-300 transition-all duration-200 cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0 p-3 bg-emerald-100 rounded-xl group-hover:bg-emerald-200 transition-colors">
                  <svg className="w-7 h-7 text-emerald-700" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors">
                    Register New Patient
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Add a new patient record with FHIR R4 compliant data entry
                  </p>
                </div>
                <svg className="ml-auto w-5 h-5 text-gray-400 group-hover:text-emerald-600 flex-shrink-0 transition-colors" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Card>
          </Link>

          <Link href="/patients" className="group">
            <Card className="h-full hover:shadow-lg hover:border-emerald-300 transition-all duration-200 cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0 p-3 bg-blue-100 rounded-xl group-hover:bg-blue-200 transition-colors">
                  <svg className="w-7 h-7 text-blue-700" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                    View All Patients
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Browse, search, and filter your patient registry
                  </p>
                </div>
                <svg className="ml-auto w-5 h-5 text-gray-400 group-hover:text-blue-600 flex-shrink-0 transition-colors" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Card>
          </Link>
        </div>
      </section>

      {/* System Info */}
      <section>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">System Information</h2>
        <Card className="overflow-hidden p-0">
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {[
                { key: 'API Base URL',    value: API_URL },
                { key: 'FHIR Base URL',   value: `${API_URL}/fhir` },
                { key: 'FHIR Version',    value: 'R4 (4.0.1)' },
                { key: 'Standard',        value: 'HL7 FHIR R4' },
                { key: 'Database Status', value: patientCount !== null ? 'Connected' : 'Unreachable' },
                { key: 'Patient Count',   value: patientCount !== null ? `${patientCount} registered` : 'Unknown' },
              ].map(({ key, value }) => (
                <tr key={key} className="hover:bg-gray-50">
                  <td className="px-6 py-3 font-medium text-gray-600 w-48">{key}</td>
                  <td className="px-6 py-3 text-gray-800 font-mono text-xs">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>
    </div>
  );
}
