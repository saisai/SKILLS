#!/usr/bin/env python3
"""Save a Cursor Plan markdown file into the current working directory."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SECRET_RE = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|bearer)\s*[:=]\s*\S+"
)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.M)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug[:48] or "plan").strip("-")


def redact(text: str) -> str:
    return SECRET_RE.sub(r"\1: [redacted]", text)


def first_title(text: str, fallback: str) -> str:
    match = TITLE_RE.search(text)
    if match:
        return match.group(1).strip()
    line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    return line[:72] or fallback


def newest_plan(roots: list[Path]) -> Path | None:
    files: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        files.extend(root.rglob("*.md"))
        files.extend(root.rglob("*.plan.md"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a Cursor plan to markdown")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path.cwd() / "plans")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--search-dir", type=Path, action="append", default=[])
    args = parser.parse_args()

    source: Path | None = args.source.expanduser() if args.source else None
    if args.stdin:
        body = sys.stdin.read()
        origin = "stdin"
    else:
        if source is None:
            search = [p.expanduser() for p in args.search_dir] or [
                Path.cwd() / ".cursor" / "plans",
            ]
            source = newest_plan(search)
        if source is None or not source.is_file():
            print("No Cursor Plan file found.", file=sys.stderr)
            return 2
        body = source.read_text(encoding="utf-8")
        origin = str(source)

    body = redact(body).strip() + "\n"
    if body.strip() == "":
        print("Plan is empty.", file=sys.stderr)
        return 2

    title = args.title or first_title(body, "Plan")
    dest = (
        args.out.expanduser()
        if args.out
        else args.out_dir.expanduser() / f"{date.today().isoformat()}-{slugify(title)}.md"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not body.lstrip().startswith("#"):
        body = f"# {title}\n\n- Saved: {date.today().isoformat()}\n- Source: `{origin}`\n\n{body}"
    dest.write_text(body, encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
