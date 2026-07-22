# Tauri 2 shell — BC Legal AI Associate

**Primary packaging path** for Windows, macOS, Android, and iOS.  
Shared UI: `../../frontend/client`  
Private API: configurable backend (not bundled weights / not public demo for real matters).

See **[docs/PLATFORM_AND_INSTALLATION.md](../../docs/PLATFORM_AND_INSTALLATION.md)**.

## Prerequisites

| Tool | Notes |
|------|--------|
| Node.js 20+ | `npm` / `pnpm` |
| Rust stable | [rustup](https://rustup.rs) |
| Tauri CLI 2 | `npm i -g @tauri-apps/cli@^2` or project local |
| **Windows** | WebView2 (usually preinstalled on Win10/11) |
| **macOS** | Xcode Command Line Tools; full Xcode for iOS |
| **Android** | Android Studio, SDK, NDK (Tauri mobile docs) |
| **iOS** | Xcode, Apple Developer account for device/TestFlight |

## Configuration

1. Copy `.env.example` → `.env` and set API base to your **private** backend.
2. `src-tauri/tauri.conf.json` — product name, identifiers, windows.
3. Platform permissions stay **minimal**; file dialogs only for approved-folder flows (M6).

## Develop (desktop)

From repo root or this directory:

```bash
cd apps/tauri
npm install
npm run tauri dev
```

Default: load static UI from `frontend/client` and call API at `http://127.0.0.1:8000` (start backend separately):

```bash
# another terminal, repo root
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

## Build artifacts

| Platform | Command (from `apps/tauri`) | Output (typical) |
|----------|----------------------------|------------------|
| Windows | `npm run tauri build` | `src-tauri/target/release/bundle/nsis/*.exe` or MSI |
| macOS | `npm run tauri build` | `bundle/dmg/*.dmg` + `.app` |
| Android | `npm run tauri android build` | `.aab` / `.apk` |
| iOS | `npm run tauri ios build` | `.ipa` (Xcode / CI) |

Exact bundle paths depend on Tauri version and `tauri.conf.json` `bundle` targets. Prefer **signed** builds only for Internal Alpha+.

## Security notes

- Do not point production shells at public Hugging Face Spaces for client data.
- Do not enable broad filesystem plugins without the approved-folder gate.
- `APP_MODE=public_demo` on the server rejects confidential workflows.

## Interim fallback

If the Tauri toolchain is not installed, use:

```text
python apps/desktop/launcher.py
# or apps/desktop/build_windows.ps1  (PyInstaller prototype only)
```

That path is **not** the long-term store packaging strategy.
