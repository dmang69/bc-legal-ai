# Install BC Legal AI Associate — all platforms

**Not a lawyer. Not legal advice.**  
Do not use public demos for confidential client files.

**Controlling architecture:** [`docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`](docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md)

| Product surface | Name |
|-----------------|------|
| Family | BC Legal AI Associate |
| Desktop | **BC Legal AI Workbench** |
| Mobile | **BC Legal AI Client** |
| Web | **BC Legal AI Portal** |

---

## Five delivery methods

| Platform | Installation |
|----------|--------------|
| **Windows** | Signed **`.exe`** setup; optional **`.msi`** / later **`.msix`** |
| **macOS** | Signed + notarized **`.dmg`** (`.app`) |
| **Android** | Google Play **`.aab`**; optional test **`.apk`** |
| **iPhone / iPad** | App Store / TestFlight **`.ipa`** |
| **Browser** | Installable **PWA** (Portal) |

```text
React UI (apps/platform-ui)
        │
   Tauri 2 (apps/desktop-mobile)  ──or──  Portal / PWA
        │
 Private FastAPI modular monolith
```

---

## 1. Prerequisites

### Backend (always for real work)

```bash
git clone https://github.com/dmang69/bc-legal-ai
cd bc-legal-ai
pip install fastapi "uvicorn[standard]" pydantic
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

### Shared UI + Tauri (recommended)

- Node.js **20+**
- Rust (rustup)
- Platform SDKs: WebView2 (Windows), Xcode (macOS/iOS), Android Studio (Android)

---

## 2. Web portal / PWA (fastest)

```bash
cd apps/platform-ui
cp .env.example .env
# VITE_API_BASE_URL=http://127.0.0.1:8000
# VITE_APP_MODE=portal
npm install
npm run dev
# open http://127.0.0.1:5173 → Install / Add to Home Screen when hosted on HTTPS
```

Production: `npm run build` → deploy `dist/` behind TLS.

**Interim:** static shell at `frontend/client` still served by FastAPI on port 8000.

---

## 3. Desktop Workbench (Tauri — Windows / macOS)

```bash
# backend running on :8000
cd apps/platform-ui && npm install
cd ../desktop-mobile && npm install
npm run tauri dev
```

Unsigned release build:

```bash
cd apps/desktop-mobile
npm run tauri build
```

| Platform | Target names (Section G) |
|----------|---------------------------|
| Windows | `BC-Legal-AI-Associate-Setup-x64.exe`, optional MSI |
| macOS | `BC-Legal-AI-Associate-universal.dmg` |

Sign / notarize before alpha distribution.

---

## 4. Mobile Client (Tauri Android / iOS)

```bash
cd apps/desktop-mobile
npm run android:init   # first time
npm run ios:init       # first time, macOS only
npm run android:dev    # Client-focused features
npm run ios:dev
```

| Artifact | Channel |
|----------|---------|
| `.aab` | Google Play closed beta → production |
| `.ipa` | TestFlight → App Store |

Mobile V1 focus: messaging, capture, consent, tasks, timelines — **not** on-device OCR/legal engines.

---

## 5. Application modes

| `VITE_APP_MODE` | Surface |
|-----------------|---------|
| `workbench` | Lawyer Workbench |
| `client` | Client Application |
| `self_rep` | Self-represented Workbench |
| `portal` | Web Portal / PWA |

---

## 6. Interim Python desktop (fallback)

```text
python apps/desktop/launcher.py
```

Not the store packaging path. Prefer Tauri Workbench.

---

## 7. Security

- Installers contain **no** client data or production secrets  
- Offline mode is limited (Section G §13)  
- Windows folder access is **approved-folder only**  
- Real matters only after M1 isolation + M2 quarantine  
- See `SECURITY.md` and Phase 4 controlling program  
