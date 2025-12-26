# Echo Architecture

## Overview

Echo is an AI-powered wearable companion designed for real-time voice interaction, intelligent note-taking, and automated action execution. This document outlines the system architecture and strategic decisions.

## Strategy: B1 (Ship Fast)

Echo follows the **B1 strategy**, which means:

1. **Vendor Omi as-is** — We import the [Omi](https://github.com/BasedHardware/omi) codebase directly and white-label it as Echo.

2. **Rebrand, don't rewrite** — Minimal changes: app name, bundle IDs, assets. Keep Omi's proven architecture intact.

3. **Ship fast, iterate later** — Get to market quickly, then customize based on user feedback.

### Why B1?

- **Speed**: Omi is production-tested. Reusing it directly gets us to market fastest.
- **Risk reduction**: Proven codebase with existing features (BLE, transcription, memory) means fewer bugs.
- **Upgrade path**: Keeping close to upstream makes pulling future Omi improvements easier.

## Repository Structure

```
echo/
├── apps/
│   ├── echo_mobile/           # Omi-based Flutter app (rebranded)
│   └── echo_mobile_scaffold/  # Original scaffold (fallback)
├── services/
│   ├── echo_backend/          # Omi-based backend
│   └── echo_backend_scaffold/ # Original scaffold (fallback)
├── vendor/
│   └── omi_upstream/          # Read-only Omi snapshot
├── infra/                     # Docker, deployment configs
└── docs/                      # Documentation
```

### Vendor Directory

The `vendor/omi_upstream/` directory contains a read-only snapshot of the Omi codebase at a specific commit. This serves as:
- Reference for upstream changes
- Source of truth for what we imported
- Easy diffing when pulling upstream updates

See `vendor/omi_upstream/PROVENANCE.md` for the exact commit and import date.

### Scaffold Directories

The `*_scaffold` directories contain our original Phase 0 implementation:
- `apps/echo_mobile_scaffold/` — Custom Flutter app scaffold
- `services/echo_backend_scaffold/` — Custom FastAPI backend scaffold

These are preserved as fallback if we need to pivot away from the Omi baseline.

## System Components

### 1. Echo Mobile (Flutter)

The mobile app is based on Omi's Flutter application, rebranded as Echo.

**Key directories:**
- `lib/` — Dart source code
- `android/` — Android platform code (applicationId: `com.yosiwizman.echo`)
- `ios/` — iOS platform code (bundleId: `com.yosiwizman.echo`)

**Branding changes applied:**
- App name: "Echo" (was "Omi")
- Package name: `echo_mobile`
- Bundle/Application IDs: `com.yosiwizman.echo`
- UI strings: "Omi" → "Echo" throughout

### 2. Echo Backend (Python)

The backend is based on Omi's Python backend with Firebase, Pinecone, and various AI integrations.

**Key directories:**
- `routers/` — API endpoints
- `models/` — Data models
- `utils/` — Utility functions

### 3. Infrastructure

```
infra/
├── docker-compose.yml   # Local development stack
└── (future)             # Kubernetes, Terraform
```

## Omi Features (Inherited)

By adopting Omi as our baseline, Echo inherits:

- **Real-time transcription** via WebSocket with multiple STT providers
- **LangGraph chat processing** with tool routing
- **Memory system** with vector search (Pinecone)
- **BLE device support** for Omi-compatible wearables
- **Firebase integration** for auth and data storage
- **Plugin system** for extensibility

### Configuration Required

The Omi backend requires environment variables for:
- Firebase credentials
- OpenAI/Deepgram API keys
- Pinecone vector database
- Various third-party integrations

See `services/echo_backend/.env.template` for the full list.

## Phase Roadmap

### Phase 0 — Foundation ✅
- Monorepo structure
- FastAPI backend scaffold
- Flutter app scaffold
- CI/CD pipeline
- Documentation

### Phase 1 — Omi Import + White-Label 🚧
**Goal**: Ship Echo using Omi baseline

- Import Omi codebase to vendor/
- Move scaffolds to fallback directories
- Rebrand Omi → Echo (names, IDs, strings)
- Update CI for Omi structure
- Document the import

### Phase 2 — Configuration & Deploy
**Goal**: Make Echo runnable

- Set up Firebase project
- Configure API keys (OpenAI, Deepgram, etc.)
- Deploy backend to cloud
- Build and test mobile app
- First end-to-end test

### Phase 3 — Customization
**Goal**: Differentiate from Omi

- Custom branding/UI polish
- Echo-specific features
- Remove unused Omi features
- Optimize for our use case

## CI Configuration

CI runs on every push to `main` and on pull requests.

### Primary Jobs (Omi-based)

**backend-lint**: Runs ruff on `services/echo_backend/`
- Currently permissive (`|| true`) as Omi codebase has existing lint issues
- Will be tightened as we clean up the code

**mobile-build**: Validates Flutter app structure
- Uses Flutter 3.24.0 (pinned for reproducibility)
- Checks that required directories exist
- Runs `flutter pub get`
- Runs `flutter analyze` (permissive mode)

### Scaffold Jobs (Fallback)

**scaffold-tests**: Tests our original scaffold code
- Runs ruff, mypy, pytest on `services/echo_backend_scaffold/`
- Runs flutter analyze/test on `apps/echo_mobile_scaffold/`
- Ensures fallback code remains healthy

### Permissive Mode

The Omi codebase has existing lint/type issues that we haven't fixed yet. CI uses `|| true` to prevent these from blocking PRs. As we clean up the code, we'll remove these workarounds.

### Flutter SDK Dependencies

CI uses Flutter 3.24.0 which pins certain core packages (e.g., `collection: 1.18.0`). The `pubspec.yaml` aligns direct dependencies with these constraints to avoid version conflicts.

**When upgrading Flutter:**
1. Check Flutter SDK's pinned package versions
2. Update `pubspec.yaml` constraints if needed
3. Test with `flutter pub get` and `flutter analyze`
4. Review any deprecation warnings

## Security Considerations

- No secrets in code or logs
- Environment-based configuration
- CORS properly configured for production
- API authentication (future: OAuth2/JWT)
- Encrypted data at rest (future)

## Upstream Sync Strategy

To pull updates from Omi upstream:

1. Clone fresh Omi repo
2. Copy to `vendor/omi_upstream/` (replace existing)
3. Update `vendor/omi_upstream/PROVENANCE.md` with new commit
4. Diff against `apps/echo_mobile/` and `services/echo_backend/`
5. Apply relevant changes, preserving Echo branding

Keep changes minimal to make upstream syncs easier.

---

*This document evolves with the project. Last updated: Phase 1 (B1 import).*
