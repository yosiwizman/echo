# Branch Protection for Main

## Overview

This document describes the branch protection rules required for the `main` branch to ensure platform stability and prevent regressions.

## Purpose

Branch protection enforces:
- **No direct pushes** to `main` (all changes via PR)
- **Required CI checks** must pass before merge
- **Squash merge only** for clean git history
- **Contract stability** for external consumers (iOS, web, integrations)

## Required Status Checks

The following CI workflows MUST pass before any PR can be merged to `main`:

### 1. Backend Tests
- **Workflow**: `.github/workflows/ci.yml` → `backend` job
- **What it checks**: 
  - Ruff linting
  - Unit tests with pytest
  - Smoke tests (health endpoints)

### 2. Mobile Tests
- **Workflow**: `.github/workflows/ci.yml` → `mobile` job
- **What it checks**:
  - Flutter analyze
  - Flutter test (unit + widget tests)

### 3. Scaffold Tests (Legacy)
- **Workflow**: `.github/workflows/ci.yml` → `scaffold_tests` job
- **What it checks**:
  - Backward compatibility for legacy endpoints

### 4. Brain API Contract Validation
- **Workflow**: `.github/workflows/brain_contract_smoke.yml` → `contract-validation` job
- **What it checks**:
  - Brain API v1 contract stability
  - Health, chat, and streaming endpoints
  - OpenAPI schema matches committed snapshot

## Manual Setup Instructions

### Step-by-Step (GitHub UI)

1. **Navigate to Repository Settings**
   - Go to: `https://github.com/yosiwizman/echo/settings/branches`
   - Or: Settings → Branches → Branch protection rules

2. **Add Branch Protection Rule**
   - Click "Add branch protection rule"
   - Branch name pattern: `main`

3. **Enable Required Settings**
   
   Check the following boxes:

   ✅ **Require a pull request before merging**
   - Required approvals: 0 (single maintainer workflow)
   - Dismiss stale pull request approvals when new commits are pushed: ✅
   
   ✅ **Require status checks to pass before merging**
   - Require branches to be up to date before merging: ✅
   
   Search for and add these required status checks:
   - `backend` (from CI / backend)
   - `mobile` (from CI / mobile)
   - `scaffold_tests` (from CI / scaffold_tests)
   - `contract-validation` (from Brain API Contract Validation)
   
   ✅ **Require conversation resolution before merging**
   
   ✅ **Do not allow bypassing the above settings**

4. **Merge Strategy Settings**
   - Navigate to: Settings → General → Pull Requests
   - Uncheck: "Allow merge commits"
   - Uncheck: "Allow rebase merging"
   - ✅ Check: "Allow squash merging"
   - Set default commit message: "Pull request title and description"

5. **Save Changes**
   - Click "Create" or "Save changes"

### Verification

After setup, verify protection is active:

```bash
# Try to push directly to main (should fail)
git checkout main
git commit --allow-empty -m "test: direct push"
git push origin main
# Expected: remote rejected (protected branch)
```

If you see:
```
remote: error: GH006: Protected branch update failed for refs/heads/main.
```

✅ Branch protection is active.

## Why These Rules Matter

### Prevents Production Incidents
- Breaking changes caught in CI before merge
- Contract regressions blocked automatically
- No accidental direct commits bypass review

### Enables External Integrations
- iOS app can trust API stability
- Web clients rely on versioned contracts
- Third-party integrations have predictable behavior

### Maintains Code Quality
- All code passes linting + tests
- Consistent git history (squash merges)
- Clear audit trail for changes

## Contract Stability Guarantee

The Brain API v1 contract is **frozen** and validated on every push. Any changes that break the contract will fail the `contract-validation` check.

**Breaking changes require**:
- New API version path: `/v2/brain/*`
- Updated contract snapshot
- Migration guide for existing clients

See: `docs/brain_versioning.md` for versioning policy.

## Emergency Override (Not Recommended)

In extreme cases (production hotfix, critical security patch), repository admins can temporarily disable branch protection:

1. Settings → Branches → Edit rule for `main`
2. Uncheck "Do not allow bypassing the above settings"
3. Push fix
4. **Immediately re-enable** protection

⚠️ **Always document emergency overrides in commit message and post-merge retrospective.**

## Maintenance

**When adding new workflows:**
1. Add workflow file to `.github/workflows/`
2. Update this document with new required check
3. Add check to branch protection rules (GitHub UI)

**When deprecating workflows:**
1. Remove from branch protection rules first
2. Delete workflow file
3. Update this document

## Related Documentation

- `docs/ops/brain_contract_smoke.md` - Contract validation details
- `docs/brain_versioning.md` - API versioning policy
- `.github/workflows/brain_contract_smoke.yml` - Contract validation workflow
