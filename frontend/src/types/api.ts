export interface ChatRequest {
  message: string;
  session_id?: string;
  message_type?: string;
  metadata?: Record<string, any>;
}

export interface ChatResponse {
  content: string;
  session_id: string;
  message_id: string;
  timestamp: string;
  status: string;
  metadata?: Record<string, any>;
  processing_time_ms?: number;
}

export interface SessionRequest {
  user_id: string;
  metadata?: Record<string, any>;
}

export interface SessionResponse {
  session_id: string;
  user_id: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  metadata?: Record<string, any>;
  status: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  uptime_seconds: number;
  components: Record<string, Record<string, any>>;
  memory_usage_mb?: number;
  cpu_usage_percent?: number;
}

export interface StatsResponse {
  total_sessions: number;
  active_sessions: number;
  total_messages: number;
  llm_providers: Record<string, Record<string, any>>;
  mcp_servers: Record<string, Record<string, any>>;
  average_response_time_ms: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  timestamp: string;
  type: 'user' | 'assistant';
  session_id: string;
  processing_time_ms?: number;
} 