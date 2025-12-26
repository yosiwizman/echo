# Echo Architecture

## Overview

Echo is an AI-powered wearable companion designed for real-time voice interaction, intelligent note-taking, and automated action execution. This document outlines the system architecture and strategic decisions.

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

## Phase Roadmap

### Phase 0 — Foundation ✅
- Monorepo structure
- FastAPI backend scaffold
- Flutter app scaffold
- CI/CD pipeline
- Documentation

### Phase 1 — Session Mode
**Goal**: Real-time voice interaction

- Audio capture in Flutter
- WebSocket streaming to backend
- STT integration (Whisper/Deepgram)
- Live transcription display
- Basic LLM chat integration

### Phase 2 — Sleep Phrase & VAD
**Goal**: Ambient listening with wake word

- Wake word detection ("Hey Echo")
- Voice Activity Detection (VAD)
- Background listening mode
- Battery-optimized audio processing

### Phase 3 — BLE & Wearable
**Goal**: Hardware device support

- BLE service implementation
- Omi-compatible device pairing
- Hardware button handling
- Firmware communication protocol

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

*This document evolves with the project. Last updated: Phase 0.*
