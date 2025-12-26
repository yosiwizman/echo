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

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or with Docker:

```bash
cd infra
docker-compose up echo-backend
```

The API will be available at `http://localhost:8000`. Health check: `GET /healthz`

### Running the Mobile App

```bash
cd apps/echo_mobile

# Get dependencies
flutter pub get

# Run on connected device/emulator
flutter run
```

Configure the backend URL in `lib/config/app_config.dart`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/healthz` | Health check |
| POST | `/chat` | Chat with Echo (stub) |
| POST | `/notes` | Create a note |
| GET | `/notes` | List all notes |
| GET | `/notes/{id}` | Get note by ID |
| DELETE | `/notes/{id}` | Delete a note |

## Development

### Backend Commands

```bash
cd services/echo_backend

# Lint
ruff check .

# Type check
mypy app

# Test
pytest

# Format
ruff format .
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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Echo: Your AI companion that listens and acts.*
