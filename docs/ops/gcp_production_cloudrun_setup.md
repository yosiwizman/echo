# GCP Production Cloud Run Setup (Complete Guide)

This guide shows you how to set up **production** deployment from GitHub to Cloud Run.

> ⚠️ **Important:** This is for PRODUCTION. Make sure you've tested in staging first!

---

## Overview

```
GitHub (tag push or manual trigger)
    ↓
GitHub Actions (builds Docker image)
    ↓
Google Artifact Registry (stores image)
    ↓
Cloud Run (runs your backend)
    ↓
https://echo-backend-xxxxx.run.app
```

---

## Prerequisites

Before setting up production, you should have:
- ✅ Staging deployment working (see `docs/ops/gcp_staging_cloudrun_setup.md`)
- ✅ GCP project with billing enabled
- ✅ GitHub repo access with admin permissions

---

## Production vs Staging

| Aspect | Staging | Production |
|--------|---------|------------|
| Service name | `echo-backend-staging` | `echo-backend` |
| Trigger | Push to main | Tag push (`backend-prod-v*`) or manual |
| Variables | `GCP_PROJECT_ID` | `GCP_PROJECT_ID_PROD` |
| Instances | 0-3 | 0-3 (configurable) |

---

## Step 1: Reuse Staging Infrastructure (Recommended)

For simplicity, we'll use the **same GCP project** as staging. This means:
- ✅ Same Artifact Registry repo
- ✅ Same service account
- ✅ Same Workload Identity Federation pool

If you want a separate production project, follow the staging setup guide for a new project.

---

## Step 2: Add Production GitHub Variables

1. Go to: **github.com/YOUR-ORG/echo** → **Settings** → **Secrets and variables** → **Actions**
2. Click the **Variables** tab
3. Click **New repository variable** for each:

| Variable Name | Value | Notes |
|---------------|-------|-------|
| `GCP_PROJECT_ID_PROD` | `echo-staging-483002` | Same project as staging |
| `GCP_REGION_PROD` | `europe-west1` | Same region as staging |
| `GAR_REPO_PROD` | `echo-backend` | Same GAR repo as staging |
| `CLOUD_RUN_SERVICE_PROD` | `echo-backend` | Production service name |
| `GCP_WIF_PROVIDER_PROD` | `projects/1051039678986/locations/global/workloadIdentityPools/echo-staging-gha/providers/github` | Same WIF provider |
| `GCP_SERVICE_ACCOUNT_PROD` | `github-deploy@echo-staging-483002.iam.gserviceaccount.com` | Same service account |

---

## Step 3: Deploy to Production

### Option A: Tag-based Deploy (Recommended for releases)

1. Create and push a tag:
   ```bash
   git tag backend-prod-v1.0.0
   git push origin backend-prod-v1.0.0
   ```

2. The workflow triggers automatically on tag push

3. Watch progress: **GitHub → Actions → Deploy Backend to Cloud Run (Production)**

### Option B: Manual Deploy (For urgent fixes)

1. Go to: **github.com/YOUR-ORG/echo** → **Actions**
2. Click **Deploy Backend to Cloud Run (Production)** in the left sidebar
3. Click **Run workflow**
4. Type `deploy` in the confirmation field (required!)
5. Click **Run workflow**

---

## Step 4: Verify Production

After deploy, you'll see a URL like:
```
https://echo-backend-xxxxx-ew.a.run.app
```

Test it:
- **Root:** `https://YOUR-URL/` → Should show service info JSON
- **Health:** `https://YOUR-URL/health` → `{"status":"ok"}`
- **API Docs:** `https://YOUR-URL/docs`

---

## Scaling Configuration

Default production settings:
- **min-instances:** 0 (scales to zero when idle - saves money)
- **max-instances:** 3 (limits costs during traffic spikes)
- **concurrency:** 80 (requests per instance)

### To change scaling:

**Option 1:** Edit the workflow file (`.github/workflows/backend_cloudrun_production.yml`):
```yaml
flags: '--allow-unauthenticated --min-instances=1 --max-instances=10'
```

**Option 2:** Use GCP Console:
1. **☰ menu** → **Cloud Run** → click `echo-backend`
2. Click **Edit & Deploy New Revision**
3. Scroll to **Container, Networking, Security**
4. Adjust **Autoscaling** settings
5. Click **Deploy**

---

## Troubleshooting

### Workflow skipped (no job ran)
- Check that `GCP_PROJECT_ID_PROD` is set
- For manual dispatch, make sure you typed `deploy` exactly

### "Permission denied" during auth
- Verify `GCP_WIF_PROVIDER_PROD` uses the correct project number
- Verify the service account has all required roles

### Health check fails
- Check Cloud Run → Logs for startup errors
- Verify environment variables are set in Cloud Run

### Service returns 404 on root
- Update to latest version (root route was added)
- Check that the new code deployed successfully

---

## Quick Reference

| Task | How |
|------|-----|
| Deploy via tag | `git tag backend-prod-v1.2.3 && git push origin backend-prod-v1.2.3` |
| Manual deploy | GitHub → Actions → Production workflow → Run workflow → type "deploy" |
| Check status | GitHub → Actions → latest production run |
| View logs | GCP Console → Cloud Run → echo-backend → Logs |
| Roll back | Deploy a previous tag or use Cloud Run → Revisions |

---

## Related Docs

- Staging setup: `docs/ops/gcp_staging_cloudrun_setup.md`
- GitHub variables: `docs/ops/github_variables_for_production.md`
- Disable Cloud Build: `docs/ops/disable_cloud_build_trigger.md`
