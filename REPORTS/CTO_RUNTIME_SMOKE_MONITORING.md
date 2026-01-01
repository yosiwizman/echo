# Echo — CTO Report: Runtime Smoke Monitoring
Date: 2026-01-01
Author: Senior Platform Engineer

## Executive Summary

Added always-on runtime monitoring that validates staging and production Cloud Run deployments every 15 minutes via GitHub Actions. This provides visibility into service health independent of GCP Console, alerting immediately when endpoints break or deployment metadata regresses.

---

## What Was Added

### New Workflow: `.github/workflows/backend_runtime_smoke.yml`

A scheduled GitHub Actions workflow that:
- **Runs every 15 minutes** (cron: `*/15 * * * *`)
- **Can be triggered manually** via workflow_dispatch
- **Tests both staging and production** `/health` and `/version` endpoints
- **Validates responses** for:
  - HTTP 200 status
  - Valid JSON
  - Correct `env` field (staging/production)
  - Valid `git_sha` (not "unknown", >= 7 chars)
  - Valid `build_time` (ISO-8601 format)
- **Includes retries** (5 attempts with exponential backoff)
- **Prints summary tables** for each environment
- **Fails loudly** if any check fails (red ❌ in Actions)

### GitHub Actions Variables (Set via CLI)

| Variable | Value |
|----------|-------|
| `STAGING_BASE_URL` | `https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app` |
| `PROD_BASE_URL` | `https://echo-backend-zxuvsjb5qa-ew.a.run.app` |

Variables were created using:
```bash
gh variable set STAGING_BASE_URL --body "..." --repo yosiwizman/echo
gh variable set PROD_BASE_URL --body "..." --repo yosiwizman/echo
```

### Documentation

| File | Purpose |
|------|---------|
| `docs/ops/runtime_smoke_monitoring.md` | Full operational guide |
| README.md | Added "Runtime Monitoring" section |

---

## How to Operate

### View Status

1. Go to **GitHub Actions** → **Backend Runtime Smoke Monitor**
2. Green ✓ = healthy, Red ❌ = failure

### Run Manually

```bash
gh workflow run backend_runtime_smoke.yml --repo yosiwizman/echo
```

Or via GitHub UI: **Actions** → **Backend Runtime Smoke Monitor** → **Run workflow**

### Update URLs

If Cloud Run URLs change:
```bash
gh variable set STAGING_BASE_URL --body "https://new-url" --repo yosiwizman/echo
gh variable set PROD_BASE_URL --body "https://new-url" --repo yosiwizman/echo
```

### Investigate Failures

1. Check workflow output for specific validation errors
2. Check Cloud Run Console → Logs for application errors
3. Verify deployment injected correct env vars (`APP_ENV`, `GIT_SHA`, `BUILD_TIME`)

---

## Why This Approach

| Design Choice | Rationale |
|---------------|-----------|
| GitHub Actions (not GCP Monitoring) | Visible to all team members, no GCP Console access needed |
| 15-minute schedule | Balances freshness with GitHub Actions quota |
| Retry with backoff | Handles cold starts and transient failures |
| `workflow_dispatch` | Allows on-demand validation after deployments |
| Repo-level variables | Easy to update without code changes |
| Not a PR check | Monitoring shouldn't block feature development |

---

## Files in This PR

```
.github/workflows/backend_runtime_smoke.yml  (new)
docs/ops/runtime_smoke_monitoring.md         (new)
README.md                                    (updated)
REPORTS/CTO_RUNTIME_SMOKE_MONITORING.md      (this report)
```

---

## Related Work

- Staging deployment: PR #20
- Production deployment: (previous PR)
- Branch protection: PR #14
- Runtime metadata verification: `docs/ops/runtime_metadata_verification.md`
