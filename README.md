# Echo

[![CI](https://github.com/yosiwizman/echo/actions/workflows/ci.yml/badge.svg)](https://github.com/yosiwizman/echo/actions/workflows/ci.yml)

**Echo** is an AI-powered wearable companion that listens, understands, and acts on your behalf. Built with a Flutter mobile app and a FastAPI backend, Echo is designed for real-time voice interaction with intelligent note-taking and action execution.

## Project Status

**Phase 1 Complete** ✅ — Omi baseline imported and white-labeled as Echo  
**Phase 2 Active** 🚧 — White-label productization and branding abstraction

## Strategy: White-Label Platform

Echo is built as a **white-label AI companion platform** based on [Omi](https://github.com/BasedHardware/omi):
- Full Omi codebase vendored and rebranded
- Centralized branding configuration for easy customization
- Production-ready features from day 1 (transcription, chat, memory, BLE)
- Clear separation between platform code and brand identity

## Repository Structure

```
echo/
├── apps/
│   ├── echo_mobile/              # Flutter app (Omi-based, rebranded)
│   │   └── lib/branding/         # ← Branding configuration
│   └── echo_mobile_scaffold/     # Original scaffold (fallback)
├── services/
│   ├── echo_backend/             # FastAPI backend (Omi-based)
│   │   └── app/config/branding/  # ← Branding configuration
│   └── echo_backend_scaffold/    # Original scaffold (fallback)
├── vendor/
│   └── omi_upstream/             # Omi source snapshot (reference)
├── infra/                        # Docker, deployment configs
├── docs/                         # Architecture documentation
└── .github/workflows/            # CI/CD pipelines
```

## White-Label Architecture

Echo uses a **centralized branding configuration** to enable easy customization:

### Mobile App Branding

**Configuration:** `apps/echo_mobile/lib/branding/branding_config.dart`

```dart
class BrandingConfig {
  static const String appName = 'Echo';
  static const int primaryColorValue = 0xFF000000;
  static const String logoAssetPath = 'assets/images/herologo.png';
  // ... more config
}
```

**To rebrand:**
1. Update `BrandingConfig` values (name, colors, logo path)
2. Replace logo assets in `assets/images/`
3. Update platform identifiers:
   - Android: `android/app/build.gradle` (applicationId, app_name)
   - iOS: `ios/Runner/Info.plist` (bundle identifier)
4. Rebuild and test

### Backend Branding

**Configuration:** `services/echo_backend/app/config/branding.py`

```python
class BrandingConfig:
    PRODUCT_NAME = "Echo"
    API_TITLE = "Echo API"
    SUPPORT_EMAIL = "support@echo.example.com"
    # ... more config
```

**To rebrand:**
1. Update `BrandingConfig` class constants
2. Update environment-specific settings if needed
3. Restart backend

See `docs/ARCHITECTURE.md` for detailed white-label guidance.

## Run Echo Locally

### First-Time Setup

**Quick preview in 3 steps:**

1. **Clone and navigate:**
   ```bash
   git clone https://github.com/yosiwizman/echo.git
   cd echo/apps/echo_mobile
   ```

2. **Install dependencies:**
   ```bash
   # With FVM (recommended)
   fvm install && fvm use
   fvm flutter pub get
   
   # Without FVM
   flutter pub get
   ```

3. **Run on emulator:**
   ```bash
   # Android
   flutter run
   
   # iOS (macOS only)
   open -a Simulator && flutter run
   ```

**That's it!** Echo will launch on your emulator with a functional UI.

### Detailed Instructions

For complete setup instructions including:
- Platform-specific requirements (Android Studio, Xcode)
- Physical device setup
- Troubleshooting common issues
- Expected first-run behavior
- Build for distribution

**Platform-specific guides:**
- **Windows + Android:** [docs/ANDROID_PREVIEW_WINDOWS.md](docs/ANDROID_PREVIEW_WINDOWS.md) — Detailed Windows setup with Android emulator
- **General:** [docs/PREVIEW.md](docs/PREVIEW.md) — Cross-platform preview guide

### Backend (Optional for Preview)

The mobile app runs standalone. To test full backend integration, see "Quick Start" below.

## Quick Start

### Prerequisites

- **Mobile**: Flutter 3.27.0+ (includes Dart 3.6.0+), FVM recommended
- **Backend**: Python 3.11+, Firebase project
- **Optional**: Modal account (for cloud deployment)

### Running the Backend

```bash
cd services/echo_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create env file
cp .env.example .env

# Install dependencies
# NOTE: On Windows, uvloop is skipped automatically via environment markers.
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --env-file .env
```

Or with Docker:

```bash
cd infra
docker compose up echo-backend
```

The API will be available at `http://localhost:8000`.
- HTTP health: `GET /healthz`
- WebSocket health: connect to `ws://localhost:8000/ws/health`

## API Documentation
FastAPI serves Swagger UI and OpenAPI docs by default:
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Running the Mobile App

```bash
cd apps/echo_mobile

# Get dependencies
flutter pub get

# Run on connected device/emulator
flutter run
```

Configure the backend URL in `lib/config/app_config.dart`.

## Development

### Backend Commands

```bash
cd services/echo_backend

# Install dev tooling
pip install -r requirements-dev.txt

# Lint (fail-fast)
ruff check . --select E9,F63,F7,F82

# Unit/smoke tests (integration tests are excluded by default)
pytest
```

### Mobile Commands

```bash
cd apps/echo_mobile

# Analyze
flutter analyze

# Test
flutter test

# Build
flutter build apk  # Android
flutter build ios  # iOS
```

## Phase Roadmap

### Phase 0 — Foundation ✅
- Monorepo structure
- FastAPI backend scaffold
- Flutter app scaffold
- CI/CD pipeline
- Documentation

### Phase 1 — Omi Import ✅ 
- Import Omi codebase to vendor/
- Rebrand Omi → Echo (names, IDs, strings)
- Configure CI for Flutter 3.27.0 stable
- Align dependencies for Dart 3.6.0
- FVM configuration
- Baseline tag: `v0.1.0-white-label-base`

### Phase 2 — White-Label Productization 🚧 (Current)
- Centralized branding configuration (mobile + backend)
- White-label documentation and guidelines
- Multi-brand deployment strategy
- Asset management and theme system

### Phase 3 — Production Hardening
- Firebase project setup
- API key configuration
- Cloud deployment
- End-to-end testing
- Performance optimization

### Phase 4 — Customization & Features
- Custom UI/UX enhancements
- Additional integrations
- Enhanced privacy controls
- Analytics and monitoring

## Runtime Monitoring

The backend includes always-on runtime smoke monitoring that validates staging and production deployments every 15 minutes:

- **What it checks**: `/health` and `/version` endpoints for HTTP 200, valid JSON, correct `env`, valid `git_sha`, and `build_time`
- **Where to see it**: [GitHub Actions → Backend Runtime Smoke Monitor](https://github.com/yosiwizman/echo/actions/workflows/backend_runtime_smoke.yml)
- **Manual trigger**: `gh workflow run backend_runtime_smoke.yml --repo yosiwizman/echo`
- **Full docs**: [docs/ops/runtime_smoke_monitoring.md](docs/ops/runtime_smoke_monitoring.md)

## GCP Uptime Alerting

Cloud Monitoring uptime checks with email alerts monitor both staging and production:

- **What it monitors**: `/health` endpoint every 60 seconds with JSON validation
- **Alerts**: Email notifications on failures lasting 120+ seconds
- **Setup/Run**: `ALERT_EMAIL="you@example.com" bash ops/gcp/monitoring/apply_monitoring.sh`
- **Full docs**: [docs/ops/gcp_uptime_alerting.md](docs/ops/gcp_uptime_alerting.md)

## Alert Self-Test

Verify the end-to-end alerting pipeline without causing real downtime:

- **What it does**: Triggers a test alert via protected endpoint `/ops/alert-test`
- **How to run**: GitHub Actions → Alert Self-Test → Run workflow
- **Full docs**: [docs/ops/alerting_self_test.md](docs/ops/alerting_self_test.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Echo: Your AI companion that listens and acts.*
