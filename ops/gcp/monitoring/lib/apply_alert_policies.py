#!/usr/bin/env python3
"""
Apply alert policies via gcloud alpha monitoring policies commands.

Creates or updates alert policies based on rendered JSON templates.
Uses gcloud CLI for operations.

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


def list_alert_policies(project_id: str) -> list:
    """List all alert policies in the project."""
    result = run_gcloud([
        "alpha", "monitoring", "policies", "list",
        "--project", project_id,
        "--format=json"
    ])
    if result.returncode != 0:
        return []
    try:
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []


def find_policy_by_display_name(policies: list, display_name: str) -> dict:
    """Find a policy by its displayName."""
    for policy in policies:
        if policy.get("displayName") == display_name:
            return policy
    return None


def create_alert_policy(project_id: str, policy_file: Path) -> dict:
    """Create a new alert policy from a JSON file."""
    result = run_gcloud([
        "alpha", "monitoring", "policies", "create",
        "--project", project_id,
        f"--policy-from-file={policy_file}",
        "--format=json"
    ])
    return json.loads(result.stdout)


def update_alert_policy(policy_name: str, policy_file: Path) -> dict:
    """Update an existing alert policy."""
    # gcloud alpha monitoring policies update requires the policy name
    # and reads updates from the file
    result = run_gcloud([
        "alpha", "monitoring", "policies", "update",
        policy_name,
        f"--policy-from-file={policy_file}",
        "--format=json"
    ])
    return json.loads(result.stdout)


def render_alert_policy(template_path: Path, output_path: Path, variables: dict) -> None:
    """Render an alert policy template with variables."""
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        content = content.replace(placeholder, str(value))
    
    # Validate JSON
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in rendered template: {e}", file=sys.stderr)
        sys.exit(1)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def save_state(state_file: Path, state: dict) -> None:
    """Save state to JSON file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    print(f"State saved to: {state_file}")


def main():
    """Main entry point for applying alert policies."""
    project_id = os.environ.get("PROJECT_ID", "echo-staging-483002")
    channel_name = os.environ.get("CHANNEL_NAME", "")
    staging_check_id = os.environ.get("STAGING_CHECK_ID", "")
    prod_check_id = os.environ.get("PROD_CHECK_ID", "")
    
    if not channel_name:
        print("ERROR: CHANNEL_NAME environment variable is required", file=sys.stderr)
        sys.exit(1)
    if not staging_check_id or not prod_check_id:
        print("ERROR: STAGING_CHECK_ID and PROD_CHECK_ID environment variables are required", file=sys.stderr)
        sys.exit(1)
    
    script_dir = Path(__file__).parent.parent
    templates_dir = script_dir / "templates"
    generated_dir = script_dir / "generated"
    state_dir = script_dir / "state"
    
    # List existing policies
    print(f"Listing existing alert policies in project {project_id}...")
    existing_policies = list_alert_policies(project_id)
    print(f"Found {len(existing_policies)} existing alert policy(ies)")
    
    # Define policies to apply
    policies = [
        {
            "env": "staging",
            "template": "alert_policy_uptime_staging.template.json",
            "output": "alert_policy_staging.json",
            "display_name": "Echo Backend STAGING - Uptime Failed",
            "check_id": staging_check_id,
        },
        {
            "env": "prod",
            "template": "alert_policy_uptime_prod.template.json",
            "output": "alert_policy_prod.json",
            "display_name": "Echo Backend PROD - Uptime Failed",
            "check_id": prod_check_id,
        },
    ]
    
    results = {}
    
    for policy_config in policies:
        env = policy_config["env"]
        template_path = templates_dir / policy_config["template"]
        output_path = generated_dir / policy_config["output"]
        display_name = policy_config["display_name"]
        
        # Render template
        variables = {
            "CHECK_ID": policy_config["check_id"],
            "CHANNEL_NAME": channel_name,
            "PROJECT_ID": project_id,
        }
        
        print(f"\n[{env}] Rendering alert policy template...")
        render_alert_policy(template_path, output_path, variables)
        
        # Check if already exists
        existing = find_policy_by_display_name(existing_policies, display_name)
        
        if existing:
            print(f"[{env}] Updating existing alert policy: {existing['name']}")
            result = update_alert_policy(existing["name"], output_path)
            action = "updated"
        else:
            print(f"[{env}] Creating new alert policy: {display_name}")
            result = create_alert_policy(project_id, output_path)
            action = "created"
        
        results[env] = {
            "displayName": result.get("displayName", display_name),
            "name": result.get("name", ""),
            "enabled": result.get("enabled", True),
            "notificationChannels": result.get("notificationChannels", []),
            "action": action,
        }
        
        print(f"  Name: {results[env]['name']}")
        print(f"  Action: {action}")
    
    # Save state
    state_file = state_dir / "alert_policies.json"
    save_state(state_file, results)
    
    return results


if __name__ == "__main__":
    main()
