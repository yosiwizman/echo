# Brain API Contract Smoke Tests

This document describes the Brain API contract smoke tests that run on every push to `main` and on all pull requests. These tests serve as permanent API guardrails to prevent regressions and ensure the Brain API contract remains stable.

## Purpose

The contract smoke tests validate:
1. **Health endpoint** (`GET /v1/brain/health`) - Returns valid health status
2. **Chat endpoint** (`POST /v1/brain/chat`) - Returns properly structured chat response
3. **Streaming endpoint** (`POST /v1/brain/chat/stream`) - Returns valid SSE stream with token and final events

These tests run against the stub provider (no external dependencies) and validate the API contract at the HTTP/JSON level.

## What It Checks

### Health Endpoint
- Status code: 200
- Response structure:
  - `ok: true`
  - `version` field present
  - `provider == "stub"` (in test mode)

### Chat Endpoint
- Status code: 200
- Response structure:
  - `session_id` field present
  - `message.role == "assistant"`
  - `message.content` field present
  - `usage.total_tokens` field present
- Stub response contains "stub" text

### Streaming Endpoint
- Status code: 200
- SSE format validation:
  - Contains `event: token` lines
  - Contains `event: final` line
  - Contains `data:` lines with JSON payloads
- Final event contains `session_id`

## Running Locally

### Quick Test (Shell)

```bash
cd services/echo_backend

# Start server in stub mode
export ECHO_BRAIN_PROVIDER=stub
export ECHO_DISABLE_MODEL_DOWNLOADS=1
uvicorn main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

# Wait for server
sleep 5

# Test health
curl http://127.0.0.1:8000/v1/brain/health | jq .

# Test chat
curl -X POST http://127.0.0.1:8000/v1/brain/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Test"}]}' | jq .

# Test streaming
curl -X POST http://127.0.0.1:8000/v1/brain/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Test"}]}'

# Cleanup
kill $SERVER_PID
```

### Automated Script

Create `scripts/test_brain_contract.sh`:

```bash
#!/bin/bash
set -e

cd "$(dirname "$0")/../services/echo_backend"

export ECHO_BRAIN_PROVIDER=stub
export ECHO_DISABLE_MODEL_DOWNLOADS=1

echo "Starting server..."
uvicorn main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

# Cleanup on exit
trap "kill $SERVER_PID 2>/dev/null || true" EXIT

echo "Waiting for server..."
for i in {1..30}; do
  if curl -s http://127.0.0.1:8000/healthz > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Testing health endpoint..."
HEALTH=$(curl -s http://127.0.0.1:8000/v1/brain/health)
echo "$HEALTH" | jq -e '.ok == true' || { echo "FAIL: Health"; exit 1; }
echo "✓ Health OK"

echo "Testing chat endpoint..."
CHAT=$(curl -s -X POST http://127.0.0.1:8000/v1/brain/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Test"}]}')
echo "$CHAT" | jq -e '.message.role == "assistant"' || { echo "FAIL: Chat"; exit 1; }
echo "✓ Chat OK"

echo "Testing stream endpoint..."
STREAM=$(timeout 5s curl -s -X POST http://127.0.0.1:8000/v1/brain/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Test"}]}' || true)
[[ "$STREAM" =~ "event: final" ]] || { echo "FAIL: Stream"; exit 1; }
echo "✓ Stream OK"

echo ""
echo "All contract tests passed!"
```

Make it executable:
```bash
chmod +x scripts/test_brain_contract.sh
./scripts/test_brain_contract.sh
```

## Environment Variables

The contract smoke tests use these environment variables:

- `ECHO_BRAIN_PROVIDER=stub` - Use stub provider (no OpenAI API key required)
- `ECHO_DISABLE_MODEL_DOWNLOADS=1` - Prevent VAD model downloads
- `ECHO_REQUIRE_SECRETS=0` - Allow running without secrets

## CI Integration

The workflow runs automatically on:
- Every push to `main`
- Every pull request targeting `main`

Workflow file: `.github/workflows/brain_contract_smoke.yml`

## Troubleshooting

### Server fails to start

Check that all dependencies are installed:
```bash
cd services/echo_backend
pip install -r requirements.txt
```

### Health endpoint times out

Ensure the server is binding to the correct host/port:
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill existing process if needed
kill -9 <PID>
```

### Tests fail with "jq: command not found"

Install jq:
- macOS: `brew install jq`
- Ubuntu: `apt-get install jq`
- Windows: Download from https://jqlang.github.io/jq/

### Contract validation fails

If a contract test fails, it means the API contract has changed:
1. Check if the change was intentional
2. If yes, update the contract tests to match the new contract
3. If no, fix the regression before merging
4. Document any contract changes in the PR description

## Adding New Contract Tests

To add a new endpoint to the contract smoke tests:

1. Add a new step to `.github/workflows/brain_contract_smoke.yml`
2. Use curl to call the endpoint
3. Validate the response structure with `jq`
4. Update this documentation

Example:
```yaml
- name: Contract Test - New Endpoint
  run: |
    echo "Testing POST /v1/brain/new-endpoint..."
    RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/v1/brain/new-endpoint \
      -H "Content-Type: application/json" \
      -d '{"param":"value"}')
    echo "$RESPONSE" | jq -e '.expected_field' || { echo "FAIL"; exit 1; }
    echo "✓ New endpoint validated"
```

## Contract Stability Guarantee

The Brain API v1 contract is stable. Any changes that break these contract tests are considered breaking changes and require:
- Major version bump (e.g., v1 → v2)
- Migration guide for clients
- Deprecation period for v1

Non-breaking additions (new optional fields, new endpoints) are allowed and should include corresponding contract tests.
