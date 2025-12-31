"""Unit tests for contract normalization determinism.

These tests ensure that normalize_contract() produces identical output
regardless of input ordering, and that computing hashes is idempotent.
"""
import sys
from pathlib import Path

# Ensure backend root is in sys.path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.brain.contract_snapshot import normalize_contract, compute_contract_hash


def test_normalization_is_idempotent():
    """Normalizing twice produces identical output."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0", "title": "Test API"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "test_get",
                    "responses": {"200": {"description": "OK"}}
                }
            }
        },
        "components": {
            "schemas": {
                "Message": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"]
                }
            }
        }
    }
    
    normalized1 = normalize_contract(contract)
    normalized2 = normalize_contract(normalized1)  # Normalize the already-normalized
    
    hash1 = compute_contract_hash(normalized1)
    hash2 = compute_contract_hash(normalized2)
    
    assert hash1 == hash2, "Normalizing twice should produce same hash"


def test_required_array_sorting():
    """Required arrays are sorted deterministically."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Test": {
                    "type": "object",
                    "required": ["z_field", "a_field", "m_field"],
                    "properties": {
                        "z_field": {"type": "string"},
                        "a_field": {"type": "string"},
                        "m_field": {"type": "string"}
                    }
                }
            }
        }
    }
    
    normalized = normalize_contract(contract)
    required = normalized["components"]["schemas"]["Test"]["required"]
    
    assert required == ["a_field", "m_field", "z_field"], "Required should be sorted alphabetically"


def test_enum_array_sorting():
    """Enum arrays are sorted deterministically."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Status": {
                    "type": "string",
                    "enum": ["pending", "active", "completed"]
                }
            }
        }
    }
    
    normalized = normalize_contract(contract)
    enum = normalized["components"]["schemas"]["Status"]["enum"]
    
    assert enum == ["active", "completed", "pending"], "Enum should be sorted alphabetically"


def test_anyof_array_sorting():
    """anyOf arrays are sorted by stable JSON key."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Test": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                        {"type": "integer"}
                    ]
                }
            }
        }
    }
    
    normalized = normalize_contract(contract)
    anyof = normalized["components"]["schemas"]["Test"]["anyOf"]
    
    # Should be sorted by JSON representation
    assert anyof[0]["type"] == "integer"
    assert anyof[1]["type"] == "null"
    assert anyof[2]["type"] == "string"


def test_non_contract_fields_removed():
    """Non-contract fields are removed during normalization."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0", "title": "Should be removed", "description": "Also removed"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "should_remove",
                    "summary": "Should remove",
                    "description": "Should remove",
                    "tags": ["should", "remove"],
                    "responses": {"200": {}}
                }
            }
        },
        "components": {
            "schemas": {
                "Test": {
                    "type": "object",
                    "title": "Should Remove",
                    "description": "Should remove",
                    "default": {"key": "value"},
                    "x-custom": "should remove",
                    "properties": {"name": {"type": "string"}}
                }
            }
        }
    }
    
    normalized = normalize_contract(contract)
    
    # Info should only have version
    assert "title" not in normalized["info"]
    assert "description" not in normalized["info"]
    
    # Path operation should not have operationId, summary, description, tags
    path = normalized["paths"]["/test"]["get"]
    assert "operationId" not in path
    assert "summary" not in path
    assert "description" not in path
    assert "tags" not in path
    
    # Schema should not have title, description, default, x-custom
    schema = normalized["components"]["schemas"]["Test"]
    assert "title" not in schema
    assert "description" not in schema
    assert "default" not in schema
    assert "x-custom" not in schema


def test_hash_determinism_across_multiple_runs():
    """Computing hash multiple times produces identical results."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "paths": {
            "/v1/brain/health": {
                "get": {"responses": {"200": {}}}
            }
        },
        "components": {
            "schemas": {
                "Response": {
                    "type": "object",
                    "required": ["status", "message"],
                    "properties": {
                        "status": {"type": "string"},
                        "message": {"type": "string"}
                    }
                }
            }
        }
    }
    
    hashes = set()
    for _ in range(10):
        normalized = normalize_contract(contract)
        h = compute_contract_hash(normalized)
        hashes.add(h)
    
    assert len(hashes) == 1, f"Expected 1 unique hash, got {len(hashes)}: {hashes}"
