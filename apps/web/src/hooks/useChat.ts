import { useState, useCallback, useEffect, useRef } from 'react';
import type { ChatMessage, ResponseMetadata, ChatResponse } from '../types';
import { BACKEND_URLS, API_ENDPOINTS, type Environment } from '../config';
import { parseStreamBuffer } from '../utils/streamParser';

const STORAGE_KEY = 'echo-chat-messages';
const SESSION_KEY = 'echo-session-id';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function loadMessages(): ChatMessage[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveMessages(messages: ChatMessage[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  } catch {
    // Ignore storage errors
  }
}

function loadSessionId(): string {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) return stored;
    const newId = generateId();
    localStorage.setItem(SESSION_KEY, newId);
    return newId;
  } catch {
    return generateId();
  }
}

export function useChat(
  environment: Environment,
  streamingEnabled: boolean,
  authToken: string | null = null,
  onAuthRequired?: () => void
) {
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionId = useRef(loadSessionId());
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // Use ref to always get the latest authToken value in callbacks
  // This avoids stale closure issues when token changes after login
  const authTokenRef = useRef(authToken);
  authTokenRef.current = authToken;

  // Persist messages to localStorage
  useEffect(() => {
    saveMessages(messages);
  }, [messages]);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setError(null);
      setIsLoading(true);

      // Add user message
      const userMessage: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: content.trim(),
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage]);

      // Create placeholder for assistant message
      const assistantId = generateId();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      const baseUrl = BACKEND_URLS[environment];
      const endpoint = streamingEnabled ? API_ENDPOINTS.chatStream : API_ENDPOINTS.chat;
      const url = `${baseUrl}${endpoint}`;

      abortControllerRef.current = new AbortController();

      try {
        // Read token from ref to ensure we always have the latest value
        const currentToken = authTokenRef.current;
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (currentToken) {
          headers['Authorization'] = `Bearer ${currentToken}`;
        }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          messages: [{ role: 'user', content: content.trim() }],
          session_id: sessionId.current,
        }),
        credentials: 'omit',
        mode: 'cors',
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        // Handle 401 - auth required
        if (response.status === 401 && onAuthRequired) {
          onAuthRequired();
          throw new Error('Authentication required');
        }

        // Try to extract FastAPI error detail
        let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorBody = await response.json();
          if (errorBody.detail) {
            errorDetail = typeof errorBody.detail === 'string'
              ? errorBody.detail
              : JSON.stringify(errorBody.detail);
          }
        } catch {
          // Ignore JSON parse errors
        }
        throw new Error(errorDetail);
      }

        if (streamingEnabled && response.body) {
          // Handle streaming response
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          let fullContent = '';
          let metadata: ResponseMetadata | undefined;

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const { chunks, remainder } = parseStreamBuffer(buffer);
            buffer = remainder;

            for (const chunk of chunks) {
              if (chunk.content) {
                fullContent += chunk.content;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantId ? { ...msg, content: fullContent } : msg
                  )
                );
              }
              if (chunk.metadata) {
                metadata = { ...metadata, ...chunk.metadata };
              }
            }
          }

          // Final update with metadata
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? { ...msg, content: fullContent || '(No response)', metadata }
                : msg
            )
          );
        } else {
          // Handle non-streaming response
          const data: ChatResponse = await response.json();
          const metadata: ResponseMetadata = {
            trace_id: data.runtime?.trace_id,
            provider: data.runtime?.provider,
            env: data.runtime?.env,
            git_sha: data.runtime?.git_sha,
            build_time: data.runtime?.build_time,
          };

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? { ...msg, content: data.message?.content || '(No response)', metadata }
                : msg
            )
          );
        }
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          // Request was cancelled
          setMessages((prev) => prev.filter((msg) => msg.id !== assistantId));
        } else {
          const errorMessage = err instanceof Error ? err.message : 'Unknown error';
          setError(errorMessage);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId ? { ...msg, content: `Error: ${errorMessage}` } : msg
            )
          );
        }
      } finally {
        setIsLoading(false);
        abortControllerRef.current = null;
      }
    },
    [environment, streamingEnabled, isLoading, onAuthRequired]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const cancelRequest = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    cancelRequest,
  };
}
