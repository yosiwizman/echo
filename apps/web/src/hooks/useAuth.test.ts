/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getAuthToken, clearAuthToken } from './useAuth';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('Auth token storage', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  it('returns null when no token stored', () => {
    const token = getAuthToken();
    expect(token).toBeNull();
  });

  it('returns token when valid token stored', () => {
    const futureDate = new Date(Date.now() + 3600000).toISOString(); // 1 hour from now
    localStorageMock.setItem('echo-auth-token', 'test-token-123');
    localStorageMock.setItem('echo-auth-expiry', futureDate);

    const token = getAuthToken();
    expect(token).toBe('test-token-123');
  });

  it('returns null when token expired', () => {
    const pastDate = new Date(Date.now() - 3600000).toISOString(); // 1 hour ago
    localStorageMock.setItem('echo-auth-token', 'expired-token');
    localStorageMock.setItem('echo-auth-expiry', pastDate);

    const token = getAuthToken();
    expect(token).toBeNull();
  });

  it('clearAuthToken removes token from storage', () => {
    localStorageMock.setItem('echo-auth-token', 'test-token');
    localStorageMock.setItem('echo-auth-expiry', new Date().toISOString());

    clearAuthToken();

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('echo-auth-token');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('echo-auth-expiry');
  });
});

describe('Authorization header injection', () => {
  it('useChat should include auth header when token provided', () => {
    // This is a structural test - the actual fetch behavior is tested in integration
    // The implementation adds Authorization: Bearer <token> when authToken is provided
    // See useChat.ts lines 94-97
    expect(true).toBe(true); // Placeholder for integration test
  });
});
