# GCP Staging Cloud Run Setup (Complete Guide)

This guide shows you how to set up automatic deployment from GitHub to Cloud Run.

**What this does:** Every time you push code to `main`, GitHub automatically builds your backend and deploys it to Cloud Run.

---

## Overview

```
GitHub (push to main)
    ↓
GitHub Actions (builds Docker image)
    ↓
Google Artifact Registry (stores image)
    ↓
Cloud Run (runs your backend)
    ↓
https://your-service-xxxxx.run.app
```

---

## Step 1: Enable GCP APIs

1. Go to: **console.cloud.google.com**
2. Select your project (top left dropdown)
3. Click the **☰ menu** → **APIs & Services** → **Library**
4. Search and enable each of these:
   - **Cloud Run Admin API**
   - **Artifact Registry API**
   - **IAM Service Account Credentials API**
   - **Cloud Resource Manager API**

> 💡 **Note:** After enabling each API, you might see a "Create credentials" button.
> **Ignore this button!** You don't need OAuth credentials — our GitHub Actions
> workflow uses Workload Identity Federation (OIDC) instead.

Or run this in Cloud Shell (click the `>_` icon top-right):
```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com
```

---

## Step 2: Create Artifact Registry Repository

This is where your Docker images will be stored.

1. **☰ menu** → **Artifact Registry** → **Repositories**
2. Click **+ CREATE REPOSITORY**
3. Fill in:
   - **Name:** `echo`
   - **Format:** Docker
   - **Mode:** Standard
   - **Region:** `us-east1` (or your preferred region)
4. Click **CREATE**

Or run:
```bash
gcloud artifacts repositories create echo \
  --repository-format=docker \
  --location=us-east1 \
  --description="Echo backend images"
```

**Write this down:** `us-east1` (your GAR region)

---

## Step 3: Create Service Account for GitHub Actions

1. **☰ menu** → **IAM & Admin** → **Service Accounts**
2. Click **+ CREATE SERVICE ACCOUNT**
3. Fill in:
   - **Name:** `github-actions-deploy`
   - **ID:** `github-actions-deploy`
4. Click **CREATE AND CONTINUE**
5. Add these roles:
   - `Cloud Run Admin`
   - `Service Account User`
   - `Artifact Registry Writer`
6. Click **CONTINUE** → **DONE**

Or run:
```bash
PROJECT_ID=$(gcloud config get-value project)

gcloud iam service-accounts create github-actions-deploy \
  --display-name="GitHub Actions Deploy"

SA_EMAIL="github-actions-deploy@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/artifactregistry.writer"
```

**Write this down:** `github-actions-deploy@YOUR-PROJECT.iam.gserviceaccount.com`

---

## Step 4: Set Up Workload Identity Federation (OIDC)

This lets GitHub Actions authenticate to GCP without storing passwords.

### 4a. Create Workload Identity Pool

1. **☰ menu** → **IAM & Admin** → **Workload Identity Federation**
2. Click **CREATE POOL**
3. Fill in:
   - **Name:** `github-actions`
   - **Pool ID:** `github-actions`
4. Click **CONTINUE**

### 4b. Create Provider

1. Select: **OpenID Connect (OIDC)**
2. Fill in:
   - **Provider name:** `github`
   - **Provider ID:** `github`
   - **Issuer URL:** `https://token.actions.githubusercontent.com`
3. Under **Attribute Mapping**, add:
   - `google.subject` = `assertion.sub`
   - `attribute.repository` = `assertion.repository`
4. Click **SAVE**

