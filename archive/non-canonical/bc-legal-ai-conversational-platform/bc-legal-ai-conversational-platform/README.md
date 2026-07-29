# BC Legal AI Associate — Conversational Platform Scaffold

This scaffold is the first implementation layer for the cross-platform conversational legal AI workspace.

## Included

- React + TypeScript + Vite conversational interface
- Matter-scoped chat header and privacy indicators
- Chat history sidebar
- Fast / Balanced / Deep Analysis / Private Local modes
- Specialist-agent selector
- File attachment queue with public-demo restrictions
- Sources, evidence, draft, timeline, and agent side panels
- Mock streaming AI responses for frontend development
- Tauri 2 desktop/mobile wrapper configuration
- Windows, macOS, Android, iOS configuration overlays
- GitHub Actions checks and unsigned development-build workflows

## Important status

This is an interface scaffold, not a production legal system. It does not yet provide:

- production authentication or matter isolation;
- real document ingestion or OCR;
- official legal retrieval;
- actual AI inference;
- citation verification;
- signed installers;
- App Store or Play Store releases.

The default application mode is `public_demo`, which rejects real legal file numbers and warns against confidential uploads.

## Development

Requirements:

- Node.js 20 or newer
- Rust and Cargo
- Tauri platform prerequisites

```bash
cd apps/platform-ui
npm install
npm run dev
```

## Desktop development

```bash
cd apps/platform-ui
npm install
npm run tauri:dev
```

## Production web build

```bash
cd apps/platform-ui
npm run build
```

## Windows/macOS desktop build

```bash
cd apps/platform-ui
npm run tauri:build
```

## Android initialization and build

```bash
cd apps/platform-ui
npm run tauri:android:init
npm run tauri:android:dev
npm run tauri:android:build
```

## iOS initialization and build

Requires macOS and Xcode.

```bash
cd apps/platform-ui
npm run tauri:ios:init
npm run tauri:ios:dev
npm run tauri:ios:build
```

## Backend integration

Set:

```bash
VITE_API_BASE_URL=https://your-private-api.example
VITE_APP_MODE=private
```

Until a private API is available, the interface runs in mock mode.
