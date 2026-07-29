# BC Legal AI Associate — Section G Project Plan

**Platform & Distribution Work Breakdown Structure**

| Field | Value |
|-------|--------|
| Program | BC Legal AI Associate |
| Section | G — Platform and Distribution |
| Date prepared | 2026-07-22 |
| Status | **Active** — foundation partially implemented; signed store releases not started |
| Parent | [`SECTION_G_PLATFORM_AND_DISTRIBUTION.md`](SECTION_G_PLATFORM_AND_DISTRIBUTION.md) |
| Related | [`INSTALLABLE_CLIENT_STATUS.md`](INSTALLABLE_CLIENT_STATUS.md), [`CONVERSATIONAL_WORKSPACE_SPEC.md`](CONVERSATIONAL_WORKSPACE_SPEC.md) |

> The platform shell is only the **container**. Product interaction is the **conversational legal workspace**. Both share this distribution plan.

---

## Implementation status legend

| Mark | Meaning |
|------|---------|
| **Done** | In repo / verified locally |
| **Partial** | Scaffold or unsigned/local only |
| **Open** | Not started or blocked |

---

## 1. Delivery sequence (recommended)

| Order | Deliverable | Channel | Status |
|------:|-------------|---------|--------|
| 1 | Secure responsive web portal | Web host | **Partial** — conversational UI + API local; no production host |
| 2 | Installable PWA | Web host | **Partial** — VitePWA in `platform-ui`; no prod HTTPS deploy |
| 3 | Windows Tauri setup.exe | Direct download | **Partial** — **unsigned** local build exists |
| 4 | macOS Tauri DMG | Direct download | **Open** (source ready; needs Mac + notarize) |
| 5 | Android closed beta | Google Play closed | **Open** (config only) |
| 6 | iOS TestFlight beta | TestFlight | **Open** (config only) |
| 7 | Microsoft Store package | Microsoft Store | **Open** |
| 8 | Google Play production | Google Play | **Open** |
| 9 | Apple App Store production | App Store | **Open** |
| 10 | Enterprise MSI deployment | Managed distribution | **Partial** — MSI built unsigned locally |

---

## 2. Dependency graph

```text
M6A (Foundation) ──┬──► M6B (Windows) ──► M6B-010 (MS Store)
                   ├──► M6C (macOS)   ──► M6C-010 (Mac App Store)
                   ├──► M6D (Android) ──► M6D-010 (Play Store)
                   ├──► M6E (iOS)     ──► M6E-010 (App Store)
                   └──► M6F (PWA)     ──► Production web deployment

Release pipeline requires:
  M6F-001/002 (manifest + service worker) before M6F-003 (install prompt)
  M6A-002 (Tauri workspace) before any native build
  M6A-001 (React/TS interface) before any platform shell
```

**Key insight:** M6A delays cascade to all platform tracks. Prioritize M6A + INFRA in parallel.

---

## 3. Milestone M6A — Cross-Platform Application Foundation

**Priority:** CRITICAL — blocks all other milestones  
**Prerequisites:** Backend API (auth + matters minimum) — **available** (`/v1/platform/*`)

| ID | Task | Status | Notes |
|----|------|--------|-------|
| M6A-001 | React/TypeScript platform interface | **Done** | `apps/platform-ui/` — conversational 3-panel workspace (IF-1) |
| M6A-002 | Initialize Tauri 2 workspace | **Done** | `apps/desktop-mobile/src-tauri/` + platform confs |
| M6A-003 | Shared API client package | **Partial** | Client lives in `platform-ui/src/lib/api.ts`; extract to `packages/api-client/` later |
| M6A-004 | Shared design system package | **Partial** | Tokens/styles in UI; not yet `packages/design-system/` |
| M6A-005 | Secure token storage | **Partial** | Browser `localStorage` only; OS Cred Manager / Keychain / Keystore **Open** |
| M6A-006 | Application lock | **Open** | PIN / biometric / idle / remote revoke |
| M6A-007 | Environment selection | **Partial** | `VITE_API_BASE_URL` / modes; no in-app env switcher UI |
| M6A-008 | Deep-link handling | **Open** | |
| M6A-009 | File-association framework | **Open** | |
| M6A-010 | Encrypted offline cache | **Open** | Offline banner only in UI |
| M6A-011 | Update framework | **Open** | |
| M6A-012 | Crash reporting (privacy-controlled) | **Open** | |

### M6A completion standard

| Criterion | Status |
|-----------|--------|
| Shared UI renders on desktop and mobile shells | **Partial** — web + Windows shell; mobile shells not init’d |
| API client authenticates against backend | **Done** |
| Tokens in platform-secure storage | **Open** (web storage only) |
| App lock + biometrics on ≥1 platform | **Open** |
| Environment switching changes API target | **Partial** |
| Offline cache encrypts/decrypts | **Open** |

---

