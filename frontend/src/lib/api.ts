export function getApiBase(): string {
  if (typeof window === 'undefined') {
    // Server-side: Must communicate via internal docker network
    return process.env.INTERNAL_API_URL || 'http://backend:8000';
  }
  // Browser client-side: Hits host port or nginx
  const envUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  return envUrl.replace(/\/fhir\/?$/, '');
}

let _cachedToken: string | null = null;
export async function getAuthHeader(): Promise<Record<string, string>> {
  // Check client-side active session token first
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem('siru_access_token');
      if (stored) return { Authorization: `Bearer ${stored}` };
    } catch {
      // localStorage may fail in private mode
    }
  }

  if (_cachedToken) return { Authorization: `Bearer ${_cachedToken}` };
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'admin', password: 'admin123' }),
      cache: 'no-store',
    });
    if (res.ok) {
      const data = await res.json();
      _cachedToken = data.access_token;
      return { Authorization: `Bearer ${_cachedToken}` };
    }
  } catch (e) {
    // ignore
  }
  return {};
}

// ─── Patient ────────────────────────────────────────────────────────────────

export async function createPatient(data: Record<string, unknown>) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const res = await fetch(`${base}/fhir/Patient`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPatients(params?: Record<string, string>) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  const res = await fetch(`${base}/fhir/Patient${qs}`, {
    headers: { ...auth },
    cache: 'no-store'
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPatient(id: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const res = await fetch(`${base}/fhir/Patient/${id}`, {
    headers: { ...auth },
    cache: 'no-store'
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updatePatient(id: string, data: Record<string, unknown>) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const res = await fetch(`${base}/fhir/Patient/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...auth },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deletePatient(id: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const res = await fetch(`${base}/fhir/Patient/${id}`, {
    method: 'DELETE',
    headers: { ...auth }
  });
  if (!res.ok && res.status !== 204) throw new Error(await res.text());
}

// ─── Clinical / Phase 2 Resources ──────────────────────────────────────────

export async function getPatientEncounters(patientId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  try {
    const res = await fetch(`${base}/fhir/Encounter?patient=${patientId}`, {
      headers: { ...auth },
      cache: 'no-store'
    });
    if (!res.ok) return { total: 0, entry: [] };
    return await res.json();
  } catch (e) {
    return { total: 0, entry: [] };
  }
}

export async function getPatientObservations(patientId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  try {
    const res = await fetch(`${base}/fhir/Observation?patient=${patientId}`, {
      headers: { ...auth },
      cache: 'no-store'
    });
    if (!res.ok) return { total: 0, entry: [] };
    return await res.json();
  } catch (e) {
    return { total: 0, entry: [] };
  }
}

export async function getPatientConditions(patientId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  try {
    const res = await fetch(`${base}/fhir/Condition?patient=${patientId}`, {
      headers: { ...auth },
      cache: 'no-store'
    });
    if (!res.ok) return { total: 0, entry: [] };
    return await res.json();
  } catch (e) {
    return { total: 0, entry: [] };
  }
}

export async function getPatientMedications(patientId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  try {
    const res = await fetch(`${base}/fhir/MedicationRequest?patient=${patientId}`, {
      headers: { ...auth },
      cache: 'no-store'
    });
    if (!res.ok) return { total: 0, entry: [] };
    return await res.json();
  } catch (e) {
    return { total: 0, entry: [] };
  }
}

export async function getPatientAppointments(patientId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  try {
    const res = await fetch(`${base}/fhir/Appointment?patient=${patientId}`, {
      headers: { ...auth },
      cache: 'no-store'
    });
    if (!res.ok) return { total: 0, entry: [] };
    return await res.json();
  } catch (e) {
    return { total: 0, entry: [] };
  }
}

export async function createObservation(data: Record<string, unknown>) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const res = await fetch(`${base}/fhir/Observation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createEncounter(data: Record<string, unknown>) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const res = await fetch(`${base}/fhir/Encounter`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ─── Phase 4: Insurance, Eligibility & Claims ──────────────────────────────

export async function getPatientCoverages(patientId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  try {
    const res = await fetch(`${base}/fhir/Coverage?patient=${patientId}`, {
      headers: { ...auth },
      cache: 'no-store'
    });
    if (!res.ok) return { total: 0, entry: [] };
    return await res.json();
  } catch (e) {
    return { total: 0, entry: [] };
  }
}

export async function checkEligibility(coverageId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const res = await fetch(`${base}/fhir/Coverage/${coverageId}/eligibility-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth },
  });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function getPatientClaims(patientId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  try {
    const res = await fetch(`${base}/fhir/Claim?patient=${patientId}`, {
      headers: { ...auth },
      cache: 'no-store'
    });
    if (!res.ok) return { total: 0, entry: [] };
    return await res.json();
  } catch (e) {
    return { total: 0, entry: [] };
  }
}

export async function getPatientClaimResponses(patientId: string) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  try {
    const res = await fetch(`${base}/fhir/ClaimResponse?patient=${patientId}`, {
      headers: { ...auth },
      cache: 'no-store'
    });
    if (!res.ok) return { total: 0, entry: [] };
    return await res.json();
  } catch (e) {
    return { total: 0, entry: [] };
  }
}

export async function submitClaim(data: Record<string, unknown>) {
  const base = getApiBase();
  const auth = await getAuthHeader();
  const res = await fetch(`${base}/fhir/Claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...auth },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
