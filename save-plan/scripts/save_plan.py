#!/usr/bin/env python3
"""Export a Cursor Plan (.plan.md) into the project's plans/ archive format."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)
NAME_RE = re.compile(r"(?m)^name:\s*(.+?)\s*$")
OVERVIEW_RE = re.compile(r"(?m)^overview:\s*(.+?)\s*$")
# Multiline overview with quotes
OVERVIEW_BLOCK_RE = re.compile(
    r"(?ms)^overview:\s*[>|]?-?\s*\n((?:[ \t].+\n?)+)"
    r"|^overview:\s*[\"'](.+?)[\"']\s*$"
    r"|^overview:\s*(.+?)\s*$",
)
TODO_ITEM_RE = re.compile(
    r"(?ms)^[ \t]*-[ \t]+id:\s*(.+?)\s*\n"
    r"[ \t]+content:\s*(?P<q>[\"']?)(?P<content>.*?)(?P=q)\s*\n"
    r"[ \t]+status:\s*(?P<status>\w+)\s*$"
)
HEADING_RE = re.compile(r"(?m)^#\s+(.+?)\s*$")


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug[:64] or "plan").strip("-")


def newest_plan(roots: list[Path]) -> Path | None:
    files: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        files.extend(root.glob("*.plan.md"))
        files.extend(root.glob("*.md"))
    # Prefer *.plan.md; fall back to any md already collected from plans dirs
    plan_files = [p for p in files if p.name.endswith(".plan.md")]
    candidates = plan_files or files
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def parse_overview(fm: str) -> str:
    block = OVERVIEW_BLOCK_RE.search(fm)
    if not block:
        return ""
    if block.group(1):
        lines = [ln.strip() for ln in block.group(1).splitlines() if ln.strip()]
        return " ".join(lines)
    return (block.group(2) or block.group(3) or "").strip().strip("\"'")


def parse_todos(fm: str) -> list[tuple[str, str]]:
    todos: list[tuple[str, str]] = []
    for match in TODO_ITEM_RE.finditer(fm):
        content = match.group("content").strip()
        # Unescape simple YAML double-quoted content
        content = content.replace('\\"', '"')
        status = match.group("status").strip().lower()
        todos.append((content, status))
    return todos


def parse_plan(text: str) -> tuple[str, str, list[tuple[str, str]], str]:
    """Return title, overview, todos, body."""
    fm = ""
    body = text
    match = FRONTMATTER_RE.match(text)
    if match:
        fm = match.group(1)
        body = text[match.end() :]

    name = ""
    name_match = NAME_RE.search(fm)
    if name_match:
        name = name_match.group(1).strip().strip("\"'")

    overview = parse_overview(fm)
    todos = parse_todos(fm)

    heading = ""
    head_match = HEADING_RE.search(body)
    if head_match:
        heading = head_match.group(1).strip()
        # Drop the first H1 from body so we can rewrite it
        body = body[: head_match.start()] + body[head_match.end() :]
        body = body.lstrip("\n")

    title = name or heading or "Untitled plan"
    return title, overview, todos, body.strip() + ("\n" if body.strip() else "")


def status_checkbox(status: str) -> str:
    if status in {"completed", "complete", "done", "cancelled", "canceled"}:
        return "[x]"
    return "[ ]"


def render(
    title: str,
    overview: str,
    todos: list[tuple[str, str]],
    body: str,
    saved_on: str,
) -> str:
    parts = [
        f"# Plan — {title}",
        "",
        f"Saved from Cursor plan on {saved_on}.",
        "",
    ]
    if overview:
        parts.extend(["## Overview", "", overview, ""])
    if todos:
        parts.append("## Todos")
        parts.append("")
        for content, status in todos:
            mark = status_checkbox(status)
            # Preserve cancelled distinction lightly
            if status in {"cancelled", "canceled"}:
                parts.append(f"- {mark} ~~{content}~~")
            else:
                parts.append(f"- {mark} {content}")
        parts.append("")
    if body.strip():
        # Avoid duplicating Overview/Todos if body already has them after strip
        parts.append(body.strip())
        parts.append("")
    return "\n".join(parts)


def unique_dest(out_dir: Path, date_slug: str) -> Path:
    dest = out_dir / f"{date_slug}.md"
    if not dest.exists():
        return dest
    stamp = datetime.now().strftime("%H%M%S")
    return out_dir / f"{date_slug}-{stamp}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a Cursor plan to markdown")
    parser.add_argument(
        "--plans-dir",
        type=Path,
        default=Path.home() / ".cursor" / "plans",
    )
    parser.add_argument("--also-dir", type=Path, action="append", default=[])
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path.cwd() / "plans")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title")
    args = parser.parse_args()

    if args.source:
        source = args.source.expanduser()
        if not source.is_file():
            print(f"Plan file not found: {source}", file=sys.stderr)
            return 2
    else:
        roots = [args.plans_dir.expanduser()]
        roots.extend(p.expanduser() for p in args.also_dir)
        source = newest_plan(roots)
        if source is None:
            print(
                "No Cursor plan files found. Open or create a plan in Plan mode, then retry.",
                file=sys.stderr,
            )
            return 2

    raw = source.read_text(encoding="utf-8")
    title, overview, todos, body = parse_plan(raw)
    if args.title:
        title = args.title.strip() or title

    saved_on = datetime.now().strftime("%Y-%m-%d")
    date_slug = f"{saved_on}-{slugify(title)}"

    dest = (
        args.out.expanduser()
        if args.out
        else unique_dest(args.out_dir.expanduser(), date_slug)
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        render(title, overview, todos, body, saved_on),
        encoding="utf-8",
    )
    print(dest)
    print(f"title={title}")
    print(f"todos={len(todos)}")
    print(f"source={source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
