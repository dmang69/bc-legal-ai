# Mobile installs (Android + iPhone)

The primary mobile path is a **Progressive Web App (PWA)** served by the local or private API.

## Option A — PWA (recommended for prototype)

1. On a PC, start the platform: `python apps/desktop/launcher.py` (or private server).
2. Open the URL on the phone (same Wi‑Fi), e.g. `http://192.168.x.x:8765/`.
3. **iPhone (Safari):** Share → **Add to Home Screen**.
4. **Android (Chrome):** Menu → **Install app** / **Add to Home Screen**.

PWA shell caches UI only; API data is not cached offline (confidentiality).

## Option B — Capacitor native shells

Requires Node.js 18+, Xcode (iOS), Android Studio (Android).

```bash
cd apps/mobile
npm init -y
npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios
npx cap init "BC Legal AI Associate" ca.bc.legalai.associate --web-dir ../../frontend/client
# copy capacitor.config.json settings (server.url → your API host)
npx cap add android
npx cap add ios
npx cap sync
npx cap open android   # Android Studio → Run
npx cap open ios       # Xcode → Run on simulator/device
```

**Important:** Point `server.url` at a **private** API host (TLS). Do not ship a public Space URL as a production backend for client files.

## App Store notes

- Store submissions need privacy policy, account deletion, legal disclaimers.
- This product is **support software**, not a substitute for a licensed lawyer.
- Unsigned / sideload builds are for development only.
