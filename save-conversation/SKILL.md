---
name: save-conversation
description: >-
  Saves Cursor chat turns into dated markdown under conversions/YYYY-MM-DD.md,
  including Shell commands and how resources were found (WebSearch, Grep, Glob,
  Read, etc.). Use when the user asks to save, update, export, or rebuild
  conversation records, chat logs, conversions notes, or daily conversation
  markdown.
---

# Save Conversation

Persist chat with the agent as markdown in the project workspace.

## Defaults

| Setting | Value |
|---------|--------|
| Folder | `conversions/` at the workspace root |
| Filename | `YYYY-MM-DD.md` (local calendar day the chat happened) |
| Source (save today) | Current conversation (You ↔ Assistant text + tools used) |
| Source (rebuild) | Agent transcript JSONL under the Cursor project `agent-transcripts/` |

Create `conversions/` if missing. Do **not** invent chats or write stub files for days with no transcript.

## When to use

- “Save today’s conversation”
- “Update conversions”
- “Rebuild conversation records from Jul 18”
- “Export this chat to markdown”

## Save / update today

1. Resolve today’s date as `YYYY-MM-DD` (prefer the user’s local date from context).
2. Path: `conversions/YYYY-MM-DD.md`
3. Write or refresh the file using the format below.
4. Prefer appending new turns if the file already exists and earlier turns are still accurate; otherwise rewrite the full day from transcripts (see Rebuild).
5. For each turn, include a **Commands & resources** section listing notable tools used (Shell commands, WebSearch queries, Grep/Glob/Read lookups). Redact secrets.
6. Briefly tell the user the path written.

### Format

```markdown
# Conversation — YYYY-MM-DD

Chat record with Cursor agent.

## 1. <timestamp or time>

### You

<user message>

### Assistant

<assistant text reply; omit tool-call noise; keep useful final answers>

### Commands & resources

- `Shell`: `<command>` — <short description>
- `WebSearch`: `<search term>` — <why it was used>
- `Grep`: `<pattern>` in `<path>`
- `Glob`: `<pattern>` under `<dir>`
- `Read`: `<path>`
- `WebFetch`: <url>

---
```

Number turns `1.`, `2.`, … in chronological order.

### What to record under Commands & resources

| Tool | Record |
|------|--------|
| `Shell` | Command (truncated if long) + description |
| `WebSearch` | Search term + explanation |
| `WebFetch` | URL |
| `Grep` / `Glob` | Pattern and path/directory |
| `Read` | File path |
| `GetMcpTools` | Server / tool name / pattern used to discover MCP tools |
| `CallMcpTool` | Server + tool name (+ description or arg keys); `mcp_auth` noted as auth |
| `FetchMcpResource` | Server + resource URI |
| `Task` | Subagent description |

Skip noisy edit payloads (`Write`/`StrReplace` file bodies). Prefer paths only if you mention writes at all. Deduplicate identical lines. Cap at ~80 entries per turn.

## Rebuild from transcripts

When the user asks to rebuild a date range (e.g. from Jul 18):

1. Run the helper script (preferred) or equivalent logic:

```bash
python3 ~/.cursor/skills/save-conversation/scripts/export_transcripts.py \
  --workspace "$PWD" \
  --from YYYY-MM-DD \
  --to YYYY-MM-DD
```

On Windows (PowerShell):

```powershell
python "$env:USERPROFILE\.cursor\skills\save-conversation\scripts\export_transcripts.py" `
  --workspace "$PWD" `
  --from YYYY-MM-DD `
  --to YYYY-MM-DD
```

Omit tools with `--no-tools` if needed.

2. The script:
   - Reads parent chat JSONL only (skips `subagents/`)
   - Parses `<timestamp>` + `<user_query>` from user messages
   - Collects `tool_use` blocks (`Shell`, `WebSearch`, `Grep`, `Glob`, `Read`, `GetMcpTools`, `CallMcpTool`, `FetchMcpResource`, …) into **Commands & resources**
   - Groups by calendar day
   - Writes `conversions/YYYY-MM-DD.md` only for days that have at least one chat turn
   - Skips days with no transcript (does **not** create stub files)
   - Removes an existing file for an empty day only if it is a prior “no chat found” stub; leaves rich day files alone
   - Redacts common secrets in commands/URLs (passwords, tokens, `postgres://user:***@…`)

3. Confirm how many days/turns were written (and how many empty days were skipped).

## Do not

- Put conversation logs in `~/.cursor/skills-cursor/`
- Commit secrets from chats (tokens, passwords); redact if present
- Create or keep empty-day stubs when no chat was found
- Overwrite a rich existing day file with empty content when rebuild finds no turns for that day
- Dump full Write/StrReplace file contents into the conversion log
