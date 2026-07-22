#!/usr/bin/env bash
# Dev install (no .app) — macOS: Applications symlink + LaunchAgent optional
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3 -m pip install -q "fastapi>=0.115" "uvicorn[standard]>=0.30" "pydantic>=2" "pywebview>=5.0" "gradio>=4.44"

WRAPPER="$HOME/Applications/BC Legal AI Associate.command"
mkdir -p "$HOME/Applications"
cat > "$WRAPPER" <<EOF
#!/bin/bash
cd "$ROOT"
exec python3 apps/desktop/launcher.py
EOF
chmod +x "$WRAPPER"
echo "Installed: $WRAPPER"
echo "Or run: python3 apps/desktop/launcher.py"
