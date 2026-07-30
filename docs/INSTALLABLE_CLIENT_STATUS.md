# Installable client — what must be built first

**Status corrected 2026-07-22.** The shared application source **already exists** in this repository. What does **not** exist yet is **published signed installer binaries** on GitHub Releases.

**Full WBS:** [`SECTION_G_PROJECT_PLAN.md`](SECTION_G_PROJECT_PLAN.md) (M6A–M6F, INFRA, risks, critical path).

## Correct current status

| Platform | Source | Installer binary |
|----------|--------|------------------|
| Shared React UI | **Exists** — `apps/platform-ui/` | Web + **PWA** (`public/manifest.webmanifest`) |
| Tauri 2 shell | **Exists** — `apps/desktop-mobile/` + `src-tauri/` | Not published on Releases |
| Windows | Config: `tauri.windows.conf.json` + `scripts/build_windows_installer.ps1` | **Build locally (unsigned)** → `releases/windows/*.exe` |
| macOS | Config: `tauri.macos.conf.json` | **Build on Mac** → `.dmg` / `.app` |
| Linux | Tauri / Docker | **Build on Linux** or run API via Docker |
| Android | Config: `tauri.android.conf.json` | **Build with Android SDK** → `.aab` / `.apk` |
| iOS | Config: `tauri.ios.conf.json` | **Build on Mac + Xcode** → TestFlight `.ipa` |
| Chrome / Edge | Manifest + icons in platform-ui | **Install as app** when hosted on HTTPS |
| App signing / stores | Process documented | Org certs required — see SIGNING_AND_DISTRIBUTION |
| Public demo Space | `huggingface-space-static/` | Live: spaces/Dmang69/bc-legal-ai |

## Source tree (required components — present)

```text
apps/platform-ui/                 React + TypeScript + Vite
apps/desktop-mobile/
  package.json
  src-tauri/
    Cargo.toml
    build.rs
    tauri.conf.json
    tauri.windows.conf.json
    tauri.macos.conf.json
    tauri.android.conf.json
    tauri.ios.conf.json
    capabilities/default.json
    icons/
    src/main.rs
    src/lib.rs
```

## Build order (correct)

```text
1. Private API running (or known API URL)
2. npm install in platform-ui + desktop-mobile
3. npm run build (platform-ui)  → dist/
4. npm run tauri build (desktop-mobile)
5. Collect artifacts from src-tauri/target/release/bundle/
6. Sign (Windows Authenticode / Apple notarize)
7. Publish GitHub Release + checksums
8. Android .aab → Play; iOS .ipa → TestFlight/App Store
```

## Intended GitHub Release layout (after build + sign)

```text
GitHub Releases
├── BC-Legal-AI-Associate-Setup-x64.exe   # NSIS
├── BC-Legal-AI-Associate-x64.msi         # WiX (Windows runner)
├── BC-Legal-AI-Associate-universal.dmg   # macOS
├── BC-Legal-AI-Associate.apk             # Android testing only
├── checksums.txt
└── release-notes.md
```

- Production Android: **`.aab`** via Google Play (not a public apk download).  
- iPhone: **TestFlight / App Store** (not a public downloadable installer).

## Dependency rule

Installers that only wrap a UI still require a **private backend** for real matters.  
Public demos stay synthetic (`APP_MODE=public_demo`).  
Do not ship court-ready features without M1 isolation + privilege gates.

## Scripts

- Windows local: `scripts/build_windows_installer.ps1`  
- CI scaffold: `.github/workflows/build-windows.yml`
