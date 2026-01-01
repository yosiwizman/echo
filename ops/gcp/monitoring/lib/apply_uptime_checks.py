#!/usr/bin/env python3
"""
Apply uptime checks via GCP Cloud Monitoring API v3.

Uses gcloud auth for authentication and makes REST API calls to create/update
uptime checks. Outputs check IDs for use in alert policies.

No external dependencies required (uses urllib from stdlib).
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def get_access_token() -> str:
    """Get access token from gcloud auth."""
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def api_request(method: str, url: str, token: str, data: dict = None) -> dict:
    """Make an authenticated API request to Cloud Monitoring."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    body = json.dumps(data).encode('utf-8') if data else None
    req = Request(url, data=body, headers=headers, method=method)
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"API Error ({e.code}): {error_body}", file=sys.stderr)
        raise


def list_uptime_checks(project_id: str, token: str) -> list:
    """List all existing uptime checks in the project."""
    url = f"https://monitoring.googleapis.com/v3/projects/{project_id}/uptimeCheckConfigs"
    try:
        response = api_request("GET", url, token)
        return response.get("uptimeCheckConfigs", [])
    except HTTPError as e:
        if e.code == 404:
            return []
        raise


def find_check_by_display_name(checks: list, display_name: str) -> dict:
    """Find an uptime check by its displayName."""
    for check in checks:
        if check.get("displayName") == display_name:
            return check
    return None


def create_uptime_check(project_id: str, token: str, config: dict) -> dict:
    """Create a new uptime check."""
    url = f"https://monitoring.googleapis.com/v3/projects/{project_id}/uptimeCheckConfigs"
    return api_request("POST", url, token, config)


def update_uptime_check(name: str, token: str, config: dict) -> dict:
    """Update an existing uptime check."""
    url = f"https://monitoring.googleapis.com/v3/{name}"
    # Remove name from config for update
    config_copy = {k: v for k, v in config.items() if k != "name"}
    return api_request("PATCH", url, token, config_copy)


def extract_check_id(name: str) -> str:
    """Extract the check ID from the full resource name.
    
    Example: projects/my-project/uptimeCheckConfigs/abc123 -> abc123
    """
    return name.split("/")[-1]


def save_state(state_file: Path, state: dict) -> None:
    """Save state to JSON file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    print(f"State saved to: {state_file}")


def main():
    """Main entry point for applying uptime checks."""
    project_id = os.environ.get("PROJECT_ID", "echo-staging-483002")
    script_dir = Path(__file__).parent.parent
    generated_dir = script_dir / "generated"
    state_dir = script_dir / "state"
    
    # Get auth token
    print("Getting access token...")
    token = get_access_token()
    
    # List existing checks
    print(f"Listing existing uptime checks in project {project_id}...")
    existing_checks = list_uptime_checks(project_id, token)
    print(f"Found {len(existing_checks)} existing uptime check(s)")
    
    # Process each environment
    environments = [
        ("staging", "uptime_check_staging.json", "Echo Backend STAGING - Health Check"),
        ("prod", "uptime_check_prod.json", "Echo Backend PROD - Health Check"),
    ]
    
    results = {}
    
    for env_name, config_file, display_name in environments:
        config_path = generated_dir / config_file
        if not config_path.exists():
            print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
            sys.exit(1)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check if already exists
        existing = find_check_by_display_name(existing_checks, display_name)
        
        if existing:
            print(f"\n[{env_name}] Updating existing uptime check: {existing['name']}")
            result = update_uptime_check(existing["name"], token, config)
            action = "updated"
        else:
            print(f"\n[{env_name}] Creating new uptime check: {display_name}")
            result = create_uptime_check(project_id, token, config)
            action = "created"
        
        check_id = extract_check_id(result["name"])
        
        results[env_name] = {
            "displayName": result["displayName"],
            "name": result["name"],
            "check_id": check_id,
            "host": result["monitoredResource"]["labels"]["host"],
            "path": result["httpCheck"]["path"],
            "period": result["period"],
            "timeout": result["timeout"],
            "action": action,
        }
        
        print(f"  Name: {result['name']}")
        print(f"  Check ID: {check_id}")
        print(f"  Action: {action}")
    
    # Save state
    state_file = state_dir / "uptime_checks.json"
    save_state(state_file, results)
    
    # Output for shell script consumption
    print("\n--- CHECK IDS FOR ALERT POLICIES ---")
    print(f"STAGING_CHECK_ID={results['staging']['check_id']}")
    print(f"PROD_CHECK_ID={results['prod']['check_id']}")
    
    return results


if __name__ == "__main__":
    main()
