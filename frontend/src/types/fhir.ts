export interface HumanName {
  use?: string;
  family?: string;
  given?: string[];
  text?: string;
  prefix?: string[];
  suffix?: string[];
}

export interface ContactPoint {
  system?: string;
  value?: string;
  use?: string;
}

export interface Address {
  use?: string;
  line?: string[];
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
}

export interface Coding {
  system?: string;
  code?: string;
  display?: string;
}

export interface CodeableConcept {
  coding?: Coding[];
  text?: string;
}

export interface Reference {
  reference?: string;
  display?: string;
  type?: string;
}

export interface Quantity {
  value?: number;
  unit?: string;
  system?: string;
  code?: string;
}

export interface FHIRPatient {
  resourceType: 'Patient';
  id?: string;
  meta?: {
    versionId?: string;
    lastUpdated?: string;
  };
  active?: boolean;
  name?: HumanName[];
  telecom?: ContactPoint[];
  gender?: 'male' | 'female' | 'other' | 'unknown';
  birthDate?: string;
  address?: Address[];
}

export interface FHIRPractitioner {
  resourceType: 'Practitioner';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  active?: boolean;
  name?: HumanName[];
  gender?: string;
  qualification?: Array<{ code?: CodeableConcept }>;
}

export interface FHIREncounter {
  resourceType: 'Encounter';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  status?: string;
  class?: { code?: string; display?: string };
  subject?: Reference;
  participant?: Array<{ individual?: Reference }>;
  period?: { start?: string; end?: string };
  reasonCode?: CodeableConcept[];
  serviceProvider?: Reference;
}

export interface FHIRObservation {
  resourceType: 'Observation';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  status?: string;
  category?: CodeableConcept[];
  code: CodeableConcept;
  subject?: Reference;
  encounter?: Reference;
  effectiveDateTime?: string;
  valueQuantity?: Quantity;
  valueString?: string;
  component?: Array<{
    code: CodeableConcept;
    valueQuantity?: Quantity;
    valueString?: string;
  }>;
}

export interface FHIRCondition {
  resourceType: 'Condition';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  clinicalStatus?: CodeableConcept;
  verificationStatus?: CodeableConcept;
  code: CodeableConcept;
  subject?: Reference;
  encounter?: Reference;
  onsetDateTime?: string;
}

export interface FHIRMedicationRequest {
  resourceType: 'MedicationRequest';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  status?: string;
  intent?: string;
  medicationCodeableConcept: CodeableConcept;
  subject?: Reference;
  encounter?: Reference;
  authoredOn?: string;
  requester?: Reference;
  dosageInstruction?: Array<{ text?: string }>;
}

export interface FHIRAppointment {
  resourceType: 'Appointment';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  status?: string;
  description?: string;
  start?: string;
  end?: string;
  participant?: Array<{ actor?: Reference; status?: string }>;
}

export interface FHIRBundle<T = any> {
  resourceType: 'Bundle';
  total: number;
  entry?: Array<{
    fullUrl: string;
    resource: T;
  }>;
}

export interface FHIRCoverage {
  resourceType: 'Coverage';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  status: string;
  type?: CodeableConcept;
  subscriberId?: string;
  beneficiary?: Reference;
  period?: { start?: string; end?: string };
  payor?: Reference[];
  class?: Array<{ type?: CodeableConcept; value?: string; name?: string }>;
  costToBeneficiary?: Array<{ type?: CodeableConcept; valueMoney?: { value?: number; currency?: string } }>;
}

export interface FHIRClaim {
  resourceType: 'Claim';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  status: string;
  type?: CodeableConcept;
  use: string;
  patient?: Reference;
  created?: string;
  provider?: Reference;
  facility?: Reference;
  insurance?: Array<{ sequence?: number; focal?: boolean; coverage?: Reference }>;
  diagnosis?: Array<{ sequence?: number; diagnosisReference?: Reference }>;
  item?: Array<{
    sequence?: number;
    productOrService?: CodeableConcept;
    unitPrice?: { value?: number; currency?: string };
    net?: { value?: number; currency?: string };
  }>;
  total?: { value?: number; currency?: string };
}

export interface FHIRClaimResponse {
  resourceType: 'ClaimResponse';
  id?: string;
  meta?: { versionId?: string; lastUpdated?: string };
  status: string;
  type?: CodeableConcept;
  use: string;
  patient?: Reference;
  created?: string;
  insurer?: Reference;
  request?: Reference;
  outcome: string;
  disposition?: string;
  total?: Array<{
    category?: CodeableConcept;
    amount?: { value?: number; currency?: string };
  }>;
  item?: Array<{
    itemSequence?: number;
    adjudication?: Array<{
      category?: CodeableConcept;
      amount?: { value?: number; currency?: string };
      reason?: { text?: string };
    }>;
  }>;
}

export interface EligibilityResult {
  eligible: boolean;
  status: string;
  planName: string;
  subscriberId: string;
  copayPercent: number;
  coinsuranceBenefit: number;
  remainingDeductible?: { value: number; currency: string };
  inNetwork: boolean;
  disposition: string;
  verifiedAt: string;
}

