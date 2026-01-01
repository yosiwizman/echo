/**
 * Backend configuration for Echo Web Chat
 *
 * Both URLs are hardcoded here. The UI provides a toggle to switch between them.
 * This approach avoids build-time environment variable injection.
 */

export const BACKEND_URLS = {
  staging: 'https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app',
  production: 'https://echo-backend-zxuvsjb5qa-ew.a.run.app',
} as const;

export type Environment = keyof typeof BACKEND_URLS;

export const DEFAULT_ENVIRONMENT: Environment = 'staging';

/**
 * API endpoints relative to the backend base URL
 */
export const API_ENDPOINTS = {
  health: '/health',
  chat: '/v1/brain/chat',
  chatStream: '/v1/brain/chat/stream',
  version: '/version',
} as const;
