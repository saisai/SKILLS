---
name: save-thoughts
description: >-
  Exports Cursor assistant thoughts and commands used in this chat to markdown
  in the working directory. Use when the user asks to save thoughts, reasoning,
  commands, shell history, or tool usage from this conversation.
---

# Save Thoughts and Commands

Write this chat's **assistant thoughts** and **commands used** to the working directory.

## Default output

- Directory: `<cwd>/cursor/thoughts/`
- File: `YYYY-MM-DD-HH-MM-SS.md` (one file per save; does not overwrite earlier saves that day)
- Override the path if the user names one

Do not commit the file unless the user asks.

## Workflow

1. Resolve the workspace transcript folder:

   ```text
   ~/.cursor/projects/<workspace-slug>/agent-transcripts/
   ```

   `<workspace-slug>` is the workspace path with `/` replaced by `-`.

2. Run the exporter (newest `.jsonl` unless the user names another chat):

   ```bash
   python3 ~/.cursor/skills/save-thoughts/scripts/save_thoughts.py \
     --transcripts-dir "$HOME/.cursor/projects/<workspace-slug>/agent-transcripts" \
     --out-dir "$PWD/cursor/thoughts"
   ```

   Optional:

   - `--title "My title"`
   - `--out /path/to/file.md`
   - `--include-other-tools` (list non-shell tools too)

3. Tell the user the saved path and how many thoughts and commands were written.

## Redaction

The script redacts common secret patterns. Skim commands for credentials before
reporting success. If a secret slipped through, rewrite the file without it.

## If no transcript exists

Say the chat is not on disk yet. Do not invent thoughts or commands.
