'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { createPatient } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import type { FHIRPatient } from '@/types/fhir';
import {
  FiUserPlus,
  FiUser,
  FiPhone,
  FiMapPin,
  FiCheckCircle,
  FiAlertCircle,
  FiArrowLeft,
  FiCalendar,
  FiMail
} from 'react-icons/fi';

// ─── Types ───────────────────────────────────────────────────────────────────

interface FormState {
  // Basic
  firstName: string;
  lastName: string;
  gender: 'male' | 'female' | 'other' | 'unknown' | '';
  birthDate: string;
  // Contact
  phone: string;
  email: string;
  // Address
  street: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

interface FormErrors {
  firstName?: string;
  lastName?: string;
  gender?: string;
  birthDate?: string;
}

const initialForm: FormState = {
  firstName: '',
  lastName: '',
  gender: '',
  birthDate: '',
  phone: '',
  email: '',
  street: '',
  city: '',
  state: '',
  postalCode: '',
  country: 'United States',
};

// ─── Build FHIR payload ──────────────────────────────────────────────────────

function buildFHIRPatient(form: FormState): FHIRPatient {
  const patient: FHIRPatient = {
    resourceType: 'Patient',
    name: [
      {
        family: form.lastName,
        given: [form.firstName],
      },
    ],
    gender: form.gender as FHIRPatient['gender'],
    birthDate: form.birthDate,
  };

  const telecom = [];
  if (form.phone) telecom.push({ system: 'phone', value: form.phone, use: 'home' });
  if (form.email) telecom.push({ system: 'email', value: form.email, use: 'home' });
  if (telecom.length) patient.telecom = telecom;

  const hasAddress = form.street || form.city || form.state || form.postalCode || form.country;
  if (hasAddress) {
    patient.address = [
      {
        use: 'home',
        ...(form.street ? { line: [form.street] } : {}),
        ...(form.city       ? { city:       form.city }       : {}),
        ...(form.state      ? { state:      form.state }      : {}),
        ...(form.postalCode ? { postalCode: form.postalCode } : {}),
        ...(form.country    ? { country:    form.country }    : {}),
      },
    ];
  }

  return patient;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function NewPatientPage() {
  const [form, setForm] = useState<FormState>(initialForm);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [createdPatient, setCreatedPatient] = useState<FHIRPatient | null>(null);

  function update(field: keyof FormState, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  function validate(): boolean {
    const newErrors: FormErrors = {};
    if (!form.firstName.trim()) newErrors.firstName = 'First name is required';
    if (!form.lastName.trim())  newErrors.lastName  = 'Last name is required';
    if (!form.gender)           newErrors.gender    = 'Please select a gender';
    if (!form.birthDate)        newErrors.birthDate = 'Date of birth is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const payload = buildFHIRPatient(form);
      const result: FHIRPatient = await createPatient(payload as unknown as Record<string, unknown>);
      setCreatedPatient(result);
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to register patient. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleReset() {
    setForm(initialForm);
    setErrors({});
    setSubmitError(null);
    setCreatedPatient(null);
  }

  // ── Success screen ──
  if (createdPatient) {
    const name = [createdPatient.name?.[0]?.given?.join(' '), createdPatient.name?.[0]?.family]
      .filter(Boolean)
      .join(' ');

    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <Card className="text-center border-emerald-200 bg-gradient-to-b from-emerald-50/60 to-white shadow-md p-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center shadow-inner">
              <FiCheckCircle className="w-9 h-9" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Patient Enrolled Successfully</h2>
          <p className="text-gray-600 mb-1">
            <span className="font-semibold text-gray-900">{name || 'Patient'}</span> has been assigned a logical FHIR logical ID.
          </p>
          <p className="text-xs text-gray-500 font-mono mb-6 bg-white py-1 px-3 rounded border inline-block">
            Logical ID: {createdPatient.id}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href={`/patients/${createdPatient.id}`}
              className="inline-flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-lg font-semibold text-sm shadow-sm transition"
            >
              View Clinical Record
            </Link>
            <button
              onClick={handleReset}
              className="inline-flex items-center justify-center gap-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 px-5 py-2.5 rounded-lg font-semibold text-sm transition"
            >
              Enroll Another Patient
            </button>
          </div>
        </Card>
      </div>
    );
  }

  // ── Form ──
  return (
    <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <FiUserPlus className="w-6 h-6" />
            </div>
            Enroll New Patient
          </h1>
          <p className="text-sm text-gray-500 mt-1">Create an HL7 FHIR R4 compliant master patient record</p>
        </div>
        <Link
          href="/patients"
          className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-gray-300 rounded-lg text-xs font-semibold text-gray-700 bg-white hover:bg-gray-50 transition"
        >
          <FiArrowLeft className="w-3.5 h-3.5" /> Back
        </Link>
      </div>

      {/* Global error */}
      {submitError && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl px-4 py-3 flex items-start gap-3">
          <FiAlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-rose-800 text-sm">Enrollment failed</p>
            <p className="text-rose-600 text-xs mt-0.5">{submitError}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-6">

        {/* Section 1: Basic Information */}
        <Card>
          <h2 className="text-base font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-lg bg-emerald-100 text-emerald-700 text-xs font-bold">
              <FiUser className="w-3.5 h-3.5" />
            </span>
            Basic Demographics
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="firstName" className="block text-xs font-semibold text-gray-700 mb-1">
                First Name <span className="text-rose-500">*</span>
              </label>
              <input
                id="firstName"
                type="text"
                placeholder="e.g. Robert"
                value={form.firstName}
                onChange={(e) => update('firstName', e.target.value)}
                className={`w-full border rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 ${errors.firstName ? 'border-rose-400 focus:ring-rose-400' : 'border-gray-300 focus:ring-emerald-500'}`}
              />
              {errors.firstName && <p className="text-xs text-rose-600 mt-1">{errors.firstName}</p>}
            </div>

            <div>
              <label htmlFor="lastName" className="block text-xs font-semibold text-gray-700 mb-1">
                Last Name / Family Name <span className="text-rose-500">*</span>
              </label>
              <input
                id="lastName"
                type="text"
                placeholder="e.g. Miller"
                value={form.lastName}
                onChange={(e) => update('lastName', e.target.value)}
                className={`w-full border rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 ${errors.lastName ? 'border-rose-400 focus:ring-rose-400' : 'border-gray-300 focus:ring-emerald-500'}`}
              />
              {errors.lastName && <p className="text-xs text-rose-600 mt-1">{errors.lastName}</p>}
            </div>

            <div>
              <label htmlFor="gender" className="block text-xs font-semibold text-gray-700 mb-1">
                Administrative Gender <span className="text-rose-500">*</span>
              </label>
              <select
                id="gender"
                value={form.gender}
                onChange={(e) => update('gender', e.target.value)}
                className={`w-full border rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 ${errors.gender ? 'border-rose-400 focus:ring-rose-400' : 'border-gray-300 focus:ring-emerald-500'}`}
              >
                <option value="">Select gender...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="unknown">Unknown</option>
              </select>
              {errors.gender && <p className="text-xs text-rose-600 mt-1">{errors.gender}</p>}
            </div>

            <div>
              <label htmlFor="birthDate" className="block text-xs font-semibold text-gray-700 mb-1">
                Date of Birth <span className="text-rose-500">*</span>
              </label>
              <input
                id="birthDate"
                type="date"
                value={form.birthDate}
                max={new Date().toISOString().split('T')[0]}
                onChange={(e) => update('birthDate', e.target.value)}
                className={`w-full border rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 ${errors.birthDate ? 'border-rose-400 focus:ring-rose-400' : 'border-gray-300 focus:ring-emerald-500'}`}
              />
              {errors.birthDate && <p className="text-xs text-rose-600 mt-1">{errors.birthDate}</p>}
            </div>
          </div>
        </Card>

        {/* Section 2: Contact Information */}
        <Card>
          <h2 className="text-base font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-lg bg-emerald-100 text-emerald-700 text-xs font-bold">
              <FiPhone className="w-3.5 h-3.5" />
            </span>
            Contact Points
            <span className="ml-auto text-xs font-normal text-gray-400">Optional</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="phone" className="block text-xs font-semibold text-gray-700 mb-1">Phone Number</label>
              <input
                id="phone"
                type="tel"
                placeholder="+1 (555) 234-5678"
                value={form.phone}
                onChange={(e) => update('phone', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-gray-700 mb-1">Email Address</label>
              <input
                id="email"
                type="email"
                placeholder="robert.miller@example.com"
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>
        </Card>

        {/* Section 3: Address */}
        <Card>
          <h2 className="text-base font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-lg bg-emerald-100 text-emerald-700 text-xs font-bold">
              <FiMapPin className="w-3.5 h-3.5" />
            </span>
            Residential Address
            <span className="ml-auto text-xs font-normal text-gray-400">Optional</span>
          </h2>
          <div className="space-y-4">
            <div>
              <label htmlFor="street" className="block text-xs font-semibold text-gray-700 mb-1">Street Address</label>
              <input
                id="street"
                type="text"
                placeholder="100 Longwood Ave, Suite 300"
                value={form.street}
                onChange={(e) => update('street', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="city" className="block text-xs font-semibold text-gray-700 mb-1">City</label>
                <input
                  id="city"
                  type="text"
                  placeholder="Boston"
                  value={form.city}
                  onChange={(e) => update('city', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label htmlFor="state" className="block text-xs font-semibold text-gray-700 mb-1">State / Province</label>
                <input
                  id="state"
                  type="text"
                  placeholder="MA"
                  value={form.state}
                  onChange={(e) => update('state', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label htmlFor="postalCode" className="block text-xs font-semibold text-gray-700 mb-1">ZIP / Postal Code</label>
                <input
                  id="postalCode"
                  type="text"
                  placeholder="02115"
                  value={form.postalCode}
                  onChange={(e) => update('postalCode', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label htmlFor="country" className="block text-xs font-semibold text-gray-700 mb-1">Country</label>
                <input
                  id="country"
                  type="text"
                  placeholder="United States"
                  value={form.country}
                  onChange={(e) => update('country', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Submit */}
        <div className="flex flex-col sm:flex-row gap-3 justify-end pb-4">
          <Link
            href="/patients"
            className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-semibold text-sm transition"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold text-sm transition shadow-sm disabled:opacity-50 min-w-[170px]"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Enrolling Patient...
              </>
            ) : (
              <>
                <FiCheckCircle className="w-4 h-4" /> Enrol Patient
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
