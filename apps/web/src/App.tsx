import { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from './components/Header';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { PinModal } from './components/PinModal';
import { VoiceButton } from './components/VoiceButton';
import { useChat } from './hooks/useChat';
import { useHealth } from './hooks/useHealth';
import { useAuth } from './hooks/useAuth';
import { useVoice } from './hooks/useVoice';
import { DEFAULT_ENVIRONMENT, type Environment } from './config';

const ENV_STORAGE_KEY = 'echo-environment';
const STREAM_STORAGE_KEY = 'echo-streaming';
const VOICE_AUTOPLAY_KEY = 'echo-voice-autoplay';

function loadEnvironment(): Environment {
  try {
    const stored = localStorage.getItem(ENV_STORAGE_KEY);
    if (stored === 'staging' || stored === 'production') return stored;
  } catch {
    // Ignore
  }
  return DEFAULT_ENVIRONMENT;
}

function loadStreaming(): boolean {
  try {
    const stored = localStorage.getItem(STREAM_STORAGE_KEY);
    return stored === 'true';
  } catch {
    return false;
  }
}

function loadVoiceAutoPlay(): boolean {
  try {
    const stored = localStorage.getItem(VOICE_AUTOPLAY_KEY);
    // Default to true for voice auto-play
    return stored === null ? true : stored === 'true';
  } catch {
    return true;
  }
}

export default function App() {
  const [environment, setEnvironment] = useState<Environment>(loadEnvironment);
  const [streamingEnabled, setStreamingEnabled] = useState(loadStreaming);
  const [voiceAutoPlay, setVoiceAutoPlay] = useState(loadVoiceAutoPlay);
  const [pendingVoiceText, setPendingVoiceText] = useState<string | null>(null);
  const [showPinModal, setShowPinModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { status: healthStatus, checkHealth } = useHealth(environment);
  const auth = useAuth(environment);

  const handleAuthRequired = useCallback(() => {
    auth.logout();
    setShowPinModal(true);
  }, [auth]);

  const { messages, isLoading, error, sendMessage, clearMessages, cancelRequest } = useChat(
    environment,
    streamingEnabled,
    auth.token,
    handleAuthRequired
  );

  // Voice input hook
  const handleTranscription = useCallback((text: string) => {
    // Send transcribed text to chat
    sendMessage(text);
  }, [sendMessage]);

  const voice = useVoice({
    environment,
    authToken: auth.token,
    onAuthRequired: handleAuthRequired,
    onTranscription: handleTranscription,
  });

  const handleLogin = useCallback(async (pin: string) => {
    const success = await auth.login(pin);
    if (success) {
      setShowPinModal(false);
    }
  }, [auth]);

  // Persist preferences
  useEffect(() => {
    localStorage.setItem(ENV_STORAGE_KEY, environment);
  }, [environment]);

  useEffect(() => {
    localStorage.setItem(STREAM_STORAGE_KEY, String(streamingEnabled));
  }, [streamingEnabled]);

  useEffect(() => {
    localStorage.setItem(VOICE_AUTOPLAY_KEY, String(voiceAutoPlay));
  }, [voiceAutoPlay]);

  // Auto-play TTS for new assistant messages when enabled
  useEffect(() => {
    if (!voiceAutoPlay || messages.length === 0) return;
    
    const lastMessage = messages[messages.length - 1];
    // Only play if it's an assistant message and not loading
    if (lastMessage.role === 'assistant' && !isLoading && lastMessage.content) {
      // Check if this is a new message we haven't played yet
      if (pendingVoiceText !== lastMessage.content && !lastMessage.content.startsWith('Error:')) {
        setPendingVoiceText(lastMessage.content);
        voice.playTTS(lastMessage.content);
      }
    }
  }, [messages, isLoading, voiceAutoPlay, pendingVoiceText, voice]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Header
        environment={environment}
        onEnvironmentChange={setEnvironment}
        streamingEnabled={streamingEnabled}
        onStreamingChange={setStreamingEnabled}
        voiceAutoPlay={voiceAutoPlay}
        onVoiceAutoPlayChange={setVoiceAutoPlay}
        healthStatus={healthStatus}
        onHealthCheck={checkHealth}
        onClearChat={clearMessages}
        isAuthenticated={auth.isAuthenticated}
        onLogin={() => setShowPinModal(true)}
        onLogout={auth.logout}
      />

      <PinModal
        isOpen={showPinModal}
        isLoading={auth.isLoading}
        error={auth.error}
        onSubmit={handleLogin}
        onClose={auth.isAuthenticated ? () => setShowPinModal(false) : undefined}
      />

      <main className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              <p className="text-lg">Welcome to Echo Chat!</p>
              <p className="text-sm mt-2">
                Send a message to start chatting with the {environment} backend.
              </p>
              <p className="text-xs mt-4 text-gray-400">
                {streamingEnabled ? 'Streaming mode enabled' : 'Non-streaming mode'}
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {error && (
            <div className="text-center text-red-500 text-sm py-2">Error: {error}</div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-2">
            <VoiceButton
              recordingState={voice.recordingState}
              onStartRecording={voice.startRecording}
              onStopRecording={voice.stopRecording}
              disabled={healthStatus === 'error' || isLoading}
            />
            <div className="flex-1">
              <ChatInput
                onSend={sendMessage}
                onCancel={cancelRequest}
                disabled={healthStatus === 'error'}
                isLoading={isLoading}
              />
            </div>
          </div>
          {voice.error && (
            <p className="text-xs text-red-500 mt-1">Voice: {voice.error}</p>
          )}
          {healthStatus === 'error' && (
            <p className="text-xs text-red-500 mt-2 text-center">
              Cannot send messages while disconnected from backend
            </p>
          )}
        </div>
      </footer>
    </div>
  );
}
