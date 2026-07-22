# Platform and Installation Strategy

**Status:** Controlling client-delivery strategy (2026-07-22)  
**Related:** `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md` (M6), `architecture/MODULAR_MONOLITH.md`, `architecture/WINDOWS_CONNECTOR_BOUNDARY.md`

## Principle

One **shared application interface** (the web client in `frontend/client/`) is wrapped with **Tauri 2** and connected to the **private BC Legal AI backend** (modular FastAPI monolith). Platform packaging differs; product logic does not.

```text
┌─────────────────────────────────────────────────────────┐
│  Shared UI  frontend/client  (+ later design system)     │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP/TLS to private API
┌───────────────────────────▼─────────────────────────────┐
│  Tauri 2 shell (desktop + mobile)  OR  browser PWA      │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  Private backend  backend.api.main  (modular monolith)  │
│  · identity · matter · consent · privilege · evidence…  │
└─────────────────────────────────────────────────────────┘
```

Tauri 2 supports **Windows, macOS, Android, and iOS** from one frontend codebase, with platform-specific configuration and native hooks (e.g. approved-folder connector on Windows only).

---

## Five delivery methods

| Platform | Installation artifact | Notes |
|----------|----------------------|--------|
| **Windows** | Signed **`.exe`** installer; optional **`.msi`** | Code signing required before pilot |
| **macOS** | Signed and **notarized** **`.dmg`** containing **`.app`** | Apple Developer ID + notarization |
| **Android** | Google Play **`.aab`**; optional direct **`.apk`** | Play Console / internal testing tracks |
| **iPhone / iPad** | App Store / TestFlight **`.ipa`** | Apple Developer + privacy nutrition labels |
| **Browser** | Installable **Progressive Web App** | Same UI; no native FS connector |

---

## Why Tauri 2 (not five separate apps)

| Approach | Role in this project |
|----------|----------------------|
| **Tauri 2 (primary)** | One shell, small binary footprint, Rust security boundary, mobile + desktop |
| **PWA (always)** | Browser install path; demos; zero-store distribution of UI only |
| **Python + PyInstaller (interim)** | Local prototype when Node/Rust toolchain unavailable (`apps/desktop/`) |
| **Capacitor (deprecated for new work)** | Superseded by Tauri 2 mobile; do not expand |

---

## Backend connection rules

| Mode | Backend | Client data |
|------|---------|-------------|
| **Production / pilot** | Private API (TLS, MFA, matter ACL) | Real matters only after M1+M2 gates |
| **Public demo** | `APP_MODE=public_demo` | Synthetic only; no uploads; no court-ready export |
| **Local prototype** | `127.0.0.1` or org VPN | Synthetic preferred; never public Git |

The shell **never** embeds model weights or live matter files. Configuration supplies `API_BASE_URL` (and future OIDC endpoints).

### Environment variables (client)

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` / `ALA_API_BASE` | Private backend origin |
| `APP_MODE` | Server-side; client may display banner only |

---

## Platform-specific native capabilities

| Capability | Windows | macOS | Android | iOS | Browser PWA |
|------------|:-------:|:-----:|:-------:|:---:|:-----------:|
| Shared UI + API | ✓ | ✓ | ✓ | ✓ | ✓ |
| Approved-folder connector | ✓ | later | — | — | — |
| Biometric / OS secure store | ✓ | ✓ | ✓ | ✓ | limited |
| Background upload (policy-gated) | ✓ | ✓ | ✓ | ✓ | limited |
| Silent whole-drive index | **Forbidden** | **Forbidden** | n/a | n/a | n/a |

Windows connector rules: `architecture/WINDOWS_CONNECTOR_BOUNDARY.md`.

---

## Release maturity vs installers

| Release level | What may be distributed |
|---------------|-------------------------|
| **Prototype** | Unsigned local builds; PWA against local API |
| **Internal Alpha** | Signed internal builds; synthetic data only |
| **Supervised Beta** | TestFlight / Play internal / signed desktop; real matters under supervision |
| **Controlled Production** | Store listings + signed installers; pilot scope defined |

Do not publish store apps that accept real client files until M1 isolation, M2 quarantine, and M8 gates apply.

---

## Repository layout

```text
frontend/client/          Shared UI (HTML/CSS/JS → evolve to Vite if needed)
apps/tauri/               Tauri 2 shell (desktop + mobile)  ← primary packaging
apps/desktop/             Interim Python launcher / PyInstaller (fallback)
apps/mobile/              Legacy Capacitor notes (do not expand)
```

Build entry: `apps/tauri/README.md`.

---

## Signing and compliance checklist (later)

- [ ] Windows Authenticode certificate  
- [ ] macOS Developer ID Application + notarization  
- [ ] Android Play App Signing  
- [ ] Apple App Store privacy + export compliance  
- [ ] Privacy nutrition labels / data safety forms  
- [ ] Update channel (no silent remote code without consent)  
- [ ] Crash reporting without confidential matter payloads  

---

## Controlling build rule (installers)

An installer that “works” does **not** authorize:

- public real-client intake;
- court-ready export without privilege gates;
- Windows whole-drive search;
- connecting a public Space to live matters.

See `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`.
