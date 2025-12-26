# Echo Architecture

## Overview

Echo is a **white-label AI companion platform** built on the [Omi](https://github.com/BasedHardware/omi) open-source ecosystem. This document outlines the system architecture, white-label strategy, and strategic decisions.

**Current Status:** Phase 2 (White-Label Productization)  
**Baseline:** `v0.1.0-white-label-base`

## Strategy: B2 (Best Practice)

Echo follows the **B2 strategy**, which means:

1. **Build on Omi's patterns** — We leverage the [Omi](https://github.com/BasedHardware/omi) open-source ecosystem for proven architecture, BLE protocols, and device assumptions.

2. **Own the backend** — We control our backend infrastructure from day 1. No dependency on Omi's hosted services.

3. **Reference, don't fork** — We study Omi's architecture and adapt patterns to our needs rather than maintaining a fork.

### Why B2?

- **Velocity**: Omi has solved many problems (BLE streaming, VAD, transcription pipelines). Learning from their solutions accelerates development.
- **Control**: Owning the backend ensures we can customize, scale, and pivot without external dependencies.
- **Compatibility**: Following Omi's device assumptions enables future hardware compatibility.

## System Components

### 1. Echo Mobile (Flutter)

The mobile application serves as the primary user interface and device coordinator.

```
apps/echo_mobile/
├── lib/
│   ├── config/          # App configuration
│   ├── models/          # Data models
│   ├── screens/         # UI screens
│   ├── services/        # API & device services
│   └── widgets/         # Reusable components
└── test/                # Widget & unit tests
```

**Responsibilities:**
- User interface and navigation
- Backend API communication
- BLE device management (Phase 3)
- Audio capture and streaming (Phase 1)
- Local state management

### 2. Echo Backend (FastAPI)

The backend provides API services, AI orchestration, and data persistence.

```
services/echo_backend/
├── app/
│   ├── main.py          # Application entry
│   ├── routers/         # API endpoints
│   ├── models/          # Pydantic schemas
│   └── services/        # Business logic
└── tests/               # API tests
```

**Responsibilities:**
- REST API for mobile app
- Chat/conversation processing
- Notes CRUD operations
- Future: LLM integration, action execution, memory management

### 3. Infrastructure

```
infra/
├── docker-compose.yml   # Local development stack
└── (future)             # Kubernetes, Terraform
```

## API Design

### Current Endpoints (Phase 0)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/healthz` | GET | Service health check |
| `/chat` | POST | Process chat messages |
| `/notes` | GET, POST | List/create notes |
| `/notes/{id}` | GET, DELETE | Get/delete note |

### Future Endpoints

- `/v1/transcribe` — WebSocket for real-time transcription
- `/v1/sessions` — Conversation session management
- `/v1/actions` — Action execution and status
- `/v1/memories` — Long-term memory retrieval

## Data Flow

### Chat Flow (Phase 0 - Stub)

```
Mobile App → POST /chat → Backend → Stub Response → Mobile App
```

### Chat Flow (Phase 1 - LLM)

```
Mobile App → POST /chat → Backend → LLM → Response + Actions → Mobile App
                                      ↓
                              Tool Execution
                              (notes, email, etc.)
```

### Audio Flow (Phase 1+)

```
Device/Mic → Mobile App → WebSocket → Backend → STT → LLM → Response
                                                 ↓
                                            Transcription
```

## Omi Reference Points

Key Omi components we study and adapt:

| Omi Component | Echo Adaptation |
|---------------|-----------------|
| `/backend/routers/transcribe.py` | WebSocket transcription endpoint |
| `/backend/routers/chat.py` | Chat with LangGraph orchestration |
| `/app/lib/services/` | Mobile service patterns |
| `/omi/firmware/` | BLE protocol understanding |

### Omi Architecture Insights

From [Omi's system architecture](https://deepwiki.com/basedhardware/omi/1.1-system-architecture):

- **Real-time transcription** via WebSocket with multiple STT service support
- **LangGraph** for chat processing and tool routing
- **Memory system** with vector search for context retrieval

## White-Label Architecture (Phase 2)

Echo is explicitly designed as a **white-label platform** to enable easy rebranding for multiple deployments.

### Branding Configuration Layer

**Mobile:** `apps/echo_mobile/lib/branding/branding_config.dart`
```dart
class BrandingConfig {
  static const String appName = 'Echo';
  static const int primaryColorValue = 0xFF000000;
  static const String logoAssetPath = 'assets/images/herologo.png';
  // ...
}
```

**Backend:** `services/echo_backend/app/config/branding.py`
```python
class BrandingConfig:
    PRODUCT_NAME = "Echo"
    API_TITLE = "Echo API"
    SUPPORT_EMAIL = "support@echo.example.com"
    # ...
```

### White-Label Customization Guide

To rebrand Echo for a new deployment:

1. **Update Configuration Files**
   - Modify `BrandingConfig` in both mobile and backend
   - Set product name, colors, support URLs

2. **Replace Assets**
   - Logo: `apps/echo_mobile/assets/images/herologo.png`
   - App icon: `apps/echo_mobile/assets/images/app_launcher_icon.png`
   - Other branded images as needed

3. **Update Platform Identifiers** (for app stores)
   - Android: `android/app/build.gradle`
     - `applicationId "com.yourcompany.yourapp"`
     - `resValue "string", "app_name", "Your App Name"`
   - iOS: `ios/Runner/Info.plist`
     - Bundle identifier
     - Display name

4. **Build and Test**
   ```bash
   # Mobile
   cd apps/echo_mobile
   flutter pub get
   flutter build apk  # or ios
   
   # Backend
   cd services/echo_backend
   # Verify branding in API docs at /docs
   ```

### Multi-Brand Deployment Strategy

For managing multiple brands:

1. **Option A: Flutter Flavors** (recommended for mobile)
   - Define flavors in `pubspec.yaml`
   - Create brand-specific config files
   - Build: `flutter build apk --flavor brand_a`

2. **Option B: Git Branches**
   - `main` branch: vanilla Echo
   - `brand-a`, `brand-b` branches: customized configs
   - Cherry-pick platform updates from main

3. **Option C: Configuration Service**
   - Load branding at runtime from API/Firebase
   - Suitable for multi-tenant SaaS deployments

## Phase Roadmap

### Phase 0 — Foundation ✅
- Monorepo structure
- FastAPI backend scaffold
- Flutter app scaffold
- CI/CD pipeline
- Documentation

### Phase 1 — Omi Import ✅
**Goal**: Ship fast by adopting Omi baseline

- Import Omi codebase to `vendor/`
- Rebrand Omi → Echo (names, IDs, strings)
- Configure CI for Flutter 3.27.0 stable
- Align dependencies for Dart 3.6.0
- FVM configuration for deterministic builds
- **Baseline tag:** `v0.1.0-white-label-base`

### Phase 2 — White-Label Productization 🚧 (Current)
**Goal**: Enable easy rebranding and customization

- Centralized branding configuration (mobile + backend)
- White-label documentation and guidelines
- Multi-brand deployment strategy
- Asset management system
- Theme abstraction layer

### Phase 3 — Production Hardening
**Goal**: Make Echo production-ready

- Firebase project setup
- API key configuration (OpenAI, Deepgram, etc.)
- Cloud deployment (Modal/GCP/AWS)
- End-to-end testing
- Performance optimization
- Monitoring and analytics

### Phase 4 — Feature Development
**Goal**: Enhance beyond Omi baseline

- Custom UI/UX improvements
- Additional integrations
- Enhanced privacy controls
- Custom analytics
- Platform-specific optimizations

## CI Configuration

CI runs on every push to `main` and on pull requests. All checks must pass.

### Backend Checks
- **Ruff**: Linting with pycodestyle, pyflakes, isort, bugbear rules
- **Mypy**: Strict type checking with Pydantic v2 plugin
- **Pytest**: Async test suite with per-test state isolation

### Mobile Checks
- **Flutter Analyze**: Dart static analysis
- **Flutter Test**: Widget tests with proper async handling

### Smoke Test
- Starts backend and validates `/healthz`, `/chat`, `/notes` endpoints

### Configuration Notes
- `pyproject.toml` contains mypy overrides for FastAPI/Starlette typing compatibility
- Test fixtures reset `NotesStore` between tests for isolation
- Widget tests use `TestWidgetsFlutterBinding.ensureInitialized()` and `pump()` for async handling

## Security Considerations

- No secrets in code or logs
- Environment-based configuration
- CORS properly configured for production
- API authentication (future: OAuth2/JWT)
- Encrypted data at rest (future)

## Scalability Path

1. **Phase 0-1**: Single instance, in-memory/SQLite
2. **Phase 2**: PostgreSQL, Redis caching
3. **Phase 3**: Kubernetes, horizontal scaling, CDN

---

*This document evolves with the project. Last updated: Phase 2 (White-Label Productization).*
