# Auth v1: PIN + JWT Authentication

This document describes the authentication system for Echo Brain API.

## Overview

Auth v1 provides a simple PIN-based authentication that issues JWT bearer tokens:

1. **Login**: POST `/v1/auth/login` with `{"pin": "YOUR_PIN"}`
2. **Receive JWT**: Response includes a bearer token valid for 12 hours
3. **Use Token**: Include `Authorization: Bearer <token>` on protected endpoints

## Protected vs Public Endpoints

### Protected (require auth when `AUTH_REQUIRED=true`)
- `POST /v1/brain/chat`
- `POST /v1/brain/chat/stream`
- Any future `/v1/brain/*` endpoints

### Always Public
- `GET /health` - Uptime monitoring
- `GET /version` - Version info
- `GET /v1/brain/health` - Brain API health

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTH_REQUIRED` | No | `false` | Set to `true` to require auth for brain endpoints |
| `AUTH_JWT_SECRET` | If auth enabled | - | Secret for HS256 JWT signing (min 32 chars) |
| `AUTH_PIN_HASH` | If auth enabled | - | bcrypt hash of the PIN |
| `AUTH_TOKEN_TTL_SECONDS` | No | `43200` | Token lifetime (default 12 hours) |

## Setup on Cloud Run

### 1. Create Secrets in Secret Manager

```bash
# Generate a random JWT secret (32+ bytes)
JWT_SECRET=$(openssl rand -base64 32)
echo -n "$JWT_SECRET" | gcloud secrets create echo-auth-jwt-secret \
  --data-file=- \
  --replication-policy="automatic" \
  --project YOUR_PROJECT

# Generate PIN and hash it
PIN="YOUR_8_DIGIT_PIN"
# Use Python to generate bcrypt hash (note: use double quotes for variable expansion)
PIN_HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'"$PIN"', bcrypt.gensalt()).decode())")
echo -n "$PIN_HASH" | gcloud secrets create echo-auth-pin-hash \
  --data-file=- \
  --replication-policy="automatic" \
  --project YOUR_PROJECT
```

### 2. Grant Access to Cloud Run Service Account

```bash
# Get the service account
SA=$(gcloud run services describe echo-backend-staging \
  --region europe-west1 \
  --project YOUR_PROJECT \
  --format='value(spec.template.spec.serviceAccountName)')

# If empty, it's the default compute SA
if [ -z "$SA" ]; then
  PROJECT_NUM=$(gcloud projects describe YOUR_PROJECT --format='value(projectNumber)')
  SA="${PROJECT_NUM}-compute@developer.gserviceaccount.com"
fi

# Grant access
gcloud secrets add-iam-policy-binding echo-auth-jwt-secret \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project YOUR_PROJECT

gcloud secrets add-iam-policy-binding echo-auth-pin-hash \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project YOUR_PROJECT
```

### 3. Update Cloud Run Service

```bash
gcloud run services update echo-backend-staging \
  --region europe-west1 \
  --project YOUR_PROJECT \
  --set-secrets "AUTH_JWT_SECRET=echo-auth-jwt-secret:latest,AUTH_PIN_HASH=echo-auth-pin-hash:latest" \
  --set-env-vars "AUTH_REQUIRED=true"
```

## API Reference

### POST /v1/auth/login

Exchange PIN for JWT token.

**Request:**
```json
{
  "pin": "12345678"
}
```

**Success Response (200):**
```json
{
  "ok": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-01-04T12:00:00Z",
  "runtime": {
    "trace_id": "abc123",
    "provider": "auth",
    "env": "staging"
  }
}
```

**Error Responses:**

- **401 Invalid PIN:**
```json
{
  "detail": {
    "ok": false,
    "error": {
      "code": "invalid_pin",
      "message": "Invalid PIN."
    },
    "runtime": {...}
  }
}
```

- **429 Rate Limited:**
```json
{
  "detail": {
    "ok": false,
    "error": {
      "code": "rate_limit",
      "message": "Too many login attempts. Please try again later.",
      "retry_after": 300
    },
    "runtime": {...}
  }
}
```

### Rate Limiting

Login attempts are rate-limited per IP:
- **10 attempts per 10 minutes**
- Successful login resets the counter
- `Retry-After` header indicates when to retry

## Rotating Credentials

### Rotate JWT Secret

```bash
# Create new secret version
NEW_SECRET=$(openssl rand -base64 32)
echo -n "$NEW_SECRET" | gcloud secrets versions add echo-auth-jwt-secret \
  --data-file=- \
  --project YOUR_PROJECT

# Redeploy to pick up new secret
gcloud run services update echo-backend-staging \
  --region europe-west1 \
  --project YOUR_PROJECT \
  --set-secrets "AUTH_JWT_SECRET=echo-auth-jwt-secret:latest"
```

Note: This invalidates all existing tokens. Users must re-login.

### Rotate PIN

```bash
# Generate new PIN hash (note: use double quotes for variable expansion)
NEW_PIN="NEW_8_DIGIT_PIN"
NEW_HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'"$NEW_PIN"', bcrypt.gensalt()).decode())")
echo -n "$NEW_HASH" | gcloud secrets versions add echo-auth-pin-hash \
  --data-file=- \
  --project YOUR_PROJECT

# Redeploy
gcloud run services update echo-backend-staging \
  --region europe-west1 \
  --project YOUR_PROJECT \
  --set-secrets "AUTH_PIN_HASH=echo-auth-pin-hash:latest"
```

## Disabling Auth

To disable auth (revert to open access):

```bash
gcloud run services update echo-backend-staging \
  --region europe-west1 \
  --project YOUR_PROJECT \
  --set-env-vars "AUTH_REQUIRED=false"
```

Note: Even with `AUTH_REQUIRED=false`, valid tokens are still accepted if provided.

## Security Considerations

1. **PIN is never logged** - Only trace IDs and IP addresses appear in logs
2. **bcrypt hashing** - Timing-safe comparison prevents timing attacks
3. **JWT claims** - Tokens include `jti` (unique ID) for audit trails
4. **Algorithm restriction** - Only HS256 accepted, prevents algorithm confusion
5. **Rate limiting** - Per-IP sliding window prevents brute force

## Troubleshooting

### "AUTH_JWT_SECRET not configured"
- Verify secret exists in Secret Manager
- Check service account has `secretmanager.secretAccessor` role
- Ensure Cloud Run service has the secret mounted

### "Invalid PIN" but PIN is correct
- Verify PIN_HASH was generated with bcrypt
- Check for trailing newlines in the secret
- Re-generate hash: `python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PIN_HERE', bcrypt.gensalt()).decode())"`

### Token expired immediately
- Check `AUTH_TOKEN_TTL_SECONDS` setting
- Verify server and client clocks are synchronized

### Rate limited on first attempt
- Check for load balancer IP forwarding (X-Forwarded-For)
- Multiple users behind same NAT share IP
