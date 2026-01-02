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

/**
 * Message in a conversation (matches backend Message model).
 */
export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

/**
 * Request for chat completion (matches backend ChatRequest model).
 */
export interface ChatRequest {
  messages: Message[];
  session_id?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Runtime metadata from backend response.
 */
export interface RuntimeMetadata {
  trace_id: string;
  provider: string;
  env: string;
  git_sha: string;
  build_time: string;
}

/**
 * Response from chat completion (matches backend ChatResponse model).
 */
export interface ChatResponse {
  ok: boolean;
  session_id: string;
  message: Message;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  metadata?: Record<string, unknown>;
  runtime?: RuntimeMetadata;
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
