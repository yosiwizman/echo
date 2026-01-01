# CTO Report: Alerting Self-Test Implementation

**Date**: 2026-01-01  
**Author**: Warp Agent  
**Status**: Complete

## Executive Summary

Implemented an end-to-end alerting self-test feature that allows triggering real alert emails without causing actual downtime. This enables verification of the complete alerting pipeline at any time.

## Changes Made

### 1. Backend Endpoint

**File**: `services/echo_backend/routers/other.py`

- Added `GET /ops/alert-test` endpoint
- Protected by `X-Alert-Test-Token` header (matches `ALERT_TEST_TOKEN` env var)
- On success: logs `ECHO_ALERT_TEST_TRIGGERED` at ERROR level, returns `{"ok": true}`
- Returns 403 if token missing/invalid, 500 if token not configured

### 2. Tests

**File**: `services/echo_backend/tests/test_health.py`

Added 4 test cases:
- `test_ops_alert_test_missing_header_returns_403`
- `test_ops_alert_test_wrong_token_returns_403`
- `test_ops_alert_test_correct_token_returns_200`
- `test_ops_alert_test_unconfigured_token_returns_500`

### 3. Secrets (Secret Manager)

**Secret**: `echo-alert-test-token`
- Created in GCP Secret Manager (echo-staging-483002)
- 43-character URL-safe token
- Granted `secretmanager.secretAccessor` to Cloud Run service account

### 4. Cloud Run Configuration

Both services updated to mount secret as env var:
- `echo-backend-staging` (europe-west1)
- `echo-backend` (europe-west1)

Deploy workflows updated to preserve secret mapping:
- `.github/workflows/backend_cloudrun_staging.yml`
- `.github/workflows/backend_cloudrun_production.yml`

### 5. Monitoring-as-Code

**Log-Based Metrics**:
- `echo_alert_test_staging` - filters Cloud Run logs for staging
- `echo_alert_test_prod` - filters Cloud Run logs for production

**Alert Policy Templates**:
- `ops/gcp/monitoring/templates/alert_policy_logmetric_staging.template.json`
- `ops/gcp/monitoring/templates/alert_policy_logmetric_prod.template.json`

**Python Helpers**:
- `ops/gcp/monitoring/lib/apply_log_metrics.py` - creates/updates log metrics
- `ops/gcp/monitoring/lib/apply_logmetric_policies.py` - creates/updates alert policies

**Updated Scripts**:
- `ops/gcp/monitoring/apply_monitoring.sh` - now includes log metrics and alert policies

### 6. GitHub Actions Workflow

**File**: `.github/workflows/backend_alert_self_test.yml`

- Manual trigger with environment selection (staging/production)
- Reads base URL from repo variables
- Calls endpoint with token from GitHub secret
- Outputs expected email subject and timing

**GitHub Secret Set**:
- `ALERT_TEST_TOKEN` - matches Secret Manager value

### 7. Documentation

- `docs/ops/alerting_self_test.md` - user guide
- `REPORTS/CTO_ALERTING_SELF_TEST.md` - this report

## Resources Created

| Resource Type | Name | Environment |
|---------------|------|-------------|
| Secret | echo-alert-test-token | GCP |
| Log Metric | echo_alert_test_staging | GCP |
| Log Metric | echo_alert_test_prod | GCP |
| Alert Policy | Echo Backend STAGING - Alert Self-Test Triggered | GCP |
| Alert Policy | Echo Backend PROD - Alert Self-Test Triggered | GCP |
| GitHub Secret | ALERT_TEST_TOKEN | GitHub |

## How to Operate

### Run Self-Test

1. **GitHub Actions** (recommended):
   - Actions → Alert Self-Test → Run workflow → Select env

2. **Manual**:
   ```bash
   TOKEN=$(gcloud secrets versions access latest --secret=echo-alert-test-token --project echo-staging-483002)
   curl -H "X-Alert-Test-Token: $TOKEN" https://echo-backend-staging-1051039678986.europe-west1.run.app/ops/alert-test
   ```

### Apply Monitoring Resources

```bash
cd ops/gcp/monitoring
ALERT_EMAIL="your@email.com" bash apply_monitoring.sh
```

### Rotate Token

1. Create new Secret Manager version
2. Update GitHub secret
3. Redeploy Cloud Run services (or wait for next deploy)

### Disable Alerts

```bash
gcloud alpha monitoring policies update POLICY_NAME --no-enabled --project echo-staging-483002
```

## Security Considerations

- Token never committed to repository
- Stored in GCP Secret Manager (industry best practice)
- Cloud Run accesses via IAM-controlled secret mount
- GitHub Actions has separate copy (not derived at runtime)
- Endpoint protected by token comparison (no public access)

## Future Improvements

1. Add Slack/PagerDuty notification channels
2. Implement token rotation automation
3. Add self-test to periodic health check (e.g., weekly cron)
4. Create runbook for alert verification failures
