#!/usr/bin/env python3
"""Export Cursor *.plan.md files into workspace plans/YYYY-MM-DD-<slug>.md."""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)
SECRET_RE = re.compile(
    r"(?i)(password|passwd|token|secret|api[_-]?key)\s*[=:]\s*\S+"
)


def redact(text: str) -> str:
    text = SECRET_RE.sub(r"\1=***", text)
    text = re.sub(
        r"(?i)(postgres://[^:]+:)([^@]+)(@)",
        r"\1***\3",
        text,
    )
    return text


def slugify(value: str) -> str:
    value = value.strip().lower().replace("_", "-").replace(" ", "-")
    value = re.sub(r"[^a-z0-9-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "plan"


def parse_day(value: str) -> date:
    return date.fromisoformat(value)


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    meta: dict = {}
    body = raw[match.end() :]
    current_key = None
    current_todo: dict | None = None
    todos: list[dict] = []

    def flush_todo() -> None:
        nonlocal current_todo
        if current_todo is not None:
            todos.append(current_todo)
            current_todo = None

    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if re.match(r"^[a-zA-Z0-9_-]+:", line) and not line.startswith(" "):
            flush_todo()
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            current_key = key
            if key == "todos":
                meta["todos"] = todos
                current_todo = None
            elif rest:
                meta[key] = rest.strip().strip("\"'")
            else:
                meta[key] = ""
            continue

        if current_key == "todos":
            item = re.match(r"^\s*-\s+id:\s*(.+)\s*$", line)
            if item:
                flush_todo()
                current_todo = {"id": item.group(1).strip().strip("\"'")}
                continue
            if current_todo is None:
                continue
            content = re.match(r"^\s+content:\s*(.+)\s*$", line)
            if content:
                val = content.group(1).strip()
                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]
                current_todo["content"] = val
                continue
            status = re.match(r"^\s+status:\s*(.+)\s*$", line)
            if status:
                current_todo["status"] = status.group(1).strip().strip("\"'")
                continue

    flush_todo()
    if todos and "todos" not in meta:
        meta["todos"] = todos
    return meta, body


def render_plan(meta: dict, body: str, saved_on: date, source_name: str) -> str:
    title = str(meta.get("name") or Path(source_name).stem)
    overview = str(meta.get("overview") or "").strip()
    todos = meta.get("todos") if isinstance(meta.get("todos"), list) else []

    lines = [
        f"# Plan — {title}",
        "",
        f"Saved from Cursor plan on {saved_on.isoformat()}.",
        "",
    ]
    if overview:
        lines.extend(["## Overview", "", overview, ""])

    if todos:
        lines.extend(["## Todos", ""])
        for todo in todos:
            if not isinstance(todo, dict):
                continue
            content = str(todo.get("content") or todo.get("id") or "").strip()
            if not content:
                continue
            done = str(todo.get("status") or "").lower() == "completed"
            mark = "x" if done else " "
            lines.append(f"- [{mark}] {content}")
        lines.append("")

    body = body.strip()
    if body:
        # Avoid duplicating an H1 that matches the title.
        body_lines = body.splitlines()
        if body_lines and body_lines[0].startswith("# "):
            first = body_lines[0][2:].strip()
            if first.lower() == title.lower():
                body = "\n".join(body_lines[1:]).lstrip("\n")
        body = body.strip()
        if body:
            if body.lstrip().startswith("#"):
                lines.extend([body, ""])
            else:
                lines.extend(["## Plan", "", body, ""])

    return redact("\n".join(lines).rstrip() + "\n")


def discover_plan_dirs(workspace: Path, extra: Path | None) -> list[Path]:
    dirs: list[Path] = []
    home_plans = Path.home() / ".cursor" / "plans"
    workspace_plans = workspace / ".cursor" / "plans"
    for path in (home_plans, workspace_plans):
        if path.is_dir():
            dirs.append(path)
    if extra is not None and extra.is_dir():
        dirs.append(extra)
    return dirs


def collect_plans(dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in dirs:
        files.extend(sorted(directory.glob("*.plan.md")))
        files.extend(sorted(directory.glob("*.md")))
    # Prefer *.plan.md; also allow plain .md inside plans dirs, but skip SKILL-like noise.
    unique: dict[str, Path] = {}
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        if path.name.lower() in {"readme.md", "skill.md"}:
            continue
        key = path.resolve().as_posix().lower()
        unique[key] = path
    return list(unique.values())


def local_mtime_date(path: Path) -> date:
    return datetime.fromtimestamp(path.stat().st_mtime).date()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Project root (plans/ is written here)",
    )
    parser.add_argument("--today", action="store_true", help="Only plans modified today")
    parser.add_argument("--from", dest="date_from", help="Include plans mtime on/after this day")
    parser.add_argument("--to", dest="date_to", help="Include plans mtime on/before this day")
    parser.add_argument("--name", help="Substring match on plan title or filename")
    parser.add_argument("--all", action="store_true", help="Export all discovered plans")
    parser.add_argument(
        "--plans-dir",
        type=Path,
        help="Extra directory containing *.plan.md files",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    out_dir = workspace / "plans"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.today and not args.all and not args.date_from and not args.name:
        raise SystemExit("Specify --today, --all, --from/--to, and/or --name")

    start = parse_day(args.date_from) if args.date_from else None
    end = parse_day(args.date_to) if args.date_to else None
    if args.today:
        start = date.today()
        end = date.today()
    if start and end and end < start:
        raise SystemExit("--to must be on or after --from")

    name_q = (args.name or "").strip().lower()
    dirs = discover_plan_dirs(workspace, args.plans_dir)
    if not dirs:
        raise SystemExit("No plan directories found (~/.cursor/plans or .cursor/plans)")

    candidates = collect_plans(dirs)
    # Dedupe by slug, keep newest mtime.
    by_slug: dict[str, tuple[Path, dict, str, date]] = {}
    skipped = 0

    for path in candidates:
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        title = str(meta.get("name") or path.stem.replace(".plan", ""))
        slug = slugify(title if meta.get("name") else path.stem.replace(".plan", ""))
        mday = local_mtime_date(path)

        if start and mday < start:
            skipped += 1
            continue
        if end and mday > end:
            skipped += 1
            continue
        if name_q and name_q not in title.lower() and name_q not in path.name.lower():
            skipped += 1
            continue

        prev = by_slug.get(slug)
        if prev is None or mday >= prev[3] and path.stat().st_mtime >= prev[0].stat().st_mtime:
            by_slug[slug] = (path, meta, body, mday)

    if not by_slug:
        print("No matching plans to export")
        print(f"Searched: {', '.join(str(d) for d in dirs)}")
        return 0

    written = 0
    for slug, (path, meta, body, mday) in sorted(
        by_slug.items(), key=lambda item: (item[1][3], item[0])
    ):
        out_path = out_dir / f"{mday.isoformat()}-{slug}.md"
        out_path.write_text(
            render_plan(meta, body, mday, path.name),
            encoding="utf-8",
        )
        written += 1
        print(f"{out_path.name} <- {path}")

    print(f"Wrote {written} file(s) under {out_dir} (filtered out {skipped})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
