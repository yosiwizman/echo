# Brain API v1

The Brain API provides conversational intelligence endpoints for stateless chat, streaming responses, and session management.

## Base URL

All Brain API endpoints are prefixed with `/v1/brain`.

## Provider Selection

The Brain API supports multiple backend providers:

- **OpenAI**: Uses OpenAI's GPT models via langchain (default when `OPENAI_API_KEY` is set)
- **Stub**: Deterministic canned responses for CI/testing (automatically used when no API key is available)

### Environment Variables

- `ECHO_BRAIN_PROVIDER`: Explicitly set provider (`openai` or `stub`)
- `OPENAI_API_KEY`: OpenAI API key (required for `openai` provider)
- `ECHO_REQUIRE_OPENAI=1`: Fail fast if OpenAI required but key missing (strict mode)

## Endpoints

### Health Check

```
GET /v1/brain/health
```

Returns the health status and configuration of the Brain API.

**Response:**

```json
{
  "ok": true,
  "time": "2025-12-30T17:00:00.000Z",
  "version": "1.0.0",
  "provider": "openai"
}
```

**Example:**

```bash
curl http://localhost:8000/v1/brain/health
```

### Chat Completion (Non-Streaming)

```
POST /v1/brain/chat
```

Generate a complete chat response.

**Request Body:**

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "session_id": "optional-session-123",
  "metadata": {
    "user_id": "user-456",
    "source": "web"
  }
}
```

**Response:**

```json
{
  "ok": true,
  "session_id": "optional-session-123",
  "message": {
    "role": "assistant",
    "content": "Hello! I'm doing well, thank you for asking. How can I assist you today?"
  },
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 18,
    "total_tokens": 43
  },
  "metadata": {
    "provider": "openai"
  },
  "runtime": {
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "provider": "openai",
    "env": "staging",
    "git_sha": "abc1234",
    "build_time": "2025-12-30T12:00:00Z"
  }
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/v1/brain/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

### Chat Completion (Streaming)

```
POST /v1/brain/chat/stream
```

Generate a streaming chat response using Server-Sent Events (SSE).

**Request Body:**

Same as non-streaming endpoint.

**Response:**

Content-Type: `text/event-stream`

**SSE Event Format:**

```
event: <event_type>
data: <json_payload>

```

**Event Types:**

1. **token**: Partial response tokens

```
event: token
data: {"token": "Hello", "session_id": "session-123"}

event: token
data: {"token": " there!", "session_id": "session-123"}
```

2. **final**: Complete response with metadata and runtime info

```
event: final
data: {
  "ok": true,
  "session_id": "session-123",
  "message": {"role": "assistant", "content": "Hello there!"},
  "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
  "metadata": {"provider": "openai"},
  "runtime": {"trace_id": "uuid", "provider": "openai", "env": "staging", "git_sha": "...", "build_time": "..."}
}
```

3. **error**: Error information

```
event: error
data: {"error": "Rate limit exceeded"}
```

4. **meta**: Optional metadata events

```
event: meta
data: {"info": "Processing started"}
```

**Example:**

```bash
curl -X POST http://localhost:8000/v1/brain/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Tell me a short joke"}
    ]
  }'
```

**JavaScript Example:**

```javascript
const eventSource = new EventSource('/v1/brain/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    messages: [
      {role: 'user', content: 'Hello!'}
    ]
  })
});

eventSource.addEventListener('token', (e) => {
  const data = JSON.parse(e.data);
  console.log('Token:', data.token);
});

eventSource.addEventListener('final', (e) => {
  const data = JSON.parse(e.data);
  console.log('Complete:', data.message.content);
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  const data = JSON.parse(e.data);
  console.error('Error:', data.error);
  eventSource.close();
});
```

## Message Schema

### Message

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| role | string | Yes | One of: `system`, `user`, `assistant` |
| content | string | Yes | The message content |

### ChatRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| messages | Message[] | Yes | Conversation history |
| session_id | string | No | Session identifier for continuity |
| metadata | object | No | Custom metadata for the request |

### ChatResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ok | boolean | No | Request success status (default: true) |
| session_id | string | Yes | Session identifier (generated if not provided) |
| message | Message | Yes | The assistant's response |
| usage | UsageInfo | No | Token usage information |
| metadata | object | No | Response metadata (includes provider) |
| runtime | RuntimeMetadata | No | Runtime metadata for observability |

### RuntimeMetadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| trace_id | string | Yes | Unique trace ID for request correlation |
| provider | string | Yes | Active brain provider (stub/openai) |
| env | string | No | Deployment environment (staging/production/unknown) |
| git_sha | string | No | Git commit SHA of deployed version |
| build_time | string | No | Build timestamp of deployed version |

### UsageInfo

| Field | Type | Description |
|-------|------|-------------|
| prompt_tokens | integer | Number of tokens in the prompt |
| completion_tokens | integer | Number of tokens in the completion |
| total_tokens | integer | Total tokens used |

## Error Handling

HTTP status codes:
- `200 OK`: Successful response
- `422 Unprocessable Entity`: Invalid request schema
- `500 Internal Server Error`: Server-side error

Error responses follow this format:

```json
{
  "detail": "Chat generation failed: <error_message>"
}
```

## Testing

The Brain API includes a stub provider for CI/testing without external dependencies:

```bash
# Force stub provider
export ECHO_BRAIN_PROVIDER=stub

# Run tests
pytest services/echo_backend/tests/test_brain_*.py
```

## Logging and Observability

Every chat request (streaming and non-streaming) logs a structured line at INFO level:

```
ECHO_CHAT_REQUEST trace_id=<uuid> provider=<stub|openai> msg_count=<n>
```

For streaming requests, the log line is:

```
ECHO_CHAT_STREAM_REQUEST trace_id=<uuid> provider=<stub|openai> msg_count=<n>
```

**Privacy**: Message contents are never logged by default. The `trace_id` allows correlating logs with API responses for debugging.

**Runtime Metadata**: The `runtime` field in responses includes:
- `trace_id`: Unique ID for this request (UUID)
- `provider`: Which backend is handling requests (stub/openai)
- `env`: Deployment environment (staging/production/unknown)
- `git_sha`: Git commit of deployed version
- `build_time`: Build timestamp

This enables end-to-end request tracing from UI to backend.

## Notes

- Session IDs are optional but recommended for maintaining conversation context
- The stub provider returns deterministic responses for reproducible testing
- Streaming responses use chunked transfer encoding; ensure your HTTP client supports it
- The `X-Accel-Buffering: no` header disables nginx buffering for low-latency streaming
- Use `trace_id` from responses to correlate with backend logs for debugging
