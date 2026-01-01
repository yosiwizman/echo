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

export function Header({
  environment,
  onEnvironmentChange,
  streamingEnabled,
  onStreamingChange,
  healthStatus,
  onHealthCheck,
  onClearChat,
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