Or run:
```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Create pool
gcloud iam workload-identity-pools create github-actions \
  --location="global" \
  --display-name="GitHub Actions"

# Create provider
gcloud iam workload-identity-pools providers create-oidc github \
  --location="global" \
  --workload-identity-pool="github-actions" \
  --display-name="GitHub" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### 4c. Allow GitHub to Use Service Account

Run this (replace `yosiwizman/echo` with your repo):
```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SA_EMAIL="github-actions-deploy@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/attribute.repository/yosiwizman/echo"
```

### 4d. Get the Provider Resource Name

Run this and copy the output:
```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
echo "projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/providers/github"
```

**Write this down:** This is your `GCP_WIF_PROVIDER` value.

---

## Step 5: Add GitHub Repository Variables

1. Go to: **github.com/yosiwizman/echo** → **Settings** → **Secrets and variables** → **Actions**
2. Click the **Variables** tab
3. Click **New repository variable** for each:

| Variable Name | Value | Example |
|---------------|-------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | `my-project-123` |
| `GCP_REGION` | Region for GAR & Cloud Run | `us-east1` |
| `GAR_REPO` | Artifact Registry repo name | `echo` |
| `CLOUD_RUN_SERVICE` | Cloud Run service name | `echo-backend-staging` |
| `GCP_WIF_PROVIDER` | From step 4d | `projects/123456/locations/global/workloadIdentityPools/github-actions/providers/github` |
| `GCP_SERVICE_ACCOUNT` | From step 3 | `github-actions-deploy@my-project-123.iam.gserviceaccount.com` |

---

## Step 6: Run Your First Deploy

### Option A: Manual Deploy (Recommended first time)

1. Go to: **github.com/yosiwizman/echo** → **Actions**
2. Click **Deploy Backend to Cloud Run (Staging)** in the left sidebar
3. Click **Run workflow** (blue button on right)
4. Click **Run workflow** in the popup
5. Wait for it to complete (5-10 minutes)
6. Click the completed run to see the **Service URL**

### Option B: Automatic Deploy

Just push any change to `services/echo_backend/` on `main` branch:
```bash
git add .
git commit -m "trigger deploy"
git push origin main
```

---

## Step 7: Test Your Service

After deploy, you'll see a URL like:
```
https://echo-backend-staging-xxxxx-ue.a.run.app
```

Test it:
- **Health:** `https://YOUR-URL/healthz`
- **API Docs:** `https://YOUR-URL/docs`

---

## Troubleshooting

### "Missing required GitHub Variables"
Go to repo Settings → Secrets and variables → Actions → Variables and add all 6 variables from Step 5.

### "Permission denied" during auth
- Check that the WIF provider name is correct (Step 4d)
- Check that the service account has all 3 roles (Step 3)
- Check that the GitHub repo is allowed (Step 4c)

### "Repository not found" in Artifact Registry
- Create the repository first (Step 2)
- Make sure the region matches `GCP_REGION`

### Old Cloud Build check still failing
If you previously used "Connect repository", disable that trigger:
1. **☰ menu** → **Cloud Build** → **Triggers**
2. Find the trigger named `rmgpgab-echo-backend-...` or similar
3. Click the **⋮** menu → **Disable** or **Delete**

This check is NOT required for merging PRs.

See `docs/ops/disable_cloud_build_trigger.md` for detailed click-by-click instructions.

### Cloud Run UI rejects `ghcr.io` images
If you try to paste a `ghcr.io/...` URL directly into Cloud Run's deploy form, it won't work.

Cloud Run's UI only accepts images from:
- Google Container Registry (`gcr.io`)
- Artifact Registry (`docker.pkg.dev`)
- Artifact Registry remote repositories (advanced setup)

**Solution:** Use GitHub Actions to push to Artifact Registry instead of ghcr.io.
That's what this guide sets up! The workflow pushes to `docker.pkg.dev`, which Cloud Run accepts.

---

## Adding Environment Variables

Your backend needs API keys and secrets to work. Add them in Cloud Run:

1. **☰ menu** → **Cloud Run** → click your service
2. Click **Edit & Deploy New Revision**
3. Expand **Container, Variables & Secrets**
4. Click **Variables & Secrets** → **+ Add Variable**
5. Add your env vars (see `services/echo_backend/.env.template` for list)
6. Click **Deploy**

For secrets, use **Reference a Secret** instead of plain text values.

---

## Quick Reference

| What | Where |
|------|-------|
| Run deploy | GitHub → Actions → Deploy Backend to Cloud Run → Run workflow |
| Check deploy status | GitHub → Actions → latest run |
| See service URL | Cloud Run → your service → URL at top |
| Add env vars | Cloud Run → service → Edit & Deploy → Variables |
| View logs | Cloud Run → service → Logs tab |
| Disable old trigger | Cloud Build → Triggers → ⋮ → Disable |
