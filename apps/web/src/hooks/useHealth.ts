import { useState, useEffect, useCallback } from 'react';
import { BACKEND_URLS, API_ENDPOINTS, type Environment } from '../config';
import type { HealthResponse } from '../types';

export type HealthStatus = 'checking' | 'ok' | 'error';

export function useHealth(environment: Environment) {
  const [status, setStatus] = useState<HealthStatus>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    setStatus('checking');

    const baseUrl = BACKEND_URLS[environment];
    const url = `${baseUrl}${API_ENDPOINTS.health}`;

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: { Accept: 'application/json' },
        signal: AbortSignal.timeout(10000), // 10s timeout
      });

      if (response.ok) {
        const data: HealthResponse = await response.json();
        if (data.status === 'ok' || data.status === 'healthy') {
          setStatus('ok');
        } else {
          setStatus('error');
        }
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }

    setLastChecked(new Date());
  }, [environment]);

  // Check health on mount and when environment changes
  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Periodic health check every 60 seconds
  useEffect(() => {
    const interval = setInterval(checkHealth, 60000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return { status, lastChecked, checkHealth };
}
