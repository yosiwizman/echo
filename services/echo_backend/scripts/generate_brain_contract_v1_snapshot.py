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

See: docs/brain_versioning.md
"""
import os
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

from fastapi.testclient import TestClient
from utils.brain.contract_snapshot import (
    build_brain_v1_contract,
    normalize_contract,
    compute_contract_hash,
)


def main() -> int:
    """Generate and write Brain API v1 contract snapshot."""
    try:
        # Import app after env vars are set
        from main import app
        
        print("Generating Brain API v1 contract snapshot...")
        
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
            json.dump(contract, f, indent=2, sort_keys=True)
            f.write("\n")  # Trailing newline for git cleanliness
        
        print(f"✓ Snapshot written to: {snapshot_path.relative_to(BACKEND_ROOT)}")
        print(f"✓ Contract hash (SHA256): {contract_hash}")
        print()
        print("Endpoints frozen:")
        for path in sorted(contract.get("paths", {}).keys()):
            print(f"  - {path}")
        print()
        print("Schemas frozen:")
        for schema_name in sorted(contract.get("components", {}).get("schemas", {}).keys()):
            print(f"  - {schema_name}")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error generating snapshot: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
