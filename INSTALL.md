# Install BC Legal AI Associate — all platforms

**Not a lawyer. Not legal advice.**  
Do **not** put confidential client files on public demos. Real matters need a **private API**.

| Doc | Purpose |
|-----|---------|
| This file | End-user & builder install steps |
| [docs/INSTALLABLE_CLIENT_STATUS.md](docs/INSTALLABLE_CLIENT_STATUS.md) | Source vs signed binary status |
| [docs/SIGNING_AND_DISTRIBUTION.md](docs/SIGNING_AND_DISTRIBUTION.md) | Code signing / stores |
| [docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md](docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md) | Architecture |

---

## Status at a glance

| Platform | How you install | Artifact | Published store binary? |
|----------|-----------------|----------|-------------------------|
| **Windows** | Setup wizard / MSI / portable | `.exe` (NSIS), optional `.msi` | Build from source · **not** signed store release yet |
| **macOS** | DMG → Applications | `.dmg` / `.app` | Build on Mac · notarize before share |
| **Linux** | AppImage / deb (Tauri) or Docker / browser | bundle / Docker | Build from source |
| **Android** | Play / sideload APK | `.aab` (Play), `.apk` (test) | Build with Android SDK |
| **iPhone / iPad** | TestFlight / App Store | `.ipa` | Build on Mac + Xcode |
| **Google Chrome** | Installable **PWA** (Portal) | `manifest.webmanifest` | Host UI on **HTTPS** |
| **Public demo** | No install | HF Space | https://huggingface.co/spaces/Dmang69/bc-legal-ai |

```text
                 ┌─────────────────────────────────────┐
                 │  Clients                            │
                 │  Windows.exe · macOS.app · Linux    │
                 │  Android · iOS · Chrome PWA         │
                 └──────────────────┬──────────────────┘
                                    │ HTTPS
                 ┌──────────────────▼──────────────────┐
                 │  Private FastAPI backend            │
                 │  (Docker / uvicorn / cloud)         │
                 └─────────────────────────────────────┘
```

Every installed client still needs a **reachable private API** (`VITE_API_BASE_URL`).  
Public Spaces are **synthetic-only** and do not replace that backend.

---

## 0. Private API (required for real work)

### Option A — Docker (any OS with Docker)

```bash
docker run --rm -p 8000:8000 \
  -e APP_MODE=development \
  -e ALA_ALLOW_EXTERNAL_LLM=0 \
  ghcr.io/dmang69/bc-legal-ai:latest
```

Health: http://127.0.0.1:8000/health · Docs: http://127.0.0.1:8000/docs

### Option B — Python from source

```bash
git clone https://github.com/dmang69/bc-legal-ai.git
cd bc-legal-ai
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev,export,pdf]"
cp .env.example .env
# APP_MODE=development
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Option C — Windows one-click starters (dev)

From repo root (API + UI in separate windows):

```text
START-API.cmd
START-UI.cmd
START-BOTH.cmd
```

Or PowerShell: `scripts\start-api.ps1` · `scripts\start-ui.ps1`

---

## 1. Google Chrome / Edge / desktop browser (PWA Portal)

**Fastest “install”** — no store, no native toolchain.

### Run locally

```bash
cd apps/platform-ui
npm ci
# optional: create .env with
#   VITE_API_BASE_URL=http://127.0.0.1:8000
#   VITE_APP_MODE=portal
npm run dev
```

Open **http://127.0.0.1:1420** (Vite default for this app).

### Production build

```bash
cd apps/platform-ui
set VITE_API_BASE_URL=https://api.example.com   # Windows
# export VITE_API_BASE_URL=https://api.example.com  # macOS/Linux
npm run build
# serve dist/ behind HTTPS (required for install prompt)
```

### Install as app (Chrome / Edge)

1. Host `apps/platform-ui/dist` on **HTTPS** (or localhost).  
2. Chrome → **⋯** → **Cast, save and share** → **Install page as app…**  
   (or install icon in the address bar when available)  
3. Edge → **⋯** → **Apps** → **Install this site as an app**  

**Manifest:** `apps/platform-ui/public/manifest.webmanifest`  
**Icons:** `public/icons/icon-192.png`, `icon-512.png`

> Chrome only offers install when the page is served securely and the web app manifest is linked (already in `index.html`).

---

## 2. Windows — `.exe` setup installer (Workbench)

**Recommended packaging:** Tauri 2 → NSIS **Setup `.exe`** (+ optional MSI).

### Prerequisites

| Tool | Notes |
|------|--------|
| Node.js **20+** | https://nodejs.org |
| Rust (rustup) | https://rustup.rs |
| WebView2 | Usually preinstalled on Windows 10/11 |
| Visual Studio C++ Build Tools | “Desktop development with C++” |
| Backend | Running at `http://127.0.0.1:8000` or set `VITE_API_BASE_URL` |

