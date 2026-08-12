#!/usr/bin/env python3
"""Export Cursor agent chat transcripts into conversions/YYYY-MM-DD.md.

Includes assistant replies plus a Commands & resources section derived from
tool_use blocks (Shell commands, WebSearch, Grep/Glob/Read lookups, etc.).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

TS_RE = re.compile(r"<timestamp>(.*?)</timestamp>", re.S)
QUERY_RE = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S)
SYSTEM_NOTIFY = re.compile(r"<system_notification>.*?</system_notification>", re.S)
SKILLS_ATTACH = re.compile(
    r"<manually_attached_skills>.*?</manually_attached_skills>",
    re.S,
)
MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

# Tool names worth recording for "how resources were found" / commands used.
RESOURCE_TOOLS = {
    "Shell",
    "WebSearch",
    "WebFetch",
    "Grep",
    "Glob",
    "Read",
    "GetMcpTools",
    "FetchMcpResource",
    "CallMcpTool",
    "Task",
}

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


def extract_text_blocks(message: dict) -> list[str]:
    content = message.get("content") if isinstance(message, dict) else None
    texts: list[str] = []
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                t = (part.get("text") or "").strip()
                if t:
                    texts.append(t)
            elif isinstance(part, str) and part.strip():
                texts.append(part.strip())
    elif isinstance(content, str) and content.strip():
        texts.append(content.strip())
    return texts


def extract_tool_uses(message: dict) -> list[dict]:
    content = message.get("content") if isinstance(message, dict) else None
    tools: list[dict] = []
    if not isinstance(content, list):
        return tools
    for part in content:
        if not isinstance(part, dict) or part.get("type") != "tool_use":
            continue
        name = part.get("name") or ""
        if name not in RESOURCE_TOOLS:
            continue
        inp = part.get("input") if isinstance(part.get("input"), dict) else {}
        tools.append({"name": name, "input": inp})
    return tools


def summarize_tool(tool: dict) -> str | None:
    """One-line summary of a tool use for the markdown log."""
    name = tool["name"]
    inp = tool["input"]

    def short(value: object, limit: int = 160) -> str:
        s = redact(str(value or "")).replace("\n", " ").strip()
        if len(s) > limit:
            s = s[: limit - 1].rstrip() + "…"
        return s

    if name == "Shell":
        cmd = short(inp.get("command"), 200)
        desc = (inp.get("description") or "").strip()
        if desc:
            return f"`Shell`: `{cmd}` — {desc}"
        return f"`Shell`: `{cmd}`"

    if name == "WebSearch":
        term = short(inp.get("search_term"), 120)
        why = (inp.get("explanation") or "").strip()
        if why:
            return f"`WebSearch`: `{term}` — {why}"
        return f"`WebSearch`: `{term}`"

    if name == "WebFetch":
        return f"`WebFetch`: {short(inp.get('url'), 180)}"

    if name == "Grep":
        pattern = short(inp.get("pattern"), 80)
        path = short(inp.get("path") or inp.get("glob") or ".", 100)
        return f"`Grep`: `{pattern}` in `{path}`"

    if name == "Glob":
        pattern = short(inp.get("glob_pattern"), 100)
        target = short(inp.get("target_directory") or ".", 100)
        return f"`Glob`: `{pattern}` under `{target}`"

    if name == "Read":
        return f"`Read`: `{short(inp.get('path'), 160)}`"

    if name == "GetMcpTools":
        server = (inp.get("server") or "").strip()
        tool_name = (inp.get("toolName") or "").strip()
        pattern = (inp.get("pattern") or "").strip()
        parts: list[str] = []
        if server:
            parts.append(f"server=`{server}`")
        if tool_name:
            parts.append(f"tool=`{tool_name}`")
        if pattern:
            parts.append(f"pattern=`{short(pattern, 80)}`")
        if not parts:
            return "`GetMcpTools`: catalog"
        return "`GetMcpTools`: " + ", ".join(parts)

    if name == "FetchMcpResource":
        server = inp.get("server") or "?"
        uri = short(inp.get("uri"), 120)
        return f"`FetchMcpResource`: {server} → `{uri}`"

    if name == "CallMcpTool":
        server = inp.get("server") or "?"
        tool_name = inp.get("toolName") or inp.get("tool") or "?"
        desc = (inp.get("description") or "").strip()
        # mcp_auth and similar: note when authenticating a server
        if tool_name == "mcp_auth" or str(tool_name).endswith("mcp_auth"):
            return f"`CallMcpTool`: {server}/mcp_auth — authenticate MCP server"
        if desc:
            return f"`CallMcpTool`: {server}/{tool_name} — {desc}"
        args = inp.get("arguments")
        if isinstance(args, dict) and args:
            keys = ", ".join(sorted(str(k) for k in list(args.keys())[:6]))
            return f"`CallMcpTool`: {server}/{tool_name} (args: {keys})"
        return f"`CallMcpTool`: {server}/{tool_name}"

    if name == "Task":
        desc = short(inp.get("description") or inp.get("subagent_type") or "task", 120)
        return f"`Task`: {desc}"

    return None


def dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def parse_user_day_and_query(text: str) -> tuple[str | None, str | None, str | None]:
    # Skill attachments can include literal <user_query> examples — strip them first.
    text = SKILLS_ATTACH.sub("", text)

    timestamps = TS_RE.findall(text)
    queries = QUERY_RE.findall(text)
    day = None
    time_part = None
    if timestamps:
        raw = timestamps[-1].strip()
        time_part = raw
        m = re.search(
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})",
            raw,
        )
        if m:
            day = date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2))).isoformat()
    query = queries[-1].strip() if queries else None
    return day, time_part, query


def clean_assistant(text: str) -> str:
    text = SYSTEM_NOTIFY.sub("", text)
    return text.replace("[REDACTED]", "").strip()


def find_transcript_root(workspace: Path) -> Path | None:
    # Cursor stores transcripts under ~/.cursor/projects/<slug>/agent-transcripts
    projects = Path.home() / ".cursor" / "projects"
    if not projects.is_dir():
        return None

    workspace = workspace.resolve()
    candidates: list[Path] = []
    for project_dir in projects.iterdir():
        transcripts = project_dir / "agent-transcripts"
        if not transcripts.is_dir():
            continue
        # Prefer slug that looks like this workspace path
        slug = project_dir.name
        normalized = str(workspace).lstrip("/").replace("/", "-").replace("\\", "-")
        # Windows: D:\foo\bar -> d-foo-bar style slug often used by Cursor
        win_slug = re.sub(r"^([A-Za-z]):\\", r"\1-", str(workspace)).replace("\\", "-")
        if (
            slug == normalized
            or slug == win_slug
            or slug.endswith(workspace.name)
            or workspace.name.lower() in slug.lower()
        ):
            candidates.append(transcripts)

    if candidates:
        # Prefer exact / closest match
        for c in candidates:
            if workspace.name.lower() in c.parent.name.lower():
                return c
        return candidates[0]

    # Fallback: any project with newest transcript mtime
    best = None
    best_mtime = -1.0
    for project_dir in projects.iterdir():
        transcripts = project_dir / "agent-transcripts"
        if not transcripts.is_dir():
            continue
        for f in transcripts.glob("*/*.jsonl"):
            if "subagents" in str(f):
                continue
            mtime = f.stat().st_mtime
            if mtime > best_mtime:
                best_mtime = mtime
                best = transcripts
    return best


def load_turns(transcript_root: Path) -> dict[str, list[dict]]:
    by_day: dict[str, list[dict]] = defaultdict(list)

    for f in sorted(transcript_root.glob("*/*.jsonl")):
        if "subagents" in str(f):
            continue

        pending = None
        chunks: list[str] = []
        tool_lines: list[str] = []

        def flush() -> None:
            nonlocal pending, chunks, tool_lines
            if not pending:
                chunks = []
                tool_lines = []
                return
            day = pending["day"] or "unknown"
            by_day[day].append(
                {
                    "time": pending["time"],
                    "user": pending["query"],
                    "assistant": "\n\n".join(chunks).strip(),
                    "tools": dedupe_preserve(tool_lines),
                }
            )
            pending = None
            chunks = []
            tool_lines = []

        with f.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                role = obj.get("role")
                message = obj.get("message") or {}
                texts = extract_text_blocks(message)
                if role == "user":
                    flush()
                    full = "\n".join(texts)
                    day, time_part, query = parse_user_day_and_query(full)
                    if not query:
                        continue
                    pending = {"day": day, "time": time_part, "query": query}
                    chunks = []
                    tool_lines = []
                elif role == "assistant" and pending:
                    for t in texts:
                        t = clean_assistant(t)
                        if t:
                            chunks.append(t)
                    for tool in extract_tool_uses(message):
                        summary = summarize_tool(tool)
                        if summary:
                            tool_lines.append(summary)
        flush()

    return by_day


STUB_MARKER = "_No chat transcript found for this day in agent history._"


def is_stub_file(path: Path) -> bool:
    """True if the markdown looks like an empty-day stub from a prior export."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return STUB_MARKER in text


