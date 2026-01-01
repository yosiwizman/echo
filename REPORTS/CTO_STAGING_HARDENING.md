# Echo — CTO Report: Staging Deployment Hardening
Date: 2026-01-01
Author: Senior DevOps / Platform Engineer

## Executive Summary

This change hardens the GitHub Actions → Artifact Registry → Cloud Run staging deployment pipeline with:
1. **Enhanced preflight checks** that fail fast with human-readable instructions when GitHub Variables are missing
2. **Post-deploy smoke test** that fails the workflow if `/healthz` doesn't return HTTP 200
3. **New documentation** for disabling the legacy Cloud Build trigger and understanding GitHub Variables
4. **Updated existing docs** with troubleshooting for common issues (ghcr.io rejection, "Create credentials" button)

---

## What Changed

### Workflow Hardening (`.github/workflows/backend_cloudrun_staging.yml`)

1. **Preflight check step** — Now prints a formatted table showing:
   - Which required variables are missing (with exact location in GCP console)
   - Which optional variables are using defaults
   - Links to setup docs if something is missing

2. **Post-deploy smoke test** — Now:
   - Retries up to 5 times with 10s backoff
   - **Fails the workflow** if `/healthz` doesn't return HTTP 200
   - Provides debugging instructions (Cloud Run → Logs tab)

3. **Path triggers** — Added `docs/ops/**` so docs changes trigger the workflow (for testing)

### New Documentation

| File | Purpose |
|------|---------|
| `docs/ops/disable_cloud_build_trigger.md` | Click-by-click guide to disable/delete the legacy `rmgpgab-...` Cloud Build trigger |
| `docs/ops/github_variables_for_staging.md` | Quick reference for all 6 GitHub Variables with exact "where to find" instructions |

### Updated Documentation

| File | What Changed |
|------|--------------|
| `docs/ops/gcp_staging_cloudrun_setup.md` | Added "Create credentials" ignore note, ghcr.io rejection troubleshooting |
| `docs/ops/cloud_run_staging_clickthrough.md` | Links to new docs, related docs section |

---

## How to Operate

### First-Time Setup (Mr W)
1. Follow `docs/ops/gcp_staging_cloudrun_setup.md` (complete setup)
2. Use `docs/ops/github_variables_for_staging.md` as a checklist
3. Disable the old Cloud Build trigger per `docs/ops/disable_cloud_build_trigger.md`

### Day-to-Day
- Push to `main` touching `services/echo_backend/**` → auto-deploys
- Manual deploy: GitHub → Actions → "Deploy Backend to Cloud Run" → Run workflow

### If Something Goes Wrong
1. Check workflow output — preflight step shows missing variables
2. Check smoke test output — shows HTTP status and debugging steps
3. Check Cloud Run → Logs for application errors

---

## Why These Changes

| Problem | Solution |
|---------|----------|
| Workflow would silently skip or succeed with missing config | Preflight step fails fast with clear instructions |
| Health check didn't fail workflow on non-200 | Now retries and fails with debugging info |
| Users confused by failing `rmgpgab-...` Cloud Build check | New doc explains what it is and how to disable it |
| Users unsure which variables go where | New quick reference doc with GCP console locations |
| Users confused by "Create credentials" button after enabling APIs | Note in setup doc: "Ignore this button" |
| Users try to paste ghcr.io URLs into Cloud Run UI | Troubleshooting section explains why and what to do |

---

## Files in This PR

```
.github/workflows/backend_cloudrun_staging.yml  (hardened)
docs/ops/disable_cloud_build_trigger.md         (new)
docs/ops/github_variables_for_staging.md        (new)
docs/ops/gcp_staging_cloudrun_setup.md          (updated)
docs/ops/cloud_run_staging_clickthrough.md      (updated)
REPORTS/CTO_STAGING_HARDENING.md                (this report)
```

---

## Related Work

- PR #20: Initial GitHub Actions deploy workflow (merged)
- PR #14: Branch protection + CODEOWNERS
- PR #16: GHCR image publishing
