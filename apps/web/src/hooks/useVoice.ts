import { useState, useCallback, useRef } from 'react';
import type { STTResponse, TTSResponse } from '../types';
import { BACKEND_URLS, API_ENDPOINTS, type Environment } from '../config';

export type RecordingState = 'idle' | 'recording' | 'processing';

interface UseVoiceOptions {
  environment: Environment;
  authToken: string | null;
  onAuthRequired?: () => void;
  onTranscription?: (text: string) => void;
}

export function useVoice({
  environment,
  authToken,
  onAuthRequired,
  onTranscription,
}: UseVoiceOptions) {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const authTokenRef = useRef(authToken);
  
  // Keep authToken ref updated
  authTokenRef.current = authToken;

  const startRecording = useCallback(async () => {
    setError(null);
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Prefer webm if supported, fallback to other formats
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : MediaRecorder.isTypeSupported('audio/mp4')
        ? 'audio/mp4'
        : 'audio/wav';
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Process recorded audio
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        await sendToSTT(audioBlob, mimeType);
      };
      
      mediaRecorder.start();
      setRecordingState('recording');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to access microphone';
      setError(message);
      setRecordingState('idle');
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState === 'recording') {
      setRecordingState('processing');
      mediaRecorderRef.current.stop();
    }
  }, [recordingState]);

  const sendToSTT = async (audioBlob: Blob, mimeType: string) => {
    const baseUrl = BACKEND_URLS[environment];
    const url = `${baseUrl}${API_ENDPOINTS.stt}`;
    
    try {
      // Build multipart form data
      const formData = new FormData();
      const extension = mimeType.includes('webm') ? 'webm' 
        : mimeType.includes('mp4') ? 'm4a' 
        : 'wav';
      formData.append('file', audioBlob, `recording.${extension}`);
      
      // Build headers with auth
      const headers: Record<string, string> = {};
      const currentToken = authTokenRef.current;
      if (currentToken) {
        headers['Authorization'] = `Bearer ${currentToken}`;
      }
      
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
        credentials: 'omit',
        mode: 'cors',
      });
      
      if (response.status === 401) {
        onAuthRequired?.();
        setError('Authentication required');
        setRecordingState('idle');
        return;
      }
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorBody = await response.json();
          if (errorBody.detail?.error?.message) {
            errorMessage = errorBody.detail.error.message;
          }
        } catch {
          // Ignore JSON parse errors
        }
        throw new Error(errorMessage);
      }
      
      const data: STTResponse = await response.json();
      
      if (data.ok && data.text) {
        onTranscription?.(data.text);
      } else {
        setError('No transcription returned');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'STT request failed';
      setError(message);
    } finally {
      setRecordingState('idle');
    }
  };

  const playTTS = useCallback(async (text: string): Promise<void> => {
    if (!text.trim()) return;
    
    const baseUrl = BACKEND_URLS[environment];
    const url = `${baseUrl}${API_ENDPOINTS.tts}`;
    
    try {
      setIsPlaying(true);
      setError(null);
      
      // Build headers with auth
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      const currentToken = authTokenRef.current;
      if (currentToken) {
        headers['Authorization'] = `Bearer ${currentToken}`;
      }
      
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ text }),
        credentials: 'omit',
        mode: 'cors',
      });
      
      if (response.status === 401) {
        onAuthRequired?.();
        setError('Authentication required');
        setIsPlaying(false);
        return;
      }
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorBody = await response.json();
          if (errorBody.detail?.error?.message) {
            errorMessage = errorBody.detail.error.message;
          }
        } catch {
          // Ignore JSON parse errors
        }
        throw new Error(errorMessage);
      }
      
      const data: TTSResponse = await response.json();
      
      if (data.ok && data.audio_base64) {
        // Decode base64 and create audio element
        const audioBytes = base64ToArrayBuffer(data.audio_base64);
        const audioBlob = new Blob([audioBytes], { type: data.mime_type });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Stop any existing playback
        if (audioRef.current) {
          audioRef.current.pause();
          URL.revokeObjectURL(audioRef.current.src);
        }
        
        // Create and play audio
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        
        audio.onended = () => {
          setIsPlaying(false);
          URL.revokeObjectURL(audioUrl);
        };
        
        audio.onerror = () => {
          setIsPlaying(false);
          setError('Failed to play audio');
          URL.revokeObjectURL(audioUrl);
        };
        
        await audio.play();
      } else {
        setError('No audio returned');
        setIsPlaying(false);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'TTS request failed';
      setError(message);
      setIsPlaying(false);
    }
  }, [environment, onAuthRequired]);

  const stopPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  }, []);

  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState === 'recording') {
      // Stop without processing
      const stream = mediaRecorderRef.current.stream;
      mediaRecorderRef.current.ondataavailable = null;
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
      stream.getTracks().forEach(track => track.stop());
      setRecordingState('idle');
    }
  }, [recordingState]);

  return {
    recordingState,
    isPlaying,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
    playTTS,
    stopPlayback,
  };
}

/**
 * Convert base64 string to ArrayBuffer.
 */
function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}
