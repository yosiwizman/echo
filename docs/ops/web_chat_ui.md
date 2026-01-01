# Web Chat UI Operations Guide

The Echo Web Chat UI is a React-based web application that provides a browser-based chat interface to interact with the Echo backend.

## Deployment URLs

After deployment, the Web Chat UI is available at:

- **Staging**: `https://echo-web-staging-<hash>-ew.a.run.app` (deployed on push to main)
- **Production**: `https://echo-web-<hash>-ew.a.run.app` (deployed on `web-prod-v*` tag)

> Note: The actual URLs are determined by Cloud Run after deployment. Check the GitHub Actions workflow output or Cloud Run console for the exact URLs.

## Features

### Environment Selector
Toggle between **Staging** and **Production** backends using the dropdown in the header. This switches which backend URL the chat requests are sent to.

### Streaming Mode
Toggle streaming on/off using the checkbox:
- **Streaming ON**: Uses `/v1/brain/chat/stream` endpoint, renders tokens as they arrive
- **Streaming OFF**: Uses `/v1/brain/chat` endpoint, waits for complete response

### Connectivity Indicator
Shows the connection status to the selected backend:
- **Green**: Connected (health check passed)
- **Yellow**: Checking...
- **Red**: Disconnected (health check failed)

Click the indicator to manually refresh the health check.

### Debug Panel
Click "Show debug" on any assistant message to see runtime metadata:
- `trace_id`: Request trace identifier
- `provider`: AI provider used (e.g., "mock", "openai")
- `env`: Backend environment
- `git_sha`: Backend deployment commit
- `build_time`: Backend build timestamp

### Chat Persistence
Messages are stored in localStorage and persist across page refreshes. Click "Clear" to reset the conversation.

## Deployment

### Staging Deployment
Automatic deployment on push to `main` when `apps/web/**` files change:

```
.github/workflows/web_deploy_staging.yml
```

Manual trigger:
```bash
gh workflow run web_deploy_staging.yml --repo yosiwizman/echo
```

### Production Deployment
Deploy to production by creating a version tag:

```bash
git tag web-prod-v1.0.0
git push origin web-prod-v1.0.0
```

This triggers `.github/workflows/web_deploy_prod.yml`.

## Architecture

### Stack
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **Styling**: TailwindCSS
- **Container**: nginx:alpine (multi-stage Docker build)
- **Hosting**: Cloud Run (europe-west1)

### Directory Structure
```
apps/web/
├── src/
│   ├── components/     # React components
│   ├── hooks/          # Custom React hooks
│   ├── utils/          # Utility functions
│   ├── types/          # TypeScript types
│   ├── config.ts       # Backend URLs
│   └── App.tsx         # Main app component
├── Dockerfile          # Multi-stage build
├── nginx.conf          # SPA routing config
└── package.json
```

### Backend Configuration
Backend URLs are hardcoded in `apps/web/src/config.ts`:

```typescript
export const BACKEND_URLS = {
  staging: 'https://echo-backend-staging-zxuvsjb5qa-ew.a.run.app',
  production: 'https://echo-backend-zxuvsjb5qa-ew.a.run.app',
} as const;
```

The UI toggle switches between these at runtime.

## Monitoring

### Runtime Smoke Checks
The Web UI is included in the runtime smoke monitoring workflow. After deployment, set these GitHub Actions variables:

- `WEB_STAGING_BASE_URL`: Staging web URL (e.g., `https://echo-web-staging-xxx-ew.a.run.app`)
- `WEB_PROD_BASE_URL`: Production web URL (e.g., `https://echo-web-xxx-ew.a.run.app`)

The smoke monitor runs every 15 minutes and validates HTTP 200 from the web URLs.

### Health Check
The nginx configuration provides a `/health` endpoint that returns `{"status":"ok"}`.

## Troubleshooting

### CORS Issues
The Web UI makes direct requests to Cloud Run backends. Cloud Run services are configured to allow unauthenticated requests, and CORS should work out of the box since both frontend and backend are on `*.run.app` domains.

If you encounter CORS errors:
1. Verify the backend service allows unauthenticated access
2. Check the backend CORS middleware configuration
3. Try clearing browser cache and cookies

### Connection Errors
If the connectivity indicator shows "Disconnected":
1. Click the indicator to retry the health check
2. Verify the correct environment is selected
3. Check if the backend service is running in Cloud Run console
4. Try opening the backend URL directly in a new tab

### Build Failures
Check the GitHub Actions workflow logs:
- **Lint errors**: Run `npm run lint` locally to see issues
- **Type errors**: Run `npm run typecheck` locally
- **Test failures**: Run `npm run test` locally

### Local Development
```bash
cd apps/web
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

Note: Local development will make requests to the hardcoded backend URLs. To test against a local backend, temporarily modify `config.ts`.
