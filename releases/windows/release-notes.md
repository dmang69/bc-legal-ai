# BC Legal AI Associate — Windows 0.1.0 (unsigned development)

**Not a lawyer. Not legal advice.**

## Artifacts (build locally)

```text
BC-Legal-AI-Associate-Setup-x64.exe
BC-Legal-AI-Associate-x64.msi
checksums.txt
```

Produced by:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1
```

Or:

```powershell
cd apps\desktop-mobile
npx tauri build --config src-tauri/tauri.windows.conf.json
```

## Status

- **Source:** complete (`apps/platform-ui` + `apps/desktop-mobile`)
- **Signing:** not applied (do not distribute publicly until Authenticode-signed)
- **Backend:** private FastAPI (`uvicorn backend.api.main:app --port 8000`)
- **Stores:** not submitted

macOS / Android / iOS installers require their platform toolchains and are not produced on Windows.
