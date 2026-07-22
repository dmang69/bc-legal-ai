# Client packaging

**Strategy:** [`docs/PLATFORM_AND_INSTALLATION.md`](../docs/PLATFORM_AND_INSTALLATION.md)

| Path | Role |
|------|------|
| **`tauri/`** | **Primary** — Tauri 2 shell (Windows, macOS, Android, iOS) + shared UI |
| `desktop/` | Interim Python launcher / PyInstaller prototype only |
| `mobile/` | Legacy Capacitor notes — **do not expand**; use Tauri mobile |

Shared UI lives in `frontend/client/` (also served by FastAPI and as PWA).
