"""Test Brain API v1 contract stability against committed snapshot.

This test ensures no breaking changes are introduced to Brain API v1 without
creating a new version. The contract is frozen and must remain backward compatible.
"""
import json
import hashlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path for main import (import-safe from any CWD)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from main import app


# Force stub provider for deterministic testing
@pytest.fixture(autouse=True)
def force_stub_provider(monkeypatch):
    """Force stub provider for all tests."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "stub")


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def contract_snapshot_path():
    """Path to committed contract snapshot."""
    return BACKEND_ROOT / "models" / "brain_contract_v1.json"


def normalize_openapi_schema(schema: dict) -> dict:
    """Normalize OpenAPI schema for comparison.
    
    Removes fields that can vary between runs (timestamps, server URLs, etc.)
    but preserves the contract-critical fields.
    """
    normalized = {
        "openapi": schema.get("openapi", "3.1.0"),
        "info": {
            "title": schema.get("info", {}).get("title", ""),
            "version": schema.get("info", {}).get("version", ""),
            "description": schema.get("info", {}).get("description", ""),
        },
        "paths": schema.get("paths", {}),
        "components": schema.get("components", {}),
    }
    return normalized


def compute_schema_hash(schema: dict) -> str:
    """Compute deterministic hash of normalized schema."""
    schema_json = json.dumps(schema, sort_keys=True, indent=2)
    return hashlib.sha256(schema_json.encode()).hexdigest()


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
    current_schema = response.json()
    
    # Extract only Brain API v1 paths
    brain_v1_paths = {
        path: spec
        for path, spec in current_schema.get("paths", {}).items()
        if path.startswith("/v1/brain/")
    }
    
    # Extract Brain API schemas (referenced components)
    brain_schemas = {}
    for path_spec in brain_v1_paths.values():
        for method_spec in path_spec.values():
            # Collect schema refs from responses
            for response in method_spec.get("responses", {}).values():
                for content_spec in response.get("content", {}).values():
                    schema_ref = content_spec.get("schema", {}).get("$ref", "")
                    if schema_ref:
                        schema_name = schema_ref.split("/")[-1]
                        if schema_name in current_schema.get("components", {}).get("schemas", {}):
                            brain_schemas[schema_name] = current_schema["components"]["schemas"][schema_name]
            
            # Collect schema refs from request bodies
            request_body = method_spec.get("requestBody", {})
            for content_spec in request_body.get("content", {}).values():
                schema_ref = content_spec.get("schema", {}).get("$ref", "")
                if schema_ref:
                    schema_name = schema_ref.split("/")[-1]
                    if schema_name in current_schema.get("components", {}).get("schemas", {}):
                        brain_schemas[schema_name] = current_schema["components"]["schemas"][schema_name]
    
    # Recursively collect nested schema refs
    def collect_nested_schemas(schema_name):
        """Recursively collect schemas referenced by this schema."""
        if schema_name not in current_schema.get("components", {}).get("schemas", {}):
            return
        
        schema_obj = current_schema["components"]["schemas"][schema_name]
        
        # Check properties for refs
        for prop_spec in schema_obj.get("properties", {}).values():
            ref = prop_spec.get("$ref", "")
            if ref:
                nested_name = ref.split("/")[-1]
                if nested_name not in brain_schemas:
                    brain_schemas[nested_name] = current_schema["components"]["schemas"][nested_name]
                    collect_nested_schemas(nested_name)
            
            # Check anyOf refs
            for any_of_spec in prop_spec.get("anyOf", []):
                ref = any_of_spec.get("$ref", "")
                if ref:
                    nested_name = ref.split("/")[-1]
                    if nested_name not in brain_schemas:
                        brain_schemas[nested_name] = current_schema["components"]["schemas"][nested_name]
                        collect_nested_schemas(nested_name)
            
            # Check array items refs
            items = prop_spec.get("items", {})
            ref = items.get("$ref", "")
            if ref:
                nested_name = ref.split("/")[-1]
                if nested_name not in brain_schemas:
                    brain_schemas[nested_name] = current_schema["components"]["schemas"][nested_name]
                    collect_nested_schemas(nested_name)
    
    for schema_name in list(brain_schemas.keys()):
        collect_nested_schemas(schema_name)
    
    # Build current Brain API v1 contract
    current_contract = {
        "openapi": current_schema.get("openapi", "3.1.0"),
        "info": {
            "title": "Brain API v1 Contract",
            "version": "1.0.0",
            "description": "Immutable contract for Brain API v1. Breaking changes require /v2/brain/*",
        },
        "paths": brain_v1_paths,
        "components": {
            "schemas": brain_schemas
        }
    }
    
    # Normalize both schemas
    normalized_committed = normalize_openapi_schema(committed_snapshot)
    normalized_current = normalize_openapi_schema(current_contract)
    
    # Compute hashes
    committed_hash = compute_schema_hash(normalized_committed)
    current_hash = compute_schema_hash(normalized_current)
    
    # Compare
    assert current_hash == committed_hash, (
        f"\n"
        f"❌ BREAKING CHANGE DETECTED\n"
        f"\n"
        f"The Brain API v1 contract has changed since it was frozen.\n"
        f"\n"
        f"Committed snapshot hash: {committed_hash}\n"
        f"Current schema hash:     {current_hash}\n"
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
        f"- Update the snapshot: services/echo_backend/models/brain_contract_v1.json\n"
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
