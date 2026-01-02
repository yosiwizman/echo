# CTO Report: OpenAI Provider v1

**Date**: 2026-01-02
**Author**: Platform Engineering (Agent)
**Status**: Implemented, pending deployment

## Executive Summary

Implemented a production-grade OpenAI provider for the Brain API that:
- Uses the official OpenAI SDK directly (no langchain for core chat)
- Supports both streaming and non-streaming responses
- Includes comprehensive error handling and trace propagation
- Maintains backward compatibility with the stub provider

## Architecture

### Provider Abstraction

```
BrainProvider (ABC)
├── StubBrainProvider    # Deterministic responses for CI/testing
└── OpenAIBrainProvider  # Real AI via OpenAI API
```

### Selection Logic

1. `ECHO_BRAIN_PROVIDER=stub` → StubBrainProvider
2. `ECHO_BRAIN_PROVIDER=openai` → OpenAIBrainProvider (requires API key)
3. `OPENAI_API_KEY` present → OpenAIBrainProvider
4. Otherwise → StubBrainProvider (safe default for CI)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ECHO_BRAIN_PROVIDER` | No | auto | Force provider selection |
| `OPENAI_API_KEY` | For OpenAI | - | API key (via Secret Manager) |
| `OPENAI_MODEL` | No | `gpt-4.1-mini` | Model to use |
| `OPENAI_TIMEOUT` | No | `60` | Request timeout (seconds) |
| `OPENAI_MAX_TOKENS` | No | `4096` | Max completion tokens |

## Key Features

### 1. Direct OpenAI SDK
- Uses `openai` Python SDK v1.x
- Async client for non-blocking I/O
- Built-in retry with exponential backoff (max 2 retries)

### 2. Trace Propagation
- Our `trace_id` sent to OpenAI via `X-Client-Request-Id` header
- OpenAI's `x-request-id` captured and logged
- Enables end-to-end request correlation

### 3. Structured Error Handling
```json
{
  "ok": false,
  "error": {
    "code": "rate_limit",
    "message": "OpenAI rate limit exceeded. Please retry later.",
    "upstream_request_id": "req-abc123"
  },
  "runtime": {
    "trace_id": "...",
    "provider": "openai",
    "env": "staging"
  }
}
```

Error code to HTTP status mapping:
- `auth_error` → 401
- `rate_limit` → 429
- `timeout` → 504
- `connection_error` → 502
- `bad_request` → 400
- `upstream_error` → 502

### 4. Privacy
- Message contents are NEVER logged
- Only metadata logged: trace_id, model, token counts, request IDs

## Files Changed

### Backend
- `services/echo_backend/utils/brain/provider.py` - OpenAI provider implementation
- `services/echo_backend/models/brain.py` - Added ErrorInfo, ErrorResponse models
- `services/echo_backend/routers/brain.py` - Error handling, trace_id propagation
- `services/echo_backend/tests/test_openai_provider.py` - Comprehensive unit tests

### Documentation
- `docs/brain_api.md` - Updated provider selection docs
- `docs/ops/openai_provider.md` - NEW: Enabling guide

### CI/Ops
- `.github/workflows/backend_openai_smoke.yml` - NEW: Manual OpenAI verification

## Enabling on Staging

### Step 1: Create Secret
```bash
gcloud secrets create openai-api-key --replication-policy="automatic"
echo -n "sk-..." | gcloud secrets versions add openai-api-key --data-file=-
```

### Step 2: Grant Access
```bash
PROJECT_ID=$(gcloud config get-value project)
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 3: Update Cloud Run
```bash
gcloud run services update echo-backend-staging \
  --region europe-west1 \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
  --set-env-vars "ECHO_BRAIN_PROVIDER=openai,OPENAI_MODEL=gpt-4.1-mini"
```

### Step 4: Verify
```bash
curl https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/v1/brain/health
# {"ok": true, "provider": "openai", ...}
```

Or run the manual workflow:
```
gh workflow run backend_openai_smoke.yml --repo yosiwizman/echo -f environment=staging
```

## Cost Considerations

- **Default model**: `gpt-4.1-mini` (cost-efficient, ~$0.15/1M input tokens)
- **Rate limits**: Depend on OpenAI tier
- **Monitoring**: Use OpenAI dashboard for usage tracking

## Security Notes

1. **Server-side only**: API key never exposed to clients
2. **Secret Manager**: Production keys stored securely
3. **No logging**: Message content never logged
4. **CORS**: Web UI cannot access API key

## Rollback

To disable OpenAI:
```bash
gcloud run services update echo-backend-staging \
  --region europe-west1 \
  --set-env-vars "ECHO_BRAIN_PROVIDER=stub" \
  --remove-secrets "OPENAI_API_KEY"
```

## Test Coverage

- Provider selection logic
- Missing API key handling
- Error mapping (auth, rate limit, timeout, connection)
- Streaming event generation
- HTTP status code mapping
- Router integration

All tests use mocked OpenAI client (no real API calls in CI).

## Next Steps

1. Merge PR
2. Deploy staging (automatic on merge)
3. Mr W to provision OpenAI API key in Secret Manager
4. Update Cloud Run with secret + env vars
5. Run `backend_openai_smoke.yml` to verify
6. Repeat for production when ready

## Related Documentation

- [Brain API Reference](../docs/brain_api.md)
- [OpenAI Provider Guide](../docs/ops/openai_provider.md)
