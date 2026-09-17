import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { getPatients } from '@/lib/api';
import type { FHIRBundle } from '@/types/fhir';
import {
  FiUsers,
  FiFileText,
  FiActivity,
  FiShield,
  FiUserPlus,
  FiArrowRight,
  FiCheckCircle,
  FiServer,
  FiDatabase
} from 'react-icons/fi';
import { FaHeartPulse, FaHospital } from 'react-icons/fa6';

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
      sub: patientCount !== null ? 'Registered in FHIR registry' : 'API unavailable',
      icon: <FiUsers className="w-6 h-6 text-emerald-600" />,
      bg: 'bg-emerald-50'
    },
    {
      label: 'FHIR Standard',
      value: 'R4',
      sub: 'HL7 Specification 4.0.1',
      icon: <FiFileText className="w-6 h-6 text-blue-600" />,
      bg: 'bg-blue-50'
    },
    {
      label: 'API Status',
      value: patientCount !== null ? 'Online' : 'Offline',
      sub: patientCount !== null ? 'All services operational' : 'Cannot reach backend',
      icon: <FiActivity className="w-6 h-6 text-emerald-600" />,
      bg: 'bg-emerald-50',
      badge: patientCount !== null
        ? <Badge variant="green">Online</Badge>
        : <Badge variant="red">Offline</Badge>,
    },
    {
      label: 'HIPAA & RBAC',
      value: 'Secured',
      sub: 'JWT & Redis Revocation',
      icon: <FiShield className="w-6 h-6 text-purple-600" />,
      bg: 'bg-purple-50'
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">

      {/* Hero */}
      <section className="text-center py-12 px-6 bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-800 rounded-2xl text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex justify-center mb-4">
            <div className="bg-white/15 backdrop-blur-md rounded-2xl p-4 shadow-inner">
              <FaHeartPulse className="w-12 h-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-3 tracking-tight">Siru HealthHub Healthcare System</h1>
          <p className="text-emerald-100 text-lg max-w-2xl mx-auto font-normal leading-relaxed">
            Enterprise HL7 FHIR R4 clinical repository, real-time insurance eligibility (EDI 270/271),
            automated claims adjudication engine, and HIPAA security intelligence.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/patients/new"
              className="inline-flex items-center gap-2 bg-white text-emerald-700 hover:bg-emerald-50 px-6 py-3 rounded-xl font-semibold shadow-md transition-all hover:shadow-lg"
            >
              <FiUserPlus className="w-4 h-4" /> Register Patient
            </Link>
            <Link
              href="/patients"
              className="inline-flex items-center gap-2 border border-white/60 text-white hover:bg-white/10 px-6 py-3 rounded-xl font-semibold transition-colors"
            >
              <FiUsers className="w-4 h-4" /> View Patient Registry
            </Link>
          </div>
        </div>
      </section>

      {/* Stats grid */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">Platform Overview</h2>
          <span className="text-xs bg-emerald-50 text-emerald-700 font-medium px-2.5 py-1 rounded-full border border-emerald-200 flex items-center gap-1.5">
            <FiCheckCircle className="w-3.5 h-3.5 text-emerald-600" /> Live System Telemetry
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <Card key={stat.label} className="flex items-start gap-4 hover:shadow-md transition-shadow">
              <div className={`flex-shrink-0 p-3 ${stat.bg} rounded-xl`}>
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
        <h2 className="text-xl font-bold text-gray-800 mb-4">Clinical & Operational Portals</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link href="/patients/new" className="group">
            <Card className="h-full hover:shadow-lg hover:border-emerald-300 transition-all duration-200 cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0 p-3.5 bg-emerald-50 text-emerald-700 rounded-xl group-hover:bg-emerald-100 transition-colors">
                  <FiUserPlus className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors">
                    Register New Patient
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Add a new patient record with FHIR R4 compliant demographics and identifiers
                  </p>
                </div>
                <FiArrowRight className="ml-auto w-5 h-5 text-gray-400 group-hover:text-emerald-600 group-hover:translate-x-1 flex-shrink-0 transition-all" />
              </div>
            </Card>
          </Link>

          <Link href="/patients" className="group">
            <Card className="h-full hover:shadow-lg hover:border-blue-300 transition-all duration-200 cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0 p-3.5 bg-blue-50 text-blue-700 rounded-xl group-hover:bg-blue-100 transition-colors">
                  <FiUsers className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                    View All Patients
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Browse, search, and filter clinical EHR records, vitals, and billing claims
                  </p>
                </div>
                <FiArrowRight className="ml-auto w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 flex-shrink-0 transition-all" />
              </div>
            </Card>
          </Link>
        </div>
      </section>

      {/* System Info */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">System Infrastructure</h2>
          <span className="text-xs text-gray-500 font-mono">TLS 1.3 / Reverse Proxy</span>
        </div>
        <Card className="overflow-hidden p-0">
          <table className="w-full text-sm">
            <tbody className="divide-y divide-gray-100">
              {[
                { key: 'API Base URL',    value: API_URL, icon: FiServer },
                { key: 'FHIR Base URL',   value: `${API_URL}/fhir`, icon: FiServer },
                { key: 'FHIR Version',    value: 'R4 (4.0.1)', icon: FiFileText },
                { key: 'Standard',        value: 'HL7 FHIR R4', icon: FiShield },
                { key: 'Database Status', value: patientCount !== null ? 'PostgreSQL 15 Connected' : 'Unreachable', icon: FiDatabase },
                { key: 'Patient Registry', value: patientCount !== null ? `${patientCount} active records` : 'Unknown', icon: FiUsers },
              ].map(({ key, value, icon: RowIcon }) => (
                <tr key={key} className="hover:bg-gray-50/75 transition-colors">
                  <td className="px-6 py-3 font-medium text-gray-600 w-56 flex items-center gap-2">
                    <RowIcon className="w-4 h-4 text-gray-400" />
                    {key}
                  </td>
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
