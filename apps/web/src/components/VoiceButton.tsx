import type { RecordingState } from '../hooks/useVoice';

interface VoiceButtonProps {
  recordingState: RecordingState;
  onStartRecording: () => void;
  onStopRecording: () => void;
  disabled?: boolean;
}

export function VoiceButton({
  recordingState,
  onStartRecording,
  onStopRecording,
  disabled = false,
}: VoiceButtonProps) {
  const isRecording = recordingState === 'recording';
  const isProcessing = recordingState === 'processing';
  const isDisabled = disabled || isProcessing;

  const handleClick = () => {
    if (isDisabled) return;
    
    if (isRecording) {
      onStopRecording();
    } else {
      onStartRecording();
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isDisabled}
      className={`
        relative p-3 rounded-full transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-offset-2
        ${isRecording
          ? 'bg-red-500 hover:bg-red-600 text-white focus:ring-red-500'
          : isProcessing
          ? 'bg-gray-400 text-white cursor-wait'
          : isDisabled
          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
          : 'bg-cyan-500 hover:bg-cyan-600 text-white focus:ring-cyan-500'
        }
      `}
      title={
        isRecording
          ? 'Click to stop recording'
          : isProcessing
          ? 'Processing audio...'
          : 'Click to start voice input'
      }
    >
      {/* Microphone Icon */}
      {!isRecording && !isProcessing && (
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
      )}

      {/* Stop Icon (when recording) */}
      {isRecording && (
        <svg
          className="w-5 h-5"
          fill="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect x="6" y="6" width="12" height="12" rx="1" />
        </svg>
      )}

      {/* Spinner (when processing) */}
      {isProcessing && (
        <svg
          className="w-5 h-5 animate-spin"
          fill="none"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}

      {/* Recording pulse indicator */}
      {isRecording && (
        <span className="absolute -top-1 -right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
        </span>
      )}
    </button>
  );
}
