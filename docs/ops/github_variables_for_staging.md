# GitHub Variables for Staging Deployment

Quick reference for all the GitHub repository variables needed for the Cloud Run staging deployment.

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

| Variable | Description | Where to Find in GCP | Example |
|----------|-------------|---------------------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | Top-left dropdown in console, or Project Settings | `my-project-123456` |
| `GCP_WIF_PROVIDER` | Workload Identity Federation provider resource name | IAM → Workload Identity Federation → Pool → Provider | `projects/123456789/locations/global/workloadIdentityPools/github-actions/providers/github` |
| `GCP_SERVICE_ACCOUNT` | Service account email for deployments | IAM → Service Accounts | `github-actions-deploy@my-project-123456.iam.gserviceaccount.com` |

---

## Optional Variables (Have Defaults)

| Variable | Description | Default | When to Change |
|----------|-------------|---------|----------------|
| `GCP_REGION` | Region for Artifact Registry & Cloud Run | `us-east1` | If your GAR repo is in a different region |
| `GAR_REPO` | Artifact Registry repository name | `echo` | If you named your repo differently |
| `CLOUD_RUN_SERVICE` | Cloud Run service name | `echo-backend-staging` | If you want a different service name |

---

## How to Find Each Value

### GCP_PROJECT_ID

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Look at the **top-left dropdown** next to "Google Cloud"
3. Your project name and ID are shown there
4. Or go to **☰ menu** → **IAM & Admin** → **Settings** → look for "Project ID"

**Format:** Letters, numbers, hyphens (e.g., `my-project-123456`)

### GCP_WIF_PROVIDER

1. Go to **☰ menu** → **IAM & Admin** → **Workload Identity Federation**
2. Click your pool (probably `github-actions`)
3. Click your provider (probably `github`)
4. Look for **"Provider resource name"** — it's a long string

**Format:** `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID`

**Important:** This uses the numeric PROJECT_NUMBER, not the PROJECT_ID!

Or run this in Cloud Shell:
```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
echo "projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/providers/github"
```

### GCP_SERVICE_ACCOUNT

1. Go to **☰ menu** → **IAM & Admin** → **Service Accounts**
2. Find the service account you created for deployments (e.g., `github-actions-deploy`)
3. Copy the **Email** column value

**Format:** `SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com`

### GCP_REGION

Use the same region as your Artifact Registry repository.

1. Go to **☰ menu** → **Artifact Registry** → **Repositories**
2. Look at the **Location** column

**Common values:** `us-east1`, `us-central1`, `us-west1`, `europe-west1`, `asia-east1`

### GAR_REPO

The name of your Artifact Registry repository.

1. Go to **☰ menu** → **Artifact Registry** → **Repositories**
2. Copy the **Name** of your Docker repository

**Default:** `echo`

### CLOUD_RUN_SERVICE

The name you want for your Cloud Run service.

**Default:** `echo-backend-staging`

---

## Checklist Before First Deploy

- [ ] Created Artifact Registry repository
- [ ] Created service account with roles: `Cloud Run Admin`, `Service Account User`, `Artifact Registry Writer`
- [ ] Set up Workload Identity Federation pool and provider
- [ ] Allowed GitHub repo to impersonate service account
- [ ] Added all 3 required GitHub variables
- [ ] (Optional) Added optional variables if using non-default values

---

## Troubleshooting

### "Missing required GitHub Variables" in workflow

You haven't added all required variables. Check the Variables tab (not Secrets!).

### "Permission denied" or "403 Forbidden"

- Double-check `GCP_WIF_PROVIDER` — it needs the numeric project number
- Make sure the service account has all 3 roles
- Make sure the GitHub repo is allowed in the WIF binding

### Variables not being read

- Make sure you added them to **Variables**, not **Secrets**
- Variable names are case-sensitive
- Re-run the workflow after adding variables

---

## Related Docs

- Full setup guide: `docs/ops/gcp_staging_cloudrun_setup.md`
- Simple deploy guide: `docs/ops/cloud_run_staging_clickthrough.md`
- Disable old trigger: `docs/ops/disable_cloud_build_trigger.md`
