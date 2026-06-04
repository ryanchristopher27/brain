#!/usr/bin/env bash
# Hook type: PostToolUse (Write|Edit)
# Fires after any file write/edit — re-runs install.sh if the file is inside brain

BRAIN_DIR="/Users/rchristopher/Desktop/Code/brain"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[ -z "$FILE" ] && exit 0

ABS_FILE=$(realpath "$FILE" 2>/dev/null || echo "$FILE")

# Only fire for brain files, skip .git internals and the install log itself
if [[ "$ABS_FILE" == "$BRAIN_DIR"* ]] && [[ "$ABS_FILE" != "$BRAIN_DIR/.git"* ]]; then
  OUTPUT=$(bash "$BRAIN_DIR/install/install.sh" 2>&1)
  STATUS=$?
  if [ $STATUS -eq 0 ]; then
    echo "[brain] Auto-synced global install (edited: $(basename "$ABS_FILE"))"
  else
    echo "[brain] Install sync FAILED (edited: $(basename "$ABS_FILE")) — run install.sh manually to debug"
    echo "$OUTPUT" | tail -5
  fi
fi
