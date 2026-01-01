# CTO Report: GCP Uptime Checks & Alerting

**Date**: 2026-01-01  
**Status**: Implemented  
**PR**: (pending)

## Executive Summary

Implemented GCP Cloud Monitoring uptime checks and email alerting for both staging and production Cloud Run environments. The solution follows monitoring-as-code principles with reproducible, idempotent configuration.

## What Was Implemented

### Resources Created

| Resource Type | Name | Environment |
|--------------|------|-------------|
| Notification Channel | Echo Ops Alerts (Email) | Shared |
| Uptime Check | Echo Backend STAGING - Health Check | Staging |
| Uptime Check | Echo Backend PROD - Health Check | Production |
| Alert Policy | Echo Backend STAGING - Uptime Failed | Staging |
| Alert Policy | Echo Backend PROD - Uptime Failed | Production |

### Monitoring Configuration

- **Check Frequency**: Every 60 seconds
- **Timeout**: 10 seconds
- **Endpoint**: `/health` (JSON path validation: `$.status == "ok"`)
- **Alert Duration**: 120 seconds (2 consecutive failures before alert)
- **SSL Validation**: Enabled

### Directory Structure

```
ops/gcp/monitoring/
├── apply_monitoring.sh          # Idempotent apply script
├── README.md                    # Quick reference
├── templates/                   # JSON templates (no secrets)
│   ├── notification_channel_email.template.json
│   ├── uptime_check_staging.template.json
│   ├── uptime_check_prod.template.json
│   ├── alert_policy_uptime_staging.template.json
│   └── alert_policy_uptime_prod.template.json
├── lib/                         # Python helper scripts
│   ├── render_templates.py
│   ├── apply_uptime_checks.py
│   └── apply_alert_policies.py
├── generated/                   # Rendered configs (gitignored)
└── state/                       # Resource state (tracked)
```

## Security & Compliance

### No Secrets Committed

- Email address provided at runtime via `ALERT_EMAIL` env var
- Templates use `{{PLACEHOLDER}}` syntax
- Generated configs are gitignored

### Least Privilege IAM

Required permissions documented:
- `monitoring.notificationChannels.*`
- `monitoring.uptimeCheckConfigs.*`
- `monitoring.alertPolicies.*`
- `serviceusage.services.enable`

Recommended role: `roles/monitoring.editor`

## How to Run

```bash
ALERT_EMAIL="your@email.com" bash ops/gcp/monitoring/apply_monitoring.sh
```

The script is idempotent - safe to re-run.

## Email Verification Note

**IMPORTANT**: Email notification channels require recipient verification. After running the script, the recipient must click the confirmation link in the email from GCP. Alerts will not be delivered until verification is complete.

## Verification Console Links

- [Uptime Checks](https://console.cloud.google.com/monitoring/uptime?project=echo-staging-483002)
- [Alert Policies](https://console.cloud.google.com/monitoring/alerting?project=echo-staging-483002)
- [Notification Channels](https://console.cloud.google.com/monitoring/alerting/notifications?project=echo-staging-483002)

## Documentation

- Full runbook: `docs/ops/gcp_uptime_alerting.md`
- Quick start: `ops/gcp/monitoring/README.md`

## Runbook (Included in Alerts)

Alert notifications include embedded runbook with:
1. Commands to check `/health` and `/version` endpoints
2. Links to Cloud Run logs
3. How to identify last deploy SHA
4. Escalation instructions

## Recommendations

1. **Verify Email**: Recipient must verify email address before alerts will be delivered
2. **Test Alerts**: Consider temporarily failing the health check to verify end-to-end alerting
3. **Add PagerDuty**: For production critical alerting, consider adding PagerDuty integration
4. **SLO Dashboard**: Consider creating an SLO dashboard based on uptime metrics
