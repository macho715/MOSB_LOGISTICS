from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd))
    subprocess.check_call(cmd)


def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Initialize Cursor workspace + hooks (high-autonomy safe defaults).")
    p.add_argument("--apply-precommit", action="store_true")
    p.add_argument("--apply-ci", action="store_true")
    p.add_argument("--apply-workspace", action="store_true")
    p.add_argument("--apply-all", action="store_true")
    args = p.parse_args()

    apply_pre = args.apply_all or args.apply_precommit
    apply_ci = args.apply_all or args.apply_ci
    apply_ws = args.apply_all or args.apply_workspace

    # Workspace config is already in pack; keep it idempotent.
    if apply_ws:
        print("Workspace config present: .cursor/config/workspace.json")

    if apply_pre:
        # Install pre-commit hooks if available.
        try:
            run(["pre-commit", "install"])
            run(["pre-commit", "install", "--hook-type", "commit-msg"])
        except FileNotFoundError:
            print("pre-commit not installed. Run: pip install pre-commit")
        except subprocess.CalledProcessError as e:
            print(f"pre-commit install failed: {e}")

    if apply_ci:
        print("CI workflow present: .github/workflows/ci.yml")

    # Optional: initialize git if not already.
    if not (Path(".git").exists()):
        try:
            run(["git", "init", "-b", "main"])
        except Exception as e:
            print(f"git init skipped/failed: {e}")

    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
