# Echo

**Echo** is an AI-powered wearable companion that listens, understands, and acts on your behalf. Built with a Flutter mobile app and a FastAPI backend, Echo is designed for real-time voice interaction with intelligent note-taking and action execution.

## Strategy

Echo follows the **B2 (Best Practice)** strategy:
- We build on the [Omi](https://github.com/BasedHardware/omi) open-source ecosystem for proven patterns and device assumptions
- We own our backend from day 1 — no dependency on external hosted services
- We leverage Omi's architecture as a reference while maintaining full control

## Repository Structure

```
echo/
├── apps/
│   └── echo_mobile/          # Flutter mobile application
├── services/
│   └── echo_backend/         # FastAPI backend service
├── infra/                    # Docker, scripts, deployment configs
├── docs/                     # Architecture and roadmap documentation
└── .github/
    └── workflows/            # CI/CD pipelines
```

## Quick Start

### Prerequisites

- **Backend**: Python 3.12+, Docker (optional)
- **Mobile**: Flutter 3.x, Dart SDK

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
- FastAPI backend with health, chat, and notes APIs
- Flutter app scaffold with navigation
- CI/CD pipeline
- Documentation

### Phase 1 — Session Mode
- Real-time audio streaming
- Speech-to-text integration
- Live transcription display
- Basic conversation memory

### Phase 2 — Sleep Phrase & VAD
- Wake word detection ("Hey Echo")
- Voice Activity Detection (VAD)
- Ambient listening mode
- Battery optimization

### Phase 3 — BLE & Wearable
- Bluetooth Low Energy integration
- Omi-compatible device support
- Hardware button actions
- Persistent background service

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Echo: Your AI companion that listens and acts.*
