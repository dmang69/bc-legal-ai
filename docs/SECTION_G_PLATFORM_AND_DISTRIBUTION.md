# Section G — Platform and Distribution

**Status:** Controlling program section (2026-07-22)  
**Product family:** BC Legal AI Associate  
**Parent program:** [`PHASE_4_MASTER_ENGINEERING_PROGRAM.md`](PHASE_4_MASTER_ENGINEERING_PROGRAM.md)  
**Install quickstart:** [`../INSTALL.md`](../INSTALL.md)

| Product surface | Application name |
|-----------------|------------------|
| Family / legal brand | **BC Legal AI Associate** |
| Desktop (lawyer / advanced) | **BC Legal AI Workbench** |
| Mobile (client-first) | **BC Legal AI Client** |
| Public / secure web | **BC Legal AI Portal** |

> All clients connect to **one private backend**. Legal engine, evidence, knowledge, citations, privilege, deadlines, and audit stay on private infrastructure. Installers never ship client data or production secrets.

**Added workload:** approximately **55–75** platform, packaging, signing, store, update, and device-security tasks (on top of core M0–M8).

---

## 1. Platform objective

```text
Windows desktop application
macOS desktop application
Android mobile application
iPhone and iPad application
Installable browser application (PWA)
Secure web portal
```

Installed applications provide (as maturity allows): authentication; matter access; evidence viewing; document upload; secure messaging; timeline; drafting (workbench); deadline notifications; review and approvals; encrypted local caching; OS integration.

Heavy OCR, legal research, citation verification, and document rendering run on the **secure backend**, not on the phone in Version 1.

---

## 2. Technology stack

| Layer | Choice |
|-------|--------|
| Shared UI | **React · TypeScript · Vite** |
| Native wrapper | **Tauri 2 · Rust** |
| Backend | FastAPI modular monolith, PostgreSQL, pgvector, S3, Redis, workers, private inference |
| Web | Same React app · PWA manifest · service worker · HTTPS |

