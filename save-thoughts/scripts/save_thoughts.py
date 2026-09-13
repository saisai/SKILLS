#!/usr/bin/env python3
"""Export assistant thoughts and commands from a Cursor transcript."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

SECRET_RE = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|bearer)\s*[:=]\s*\S+"
)
USER_QUERY_RE = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S)
TIMESTAMP_RE = re.compile(r"<timestamp>.*?</timestamp>", re.S)


def newest_jsonl(root: Path) -> Path | None:
    files = sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def redact(text: str) -> str:
    return SECRET_RE.sub(r"\1: [redacted]", text)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug[:48] or "thoughts").strip("-")


def first_user_title(rows: list[dict]) -> str:
    for row in rows:
        if row.get("role") != "user":
            continue
        text = extract_text(row)
        if not text:
            continue
        text = TIMESTAMP_RE.sub("", text)
        match = USER_QUERY_RE.search(text)
        if match:
            text = match.group(1)
        line = re.sub(r"[#*_`]+", "", text.strip().splitlines()[0]).strip()
        return line[:72] or "Thoughts and commands"
    return "Thoughts and commands"


def extract_text(row: dict) -> str:
    content = (row.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = [p.get("text") or "" for p in content if isinstance(p, dict) and p.get("type") == "text"]
    return "\n\n".join(p for p in parts if p.strip())


def collect(path: Path, include_other: bool) -> tuple[list[str], list[dict], list[str], list[dict]]:
    thoughts: list[str] = []
    commands: list[dict] = []
    other: list[str] = []
    with path.open(encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    for row in rows:
        if row.get("role") != "assistant":
            continue
        text = extract_text(row).strip()
        if text:
            thoughts.append(redact(text))
        content = (row.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "tool_use":
                continue
            name = part.get("name") or "tool"
            inp = part.get("input") or {}
            if name == "Shell":
                commands.append(
                    {
                        "description": redact(str(inp.get("description") or "")),
                        "command": redact(str(inp.get("command") or "")),
                    }
                )
            elif include_other:
                other.append(name)
    return thoughts, commands, other, rows


def render(title: str, source: Path, thoughts: list[str], commands: list[dict], other: list[str]) -> str:
    parts = [
        f"# {title}",
        "",
        f"- Saved: {date.today().isoformat()}",
        f"- Source: `{source}`",
        f"- Thoughts: {len(thoughts)}",
        f"- Commands: {len(commands)}",
        "",
        "## Thoughts",
        "",
    ]
    if not thoughts:
        parts.append("_No assistant thoughts in this transcript._")
        parts.append("")
    else:
        for i, thought in enumerate(thoughts, 1):
            parts.append(f"### {i}")
            parts.append("")
            parts.append(thought)
            parts.append("")
    parts.extend(["## Commands used", ""])
    if not commands:
        parts.append("_No shell commands in this transcript._")
        parts.append("")
    else:
        for i, cmd in enumerate(commands, 1):
            desc = cmd["description"] or "command"
            parts.append(f"### {i}. {desc}")
            parts.append("")
            parts.append("```bash")
            parts.append(cmd["command"].rstrip() or "# (empty)")
            parts.append("```")
            parts.append("")
    if other:
        parts.extend(["## Other tools", "", ", ".join(other), ""])
    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Save Cursor thoughts and commands")
    parser.add_argument("--transcripts-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path.cwd() / "thoughts")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--include-other-tools", action="store_true")
    args = parser.parse_args()

    root = args.transcripts_dir.expanduser()
    if not root.is_dir():
        print(f"No transcript folder: {root}", file=sys.stderr)
        return 2
    source = newest_jsonl(root)
    if source is None:
        print(f"No .jsonl transcripts in {root}", file=sys.stderr)
        return 2

    thoughts, commands, other, rows = collect(source, args.include_other_tools)
    if not thoughts and not commands:
        print(f"No thoughts or commands in {source}", file=sys.stderr)
        return 2

    title = args.title or first_user_title(rows)
    dest = (
        args.out.expanduser()
        if args.out
        else args.out_dir.expanduser() / f"{date.today().isoformat()}-{slugify(title)}.md"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(title, source, thoughts, commands, other), encoding="utf-8")
    print(dest)
    print(f"thoughts={len(thoughts)} commands={len(commands)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
