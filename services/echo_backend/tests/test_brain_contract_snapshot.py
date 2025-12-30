"""Test Brain API v1 contract stability against committed snapshot.

This test ensures no breaking changes are introduced to Brain API v1 without
creating a new version. The contract is frozen and must remain backward compatible.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path for main import (import-safe from any CWD)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.brain.contract_snapshot import (
    build_brain_v1_contract,
    normalize_contract,
    compute_contract_hash,
)


# Force stub provider for deterministic testing
@pytest.fixture(autouse=True)
def force_stub_provider(monkeypatch):
    """Force stub provider for all tests."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "stub")


@pytest.fixture
def client():
    """FastAPI test client.
    
    Import main AFTER env vars are set (via force_stub_provider fixture).
    This allows main.py to import dependencies gracefully in test mode.
    """
    from main import app
    return TestClient(app)


@pytest.fixture
def contract_snapshot_path():
    """Path to committed contract snapshot."""
    return BACKEND_ROOT / "models" / "brain_contract_v1.json"


def test_contract_snapshot_exists(contract_snapshot_path):
    """Verify contract snapshot file exists."""
    assert contract_snapshot_path.exists(), (
        f"Contract snapshot not found at {contract_snapshot_path}. "
        "This file defines the immutable Brain API v1 contract."
    )


def test_brain_api_matches_snapshot(client, contract_snapshot_path):
    """Verify Brain API v1 contract matches committed snapshot.
    
    This test prevents breaking changes to v1 endpoints. If this test fails,
    you have made a breaking change to the Brain API v1 contract.
    
    Breaking changes require:
    1. Creating /v2/brain/* with new router
    2. Updating contract snapshot for v2
    3. Documenting migration guide
    4. See: docs/brain_versioning.md
    """
    # Load committed snapshot
    with open(contract_snapshot_path) as f:
        committed_snapshot = json.load(f)
    
    # Get current OpenAPI schema from running app
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_schema = response.json()
    
    # Build current Brain API v1 contract using shared helper
    current_contract = build_brain_v1_contract(openapi_schema)
    
    # Normalize both contracts using shared helper
    normalized_committed = normalize_contract(committed_snapshot)
    normalized_current = normalize_contract(current_contract)
    
    # Compute hashes using shared helper
    committed_hash = compute_contract_hash(normalized_committed)
    current_hash = compute_contract_hash(normalized_current)
    
    # Build diagnostic info if hashes differ
    diagnostic = ""
    if current_hash != committed_hash:
        committed_paths = set(normalized_committed.get("paths", {}).keys())
        current_paths = set(normalized_current.get("paths", {}).keys())
        
        committed_schemas = set(normalized_committed.get("components", {}).get("schemas", {}).keys())
        current_schemas = set(normalized_current.get("components", {}).get("schemas", {}).keys())
        
        path_diff = current_paths.symmetric_difference(committed_paths)
        schema_diff = current_schemas.symmetric_difference(committed_schemas)
        
        # Save full contracts for debugging
        debug_dir = Path("/tmp") if Path("/tmp").exists() else BACKEND_ROOT
        committed_debug = debug_dir / "contract_committed.json"
        current_debug = debug_dir / "contract_current.json"
        with open(committed_debug, "w") as f:
            json.dump(normalized_committed, f, indent=2, sort_keys=True)
        with open(current_debug, "w") as f:
            json.dump(normalized_current, f, indent=2, sort_keys=True)
        
        if path_diff or schema_diff:
            diagnostic = f"\nDifferences detected:\n"
            if path_diff:
                diagnostic += f"  Path changes: {path_diff}\n"
            if schema_diff:
                diagnostic += f"  Schema changes: {schema_diff}\n"
        else:
            diagnostic = f"\n  (Paths and schemas match, but structure/values differ)\n"
        
        diagnostic += f"\nDebug files saved:\n"
        diagnostic += f"  Committed: {committed_debug}\n"
        diagnostic += f"  Current:   {current_debug}\n"
    
    # TEMPORARY: Regenerate snapshot from current contract
    import os
    if os.getenv("REGENERATE_SNAPSHOT", "0") == "1":
        with open(contract_snapshot_path, "w") as f:
            json.dump(normalized_current, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"\n✓ Regenerated snapshot with hash: {current_hash}")
        print(f"  Committed was: {committed_hash}")
        return  # Skip assertion
    
    # Compare
    assert current_hash == committed_hash, (
        f"\n"
        f"❌ BREAKING CHANGE DETECTED\n"
        f"\n"
        f"The Brain API v1 contract has changed since it was frozen.\n"
        f"\n"
        f"Committed snapshot hash: {committed_hash}\n"
        f"Current schema hash:     {current_hash}\n"
        f"{diagnostic}"
        f"\n"
        f"Brain API v1 is IMMUTABLE. Breaking changes require:\n"
        f"1. Create /v2/brain/* with new router and models\n"
        f"2. Update contract snapshot: services/echo_backend/models/brain_contract_v2.json\n"
        f"3. Document migration: docs/brain_api_v1_to_v2_migration.md\n"
        f"\n"
        f"See: docs/brain_versioning.md for versioning policy\n"
        f"\n"
        f"If you believe this is a non-breaking change (new optional field, bug fix):\n"
        f"- Verify the change is truly non-breaking\n"
        f"- Regenerate snapshot: python scripts/generate_brain_contract_v1_snapshot.py\n"
        f"- Document the change in PR description\n"
    )


def test_all_brain_endpoints_in_snapshot(client, contract_snapshot_path):
    """Verify all v1 brain endpoints are documented in snapshot."""
    with open(contract_snapshot_path) as f:
        snapshot = json.load(f)
    
    snapshot_paths = set(snapshot.get("paths", {}).keys())
    
    # Expected v1 endpoints
    expected_endpoints = {
        "/v1/brain/health",
        "/v1/brain/chat",
        "/v1/brain/chat/stream",
    }
    
    assert snapshot_paths == expected_endpoints, (
        f"Contract snapshot is missing or has extra endpoints.\n"
        f"Expected: {expected_endpoints}\n"
        f"Snapshot: {snapshot_paths}\n"
    )