def render_day(day: str, turns: list[dict], *, include_tools: bool = True) -> str:
    lines = [
        f"# Conversation — {day}",
        "",
        "Chat record with Cursor agent.",
        "",
    ]
    for i, turn in enumerate(turns, 1):
        when = turn["time"] or day
        lines.append(f"## {i}. {when}")
        lines.append("")
        lines.append("### You")
        lines.append("")
        lines.append(turn["user"])
        lines.append("")
        lines.append("### Assistant")
        lines.append("")
        reply = turn["assistant"] or "_No text reply recorded (tools-only turn)._"
        if len(reply) > 5000:
            reply = reply[:5000].rstrip() + "\n\n… _(truncated)_"
        lines.append(reply)
        lines.append("")

        tools = turn.get("tools") or []
        if include_tools and tools:
            lines.append("### Commands & resources")
            lines.append("")
            # Cap very long tool lists
            shown = tools[:80]
            for item in shown:
                lines.append(f"- {item}")
            if len(tools) > len(shown):
                lines.append(f"- … _({len(tools) - len(shown)} more omitted)_")
            lines.append("")

        lines.append("---")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_day(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--from", dest="date_from", required=True, help="YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", default=None, help="YYYY-MM-DD (default: today)")
    parser.add_argument(
        "--transcripts",
        type=Path,
        default=None,
        help="Override agent-transcripts directory",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Omit Commands & resources sections",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    out_dir = workspace / "conversions"
    out_dir.mkdir(parents=True, exist_ok=True)

    transcript_root = args.transcripts or find_transcript_root(workspace)
    if transcript_root is None or not transcript_root.is_dir():
        raise SystemExit(
            "Could not find agent-transcripts. Pass --transcripts /path/to/agent-transcripts"
        )

    start = parse_day(args.date_from)
    end = parse_day(args.date_to) if args.date_to else date.today()
    if end < start:
        raise SystemExit("--to must be on or after --from")

    by_day = load_turns(transcript_root)
    include_tools = not args.no_tools

    d = start
    written = 0
    skipped = 0
    removed_stubs = 0
    while d <= end:
        key = d.isoformat()
        out_path = out_dir / f"{key}.md"
        turns = by_day.get(key, [])
        if not turns:
            # Do not create empty-day files; clean up prior stubs only.
            if out_path.is_file() and is_stub_file(out_path):
                out_path.unlink()
                removed_stubs += 1
                print(f"{key}: no chat (removed stub)")
            else:
                skipped += 1
                print(f"{key}: no chat (skipped)")
            d += timedelta(days=1)
            continue

        out_path.write_text(
            render_day(key, turns, include_tools=include_tools),
            encoding="utf-8",
        )
        written += 1
        tool_count = sum(len(t.get("tools") or []) for t in turns)
        print(f"{key}: {len(turns)} turns ({tool_count} tool entries)")
        d += timedelta(days=1)

    print(
        f"Wrote {written} file(s) under {out_dir}"
        f" (skipped {skipped} empty day(s), removed {removed_stubs} stub(s))"
    )
    print(f"Transcripts: {transcript_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
