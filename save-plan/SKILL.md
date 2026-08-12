---
name: save-plan
description: >-
  Saves Cursor agent plans into markdown under plans/ in the workspace
  (from ~/.cursor/plans or the current chat plan). Use when the user asks to
  save, export, archive, or update plans, plan docs, or plan markdown.
---

# Save Plan

Persist Cursor plan documents as markdown in the project workspace — the plan
counterpart to `save-conversation`.

## Defaults

| Setting | Value |
|---------|--------|
| Folder | `plans/` at the workspace root |
| Filename | `YYYY-MM-DD-<slug>.md` (plan day + name slug) |
| Source (save now / today) | Plan(s) from the current chat, or Cursor plan files modified today |
| Source (export / rebuild) | `~/.cursor/plans/*.plan.md` and workspace `.cursor/plans/*.plan.md` |

Create `plans/` if missing. Do **not** invent plans or write stub files when none exist.

## When to use

- “Save this plan”
- “Save today’s plans”
- “Export plans to the repo”
- “Archive the DayFlow calendar plan”
- “Update plans/”

## Save current / named plan

1. Prefer the plan file attached or referenced in the chat (e.g. under
   `~/.cursor/plans/` or `.cursor/plans/`).
2. If the user names a plan (“DayFlow Expense Calendar”), match by frontmatter
   `name` or filename slug.
3. If they say “today’s plans”, export plans whose file mtime falls on today’s
   local calendar day (or run the helper with `--today`).
4. Write into `plans/YYYY-MM-DD-<slug>.md` using the format below.
5. Overwrite the same path if that plan was already saved (refresh), unless the
   user asks to keep versions.
6. Briefly tell the user the path(s) written.

### Format

```markdown
# Plan — <Plan Title>

Saved from Cursor plan on YYYY-MM-DD.

## Overview

<overview from plan frontmatter, if present>

## Todos

- [ ] <pending todo>
- [x] <completed todo>

## Plan

<body markdown from the plan file, without YAML frontmatter>
```

Rules for the body:

- Strip YAML frontmatter (`---` … `---`) from the source `.plan.md`.
- Keep mermaid, file links, and headings.
- Map frontmatter `todos` into a checklist (`completed` → `[x]`, else `[ ]`).
- Do not invent todos or overview text that are not in the source plan.
- Redact secrets if any appear in the plan text.

### Filename slug

From the plan `name` (or filename stem): lowercase, spaces/`_` → `-`, keep
`a-z0-9-` only, collapse repeats. Example:

`DayFlow Expense Calendar` → `dayflow-expense-calendar`  
→ `plans/2026-08-11-dayflow-expense-calendar.md`

Use the plan file’s local modification date for `YYYY-MM-DD` when exporting from
disk; use today’s date when saving a plan just created in the current chat and
mtime is unavailable.

## Export / rebuild from Cursor plan files

Preferred helper:

```bash
python3 ~/.cursor/skills/save-plan/scripts/export_plans.py \
  --workspace "$PWD" \
  --today
```

Windows (PowerShell):

```powershell
python "$env:USERPROFILE\.cursor\skills\save-plan\scripts\export_plans.py" `
  --workspace "$PWD" `
  --today
```

Useful flags:

| Flag | Meaning |
|------|---------|
| `--today` | Only plans modified today (local day) |
| `--from YYYY-MM-DD` / `--to YYYY-MM-DD` | Filter by plan file mtime |
| `--name <substr>` | Match plan title or filename (case-insensitive) |
| `--all` | Export every discovered plan file |
| `--plans-dir <path>` | Extra directory of `*.plan.md` files |

Discovery order (dedupe by slug, prefer newer mtime):

1. `~/.cursor/plans/*.plan.md`
2. `<workspace>/.cursor/plans/*.plan.md`
3. Any `--plans-dir`

The script writes `plans/YYYY-MM-DD-<slug>.md` and prints how many files were
written or skipped.

## Do not

- Put this skill under `~/.cursor/skills-cursor/`
- Commit secrets from plans; redact if present
- Create empty stub files when no plan matches
- Overwrite an unrelated saved plan that shares no slug/title match
- Dump raw binary or huge generated assets into `plans/`
