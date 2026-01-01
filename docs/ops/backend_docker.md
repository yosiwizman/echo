# Backend Docker Image

The Echo backend is published to GitHub Container Registry (GHCR) on every push to `main` and on version tags.

## Image Location

```
ghcr.io/yosiwizman/echo-backend
```

## Tags

| Tag Pattern | When Published | Example |
|-------------|----------------|---------|
| `sha-<shortsha>` | Every push to main | `sha-a933222` |
| `latest` | Push to main | `latest` |
| `<version>` | Version tags (v*.*.*) | `1.0.0` |
| `<major>.<minor>` | Version tags | `1.0` |

## Quick Start

### Pull the image

```bash
docker pull ghcr.io/yosiwizman/echo-backend:latest
```

### Run locally

```bash
docker run -p 8000:8000 \
  -e ECHO_ENV=development \
  ghcr.io/yosiwizman/echo-backend:latest
```

### With environment file

```bash
# Copy and configure environment
cp services/echo_backend/.env.template .env
# Edit .env with your values

docker run -p 8000:8000 \
  --env-file .env \
  ghcr.io/yosiwizman/echo-backend:latest
```

## Configuration

The image requires environment variables for full functionality. See `services/echo_backend/.env.template` for all available options.

**Key variables:**
- `OPENAI_API_KEY` - Required for AI features
- `FIREBASE_*` / `SERVICE_ACCOUNT_JSON` - Authentication
- `REDIS_DB_*` - Session/cache storage
- `PINECONE_*` - Vector search

**Note:** Secrets are NOT baked into the image. You must provide them at runtime.

## Using docker-compose

A development compose file is available:

```bash
cd infra
docker-compose up echo-backend
```

## Build Locally

```bash
cd services/echo_backend
docker build -t echo-backend:local .
```

## CI/CD Workflow

The image is built by `.github/workflows/backend_ghcr.yml`:
- **PRs**: Build only (validates Dockerfile)
- **main**: Build + push with `sha-*` and `latest` tags
- **Tags (v*.*.*)**: Build + push with version tags

This workflow is separate from the main CI checks and does not affect branch protection.
