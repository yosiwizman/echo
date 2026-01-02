import type { StreamChunk, ResponseMetadata } from '../types';

/**
 * Parse a single line from a streaming response.
 * Handles SSE-style "event: <type>" and "data: {...}" lines, plus plain JSON.
 *
 * @param line - A single line from the stream
 * @returns Parsed StreamChunk or null if line should be skipped
 */
export function parseStreamLine(line: string): StreamChunk | null {
  const trimmed = line.trim();

  // Skip empty lines
  if (!trimmed) {
    return null;
  }

  // Skip SSE comments
  if (trimmed.startsWith(':')) {
    return null;
  }

  // Skip SSE "event:" lines (we handle type from data payload)
  if (trimmed.startsWith('event:')) {
    return null;
  }

  // Handle SSE "data:" prefix
  let jsonStr = trimmed;
  if (trimmed.startsWith('data:')) {
    jsonStr = trimmed.slice(5).trim();
  }

  // Handle SSE "[DONE]" signal
  if (jsonStr === '[DONE]') {
    return { done: true };
  }

  // Skip empty data
  if (!jsonStr) {
    return null;
  }

  try {
    const parsed = JSON.parse(jsonStr);

    // Normalize different response formats
    const chunk: StreamChunk = {
      content: parsed.content ?? parsed.text ?? parsed.response ?? parsed.delta?.content,
      done: parsed.done ?? parsed.finished ?? false,
      metadata: extractMetadata(parsed),
    };

    // Handle error events
    if (parsed.error) {
      chunk.error = parsed.error;
    }

    // Handle 'ok' field from final events
    if (parsed.ok === false) {
      chunk.error = parsed.error || 'Request failed';
    }

    return chunk;
  } catch {
    // If it's not valid JSON, treat the whole line as content (fallback)
    return { content: jsonStr };
  }
}

/**
 * Extract metadata from a parsed response object
 */
function extractMetadata(parsed: Record<string, unknown>): ResponseMetadata | undefined {
  const metadata: ResponseMetadata = {};

  if (parsed.trace_id) metadata.trace_id = String(parsed.trace_id);
  if (parsed.provider) metadata.provider = String(parsed.provider);
  if (parsed.env) metadata.env = String(parsed.env);
  if (parsed.git_sha) metadata.git_sha = String(parsed.git_sha);
  if (parsed.build_time) metadata.build_time = String(parsed.build_time);
  if (parsed.model) metadata.model = String(parsed.model);
  if (parsed.tokens_used) metadata.tokens_used = Number(parsed.tokens_used);

  // Also check nested metadata object
  if (parsed.metadata && typeof parsed.metadata === 'object') {
    const nested = parsed.metadata as Record<string, unknown>;
    if (nested.trace_id) metadata.trace_id = String(nested.trace_id);
    if (nested.provider) metadata.provider = String(nested.provider);
    if (nested.env) metadata.env = String(nested.env);
    if (nested.git_sha) metadata.git_sha = String(nested.git_sha);
    if (nested.build_time) metadata.build_time = String(nested.build_time);
    if (nested.model) metadata.model = String(nested.model);
    if (nested.tokens_used) metadata.tokens_used = Number(nested.tokens_used);
  }

  return Object.keys(metadata).length > 0 ? metadata : undefined;
}

/**
 * Process multiple lines from a stream buffer
 */
export function parseStreamBuffer(buffer: string): {
  chunks: StreamChunk[];
  remainder: string;
} {
  const lines = buffer.split('\n');
  const remainder = lines.pop() ?? ''; // Last element might be incomplete
  const chunks: StreamChunk[] = [];

  for (const line of lines) {
    const chunk = parseStreamLine(line);
    if (chunk) {
      chunks.push(chunk);
    }
  }

  return { chunks, remainder };
}
