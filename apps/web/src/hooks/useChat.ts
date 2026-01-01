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

export function useChat(environment: Environment, streamingEnabled: boolean) {
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionId = useRef(loadSessionId());
  const abortControllerRef = useRef<AbortController | null>(null);

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
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content.trim(),
            session_id: sessionId.current,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
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
            trace_id: data.trace_id,
            provider: data.provider,
            ...data.metadata,
          };

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? { ...msg, content: data.response || '(No response)', metadata }
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
    [environment, streamingEnabled, isLoading]
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
