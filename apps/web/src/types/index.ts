export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  metadata?: ResponseMetadata;
}

export interface ResponseMetadata {
  trace_id?: string;
  provider?: string;
  env?: string;
  git_sha?: string;
  build_time?: string;
  model?: string;
  tokens_used?: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  trace_id?: string;
  provider?: string;
  metadata?: ResponseMetadata;
}

export interface HealthResponse {
  status: string;
  env?: string;
  timestamp?: string;
}

export interface StreamChunk {
  content?: string;
  done?: boolean;
  metadata?: ResponseMetadata;
  error?: string;
}
