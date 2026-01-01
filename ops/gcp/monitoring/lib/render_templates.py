#!/usr/bin/env python3
"""
Template rendering utility for GCP monitoring configs.

Performs simple placeholder replacement ({{PLACEHOLDER}}) in template files.
No external dependencies required.
"""

import json
import os
import re
import sys
from pathlib import Path


def render_template(template_content: str, variables: dict) -> str:
    """Replace {{PLACEHOLDER}} patterns with values from variables dict."""
    result = template_content
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))
    
    # Check for any remaining unresolved placeholders
    remaining = re.findall(r'\{\{([A-Z_]+)\}\}', result)
    if remaining:
        print(f"WARNING: Unresolved placeholders: {remaining}", file=sys.stderr)
    
    return result


def render_file(template_path: Path, output_path: Path, variables: dict) -> None:
    """Read template file, render it, and write to output path."""
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    rendered = render_template(template_content, variables)
    
    # Validate JSON if it's a JSON file
    if template_path.suffix == '.json':
        try:
            json.loads(rendered)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON after rendering {template_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered)
    
    print(f"Rendered: {template_path.name} -> {output_path}")


def main():
    """Main entry point for template rendering."""
    # Get script directory
    script_dir = Path(__file__).parent.parent
    templates_dir = script_dir / "templates"
    generated_dir = script_dir / "generated"
    
    # Load variables from environment
    variables = {
        "PROJECT_ID": os.environ.get("PROJECT_ID", "echo-staging-483002"),
        "ALERT_EMAIL": os.environ.get("ALERT_EMAIL", ""),
        "DISPLAY_NAME": os.environ.get("DISPLAY_NAME", "Echo Ops Alerts (Email)"),
        "STAGING_HOST": os.environ.get("STAGING_HOST", "echo-backend-staging-zxuvsjb5qa-ew.a.run.app"),
        "PROD_HOST": os.environ.get("PROD_HOST", "echo-backend-zxuvsjb5qa-ew.a.run.app"),
        # These will be set by apply scripts after uptime checks are created
        "CHECK_ID": os.environ.get("CHECK_ID", ""),
        "STAGING_CHECK_ID": os.environ.get("STAGING_CHECK_ID", ""),
        "PROD_CHECK_ID": os.environ.get("PROD_CHECK_ID", ""),
        "CHANNEL_NAME": os.environ.get("CHANNEL_NAME", ""),
    }
    
    # Validate required variables
    if not variables["ALERT_EMAIL"]:
        print("ERROR: ALERT_EMAIL environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    # Clean generated directory
    generated_dir.mkdir(parents=True, exist_ok=True)
    
    # Define template mappings
    templates_to_render = [
        ("notification_channel_email.template.json", "notification_channel.json"),
        ("uptime_check_staging.template.json", "uptime_check_staging.json"),
        ("uptime_check_prod.template.json", "uptime_check_prod.json"),
    ]
    
    # Render base templates (channel and uptime checks - no CHECK_ID needed)
    for template_name, output_name in templates_to_render:
        template_path = templates_dir / template_name
        if template_path.exists():
            output_path = generated_dir / output_name
            render_file(template_path, output_path, variables)
    
    print(f"\nBase templates rendered to: {generated_dir}")
    print("Note: Alert policy templates require CHECK_ID and CHANNEL_NAME,")
    print("      which are set after uptime checks and channel are created.")


if __name__ == "__main__":
    main()
