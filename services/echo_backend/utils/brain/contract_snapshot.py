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
    
    # Handle Pydantic naming variations (Message vs Message-Input)
    # Include both if either exists to handle FastAPI/Pydantic naming drift
    message_variants = []
    for schema_name in list(brain_schemas.keys()):
        if "Message" in schema_name:
            message_variants.append(schema_name)
    
    # If we have any Message variant, include all Message-related schemas
    if message_variants:
        all_components = openapi_schema.get("components", {}).get("schemas", {})
        for candidate in ["Message", "Message-Input", "Message-Output"]:
            if candidate in all_components and candidate not in brain_schemas:
                brain_schemas[candidate] = all_components[candidate]
    
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
    # Fields to remove at any level
    NON_CONTRACT_FIELDS = {
        "operationId", "summary", "description", 
        "title", "examples", "example", "tags"
    }
    
    def remove_non_contract_fields(obj: Any) -> Any:
        """Recursively remove non-contract-critical fields."""
        if isinstance(obj, dict):
            filtered = {}
            for key, value in obj.items():
                # Skip non-contract-critical fields
                if key in NON_CONTRACT_FIELDS or key.startswith("x-"):
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
            "version": contract.get("info", {}).get("version", ""),
        },
        "paths": remove_non_contract_fields(contract.get("paths", {})),
        "components": remove_non_contract_fields(contract.get("components", {})),
    }
    
    # Canonicalize Pydantic schema variants (symmetric)
    # FastAPI/Pydantic v2 may emit X, X-Input, X-Output in various combinations
    # To ensure determinism, create symmetric aliases with base as stable $ref
    schemas = normalized.get("components", {}).get("schemas", {})
    if schemas:
        canonicalize_schema_variants(schemas)
    
    return normalized


def canonicalize_schema_variants(schemas: Dict[str, Any]) -> None:
    """Canonicalize Pydantic schema naming variants for deterministic hashing.
    
    FastAPI/Pydantic may emit schemas as:
    - Just "Message" (base)
    - Just "Message-Input"
    - Just "Message-Output"
    - Various combinations of the above
    
    To ensure determinism across environments:
    1. Group schemas by stem (base name without -Input/-Output suffix)
    2. For each stem with variants, create symmetric aliases
    3. Replace base schema with $ref to -Input (preferred) or -Output variant
    
    This makes base schema deterministic regardless of which variants exist.
    
    Args:
        schemas: Dictionary of schema definitions (mutated in place).
    """
    import copy
    
    # Find all schema stems (groups of related schemas)
    stems: Dict[str, Dict[str, str]] = {}  # stem -> {"base": name, "input": name, "output": name}
    
    for schema_name in list(schemas.keys()):
        if schema_name.endswith("-Input"):
            stem = schema_name[:-6]
            if stem not in stems:
                stems[stem] = {}
            stems[stem]["input"] = schema_name
        elif schema_name.endswith("-Output"):
            stem = schema_name[:-7]
            if stem not in stems:
                stems[stem] = {}
            stems[stem]["output"] = schema_name
        else:
            # Base schema (no suffix)
            stem = schema_name
            if stem not in stems:
                stems[stem] = {}
            stems[stem]["base"] = schema_name
    
    # Canonicalize each stem group
    for stem, variants in stems.items():
        has_base = "base" in variants
        has_input = "input" in variants
        has_output = "output" in variants
        
        # Determine canonical source (prefer -Input, fallback to -Output, then base)
        if has_input:
            canonical_source = variants["input"]
            canonical_content = copy.deepcopy(schemas[canonical_source])
        elif has_output:
            canonical_source = variants["output"]
            canonical_content = copy.deepcopy(schemas[canonical_source])
        elif has_base:
            canonical_source = variants["base"]
            canonical_content = copy.deepcopy(schemas[canonical_source])
        else:
            continue  # No variants for this stem
        
        # Create symmetric aliases if missing
        input_name = f"{stem}-Input"
        output_name = f"{stem}-Output"
        
        if not has_input:
            # Create -Input from canonical content
            schemas[input_name] = canonical_content
        
        if not has_output:
            # Create -Output from canonical content
            schemas[output_name] = copy.deepcopy(canonical_content)
        
        # Always set/replace base schema as $ref to -Input for determinism
        # This prevents content-based drift - base always points to -Input
        schemas[stem] = {"$ref": f"#/components/schemas/{input_name}"}


def compute_contract_hash(normalized_contract: Dict[str, Any]) -> str:
    """Compute deterministic SHA256 hash of normalized contract.
    
    Args:
        normalized_contract: Normalized contract dictionary.
    
    Returns:
        SHA256 hex digest of the contract.
    """
    contract_json = json.dumps(normalized_contract, sort_keys=True, indent=2)
    return hashlib.sha256(contract_json.encode()).hexdigest()
