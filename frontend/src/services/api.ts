/**
 * Centralized, typed Axios API client for Patient360.
 * Handles authentication header injection, centralized error parsing,
 * network resilience, and structured responses across all clinical workflows.
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import {
  User,
  LoginResponse,
  Patient,
  PatientCreate,
  Document,
  DocumentChunk,
  IngestionResponse,
  RAGQueryResponse,
  RAGFeedbackRequest,
  PatientTimelineResponse,
  TimelineExtractResponse,
  AgentRunSnapshot,
  AgentApprovalResponse,
  ResearchStudy,
  StudyComparisonMatrix,
  DossierExportResponse,
  EvaluationRun,
  EvaluationRunSummary,
  HealthResponse,
  VectorStatsResponse,
} from '../types';

const API_BASE_URL = (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL || '';

export class ApiError extends Error {
  statusCode: number;
  code?: string;
  details?: unknown;

  constructor(message: string, statusCode: number = 500, code?: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
  }
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: Inject JWT token into Authorization header
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('patient360_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: unknown) => Promise.reject(error)
);

// Interceptor: Standardize API errors and handle 401s
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string | unknown[]; message?: string; code?: string }>) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;

      // Parse error message
      let message = 'An unexpected server error occurred.';
      if (typeof data?.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data?.detail) && data.detail.length > 0) {
        message = (data.detail[0] as { msg?: string }).msg || JSON.stringify(data.detail);
      } else if (data?.message) {
        message = data.message;
      } else if (status === 401) {
        message = 'Authentication required or session expired.';
      } else if (status === 403) {
        message = 'Access denied. You lack required authorization for this patient record.';
      } else if (status === 404) {
        message = 'Requested clinical resource was not found.';
      }

      if (status === 401) {
        window.dispatchEvent(new CustomEvent('patient360:auth-expired'));
      }

      return Promise.reject(new ApiError(message, status, data?.code, data));
    }

    if (error.request) {
      return Promise.reject(
        new ApiError(
          'Network error: Unable to reach the clinical API server. Please check your connection.',
          0,
          'NETWORK_ERROR'
        )
      );
    }

    return Promise.reject(new ApiError(error.message || 'Client error occurred.', 0));
  }
);

export const api = {
  // --- Auth Services ---
  auth: {
    async login(email: string, password?: string): Promise<LoginResponse> {
      const { data } = await apiClient.post<LoginResponse>('/api/v1/auth/login', {
        email,
        password: password || 'demo123456',
      });
      return data;
    },
    async getMe(): Promise<User> {
      const { data } = await apiClient.get<User>('/api/v1/auth/me');
      return data;
    },
    async refreshToken(refreshToken: string): Promise<LoginResponse> {
      const { data } = await apiClient.post<LoginResponse>('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });
      return data;
    },
  },

  // --- Patient Services ---
  patients: {
    async list(params?: { search?: string; limit?: number; skip?: number }): Promise<Patient[]> {
      const query = new URLSearchParams();
      if (params?.search) query.append('search', params.search);
      if (params?.limit) query.append('limit', String(params.limit));
      if (params?.skip) query.append('skip', String(params.skip));
      const queryString = query.toString() ? `?${query.toString()}` : '';

      const { data } = await apiClient.get<Patient[]>(`/api/v1/patients${queryString}`);
      return data;
    },
    async get(id: string): Promise<Patient> {
      const { data } = await apiClient.get<Patient>(`/api/v1/patients/${id}`);
      return data;
    },
    async create(payload: PatientCreate): Promise<Patient> {
      const { data } = await apiClient.post<Patient>('/api/v1/patients', payload);
      return data;
    },
    async delete(id: string): Promise<{ success: boolean; message: string }> {
      const { data } = await apiClient.delete<{ success: boolean; message: string }>(`/api/v1/patients/${id}`);
      return data;
    },
  },

  // --- Document Ingestion & Storage ---
  documents: {
    async list(patientId?: string): Promise<Document[]> {
      const query = patientId ? `?patient_id=${patientId}` : '';
      const { data } = await apiClient.get<Document[]>(`/api/v1/documents${query}`);
      return data;
    },
    async upload(formData: FormData): Promise<Document> {
      const { data } = await apiClient.post<Document>('/api/v1/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
    async ingest(docId: string): Promise<IngestionResponse> {
      const { data } = await apiClient.post<IngestionResponse>(`/api/v1/documents/${docId}/ingest`);
      return data;
    },
    async getChunks(docId: string): Promise<DocumentChunk[]> {
      const { data } = await apiClient.get<DocumentChunk[]>(`/api/v1/documents/${docId}/chunks`);
      return data;
    },
    getDownloadUrl(docId: string): string {
      return `/api/v1/documents/${docId}/file`;
    },
    async getVectorStats(): Promise<VectorStatsResponse> {
      const { data } = await apiClient.get<VectorStatsResponse>('/api/v1/vector/stats');
      return data;
    },
  },

  // --- Evidence-Grounded RAG ---
  rag: {
    async query(queryText: string, patientId: string, topK: number = 5): Promise<RAGQueryResponse> {
      const { data } = await apiClient.post<RAGQueryResponse>('/api/v1/rag/query', {
        query: queryText,
        patient_id: patientId,
        top_k: topK,
      });
      return data;
    },
    async submitFeedback(payload: RAGFeedbackRequest): Promise<{ status: string }> {
      const { data } = await apiClient.post<{ status: string }>('/api/v1/rag/feedback', payload);
      return data;
    },
  },

  // --- Clinical Timeline & Contradiction Detection ---
  timeline: {
    async getTimeline(
      patientId: string,
      params?: { eventType?: string; startDate?: string; endDate?: string }
    ): Promise<PatientTimelineResponse> {
      const query = new URLSearchParams();
      if (params?.eventType && params.eventType !== 'all') query.append('event_type', params.eventType);
      if (params?.startDate) query.append('start_date', params.startDate);
      if (params?.endDate) query.append('end_date', params.endDate);
      const queryString = query.toString() ? `?${query.toString()}` : '';

      const { data } = await apiClient.get<PatientTimelineResponse>(
        `/api/v1/timeline/patients/${patientId}${queryString}`
      );
      return data;
    },
    async extractEvents(patientId: string, documentIds?: string[]): Promise<TimelineExtractResponse> {
      const { data } = await apiClient.post<TimelineExtractResponse>(
        `/api/v1/timeline/patients/${patientId}/extract`,
        { document_ids: documentIds }
      );
      return data;
    },
  },

  // --- LangGraph Research Agent Workflows ---
  agents: {
    async startRun(patientId: string, queryText: string, maxIterations: number = 5): Promise<AgentRunSnapshot> {
      const { data } = await apiClient.post<AgentRunSnapshot>('/api/v1/agents/runs', {
        patient_id: patientId,
        query: queryText,
        max_iterations: maxIterations,
      });
      return data;
    },
    async getRun(runId: string): Promise<AgentRunSnapshot> {
      const { data } = await apiClient.get<AgentRunSnapshot>(`/api/v1/agents/runs/${runId}`);
      return data;
    },
    async listRuns(patientId: string): Promise<AgentRunSnapshot[]> {
      const { data } = await apiClient.get<AgentRunSnapshot[]>(`/api/v1/agents/patients/${patientId}/runs`);
      return data;
    },
    async reviewRun(runId: string, approved: boolean, feedback?: string): Promise<AgentApprovalResponse> {
      const { data } = await apiClient.post<AgentApprovalResponse>(`/api/v1/agents/runs/${runId}/review`, {
        approved,
        feedback: feedback || null,
      });
      return data;
    },
  },

  // --- Biomedical Literature & PICO Research ---
  research: {
    async listStudies(): Promise<ResearchStudy[]> {
      const { data } = await apiClient.get<ResearchStudy[]>('/api/v1/research/studies');
      return data;
    },
    async getMatrix(studyIds?: string[]): Promise<StudyComparisonMatrix> {
      const query = new URLSearchParams();
      if (studyIds && studyIds.length > 0) {
        studyIds.forEach((id) => query.append('study_ids', id));
      }
      const queryString = query.toString() ? `?${query.toString()}` : '';
      const { data } = await apiClient.get<StudyComparisonMatrix>(`/api/v1/research/matrix${queryString}`);
      return data;
    },
    async exportSummary(studyIds?: string[]): Promise<DossierExportResponse> {
      const query = new URLSearchParams();
      if (studyIds && studyIds.length > 0) {
        studyIds.forEach((id) => query.append('study_ids', id));
      }
      const queryString = query.toString() ? `?${query.toString()}` : '';
      const { data } = await apiClient.get<DossierExportResponse>(`/api/v1/research/matrix/export${queryString}`);
      return data;
    },
  },

  // --- RAG Evaluation Lab ---
  evaluation: {
    async runBenchmark(datasetType: string = 'synthetic_golden'): Promise<EvaluationRun> {
      const { data } = await apiClient.post<EvaluationRun>('/api/v1/evaluation/run', {
        dataset_type: datasetType,
      });
      return data;
    },
    async getHistory(limit: number = 15): Promise<EvaluationRun[]> {
      const { data } = await apiClient.get<EvaluationRun[]>(`/api/v1/evaluation/runs?limit=${limit}`);
      return data;
    },
    async getSummary(): Promise<EvaluationRunSummary | null> {
      const { data } = await apiClient.get<EvaluationRunSummary | null>('/api/v1/evaluation/summary');
      return data;
    },
  },

  // --- System Diagnostics & Telemetry ---
  system: {
    async getHealth(): Promise<HealthResponse> {
      const { data } = await apiClient.get<HealthResponse>('/api/v1/health');
      return data;
    },
  },
};

export default api;
