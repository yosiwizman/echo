# Enabling OpenAI Provider on Cloud Run

This guide explains how to enable the OpenAI provider for the Echo Brain API on Google Cloud Run using Secret Manager for secure API key storage.

## Prerequisites

- Google Cloud project with Secret Manager API enabled
- `gcloud` CLI authenticated with appropriate permissions
- OpenAI API key from https://platform.openai.com/api-keys

## Overview

The Brain API supports two providers:
- **stub** (default): Deterministic responses for testing
- **openai**: Real AI responses using OpenAI GPT models

By default, the backend uses the stub provider unless `OPENAI_API_KEY` is configured.

## Step 1: Store API Key in Secret Manager

Create a secret to store your OpenAI API key:

```bash
# Create the secret (run once)
gcloud secrets create openai-api-key --replication-policy="automatic"

# Add your API key as a version
echo -n "sk-your-actual-api-key" | gcloud secrets versions add openai-api-key --data-file=-
```

Grant the Cloud Run service account access:

```bash
# Get your Cloud Run service's identity (default: compute service account)
PROJECT_NUM=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUM}-compute@developer.gserviceaccount.com"

# Or for dedicated service account:
# SERVICE_ACCOUNT="echo-backend-sa@$(gcloud config get-value project).iam.gserviceaccount.com"

# Grant access
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 2: Update Cloud Run Service

### Option A: Via gcloud CLI

```bash
# For staging
gcloud run services update echo-backend-staging \
  --region europe-west1 \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
  --set-env-vars "ECHO_BRAIN_PROVIDER=openai,OPENAI_MODEL=gpt-4o-mini"

# For production
gcloud run services update echo-backend \
  --region europe-west1 \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
  --set-env-vars "ECHO_BRAIN_PROVIDER=openai,OPENAI_MODEL=gpt-4o-mini"
```

### Option B: Via GitHub Actions Workflow

Update the deploy workflow to include the secret:

```yaml
# In .github/workflows/backend_cloudrun_staging.yml
- name: Deploy to Cloud Run
  uses: google-github-actions/deploy-cloudrun@v2
  with:
    service: echo-backend-staging
    region: europe-west1
    image: ...
    env_vars: |
      APP_ENV=staging
      ECHO_BRAIN_PROVIDER=openai
      OPENAI_MODEL=gpt-4o-mini
    secrets: |
      OPENAI_API_KEY=openai-api-key:latest
```

## Step 3: Verify Deployment

Check that the provider is active:

```bash
# Health check shows provider
curl https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/v1/brain/health
# Should return: {"ok": true, "provider": "openai", ...}

# Test chat endpoint
curl -X POST https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/v1/brain/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
# Should return real AI response with runtime.provider: "openai"
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ECHO_BRAIN_PROVIDER` | No | auto | Force `openai` or `stub` |
| `OPENAI_API_KEY` | Yes | - | API key (use Secret Manager) |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model to use |
| `OPENAI_TIMEOUT` | No | `60` | Request timeout (seconds) |
| `OPENAI_MAX_TOKENS` | No | `4096` | Max completion tokens |

## Cost & Safety Guardrails

### Model Selection
- **Default**: `gpt-4o-mini` — cost-efficient, strong baseline
- For higher quality: `gpt-4o` or `gpt-4-turbo`
- Check [OpenAI pricing](https://openai.com/pricing) for current rates

### Rate Limits
- OpenAI has per-minute token limits based on tier
- The API returns HTTP 429 with `error.code: "rate_limit"` when exceeded
- Consider implementing client-side retry with exponential backoff

### Security
- **NEVER** expose `OPENAI_API_KEY` to clients
- Always use Secret Manager for production keys
- The backend never logs message content (privacy)
- Trace IDs are propagated to OpenAI for debugging

## Troubleshooting

### "OPENAI_API_KEY not configured"
- Verify secret exists: `gcloud secrets versions access latest --secret=openai-api-key`
- Check service account has `secretmanager.secretAccessor` role
- Ensure Cloud Run service has the secret mounted

### "OpenAI authentication failed"
- API key may be invalid or revoked
- Check key status at https://platform.openai.com/api-keys
- Rotate key and update secret version

### Rate Limit Errors (HTTP 429)
- Check OpenAI usage dashboard
- Consider upgrading OpenAI tier
- Implement request queuing/throttling

### Timeout Errors (HTTP 504)
- Increase `OPENAI_TIMEOUT` env var
- Use shorter prompts or lower `max_tokens`
- Consider streaming for long responses

## Rollback to Stub Provider

To disable OpenAI and revert to stub:

```bash
gcloud run services update echo-backend-staging \
  --region europe-west1 \
  --set-env-vars "ECHO_BRAIN_PROVIDER=stub" \
  --remove-secrets "OPENAI_API_KEY"
```

## Monitoring

### Logs to Watch
```
OPENAI_CHAT_SUCCESS trace_id=... model=... openai_request_id=...
OPENAI_CHAT_ERROR trace_id=... error_type=... openai_request_id=...
```

### Key Metrics
- Response latency (P50, P95, P99)
- Error rate by `error.code`
- Token usage (prompt + completion)
- Cost per request (via OpenAI dashboard)
