"""
CLI for legal-file-assistant: court download + local search.

Examples:
  python cli.py download --citation "2019 SCC 65" --out ../outputs
  python cli.py search --query "vavilov" --ext .pdf
  python cli.py both --citation "2019 SCC 65" --query vavilov
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# allow running from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from court_engine import download_batch  # noqa: E402
from file_engine import export_results, parse_nl, search  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Court download + Windows file search")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download", help="Download court document(s)")
    d.add_argument("--citation", action="append", required=True)
    d.add_argument("--name", action="append", default=[])
    d.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")

    s = sub.add_parser("search", help="Local file search")
    s.add_argument("--query", required=True)
    s.add_argument("--ext", action="append", default=[])
    s.add_argument("--root", action="append", default=[])
    s.add_argument("--export", choices=["csv", "json", "txt"])
    s.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    s.add_argument("--duplicates", action="store_true")

    b = sub.add_parser("both", help="Search local then download if missing")
    b.add_argument("--citation", required=True)
    b.add_argument("--query", default="")
    b.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")

    args = ap.parse_args()

    if args.cmd == "download":
        cases = []
        for i, cit in enumerate(args.citation):
            name = args.name[i] if i < len(args.name) else None
            cases.append({"citation": cit, "name": name, "tab": i + 1})
        results = download_batch(cases, args.out)
        print(json.dumps([r.to_dict() for r in results], indent=2))
        return 0

    if args.cmd == "search":
        params = parse_nl(args.query)
        if args.ext:
            params.extension = [e if e.startswith(".") else f".{e}" for e in args.ext]
        if args.root:
            params.root_paths = args.root
        if args.duplicates:
            params.find_duplicates = True
        results = search(params)
        for r in results:
            print(f"{r.relevance_score:.2f}\t{r.path}")
        if args.export:
            path = export_results(
                results, args.out / f"file_search.{args.export}", args.export
            )
            print(f"Exported: {path}")
        return 0

    if args.cmd == "both":
        q = args.query or args.citation
        params = parse_nl(q)
        params.extension = [".pdf"]
        found = search(params)
        print(f"LOCAL hits: {len(found)}")
        for r in found[:5]:
            print(f"  {r.path}")
        if not found:
            print("Not found locally — downloading…")
            download_batch(
                [{"citation": args.citation, "tab": 1}],
                args.out,
            )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
