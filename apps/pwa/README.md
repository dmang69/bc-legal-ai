# PWA packaging — BC Legal AI Portal

Installable web app is produced from **`apps/platform-ui`** via VitePWA.

| Mode | `VITE_APP_MODE=portal` |
|------|------------------------|
| Name | BC Legal AI Portal |
| Offline | Network-only for `/v1/*`; limited UI shell cache only |

## Build static portal

```bash
cd apps/platform-ui
cp .env.example .env
# set VITE_API_BASE_URL to private HTTPS origin
npm install
npm run build
# deploy dist/ to secure host (TLS required for installability)
```

See Section G §9 and M6F issues in `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`.

Interim static shell remains in `frontend/client/` until portal cutover is complete.
