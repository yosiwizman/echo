# Runtime Smoke Monitoring

This document describes the scheduled runtime smoke monitoring that continuously validates staging and production Cloud Run deployments.

## Purpose

The runtime smoke monitor runs every 15 minutes to verify that both staging and production backends are:
1. **Reachable** — Endpoints respond with HTTP 200
2. **Returning valid JSON** — Responses parse correctly
3. **Correctly configured** — Environment matches expected (`staging`/`production`)
4. **Properly deployed** — `git_sha` and `build_time` are present and valid

This monitoring is independent of GCP's built-in monitoring, providing visibility directly in GitHub Actions.

## What It Checks

### Endpoints Tested

For each environment (staging + production):

| Endpoint | Validation |
|----------|------------|
| `/health` | HTTP 200, valid JSON, `status: "ok"` |
| `/version` | HTTP 200, valid JSON, correct `env`, valid `git_sha`, valid `build_time` |

### Validation Rules

**`/health` endpoint:**
| Field | Rule |
|-------|------|
| `status` | Must be `"ok"` |

**`/version` endpoint:**
| Field | Rule |
|-------|------|
| `env` | Must match expected environment (`staging` or `production`) |
| `git_sha` | Must exist, not be `"unknown"`, and be at least 7 characters |
| `build_time` | Must exist and follow ISO-8601 format (`YYYY-MM-DD...`) |

### Retry Behavior

Each endpoint is tested with:
- **5 retry attempts** with exponential backoff (3s, 6s, 12s, 24s, 48s)
- **10-second connect timeout** per attempt
- **30-second max time** per request

This helps avoid false positives from transient network issues or cold starts.

## Running Manually

### From GitHub UI

1. Go to **Actions** → **Backend Runtime Smoke Monitor**
2. Click **Run workflow** (dropdown on the right)
3. Optionally check "Skip staging checks" or "Skip production checks"
4. Click **Run workflow**

### From CLI

```bash
gh workflow run backend_runtime_smoke.yml --repo yosiwizman/echo
```

Or to skip an environment:

```bash
gh workflow run backend_runtime_smoke.yml \
  --repo yosiwizman/echo \
  -f skip_staging=true
```

## Where to See Failures

### GitHub Actions

1. Go to https://github.com/yosiwizman/echo/actions
2. Filter by **Backend Runtime Smoke Monitor**
3. Failed runs show with a red ❌
4. Click into any run to see detailed output

### Email Notifications

GitHub sends email notifications for workflow failures if you have:
- **Settings** → **Notifications** → **Actions** enabled

## Updating URLs

If Cloud Run service URLs change (e.g., new project or region):

### Option 1: GitHub UI

1. Go to **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. Edit `STAGING_BASE_URL` or `PROD_BASE_URL`

### Option 2: CLI

```bash
gh variable set STAGING_BASE_URL \
  --body "https://new-staging-url.a.run.app" \
  --repo yosiwizman/echo

gh variable set PROD_BASE_URL \
  --body "https://new-production-url.a.run.app" \
  --repo yosiwizman/echo
```

## Troubleshooting

### "Missing required GitHub Actions Variables"

The workflow requires two repo-level variables:
- `STAGING_BASE_URL`
- `PROD_BASE_URL`

Set them via:
```bash
gh variable set STAGING_BASE_URL --body "https://..." --repo yosiwizman/echo
gh variable set PROD_BASE_URL --body "https://..." --repo yosiwizman/echo
```

### Endpoint unreachable (all retries failed)

1. Check if the Cloud Run service is running in GCP Console
2. Verify the URL is correct (no typos, correct region)
3. Check if there are networking issues (firewall, IAM)

### `env` mismatch

The service is returning a different environment than expected:
1. Check the `APP_ENV` environment variable in Cloud Run
2. Re-deploy with the correct `APP_ENV` value

### `git_sha` is "unknown"

The deployment didn't inject the Git SHA:
1. Check the deploy workflow is passing `GIT_SHA` correctly
2. Verify the backend reads `GIT_SHA` from environment

### `build_time` missing or invalid

The deployment didn't inject build timestamp:
1. Check the deploy workflow is passing `BUILD_TIME` correctly
2. Verify the backend reads `BUILD_TIME` from environment

## Related Documentation

- [GitHub Variables for Staging](github_variables_for_staging.md)
- [GitHub Variables for Production](github_variables_for_production.md)
- [Runtime Metadata Verification](runtime_metadata_verification.md)
- [GCP Staging Cloud Run Setup](gcp_staging_cloudrun_setup.md)
- [GCP Production Cloud Run Setup](gcp_production_cloudrun_setup.md)

## Workflow File

Location: `.github/workflows/backend_runtime_smoke.yml`

Triggers:
- **Schedule**: Every 15 minutes (`*/15 * * * *`)
- **Manual**: `workflow_dispatch` with optional skip flags

This workflow is NOT a PR check — it doesn't block merges.
