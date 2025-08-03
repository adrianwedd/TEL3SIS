export interface Call {
  id: string;
  from_number: string;
  to_number: string;
  summary?: string;
  sentiment?: number;
  created_at: string;
  duration?: number;
  status: 'active' | 'completed' | 'failed';
}

export interface CallDetail extends Call {
  transcript: string;
  tool_calls?: ToolCall[];
  escalation?: boolean;
}

export interface ToolCall {
  id: string;
  tool_name: string;
  arguments: Record<string, any>;
  result?: any;
  timestamp: string;
}

export interface AgentStatus {
  state: 'online' | 'offline' | 'busy' | 'error';
  last_activity?: string;
  active_calls: number;
  total_calls_today: number;
}

export interface WebSocketMessage {
  event: 'agent_state' | 'call_update' | 'system_alert';
  data: any;
  timestamp: string;
}

export interface User {
  id: string;
  username: string;
  role: 'admin' | 'operator' | 'viewer';
  last_login?: string;
}

export interface ApiResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface SearchFilters {
  query?: string;
  from_date?: string;
  to_date?: string;
  sentiment_min?: number;
  sentiment_max?: number;
  status?: Call['status'];
}