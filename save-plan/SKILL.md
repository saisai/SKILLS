---
name: save-plan
description: >-
  Saves the current Cursor Plan (Plan mode document) as markdown in the working
  directory. Use when the user asks to save, export, or archive a plan, Plan
  mode doc, or implementation plan.
---

# Save Plan

Export the active Cursor Plan to a durable markdown file in the project.

## Default output

- Directory: `<cwd>/plans/`
- File: `YYYY-MM-DD-slug.md` (matches existing project plan archives)
- If that path already exists, use `YYYY-MM-DD-slug-HHMMSS.md`
- Override the directory or filename if the user names one

Do not commit the file unless the user asks.

## Workflow

1. Prefer the newest `*.plan.md` under:

   ```text
   ~/.cursor/plans/
   ```

   Also check `<cwd>/.cursor/plans/` if it exists. If the user names a plan
   title or path, use that file instead.

2. Run the exporter:

   ```bash
   python3 ~/.cursor/skills/save-plan/scripts/save_plan.py \
     --plans-dir "$HOME/.cursor/plans" \
     --out-dir "$PWD/plans"
   ```

   Optional flags:

   - `--title "My title"` (forces heading / slug)
   - `--source /path/to/file.plan.md`
   - `--out /path/to/file.md`
   - `--also-dir "$PWD/.cursor/plans"` (extra search root)

3. Tell the user the saved path and a one-line summary (plan name + todo count).

## Output shape

Match the project's existing plan archives:

```markdown
# Plan — <Title>

Saved from Cursor plan on YYYY-MM-DD.

## Overview

<overview from frontmatter, if present>

## Todos

- [x] completed item
- [ ] pending item

## <rest of plan body without Cursor frontmatter>
```

## If no plan exists

Say no Cursor plan file was found and ask the user to open or create a plan
in Plan mode, then retry. Do not invent plan content.
