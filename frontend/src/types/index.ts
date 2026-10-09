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
