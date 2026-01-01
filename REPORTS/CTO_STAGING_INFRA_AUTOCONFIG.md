# Echo — CTO Report: GCP Staging Infrastructure Auto-Configuration
Date: 2026-01-01
Author: Senior DevOps / Platform Engineer

## Executive Summary

Fully automated provisioning of GCP staging infrastructure for GitHub Actions → Artifact Registry → Cloud Run deployment pipeline using Workload Identity Federation (OIDC).

**Result:** Staging deploys now run on every push to `main` (backend paths) and pass smoke tests.

---

## What Was Changed/Created

### 1. Legacy Cloud Build Trigger — DELETED
| Property | Value |
|----------|-------|
| Trigger Name | `rmgpgab-echo-backend-staging-europe-west1-yosiwizman-echo--mhod` |
| Trigger ID | `602a5cea-b447-42f4-bb6f-473c05b211b1` |
| Action | Deleted via `gcloud builds triggers delete` |
| Effect | No more failing `rmgpgab-...` GitHub status checks |

### 2. GCP APIs Enabled
- `run.googleapis.com` (Cloud Run Admin)
- `artifactregistry.googleapis.com` (Artifact Registry)
- `iam.googleapis.com` (IAM)
- `iamcredentials.googleapis.com` (IAM Credentials)
- `sts.googleapis.com` (Security Token Service)
- `cloudresourcemanager.googleapis.com` (Resource Manager)

### 3. Artifact Registry Repository
| Property | Value |
|----------|-------|
| Name | `echo-backend` |
| Location | `europe-west1` |
| Format | Docker |
| Full Path | `europe-west1-docker.pkg.dev/echo-staging-483002/echo-backend` |

### 4. Service Account for GitHub Actions
| Property | Value |
|----------|-------|
| Email | `github-deploy@echo-staging-483002.iam.gserviceaccount.com` |
| Display Name | GitHub Actions Deploy |
| Roles | `roles/run.admin`, `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser` |

### 5. Workload Identity Federation (OIDC)
| Property | Value |
|----------|-------|
| Pool ID | `echo-staging-gha` |
| Pool Name | Echo Staging GitHub Actions |
| Provider ID | `github` |
| Issuer | `https://token.actions.githubusercontent.com` |
| Attribute Mapping | `google.subject=assertion.sub`, `attribute.repository=assertion.repository` |
| Attribute Condition | `assertion.repository=='yosiwizman/echo'` |
| Full Provider Resource | `projects/1051039678986/locations/global/workloadIdentityPools/echo-staging-gha/providers/github` |

**Security:** Only `yosiwizman/echo` repository can request tokens that impersonate the service account.

### 6. GitHub Repository Variables Set
| Variable | Value |
|----------|-------|
| `GCP_PROJECT_ID` | `echo-staging-483002` |
| `GCP_REGION` | `europe-west1` |
| `GAR_REPO` | `echo-backend` |
| `CLOUD_RUN_SERVICE` | `echo-backend-staging` |
| `GCP_WIF_PROVIDER` | `projects/1051039678986/locations/global/workloadIdentityPools/echo-staging-gha/providers/github` |
| `GCP_SERVICE_ACCOUNT` | `github-deploy@echo-staging-483002.iam.gserviceaccount.com` |

### 7. Workflow Fixes (PR #22)
- Changed smoke test endpoint from `/healthz` to `/health` (more reliable)
- Added `--allow-unauthenticated` flag for public health check access

---

## Current State

| Component | Status | URL/Resource |
|-----------|--------|--------------|
| Cloud Run Service | ✅ Running | `https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app` |
| Health Check | ✅ Passing | `GET /health` → `{"status":"ok"}` |
| Deploy Workflow | ✅ Working | GitHub Actions → GAR → Cloud Run |
| Legacy Trigger | ❌ Deleted | No more `rmgpgab-...` noise |

---

## How to Operate

### Manual Deploy
1. GitHub → Actions → "Deploy Backend to Cloud Run (Staging)"
2. Click "Run workflow" → "Run workflow"

### Automatic Deploy
Push to `main` branch touching:
- `services/echo_backend/**`
- `Dockerfile`
- `.dockerignore`
- `.github/workflows/backend_cloudrun_staging.yml`
- `docs/ops/**`

### View Logs
1. GCP Console → Cloud Run → `echo-backend-staging`
2. Click "Logs" tab

---

## How to Roll Back / Undo

### Delete Service Account
```bash
gcloud iam service-accounts delete github-deploy@echo-staging-483002.iam.gserviceaccount.com
```

### Delete WIF Pool (removes pool and provider)
```bash
gcloud iam workload-identity-pools delete echo-staging-gha --location=global
```

### Delete Artifact Registry Repo
```bash
gcloud artifacts repositories delete echo-backend --location=europe-west1
```

### Delete Cloud Run Service
```bash
gcloud run services delete echo-backend-staging --region=europe-west1
```

### Remove GitHub Variables
```bash
gh variable delete GCP_PROJECT_ID --repo yosiwizman/echo
gh variable delete GCP_REGION --repo yosiwizman/echo
gh variable delete GAR_REPO --repo yosiwizman/echo
gh variable delete CLOUD_RUN_SERVICE --repo yosiwizman/echo
gh variable delete GCP_WIF_PROVIDER --repo yosiwizman/echo
gh variable delete GCP_SERVICE_ACCOUNT --repo yosiwizman/echo
```

---

## Key Resource IDs (for reference)

| Resource | ID |
|----------|-----|
| GCP Project ID | `echo-staging-483002` |
| GCP Project Number | `1051039678986` |
| WIF Pool | `echo-staging-gha` |
| WIF Provider | `github` |
| Service Account | `github-deploy` |
| GAR Repository | `echo-backend` |
| Cloud Run Service | `echo-backend-staging` |
| Cloud Run Region | `europe-west1` |

---

## Related PRs

- PR #21: Staging hardening + docs
- PR #22: Health endpoint fix + allow-unauthenticated
