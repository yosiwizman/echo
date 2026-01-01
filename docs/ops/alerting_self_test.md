# Alerting Self-Test

This document describes how to use the alerting self-test feature to verify the end-to-end alerting pipeline without causing real downtime.

## Overview

The alerting self-test allows you to trigger a real alert email by calling a protected endpoint. This verifies that:

1. The backend can log the trigger message
2. Cloud Logging captures the log line
3. The log-based metric increments
4. The alert policy fires
5. The notification channel (email) delivers the alert

## How It Works

1. **Endpoint**: `GET /ops/alert-test`
   - Protected by `X-Alert-Test-Token` header
   - Token stored in GCP Secret Manager (`echo-alert-test-token`)
   - On success, logs `ECHO_ALERT_TEST_TRIGGERED` at ERROR level

2. **Log-Based Metrics**:
   - `echo_alert_test_staging` - counts trigger logs from staging
   - `echo_alert_test_prod` - counts trigger logs from production

3. **Alert Policies**:
   - "Echo Backend STAGING - Alert Self-Test Triggered"
   - "Echo Backend PROD - Alert Self-Test Triggered"
   - Fire when metric > 0 (any trigger)
   - Auto-close after 10 minutes

## Running the Self-Test

### Option 1: GitHub Actions (Recommended)

1. Go to **Actions** > **Alert Self-Test**
2. Click **Run workflow**
3. Select environment: `staging` or `production`
4. Click **Run workflow**
5. Check your email for the alert (arrives within 1-2 minutes)

### Option 2: Manual curl

```bash
# Get the token from Secret Manager
TOKEN=$(gcloud secrets versions access latest --secret=echo-alert-test-token --project echo-staging-483002)

# Staging
curl -H "X-Alert-Test-Token: $TOKEN" https://echo-backend-staging-1051039678986.europe-west1.run.app/ops/alert-test

# Production
curl -H "X-Alert-Test-Token: $TOKEN" https://echo-backend-1051039678986.europe-west1.run.app/ops/alert-test
```

## Expected Email

When the self-test succeeds, you'll receive an email with:

- **Subject**: `[FIRING] Echo Backend STAGING - Alert Self-Test Triggered` (or PROD)
- **Body**: Documentation explaining this is a test alert

The alert will automatically resolve after 10 minutes.

## Disabling Alert Policies

If you need to temporarily disable the self-test alerts:

```bash
# List policies to find the name
gcloud alpha monitoring policies list --project echo-staging-483002 --format="table(displayName,name,enabled)"

# Disable a policy
gcloud alpha monitoring policies update POLICY_NAME --no-enabled --project echo-staging-483002

# Re-enable
gcloud alpha monitoring policies update POLICY_NAME --enabled --project echo-staging-483002
```

Or use the Cloud Console: [Alerting Policies](https://console.cloud.google.com/monitoring/alerting?project=echo-staging-483002)

## Troubleshooting

### Alert not firing

1. **Check logs**: Verify the `ECHO_ALERT_TEST_TRIGGERED` log appears in Cloud Logging
2. **Check metrics**: Verify the log-based metric is incrementing in Metrics Explorer
3. **Check policy**: Ensure the alert policy is enabled
4. **Check channel**: Ensure the email notification channel is verified

### 403 Forbidden

- Verify the token header is correct: `X-Alert-Test-Token`
- Ensure the token value matches what's in Secret Manager

### 500 Server Error

- The `ALERT_TEST_TOKEN` env var is not configured on Cloud Run
- Run the deploy workflow or manually update the service

## Security

- Token is stored in GCP Secret Manager (not in code)
- Cloud Run accesses the token via secret mount at runtime
- GitHub Actions has a copy of the token for the workflow
- Rotate the token by creating a new Secret Manager version and updating GitHub

## Resources

- [GCP Secret Manager](https://console.cloud.google.com/security/secret-manager?project=echo-staging-483002)
- [Log-Based Metrics](https://console.cloud.google.com/logs/metrics?project=echo-staging-483002)
- [Alert Policies](https://console.cloud.google.com/monitoring/alerting?project=echo-staging-483002)
- [GitHub Actions Workflow](https://github.com/yosiwizman/echo/actions/workflows/backend_alert_self_test.yml)
