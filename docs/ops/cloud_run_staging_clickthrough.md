# Cloud Run: How to Redeploy and Test (Simple Guide)

This is a super simple guide. Just follow the steps!

---

## 🔄 How to Redeploy After Code Changes

### Step 1: Go to Cloud Build
1. Open your browser
2. Go to: **console.cloud.google.com**
3. Make sure your project is selected (top left dropdown)
4. Click the **☰ menu** (3 lines, top left)
5. Scroll down and click **Cloud Build** → **Triggers**

### Step 2: Run the Build
1. Find your trigger (it might be called "echo-backend" or similar)
2. Click the **"Run"** button on the right side
3. A popup appears → click **"Run trigger"**
4. Wait 5-10 minutes for the build to finish

### Step 3: Check if Build Succeeded
1. Click **Cloud Build** → **History** in the left menu
2. You'll see your build with a status:
   - ✅ **Green checkmark** = Success!
   - ❌ **Red X** = Failed (check logs by clicking on it)

---

## 🌐 How to See Your Running Service

### Step 1: Go to Cloud Run
1. Click the **☰ menu** (3 lines, top left)
2. Click **Cloud Run**
3. You'll see a list of services

### Step 2: Open Your Service
1. Click on your service name (like **"echo-backend-staging"**)
2. At the top, you'll see a **URL** that looks like:
   ```
   https://echo-backend-staging-xxxxx-uc.a.run.app
   ```
3. Click that URL to open your service!

### Step 3: Test if It's Working
Try these URLs in your browser:

| What to test | Add this to your URL |
|--------------|---------------------|
| Health check | `/healthz` |
| API docs | `/docs` |

**Example:** If your URL is `https://echo-backend-staging-abc123.run.app`, test:
- `https://echo-backend-staging-abc123.run.app/healthz`
- `https://echo-backend-staging-abc123.run.app/docs`

---

## ⚙️ How to Change Settings (Environment Variables)

### When to do this
- When you need to add API keys
- When you need to change configuration

### Steps
1. Go to **Cloud Run** → click your service
2. Click **"Edit & Deploy New Revision"** button (top of page)
3. Scroll down to **"Container, Variables & Secrets, Connections, Security"**
4. Click to expand **"Variables & Secrets"**
5. Click **"+ Add Variable"** to add environment variables
6. Click **"Deploy"** when done

### Important Notes
- **PORT** is set automatically by Cloud Run - don't change it!
- For secrets like API keys, use **"Reference a Secret"** instead of plain text

---

## ❓ Something Not Working?

### Build Failed
1. Go to **Cloud Build** → **History**
2. Click on the failed build
3. Read the error message in the logs
4. Common fixes:
   - Check if there's a typo in the code
   - Make sure all files are committed and pushed to GitHub

### Service Won't Start
1. Go to **Cloud Run** → click your service
2. Click the **"Logs"** tab
3. Look for red error messages
4. Common fixes:
   - Missing environment variables (add them in Variables & Secrets)
   - Wrong API keys

### Need Help?
Check the detailed docs: `docs/ops/staging_cloudrun.md`

---

## 📋 Quick Reference

| Task | Where to Click |
|------|----------------|
| Rebuild | Cloud Build → Triggers → Run |
| Check build status | Cloud Build → History |
| See service URL | Cloud Run → [your service] → URL at top |
| Change settings | Cloud Run → [service] → Edit & Deploy |
| View logs | Cloud Run → [service] → Logs tab |
