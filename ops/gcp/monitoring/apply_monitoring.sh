#!/usr/bin/env bash
#
# apply_monitoring.sh - Apply GCP Cloud Monitoring uptime checks, alerting, and log-based metrics
#
# This script is idempotent: it can be run multiple times safely.
# It will create or update resources as needed.
#
# Required IAM permissions for the user/service account running this script:
#   - monitoring.notificationChannels.list
#   - monitoring.notificationChannels.create
#   - monitoring.notificationChannels.update
#   - monitoring.uptimeCheckConfigs.list
#   - monitoring.uptimeCheckConfigs.create
#   - monitoring.uptimeCheckConfigs.update
#   - monitoring.alertPolicies.list
#   - monitoring.alertPolicies.create
#   - monitoring.alertPolicies.update
#   - logging.logMetrics.list
#   - logging.logMetrics.create
#   - logging.logMetrics.update
#   - serviceusage.services.enable (if Monitoring API not yet enabled)
#
# Recommended role: roles/monitoring.editor + roles/logging.admin (or custom role with above perms)
#
# Usage:
#   ALERT_EMAIL="your@email.com" bash apply_monitoring.sh
#
# Environment variables:
#   ALERT_EMAIL     - (required) Email address for alert notifications
#   PROJECT_ID      - (optional) GCP project ID (default: echo-staging-483002)
#   STAGING_BASE_URL - (optional) Staging Cloud Run URL
#   PROD_BASE_URL   - (optional) Production Cloud Run URL
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

export PROJECT_ID="${PROJECT_ID:-echo-staging-483002}"
export STAGING_BASE_URL="${STAGING_BASE_URL:-https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app}"
export PROD_BASE_URL="${PROD_BASE_URL:-https://echo-backend-zxuvsjb5qa-ew.a.run.app}"

# Extract hosts from URLs
export STAGING_HOST="${STAGING_BASE_URL#https://}"
export PROD_HOST="${PROD_BASE_URL#https://}"

# Channel display name
export DISPLAY_NAME="${DISPLAY_NAME:-Echo Ops Alerts (Email)}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
GENERATED_DIR="$SCRIPT_DIR/generated"
STATE_DIR="$SCRIPT_DIR/state"

# ============================================================================
# Validation
# ============================================================================

if [[ -z "${ALERT_EMAIL:-}" ]]; then
    echo "ERROR: ALERT_EMAIL environment variable is required" >&2
    echo "Usage: ALERT_EMAIL=\"your@email.com\" bash $0" >&2
    exit 1
fi

export ALERT_EMAIL

echo "============================================"
echo "GCP Cloud Monitoring Setup"
echo "============================================"
echo "Project ID:      $PROJECT_ID"
echo "Alert Email:     $ALERT_EMAIL"
echo "Staging Host:    $STAGING_HOST"
echo "Prod Host:       $PROD_HOST"
echo "============================================"
echo ""

# ============================================================================
# Prerequisites
# ============================================================================

echo "[1/8] Verifying gcloud authentication..."
if ! gcloud auth print-access-token >/dev/null 2>&1; then
    echo "ERROR: Not authenticated with gcloud. Run 'gcloud auth login' first." >&2
    exit 1
fi

CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
if [[ "$CURRENT_PROJECT" != "$PROJECT_ID" ]]; then
    echo "Setting gcloud project to $PROJECT_ID..."
    gcloud config set project "$PROJECT_ID"
fi

echo "[2/8] Ensuring Cloud Monitoring API is enabled..."
if ! gcloud services list --enabled --filter="name:monitoring.googleapis.com" --format="value(name)" | grep -q monitoring; then
    echo "Enabling Cloud Monitoring API..."
    gcloud services enable monitoring.googleapis.com
fi
echo "Cloud Monitoring API is enabled."

echo "Ensuring Cloud Logging API is enabled..."
if ! gcloud services list --enabled --filter="name:logging.googleapis.com" --format="value(name)" | grep -q logging; then
    echo "Enabling Cloud Logging API..."
    gcloud services enable logging.googleapis.com
fi
echo "Cloud Logging API is enabled."
echo ""

# ============================================================================
# Render Templates
# ============================================================================

echo "[3/8] Rendering templates..."
mkdir -p "$GENERATED_DIR"
python3 "$LIB_DIR/render_templates.py"
echo ""

# ============================================================================
# Create/Update Notification Channel
# ============================================================================

echo "[4/8] Setting up notification channel..."

# Check if channel already exists
EXISTING_CHANNEL=$(gcloud beta monitoring channels list \
    --project="$PROJECT_ID" \
    --filter="displayName=\"$DISPLAY_NAME\"" \
    --format="value(name)" 2>/dev/null || echo "")

