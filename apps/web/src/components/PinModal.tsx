import { useState, useCallback, useEffect, useRef } from 'react';

interface Props {
  isOpen: boolean;
  isLoading: boolean;
  error: string | null;
  onSubmit: (pin: string) => void;
  onClose?: () => void;
}

export function PinModal({ isOpen, isLoading, error, onSubmit, onClose }: Props) {
  const [pin, setPin] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      // Small delay to ensure modal is rendered
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Clear PIN on error
  useEffect(() => {
    if (error) {
      setPin('');
    }
  }, [error]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (pin.trim() && !isLoading) {
        onSubmit(pin.trim());
      }
    },
    [pin, isLoading, onSubmit]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape' && onClose) {
        onClose();
      }
    },
    [onClose]
  );

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onKeyDown={handleKeyDown}
    >
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm mx-4">
        <div className="text-center mb-6">
          <div className="w-16 h-16 mx-auto mb-4 bg-echo-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-echo-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900">Enter PIN</h2>
          <p className="text-sm text-gray-500 mt-1">
            Authentication required to access Echo Chat
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <input
              ref={inputRef}
              type="password"
              inputMode="numeric"
              pattern="[0-9]*"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="Enter PIN"
              disabled={isLoading}
              className={`w-full px-4 py-3 text-center text-2xl tracking-widest border rounded-lg focus:outline-none focus:ring-2 focus:ring-echo-500 ${
                error ? 'border-red-500' : 'border-gray-300'
              }`}
              autoComplete="off"
            />
          </div>

          {error && (
            <div className="mb-4 text-center text-sm text-red-600">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={!pin.trim() || isLoading}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              !pin.trim() || isLoading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-echo-500 text-white hover:bg-echo-600'
            }`}
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Authenticating...
              </span>
            ) : (
              'Login'
            )}
          </button>
        </form>

        {onClose && (
          <button
            onClick={onClose}
            className="mt-4 w-full text-sm text-gray-500 hover:text-gray-700"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
