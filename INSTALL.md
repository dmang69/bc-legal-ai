# Install BC Legal AI Associate — all platforms

**Not a lawyer. Not legal advice.**  
Do not use public demos for confidential client files.

**Controlling strategy:** [`docs/PLATFORM_AND_INSTALLATION.md`](docs/PLATFORM_AND_INSTALLATION.md)  
**Primary shell:** **Tauri 2** + shared UI (`frontend/client`) → **private** backend.

---

## Five delivery methods

| Platform | Installation |
|----------|--------------|
| **Windows** | Signed **`.exe`** installer; optional **`.msi`** |
| **macOS** | Signed and notarized **`.dmg`** containing **`.app`** |
| **Android** | Google Play **`.aab`**; optional direct **`.apk`** |
| **iPhone / iPad** | App Store / TestFlight **`.ipa`** |
| **Browser** | Installable **Progressive Web App** |

```text
Shared UI (frontend/client)
        │
   Tauri 2 shell  ──or──  browser / PWA
        │
 Private BC Legal AI backend (FastAPI modular monolith)
```

---

## 1. Prerequisites

### Always

- Git  
- Private or local API (Python 3.11+) for backend work  

```bash
git clone https://github.com/dmang69/bc-legal-ai
cd bc-legal-ai
pip install fastapi "uvicorn[standard]" pydantic
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

### For Tauri 2 packages (recommended)

- Node.js **20+**  
- Rust (rustup)  
- Platform toolchains: WebView2 (Windows), Xcode (macOS/iOS), Android Studio (Android)  

Details: [`apps/tauri/README.md`](apps/tauri/README.md)

---

## 2. Browser / PWA (any OS)

1. Start the private API (above).  
2. Open `http://127.0.0.1:8000/`  
3. **Install:** browser menu → Install app / Add to Home Screen  

Uses `frontend/client/manifest.webmanifest`.  
PWA does **not** cache `/v1/*` API responses (confidentiality).

---

## 3. Tauri 2 — desktop (Windows / macOS)

```bash
cd apps/tauri
cp .env.example .env   # set ALA_API_BASE if needed
npm install
npm run tauri dev      # development
npm run tauri build    # release bundles
```

| Platform | Expected release artifacts |
|----------|----------------------------|
| Windows | NSIS **`.exe`** installer; enable **`.msi`** in `tauri.conf.json` when ready |
| macOS | **`.app`** + **`.dmg`** — sign and **notarize** before distribution |

Unsigned macOS: Right-click → Open (Gatekeeper).  
Piloted desktop builds are **prototype** only until Internal Alpha signing.

---

## 4. Tauri 2 — mobile (Android / iOS)

```bash
cd apps/tauri
npm install
# First time only (requires mobile SDKs):
npm run android:init
npm run ios:init

npm run android:dev    # or: npm run tauri android build → .aab / .apk
npm run ios:dev        # or: npm run tauri ios build → .ipa / TestFlight
```

| Platform | Store path |
|----------|------------|
| Android | Play Console internal testing → production **`.aab`** |
| iOS | TestFlight → App Store **`.ipa`** |

Do **not** accept real client files in store builds until M1/M2/M8 gates apply.

---

## 5. Interim Python desktop (fallback only)

When Node/Rust toolchains are unavailable:

| Platform | Method |
|----------|--------|
| Windows dev | `apps\desktop\install_windows_dev.ps1` or `python apps\desktop\launcher.py` |
| Windows `.exe` (prototype) | `apps\desktop\build_windows.ps1` → PyInstaller |
| macOS dev | `apps/desktop/install_macos_dev.sh` |
| macOS `.app` (prototype) | `apps/desktop/build_macos.sh` |

This path is **not** the long-term store packaging strategy. Prefer Tauri 2.

---

## 6. API only

```bash
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
# UI  http://127.0.0.1:8000/
# API http://127.0.0.1:8000/docs
```

---

## 7. Architecture (delivery)

```text
Windows .exe / macOS .dmg / Android .aab / iOS .ipa / Browser PWA
              │  HTTPS or loopback HTTP (dev)
              ▼
     FastAPI  backend.api.main   (modular monolith)
     · frontend/client (shared UI)
     · /v1 HITL + post-resolution (+ future modules)
```

Native extras (approved-folder connector, biometrics) attach **only** in the Tauri shell with least privilege — see `architecture/WINDOWS_CONNECTOR_BOUNDARY.md`.

---

## Security

- Default bind is loopback for local prototype; production needs TLS + MFA + matter ACL.  
- Public Space / `APP_MODE=public_demo` = synthetic only.  
- See `SECURITY.md` and the Phase 4 controlling program.
