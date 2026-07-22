#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI="$ROOT/apps/platform-ui"
TAURI_SOURCE="$ROOT/apps/desktop-mobile/src-tauri"
TAURI_TARGET="$UI/src-tauri"

if [[ ! -d "$TAURI_TARGET" ]]; then
  cp -R "$TAURI_SOURCE" "$TAURI_TARGET"
fi

cd "$UI"
npm install
printf '\nPlatform dependencies installed. Run: npm run dev\n'
