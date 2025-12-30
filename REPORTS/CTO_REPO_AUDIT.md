# Echo — CTO Repo Audit (Repo-Grounded)
Date: 2025-12-30
Auditor: Principal Engineer / Acting CTO (Delivery Owner)

## Executive Summary
Echo is a mono-repo containing:
- A Flutter mobile app at `apps/echo_mobile`
- A FastAPI backend at `services/echo_backend`
- A vendored upstream snapshot of Omi at `vendor/omi_upstream` (reference)

This repo is now **unblocked for day-to-day development** (build/analyze/test/health paths are deterministic) after addressing the highest-impact breakages:
- The Flutter app package is `echo_mobile`, but large parts of the codebase still self-imported using `package:omi/...` (upstream name). This caused the analyzer “error explosion.” Those imports are now migrated: `git grep "package:omi/" -- apps/echo_mobile` returns no matches.
- Backend local/dev/CI startup is now possible without Firebase credentials (best-effort init) and with deterministic health endpoints.
- CI no longer suppresses failures; it runs fail-fast checks that do not require proprietary secrets.

### What was blocking forward velocity (root causes)
1. **Flutter namespace drift**: `apps/echo_mobile/pubspec.yaml` declares `name: echo_mobile`, but the code imported itself as `package:omi/...` across the tree.
2. **Backend reproducibility gaps**:
   - Windows contributors were blocked by platform-specific dependencies (`uvloop` in `requirements.txt`).
   - Docker + compose paths were inconsistent with backend layout.
3. **Non-deterministic CI**: CI intentionally ignored failures (`|| true`), preventing a reliable feedback loop.

### What this remediation establishes (foundation PR)
Mobile (`apps/echo_mobile`):
- Analyzer correctness restored: `flutter analyze` reports **0 errors** on Flutter 3.27.0 (warnings/infos remain; see cleanup backlog).
- Minimal test signal: `flutter test` has at least a smoke test (`test/smoke_test.dart`).
- “No secrets committed” posture: placeholder generated env files and Firebase options are present so the app compiles/analyzes, but must be replaced locally for real environments.

Backend (`services/echo_backend`):
- Deterministic health endpoints:
  - HTTP: `GET/HEAD /healthz`, `/health`, `/v1/health`
  - WebSocket: `/ws/health`
- Best-effort Firebase Admin initialization so the server can boot in CI/onboarding without credentials (opt-in strict mode via `ECHO_REQUIRE_FIREBASE=1`).
- Windows install unblocked by platform-gating `uvloop` in `requirements.txt`.

CI (`.github/workflows/ci.yml`):
- Fail-fast lint + smoke tests for backend and mobile; analyzer only fails on `[error]` lines.

## Repository Structure (Key Directories)
- `apps/echo_mobile/` — Primary Flutter app
- `apps/echo_mobile_scaffold/` — Minimal legacy scaffold (fallback)
- `services/echo_backend/` — Primary backend (FastAPI)
- `services/echo_backend_scaffold/` — Minimal legacy scaffold (fallback)
- `vendor/omi_upstream/` — Upstream Omi snapshot (reference)
- `infra/docker-compose.yml` — Docker Compose for local backend
- `.github/workflows/ci.yml` — Root CI workflow

## Dependency & Build Tooling Inventory
### Flutter/Dart
- Package manager: `pub` via `apps/echo_mobile/pubspec.yaml`
- Flutter pinned via FVM: `.fvmrc` (Flutter `3.27.0`)
- BLE: `flutter_blue_plus` + Windows shim (`flutter_blue_plus_windows`) via `apps/echo_mobile/lib/utils/bluetooth/bluetooth_adapter.dart`
- Real-time transport: WebSockets via `web_socket_channel` (see `apps/echo_mobile/lib/services/sockets/pure_socket.dart`)
- Local path dependency: `opus_dart` via `../../packages/opus_dart`

### iOS (Flutter host)
- CocoaPods: `apps/echo_mobile/ios/Podfile`
- Xcode project: `apps/echo_mobile/ios/Runner.xcodeproj`
- Schemes present: `dev.xcscheme`, `prod.xcscheme`, `omiWatchApp.xcscheme` under `apps/echo_mobile/ios/Runner.xcodeproj/xcshareddata/xcschemes/`

### Backend (Python)
- Dependency manager: `pip` via `services/echo_backend/requirements.txt`
- Dev tooling: `services/echo_backend/requirements-dev.txt`
- Entrypoint: `services/echo_backend/main.py` (FastAPI app)
- Health routes: `services/echo_backend/routers/other.py`
- Transcription WebSocket: `services/echo_backend/routers/transcribe.py` (`/v4/listen`)

