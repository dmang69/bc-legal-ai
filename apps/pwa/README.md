# PWA packaging — BC Legal AI Portal

Installable web app is produced from **`apps/platform-ui`** using the web app
manifest (Chrome / Edge “Install page as app”).

| Mode | `VITE_APP_MODE=portal` (or `private`) |
|------|----------------------------------------|
| Name | BC Legal AI Associate / Portal |
| Manifest | `apps/platform-ui/public/manifest.webmanifest` |
| Icons | `public/icons/icon-192.png`, `icon-512.png` |
| Offline | API `/v1/*` requires network; install is for app chrome only |

## Build portal

```bash
cd apps/platform-ui
# set VITE_API_BASE_URL to private HTTPS origin
npm install
npm run build
# deploy dist/ to secure host (TLS required for installability)
```

### Install in Google Chrome

1. Open the hosted Portal over **HTTPS** (or `http://localhost`).  
2. Chrome menu → **Install page as app…** (or install icon in the omnibox).  
3. Launch from desktop / app launcher.

Full multi-platform install: **[INSTALL.md](../../INSTALL.md)**.

See Section G §9 and M6F in `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`.

Interim static shell remains in `frontend/client/` until portal cutover is complete.
