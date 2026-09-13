---
name: save-plan
description: >-
  Saves the current Cursor Plan (Plan mode document) as markdown in the
  working directory. Use when the user asks to save, export, or archive a
  plan, Plan mode doc, or implementation plan.
---

# Save Plan

Write the **current Cursor Plan** to the working directory. Do not invent a plan.

## Default output

- Directory: `<cwd>/plans/`
- File: `YYYY-MM-DD-<short-title>.md`
- Override the path if the user names one

Do not commit the file unless the user asks.

## Workflow

1. Find the plan, in this order:

   1. A plan the user attached, opened, or pasted in this turn
   2. The Plan mode document already in this chat
   3. The newest file under any of:

      ```text
      .cursor/plans/
      ~/.cursor/projects/<workspace-slug>/plans/
      ```

      `<workspace-slug>` is the workspace path with `/` replaced by `-`.
      Also accept `*.plan.md` in the workspace if that is clearly the active plan.

2. Save it:

   ```bash
   python3 ~/.cursor/skills/save-plan/scripts/save_plan.py \
     --source /path/to/plan.md \
     --out-dir "$PWD/plans"
   ```

   Or pipe the plan text:

   ```bash
   python3 ~/.cursor/skills/save-plan/scripts/save_plan.py \
     --title "My plan" \
     --out-dir "$PWD/plans" \
     --stdin
   ```

   Optional: `--out /path/to/file.md`

3. Tell the user the saved path and the plan title.

## Redaction

The script redacts common secret patterns. Skim the saved file for credentials
before reporting success.

## If no plan exists

Say there is no Cursor Plan in this session and ask the user to open Plan mode
or point at a plan file. Do not write a reconstructed or guessed plan.
