export type Role =
  | 'admin'
  | 'reviewer'
  | 'researcher'
  | 'demo'
  | 'doctor'
  | 'clinician'
  | 'nurse'
  | 'hospital_admin'
  | 'patient';

export interface DemoRoleItem {
  key: string;
  name: string;
  title: string;
  email: string;
  role: string;
  department: string;
  description: string;
  avatar_initials: string;
}

export interface DemoRolesResponse {
  demo_mode: boolean;
  roles: DemoRoleItem[];
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ComponentHealth {
  status: 'UP' | 'DOWN';
  latency_ms: number;
  message: string;
}

export interface HealthResponse {
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  environment: string;
  version: string;
  uptime_seconds: number;
  timestamp: string;
  components: {
    database: ComponentHealth;
    vector_store: ComponentHealth;
    storage: ComponentHealth;
    llm_provider?: ComponentHealth;
  };
}

export interface PhaseInfo {
  number: number;
  name: string;
  status: 'Verified' | 'In Progress' | 'Planned';
  description: string;
  tag: string;
}

export type DocType = 'patient_record' | 'lab_report' | 'discharge_summary' | 'research_paper' | 'clinical_guideline';

export interface Patient {
  id: string;
  mrn_synthetic: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  primary_condition: string | null;
  created_at: string;
  updated_at: string;
  document_count?: number;
}

export interface PatientCreate {
  mrn_synthetic: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  primary_condition?: string;
}

export interface Document {
  id: string;
  patient_id: string | null;
  title: string;
  file_hash_sha256: string;
  file_size_bytes: number;
  mime_type: string;
  doc_type: DocType;
  doc_date: string | null;
  ingestion_status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number: number;
  content: string;
  raw_content: string;
  token_count: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface IngestionResponse {
  document_id: string;
  status: string;
  chunk_count: number;
  total_tokens: number;
  pages_processed: number;
  message: string;
}

export interface VectorSearchResultItem {
  chunk_id: string;
  document_id: string;
  patient_id: string | null;
  page_number: number;
  chunk_index: number;
  content: string;
  raw_content: string;
  score: number;
  doc_title: string;
  doc_type: string;
  doc_date: string | null;
}

export interface VectorStatsResponse {
  collection_name: string;
  status: string;
  vectors_count: number;
  indexed_vectors_count: number;
  dimensions: number;
  is_embedded: boolean;
}

export interface CitationItem {
  document_id: string;
  document_title: string;
  page_number: number;
  exact_quote: string;
  claim_text: string;
  verification_status: 'supported' | 'partially_supported' | 'unsupported';
}

export interface RetrievalMetadata {
  dense_candidates_count: number;
  sparse_candidates_count: number;
  merged_candidates_count: number;
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  is_abstention: boolean;
}

export interface RAGQueryResponse {
  query: string;
  patient_id: string;
  answer: string;
  citations: CitationItem[];
  limitations: string[];
  confidence_score: number;
  retrieval_metadata: RetrievalMetadata;
}

export interface RAGFeedbackRequest {
  patient_id: string;
  query: string;
  answer: string;
  rating: 'positive' | 'negative';
  issue_type?: string | null;
  comment?: string | null;
}

export type ClinicalEventType =
  | 'diagnosis'
  | 'medication'
  | 'procedure'
  | 'encounter'
  | 'lab_result'
  | 'allergy';

export type DatePrecision = 'day' | 'month' | 'year' | 'approximate';

export type ClinicalStatus = 'active' | 'historical' | 'resolved' | 'disputed';

export interface ClinicalEvent {
  id: string;
  patient_id: string;
  document_id: string;
  chunk_id?: string | null;
  event_type: ClinicalEventType;
  event_date: string;
  event_date_precision: DatePrecision;
  document_date?: string | null;
  description: string;
  value_or_dosage?: string | null;
  clinical_status: ClinicalStatus;
  confidence_score: number;
  contradiction_flag: boolean;
  contradiction_details?: string | null;
  created_at: string;
  document_title?: string | null;
  page_number?: number | null;
  exact_quote?: string | null;
}

export interface ContradictionItem {
  event_id_1: string;
  event_id_2: string;
  event_1_summary: string;
  event_2_summary: string;
  document_title_1: string;
  document_title_2: string;
  page_number_1?: number | null;
  page_number_2?: number | null;
  conflict_type:
    | 'allergy_conflict'
    | 'status_conflict'
    | 'date_conflict'
    | 'value_conflict'
    | 'general_conflict';
  severity: 'critical' | 'moderate' | 'minor';
  explanation: string;
  suggested_resolution?: string | null;
}

export interface TimelineSummary {
  total_events: number;
  event_counts_by_type: Record<string, number>;
  earliest_date?: string | null;
  latest_date?: string | null;
  total_contradictions: number;
}

export interface PatientTimelineResponse {
  patient_id: string;
  patient_name: string;
  summary: TimelineSummary;
  contradictions: ContradictionItem[];
  events: ClinicalEvent[];
}

export interface TimelineExtractResponse {
  patient_id: string;
  events_extracted_count: number;
  contradictions_detected_count: number;
  documents_processed_count: number;
  status: string;
  message: string;
}

export type WorkflowStatus =
  | 'planning'
  | 'executing'
  | 'awaiting_approval'
  | 'completed'
  | 'iteration_limit_reached'
  | 'timeout_exceeded'
  | 'rejected'
  | 'failed';

export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface WorkflowStepLog {
  step_index: number;
  node_name: string;
  thought: string;
  action_tool?: string | null;
  tool_input?: Record<string, unknown> | null;
  tool_output?: unknown | null;
  timestamp_iso: string;
}

export interface AgentRunSnapshot {
  run_id: string;
  patient_id: string;
  patient_name?: string | null;
  query: string;
  status: WorkflowStatus;
  iteration_count: number;
  max_iterations: number;
  elapsed_seconds: number;
  plan: string[];
  steps: WorkflowStepLog[];
  retrieved_evidence_count: number;
  contradictions_found: Array<{
    contradiction_id: string;
    topic: string;
    conflict_type: string;
    severity: string;
    description: string;
    event_ids: string[];
    resolution_recommendation: string;
  }>;
  draft_synthesis?: string | null;
  final_report?: string | null;
  approval_status: ApprovalStatus;
  clinician_feedback?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentApprovalRequest {
  approved: boolean;
  feedback?: string | null;
}

export interface AgentApprovalResponse {
  run_id: string;
  status: WorkflowStatus;
  approval_status: ApprovalStatus;
  message: string;
  final_report?: string | null;
}

export type EvidenceStrength = 'High' | 'Moderate' | 'Low-Moderate' | 'Preliminary';

export interface ResearchStudy {
  id: string;
  document_id: string;
  pmid?: string | null;
  doi?: string | null;
  title: string;
  authors?: string | null;
  publication_date?: string | null;
  study_design?: string | null;
  population_description?: string | null;
  sample_size?: number | null;
  intervention?: string | null;
  primary_outcome?: string | null;
  limitations?: string | null;
  created_at: string;
}

export interface StudyMatrixRow {
  study_id: string;
  title: string;
  doi?: string | null;
  pmid?: string | null;
  authors?: string | null;
  publication_year?: number | null;
  study_design?: string | null;
  sample_size?: number | null;
  population?: string | null;
  intervention?: string | null;
  primary_outcome?: string | null;
  limitations?: string | null;
  evidence_strength: EvidenceStrength;
}

export interface StudyComparisonMatrix {
  comparison_topic: string;
  studies_count: number;
  matrix_rows: StudyMatrixRow[];
  synthesized_findings: string;
  guideline_alignment?: string | null;
}

export interface DossierExportResponse {
  title: string;
  markdown_content: string;
  studies_included_count: number;
  generated_at_iso: string;
}

export type BenchmarkCategory =
  | 'single_doc_factual'
  | 'multi_doc_longitudinal'
  | 'contradictory_records'
  | 'unanswerable_abstention'
  | 'adversarial_injection'
  | 'research_matrix';

export interface EvaluationBenchmarkItem {
  id: string;
  category: BenchmarkCategory;
  title: string;
  query: string;
  patient_id?: string | null;
  expected_golden_chunk_ids: string[];
  expected_answer_keywords: string[];
  forbidden_keywords: string[];
  should_abstain: boolean;
  has_contradiction: boolean;
  is_adversarial: boolean;
}

export interface EvaluationItemResult {
  item_id: string;
  category: string;
  query: string;
  retrieved_chunk_ids: string[];
  generated_answer: string;
  citations: Array<{
    document_id: string;
    page_number: number;
    verification_status?: string;
  }>;
  hit_at_5: boolean;
  reciprocal_rank: number;
  faithfulness_score: number;
  citation_precision_score: number;
  abstention_correct: boolean;
  passed: boolean;
  retrieval_latency_ms: number;
  e2e_latency_ms: number;
  failure_reason?: string | null;
}

export interface EvaluationCategorySummary {
  category: string;
  category_label: string;
  total_items: number;
  passed_items: number;
  pass_rate: number;
  avg_faithfulness: number;
  avg_citation_precision: number;
  avg_mrr: number;
}

export interface EvaluationRunSummary {
  id: string;
  name: string;
  git_commit: string;
  mode: string;
  total_items: number;
  passed_items: number;
  recall_at_5: number;
  mrr: number;
  faithfulness: number;
  citation_precision: number;
  abstention_accuracy: number;
  p95_retrieval_latency_ms: number;
  p95_e2e_latency_ms: number;
  created_at: string;
}

export interface EvaluationTargetMetric {
  target: string;
  achieved: string | number;
  met: boolean;
}

export interface EvaluationRun extends EvaluationRunSummary {
  summary_metrics: {
    mode: string;
    git_commit: string;
    total_items: number;
    passed_items: number;
    pass_rate: number;
    categories: Record<string, EvaluationCategorySummary>;
    targets: Record<string, EvaluationTargetMetric>;
  };
  item_results: EvaluationItemResult[];
}




