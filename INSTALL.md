# Install BC Legal AI Associate — all platforms

**Not a lawyer. Not legal advice.**  
Do not use public demos for confidential client files.

| Platform | Method | How |
|----------|--------|-----|
| **Windows** | Dev | `apps\desktop\install_windows_dev.ps1` or `python apps\desktop\launcher.py` |
| **Windows** | **`.exe`** | `apps\desktop\build_windows.ps1` → `dist\BCLegalAIAssociate.exe` |
| **macOS** | Dev | `apps/desktop/install_macos_dev.sh` or `python3 apps/desktop/launcher.py` |
| **macOS** | **`.app`** | `apps/desktop/build_macos.sh` → `dist/BC Legal AI Associate.app` |
| **iPhone** | **PWA** | Safari → Share → Add to Home Screen (open LAN/private URL) |
| **Android** | **PWA** | Chrome → Install app / Add to Home Screen |
| **Android / iOS** | Native shell | Capacitor project in `apps/mobile/` (see README there) |
| **Any OS** | Browser + API | `uvicorn backend.api.main:app --port 8765` |
| **Hugging Face** | Static landing | Free tier; Gradio needs HF PRO |

---

## 1. Prerequisites

- Python **3.11+**
- Git

```bash
git clone https://github.com/dmang69/bc-legal-ai
cd bc-legal-ai
pip install fastapi "uvicorn[standard]" pydantic pywebview
```

---

## 2. Windows

### Developer shortcut

```powershell
powershell -ExecutionPolicy Bypass -File apps\desktop\install_windows_dev.ps1
# or
python apps\desktop\launcher.py
```

### Build `.exe`

```powershell
powershell -ExecutionPolicy Bypass -File apps\desktop\build_windows.ps1
```

Output: `dist\BCLegalAIAssociate.exe`  
Double-click → local server on **127.0.0.1** + window/browser UI.

---

## 3. macOS

```bash
chmod +x apps/desktop/install_macos_dev.sh apps/desktop/build_macos.sh
./apps/desktop/install_macos_dev.sh
# or
python3 apps/desktop/launcher.py
```

### Build `.app`

```bash
./apps/desktop/build_macos.sh
```

Output: `dist/BC Legal AI Associate.app`  
Unsigned: Right-click → Open (Gatekeeper).

---

## 4. iPhone

1. Start the app on a PC/Mac on the same Wi‑Fi (`launcher.py` — may need `--host 0.0.0.0` for LAN; use only on trusted networks).
2. Open Safari to `http://<computer-ip>:8765/`.
3. Share → **Add to Home Screen**.

Uses PWA (`frontend/client/manifest.webmanifest`).

Native: `apps/mobile/README.md` (Capacitor + Xcode).

---

## 5. Android

1. Same PWA flow in Chrome → **Install app**.
2. Or Capacitor + Android Studio: `apps/mobile/README.md`.

---

## 6. API only

```bash
uvicorn backend.api.main:app --host 127.0.0.1 --port 8765
# UI  http://127.0.0.1:8765/
# API http://127.0.0.1:8765/docs
```

---

## 7. Architecture

```text
Windows .exe / macOS .app / Phone PWA / Browser
              │  HTTP (default 127.0.0.1)
              ▼
     FastAPI  backend.api.main
     · frontend/client (PWA)
     · /v1 HITL + post-resolution
```

## Security

- Default bind is loopback; do not expose without TLS + MFA.
- PWA does not cache `/v1/*` API responses.
- See `SECURITY.md`.