## 4. Milestone M6B — Windows Distribution

**Priority:** HIGH — first native build  
**Host:** Windows runner  
**Prerequisites:** M6A-001, M6A-002 (met); M6A-005, M6A-006 (not met for production)

| ID | Task | Status |
|----|------|--------|
| M6B-001 | Windows application shell | **Done** |
| M6B-002 | NSIS setup EXE | **Partial** — unsigned `BC-Legal-AI-Associate-Setup-x64.exe` built locally |
| M6B-003 | MSI package | **Partial** — unsigned MSI built locally |
| M6B-004 | Windows signing | **Open** |
| M6B-005 | WebView2 handling | **Partial** — relies on system WebView2; no installer detect/guide yet |
| M6B-006 | Windows Hello | **Open** |
| M6B-007 | File associations | **Open** |
| M6B-008 | Folder connector (approved-folder only) | **Open** |
| M6B-009 | Automatic updates | **Open** |
| M6B-010 | Microsoft Store MSIX | **Open** |

### Artifacts (target)

```text
releases/windows/
├── BC-Legal-AI-Associate-Setup-x64.exe
├── BC-Legal-AI-Associate-x64.msi
├── BC-Legal-AI-Associate-x64.msix
├── checksums.txt
├── signatures/
└── release-notes.md
```

**Local (unsigned):** Setup.exe + MSI + checksums produced; binaries gitignored; notes in repo.

**Script:** `scripts/build_windows_installer.ps1`

---

## 5. Milestone M6C — macOS Distribution

**Priority:** HIGH  
**Host:** macOS runner  

| ID | Task | Status |
|----|------|--------|
| M6C-001 … M6C-010 | Shell → universal → DMG → sign → notarize → Keychain → Touch ID → Finder → updates → MAS | **Open** (configs exist: `tauri.macos.conf.json`) |

---

## 6. Milestone M6D — Android Distribution

**Priority:** MEDIUM  

| ID | Task | Status |
|----|------|--------|
| M6D-001 … M6D-010 | Shell → camera → Keystore → biometrics → share → push → APK/AAB → Play signing → closed beta | **Open** (`tauri.android.conf.json` only) |

**Permissions rule:** Camera, photos, mic, notifications, biometrics, **selected** files only — **not** broad storage.

---

## 7. Milestone M6E — iOS Distribution

**Priority:** MEDIUM  
**Host:** macOS + Xcode  

| ID | Task | Status |
|----|------|--------|
| M6E-001 … M6E-010 | Shell → scanner → Keychain → Face/Touch ID → Files → APNs → signing → IPA → TestFlight → App Store | **Open** (`tauri.ios.conf.json` only) |

**V1 limits:** No whole-device scan; no arbitrary folders; no unrestricted background index; no unencrypted case files; no local full LLM; front-end to private backend.

---

## 8. Milestone M6F — Progressive Web Application

**Priority:** HIGH — delivery items #1–2  

| ID | Task | Status |
|----|------|--------|
| M6F-001 | Web manifest | **Partial** — VitePWA manifest |
| M6F-002 | Service worker | **Partial** — generated; `/v1/*` NetworkOnly |
| M6F-003 | Install prompt | **Open** (browser native only) |
| M6F-004 | Secure limited offline | **Partial** — offline banner; no encrypted offline matter cache |
| M6F-005 | Web push | **Open** |
| M6F-006 | Responsive desktop (Workbench) | **Partial** — conversational layout |
| M6F-007 | Responsive mobile (Client) | **Partial** — CSS breakpoints |
| M6F-008 | Accessibility validation | **Open** |
| M6F-009 | Browser compatibility matrix | **Open** |
| M6F-010 | Production HTTPS deployment | **Open** |

---

## 9. Infrastructure & CI/CD (parallel)

