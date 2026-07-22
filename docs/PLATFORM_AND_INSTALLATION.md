# Platform and Installation Strategy

**Status:** Pointer — full controlling text is **Section G**.

→ **[`SECTION_G_PLATFORM_AND_DISTRIBUTION.md`](SECTION_G_PLATFORM_AND_DISTRIBUTION.md)**

## Summary

| Item | Decision |
|------|----------|
| Shell | **Tauri 2** + Rust |
| Shared UI | **React · TypeScript · Vite** (`apps/platform-ui`) |
| Backend | Private FastAPI modular monolith |
| Surfaces | Workbench · Client · Portal · Self-rep mode |
| Channels | Windows EXE/MSI · macOS DMG · Android AAB · iOS IPA · PWA |

## Layout

```text
apps/platform-ui/       React shared interface
apps/desktop-mobile/    Tauri 2 (desktop + mobile)
apps/pwa/               Portal packaging notes
packages/               Shared libs (scaffold)
```

## Delivery order

1. Secure web portal → 2. PWA → 3. Windows setup.exe → 4. macOS DMG → 5–6 mobile beta → 7–10 stores / MSI

See Section G §20. Quickstart: root **`INSTALL.md`**.
