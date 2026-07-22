# Mobile packaging (legacy notes)

**Preferred path:** **Tauri 2** mobile targets under [`apps/tauri/`](../tauri/README.md)  
(Android `.aab`/`.apk`, iOS TestFlight/App Store `.ipa`).

**Always available:** **PWA** — open the private API URL in Safari/Chrome → Install / Add to Home Screen.

## Capacitor (deprecated for new work)

The files in this folder are **legacy**. Do not expand Capacitor for production. Migrate any native plugin work into Tauri 2 plugins with security review.

## PWA (prototype)

1. Start private API: `uvicorn backend.api.main:app --host 127.0.0.1 --port 8000`  
2. On phone (same private network only if trusted): open URL → Add to Home Screen.  
3. PWA caches UI only; API data is not cached offline for confidentiality.

See root **[INSTALL.md](../../INSTALL.md)**.
