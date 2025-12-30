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
    """Test that X-Input creates base schema X as $ref and symmetric -Output."""
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
    
    # All three variants should exist
    assert "Message" in schemas, "Base schema 'Message' should be created"
    assert "Message-Input" in schemas, "-Input variant should remain"
    assert "Message-Output" in schemas, "-Output variant should be created"
    
    # Base schema should be a $ref to -Input
    assert "$ref" in schemas["Message"], "Base should be a $ref"
    assert schemas["Message"]["$ref"] == "#/components/schemas/Message-Input"
    
    # -Output should have same content as -Input
    assert schemas["Message-Output"]["type"] == "object"
    assert "role" in schemas["Message-Output"]["properties"]


def test_canonicalize_input_overwrites_base_schema():
    """Test that X-Input overwrites existing X with $ref for determinism."""
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
    
    # Base schema should be replaced with $ref to -Input
    assert "$ref" in schemas["Message"], "Base should be replaced with $ref"
    assert schemas["Message"]["$ref"] == "#/components/schemas/Message-Input"
    
    # -Output should be created with -Input content
    assert "Message-Output" in schemas
    assert "content" in schemas["Message-Output"]["properties"]


def test_canonicalize_handles_multiple_input_variants():
    """Test that multiple *-Input schemas are all canonicalized symmetrically."""
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
    
    # All variants should be created for both stems
    assert "Message" in schemas
    assert "Message-Output" in schemas
    assert "ChatRequest" in schemas
    assert "ChatRequest-Output" in schemas
    
    # Both base schemas should be $ref to -Input
    assert schemas["Message"]["$ref"] == "#/components/schemas/Message-Input"
    assert schemas["ChatRequest"]["$ref"] == "#/components/schemas/ChatRequest-Input"


def test_canonicalize_base_only_creates_variants():
    """Test that base-only schemas get -Input/-Output variants created."""
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
    
    normalized = normalize_contract(contract)
    schemas = normalized["components"]["schemas"]
    
    # All variants should be created
    assert "Message" in schemas
    assert "Message-Input" in schemas
    assert "Message-Output" in schemas
    assert "UsageInfo-Input" in schemas
    assert "UsageInfo-Output" in schemas
    
    # Base schemas should be $ref to -Input
    assert schemas["Message"]["$ref"] == "#/components/schemas/Message-Input"
    assert schemas["UsageInfo"]["$ref"] == "#/components/schemas/UsageInfo-Input"


def test_canonicalize_preserves_refs_in_variant_schemas():
    """Test that $ref values in variant schemas are preserved."""
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
    
    # Base ChatRequest should be $ref
    assert schemas["ChatRequest"]["$ref"] == "#/components/schemas/ChatRequest-Input"
    
    # ChatRequest-Input should preserve nested $ref
    assert schemas["ChatRequest-Input"]["properties"]["messages"]["items"]["$ref"] == "#/components/schemas/Message"
    
    # ChatRequest-Output should also have the nested $ref
    assert "ChatRequest-Output" in schemas
    assert schemas["ChatRequest-Output"]["properties"]["messages"]["items"]["$ref"] == "#/components/schemas/Message"
