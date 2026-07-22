# desktop-mobile — Tauri 2 shell

**Section G** packaging for:

| Surface | Name |
|---------|------|
| Desktop | BC Legal AI Workbench |
| Mobile | BC Legal AI Client |

Shared UI: [`../platform-ui`](../platform-ui) (React · TypeScript · Vite)  
Controlling docs: [`docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`](../../docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md)

## Develop

```bash
# Terminal 1 — private backend
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — UI + Tauri
cd apps/platform-ui && npm install && cd ../desktop-mobile && npm install
npm run tauri dev
```

`beforeDevCommand` starts Vite on port **5173**; Tauri loads it. API base defaults to `http://127.0.0.1:8000` via `VITE_API_BASE_URL`.

## Build (unsigned development)

```bash
cd apps/desktop-mobile
npm run tauri build
```

Windows NSIS / MSI targets are enabled in `tauri.windows.conf.json`.  
Sign and notarize before alpha distribution.

## Platform configs

| File | Role |
|------|------|
| `src-tauri/tauri.conf.json` | Base |
| `src-tauri/tauri.windows.conf.json` | Workbench naming, NSIS+MSI |
| `src-tauri/tauri.macos.conf.json` | DMG, hardened runtime |
| `src-tauri/tauri.android.conf.json` | Client naming |
| `src-tauri/tauri.ios.conf.json` | Client naming |

## Security

- No client matter data in the installer  
- Approved-folder connector only (not whole-drive)  
- Offline mode limited; see Section G §13  
