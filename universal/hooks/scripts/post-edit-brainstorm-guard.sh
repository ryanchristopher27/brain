#!/usr/bin/env bash
# Hook type: PostToolUse (Write)
# When new structural brain files are created, reminds to update BRAINSTORM.md

BRAIN_DIR="/Users/rchristopher/Desktop/Code/brain"

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[ -z "$FILE" ] && exit 0
[ "$TOOL" != "Write" ] && exit 0

ABS_FILE=$(realpath "$FILE" 2>/dev/null || echo "$FILE")

# Structural locations: new commands, new domain rules, new workflow specs
if [[ "$ABS_FILE" == "$BRAIN_DIR/.claude/commands/"*.md ]] || \
   [[ "$ABS_FILE" == "$BRAIN_DIR/domains/"*/rules.md ]] || \
   [[ "$ABS_FILE" == "$BRAIN_DIR/workflow/"*/spec.md ]]; then
  echo "[brain] New structural file created: $(basename "$ABS_FILE") — update BRAINSTORM.md if this changes the design"
fi