**Why Tauri 2:** one frontend for Windows, macOS, Android, iOS (Linux later if required); platform-specific config merge; desktop + `android build` / `ios build`. See [Tauri](https://tauri.app/).

---

## 3. Overall architecture

```text
┌──────────────────────────────────────────────────────────┐
│                     APPLICATION CLIENTS                  │
├───────────────┬───────────────┬──────────────┬───────────┤
│ Windows       │ macOS         │ Android      │ iOS       │
│ Tauri App     │ Tauri App     │ Tauri App    │ Tauri App │
├───────────────┴───────────────┴──────────────┴───────────┤
│                 Web Portal / Installable PWA             │
└─────────────────────────────┬────────────────────────────┘
                              │ HTTPS / WebSocket
                              ▼
┌──────────────────────────────────────────────────────────┐
│                    API AND POLICY GATEWAY                │
│ Authentication · Authorization · Consent · Rate Limits  │
└─────────────────────────────┬────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────┐
│                  BC LEGAL AI BACKEND                     │
│ Matters · Evidence · Privilege · Research · Citations   │
│ Deadlines · Drafting · Exports · Messaging · Audit      │
└─────────────────────────────┬────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────┐
│                       DATA LAYER                         │
│ PostgreSQL · pgvector · Object Storage · Audit Ledger   │
└──────────────────────────────────────────────────────────┘
```

---

## 4. Client types (modes)

Same core interface; role and feature flags differ.

### 4.1 Lawyer Workbench (primarily Windows / macOS)

Open/manage matters; large package ingest; OCR review; Evidence Matrix; citation verification; court drafting; Books of Authorities; privilege approval; DOCX/PDF export; Windows folder connector; client activity review; competency approval.

**Display name:** BC Legal AI Workbench.

### 4.2 Client Application (mobile + browser + optional desktop)

Matter status; evidence upload / photo capture; tasks; deadlines; secure messaging; consent; approved decision summaries; enforcement / JR status.

**Must not expose:** internal legal strategy; private lawyer notes; other matters; system prompts; privileged material outside ACL; raw research administration.

**Display name:** BC Legal AI Client.

### 4.3 Self-Represented Workbench (desktop + browser)

Personal matter; organize records; chronology; official legal information; draft materials; deadline identification; **warnings requiring independent counsel**.

**Must not** represent that an attorney–client relationship has been created.

---

## 5. Windows installation

| Artifact | Purpose |
|----------|---------|
| `BC-Legal-AI-Associate-Setup-x64.exe` | Principal direct download (NSIS) |
| `BC-Legal-AI-Associate-x64.msi` | Enterprise / Intune / GPO |
| `BC-Legal-AI-Associate.msix` | Later Store / managed enterprise |

Setup should support: Win10/11; x64 (ARM64 later); per-user install; Start menu; optional desktop shortcut; auto-update; clean uninstall; secure credentials; WebView2 check; repair; silent install.

**Signing:** production EXE/MSI/MSIX digitally signed + timestamped; self-signed only for dev/managed internal. See [MSIX signing](https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview).

**Windows-specific:** approved-folder connector; drag-drop; scanner; notifications; Credential Manager; file associations; encrypted offline cache; updater; crash recovery.

**Release layout:**

```text
releases/windows/
├── BC-Legal-AI-Associate-Setup-x64.exe
├── BC-Legal-AI-Associate-x64.msi
├── BC-Legal-AI-Associate-x64.msix
├── checksums.txt
├── signatures/
└── release-notes.md
```

---

## 6. macOS installation

| Artifact | Purpose |
|----------|---------|
| `BC-Legal-AI-Associate-universal.dmg` | Direct download (preferred) |
| `…-arm64.dmg` / `…-x64.dmg` | Architecture-specific |
| Mac App Store | Stricter sandbox; clients/general users |

| Version | Intended user |
|---------|----------------|
| Direct notarized DMG | Lawyers and advanced users (Workbench) |
| Mac App Store | Clients and general users |

**Signing:** Developer ID → hardened runtime → notarize → staple → Gatekeeper test. See [Apple distribution](https://developer.apple.com/macos/distribution/) and [Tauri macOS signing](https://v2.tauri.app/distribute/sign/macos/).

**macOS-specific:** Finder import; Keychain; Notification Center; Continuity camera; scanner; Touch ID; encrypted cache.

---

## 7. Android installation

| Artifact | Purpose |
|----------|---------|
| `bc-legal-ai-associate.aab` | Google Play primary |
| `bc-legal-ai-associate-universal.apk` | Controlled internal testing only |

No unsigned APK distribution. Permissions only when needed: camera, photos, mic, notifications, biometrics, selected files — **not** broad device search.

**Signing:** separate dev / upload / Play App Signing / recovery procedure.

**Features:** camera evidence; gallery; scanner; audio; push; biometric lock; encrypted cache; upload queue; share-to; messaging; consent.

---

## 8. iPhone / iPad installation

| Channel | Use |
|---------|-----|
| App Store | Production |
| TestFlight | Internal → external → lawyer pilot → review → production |

**Features:** camera/scan; Files import; Face ID/Touch ID; push; encrypted offline; consent; messaging; timeline; approved summaries; JR/enforcement status.

**Limitations:** no whole-device scan; no arbitrary folders; no unrestricted background indexing; no unencrypted case files; no full local AI model in V1. iOS is a secure front end.

---

## 9. Installable web (PWA) + Portal

**BC Legal AI Portal:** secure website + installable PWA (manifest + controlled service worker). See [MDN installing PWAs](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Installing).

**Allow:** dashboards; upload; timeline; messages; consent; tasks; summaries; limited encrypted offline.

**Forbid:** full matter offline dumps; unrestricted folder indexing; unsigned court-ready exports; unencrypted evidence caches.

---

## 10. Repository layout (target)

```text
bc-legal-ai/
├── apps/
│   ├── platform-ui/          # React + TS + Vite (shared)
│   ├── desktop-mobile/       # Tauri 2 (src-tauri + platform confs)
│   ├── pwa/                  # manifest / SW packaging notes
│   ├── desktop/              # interim Python launcher (legacy)
│   └── tauri/                # redirect → desktop-mobile
├── packages/
│   ├── api-client/
│   ├── shared-types/
│   ├── design-system/
│   ├── legal-viewer/
│   └── validation/
├── frontend/client/          # interim static shell until platform-ui owns UI
├── backend/
└── .github/workflows/
```

---

## 11. Platform-specific Tauri config

Merged with base `tauri.conf.json` ([Tauri config](https://v2.tauri.app/reference/config/)):

| File | Controls |
|------|----------|
| `tauri.windows.conf.json` | installer, WebView2, associations, updater, signing |
| `tauri.macos.conf.json` | entitlements, hardened runtime, DMG, signing |
| `tauri.android.conf.json` | permissions, package id, deep links |
| `tauri.ios.conf.json` | entitlements, privacy strings, provisioning |

---

## 12. Security model (installed apps)

### 12.1 Never in installer

Client files; private matters; evidence; API secrets; DB credentials; signing keys; unrestricted model tokens.

### 12.2 Local storage allowed

Short-lived access token; encrypted refresh token; encrypted preferences; encrypted pending uploads; limited encrypted offline cache; synthetic demos.

### 12.3 Credential storage

| Platform | Store |
|----------|--------|
| Windows | Credential Manager |
| macOS | Keychain |
| Android | Keystore |
| iOS | Keychain |

### 12.4 Application lock

PIN/password; Windows Hello; Touch ID; Face ID; Android biometrics; idle lock; remote session revocation.

### 12.5 Lost device

Device removal; refresh-token revoke; remote session kill; local-cache expiry; security alert; audit record.

---

## 13. Offline mode (deliberately limited)

**Allowed:** previously approved limited records; private draft notes; capture photos; queue uploads; tasks; downloaded plain-language summaries.

**Not allowed:** verify current law; final deadline from unverified inputs; privilege waiver; finalize court-ready docs; authoritative treatment; final evidence package export.

**Banner:**

```text
OFFLINE — legal sources, deadlines, and matter status may be outdated.
Reconnect before relying on or filing this material.
```

---

## 14. Release channels

| Channel | Audience | Data |
|---------|----------|------|
| **development** | Developers | Unsigned; synthetic |
| **alpha** | Internal | Signed; synthetic; security/functional tests |
| **beta** | Lawyer/client pilot | TestFlight / Play closed / signed desktop; limited real matters |
| **stable** | Controlled production | Stores + signed direct; monitored updates |

---

## 15. Build matrix

| Platform | Build host | Artifact | Distribution |
|----------|------------|----------|--------------|
| Windows x64 | Windows | `.exe`, `.msi` | Direct, enterprise, Store |
| Windows ARM64 | Windows | `.exe`, `.msi` | Direct, enterprise |
| macOS arm64/x64 | macOS | `.app`, `.dmg` | Direct, App Store |
| Android | Linux/macOS | `.aab`, `.apk` | Play, testing |
| iOS | macOS | `.ipa` | TestFlight, App Store |
| Web/PWA | Linux | static build | Secure host |

---

## 16. CI/CD workflows (target)

```text
.github/workflows/
├── platform-test.yml
├── build-windows.yml
├── build-macos.yml
├── build-android.yml
├── build-ios.yml
├── build-pwa.yml
├── release-beta.yml
└── release-stable.yml
```

Sequence: version → unit/integration → security + confidential scan → frontend build → native builds → sign/notarize → checksums → manifest → beta → approval → stable.

---

## 17. Automatic updates

Desktop direct: signed update metadata (`version`, `mandatory`, `minimum_supported_version`, `download`, `signature`, `sha256`).

Store channels: platform-managed. PWA: web deploy + SW lifecycle.

Backend may refuse outdated clients when auth, privilege, encryption, or leak risk is critical.

---

## 18. Roadmap epics (M6A–M6F)

### M6A — Cross-Platform Application Foundation

M6A-001…012: React/TS UI; Tauri workspace; API client; design system; secure tokens; app lock; env selection; deep links; file associations; encrypted offline cache; updater; privacy-safe crash reporting.

### M6B — Windows Distribution

M6B-001…010: shell; NSIS; MSI; signing; WebView2; Windows Hello; associations; folder connector; updates; Microsoft Store.

### M6C — macOS Distribution

M6C-001…010: shell; universal binary; DMG; Developer ID; notarization; Keychain; Touch ID; Finder; updates; Mac App Store.

### M6D — Android Distribution

M6D-001…010: shell; camera; Keystore; biometric; import; push; APK; AAB; Play signing; closed beta.

### M6E — iOS Distribution

M6E-001…010: shell; camera/scanner; Keychain; Face/Touch ID; Files; push; provisioning; IPA; TestFlight; App Store.

### M6F — Progressive Web Application

M6F-001…010: manifest; SW; install prompt; limited offline; push; responsive layouts; a11y; browser matrix; production deploy.

---

## 19. Platform completion standard

```text
□ Windows signed setup.exe installs and uninstalls cleanly
□ Windows MSI deployment passes
□ macOS signed/notarized DMG passes Gatekeeper
□ Android signed AAB passes closed Play testing
□ Android APK installs on approved test devices
□ iOS build passes TestFlight review
□ PWA installs on supported browsers
□ All clients authenticate against the same backend
□ Matters remain isolated across every client
□ Tokens use platform-secure storage
□ Lost-device revocation works
□ Offline cache is encrypted and limited
□ Updates are signed and verifiable
□ No installer contains client data or production secrets
□ Accessibility testing passes
□ Public clients cannot bypass privilege, consent, or approval gates
```

---

## 20. Recommended delivery order

```text
1. Secure responsive web portal
2. Installable PWA
3. Windows Tauri setup.exe          ← first native (Workbench tools)
4. macOS Tauri DMG
5. Android closed beta              ← Client capture / messaging first
6. iOS TestFlight beta
7. Microsoft Store
8. Google Play production
9. Apple App Store production
10. Enterprise MSI deployment
```

**First engineering slice:** shared React/Vite shell + Tauri producing an **unsigned development Windows `.exe`**, in parallel with M0 human ops and private backend (M1+).

---

## Controlling rules

- No feature bypasses unfinished M1 isolation / M2 quarantine for real client material.  
- Windows connector remains approved-folder only (`architecture/WINDOWS_CONNECTOR_BOUNDARY.md`).  
- Modular monolith backend (`architecture/MODULAR_MONOLITH.md`).  
- Fine-tuning remains late (master program §1.5).
