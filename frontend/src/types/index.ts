export type FactCategory = 'laboratory' | 'medication' | 'instruction' | 'general';

export type FlagType = 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL' | 'ABNORMAL' | 'NONE';

export type VerificationStatus = 'VERIFIED' | 'PARTIALLY_VERIFIED' | 'NEEDS_REVIEW' | 'BLOCKED';

export interface BoundingBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  page?: number;
}

export interface MedicalFact {
  field_id: string;
  category: FactCategory;
  name: string;
  value?: number | string | null;
  value_type?: string;
  unit?: string | null;
  reference_range?: string | null;
  flag?: FlagType | null;
  strength?: string | null;
  dosage?: string | null;
  frequency?: string | null;
  route?: string | null;
  duration?: string | null;
  action?: string | null;
  negation: boolean;
  condition?: string | null;
  timing?: string | null;
  instruction_text?: string | null;
  source_text: string;
  page?: number;
  bbox?: BoundingBox | null;
  confidence: number;
  user_confirmed?: boolean;
  edited?: boolean;
}

export interface FieldComparison {
  field_id: string;
  field_name: string;
  category: FactCategory;
  original_display: string;
  explanation_display: string;
  status: 'PASS' | 'MISMATCH' | 'NEEDS_REVIEW' | 'MISSING';
  mismatch_type?: string | null;
  is_critical: boolean;
  details: string;
  source_text?: string | null;
  explanation_source_text?: string | null;
}

export interface VerificationResult {
  overall_status: VerificationStatus;
  fidelity_score: number;
  total_fields_checked: number;
  passed_count: number;
  review_count: number;
  critical_mismatches_count: number;
  field_comparisons: FieldComparison[];
  blocked_reason?: string | null;
  what_readback_could_not_verify: string[];
  explanation_safe_to_display: boolean;
}

export interface ProviderContact {
  provider_name: string;
  phone?: string;
  email?: string;
  clinic_or_hospital?: string;
  notes?: string;
}

export interface VerifiedNextStep {
  has_next_step: boolean;
  service_name?: string | null;
  timing?: string | null;
  department_or_specialty?: string | null;
  source_text?: string | null;
  page?: number | null;
  is_explicit: boolean;
  verification_status: 'VERIFIED' | 'NO_EXPLICIT_INSTRUCTION' | 'UNSUPPORTED_REJECTED' | 'UNVERIFIED';
  rationale: string;
  saved_provider?: ProviderContact | null;
}

export interface DocumentDetail {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  document_type: string;
  page_count: number;
  ocr_quality: number;
  created_at: string;
  updated_at: string;
  raw_text?: string | null;
  extracted_facts: MedicalFact[];
  confirmed_facts: MedicalFact[];
  selected_language: string;
  explanation_text?: string | null;
  explanation_pending_verification?: boolean;
  verification_result?: VerificationResult | null;
  next_step?: VerifiedNextStep | null;
  saved_provider?: ProviderContact | null;
}

export type FidelityFailureType =
  | 'numeric_value_changed'
  | 'unit_changed'
  | 'drug_name_changed'
  | 'dosage_changed'
  | 'frequency_changed'
  | 'negation_flipped'
  | 'abnormal_flag_changed'
  | 'important_fact_omitted';

export interface FidelitySimulationResponse {
  document_id: string;
  demo_label: string;
  failure_type: FidelityFailureType;
  original_explanation: string;
  simulated_explanation: string;
  original_facts: MedicalFact[];
  reextracted_facts: MedicalFact[];
  verification_result: VerificationResult;
}

export type DocumentSummary = Pick<
  DocumentDetail,
  'id' | 'filename' | 'file_type' | 'file_size' | 'document_type' | 'page_count' | 'ocr_quality' | 'created_at' | 'updated_at'
> & {
  verification_result?: VerificationResult | null;
};

export interface ConflictItem {
  field_name: string;
  category: string;
  doc_a_value: string;
  doc_b_value: string;
  doc_a_name: string;
  doc_b_name: string;
  conflict_type: string;
  warning_message: string;
}

export interface DocumentComparisonResult {
  has_conflicts: boolean;
  conflicts: ConflictItem[];
  timeline: Array<Record<string, any>>;
  summary: string;
}

export interface EvaluationMetrics {
  numeric_error_rate: number;
  unit_error_rate: number;
  drug_corruption_rate: number;
  dosage_error_rate: number;
  frequency_error_rate: number;
  negation_flip_rate: number;
  omitted_abnormal_flag_rate: number;
  verifier_catch_rate: number;
  false_block_rate: number;
  average_document_fidelity: number;
  total_test_cases: number;
  total_blocked_count: number;
  total_verified_count: number;
}

export interface LanguageBreakdown {
  language: string;
  language_name: string;
  fidelity_score: number;
  numeric_fidelity: number;
  unit_fidelity: number;
  drug_fidelity: number;
  dosage_fidelity: number;
  frequency_fidelity: number;
  negation_fidelity: number;
  flag_fidelity: number;
  test_cases_count: number;
}

export interface EvaluationRunResponse {
  run_id: string;
  timestamp: string;
  dataset_size: number;
  comparison: {
    baseline_metrics: EvaluationMetrics;
    readback_metrics: EvaluationMetrics;
  };
  language_breakdown: LanguageBreakdown[];
  category_breakdown: Record<string, Record<string, number>>;
  recent_failures: Array<{
    document_id: string;
    type: string;
    mismatch: string;
    fidelity_score: number;
    status: string;
    reason: string;
  }>;
}

export interface DashboardMetrics {
  documents_analyzed: number;
  verified_explanations: number;
  blocked_explanations: number;
  needs_review: number;
  average_document_fidelity: number;
  recent_audit_events: Array<{
    id: string;
    document_id?: string;
    event_type: string;
    timestamp: string;
    details: Record<string, any>;
  }>;
}