### Build unsigned installer (one script)

From **repo root** in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1
```

**Outputs:**

```text
releases\windows\
  *.exe          # NSIS setup (name depends on Tauri productName)
  *.msi          # if WiX/MSI target produced
  checksums.txt  # SHA-256
```

Also under:

```text
apps\desktop-mobile\src-tauri\target\release\bundle\
  nsis\*.exe
  msi\*.msi
```

### Manual Tauri build

```powershell
cd apps\platform-ui
$env:VITE_APP_MODE = "workbench"
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm ci
npm run build

cd ..\desktop-mobile
npm ci
npx tauri build --config src-tauri/tauri.windows.conf.json
```

### Sign before public distribution

```powershell
# Requires org Authenticode cert — see docs/SIGNING_AND_DISTRIBUTION.md
powershell -ExecutionPolicy Bypass -File scripts\sign_windows_installer.ps1
```

**Do not ship unsigned `.exe` to production users.**

### Alternate: portable PyInstaller `.exe` (API + UI shell)

```powershell
powershell -ExecutionPolicy Bypass -File apps\desktop\build_windows.ps1
# → dist\BCLegalAIAssociate.exe  (loopback server + webview)
```

Prefer **Tauri Workbench** for store-style packaging.

### Install on a Windows PC (end user)

1. Download signed `BC-Legal-AI-Associate-Setup-x64.exe` from **GitHub Releases** (when published).  
2. Run the setup wizard (UAC prompt).  
3. Launch **BC Legal AI Associate**.  
4. Confirm API URL (default loopback or org-provided HTTPS).  
5. Sign in / register synthetic org for pilot.

---

## 3. macOS — `.dmg` / `.app`

### Prerequisites

- macOS 12+  
- Node 20+, Rust, Xcode Command Line Tools  
- For notarized public builds: Apple Developer ID  

### Build (Tauri)

```bash
cd apps/platform-ui
export VITE_APP_MODE=workbench
export VITE_API_BASE_URL=http://127.0.0.1:8000
npm ci && npm run build

