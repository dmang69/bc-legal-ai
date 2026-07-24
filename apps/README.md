# Applications and packaging (Section G)

| Path | Role |
|------|------|
| **`platform-ui/`** | Shared **React · TypeScript · Vite** UI (target workbench; optional for API chat) |
| **`desktop-mobile/`** | **Tauri 2** shell — Workbench (desktop) / Client (mobile) |
| **`pwa/`** | Portal packaging notes |
| `desktop/` | Interim Python launcher only |
| `tauri/` | Redirect → `desktop-mobile` |
| `mobile/` | Legacy Capacitor notes — do not expand |
| `api/`, `web/` | **Not canonical** for BC Legal AI — EAP sample trees; see `docs/CANONICAL_STACK.md` |

**Product chat API lives in** [`../backend/`](../backend/) (uvicorn `backend.api.main:app`), not `apps/api`.

Shared packages: [`../packages/README.md`](../packages/README.md)  
Strategy: [`../docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`](../docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md)  
Canonical stack: [`../docs/CANONICAL_STACK.md`](../docs/CANONICAL_STACK.md)
