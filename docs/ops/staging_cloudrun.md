# Cloud Run Staging Deployment

This document describes how to deploy the Echo backend to Google Cloud Run for staging.

## Architecture

```
GitHub Actions (workflow_dispatch)
    │
    ├── OIDC Token Request
    │       ↓
    ├── Google Workload Identity Federation (WIF)
    │       ↓
    ├── Short-lived GCP credentials (no stored keys!)
    │       ↓
    └── Deploy to Cloud Run
            ↓
        ghcr.io/yosiwizman/echo-backend:tag
```

## Why Workload Identity Federation?

We use **GitHub OIDC + Google Workload Identity Federation** instead of service account JSON keys:

- ✅ **No long-lived secrets** - No JSON keys to rotate or leak
- ✅ **Scoped access** - Credentials only valid for specific GitHub repo/branch
- ✅ **Audit trail** - All authentications logged in GCP
- ✅ **Best practice** - Recommended by Google and GitHub for CI/CD

## One-Time GCP Setup

### 1. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  sts.googleapis.com
```

### 2. Create Workload Identity Pool

```bash
# Set your project
export PROJECT_ID="your-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Create the pool
gcloud iam workload-identity-pools create "github-actions" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create the provider
gcloud iam workload-identity-pools providers create-oidc "github" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-actions" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### 3. Create Service Account for Deployments

```bash
# Create service account
gcloud iam service-accounts create "github-actions-deploy" \
  --project="$PROJECT_ID" \
  --display-name="GitHub Actions Deploy"

export SA_EMAIL="github-actions-deploy@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Cloud Run deployment permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountUser"

# Allow GitHub Actions to impersonate this SA (restrict to your repo!)
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/attribute.repository/yosiwizman/echo"
```

### 4. Get the WIF Provider Resource Name

```bash
echo "projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/providers/github"
```

This is your `GCP_WIF_PROVIDER` value.

## GitHub Environment Setup

### Create the "staging" Environment

1. Go to: **GitHub repo → Settings → Environments → New environment**
2. Name: `staging`
3. (Optional) Add protection rules if desired

### Add Required Secrets

In the `staging` environment, add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | `my-project-123` |
| `GCP_WIF_PROVIDER` | Workload Identity Provider | `projects/123456789/locations/global/workloadIdentityPools/github-actions/providers/github` |
| `GCP_SERVICE_ACCOUNT` | Service account email | `github-actions-deploy@my-project-123.iam.gserviceaccount.com` |
| `CLOUD_RUN_REGION` | Deployment region | `us-central1` |
| `CLOUD_RUN_SERVICE` | Service name (optional) | `echo-backend-staging` |

## Backend Runtime Environment Variables

The backend requires several environment variables at runtime. Configure these in Cloud Run:

### Required for Core Functionality

See `services/echo_backend/.env.template` for the full list. Key variables:

```bash
# AI/LLM
OPENAI_API_KEY=<your-key>

# Authentication (Firebase)
SERVICE_ACCOUNT_JSON=<firebase-sa-json>
# OR use Application Default Credentials

# Vector Search
PINECONE_API_KEY=<your-key>
PINECONE_INDEX_NAME=<index-name>

# Cache/Session
REDIS_DB_HOST=<host>
REDIS_DB_PORT=<port>
REDIS_DB_PASSWORD=<password>
```

### Configure via Cloud Run Console

1. Go to Cloud Run service → **Edit & Deploy New Revision**
2. Under **Container** → **Variables & Secrets**
3. Add env vars or reference Secret Manager secrets

For sensitive values, use **Secret Manager**:
```bash
gcloud secrets create openai-api-key --replication-policy="automatic"
echo -n "sk-xxx" | gcloud secrets versions add openai-api-key --data-file=-
```

Then reference in Cloud Run as a secret env var.

## Running the Deployment

### Via GitHub UI

1. Go to: **Actions → Deploy Backend Staging (Cloud Run)**
2. Click **Run workflow**
3. (Optional) Enter a specific image tag
4. Click **Run workflow**

### Via GitHub CLI

```bash
gh workflow run deploy_backend_staging_cloudrun.yml \
  --repo yosiwizman/echo \
  -f image_tag=latest
```

## Verify Deployment

After deployment, the workflow outputs the service URL. Verify:

```bash
# Health check
curl https://echo-backend-staging-xxxxx.run.app/healthz

# Should return: {"status": "ok"} or similar
```

## Troubleshooting

### "Missing required secrets" error
Ensure all secrets are configured in the GitHub `staging` environment, not repo-level secrets.

### "Permission denied" during deploy
Check that:
1. The service account has `roles/run.admin` and `roles/iam.serviceAccountUser`
2. The WIF binding allows your specific repository

### Container fails to start
1. Check Cloud Run logs: `gcloud run services logs read echo-backend-staging`
2. Ensure required env vars are set
3. Verify the image exists: `docker pull ghcr.io/yosiwizman/echo-backend:latest`

## Files Reference

- **Service spec**: `services/echo_backend/deploy/cloudrun/staging.yaml`
- **Deploy workflow**: `.github/workflows/deploy_backend_staging_cloudrun.yml`
- **Env template**: `services/echo_backend/.env.template`
- **Docker image**: `ghcr.io/yosiwizman/echo-backend`
