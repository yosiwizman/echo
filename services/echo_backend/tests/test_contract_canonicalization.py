"""Unit tests for Brain API contract schema canonicalization.

Tests that normalize_contract() correctly handles Pydantic *-Input/*-Output
schema naming variants to ensure deterministic contract hashing.
"""
import sys
from pathlib import Path

# Ensure backend root is in sys.path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.brain.contract_snapshot import normalize_contract


def test_canonicalize_input_variant_creates_base_schema():
    """Test that X-Input creates base schema X."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Message-Input": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["role", "content"]
                }
            }
        }
    }
    
    normalized = normalize_contract(contract)
    schemas = normalized["components"]["schemas"]
    
    # Base schema should be created from -Input variant
    assert "Message" in schemas, "Base schema 'Message' should be created"
    assert "Message-Input" in schemas, "-Input variant should remain"
    
    # Base schema should be identical to -Input
    assert schemas["Message"] == schemas["Message-Input"]
    assert schemas["Message"]["type"] == "object"
    assert "role" in schemas["Message"]["properties"]
    assert "content" in schemas["Message"]["properties"]


def test_canonicalize_input_overwrites_base_schema():
    """Test that X-Input overwrites existing X for determinism."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Message": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"}
                    }
                },
                "Message-Input": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["role", "content"]
                }
            }
        }
    }
    
    normalized = normalize_contract(contract)
    schemas = normalized["components"]["schemas"]
    
    # Base schema should be overwritten with -Input
    assert schemas["Message"] == schemas["Message-Input"]
    assert "content" in schemas["Message"]["properties"], "Message should have content from Message-Input"
    assert schemas["Message"]["required"] == ["role", "content"]


def test_canonicalize_handles_multiple_input_variants():
    """Test that multiple *-Input schemas are all canonicalized."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Message-Input": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}}
                },
                "ChatRequest-Input": {
                    "type": "object",
                    "properties": {"messages": {"type": "array"}}
                }
            }
        }
    }
    
    normalized = normalize_contract(contract)
    schemas = normalized["components"]["schemas"]
    
    # Both base schemas should be created
    assert "Message" in schemas
    assert "ChatRequest" in schemas
    
    # Both should match their -Input variants
    assert schemas["Message"] == schemas["Message-Input"]
    assert schemas["ChatRequest"] == schemas["ChatRequest-Input"]


def test_canonicalize_no_input_variants_unchanged():
    """Test that schemas without -Input variants are unchanged."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Message": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}}
                },
                "UsageInfo": {
                    "type": "object",
                    "properties": {"tokens": {"type": "integer"}}
                }
            }
        }
    }
    
    original_message = contract["components"]["schemas"]["Message"].copy()
    original_usage = contract["components"]["schemas"]["UsageInfo"].copy()
    
    normalized = normalize_contract(contract)
    schemas = normalized["components"]["schemas"]
    
    # Schemas should remain unchanged (only non-contract fields removed)
    assert schemas["Message"]["properties"] == original_message["properties"]
    assert schemas["UsageInfo"]["properties"] == original_usage["properties"]


def test_canonicalize_preserves_refs_in_input_schema():
    """Test that $ref values in -Input schemas are preserved."""
    contract = {
        "openapi": "3.1.0",
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "ChatRequest-Input": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Message"}
                        }
                    }
                },
                "Message": {
                    "type": "object",
                    "properties": {"content": {"type": "string"}}
                }
            }
        }
    }
    
    normalized = normalize_contract(contract)
    schemas = normalized["components"]["schemas"]
    
    # Base ChatRequest should be created with $ref intact
    assert "ChatRequest" in schemas
    assert schemas["ChatRequest"]["properties"]["messages"]["items"]["$ref"] == "#/components/schemas/Message"
