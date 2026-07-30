# Installer upgrade smoke — local Windows (2026-07-29)

**Host:** Windows 10/11 · Node 24 · Rust 1.96  
**Product id:** `ca.bclegalai.associate` · **Name:** BC Legal AI Associate

## Results

| Step | Result |
|------|--------|
| Upgrade config (`npm run verify:config`) | **PASS** |
| UI typecheck + build | **PASS** |
| Pytest `test_installer_upgrade_config.py` | **PASS** (4) |
| Build **0.1.1** NSIS + MSI | **PASS** |
| Silent install 0.1.1 (`/S`) | **PASS** (exit 0) → `%LOCALAPPDATA%\BC Legal AI Associate\` |
| Build **0.1.2** NSIS + MSI | **PASS** |
| Silent **upgrade** 0.1.2 over 0.1.1 (`/S`) | **PASS** (exit 0) |
| Silent uninstall | **PASS** (app removed) |
| Chrome PWA manifest + link | **PASS** |
| macOS `.dmg` build | **Not run** (requires Mac) |
| Android / iOS store packages | **Not run** (requires Android SDK / Xcode) |
| In-app auto-updater end-to-end | **Config PASS** · needs published `latest.json` + signed `.sig` on GitHub Releases |

## Artifacts produced (local)

```text
releases/windows/
  BC Legal AI Associate_0.1.1_x64-setup.exe
  BC Legal AI Associate_0.1.1_x64_en-US.msi
  BC Legal AI Associate_0.1.2_x64-setup.exe
  BC Legal AI Associate_0.1.2_x64_en-US.msi
```

(Not committed — build outputs.)

## How upgrades work (verified design)

1. **Stable identity** — same `identifier` + `productName` + WiX `upgradeCode` across versions.  
2. **Higher semver** — 0.1.1 → 0.1.2 installer replaces prior install in place.  
3. **NSIS** `installMode=currentUser` — per-user upgrade without elevation.  
4. **Auto-updater** (optional for release): set `createUpdaterArtifacts=true`, sign with org minisign key, publish `latest.json`.  

## Commands to reproduce

```powershell
cd apps\desktop-mobile
npm run verify:config

# Build
powershell -ExecutionPolicy Bypass -File ..\..\scripts\build_windows_installer.ps1

# Install then upgrade (elevated not required for currentUser)
.\releases\windows\*0.1.1*-setup.exe /S
.\releases\windows\*0.1.2*-setup.exe /S
```

## Platform matrix (upgrade readiness)

| Platform | Ready? | Evidence |
|----------|--------|----------|
| Windows Setup.exe | **Yes** | Install + upgrade smoke |
| Windows MSI | **Built** | Same product; upgrade via MSI supported by WiX upgradeCode |
| macOS | **Config ready** | Needs Mac build + notarize |
| Linux | **Config ready** | Needs Linux Tauri prereqs |
| Android | **Config ready** | Store versionCode on release |
| iOS | **Config ready** | TestFlight build number |
| Chrome PWA | **Yes** | Manifest standalone; redeploy = update |

## Notes

- `createUpdaterArtifacts` defaults to **false** for local builds (avoids interactive key prompts). Enable for GitHub Release auto-update packages.  
- Authenticode signing of `.exe`/`.msi` is separate (org cert) — see `SIGNING_AND_DISTRIBUTION.md`.  
- Private key for updater lives only under `%USERPROFILE%\.tauri\` — never commit.
