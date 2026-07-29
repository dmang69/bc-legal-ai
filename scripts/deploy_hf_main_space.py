"""Deploy huggingface-space-static/ to Dmang69/bc-legal-ai and clean clutter."""

from __future__ import annotations

import sys
from pathlib import Path

from huggingface_hub import CommitOperationDelete, HfApi

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "huggingface-space-static"
SPACE_ID = "Dmang69/bc-legal-ai"
KEEP = {"index.html", "README.md", ".gitattributes"}


def token() -> str:
    for p in (
        Path.home() / ".cache" / "huggingface" / "token",
        Path.home() / ".huggingface" / "token",
    ):
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    import os

    t = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN") or "").strip()
    if not t:
        raise SystemExit("No Hugging Face token found")
    return t


def main() -> int:
    if not (DEMO / "index.html").is_file():
        print("missing demo index.html", file=sys.stderr)
        return 1
    api = HfApi(token=token())
    who = api.whoami()
    print("auth as", who.get("name") or who.get("fullname"))

    info = api.space_info(SPACE_ID)
    sdk = (getattr(info, "sdk", None) or "").lower()
    print("space sdk", sdk or "?")
    if sdk and sdk != "static":
        print("refusing: Space is not static", file=sys.stderr)
        return 1

    commit = api.upload_folder(
        folder_path=str(DEMO),
        repo_id=SPACE_ID,
        repo_type="space",
        path_in_repo=".",
        commit_message="fix: deploy full static demo (triage, JR clock, tagger) to main Space",
        allow_patterns=["index.html", "README.md"],
        delete_patterns=["app.py", "requirements.txt", "style.css"],
    )
    print("upload", commit)

    files = api.list_repo_files(repo_id=SPACE_ID, repo_type="space")
    to_delete = [f for f in files if f not in KEEP]
    print("will delete", len(to_delete), "clutter files")
    chunk = 40
    for i in range(0, len(to_delete), chunk):
        batch = to_delete[i : i + chunk]
        ops = [CommitOperationDelete(path_in_repo=f) for f in batch]
        c = api.create_commit(
            repo_id=SPACE_ID,
            repo_type="space",
            operations=ops,
            commit_message=f"chore: remove non-demo static Space files (batch {i // chunk + 1})",
        )
        print("deleted batch", i // chunk + 1, len(batch), c)

    remaining = api.list_repo_files(repo_id=SPACE_ID, repo_type="space")
    print("remaining", remaining)
    print("live", f"https://huggingface.co/spaces/{SPACE_ID}")
    print("host", f"https://dmang69-bc-legal-ai.static.hf.space/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
