#!/usr/bin/env python3
"""Export a Cursor agent transcript (.jsonl) to readable markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SECRET_RE = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|bearer)\s*[:=]\s*\S+"
)
USER_QUERY_RE = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S)
TIMESTAMP_RE = re.compile(r"<timestamp>.*?</timestamp>", re.S)


def newest_jsonl(root: Path) -> Path | None:
    files = sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def extract_text(content) -> tuple[str, list[str]]:
    if isinstance(content, str):
        return content, []
    texts: list[str] = []
    tools: list[str] = []
    if not isinstance(content, list):
        return "", []
    for part in content:
        if not isinstance(part, dict):
            continue
        kind = part.get("type")
        if kind == "text":
            texts.append(str(part.get("text") or ""))
        elif kind == "tool_use":
            name = part.get("name") or "tool"
            tools.append(str(name))
    return "\n\n".join(t for t in texts if t.strip()), tools


def clean_user_text(text: str) -> str:
    text = TIMESTAMP_RE.sub("", text)
    match = USER_QUERY_RE.search(text)
    if match:
        text = match.group(1)
    return text.strip()


def redact(text: str) -> str:
    return SECRET_RE.sub(r"\1: [redacted]", text)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug[:48] or "conversation").strip("-")


def first_user_title(messages: list[dict]) -> str:
    for role, text, _ in messages:
        if role == "user" and text:
            line = text.strip().splitlines()[0]
            line = re.sub(r"[#*_`]+", "", line).strip()
            return line[:72] or "Conversation"
    return "Conversation"


def load_messages(path: Path) -> list[tuple[str, str, list[str]]]:
    out: list[tuple[str, str, list[str]]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = row.get("role") or "unknown"
            msg = row.get("message") or {}
            text, tools = extract_text(msg.get("content"))
            if role == "user":
                text = clean_user_text(text)
            text = redact(text)
            if not text and not tools:
                continue
            out.append((role, text, tools))
    return out


def render(messages: list[tuple[str, str, list[str]]], title: str, source: Path, include_tools: bool) -> str:
    parts = [
        f"# {title}",
        "",
        f"- Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Source: `{source}`",
        "",
    ]
    for role, text, tools in messages:
        heading = "User" if role == "user" else "Assistant" if role == "assistant" else role.title()
        parts.append(f"## {heading}")
        parts.append("")
        if text:
            parts.append(text)
            parts.append("")
        if include_tools and tools:
            parts.append("Tools: " + ", ".join(tools))
            parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a Cursor conversation to markdown")
    parser.add_argument("--transcripts-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path.cwd() / "cursor" / "conversation")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--include-tools", action="store_true")
    args = parser.parse_args()

    root = args.transcripts_dir.expanduser()
    if not root.is_dir():
        print(f"No transcript folder: {root}", file=sys.stderr)
        return 2

    source = newest_jsonl(root)
    if source is None:
        print(f"No .jsonl transcripts in {root}", file=sys.stderr)
        return 2

    messages = load_messages(source)
    if not messages:
        print(f"Transcript is empty: {source}", file=sys.stderr)
        return 2

    title = args.title or first_user_title(messages)
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    dest = (
        args.out.expanduser()
        if args.out
        else args.out_dir.expanduser() / f"{stamp}.md"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(messages, title, source, args.include_tools), encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
