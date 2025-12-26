# Echo

[![CI](https://github.com/yosiwizman/echo/actions/workflows/ci.yml/badge.svg)](https://github.com/yosiwizman/echo/actions/workflows/ci.yml)

**Echo** is an AI-powered wearable companion that listens, understands, and acts on your behalf. Built on the [Omi](https://github.com/BasedHardware/omi) open-source platform, Echo provides real-time voice interaction, intelligent note-taking, and automated action execution.

## Strategy: B1 (White-Label)

Echo follows the **B1 strategy** — ship fast by adopting Omi "as-is" and white-labeling:
- Full Omi codebase imported and rebranded as Echo
- Production-ready features from day 1
- Original scaffold preserved as fallback
- Upstream vendor snapshot for future updates

## Repository Structure

```
echo/
├── apps/
│   ├── echo_mobile/           # Echo app (Omi-based, rebranded)
│   └── echo_mobile_scaffold/  # Original scaffold (backup)
├── services/
│   ├── echo_backend/          # Echo backend (Omi-based)
│   └── echo_backend_scaffold/ # Original scaffold (backup)
├── vendor/
│   └── omi_upstream/          # Omi source snapshot (read-only reference)
├── infra/                     # Docker, scripts
├── docs/                      # Architecture documentation
└── .github/workflows/         # CI/CD pipelines
```

## Quick Start

### Prerequisites

- **Mobile**: Flutter 3.27.0+ (includes Dart 3.6.0+), required for `webview_flutter` 4.13.0
- **Backend**: Python 3.11+, Firebase project
- **Optional**: Modal account (for cloud deployment)

#### Flutter Version Management (Recommended)

This project pins Flutter 3.27.0 for deterministic builds. Use [FVM](https://fvm.app/) to manage versions:

**Windows (PowerShell):**
```powershell
# Install FVM
choco install fvm
# Or via pub:
dart pub global activate fvm

# Install and use pinned Flutter version
fvm install
fvm use
```

**macOS/Linux:**
```bash
# Install FVM
brew tap leoafarias/fvm
brew install fvm
# Or via pub:
dart pub global activate fvm

# Install and use pinned Flutter version
fvm install
fvm use
```

Once FVM is set up, prefix Flutter commands with `fvm`:
```bash
fvm flutter pub get
fvm flutter run
```

**Note**: iOS builds require macOS + Xcode 15+

### Running the Mobile App

```bash
cd apps/echo_mobile

# Get dependencies
flutter pub get

# Set up environment (copy and configure)
cp .env.template .env
# Edit .env with your API keys

# Generate environment config
flutter pub run build_runner build

# Run (dev flavor)
flutter run --flavor dev
```

**Note**: The app requires Firebase configuration. See `apps/echo_mobile/README.md` for setup.

### Running the Backend

```bash
cd services/echo_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.template .env
# Edit .env with Firebase credentials and API keys

# Run locally
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Note**: Backend requires Firebase service account. See `services/echo_backend/README.md`.

### Running the Original Scaffold (Fallback)

If you need a simpler starting point without Firebase:

```bash
# Backend
cd services/echo_backend_scaffold
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Mobile
cd apps/echo_mobile_scaffold
flutter pub get
flutter run
```

## API Overview

Echo backend exposes the full Omi API:

| Category | Key Endpoints |
|----------|---------------|
| Transcription | `WS /v3/listen` - Real-time audio transcription |
| Chat | `POST /v2/messages` - AI chat with LangGraph |
| Memories | `GET/POST /v1/memories` - Memory management |
| Apps/Plugins | `GET/POST /v1/apps` - App marketplace |
| Auth | `/v1/auth/*` - OAuth2 authentication |

Full API docs at `http://localhost:8000/docs` when running.

## Upstream Attribution

Echo is built on [Omi](https://github.com/BasedHardware/omi) by Based Hardware.

- **Upstream Commit**: `e1c5e81fb1c72f49ac8b7c2a86c45838b0b94a52`
- **License**: MIT (see `vendor/omi_upstream/LICENSE`)
- **Provenance**: `vendor/omi_upstream/PROVENANCE.md`

## Customizing Echo

### Changing App Identifiers

**Android** (`apps/echo_mobile/android/app/build.gradle`):
```groovy
applicationId "com.yourcompany.echo"
resValue "string", "app_name", "Your App Name"
```

**iOS**: Update bundle identifier in Xcode or `ios/Runner.xcodeproj/project.pbxproj`

### App Icons

Replace `apps/echo_mobile/assets/images/app_launcher_icon.png` and run:
```bash
flutter pub run flutter_launcher_icons
```

## Phase Roadmap

### Phase 0 — Foundation ✅
- Monorepo structure
- Simple scaffold for rapid iteration
- CI/CD pipeline

### Phase 1 — Omi Import ✅ (Current)
- Import Omi codebase
- White-label rebrand to Echo
- Preserve scaffold as fallback

### Phase 2 — Customization
- Custom UI themes
- Additional integrations
- Enhanced privacy controls

### Phase 3 — Hardware
- BLE device support
- Custom firmware
- Wearable optimizations

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

Echo includes code from Omi (MIT License) — see `vendor/omi_upstream/LICENSE`.

---

*Echo: Your AI companion that listens and acts.*
