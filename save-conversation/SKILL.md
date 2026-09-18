---
name: save-conversation
description: >-
  Exports the current Cursor chat transcript to a durable markdown file.
  Use when the user asks to save, export, archive, or back up this conversation,
  chat, transcript, or thread.
---

# Save Conversation

Export the active Cursor chat to markdown so it survives session loss.

## Default output

- Directory: `<cwd>/cursor/conversation/`
- File: `YYYY-MM-DD-HH-MM-SS.md` (one file per save; does not overwrite earlier saves that day)
- Override the directory or filename if the user names one

Do not commit the file unless the user asks.

## Workflow

1. Resolve the workspace transcript folder:

   ```text
   ~/.cursor/projects/<workspace-slug>/agent-transcripts/
   ```

   `<workspace-slug>` is the workspace path with `/` replaced by `-`
   (example: `/home/snp/real-time-chat-app` → `home-snp-real-time-chat-app`).

2. Run the exporter (prefer the newest `.jsonl` unless the user names another chat):

   ```bash
   python3 ~/.cursor/skills/save-conversation/scripts/save_conversation.py \
     --transcripts-dir "$HOME/.cursor/projects/<workspace-slug>/agent-transcripts" \
     --out-dir "$PWD/cursor/conversation"
   ```

   Optional flags:

   - `--title "My title"`
   - `--out /path/to/file.md`
   - `--include-tools` (include tool-call names; off by default)

3. Tell the user the saved path and a one-line summary of what was written.

## Redaction

The script strips common secret patterns. Still scan the first and last headings
before you report success. If a secret slipped through, rewrite the file without
it and warn the user.

## If no transcript exists

Say the chat is not on disk yet and ask the user to continue in this thread,
then retry. Do not invent conversation content.
