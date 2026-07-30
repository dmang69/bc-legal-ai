# Installer upgrades — how each platform updates

**Not legal advice.** Client installers never ship confidential matter data.

## Upgrade model by platform

| Platform | Upgrade mechanism | What must increase |
|----------|-------------------|--------------------|
| **Windows** | Re-run Setup `.exe` / MSI (same product id) **or** in-app auto-updater | Semver in `tauri.conf.json` |
| **macOS** | New `.dmg` / in-app auto-updater | Semver |
| **Linux** | New AppImage/deb or in-app auto-updater | Semver |
| **Android** | Google Play (or higher `versionCode` APK) | Play versionCode |
| **iOS** | App Store / TestFlight | CFBundleVersion |
| **Chrome PWA** | Reload / reinstall PWA (browser cache + new `dist/`) | Deployed asset hash |

Stable product identity (do **not** change between upgrades):

```text
identifier:   ca.bclegalai.associate
productName:  BC Legal AI Associate
WiX upgradeCode: A1B2C3D4-E5F6-7890-ABCD-EF1234567890
```

## Desktop auto-updater (Tauri)

Configured in `apps/desktop-mobile/src-tauri/tauri.conf.json`:

- `bundle.createUpdaterArtifacts: true` — emit `.sig` + updater payloads  
- `plugins.updater.endpoints` →  
  `https://github.com/dmang69/bc-legal-ai/releases/latest/download/latest.json`  
- Public minisign key embedded (private key **never** committed)  
- Windows passive install mode for silent-friendly updates  

Runtime:

- Rust: `tauri-plugin-updater` + `tauri-plugin-process`  
- UI helper: `apps/platform-ui/src/lib/desktopUpdater.ts`  

### Release steps (desktop)

1. Bump **same** version in:
   - `apps/desktop-mobile/src-tauri/tauri.conf.json`
   - `apps/desktop-mobile/src-tauri/Cargo.toml`
   - `apps/desktop-mobile/package.json`
2. Build installers (with `TAURI_SIGNING_PRIVATE_KEY_PATH` set).  
3. Authenticode-sign Windows binaries (org cert).  
4. Upload to GitHub Release: installers, `*.sig`, `latest.json` (see `releases/latest.json.example`).  
5. Users on older desktop builds receive the update on next check.

Generate signing key (once per org, keep private key in vault):

```bash
npx tauri signer generate -w ~/.tauri/bc-legal-ai-updater.key
# put .pub contents into plugins.updater.pubkey
```

## Windows in-place upgrade test

```powershell
# 1) Build vA
powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1
# Install releases\windows\*-setup.exe

# 2) Bump version 0.1.1 → 0.1.2 in conf/Cargo/package.json, rebuild
# 3) Run new setup.exe
# Expected: same Start Menu entry, version shows 0.1.2, user data preserved (per-user install)
```

## Verify config (CI / local)

```bash
cd apps/desktop-mobile
npm run verify:config
```

**Windows smoke (this repo):** install `0.1.1` then `0.1.2` silently — **PASS**.  
See [INSTALLER_UPGRADE_SMOKE.md](INSTALLER_UPGRADE_SMOKE.md).

## Mobile store upgrades

| Store | Rule |
|-------|------|
| Google Play | Each upload needs higher `versionCode` |
| App Store | Higher build number; users update via App Store |

Tauri mobile configs: `tauri.android.conf.json`, `tauri.ios.conf.json`.  
Store credentials and listing are **org-operated** — not automated in this repo without secrets.

## Chrome / Edge PWA

1. Deploy new `apps/platform-ui/dist` to the same HTTPS origin.  
2. Users get UI updates on refresh (service worker optional future).  
3. Manifest: `public/manifest.webmanifest` — keep `name` / `start_url` stable so the installed app updates in place.

## What “working upgrade” means (acceptance)

| Check | Pass criteria |
|-------|----------------|
| Config verify | `npm run verify:config` exit 0 |
| Windows reinstall | Higher version installer upgrades same product |
| Auto-update JSON | `latest.json` version > installed; signature valid |
| PWA | New deploy visible after hard refresh / app restart |
| Mobile | Store accepts higher versionCode/build |

## Security

- Never commit `*.key` updater private keys or Authenticode PFX  
- CI may build **unsigned** installers; signing is human/vault gated  
- See [SIGNING_AND_DISTRIBUTION.md](SIGNING_AND_DISTRIBUTION.md)