| ID | Task | Status |
|----|------|--------|
| INFRA-001 | Monorepo layout | **Partial** — `apps/`, `backend/`, `docs/`; packages/* stubs |
| INFRA-002 | CI/CD workflows | **Partial** — `ci.yml`, `platform-test.yml`, `build-pwa.yml`, `build-windows.yml`, confidential scan |
| INFRA-003 | Windows runner (WebView2, WiX, NSIS, signing) | **Partial** — local build works; CI signing **Open** |
| INFRA-004 | macOS runner | **Open** |
| INFRA-005 | Android signing | **Open** |
| INFRA-006 | iOS provisioning | **Open** |
| INFRA-007 | Web hosting | **Open** |
| INFRA-008 | Code-signing certificates | **Open** |
| INFRA-009 | Secret management for CI | **Open** |

### Required workflows (target)

```text
.github/workflows/
├── platform-test.yml
├── build-windows.yml
├── build-macos.yml       # TODO
├── build-android.yml     # TODO
├── build-ios.yml         # TODO
├── build-pwa.yml
├── release-beta.yml      # TODO
└── release-stable.yml    # TODO
```

---

## 10. Release pipeline

```text
1. Version update
2. Unit tests
3. Integration tests
4. Security scan
5. Confidential-data scan
6. Frontend build
7. Native builds
8. Code signing
9. Notarization (macOS)
10. Checksums
11. Release manifest
12. Beta distribution
13. Human approval gate
14. Stable distribution
```

Current CI covers steps 2, 5, partial 6; not full signed release path.

---

## 11. Release channels

| Channel | Audience | Signing | Data | Distribution |
|---------|----------|---------|------|--------------|
| development | Developers | Unsigned | Synthetic | Local (current Windows build) |
| alpha | Internal QA | Signed | Synthetic | Internal |
| beta | Controlled pilot | Signed | Limited real matters | TestFlight / Play closed / signed desktop |
| stable | Production | Signed | Controlled production | Stores + signed direct |

---

## 12. Security requirements (cross-cutting)

| Requirement | Status |
|-------------|--------|
| No client data in installers | **Policy** — enforced by process; unsigned local builds contain no matter DBs |
| No production secrets in builds | **Policy** |
| Platform-secure credential storage | **Open** (web only) |
| Encrypted local cache | **Open** |
| App lock + biometric + PIN | **Open** |
| Remote session revocation | **Partial** — logout revokes session server-side |
| Lost-device response | **Open** |
| Offline restrictions enforced | **Partial** — UI banner |
| Forced security updates for outdated clients | **Open** |
| Signed verifiable updates | **Open** |
| Accessibility | **Open** |
| Privilege/consent/approval not bypassable from public clients | **Partial** — public_demo + gates; incomplete |

---

## 13. Critical path

```text
INFRA-001 (repo)
  → M6A-001 React/TS ✅
    → M6A-002 Tauri ✅
      → M6A-005 secure tokens ⏳
        → M6A-006 application lock ⏳
          → M6B Windows ⏳ (unsigned shell/exe/msi done)
          → M6C macOS ⏳
          → M6D Android ⏳
          → M6E iOS ⏳
          → M6F PWA production ⏳
```

---

## 14. Platform completion checklist (Section G done only when all pass)

- [ ] Windows signed setup.exe installs/uninstalls cleanly  
- [ ] Windows MSI managed deploy passes  
- [ ] macOS signed/notarized DMG passes Gatekeeper  
- [ ] Android signed AAB closed Play testing  
- [ ] Android APK on approved test devices  
- [ ] iOS TestFlight review  
- [ ] PWA installs on supported browsers  
- [ ] All clients auth against same backend  
- [ ] Matter isolation across every client  
- [ ] Platform-secure token storage  
- [ ] Lost-device revocation  
- [ ] Encrypted limited offline cache  
- [ ] Signed verifiable updates  
- [ ] No client data / secrets in installers  
- [ ] Accessibility testing  
- [ ] Public clients cannot bypass privilege/consent/approval  

---

## 15. Technology stack summary

| Layer | Technology |
|-------|------------|
| Shared UI | React, TypeScript, Vite |
| Native wrapper | Tauri 2, Rust |
| Backend API | FastAPI |
| Database | PostgreSQL + pgvector (target); SQLite default dev |
| Object storage | S3-compatible |
| Cache | Redis |
| AI inference | Private endpoint (+ future Ollama) |
| Desktop dist | NSIS, WiX, DMG |
| Mobile dist | AAB/APK, IPA |
| Web dist | PWA |
| CI/CD | GitHub Actions |
| Signing | Platform-specific |

---

## 16. Risk register

| Risk | Impact | Mitigation |
|------|--------|------------|
| M6A delays cascade | HIGH | Finish M6A-005/006 next; parallel INFRA |
| Apple notarization delays | MEDIUM | Early M6C buffer |
| WebView2 missing on Windows | MEDIUM | M6B-005 installer guidance |
| Play signing key compromise | HIGH | Separate keys + recovery (M6D-009) |
| iOS sandbox vs desktop features | MEDIUM | Document Store vs DMG matrix |
| Code-signing cert expiry | HIGH | Calendar + CI checks |
| PWA offline frustration | LOW | Offline banners (started) |
| Forced update bricks legacy | MEDIUM | min supported version + grace period |

---

## 17. Immediate next tasks (execution order)

1. **M6A-005** — secure token storage abstraction (web → crypto.subtle; Tauri plugins for OS stores)  
2. **M6A-006** — application lock (PIN + idle) on web + Windows  
3. **M6A-003/004** — extract `packages/api-client` + design tokens  
4. **M6B-004** — procure Authenticode; sign Setup.exe/MSI; CI secret  
5. **M6F-010** — production HTTPS portal deploy  
6. **M6C/D/E** — platform runners when certs ready  

---

*Generated from Section G specification; status updated against repository state 2026-07-22.*
