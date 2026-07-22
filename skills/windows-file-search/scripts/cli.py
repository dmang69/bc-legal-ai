"""
CLI — Windows file search

  python cli.py search --query "vavilov" --ext .pdf
  python cli.py search --query "modified last week" --export csv
  python cli.py search --query "duplicates" --duplicates --root %USERPROFILE%\\Downloads
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from file_engine import export_results, parse_nl, search  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Windows desktop file/folder search")
    ap.add_argument("--query", "-q", required=True)
    ap.add_argument("--ext", action="append", default=[])
    ap.add_argument("--root", action="append", default=[])
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--export", choices=["csv", "json", "txt"])
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    ap.add_argument("--duplicates", action="store_true")
    ap.add_argument("--max", type=int, default=50)
    ap.add_argument("--no-powershell", action="store_true")
    ap.add_argument("--json", action="store_true", help="print JSON results")
    args = ap.parse_args()

    params = parse_nl(args.query)
    if args.ext:
        params.extension = [e if e.startswith(".") else f".{e}" for e in args.ext]
    if args.root:
        params.root_paths = args.root
    if args.exclude:
        params.exclude_paths = args.exclude
    if args.duplicates:
        params.find_duplicates = True
    params.max_results = args.max
    if args.no_powershell:
        params.use_powershell = False
    if args.export:
        params.export_format = args.export

    results, stats = search(params)

    if args.json:
        print(
            json.dumps(
                {
                    "stats": {
                        "method": stats.method,
                        "files_scanned": stats.files_scanned,
                        "folders_scanned": stats.folders_scanned,
                        "permission_skipped": stats.permission_skipped,
                        "protected_skipped": stats.protected_skipped,
                    },
                    "count": len(results),
                    "results": [r.to_dict() for r in results],
                },
                indent=2,
            )
        )
    else:
        print(
            f"Found {len(results)} | method={stats.method} | "
            f"scanned≈{stats.files_scanned} | perm_skip={stats.permission_skipped} | "
            f"protected_skip={stats.protected_skipped}"
        )
        for r in results:
            snip = f" | {r.content_snippet[:60]}…" if r.content_snippet else ""
            print(f"{r.relevance_score:.2f}\t{r.result_type}\t{r.path}{snip}")

    if params.export_format:
        path = export_results(
            results,
            args.out / f"search_results.{params.export_format}",
            params.export_format,
        )
        print(f"Exported: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
