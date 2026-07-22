"""
BC Legal AI Associate — desktop shell launcher.

Starts the local FastAPI server and opens a native window (pywebview)
or the default browser. Used as the entrypoint for Windows .exe / macOS .app.

Not legal advice. Local prototype — do not use for unredacted client files
without private security controls.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _repo_root() -> Path:
    # packaged: next to exe; dev: monorepo root (apps/desktop/../../)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _free_port(preferred: int = 8765) -> int:
    for port in range(preferred, preferred + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred


def _ensure_path(root: Path) -> None:
    r = str(root)
    if r not in sys.path:
        sys.path.insert(0, r)


def run_server(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        log_level="info",
        reload=False,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BC Legal AI Associate desktop launcher")
    parser.add_argument("--port", type=int, default=0, help="Port (0 = auto)")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Force system browser instead of pywebview",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host (default loopback only)",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    os.chdir(root)
    _ensure_path(root)

    port = args.port or _free_port(8765)
    url = f"http://{args.host}:{port}/"

    t = threading.Thread(
        target=run_server, args=(args.host, port), daemon=True, name="uvicorn"
    )
    t.start()

    # wait for health
    import urllib.request

    for _ in range(60):
        try:
            with urllib.request.urlopen(url + "health", timeout=0.5) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.25)
    else:
        print("Server failed to start. Check dependencies: fastapi uvicorn", file=sys.stderr)
        return 1

    use_browser = args.browser or os.environ.get("BC_LEGAL_AI_BROWSER") == "1"
    if not use_browser:
        try:
            import webview  # type: ignore

            webview.create_window(
                "BC Legal AI Associate",
                url,
                width=1100,
                height=780,
                min_size=(800, 600),
            )
            webview.start()
            return 0
        except Exception as e:
            print(f"pywebview unavailable ({e}); opening system browser.", file=sys.stderr)
            use_browser = True

    if use_browser:
        webbrowser.open(url)
        print(f"BC Legal AI Associate running at {url}")
        print("Press Ctrl+C to stop.")
        try:
            while t.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nShutting down.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
