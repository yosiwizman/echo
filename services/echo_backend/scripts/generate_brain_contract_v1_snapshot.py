#!/usr/bin/env python3
"""Generate Brain API v1 contract snapshot.

This script generates a deterministic, frozen contract snapshot for Brain API v1
by extracting /v1/brain/* endpoints and their schemas from the FastAPI OpenAPI spec.

Usage:
    cd services/echo_backend
    python scripts/generate_brain_contract_v1_snapshot.py

The snapshot is written to: models/brain_contract_v1.json

This should ONLY be run when intentionally updating the frozen v1 contract
(e.g., for non-breaking additions or initial freeze). Breaking changes require
creating /v2/brain/* with a new snapshot.

IMPORTANT: Run this script in an environment with the EXACT versions from
requirements.txt to ensure CI/local parity. Version mismatches cause schema
differences that fail contract validation.

See: docs/brain_versioning.md
"""
import os
import re
import sys
import json
from pathlib import Path

# Add backend root to path for imports
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

# Set environment for safe import (no secrets required)
os.environ["ECHO_BRAIN_PROVIDER"] = "stub"
os.environ["ECHO_DISABLE_MODEL_DOWNLOADS"] = "1"
os.environ["ECHO_REQUIRE_SECRETS"] = "0"


def get_pinned_versions() -> dict:
    """Parse requirements.txt to get pinned fastapi/pydantic versions."""
    requirements_path = BACKEND_ROOT / "requirements.txt"
    pinned = {}
    
    if requirements_path.exists():
        pattern = re.compile(r'^(fastapi|pydantic)==([\d.]+)', re.IGNORECASE)
        for line in requirements_path.read_text().splitlines():
            match = pattern.match(line.strip())
            if match:
                pinned[match.group(1).lower()] = match.group(2)
    
    return pinned


def check_version_parity() -> tuple:
    """Check if installed versions match requirements.txt.
    
    Returns:
        (is_ok, message) tuple
    """
    import fastapi
    import pydantic
    
    pinned = get_pinned_versions()
    installed = {
        "fastapi": fastapi.__version__,
        "pydantic": pydantic.__version__,
    }
    
    mismatches = []
    for pkg, required_ver in pinned.items():
        if pkg in installed and installed[pkg] != required_ver:
            mismatches.append(f"  {pkg}: installed={installed[pkg]}, required={required_ver}")
    
    if mismatches:
        msg = (
            "\n❌ VERSION MISMATCH DETECTED\n"
            "\n"
            "Installed versions do not match requirements.txt:\n" +
            "\n".join(mismatches) + "\n"
            "\n"
            "Different FastAPI/Pydantic versions generate different OpenAPI schemas,\n"
            "which causes contract hash mismatches in CI.\n"
            "\n"
            "To fix: create a clean venv with requirements.txt:\n"
            "  python -m venv .venv_contract\n"
            "  .venv_contract/bin/pip install -r requirements.txt\n"
            "  .venv_contract/bin/python scripts/generate_brain_contract_v1_snapshot.py\n"
            "\n"
            "Or use --force to generate anyway (NOT recommended).\n"
        )
        return False, msg
    
    return True, f"✓ Version parity OK (fastapi=={installed['fastapi']}, pydantic=={installed['pydantic']})"


from fastapi.testclient import TestClient
from utils.brain.contract_snapshot import (
    build_brain_v1_contract,
    normalize_contract,
    compute_contract_hash,
)


def main() -> int:
    """Generate and write Brain API v1 contract snapshot."""
    force = "--force" in sys.argv
    
    # Check version parity
    is_ok, msg = check_version_parity()
    if not is_ok:
        if force:
            print("⚠️  WARNING: Proceeding despite version mismatch (--force)")
            print(msg)
        else:
            print(msg, file=sys.stderr)
            return 1
    else:
        print(msg)
    
    try:
        # Import app after env vars are set
        from main import app
        
        print("\nGenerating Brain API v1 contract snapshot...")
        
        # Get OpenAPI schema from running app
        client = TestClient(app)
        response = client.get("/openapi.json")
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch OpenAPI schema: HTTP {response.status_code}", file=sys.stderr)
            return 1
        
        openapi_schema = response.json()
        
        # Build Brain API v1 contract
        contract = build_brain_v1_contract(openapi_schema)
        
        # Normalize for deterministic comparison
        normalized = normalize_contract(contract)
        
        # Compute hash
        contract_hash = compute_contract_hash(normalized)
        
        # Write to snapshot file
        snapshot_path = BACKEND_ROOT / "models" / "brain_contract_v1.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2, sort_keys=True)
            f.write("\n")  # Trailing newline for git cleanliness
        
        print(f"✓ Snapshot written to: {snapshot_path.relative_to(BACKEND_ROOT)}")
        print(f"✓ Contract hash (SHA256): {contract_hash}")
        print()
        print("Endpoints frozen:")
        for path in sorted(normalized.get("paths", {}).keys()):
            print(f"  - {path}")
        print()
        print("Schemas frozen:")
        for schema_name in sorted(normalized.get("components", {}).get("schemas", {}).keys()):
            print(f"  - {schema_name}")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error generating snapshot: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
