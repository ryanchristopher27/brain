#!/usr/bin/env bash
# Example: Stop hook — prints a /reflect reminder when a session ends
# Wire in settings.json:
#   "Stop": [{ "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/scripts/stop-reflect-nudge.sh" }] }]

INPUT=$(cat)
REASON=$(echo "$INPUT" | jq -r '.stop_reason // empty')

# Only nudge on natural stops, not errors
if [ "$REASON" = "end_turn" ]; then
  echo "Session complete. Consider running /reflect to capture what was learned."
fi
