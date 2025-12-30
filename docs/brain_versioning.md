# Brain API Versioning Policy

## Overview

Brain API follows strict semantic versioning with immutable contracts to ensure stability for external consumers (iOS, web, third-party integrations).

## Versioning Rules

### Path-Based Versioning

Brain API uses URL path versioning:

```
/v1/brain/*  → Version 1 (current, frozen)
/v2/brain/*  → Version 2 (future breaking changes)
/v3/brain/*  → Version 3 (future breaking changes)
```

### Version Lifecycle

Each version goes through these stages:

1. **Active** - Current recommended version, receives bug fixes and non-breaking enhancements
2. **Deprecated** - Still functional but not recommended, security fixes only
3. **Sunset** - No longer supported, removed from API

### What Constitutes a Breaking Change?

**Breaking changes require a new version**:

- Removing a field from request/response
- Changing field type (string → number, etc.)
- Making an optional field required
- Changing HTTP status codes
- Modifying SSE event format/schema
- Renaming endpoints or parameters
- Changing authentication requirements

**Non-breaking changes (allowed in current version)**:

- Adding new optional fields
- Adding new endpoints under same version
- Bug fixes that don't change contract
- Performance improvements
- Documentation updates

## v1 Contract Freeze

### Current Status

**Brain API v1 is FROZEN** as of `brain-api-v1.0.0` (commit `a08b720`).

The contract is captured in: `services/echo_backend/models/brain_contract_v1.json`

### v1 Endpoints

| Endpoint | Method | Status |
|----------|--------|--------|
| `/v1/brain/health` | GET | ✅ Frozen |
| `/v1/brain/chat` | POST | ✅ Frozen |
| `/v1/brain/chat/stream` | POST | ✅ Frozen |

### v1 Guarantees

- ✅ Request/response schemas are immutable
- ✅ SSE event format is immutable
- ✅ Endpoint paths are immutable
- ✅ HTTP status codes are immutable
- ✅ Bug fixes only (no behavioral changes)

### v1 Deprecation Timeline

**Not yet scheduled.** v1 will remain active indefinitely until:
1. v2 is released with migration guide
2. 6-month deprecation notice is given
3. All known clients have migrated

## Contract Validation

### Automated Checks

Every push to `main` runs contract validation:

```bash
# In CI (see .github/workflows/brain_contract_smoke.yml)
1. Start backend in stub mode
2. Hit /v1/brain/health, /v1/brain/chat, /v1/brain/chat/stream
3. Validate response schemas match snapshot
4. Fail build if contract broken
```

### Local Validation

```bash
cd services/echo_backend

# Start server in stub mode
export ECHO_BRAIN_PROVIDER=stub
uvicorn main:app --host 127.0.0.1 --port 8000 &

# Run contract tests
pytest tests/test_brain_contract_snapshot.py
```

## Introducing v2 (Future)

### When to Create v2

Create v2 when you need to make **any** breaking change to v1.

Examples:
- Add required field to `ChatRequest`
- Change `Message.role` enum values
- Modify SSE event schema
- Remove deprecated fields

### v2 Creation Process

1. **Plan Breaking Changes**
   - Document all breaking changes in a design doc
   - Get approval from stakeholders (iOS, web, integrations)

2. **Implement v2**
   ```bash
   # Create new models
   services/echo_backend/models/brain_v2.py
   
   # Create new router
   services/echo_backend/routers/brain_v2.py
   
   # Register with /v2/brain prefix
   app.include_router(brain_v2.router, prefix="/v2/brain", tags=["brain-v2"])
   ```

3. **Create v2 Contract Snapshot**
   ```bash
   cd services/echo_backend
   
   # Generate v2 snapshot using official generator
   python scripts/generate_brain_contract_v2_snapshot.py
   
   # This creates: models/brain_contract_v2.json
   # Commit the generated snapshot with your v2 implementation
   ```