## Architecture (Current) — ASCII Diagram
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        iOS / Flutter (apps/echo_mobile)                     │
│                                                                             │
│  ┌──────────────┐        ┌──────────────────┐       ┌───────────────────┐  │
│  │ BLE Device(s) │ ─BLE─▶ │ BleTransport     │ ───▶  │ DeviceConnection   │  │
│  │ (Omi, etc.)   │        │ (ble_transport)  │       │ (omi_connection)   │  │
│  └──────────────┘        └──────────────────┘       └───────────────────┘  │
│                                   │                       │                 │
│                                   │ audio bytes           │ button/image    │
│                                   ▼                       ▼                 │
│                           ┌─────────────────────────────────────────────┐   │
│                           │ CaptureProvider                              │   │
│                           │ (providers/capture_provider.dart)            │   │
│                           └─────────────────────────────────────────────┘   │
│                                             │                               │
│                                             │ WS binary frames + JSON msgs  │
│                                             ▼                               │
│                           ┌─────────────────────────────────────────────┐   │
│                           │ PureSocket / TranscriptSegmentSocketService │   │
│                           │ (services/sockets/*)                        │   │
│                           └─────────────────────────────────────────────┘   │
│                                             │                               │
└─────────────────────────────────────────────┼───────────────────────────────┘
                                              │ wss://<apiBaseUrl>/v4/listen
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (services/echo_backend)                │
│                                                                             │
│  main.py (FastAPI)                                                          │
│    ├─ routers/transcribe.py : WebSocket /v4/listen                          │
│    ├─ routers/other.py      : /healthz + /ws/health                         │
│    └─ other routers (conversations, memories, apps, mcp, etc.)              │
│                                                                             │
│  /v4/listen streams transcripts + MessageEvents back to the client           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## iOS Capabilities / Permissions (Inventory)
Source of truth: `apps/echo_mobile/ios/Runner/Info.plist` and `apps/echo_mobile/ios/Runner/Runner.entitlements`.

### Background execution / scheduling
From `apps/echo_mobile/ios/Runner/Info.plist`:
- `UIBackgroundModes` includes:
  - `audio`
  - `location`
  - `bluetooth-central`
  - `fetch`
  - `processing`
  - `remote-notification`
- `BGTaskSchedulerPermittedIdentifiers` includes:
  - `daily-summary`
  - `com.friend-app-with-wearable.ios12.daily-summary`
  - `dev.flutter.background.refresh`
  - `com.pravera.flutter_foreground_task.refresh`

### User-facing permission prompts
From `apps/echo_mobile/ios/Runner/Info.plist`:
- Bluetooth:
  - `NSBluetoothAlwaysUsageDescription`
  - `NSBluetoothPeripheralUsageDescription`
- Microphone:
  - `NSMicrophoneUsageDescription`
- Siri:
  - `NSSiriUsageDescription`
- Location:
  - `NSLocationAlwaysAndWhenInUseUsageDescription`
  - `NSLocationWhenInUseUsageDescription`
  - `NSLocationUsageDescription`
- Calendar/Contacts/Reminders:
  - `NSCalendarsFullAccessUsageDescription`
  - `NSCalendarsUsageDescription`
  - `NSContactsUsageDescription`
  - `NSRemindersUsageDescription`
- Photos/Camera:
  - `NSPhotoLibraryUsageDescription`
  - `NSCameraUsageDescription`

### Deep links / associated domains / push
- URL schemes (`CFBundleURLTypes`) include:
  - `https`
  - `$(GOOGLE_REVERSE_CLIENT_ID)`
  - `omi`
- Entitlements (`apps/echo_mobile/ios/Runner/Runner.entitlements`) include:
  - `aps-environment = development`
  - `com.apple.developer.applesignin = Default`
  - `com.apple.developer.associated-domains`:
    - `applinks:h.omi.me`
    - `applinks:try.omi.me`

## BLE Integration Mapping (Mobile)
### Discovery
- BLE scanning: `apps/echo_mobile/lib/services/devices/discovery/bluetooth_discoverer.dart`
- Cross-platform BLE abstraction:
  - `apps/echo_mobile/lib/utils/bluetooth/bluetooth_adapter.dart` (uses `flutter_blue_plus_windows` on Windows, `flutter_blue_plus` elsewhere)

### Connection + protocol surfaces
- Connection factory and transport selection: `apps/echo_mobile/lib/services/devices/device_connection.dart`
  - BLE transport implementation: `apps/echo_mobile/lib/services/devices/transports/ble_transport.dart`
- Omi/OpenGlass device connection:
  - `apps/echo_mobile/lib/services/devices/omi_connection.dart`
  - BLE UUID constants (audio/button/storage/battery/etc): `apps/echo_mobile/lib/services/devices/models.dart`
- Omi device feature flags:
  - `apps/echo_mobile/lib/services/devices.dart` (`class OmiFeatures`, firmware bit flags)

### Omi audio + button + storage UUIDs (as implemented)
Source: `apps/echo_mobile/lib/services/devices/models.dart` and `apps/echo_mobile/lib/services/devices/omi_connection.dart`.
- Omi service: `omiServiceUuid = 19b10000-e8f2-537e-4f6c-d104768a1214`
- Audio stream characteristic: `audioDataStreamCharacteristicUuid = 19b10001-e8f2-537e-4f6c-d104768a1214`
- Audio codec characteristic: `audioCodecCharacteristicUuid = 19b10002-e8f2-537e-4f6c-d104768a1214`
- Button:
  - `buttonServiceUuid = 23ba7924-0000-1000-7450-346eac492e92`
  - `buttonTriggerCharacteristicUuid = 23ba7925-0000-1000-7450-346eac492e92`
- Battery:
  - `batteryServiceUuid = 0000180f-0000-1000-8000-00805f9b34fb`
  - `batteryLevelCharacteristicUuid = 00002a19-0000-1000-8000-00805f9b34fb`
- Storage:
  - `storageDataStreamServiceUuid = 30295780-4301-eabd-2904-2849adfeae43`
  - `storageDataStreamCharacteristicUuid = 30295781-4301-eabd-2904-2849adfeae43`
  - `storageReadControlCharacteristicUuid = 30295782-4301-eabd-2904-2849adfeae43`

## Audio Pipeline Mapping (Mobile → Backend)
### Device audio → WebSocket
- BLE audio bytes subscription:
  - `apps/echo_mobile/lib/services/devices/omi_connection.dart` (`performGetBleAudioBytesListener`)
- Streaming BLE audio to backend:
  - `apps/echo_mobile/lib/providers/capture_provider.dart` (`streamAudioToWs`)
  - Implementation notes:
    - For Omi/OpenGlass devices, the first 3 bytes are treated as padding/metadata and trimmed before sending (`paddingLeft = 3`).
    - Binary audio frames are sent via `_socket?.send(trimmedValue)`.

### WebSocket client contract
- WebSocket URL construction:
  - `apps/echo_mobile/lib/services/sockets/transcription_service.dart` (`TranscriptSegmentSocketService.create`)
  - Uses `Env.apiBaseUrl` and connects to `/v4/listen` with query params including:
    - `language`, `sample_rate`, `codec`, `uid`, `include_speech_profile`, `stt_service`, `conversation_timeout`, plus optional `source`
- WebSocket transport + ping handling:
  - `apps/echo_mobile/lib/services/sockets/pure_socket.dart`
  - The client treats server text message `"ping"` specially and manually emits a pong frame.

## Backend Mapping
### Entrypoint
- `services/echo_backend/main.py`
  - Creates `app = FastAPI()` and includes routers (notably `transcribe`, `conversations`, `memories`, `mcp`, etc.)
  - Performs best-effort Firebase Admin initialization at process start (`_init_firebase_admin()`)

### Health endpoints (CI + onboarding)
- `services/echo_backend/routers/other.py`
  - HTTP: `/healthz`, `/health`, `/v1/health`
  - WebSocket: `/ws/health`

### Real-time transcription WebSocket
- `services/echo_backend/routers/transcribe.py`
  - WebSocket endpoint: `@router.websocket("/v4/listen")`
  - Auth dependency: `uid: str = Depends(auth.get_current_user_uid)`

## Target Architecture Fit: “Web Brain + iOS Shell”
### What should remain in iOS/Flutter shell
- Audio capture + background execution constraints (see iOS `UIBackgroundModes`)
- BLE scanning/connection and device protocol parsing
- “On-device realities” (Watch connectivity, headset constraints, OS permissions)

### What should move server-side (Web Brain)
- Agent orchestration and tool-calling
- Memory, summarization, knowledge graph and search
- Integrations that benefit from centralized credentials and consistent compute

## Ranked Blockers (Post-Remediation)
1. **Residual rebrand drift / naming cleanup**: iOS schemes and associated domains still contain `omi` naming (`omiWatchApp`, `applinks:h.omi.me`). This is no longer a build blocker, but it’s a product/ops risk.
2. **Backend dependency footprint**: `services/echo_backend/requirements.txt` is large and will keep CI slow unless we introduce a slim “smoke” install path.
3. **Integration tests require secrets**: tests under `services/echo_backend/tests/integration/*` require real Firebase credentials and are excluded by default via `pytest.ini`.
4. **Flutter lint backlog**: `flutter analyze` reports many warnings/infos (e.g., `avoid_print`, `build_context_synchronously`, deprecations). These are triageable now that errors are gone.

## Next 3 Steps (Authoritative, Repo-Specific)
1. **Land this PR and enforce deterministic CI**
   - Require `.github/workflows/ci.yml` to pass on every PR.
   - Keep mobile analyzer “errors-only” until the warning/infos backlog is burned down.

2. **Close the iOS “capabilities reality gap” for Echo branding**
   - Decide which iOS entitlements/domains/schemes are truly needed for Echo.
   - Update:
     - `apps/echo_mobile/ios/Runner/Runner.entitlements`
     - `apps/echo_mobile/ios/Runner/Info.plist`
     - `apps/echo_mobile/ios/Runner.xcodeproj/xcshareddata/xcschemes/*`

3. **Define the Web Brain contract and de-risk audio ingest**
   - Treat `/v4/listen` as the first stable contract boundary; document the binary frame format and any required metadata.
   - Add a minimal end-to-end test (mobile → backend → transcript event) behind a secrets-free fake STT provider.
