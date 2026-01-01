# GCP Cloud Monitoring - Uptime Checks & Alerting

This directory contains monitoring-as-code configurations for GCP Cloud Monitoring uptime checks and alerting.

## Quick Start

```bash
# Set alert email and run apply script
ALERT_EMAIL="your@email.com" bash apply_monitoring.sh
```

## What Gets Created

- **Email notification channel** - Sends alerts to specified email
- **2 uptime checks** - Monitors `/health` endpoint for staging and prod
- **2 alert policies** - Triggers alerts on uptime check failures

## Directory Structure

```
ops/gcp/monitoring/
├── apply_monitoring.sh      # Main idempotent apply script
├── templates/               # JSON templates with placeholders
│   ├── notification_channel_email.template.json
│   ├── uptime_check_staging.template.json
│   ├── uptime_check_prod.template.json
│   ├── alert_policy_uptime_staging.template.json
│   └── alert_policy_uptime_prod.template.json
├── lib/                     # Python helper scripts
│   ├── render_templates.py
│   ├── apply_uptime_checks.py
│   └── apply_alert_policies.py
├── generated/               # Rendered configs (gitignored)
└── state/                   # Tracked resource state
    ├── uptime_checks.json
    └── alert_policies.json
```

## Full Documentation

See [docs/ops/gcp_uptime_alerting.md](../../../docs/ops/gcp_uptime_alerting.md) for complete documentation including:
- Detailed setup instructions
- IAM permissions required
- Manual verification steps
- Troubleshooting guide
