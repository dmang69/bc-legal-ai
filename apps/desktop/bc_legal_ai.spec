# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Windows .exe / macOS binary
# Build from monorepo root:
#   pyinstaller apps/desktop/bc_legal_ai.spec

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(root / "platform" / "desktop" / "launcher.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "frontend" / "client"), "frontend/client"),
        (str(root / "architecture" / "contracts"), "architecture/contracts"),
    ],
    hiddenimports=[
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "pydantic",
        "backend.api.main",
        "backend.api.state",
        "services",
        "architecture",
        "knowledgebase",
        "middleware",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="BCLegalAIAssociate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
