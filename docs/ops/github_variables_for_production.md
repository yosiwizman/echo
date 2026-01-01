# GitHub Variables for Production Deployment

Quick reference for all the GitHub repository variables needed for the **production** Cloud Run deployment.

> 📝 Production variables use the `_PROD` suffix to separate from staging.

---

## Where to Add Variables

1. Go to your GitHub repo
2. Click **Settings** (gear icon, top right)
3. In the left sidebar: **Secrets and variables** → **Actions**
4. Click the **Variables** tab (not Secrets!)
5. Click **New repository variable**

Direct link: `https://github.com/YOUR-ORG/YOUR-REPO/settings/variables/actions`

---

## Required Variables (Must Have These)

| Variable | Description | Example |
|----------|-------------|---------|
| `GCP_PROJECT_ID_PROD` | GCP project ID for production | `echo-staging-483002` |
| `GCP_WIF_PROVIDER_PROD` | Workload Identity Federation provider | `projects/1051039678986/locations/global/workloadIdentityPools/echo-staging-gha/providers/github` |
| `GCP_SERVICE_ACCOUNT_PROD` | Service account email | `github-deploy@echo-staging-483002.iam.gserviceaccount.com` |

---

## Optional Variables (Have Defaults)

| Variable | Default | When to Change |
|----------|---------|----------------|
| `GCP_REGION_PROD` | `europe-west1` | If using a different region |
| `GAR_REPO_PROD` | `echo-backend` | If using a different Artifact Registry repo |
| `CLOUD_RUN_SERVICE_PROD` | `echo-backend` | If you want a different service name |

---

## Copy-Paste Values (Using Same Project as Staging)

If you're using the same GCP project for both staging and production:

```
GCP_PROJECT_ID_PROD = echo-staging-483002
GCP_REGION_PROD = europe-west1
GAR_REPO_PROD = echo-backend
CLOUD_RUN_SERVICE_PROD = echo-backend
GCP_WIF_PROVIDER_PROD = projects/1051039678986/locations/global/workloadIdentityPools/echo-staging-gha/providers/github
GCP_SERVICE_ACCOUNT_PROD = github-deploy@echo-staging-483002.iam.gserviceaccount.com
```

---

## Checklist Before First Production Deploy

- [ ] Staging deployment is working and tested
- [ ] Added all 3 required production variables (`_PROD` suffix)
- [ ] (Optional) Added optional variables if using non-default values
- [ ] Understand how to trigger: tag push (`backend-prod-v*`) or manual dispatch

---

## How to Deploy to Production

### Option 1: Tag Push (Recommended)
```bash
git tag backend-prod-v1.0.0
git push origin backend-prod-v1.0.0
```

### Option 2: Manual Dispatch
1. GitHub → Actions → "Deploy Backend to Cloud Run (Production)"
2. Click "Run workflow"
3. Type `deploy` to confirm
4. Click "Run workflow"

---

## Troubleshooting

### "Missing required GitHub Variables" in workflow
Check that you added all 3 required variables with the `_PROD` suffix.

### Workflow runs but job is skipped
- `GCP_PROJECT_ID_PROD` must be set (not empty)
- For manual dispatch, you must type `deploy` exactly

### "Permission denied" during deployment
- Verify `GCP_WIF_PROVIDER_PROD` is correct (uses project NUMBER, not ID)
- Verify the service account has required roles

---

## Production vs Staging Variables

| Purpose | Staging Variable | Production Variable |
|---------|------------------|---------------------|
| Project ID | `GCP_PROJECT_ID` | `GCP_PROJECT_ID_PROD` |
| Region | `GCP_REGION` | `GCP_REGION_PROD` |
| GAR Repo | `GAR_REPO` | `GAR_REPO_PROD` |
| Service Name | `CLOUD_RUN_SERVICE` | `CLOUD_RUN_SERVICE_PROD` |
| WIF Provider | `GCP_WIF_PROVIDER` | `GCP_WIF_PROVIDER_PROD` |
| Service Account | `GCP_SERVICE_ACCOUNT` | `GCP_SERVICE_ACCOUNT_PROD` |

---

## Related Docs

- Full production setup: `docs/ops/gcp_production_cloudrun_setup.md`
- Staging variables: `docs/ops/github_variables_for_staging.md`
- Staging setup: `docs/ops/gcp_staging_cloudrun_setup.md`
