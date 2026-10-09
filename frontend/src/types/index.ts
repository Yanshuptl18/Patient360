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
