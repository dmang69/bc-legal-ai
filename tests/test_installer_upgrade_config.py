"""Installer / upgrade configuration must stay consistent for in-place upgrades."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "apps" / "desktop-mobile"
TAURI = DESKTOP / "src-tauri"


def test_upgrade_config_script_passes():
    script = DESKTOP / "scripts" / "verify-upgrade-config.mjs"
    assert script.is_file()
    r = subprocess.run(
        [sys.executable and "node", str(script)],
        cwd=str(DESKTOP),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout + "\n" + r.stderr
    assert "PASS" in r.stdout


def test_versions_and_stable_identity():
    conf = json.loads((TAURI / "tauri.conf.json").read_text(encoding="utf-8"))
    cargo = (TAURI / "Cargo.toml").read_text(encoding="utf-8")
    pkg = json.loads((DESKTOP / "package.json").read_text(encoding="utf-8"))
    assert conf["identifier"] == "ca.bclegalai.associate"
    assert conf["productName"] == "BC Legal AI Associate"
    assert conf["version"] == pkg["version"]
    assert f'version = "{conf["version"]}"' in cargo
    assert conf["bundle"].get("createUpdaterArtifacts") in (True, False)
    updater = conf["plugins"]["updater"]
    assert updater.get("pubkey")
    assert any("latest.json" in e for e in updater["endpoints"])
    assert updater.get("windows", {}).get("installMode")


def test_windows_nsis_upgrade_surface():
    win = json.loads((TAURI / "tauri.windows.conf.json").read_text(encoding="utf-8"))
    assert "nsis" in win["bundle"]["targets"]
    assert "msi" in win["bundle"]["targets"]
    mode = win["bundle"]["windows"]["nsis"]["installMode"]
    assert mode in ("currentUser", "perUser", "perMachine")
    code = win["bundle"]["windows"]["wix"]["upgradeCode"]
    assert len(code) == 36


def test_pwa_manifest_installable():
    man = json.loads(
        (ROOT / "apps" / "platform-ui" / "public" / "manifest.webmanifest").read_text(
            encoding="utf-8"
        )
    )
    assert man["display"] == "standalone"
    assert man["start_url"]
    index = (ROOT / "apps" / "platform-ui" / "index.html").read_text(encoding="utf-8")
    assert 'rel="manifest"' in index
