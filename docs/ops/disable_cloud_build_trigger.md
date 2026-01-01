# How to Disable the Legacy Cloud Build Trigger

## Why You're Reading This

You might see a **failing GitHub check** on your pull requests that looks like:
```
rmgpgab-echo-backend-staging-... (Cloud Build)
```

This check is **NOT required for merging** — it's just noisy. This guide shows you how to turn it off.

---

## What Is This Check?

When you use Cloud Run's "Connect repository" feature, GCP automatically creates a **Cloud Build trigger**. This trigger:
- Runs on every push to your repo
- Reports back to GitHub as a status check
- Often fails due to resource limits (pip install timeouts, etc.)

The trigger was created when someone set up Cloud Run through the GCP console using "Continuously deploy from a repository."

---

## Why Disable It?

1. **We now use GitHub Actions** — The workflow in `.github/workflows/backend_cloudrun_staging.yml` handles deployments
2. **The Cloud Build check is redundant** — We don't need two deployment systems
3. **It's noisy** — Seeing a failing check on every PR is confusing

---

## How to Disable (Click-by-Click)

### Option 1: Disable the Trigger (Keep It Around)

1. **Open Cloud Build Triggers:**
   - Go to: [console.cloud.google.com/cloud-build/triggers](https://console.cloud.google.com/cloud-build/triggers)
   - Or: **☰ menu** → **Cloud Build** → **Triggers**

2. **Find the trigger:**
   - Look for one named like `rmgpgab-echo-backend-staging-...`
   - It will show "Source: GitHub" and your repo name

3. **Disable it:**
   - Click the **⋮** (three dots menu) on the right
   - Click **Disable**

The check will stop running on new commits, but the trigger still exists if you want to re-enable it later.

### Option 2: Delete the Trigger (Permanent)

1. Follow steps 1-2 above to find the trigger

2. **Delete it:**
   - Click the **⋮** (three dots menu)
   - Click **Delete**
   - Confirm in the popup

The trigger is gone. The GitHub check will no longer appear.

---

## What Happens After?

- **New pushes to main:** No Cloud Build check, just the GitHub Actions deploy
- **Pull requests:** No failing Cloud Build check spam
- **Your deployment:** Still works via GitHub Actions → Artifact Registry → Cloud Run

---

## If You Want to Reconnect Later

If you ever want to use Cloud Build again:
1. Go to **Cloud Run** → your service
2. Click **Set up continuous deployment**
3. Follow the wizard

But we recommend sticking with GitHub Actions — it gives you more control and better error messages.

---

## Quick Reference

| Task | Where |
|------|-------|
| View all triggers | Cloud Build → Triggers |
| Disable a trigger | Trigger → ⋮ → Disable |
| Delete a trigger | Trigger → ⋮ → Delete |
| Console link | [cloud-build/triggers](https://console.cloud.google.com/cloud-build/triggers) |

---

## Related Docs

- Full setup guide: `docs/ops/gcp_staging_cloudrun_setup.md`
- Simple deploy guide: `docs/ops/cloud_run_staging_clickthrough.md`
- GitHub variables: `docs/ops/github_variables_for_staging.md`
