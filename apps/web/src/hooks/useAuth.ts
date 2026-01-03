import { useState, useCallback, useEffect } from 'react';
import { BACKEND_URLS, type Environment } from '../config';

const TOKEN_KEY = 'echo-auth-token';
const TOKEN_EXPIRY_KEY = 'echo-auth-expiry';

interface LoginResponse {
  ok: boolean;
  token: string;
  expires_at: string;
  runtime?: Record<string, unknown>;
}

interface LoginErrorDetail {
  ok: false;
  error: {
    code: string;
    message: string;
    retry_after?: number;
  };
}

export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  expiresAt: Date | null;
  isLoading: boolean;
  error: string | null;
}

function loadToken(): { token: string | null; expiresAt: Date | null } {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY);
    
    if (!token || !expiryStr) {
      return { token: null, expiresAt: null };
    }
    
    const expiresAt = new Date(expiryStr);
    
    // Check if token is expired
    if (expiresAt <= new Date()) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(TOKEN_EXPIRY_KEY);
      return { token: null, expiresAt: null };
    }
    
    return { token, expiresAt };
  } catch {
    return { token: null, expiresAt: null };
  }
}

function saveToken(token: string, expiresAt: Date): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiresAt.toISOString());
  } catch {
    // Ignore storage errors
  }
}

function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  } catch {
    // Ignore
  }
}

export function useAuth(environment: Environment) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);

  // Load token on mount
  useEffect(() => {
    const { token: savedToken, expiresAt: savedExpiry } = loadToken();
    setToken(savedToken);
    setExpiresAt(savedExpiry);
  }, []);

  const login = useCallback(async (pin: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    const baseUrl = BACKEND_URLS[environment];
    const url = `${baseUrl}/v1/auth/login`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin }),
        credentials: 'omit',
        mode: 'cors',
      });

      if (!response.ok) {
        let errorMessage = `Login failed (HTTP ${response.status})`;
        try {
          const errorBody = await response.json();
          const detail = errorBody.detail as LoginErrorDetail;
          if (detail?.error?.message) {
            errorMessage = detail.error.message;
            if (detail.error.retry_after) {
              errorMessage += ` (retry in ${detail.error.retry_after}s)`;
            }
          }
        } catch {
          // Ignore parse errors
        }
        setError(errorMessage);
        return false;
      }

      const data: LoginResponse = await response.json();
      
      if (!data.ok || !data.token) {
        setError('Invalid response from server');
        return false;
      }

      const newExpiresAt = new Date(data.expires_at);
      setToken(data.token);
      setExpiresAt(newExpiresAt);
      saveToken(data.token, newExpiresAt);
      
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [environment]);

  const logout = useCallback(() => {
    setToken(null);
    setExpiresAt(null);
    setError(null);
    clearToken();
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Check if token is expired and clear if so
  useEffect(() => {
    if (expiresAt && expiresAt <= new Date()) {
      logout();
    }
  }, [expiresAt, logout]);

  return {
    isAuthenticated: !!token && (!expiresAt || expiresAt > new Date()),
    token,
    expiresAt,
    isLoading,
    error,
    login,
    logout,
    clearError,
  };
}

/**
 * Get the current auth token for use in API calls.
 * Returns null if not authenticated.
 */
export function getAuthToken(): string | null {
  const { token, expiresAt } = loadToken();
  if (!token || (expiresAt && expiresAt <= new Date())) {
    return null;
  }
  return token;
}

/**
 * Clear auth token (call on 401 responses).
 */
export function clearAuthToken(): void {
  clearToken();
}
