#!/usr/bin/env bash
# Hook type: PostToolUse (Write|Edit)
# When a command or spec file is edited, reminds to keep the paired file in sync

BRAIN_DIR="/Users/rchristopher/Desktop/Code/brain"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[ -z "$FILE" ] && exit 0

ABS_FILE=$(realpath "$FILE" 2>/dev/null || echo "$FILE")
BASENAME=$(basename "$ABS_FILE" .md)

# Command file edited → check for paired spec
if [[ "$ABS_FILE" == "$BRAIN_DIR/.claude/commands/"*.md ]]; then
  SPEC="$BRAIN_DIR/workflow/$BASENAME/spec.md"
  if [ ! -f "$SPEC" ]; then
    echo "[brain] Command edited: $BASENAME.md — no spec found at workflow/$BASENAME/spec.md (create one?)"
  else
    echo "[brain] Command edited: $BASENAME.md — keep workflow/$BASENAME/spec.md in sync"
  fi
fi

# Spec file edited → check for paired command
if [[ "$ABS_FILE" == "$BRAIN_DIR/workflow/"*/spec.md ]]; then
  WORKFLOW=$(basename "$(dirname "$ABS_FILE")")
  CMD="$BRAIN_DIR/.claude/commands/$WORKFLOW.md"
  if [ ! -f "$CMD" ]; then
    echo "[brain] Spec edited: $WORKFLOW/spec.md — no command found at .claude/commands/$WORKFLOW.md (create one?)"
  else
    echo "[brain] Spec edited: $WORKFLOW/spec.md — keep .claude/commands/$WORKFLOW.md in sync"
  fi
fi