if [[ -n "$EXISTING_CHANNEL" ]]; then
    echo "Notification channel already exists: $EXISTING_CHANNEL"
    export CHANNEL_NAME="$EXISTING_CHANNEL"
else
    echo "Creating new notification channel..."
    CHANNEL_OUTPUT=$(gcloud beta monitoring channels create \
        --project="$PROJECT_ID" \
        --channel-content-from-file="$GENERATED_DIR/notification_channel.json" \
        --format="value(name)" 2>&1)
    export CHANNEL_NAME="$CHANNEL_OUTPUT"
    echo "Created notification channel: $CHANNEL_NAME"
fi

# Verify channel exists
if [[ -z "$CHANNEL_NAME" ]]; then
    echo "ERROR: Failed to create or find notification channel" >&2
    exit 1
fi

# Get channel verification status
CHANNEL_VERIFIED=$(gcloud beta monitoring channels describe "$CHANNEL_NAME" \
    --project="$PROJECT_ID" \
    --format="value(verificationStatus)" 2>/dev/null || echo "UNKNOWN")
echo "Channel verification status: $CHANNEL_VERIFIED"

if [[ "$CHANNEL_VERIFIED" != "VERIFIED" ]]; then
    echo ""
    echo "⚠️  IMPORTANT: The email channel requires verification."
    echo "   Check $ALERT_EMAIL inbox for verification email from GCP."
    echo "   Alerts will not be delivered until email is verified."
fi
echo ""

# ============================================================================
# Create/Update Uptime Checks
# ============================================================================

echo "[5/8] Applying uptime checks..."
python3 "$LIB_DIR/apply_uptime_checks.py" | tee /tmp/uptime_output.txt

# Extract check IDs from output
export STAGING_CHECK_ID=$(grep "STAGING_CHECK_ID=" /tmp/uptime_output.txt | cut -d= -f2)
export PROD_CHECK_ID=$(grep "PROD_CHECK_ID=" /tmp/uptime_output.txt | cut -d= -f2)

if [[ -z "$STAGING_CHECK_ID" || -z "$PROD_CHECK_ID" ]]; then
    echo "ERROR: Failed to extract check IDs from uptime check output" >&2
    exit 1
fi

echo ""
echo "Uptime Check IDs:"
echo "  Staging: $STAGING_CHECK_ID"
echo "  Prod:    $PROD_CHECK_ID"
echo ""

# ============================================================================
# Create/Update Alert Policies (Uptime)
# ============================================================================

echo "[6/8] Applying uptime alert policies..."
python3 "$LIB_DIR/apply_alert_policies.py"
echo ""

# ============================================================================
# Create/Update Log-Based Metrics (Alert Self-Test)
# ============================================================================

echo "[7/8] Applying log-based metrics for alert self-test..."
python3 "$LIB_DIR/apply_log_metrics.py"
echo ""

# ============================================================================
# Create/Update Log-Metric Alert Policies (Alert Self-Test)
# ============================================================================

echo "[8/8] Applying log-metric alert policies..."
python3 "$LIB_DIR/apply_logmetric_policies.py"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Created/Updated Resources:"
echo "  • Notification Channel: $CHANNEL_NAME"
echo "    - Email: $ALERT_EMAIL"
echo "    - Verification: $CHANNEL_VERIFIED"
echo ""
echo "  • Uptime Checks:"
echo "    - Staging: Echo Backend STAGING - Health Check"
echo "      Host: $STAGING_HOST"
echo "      Check ID: $STAGING_CHECK_ID"
echo "    - Prod: Echo Backend PROD - Health Check"
echo "      Host: $PROD_HOST"
echo "      Check ID: $PROD_CHECK_ID"
echo ""
echo "  • Alert Policies (Uptime):"
echo "    - Echo Backend STAGING - Uptime Failed"
echo "    - Echo Backend PROD - Uptime Failed"
echo ""
echo "  • Log-Based Metrics (Alert Self-Test):"
echo "    - echo_alert_test_staging"
echo "    - echo_alert_test_prod"
echo ""
echo "  • Alert Policies (Alert Self-Test):"
echo "    - Echo Backend STAGING - Alert Self-Test Triggered"
echo "    - Echo Backend PROD - Alert Self-Test Triggered"
echo ""
echo "State files saved to: $STATE_DIR/"
echo ""
echo "Next Steps:"
echo "  1. Verify email notification channel (check inbox)"
echo "  2. View uptime checks in Console:"
echo "     https://console.cloud.google.com/monitoring/uptime?project=$PROJECT_ID"
echo "  3. View alert policies in Console:"
echo "     https://console.cloud.google.com/monitoring/alerting?project=$PROJECT_ID"
echo ""

# Cleanup temp file
rm -f /tmp/uptime_output.txt
