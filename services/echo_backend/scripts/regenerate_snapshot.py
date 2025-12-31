#!/usr/bin/env python3
"""Regenerate Brain API v1 contract snapshot.

This script uses only the brain router (minimal deps) with the same
FastAPI config as main.py to ensure schema parity with CI.
"""
import sys
import os
import json
import re
from pathlib import Path

# Setup paths
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

# Environment for stub mode
os.environ['ECHO_BRAIN_PROVIDER'] = 'stub'
os.environ['ECHO_DISABLE_MODEL_DOWNLOADS'] = '1'
os.environ['ECHO_REQUIRE_SECRETS'] = '0'


def get_pinned_versions():
    """Parse requirements.txt for pinned versions."""
    req_path = BACKEND_ROOT / "requirements.txt"
    pinned = {}
    if req_path.exists():
        pattern = re.compile(r'^(fastapi|pydantic)==([\d.]+)', re.IGNORECASE)
        for line in req_path.read_text().splitlines():
            m = pattern.match(line.strip())
            if m:
                pinned[m.group(1).lower()] = m.group(2)
    return pinned


def check_versions():
    """Verify installed versions match requirements.txt."""
    import fastapi
    import pydantic
    
    pinned = get_pinned_versions()
    installed = {"fastapi": fastapi.__version__, "pydantic": pydantic.__version__}
    
    mismatches = []
    for pkg, req in pinned.items():
        if pkg in installed and installed[pkg] != req:
            mismatches.append(f"  {pkg}: installed={installed[pkg]}, required={req}")
    
    if mismatches:
        print("❌ VERSION MISMATCH - snapshot would not match CI!\n")
        print("Installed versions differ from requirements.txt:\n" + "\n".join(mismatches))
        print("\nFix: Use a venv with exact requirements.txt versions:")
        print("  python -m venv .venv_ci")
        print("  .venv_ci/Scripts/pip install -r requirements.txt  # Windows")
        print("  .venv_ci/bin/pip install -r requirements.txt      # Linux")
        print("  .venv_ci/bin/python scripts/regenerate_snapshot.py")
        return False
    
    print(f"✓ Versions match CI: fastapi=={installed['fastapi']}, pydantic=={installed['pydantic']}")
    return True


def main():
    import fastapi
    import pydantic
    
    print(f"Using fastapi=={fastapi.__version__}, pydantic=={pydantic.__version__}")
    
    if not check_versions():
        return 1
    
    # Create minimal app with brain router only (same config as main.py)
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routers import brain
    
    app = FastAPI(separate_input_output_schemas=False)
    app.include_router(brain.router, prefix="/v1/brain", tags=["brain"])
    
    from utils.brain.contract_snapshot import (
        build_brain_v1_contract,
        normalize_contract, 
        compute_contract_hash,
    )
    
    print("\nGenerating Brain API v1 contract snapshot...")
    
    client = TestClient(app)
    resp = client.get("/openapi.json")
    openapi = resp.json()
    
    contract = build_brain_v1_contract(openapi)
    normalized = normalize_contract(contract)
    hash_val = compute_contract_hash(normalized)
    
    # Write snapshot
    snapshot_path = BACKEND_ROOT / "models" / "brain_contract_v1.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, sort_keys=True)
        f.write("\n")
    
    print(f"✓ Snapshot: {snapshot_path.relative_to(BACKEND_ROOT)}")
    print(f"✓ Hash: {hash_val}")
    print(f"\nSchemas: {sorted(normalized.get('components', {}).get('schemas', {}).keys())}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
