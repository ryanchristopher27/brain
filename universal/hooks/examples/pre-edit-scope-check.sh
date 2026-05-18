#!/usr/bin/env bash
# Example: PreToolUse hook — warns if an edit targets a file outside the project root
# Wire in settings.json:
#   "PreToolUse": [{ "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/scripts/pre-edit-scope-check.sh" }] }]
# Exit 0 = allow, Exit 2 = block

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
PROJECT_ROOT=$(pwd)

if [ -n "$FILE" ]; then
  # Resolve absolute path
  ABS_FILE=$(realpath "$FILE" 2>/dev/null || echo "$FILE")

  # Check if file is outside the project root
  if [[ "$ABS_FILE" != "$PROJECT_ROOT"* ]]; then
    echo "Edit target is outside the project root: $FILE"
    echo "Project root: $PROJECT_ROOT"
    exit 2  # Block the edit
  fi
fi

exit 0
