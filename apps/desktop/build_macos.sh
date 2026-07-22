#!/usr/bin/env bash
# Build macOS app binary for BC Legal AI Associate
# Usage (from monorepo root):
#   chmod +x apps/desktop/build_macos.sh
#   ./apps/desktop/build_macos.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "Repo: $ROOT"
python3 -m pip install -q --upgrade pip
python3 -m pip install -q "fastapi>=0.115" "uvicorn[standard]>=0.30" "pydantic>=2" "pywebview>=5.0" "pyinstaller>=6.0"

python3 -m PyInstaller --noconfirm --clean apps/desktop/bc_legal_ai.spec

# Optional: wrap as .app bundle
APP="dist/BC Legal AI Associate.app"
BIN="dist/BCLegalAIAssociate"
if [[ -f "$BIN" ]]; then
  rm -rf "$APP"
  mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
  cp "$BIN" "$APP/Contents/MacOS/BCLegalAIAssociate"
  cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>BC Legal AI Associate</string>
  <key>CFBundleDisplayName</key><string>BC Legal AI Associate</string>
  <key>CFBundleIdentifier</key><string>ca.bc.legalai.associate</string>
  <key>CFBundleVersion</key><string>0.2.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>BCLegalAIAssociate</string>
  <key>LSMinimumSystemVersion</key><string>12.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST
  chmod +x "$APP/Contents/MacOS/BCLegalAIAssociate"
  echo "OK: $APP"
  echo "Note: unsigned build — Gatekeeper may require right-click → Open."
else
  echo "Build failed — $BIN not found" >&2
  exit 1
fi
