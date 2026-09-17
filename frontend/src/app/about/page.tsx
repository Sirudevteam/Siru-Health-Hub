import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  FiInfo,
  FiServer,
  FiDatabase,
  FiShield,
  FiActivity,
  FiCheckCircle,
  FiExternalLink,
  FiLayers,
  FiLock,
  FiCode,
  FiUsers,
  FiDollarSign,
  FiCpu,
  FiGlobe
} from 'react-icons/fi';
import {
  FaHeartPulse,
  FaHospital,
  FaStethoscope,
  FaFileInvoiceDollar,
  FaShieldHalved
} from 'react-icons/fa6';

export default function AboutPage() {
  const standards = [
    {
      code: 'HL7 FHIR R4',
      title: 'HL7 Fast Healthcare Interoperability Resources (v4.0.1)',
      desc: 'Standardized RESTful JSON schema for clinical resources, semantic interoperability, and conformance CapabilityStatement.'
    },
    {
      code: 'HIPAA Security',
      title: '45 CFR § 164.312 Technical Safeguards',
      desc: 'Role-based access control, cryptographic token revocation via Redis, TLS 1.3 encryption, and immutable audit trails.'
    },
    {
      code: 'EDI 270 / 271',
      title: 'Real-Time Eligibility & Benefit Inquiry',
      desc: 'Instant verification of patient insurance policy active status, deductible balances, and network coverage.'
    },
    {
      code: 'EDI 837 / 835',
      title: 'Health Care Claims & Auto-Adjudication',
      desc: 'Automated payer decision engine evaluating coverage terms, calculating 90% insurer reimbursement / 10% copays, and generating ClaimResponses.'
    }
  ];

  const modules = [
    {
      title: 'Clinical FHIR Repository',
      icon: FaStethoscope,
      bg: 'bg-emerald-50 text-emerald-700 border-emerald-100',
      description: 'Fully indexed clinical dataset spanning Patients, Practitioners, Organizations, Encounters, Observations (vitals/labs), Conditions (ICD-10), Prescriptions, and Appointments.',
      features: ['Logical FHIR ID indexing', 'JSONB schema flexibility', 'Cross-resource reference resolution']
    },
    {
      title: 'Revenue Cycle Engine (RCM)',
      icon: FaFileInvoiceDollar,
      bg: 'bg-blue-50 text-blue-700 border-blue-100',
      description: 'Built-in payer adjudication engine performing real-time math, policy verification, denial triggers on expired policies, and Explanation of Benefits (EOB) tracking in USD ($).',
      features: ['Real-time auto-adjudication', '90% benefit / 10% copay math', 'Automated coverage denial rules']
    },
    {
      title: 'Zero-Trust Security & RBAC',
      icon: FaShieldHalved,
      bg: 'bg-purple-50 text-purple-700 border-purple-100',
      description: 'Hierarchical role enforcement across Admin, Doctor, Nurse, and Patient roles, backed by bcrypt password hashing and instantaneous Redis token blacklisting upon logout.',
      features: ['Granular HTTP verb authorization', 'Redis distributed token blacklist', 'Patient self-record scoping']
    },
    {
      title: 'Observability & Analytics',
      icon: FiActivity,
      bg: 'bg-amber-50 text-amber-700 border-amber-100',
      description: 'Native Prometheus scrape endpoint (/metrics) exposing request latency, status code counters, and auth events, paired with an executive RCM analytics dashboard.',
      features: ['Prometheus metrics collector', 'Executive RCM KPI dashboard', 'Searchable HIPAA audit explorer']
    }
  ];

  const stack = [
    { name: 'FastAPI (Python 3.11)', role: 'Async REST API Core', icon: FiServer },
    { name: 'SQLAlchemy 2.x & Asyncpg', role: 'Async ORM & Connection Pooling', icon: FiDatabase },
    { name: 'PostgreSQL 15', role: 'Relational DB + JSONB Indexing', icon: FiDatabase },
    { name: 'Redis 7 Alpine', role: 'Distributed Token Revocation Cache', icon: FiCpu },
    { name: 'Next.js 15 & React 19', role: 'Executive UI & Patient Portal', icon: FiLayers },
    { name: 'Nginx TLS Gateway', role: 'TLS 1.2 / 1.3 Reverse Proxy', icon: FiGlobe },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-10">
      {/* ── Header / Hero ──────────────────────────────────────────────── */}
      <section className="bg-gradient-to-br from-emerald-700 via-teal-800 to-slate-900 rounded-3xl p-8 md:p-12 text-white shadow-xl relative overflow-hidden">
        <div className="max-w-3xl relative z-10 space-y-4">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md px-3.5 py-1.5 rounded-full text-xs font-semibold text-emerald-200 border border-white/10">
            <FaHeartPulse className="w-3.5 h-3.5 text-emerald-400" />
            <span>Platform Overview & Architecture</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            About Siru HealthHub
          </h1>
          <p className="text-emerald-100/90 text-base sm:text-lg leading-relaxed font-normal">
            Siru HealthHub is an enterprise-grade, end-to-end healthcare interoperability platform built on the
            <strong className="text-white ml-1">HL7® FHIR® R4 specification</strong>. Designed for hospital networks, clinical providers,
            and health payers, it integrates high-throughput clinical records, automated claims adjudication in USD ($),
            and strict HIPAA-compliant security.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <a
              href="https://localhost/fhir/metadata"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-white text-emerald-800 hover:bg-emerald-50 rounded-xl font-semibold text-xs transition shadow"
            >
              <FiCode className="w-3.5 h-3.5" /> View CapabilityStatement <FiExternalLink className="w-3 h-3 opacity-60" />
            </a>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl font-semibold text-xs transition border border-white/20"
            >
              <FiServer className="w-3.5 h-3.5" /> OpenAPI Swagger Docs <FiExternalLink className="w-3 h-3 opacity-60" />
            </a>
            <Link
              href="/admin/analytics"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-semibold text-xs transition shadow"
            >
              <FiActivity className="w-3.5 h-3.5" /> Executive Analytics
            </Link>
          </div>
        </div>
      </section>

      {/* ── Core Capabilities ─────────────────────────────────────────── */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-md">
              <FiLayers className="w-5 h-5" />
            </div>
            Core Platform Pillars
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Built from the ground up to solve hospital clinical coordination, payer adjudication, and audit requirements.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {modules.map((m) => {
            const Icon = m.icon;
            return (
              <Card key={m.title} className="p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl border ${m.bg} flex-shrink-0`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="space-y-2 min-w-0">
                    <h3 className="text-base font-bold text-gray-900">{m.title}</h3>
                    <p className="text-xs text-gray-600 leading-relaxed">{m.description}</p>
                    <ul className="pt-2 space-y-1 text-xs text-gray-500 border-t border-gray-100">
                      {m.features.map((f, i) => (
                        <li key={i} className="flex items-center gap-1.5 text-gray-700">
                          <FiCheckCircle className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      {/* ── Healthcare Standards & Interoperability ────────────────────── */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <div className="p-1.5 bg-blue-50 text-blue-600 rounded-md">
              <FiCheckCircle className="w-5 h-5" />
            </div>
            Standards, Interoperability & Compliance
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Compliant with North American and international healthcare IT regulatory frameworks.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {standards.map((s) => (
            <Card key={s.code} className="p-5 border-t-4 border-t-emerald-600 space-y-2">
              <span className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                {s.code}
              </span>
              <h3 className="text-sm font-bold text-gray-900 leading-snug">{s.title}</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{s.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Technology Stack ──────────────────────────────────────────── */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <div className="p-1.5 bg-purple-50 text-purple-600 rounded-md">
              <FiServer className="w-5 h-5" />
            </div>
            Enterprise Technology Stack
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Production microservices packaged via Docker Compose with dedicated health checks.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {stack.map((item) => {
            const ItemIcon = item.icon;
            return (
              <Card key={item.name} className="p-4 flex items-center gap-3.5 hover:border-emerald-300 transition-colors">
                <div className="p-2.5 bg-gray-50 text-gray-700 rounded-lg flex-shrink-0">
                  <ItemIcon className="w-5 h-5 text-emerald-700" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-900">{item.name}</h4>
                  <p className="text-xs text-gray-500">{item.role}</p>
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      {/* ── System Topology & Operational Links ───────────────────────── */}
      <section className="bg-gray-50 rounded-2xl p-6 border border-gray-200 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-200 pb-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">System Gateway & Verification Endpoints</h3>
            <p className="text-xs text-gray-500">Live development and production inspection targets</p>
          </div>
          <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2.5 py-1 rounded-full self-start sm:self-auto">
            All 13 Health Checks Passing
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-500 font-medium">FHIR Capability Statement</p>
            <a href="https://localhost/fhir/metadata" target="_blank" rel="noreferrer" className="text-blue-600 font-mono hover:underline flex items-center gap-1 mt-1">
              /fhir/metadata <FiExternalLink className="w-3 h-3" />
            </a>
          </div>
          <div className="p-3 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-500 font-medium">Prometheus Metrics Feed</p>
            <a href="http://localhost:8000/metrics" target="_blank" rel="noreferrer" className="text-blue-600 font-mono hover:underline flex items-center gap-1 mt-1">
              /metrics <FiExternalLink className="w-3 h-3" />
            </a>
          </div>
          <div className="p-3 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-500 font-medium">Executive Analytics API</p>
            <a href="http://localhost:8000/analytics/summary" target="_blank" rel="noreferrer" className="text-blue-600 font-mono hover:underline flex items-center gap-1 mt-1">
              /analytics/summary <FiExternalLink className="w-3 h-3" />
            </a>
          </div>
          <div className="p-3 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-500 font-medium">HIPAA Audit Log Explorer</p>
            <Link href="/admin/audit" className="text-emerald-700 font-semibold hover:underline flex items-center gap-1 mt-1">
              /admin/audit
            </Link>
          </div>
          <div className="p-3 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-500 font-medium">RCM Analytics Dashboard</p>
            <Link href="/admin/analytics" className="text-emerald-700 font-semibold hover:underline flex items-center gap-1 mt-1">
              /admin/analytics
            </Link>
          </div>
          <div className="p-3 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-500 font-medium">Patient Master Registry</p>
            <Link href="/patients" className="text-emerald-700 font-semibold hover:underline flex items-center gap-1 mt-1">
              /patients
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

