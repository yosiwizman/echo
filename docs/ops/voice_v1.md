# Voice v1 (STT + TTS)

Voice v1 provides speech-to-text (STT) and text-to-speech (TTS) capabilities for Echo Chat using OpenAI's Audio API.

## Architecture

```
User speaks → Mic Button → MediaRecorder → /v1/brain/stt → Transcribed text
     ↓                                                           ↓
Headphones ← Audio playback ← /v1/brain/tts ← Assistant text ← /v1/brain/chat
```

## Endpoints

### POST /v1/brain/stt
Speech-to-text transcription.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` field with audio (webm, wav, mp3, m4a, ogg, flac)
- Max size: 25MB

**Response:**
```json
{
  "ok": true,
  "text": "transcribed text here",
  "duration_seconds": 3.5,
  "runtime": {
    "trace_id": "uuid",
    "provider": "openai",
    "env": "staging",
    "git_sha": "abc123",
    "build_time": "2026-01-01T00:00:00Z"
  }
}
```

### POST /v1/brain/tts
Text-to-speech synthesis.

**Request:**
```json
{
  "text": "Hello, how can I help you?",
  "voice": "alloy",  // optional
  "format": "mp3"    // optional
}
```

**Response:**
```json
{
  "ok": true,
  "audio_base64": "base64-encoded-audio-bytes",
  "mime_type": "audio/mpeg",
  "runtime": { ... }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_STT_MODEL` | `gpt-4o-mini-transcribe` | Model for speech-to-text |
| `OPENAI_TTS_MODEL` | `gpt-4o-mini-tts` | Model for text-to-speech |
| `OPENAI_TTS_VOICE` | `alloy` | Default TTS voice |
| `OPENAI_TTS_FORMAT` | `mp3` | Default audio format |
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `ECHO_VOICE_PROVIDER` | (auto) | Force `stub` or `openai` |

### Available Voices
- `alloy` - Neutral, balanced
- `echo` - Deep, warm
- `fable` - Expressive
- `onyx` - Authoritative
- `nova` - Friendly
- `shimmer` - Clear, bright

### Available Formats
- `mp3` - MPEG audio (default, widely supported)
- `opus` - Opus codec (smaller, good quality)
- `aac` - AAC audio
- `flac` - Lossless
- `wav` - Uncompressed
- `pcm` - Raw PCM

## Authentication

Both `/stt` and `/tts` endpoints require authentication when `AUTH_REQUIRED=true`:
- Include `Authorization: Bearer <jwt>` header
- Token obtained via `/v1/auth/login`

## Web UI Usage

1. **Voice Input**: Click the microphone button (cyan) to start recording
2. **Stop Recording**: Click again (red) to stop and transcribe
3. **Auto-Play**: Enable 🔊 toggle in header to auto-play assistant replies
4. **Browser Permission**: Grant microphone access when prompted

## Browser Permissions

The web app requires microphone permission for voice input:

**Chrome/Edge:**
- Click padlock icon → Site settings → Microphone: Allow

**Firefox:**
- Click padlock icon → More Information → Permissions → Microphone: Allow

**Safari:**
- Safari → Settings → Websites → Microphone → Allow

## Privacy

- **Audio content is NEVER logged** on backend
- Only metadata is logged: trace_id, audio size, duration, content type
- **Transcribed text is NEVER logged** on backend
- Audio is processed transiently and not stored

## Testing on Staging

1. Navigate to https://echo-web-staging-zxuvsjb5qa-ew.a.run.app
2. Login with PIN when prompted
3. Click mic button → speak → click stop
4. Your speech is transcribed and sent to chat
5. With 🔊 enabled, hear the AI response

## Error Handling

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `auth_required` | 401 | Missing or invalid JWT |
| `invalid_audio_format` | 400 | Unsupported audio type |
| `empty_file` | 400 | Audio file is empty |
| `file_too_large` | 413 | Exceeds 25MB limit |
| `rate_limit` | 429 | OpenAI rate limit |
| `timeout` | 504 | Request timed out |
| `upstream_error` | 502 | OpenAI API error |

## Stub Mode (CI)

For testing without OpenAI:
- Set `ECHO_VOICE_PROVIDER=stub`
- STT returns: "Echo Voice (stub): transcribed X bytes of audio."
- TTS returns: minimal valid MP3 audio
