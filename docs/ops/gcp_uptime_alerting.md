# GCP Cloud Monitoring - Uptime Checks & Alerting

This document describes the GCP Cloud Monitoring uptime checks and alerting configuration for Echo backend services.

## Overview

The monitoring setup provides:

1. **Email Notification Channel** - Receives alerts when uptime checks fail
2. **Uptime Checks** - Monitor `/health` endpoint every 60 seconds
   - Staging: `echo-backend-staging-zxuvsjb5qa-ew.a.run.app`
   - Production: `echo-backend-zxuvsjb5qa-ew.a.run.app`
3. **Alert Policies** - Trigger alerts when health checks fail for 120+ seconds

## What Gets Created

| Resource | Staging | Production |
|----------|---------|------------|
| Uptime Check | Echo Backend STAGING - Health Check | Echo Backend PROD - Health Check |
| Alert Policy | Echo Backend STAGING - Uptime Failed | Echo Backend PROD - Uptime Failed |
| Notification Channel | Echo Ops Alerts (Email) | (shared) |

### Uptime Check Configuration

- **Endpoint**: `/health`
- **Method**: GET
- **Port**: 443 (HTTPS)
- **SSL Validation**: Enabled
- **Check Interval**: 60 seconds
- **Timeout**: 10 seconds
- **Content Validation**: JSON path `$.status` must equal `"ok"`

### Alert Policy Configuration

- **Condition**: Uptime check success count < 1
- **Duration**: 120 seconds (reduces noise from transient failures)
- **Trigger**: Count = 1 (fires after single duration window)

## Running the Apply Script

### Prerequisites

1. **gcloud CLI** installed and authenticated
2. **Python 3.6+** installed
3. Required IAM permissions (see below)

### Execute

```bash
# Navigate to monitoring directory
cd ops/gcp/monitoring

# Set alert email and run
ALERT_EMAIL="your@email.com" bash apply_monitoring.sh
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALERT_EMAIL` | Yes | - | Email address for alerts |
| `PROJECT_ID` | No | `echo-staging-483002` | GCP project ID |
| `STAGING_BASE_URL` | No | Cloud Run staging URL | Staging service URL |
| `PROD_BASE_URL` | No | Cloud Run prod URL | Production service URL |

### Required IAM Permissions

The user or service account running the script needs:

```
monitoring.notificationChannels.list
monitoring.notificationChannels.create
monitoring.notificationChannels.update
monitoring.uptimeCheckConfigs.list
monitoring.uptimeCheckConfigs.create
monitoring.uptimeCheckConfigs.update
monitoring.alertPolicies.list
monitoring.alertPolicies.create
monitoring.alertPolicies.update
serviceusage.services.enable (if API not enabled)
```

**Recommended Role**: `roles/monitoring.editor`

## Email Verification Requirement

**IMPORTANT**: Email notification channels require recipient verification.

After running the apply script:
1. Check inbox for email from `noreply@google.com` (subject: "Confirm your subscription...")
2. Click the confirmation link in the email
3. Alerts will NOT be delivered until email is verified

You can check verification status in the GCP Console:
`Monitoring → Alerting → Notification channels`

## Manual Verification Steps

After running the apply script, verify the setup:

### 1. Check Uptime Status

**Console**: [Monitoring → Uptime checks](https://console.cloud.google.com/monitoring/uptime?project=echo-staging-483002)

Expected:
- Both checks show "Passing" status
- Green checkmarks on the map visualization

**CLI**:
```bash
# List uptime checks
gcloud beta monitoring uptime list-configs --project=echo-staging-483002

# Check recent results (via API)
curl -s https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/health | jq .
curl -s https://echo-backend-zxuvsjb5qa-ew.a.run.app/health | jq .
```

### 2. Check Alert Policies

**Console**: [Monitoring → Alerting](https://console.cloud.google.com/monitoring/alerting?project=echo-staging-483002)

Expected:
- Both alert policies listed and enabled
- Status shows "No incidents"

### 3. Check Notification Channel

**Console**: [Monitoring → Alerting → Edit notification channels](https://console.cloud.google.com/monitoring/alerting/notifications?project=echo-staging-483002)

Expected:
- Email channel listed under "Email"
- Shows "Verified" badge (after email confirmation)

## Troubleshooting

### Uptime Check Shows "Failing"

1. **Check endpoint directly**:
   ```bash
   curl -v https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app/health
   ```

2. **Check Cloud Run logs**:
   - [Staging logs](https://console.cloud.google.com/run/detail/europe-west1/echo-backend-staging/logs?project=echo-staging-483002)
   - [Prod logs](https://console.cloud.google.com/run/detail/europe-west1/echo-backend/logs?project=echo-staging-483002)

3. **Verify response format**:
   The `/health` endpoint must return:
   ```json
   {"status": "ok", ...}
   ```

### Alert Not Firing

1. Check alert policy is enabled
2. Verify notification channel is connected to policy
3. Confirm email is verified

### Script Errors

**"Not authenticated with gcloud"**:
```bash
gcloud auth login
```

**"Permission denied"**:
- Ensure you have `roles/monitoring.editor` or equivalent permissions

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   GCP Cloud Monitoring                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐       ┌─────────────────┐         │
│  │  Uptime Check   │       │  Uptime Check   │         │
│  │    (Staging)    │       │    (Prod)       │         │
│  └────────┬────────┘       └────────┬────────┘         │
│           │                         │                   │
│           ▼                         ▼                   │
│  ┌─────────────────┐       ┌─────────────────┐         │
│  │  Alert Policy   │       │  Alert Policy   │         │
│  │   (Staging)     │       │    (Prod)       │         │
│  └────────┬────────┘       └────────┬────────┘         │
│           │                         │                   │
│           └─────────┬───────────────┘                   │
│                     ▼                                   │
│           ┌─────────────────┐                          │
│           │  Email Channel  │                          │
│           │   (Shared)      │                          │
│           └────────┬────────┘                          │
│                    │                                    │
└────────────────────┼────────────────────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ Alert Email │
              └─────────────┘
```

## Files Reference

| File | Purpose |
|------|---------|
| `ops/gcp/monitoring/apply_monitoring.sh` | Main orchestration script |
| `ops/gcp/monitoring/templates/*.template.json` | Template configs with placeholders |
| `ops/gcp/monitoring/lib/*.py` | Python helper scripts |
| `ops/gcp/monitoring/state/*.json` | Tracked resource state (committed) |
| `ops/gcp/monitoring/generated/` | Rendered configs (gitignored) |

## Related Documentation

- [Runtime Smoke Monitoring](runtime_smoke_monitoring.md) - GitHub Actions-based monitoring
- [GCP Staging Cloud Run Setup](gcp_staging_cloudrun_setup.md)
- [GCP Production Cloud Run Setup](gcp_production_cloudrun_setup.md)
