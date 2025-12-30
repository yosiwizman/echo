"""Brain API contract snapshot utilities.

Shared logic for generating and validating Brain API v1 contract snapshots.
This ensures the snapshot generator and tests use identical extraction and
normalization logic, preventing drift between generated and validated contracts.
"""
import json
import hashlib
from typing import Dict, Any, Set


def build_brain_v1_contract(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Extract Brain API v1 contract from full OpenAPI schema.
    
    Args:
        openapi_schema: Full OpenAPI schema from FastAPI app.
    
    Returns:
        Brain API v1 contract with only /v1/brain/* paths and their schemas.
    """
    # Extract only Brain API v1 paths
    brain_v1_paths = {
        path: spec
        for path, spec in openapi_schema.get("paths", {}).items()
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
                        if schema_name in openapi_schema.get("components", {}).get("schemas", {}):
                            brain_schemas[schema_name] = openapi_schema["components"]["schemas"][schema_name]
            
            # Collect schema refs from request bodies
            request_body = method_spec.get("requestBody", {})
            for content_spec in request_body.get("content", {}).values():
                schema_ref = content_spec.get("schema", {}).get("$ref", "")
                if schema_ref:
                    schema_name = schema_ref.split("/")[-1]
                    if schema_name in openapi_schema.get("components", {}).get("schemas", {}):
                        brain_schemas[schema_name] = openapi_schema["components"]["schemas"][schema_name]
    
    # Recursively collect nested schema refs
    def collect_nested_schemas(schema_name: str, seen: Set[str]) -> None:
        """Recursively collect schemas referenced by this schema."""
        if schema_name in seen or schema_name not in openapi_schema.get("components", {}).get("schemas", {}):
            return
        
        seen.add(schema_name)
        schema_obj = openapi_schema["components"]["schemas"][schema_name]
        
        # Check properties for refs
        for prop_spec in schema_obj.get("properties", {}).values():
            ref = prop_spec.get("$ref", "")
            if ref:
                nested_name = ref.split("/")[-1]
                if nested_name not in brain_schemas:
                    brain_schemas[nested_name] = openapi_schema["components"]["schemas"][nested_name]
                    collect_nested_schemas(nested_name, seen)
            
            # Check anyOf refs
            for any_of_spec in prop_spec.get("anyOf", []):
                ref = any_of_spec.get("$ref", "")
                if ref:
                    nested_name = ref.split("/")[-1]
                    if nested_name not in brain_schemas:
                        brain_schemas[nested_name] = openapi_schema["components"]["schemas"][nested_name]
                        collect_nested_schemas(nested_name, seen)
            
            # Check array items refs
            items = prop_spec.get("items", {})
            ref = items.get("$ref", "")
            if ref:
                nested_name = ref.split("/")[-1]
                if nested_name not in brain_schemas:
                    brain_schemas[nested_name] = openapi_schema["components"]["schemas"][nested_name]
                    collect_nested_schemas(nested_name, seen)
    
    seen_schemas: Set[str] = set()
    for schema_name in list(brain_schemas.keys()):
        collect_nested_schemas(schema_name, seen_schemas)
    
    # Build current Brain API v1 contract
    contract = {
        "openapi": openapi_schema.get("openapi", "3.1.0"),
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
    
    return contract


def normalize_contract(contract: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize contract for deterministic comparison.
    
    Removes fields that can vary between runs but don't affect the contract:
    - operationId (implementation detail, not part of API contract)
    - examples (documentation, not contract-critical)
    - x-* extension fields
    
    Preserves contract-critical fields:
    - Request/response schemas
    - Path/method shape
    - Status codes
    - Content types
    - Required fields
    - Types and formats
    
    Args:
        contract: Raw contract dictionary.
    
    Returns:
        Normalized contract with only contract-critical fields.
    """
    def remove_non_contract_fields(obj: Any) -> Any:
        """Recursively remove non-contract-critical fields."""
        if isinstance(obj, dict):
            filtered = {}
            for key, value in obj.items():
                # Skip non-contract-critical fields
                if key in ("operationId", "examples") or key.startswith("x-"):
                    continue
                filtered[key] = remove_non_contract_fields(value)
            return filtered
        elif isinstance(obj, list):
            return [remove_non_contract_fields(item) for item in obj]
        else:
            return obj
    
    normalized = {
        "openapi": contract.get("openapi", "3.1.0"),
        "info": {
            "title": contract.get("info", {}).get("title", ""),
            "version": contract.get("info", {}).get("version", ""),
            "description": contract.get("info", {}).get("description", ""),
        },
        "paths": remove_non_contract_fields(contract.get("paths", {})),
        "components": remove_non_contract_fields(contract.get("components", {})),
    }
    
    return normalized


def compute_contract_hash(normalized_contract: Dict[str, Any]) -> str:
    """Compute deterministic SHA256 hash of normalized contract.
    
    Args:
        normalized_contract: Normalized contract dictionary.
    
    Returns:
        SHA256 hex digest of the contract.
    """
    contract_json = json.dumps(normalized_contract, sort_keys=True, indent=2)
    return hashlib.sha256(contract_json.encode()).hexdigest()
