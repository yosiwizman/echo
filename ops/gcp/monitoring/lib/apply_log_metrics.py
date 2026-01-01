#!/usr/bin/env python3
"""
Apply log-based metrics via gcloud logging metrics commands.

Creates or updates log-based counter metrics that fire when specific log lines appear.
Used for alerting self-test functionality.

No external dependencies required.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_gcloud(args: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a gcloud command and return the result."""
    cmd = ["gcloud"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        print(f"gcloud error: {result.stderr}", file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result


def list_log_metrics(project_id: str) -> list:
    """List all log-based metrics in the project."""
    result = run_gcloud([
        "logging", "metrics", "list",
        "--project", project_id,
        "--format=json"
    ], check=False)
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []


def find_metric_by_name(metrics: list, metric_name: str) -> dict:
    """Find a metric by its name."""
    for metric in metrics:
        # The name field is like "projects/PROJECT_ID/metrics/METRIC_NAME"
        if metric.get("name", "").endswith(f"/metrics/{metric_name}"):
            return metric
    return None


def create_log_metric(project_id: str, metric_name: str, filter_str: str, description: str) -> dict:
    """Create a new log-based counter metric."""
    result = run_gcloud([
        "logging", "metrics", "create", metric_name,
        "--project", project_id,
        f"--log-filter={filter_str}",
        f"--description={description}",
        "--format=json"
    ])
    return {"name": metric_name, "action": "created"}


def update_log_metric(project_id: str, metric_name: str, filter_str: str, description: str) -> dict:
    """Update an existing log-based metric."""
    result = run_gcloud([
        "logging", "metrics", "update", metric_name,
        "--project", project_id,
        f"--log-filter={filter_str}",
        f"--description={description}",
        "--format=json"
    ])
    return {"name": metric_name, "action": "updated"}


def main():
    """Main entry point for applying log-based metrics."""
    project_id = os.environ.get("PROJECT_ID", "echo-staging-483002")
    
    # Define the log-based metrics for alert self-test
    metrics = [
        {
            "name": "echo_alert_test_staging",
            "service": "echo-backend-staging",
            "description": "Counter for alert self-test triggers (staging)",
        },
        {
            "name": "echo_alert_test_prod",
            "service": "echo-backend",
            "description": "Counter for alert self-test triggers (production)",
        },
    ]
    
    # List existing metrics
    print(f"Listing existing log-based metrics in project {project_id}...")
    existing_metrics = list_log_metrics(project_id)
    print(f"Found {len(existing_metrics)} existing log-based metric(s)")
    
    results = {}
    
    for metric_config in metrics:
        metric_name = metric_config["name"]
        service_name = metric_config["service"]
        description = metric_config["description"]
        
        # Build the filter for Cloud Run logs containing the trigger message
        # Handles both textPayload and jsonPayload.message formats
        filter_str = (
            f'resource.type="cloud_run_revision" AND '
            f'resource.labels.service_name="{service_name}" AND '
            f'(textPayload:"ECHO_ALERT_TEST_TRIGGERED" OR jsonPayload.message="ECHO_ALERT_TEST_TRIGGERED")'
        )
        
        # Check if metric already exists
        existing = find_metric_by_name(existing_metrics, metric_name)
        
        if existing:
            print(f"\n[{metric_name}] Updating existing log-based metric...")
            result = update_log_metric(project_id, metric_name, filter_str, description)
        else:
            print(f"\n[{metric_name}] Creating new log-based metric...")
            result = create_log_metric(project_id, metric_name, filter_str, description)
        
        results[metric_name] = result
        print(f"  Action: {result['action']}")
    
    # Output for shell script to capture
    print("\n--- LOG METRIC RESULTS ---")
    for name, result in results.items():
        print(f"METRIC_{name.upper()}={result['action']}")
    
    return results


if __name__ == "__main__":
    main()
