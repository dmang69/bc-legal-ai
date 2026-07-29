# Signing and distribution (Windows / macOS)

**Policy:** Unsigned builds are for **internal development only**. Public or client distribution requires organization-owned code-signing credentials and a human release approver.

## Windows

### Unsigned build (CI / dev)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1
```

Artifacts land in `releases/windows/` with `checksums.txt` (SHA-256).

### Signing (requires certificate)

1. Obtain an Authenticode code-signing cert (org EV/OV as required by your policy).
2. Import to certificate store or use a `.pfx` with password in a **secret manager** (never commit).
3. Run:

```powershell
$env:ALA_SIGN_PFX = "C:\secure\codesign.pfx"
$env:ALA_SIGN_PFX_PASSWORD = "<from vault>"
# optional timestamp
$env:ALA_SIGN_TIMESTAMP_URL = "http://timestamp.digicert.com"
powershell -ExecutionPolicy Bypass -File scripts\sign_windows_installer.ps1
```

Uses `signtool.exe` (Windows SDK). Re-hashes `checksums.txt` after signing.

### Verification

```powershell
Get-AuthenticodeSignature .\releases\windows\*.exe
```

Expect `Status = Valid`.

## macOS

- Build: `apps/desktop/build_macos.sh` / Tauri macOS conf.
- Notarization: Apple Developer ID + `notarytool` — **human ops**, not automated in this repo without secrets.
- Gatekeeper: stapled notarization ticket required for public distribution.

## GitHub Releases

1. Build + sign on a secured runner (OIDC to vault preferred).
2. Upload only signed artifacts + `checksums.txt` + SBOM if available.
3. Tag must match release notes (`v0.3.0-alpha`, etc.).
4. Release body must state: **not legal advice; not for confidential client data on public demos**.

## What CI may do without secrets

- Compile unsigned installers
- Compute checksums
- Fail if version strings claim “signed” without evidence

## What CI must not do

- Store or print private keys / PFX passwords
- Auto-publish “signed” claims without signature verification step
