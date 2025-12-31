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
    
    def extract_schema_refs(obj: Any, refs: Set[str]) -> None:
        """Recursively extract all $ref values from nested structures."""
        if isinstance(obj, dict):
            if "$ref" in obj:
                refs.add(obj["$ref"].split("/")[-1])
            for value in obj.values():
                extract_schema_refs(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                extract_schema_refs(item, refs)
    
    # Collect all schema refs from brain endpoints
    all_refs: Set[str] = set()
    for path_spec in brain_v1_paths.values():
        for method_spec in path_spec.values():
            # Collect from ALL responses (including 422, default, etc)
            for response in method_spec.get("responses", {}).values():
                extract_schema_refs(response, all_refs)
            
            # Collect from request body
            request_body = method_spec.get("requestBody", {})
            extract_schema_refs(request_body, all_refs)
    
    # Add all discovered schemas to brain_schemas
    all_components = openapi_schema.get("components", {}).get("schemas", {})
    for ref_name in all_refs:
        if ref_name in all_components:
            brain_schemas[ref_name] = all_components[ref_name]
    
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
    
    # Always include FastAPI's standard validation error schemas if present
    # These are automatically added for 422 responses by FastAPI/Pydantic
    all_components = openapi_schema.get("components", {}).get("schemas", {})
    for error_schema in ["HTTPValidationError", "ValidationError"]:
        if error_schema in all_components and error_schema not in brain_schemas:
            brain_schemas[error_schema] = all_components[error_schema]
    
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
    - operationId, summary, description (documentation)
    - examples, example (sample data)
    - title (human-readable labels)
    - tags (organizational metadata)
    - x-* extension fields
    - default (can vary based on Pydantic serialization)
    
    Sorts arrays that may appear in non-deterministic order:
    - required (list of field names)
    - enum (list of allowed values)
    - anyOf/oneOf/allOf (sorted by stable key)
    - parameters (sorted by name + in)
    - security (sorted by JSON)
    
    Preserves contract-critical fields:
    - Request/response schemas
    - Path/method shape
    - Status codes
    - Content types
    - Required fields
    - Types, formats, enums
    - Property names and structure
    
    Args:
        contract: Raw contract dictionary.
    
    Returns:
        Normalized contract with only contract-critical fields.
    """
    # Fields to remove at any level (documentation and non-contract metadata)
    NON_CONTRACT_FIELDS = {
        "operationId", "summary", "description", 
        "title", "examples", "example", "tags",
        "default",  # Default values can vary based on Pydantic serialization
    }
    
    # Array fields that should be sorted for determinism (string/primitive arrays)
    SORTABLE_STRING_ARRAYS = {"required", "enum"}
    
    # Composite schema arrays (anyOf, oneOf, allOf) need special sorting
    COMPOSITE_ARRAYS = {"anyOf", "oneOf", "allOf"}
    
    # Parameter arrays need special sorting by name+in
    PARAMETER_ARRAYS = {"parameters"}
    
    # Security arrays need sorting by JSON representation
    SECURITY_ARRAYS = {"security"}
    
    def stable_sort_key(item: Any) -> str:
        """Generate stable sort key for any item using canonical JSON."""
        if isinstance(item, dict):
            if "$ref" in item:
                return item["$ref"]
            return json.dumps(item, sort_keys=True, separators=(",", ":"))
        return str(item)
    
    def parameter_sort_key(param: Any) -> str:
        """Sort parameters by name + in location."""
        if isinstance(param, dict):
            name = param.get("name", "")
            loc = param.get("in", "")
            return f"{name}:{loc}"
        return stable_sort_key(param)
    
    def normalize_recursively(obj: Any, parent_key: str = "") -> Any:
        """Recursively normalize: remove non-contract fields and sort arrays."""
        if isinstance(obj, dict):
            filtered = {}
            for key, value in obj.items():
                # Skip non-contract-critical fields
                if key in NON_CONTRACT_FIELDS or key.startswith("x-"):
                    continue
                filtered[key] = normalize_recursively(value, key)
            return filtered
        elif isinstance(obj, list):
            normalized_list = [normalize_recursively(item, parent_key) for item in obj]
            
            # Sort arrays based on their type for determinism
            if parent_key in SORTABLE_STRING_ARRAYS:
                # Simple string/primitive arrays - sort directly
                try:
                    return sorted(normalized_list)
                except TypeError:
                    return sorted(normalized_list, key=stable_sort_key)
            elif parent_key in COMPOSITE_ARRAYS:
                # Composite schema arrays - sort by stable key
                return sorted(normalized_list, key=stable_sort_key)
            elif parent_key in PARAMETER_ARRAYS:
                # Parameters - sort by name + in
                return sorted(normalized_list, key=parameter_sort_key)
            elif parent_key in SECURITY_ARRAYS:
                # Security arrays - sort by JSON representation
                return sorted(normalized_list, key=stable_sort_key)
            
            return normalized_list
        else:
            return obj
    
    normalized = {
        "openapi": contract.get("openapi", "3.1.0"),
        "info": {
            "version": contract.get("info", {}).get("version", ""),
        },
        "paths": normalize_recursively(contract.get("paths", {})),
        "components": normalize_recursively(contract.get("components", {})),
    }
    
    # Note: With separate_input_output_schemas=False in FastAPI, schema variants
    # (*-Input, *-Output) are not emitted. We no longer need canonicalization.
    # The array sorting above ensures determinism across environments.
    
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
