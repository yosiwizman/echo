import { describe, it, expect } from 'vitest';
import { BACKEND_URLS, DEFAULT_ENVIRONMENT, API_ENDPOINTS, type Environment } from './config';

describe('BACKEND_URLS', () => {
  it('maps staging to correct URL', () => {
    expect(BACKEND_URLS.staging).toBe('https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app');
  });

  it('maps production to correct URL', () => {
    expect(BACKEND_URLS.production).toBe('https://echo-backend-zxuvsjb5qa-ew.a.run.app');
  });

  it('staging and production URLs are different', () => {
    expect(BACKEND_URLS.staging).not.toBe(BACKEND_URLS.production);
  });

  it('all environment keys have valid URLs', () => {
    const environments: Environment[] = ['staging', 'production'];
    for (const env of environments) {
      expect(BACKEND_URLS[env]).toMatch(/^https:\/\//);
    }
  });
});

describe('DEFAULT_ENVIRONMENT', () => {
  it('defaults to staging', () => {
    expect(DEFAULT_ENVIRONMENT).toBe('staging');
  });

  it('is a valid environment key', () => {
    expect(BACKEND_URLS[DEFAULT_ENVIRONMENT]).toBeDefined();
  });
});

describe('API_ENDPOINTS', () => {
  it('has correct endpoint paths', () => {
    expect(API_ENDPOINTS.health).toBe('/health');
    expect(API_ENDPOINTS.chat).toBe('/v1/brain/chat');
    expect(API_ENDPOINTS.chatStream).toBe('/v1/brain/chat/stream');
    expect(API_ENDPOINTS.version).toBe('/version');
  });

  it('all endpoints start with /', () => {
    for (const endpoint of Object.values(API_ENDPOINTS)) {
      expect(endpoint).toMatch(/^\//);
    }
  });
});