cd ../desktop-mobile
npm ci
npx tauri build --config src-tauri/tauri.macos.conf.json
```

**Artifacts:** `apps/desktop-mobile/src-tauri/target/release/bundle/dmg/*.dmg`  
and/or `macos/*.app`

### Alternate PyInstaller app

```bash
chmod +x apps/desktop/build_macos.sh
./apps/desktop/build_macos.sh
# → dist/BC Legal AI Associate.app
```

### End-user install

1. Open the `.dmg`  
2. Drag **BC Legal AI Associate** to **Applications**  
3. First open: System Settings → Privacy if Gatekeeper blocks unsigned builds  
4. Point at private API URL  

**Notarize** before external distribution (`docs/SIGNING_AND_DISTRIBUTION.md`).

---

## 4. Linux — desktop / server

### Browser / PWA (all distros)

Same as Chrome section: host Portal on HTTPS or use `npm run dev` / Docker API + UI.

### Docker (server + browser clients)

```bash
docker compose up --build
# or GHCR image for API only
```

### Tauri desktop (AppImage / deb)

```bash
# On Linux host with webkit2gtk, rsvg, etc. — see Tauri Linux prereqs
cd apps/platform-ui && npm ci && npm run build
cd ../desktop-mobile && npm ci
npx tauri build
# bundle under src-tauri/target/release/bundle/
```

### Dev from source

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,export,pdf]"
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
# other terminal
cd apps/platform-ui && npm ci && npm run dev
```

---

## 5. Android — Google Play / APK

### Prerequisites

- Android Studio + SDK  
- JDK 17+  
- Node 20+, Rust with Android targets  
- First time: `cd apps/desktop-mobile && npm run android:init`

### Dev

```bash
# API reachable from device/emulator (not 127.0.0.1 from phone —
# use LAN IP or tunnel, e.g. http://192.168.x.x:8000)
cd apps/platform-ui
export VITE_APP_MODE=client
export VITE_API_BASE_URL=https://api.example.com
npm ci && npm run build

cd ../desktop-mobile
npm ci
npm run android:dev
```

### Release build

```bash
cd apps/desktop-mobile
npx tauri android build
# → .aab for Play Console · .apk for internal testing
```

| Artifact | Channel |
|----------|---------|
| **`.aab`** | Google Play (closed testing → production) |
| **`.apk`** | Sideload / internal QA only |

Mobile V1 focus: messaging, capture, consent, tasks, timelines — **not** on-device OCR or full legal engines.

---

## 6. iPhone / iPad — TestFlight / App Store

### Prerequisites

- **Mac** with Xcode  
- Apple Developer Program  
- First time: `cd apps/desktop-mobile && npm run ios:init`

### Dev

```bash
cd apps/platform-ui
export VITE_APP_MODE=client
export VITE_API_BASE_URL=https://api.example.com
npm ci && npm run build

cd ../desktop-mobile
npm run ios:dev
```

### Release

```bash
cd apps/desktop-mobile
npx tauri ios build
# Archive → upload → TestFlight → App Store
```

| Artifact | Channel |
|----------|---------|
| **`.ipa`** | TestFlight → App Store |

Cannot produce iOS installers on Windows-only hosts.

---

## 7. Application modes (`VITE_APP_MODE`)

| Value | Surface | Typical clients |
|-------|---------|-----------------|
| `workbench` | Lawyer Workbench | Windows / macOS Tauri |
| `client` | Client Application | Android / iOS |
| `portal` | Web Portal / PWA | Chrome, Edge, Safari |
| `private` | Authenticated private UI | Platform UI default dev |
| `public_demo` | Synthetic-only | Public demos |

---

## 8. Intended GitHub Release layout

When signed builds are published:

```text
GitHub Releases (example)
├── BC-Legal-AI-Associate-Setup-x64.exe   # Windows NSIS
├── BC-Legal-AI-Associate-x64.msi         # Windows MSI
├── BC-Legal-AI-Associate-universal.dmg   # macOS
├── BC-Legal-AI-Associate.AppImage        # Linux (if built)
├── BC-Legal-AI-Associate.apk             # Android QA only
├── checksums.txt
└── release-notes.md
```

- Production Android → **Play `.aab`** (not a public APK store)  
- iPhone → **TestFlight / App Store** only  

---

## 9. Security & legal locks

- Installers contain **no** client data or production secrets  
- External LLMs stay gated (`ALA_ALLOW_EXTERNAL_LLM=0` by default)  
- Public demos: synthetic only · `court_ready` fail-closed  
- Sign Windows (Authenticode) and notarize macOS before wide distribution  
- See [SECURITY.md](SECURITY.md) and [docs/VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md)

---

## 10. Quick matrix — what to run today

| You want… | Do this |
|-----------|---------|
| Try without install | https://huggingface.co/spaces/Dmang69/bc-legal-ai |
| Chrome “app” | Build Portal → HTTPS → Chrome **Install page as app** |
| Windows Setup.exe | `scripts\build_windows_installer.ps1` |
| macOS .app/.dmg | Tauri build on a Mac |
| Linux server | Docker / compose |
| Android test | Tauri `android:dev` / `android build` |
| iPhone test | Tauri `ios:dev` on Mac → TestFlight |
| Full API + UI dev | `START-BOTH.cmd` or uvicorn + `npm run dev` |

---

## Support paths

| Issue | Where |
|-------|--------|
| API / Docker | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/GHCR.md](docs/GHCR.md) |
| Env vars | [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md), `.env.example` |
| Signing | [docs/SIGNING_AND_DISTRIBUTION.md](docs/SIGNING_AND_DISTRIBUTION.md) |
| Verification | [docs/VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md) |
| Issues | https://github.com/dmang69/bc-legal-ai/issues |
