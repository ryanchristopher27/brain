#!/usr/bin/env bash
# Example: PostToolUse hook — logs file edits to a session log
# Wire in settings.json:
#   "PostToolUse": [{ "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/scripts/post-edit-log.sh" }] }]

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
LOG="$HOME/.claude/edit-log.txt"

if [ -n "$FILE" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') | $TOOL | $FILE" >> "$LOG"
fi
