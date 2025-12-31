#!/usr/bin/env python3
"""Diagnostic tool to show exact differences between Brain API contracts.

Usage:
    cd services/echo_backend
    python scripts/diff_brain_contracts.py

This script compares the committed contract snapshot with the current
OpenAPI schema and outputs a compact JSON-pointer diff showing exactly
which values differ.
"""
import os
import sys
import json
from pathlib import Path
from typing import Any, List, Tuple

# Add backend root to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

# Set environment for safe import
os.environ["ECHO_BRAIN_PROVIDER"] = "stub"
os.environ["ECHO_DISABLE_MODEL_DOWNLOADS"] = "1"
os.environ["ECHO_REQUIRE_SECRETS"] = "0"


def json_pointer_diff(obj1: Any, obj2: Any, path: str = "") -> List[Tuple[str, Any, Any]]:
    """Recursively compare two objects and return JSON-pointer paths that differ.
    
    Returns:
        List of (json_pointer, value_in_obj1, value_in_obj2) tuples.
    """
    diffs = []
    
    if type(obj1) != type(obj2):
        diffs.append((path or "/", obj1, obj2))
        return diffs
    
    if isinstance(obj1, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        for key in sorted(all_keys):
            new_path = f"{path}/{key}"
            if key not in obj1:
                diffs.append((new_path, "<missing>", obj2[key]))
            elif key not in obj2:
                diffs.append((new_path, obj1[key], "<missing>"))
            else:
                diffs.extend(json_pointer_diff(obj1[key], obj2[key], new_path))
    elif isinstance(obj1, list):
        if len(obj1) != len(obj2):
            diffs.append((f"{path}[len]", len(obj1), len(obj2)))
        for i, (v1, v2) in enumerate(zip(obj1, obj2)):
            diffs.extend(json_pointer_diff(v1, v2, f"{path}[{i}]"))
    else:
        if obj1 != obj2:
            diffs.append((path, obj1, obj2))
    
    return diffs


def compact_diff_summary(diffs: List[Tuple[str, Any, Any]], max_items: int = 50) -> str:
    """Generate a compact diff summary."""
    if not diffs:
        return "No differences found."
    
    lines = [f"Found {len(diffs)} differences:"]
    for i, (path, v1, v2) in enumerate(diffs[:max_items]):
        # Truncate values for readability
        v1_str = json.dumps(v1, sort_keys=True)[:80] if not isinstance(v1, str) else v1[:80]
        v2_str = json.dumps(v2, sort_keys=True)[:80] if not isinstance(v2, str) else v2[:80]
        lines.append(f"  {path}")
        lines.append(f"    committed: {v1_str}")
        lines.append(f"    current:   {v2_str}")
    
    if len(diffs) > max_items:
        lines.append(f"  ... and {len(diffs) - max_items} more differences")
    
    return "\n".join(lines)


def main() -> int:
    """Compare committed snapshot with current contract."""
    from fastapi.testclient import TestClient
    from utils.brain.contract_snapshot import (
        build_brain_v1_contract,
        normalize_contract,
        compute_contract_hash,
    )
    
    # Import app after env vars are set
    from main import app
    
    snapshot_path = BACKEND_ROOT / "models" / "brain_contract_v1.json"
    
    if not snapshot_path.exists():
        print(f"❌ Snapshot not found: {snapshot_path}")
        return 1
    
    print("Loading committed snapshot...")
    with open(snapshot_path) as f:
        committed_snapshot = json.load(f)
    
    print("Fetching current OpenAPI schema...")
    client = TestClient(app)
    response = client.get("/openapi.json")
    if response.status_code != 200:
        print(f"❌ Failed to fetch OpenAPI: HTTP {response.status_code}")
        return 1
    openapi_schema = response.json()
    
    print("Building and normalizing contracts...")
    current_contract = build_brain_v1_contract(openapi_schema)
    
    normalized_committed = normalize_contract(committed_snapshot)
    normalized_current = normalize_contract(current_contract)
    
    committed_hash = compute_contract_hash(normalized_committed)
    current_hash = compute_contract_hash(normalized_current)
    
    print(f"\nCommitted hash: {committed_hash}")
    print(f"Current hash:   {current_hash}")
    
    if committed_hash == current_hash:
        print("\n✓ Contracts match!")
        return 0
    
    print("\n❌ Hash mismatch - computing diff...")
    
    # High-level comparison
    committed_schemas = set(normalized_committed.get("components", {}).get("schemas", {}).keys())
    current_schemas = set(normalized_current.get("components", {}).get("schemas", {}).keys())
    
    schemas_only_in_committed = committed_schemas - current_schemas
    schemas_only_in_current = current_schemas - committed_schemas
    
    if schemas_only_in_committed:
        print(f"\nSchemas only in committed: {schemas_only_in_committed}")
    if schemas_only_in_current:
        print(f"\nSchemas only in current: {schemas_only_in_current}")
    
    # Detailed diff
    diffs = json_pointer_diff(normalized_committed, normalized_current)
    print(f"\n{compact_diff_summary(diffs)}")
    
    # Save debug files
    debug_dir = Path("/tmp") if Path("/tmp").exists() else BACKEND_ROOT
    with open(debug_dir / "diff_committed.json", "w") as f:
        json.dump(normalized_committed, f, indent=2, sort_keys=True)
    with open(debug_dir / "diff_current.json", "w") as f:
        json.dump(normalized_current, f, indent=2, sort_keys=True)
    
    print(f"\nDebug files saved to: {debug_dir}")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
