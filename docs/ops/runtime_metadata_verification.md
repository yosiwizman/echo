# Runtime Metadata Verification

Quick reference for verifying deployed services have correct runtime metadata.

---

## Service URLs

| Environment | Base URL |
|-------------|----------|
| **Staging** | `https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app` |
| **Production** | `https://echo-backend-zxuvsjb5qa-ew.a.run.app` |

---

## Endpoints to Test

### Root `/`

Returns service info with runtime metadata.

**Staging:**
```bash
curl https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/
```

**Production:**
```bash
curl https://echo-backend-zxuvsjb5qa-ew.a.run.app/
```

**Expected output:**
```json
{
  "service": "echo-backend",
  "env": "staging",
  "git_sha": "abc123def456...",
  "build_time": "2026-01-01T12:00:00Z",
  "status": "ok",
  "endpoints": ["GET /health", "GET /version", "GET /docs"]
}
```

### Version `/version`

Returns only build metadata.

**Staging:**
```bash
curl https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/version
```

**Production:**
```bash
curl https://echo-backend-zxuvsjb5qa-ew.a.run.app/version
```

**Expected output:**
```json
{
  "env": "staging",
  "git_sha": "abc123def456...",
  "build_time": "2026-01-01T12:00:00Z"
}
```

### Health `/health`

Simple health check (unchanged).

```bash
curl https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/health
```

**Expected output:**
```json
{"status": "ok"}
```

### API Docs `/docs`

Swagger UI (browser only).

- Staging: https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/docs
- Production: https://echo-backend-zxuvsjb5qa-ew.a.run.app/docs

---

## Environment Variables Set at Deploy

| Variable | Staging | Production |
|----------|---------|------------|
| `APP_ENV` | `staging` | `production` |
| `GIT_SHA` | Git commit SHA | Git commit SHA |
| `BUILD_TIME` | UTC ISO timestamp | UTC ISO timestamp |

These are set by GitHub Actions workflows during deployment.

---

## Verification Checklist

After a deploy, verify:

- [ ] `GET /` returns `"env": "staging"` or `"env": "production"` (not `"unknown"`)
- [ ] `GET /` returns `"git_sha"` (40-char hex string)
- [ ] `GET /` returns `"build_time"` (ISO timestamp)
- [ ] `GET /version` returns the same metadata
- [ ] `GET /health` returns `{"status": "ok"}`

---

## Troubleshooting

### `env` shows "unknown"

The Cloud Run service is missing `APP_ENV`. Check:
1. GitHub Actions workflow set `env_vars` correctly
2. Service has the latest revision deployed

To fix manually:
```bash
gcloud run services update echo-backend-staging --region=europe-west1 --update-env-vars=APP_ENV=staging
```

### `git_sha` or `build_time` shows "unknown"

The deploy workflow didn't set these variables. Re-deploy using the GitHub Actions workflow (not manual gcloud).

---

## Related Docs

- Staging setup: `docs/ops/gcp_staging_cloudrun_setup.md`
- Production setup: `docs/ops/gcp_production_cloudrun_setup.md`
