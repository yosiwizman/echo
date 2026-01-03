import type { Environment } from '../config';
import type { HealthStatus } from '../hooks/useHealth';

interface Props {
  environment: Environment;
  onEnvironmentChange: (env: Environment) => void;
  streamingEnabled: boolean;
  onStreamingChange: (enabled: boolean) => void;
  healthStatus: HealthStatus;
  onHealthCheck: () => void;
  onClearChat: () => void;
  isAuthenticated?: boolean;
  onLogin?: () => void;
  onLogout?: () => void;
}

function HealthIndicator({
  status,
  onClick,
}: {
  status: HealthStatus;
  onClick: () => void;
}) {
  const colors = {
    checking: 'bg-yellow-400',
    ok: 'bg-green-500',
    error: 'bg-red-500',
  };

  const labels = {
    checking: 'Checking...',
    ok: 'Connected',
    error: 'Disconnected',
  };

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
      title="Click to refresh"
    >
      <span className={`w-2.5 h-2.5 rounded-full ${colors[status]} animate-pulse`} />
      <span>{labels[status]}</span>
    </button>
  );
}

function AuthIndicator({
  isAuthenticated,
  onLogin,
  onLogout,
}: {
  isAuthenticated: boolean;
  onLogin?: () => void;
  onLogout?: () => void;
}) {
  if (isAuthenticated) {
    return (
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1 text-sm text-green-600">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          Authed
        </span>
        {onLogout && (
          <button
            onClick={onLogout}
            className="text-xs text-gray-500 hover:text-red-500"
          >
            Logout
          </button>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={onLogin}
      className="flex items-center gap-1 text-sm text-gray-500 hover:text-echo-600"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
      </svg>
      Login
    </button>
  );
}

export function Header({
  environment,
  onEnvironmentChange,
  streamingEnabled,
  onStreamingChange,
  healthStatus,
  onHealthCheck,
  onClearChat,
  isAuthenticated = false,
  onLogin,
  onLogout,
}: Props) {
  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-4xl mx-auto flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <svg
            className="w-8 h-8"
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle cx="50" cy="50" r="45" fill="#0ea5e9" />
            <circle cx="50" cy="50" r="30" fill="#38bdf8" />
            <circle cx="50" cy="50" r="15" fill="#ffffff" />
          </svg>
          <h1 className="text-xl font-semibold text-gray-900">Echo Chat</h1>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          {/* Auth Indicator */}
          <AuthIndicator
            isAuthenticated={isAuthenticated}
            onLogin={onLogin}
            onLogout={onLogout}
          />

          {/* Health Indicator */}
          <HealthIndicator status={healthStatus} onClick={onHealthCheck} />

          {/* Environment Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Env:</span>
            <select
              value={environment}
              onChange={(e) => onEnvironmentChange(e.target.value as Environment)}
              className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-echo-500"
            >
              <option value="staging">Staging</option>
              <option value="production">Production</option>
            </select>
          </div>

          {/* Streaming Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <span className="text-sm text-gray-600">Stream:</span>
            <input
              type="checkbox"
              checked={streamingEnabled}
              onChange={(e) => onStreamingChange(e.target.checked)}
              className="w-4 h-4 text-echo-500 rounded focus:ring-echo-500"
            />
          </label>

          {/* Clear Chat */}
          <button
            onClick={onClearChat}
            className="text-sm text-gray-500 hover:text-red-500 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>
    </header>
  );
}
