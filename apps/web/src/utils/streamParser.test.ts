import { describe, it, expect } from 'vitest';
import { parseStreamLine, parseStreamBuffer } from './streamParser';

describe('parseStreamLine', () => {
  it('parses SSE data: prefix with JSON', () => {
    const line = 'data: {"content": "Hello", "done": false}';
    const result = parseStreamLine(line);
    expect(result).toEqual({
      content: 'Hello',
      done: false,
      metadata: undefined,
    });
  });

  it('parses plain JSON line', () => {
    const line = '{"content": "World", "done": true}';
    const result = parseStreamLine(line);
    expect(result).toEqual({
      content: 'World',
      done: true,
      metadata: undefined,
    });
  });

  it('handles [DONE] signal', () => {
    expect(parseStreamLine('data: [DONE]')).toEqual({ done: true });
    expect(parseStreamLine('[DONE]')).toEqual({ done: true });
  });

  it('skips empty lines', () => {
    expect(parseStreamLine('')).toBeNull();
    expect(parseStreamLine('   ')).toBeNull();
  });

  it('skips SSE comments', () => {
    expect(parseStreamLine(': this is a comment')).toBeNull();
    expect(parseStreamLine(':ping')).toBeNull();
  });

  it('skips SSE event: lines', () => {
    expect(parseStreamLine('event: token')).toBeNull();
    expect(parseStreamLine('event: final')).toBeNull();
    expect(parseStreamLine('event: error')).toBeNull();
  });

  it('handles ok:false in error events', () => {
    const line = 'data: {"ok": false, "error": "Something went wrong"}';
    const result = parseStreamLine(line);
    expect(result?.error).toBe('Something went wrong');
  });

  it('handles ok:false without explicit error', () => {
    const line = 'data: {"ok": false}';
    const result = parseStreamLine(line);
    expect(result?.error).toBe('Request failed');
  });

  it('extracts metadata from response', () => {
    const line = 'data: {"content": "Test", "trace_id": "abc123", "provider": "mock", "env": "staging"}';
    const result = parseStreamLine(line);
    expect(result?.metadata).toEqual({
      trace_id: 'abc123',
      provider: 'mock',
      env: 'staging',
    });
  });

  it('extracts nested metadata', () => {
    const line = '{"content": "Test", "metadata": {"git_sha": "def456", "build_time": "2024-01-01"}}';
    const result = parseStreamLine(line);
    expect(result?.metadata).toEqual({
      git_sha: 'def456',
      build_time: '2024-01-01',
    });
  });

  it('handles alternative content field names', () => {
    expect(parseStreamLine('{"text": "Hello"}')?.content).toBe('Hello');
    expect(parseStreamLine('{"response": "World"}')?.content).toBe('World');
    expect(parseStreamLine('{"delta": {"content": "Foo"}}')?.content).toBe('Foo');
  });

  it('handles token field from SSE streaming responses', () => {
    // Backend sends {"token": "..."} for streaming
    expect(parseStreamLine('{"token": "Hello"}')?.content).toBe('Hello');
    expect(parseStreamLine('data: {"token": " world"}')?.content).toBe(' world');
  });

  it('treats invalid JSON as plain content', () => {
    const result = parseStreamLine('Hello World');
    expect(result).toEqual({ content: 'Hello World' });
  });
});

describe('parseStreamBuffer', () => {
  it('parses multiple lines and returns remainder', () => {
    const buffer = 'data: {"content": "One"}\ndata: {"content": "Two"}\ndata: {"cont';
    const { chunks, remainder } = parseStreamBuffer(buffer);

    expect(chunks).toHaveLength(2);
    expect(chunks[0].content).toBe('One');
    expect(chunks[1].content).toBe('Two');
    expect(remainder).toBe('data: {"cont');
  });

  it('handles buffer with complete lines only', () => {
    const buffer = '{"content": "Complete"}\n';
    const { chunks, remainder } = parseStreamBuffer(buffer);

    expect(chunks).toHaveLength(1);
    expect(chunks[0].content).toBe('Complete');
    expect(remainder).toBe('');
  });
});
