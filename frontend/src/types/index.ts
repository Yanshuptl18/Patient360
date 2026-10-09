export type Role = 'admin' | 'reviewer' | 'researcher' | 'demo';

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