4. **Add v2 Contract Tests**
   ```bash
   # Copy and adapt v1 tests
   services/echo_backend/tests/test_brain_v2_*.py
   ```

5. **Update CI**
   - Add v2 contract validation to workflow
   - Keep v1 validation running (both versions supported)

6. **Document Migration**
   - Create `docs/brain_api_v1_to_v2_migration.md`
   - Include code examples for all breaking changes
   - Provide timeline for v1 deprecation

7. **Announce Deprecation**
   - GitHub Discussions post
   - Update `docs/brain_api.md` with deprecation notice
   - Set sunset date (minimum 6 months)

### v1 Deprecation Process

Once v2 is stable:

1. **T-0: Announce Deprecation**
   - Add deprecation warning to v1 docs
   - Send notice to known integrators
   - Log warning on v1 API calls (not errors yet)

2. **T+3mo: Hard Deprecation**
   - Return `Deprecation` header on v1 responses
   - Update health check to show deprecated status

3. **T+6mo: Sunset Warning**
   - Final warning to all clients
   - Confirm migration status with stakeholders

4. **T+6mo+: Sunset**
   - Remove v1 endpoints
   - Return 410 Gone for v1 paths
   - Update contract tests to expect 410

## Provider Versioning

Provider implementations (OpenAI, Anthropic, etc.) are **internal** and **not** versioned in the API.

Clients should never depend on:
- Specific LLM model names
- Provider-specific features
- Internal implementation details

Only the **contract** is versioned and stable.

## Rollback Policy

If a regression is discovered after merge:

1. **Immediate Rollback**
   - Revert the breaking commit
   - Push to main (bypass CI if necessary via emergency override)

2. **Post-Mortem**
   - Why did contract validation miss the regression?
   - Update tests to catch similar issues
   - Consider stricter validation

3. **Re-Introduce Change**
   - Fix the regression
   - Add specific test for the issue
   - Re-submit PR with clean CI

## Questions?

For questions about versioning or contract changes:

1. Check existing GitHub Issues/Discussions
2. Review `docs/ops/branch_protection.md` for contract enforcement
3. Review `docs/ops/brain_contract_smoke.md` for validation details
4. Open a GitHub Discussion for new questions

## Snapshot Management

### Regenerating Snapshots

To regenerate a contract snapshot (e.g., for non-breaking additions):

```bash
cd services/echo_backend

# For v1 (only for non-breaking changes)
python scripts/generate_brain_contract_v1_snapshot.py

# For v2 (when v2 exists)
python scripts/generate_brain_contract_v2_snapshot.py
```

**Important**: Only regenerate v1 snapshot for:
- Non-breaking additions (new optional fields)
- Bug fixes in schema documentation
- Corrections to existing non-breaking behavior

Breaking changes require creating v2 with a new snapshot.

### Snapshot Generator Details

The generator script (`scripts/generate_brain_contract_v1_snapshot.py`):
- Runs the FastAPI app in stub mode (no secrets required)
- Extracts only `/v1/brain/*` endpoints from OpenAPI schema
- Collects all referenced component schemas (recursive)
- Normalizes the contract (removes operationId, examples, x-* fields)
- Writes deterministic JSON to `models/brain_contract_v1.json`
- Outputs SHA256 hash of normalized contract

The test uses identical extraction and normalization logic via shared
utilities in `utils/brain/contract_snapshot.py`.

## Related Documentation

- `docs/brain_api.md` - Brain API reference
- `docs/ops/brain_contract_smoke.md` - Contract validation guide
- `docs/ops/branch_protection.md` - Branch protection setup
- `services/echo_backend/models/brain_contract_v1.json` - v1 OpenAPI snapshot
- `services/echo_backend/scripts/generate_brain_contract_v1_snapshot.py` - Snapshot generator
- `services/echo_backend/utils/brain/contract_snapshot.py` - Shared snapshot utilities
