'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { createPatient } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import type { FHIRPatient } from '@/types/fhir';

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
  country: '',
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
        <Card className="text-center border-emerald-200 bg-emerald-50">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Patient Registered!</h2>
          <p className="text-gray-600 mb-1">
            <span className="font-semibold text-gray-900">{name || 'Patient'}</span> has been successfully registered.
          </p>
          <p className="text-xs text-gray-400 font-mono mb-6">ID: {createdPatient.id}</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href={`/patients/${createdPatient.id}`} className="btn-primary">
              View Patient Record
            </Link>
            <button onClick={handleReset} className="btn-secondary">
              Register Another Patient
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
          <h1 className="text-2xl font-bold text-gray-900">Register New Patient</h1>
          <p className="text-sm text-gray-500 mt-1">Create a FHIR R4 compliant patient record</p>
        </div>
        <Link href="/patients" className="btn-secondary text-sm">Cancel</Link>
      </div>

      {/* Global error */}
      {submitError && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 flex items-start gap-3">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="font-medium text-red-800 text-sm">Registration failed</p>
            <p className="text-red-600 text-sm mt-0.5">{submitError}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-6">

        {/* Section 1: Basic Information */}
        <Card>
          <h2 className="text-base font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">1</span>
            Basic Information
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="firstName" className="form-label">
                First Name <span className="text-red-500">*</span>
              </label>
              <input
                id="firstName"
                type="text"
                placeholder="e.g. Arun"
                value={form.firstName}
                onChange={(e) => update('firstName', e.target.value)}
                className={`form-input ${errors.firstName ? 'border-red-400 focus:border-red-400 focus:ring-red-400' : ''}`}
              />
              {errors.firstName && <p className="form-error">{errors.firstName}</p>}
            </div>

            <div>
              <label htmlFor="lastName" className="form-label">
                Last Name / Family Name <span className="text-red-500">*</span>
              </label>
              <input
                id="lastName"
                type="text"
                placeholder="e.g. Kumar"
                value={form.lastName}
                onChange={(e) => update('lastName', e.target.value)}
                className={`form-input ${errors.lastName ? 'border-red-400 focus:border-red-400 focus:ring-red-400' : ''}`}
              />
              {errors.lastName && <p className="form-error">{errors.lastName}</p>}
            </div>

            <div>
              <label htmlFor="gender" className="form-label">
                Gender <span className="text-red-500">*</span>
              </label>
              <select
                id="gender"
                value={form.gender}
                onChange={(e) => update('gender', e.target.value)}
                className={`form-input ${errors.gender ? 'border-red-400 focus:border-red-400 focus:ring-red-400' : ''}`}
              >
                <option value="">Select gender...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="unknown">Unknown</option>
              </select>
              {errors.gender && <p className="form-error">{errors.gender}</p>}
            </div>

            <div>
              <label htmlFor="birthDate" className="form-label">
                Date of Birth <span className="text-red-500">*</span>
              </label>
              <input
                id="birthDate"
                type="date"
                value={form.birthDate}
                max={new Date().toISOString().split('T')[0]}
                onChange={(e) => update('birthDate', e.target.value)}
                className={`form-input ${errors.birthDate ? 'border-red-400 focus:border-red-400 focus:ring-red-400' : ''}`}
              />
              {errors.birthDate && <p className="form-error">{errors.birthDate}</p>}
            </div>
          </div>
        </Card>

        {/* Section 2: Contact Information */}
        <Card>
          <h2 className="text-base font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">2</span>
            Contact Information
            <span className="ml-auto text-xs font-normal text-gray-400">Optional</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="phone" className="form-label">Phone Number</label>
              <input
                id="phone"
                type="tel"
                placeholder="+91 98765 43210"
                value={form.phone}
                onChange={(e) => update('phone', e.target.value)}
                className="form-input"
              />
            </div>
            <div>
              <label htmlFor="email" className="form-label">Email Address</label>
              <input
                id="email"
                type="email"
                placeholder="patient@example.com"
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                className="form-input"
              />
            </div>
          </div>
        </Card>

        {/* Section 3: Address */}
        <Card>
          <h2 className="text-base font-semibold text-gray-900 mb-5 pb-3 border-b border-gray-100 flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">3</span>
            Address
            <span className="ml-auto text-xs font-normal text-gray-400">Optional</span>
          </h2>
          <div className="space-y-4">
            <div>
              <label htmlFor="street" className="form-label">Street Address</label>
              <input
                id="street"
                type="text"
                placeholder="123 Main Street, Apt 4"
                value={form.street}
                onChange={(e) => update('street', e.target.value)}
                className="form-input"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="city" className="form-label">City</label>
                <input
                  id="city"
                  type="text"
                  placeholder="Chennai"
                  value={form.city}
                  onChange={(e) => update('city', e.target.value)}
                  className="form-input"
                />
              </div>
              <div>
                <label htmlFor="state" className="form-label">State</label>
                <input
                  id="state"
                  type="text"
                  placeholder="Tamil Nadu"
                  value={form.state}
                  onChange={(e) => update('state', e.target.value)}
                  className="form-input"
                />
              </div>
              <div>
                <label htmlFor="postalCode" className="form-label">Postal Code</label>
                <input
                  id="postalCode"
                  type="text"
                  placeholder="600001"
                  value={form.postalCode}
                  onChange={(e) => update('postalCode', e.target.value)}
                  className="form-input"
                />
              </div>
              <div>
                <label htmlFor="country" className="form-label">Country</label>
                <input
                  id="country"
                  type="text"
                  placeholder="India"
                  value={form.country}
                  onChange={(e) => update('country', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Submit */}
        <div className="flex flex-col sm:flex-row gap-3 justify-end pb-4">
          <Link href="/patients" className="btn-secondary">Cancel</Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-primary min-w-[160px]"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Registering...
              </span>
            ) : (
              'Register Patient'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
