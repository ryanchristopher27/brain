#!/usr/bin/env bash
# Hook type: Stop
# End-of-session: nudges /reflect and instructs Claude to append to the brain update queue

INPUT=$(cat)
REASON=$(echo "$INPUT" | jq -r '.stop_reason // empty')

[ "$REASON" != "end_turn" ] && exit 0

BRAIN_DIR="/Users/rchristopher/Desktop/Code/brain"
QUEUE="$BRAIN_DIR/updates/queue.md"
TODAY=$(date '+%Y-%m-%d')

cat << PROMPT
Session complete. Please do the following automatically:

1. Append a brief entry to $QUEUE using this exact format (append, never overwrite):

## $TODAY — [project or topic name]
- [what was accomplished, 1-3 bullets]
- Patterns: [any patterns worth capturing as brain rules/skills, or "none"]
- Brain improvements: [any friction or gaps in brain that should be addressed, or "none"]

2. If substantial work was done, mention that /reflect is available for a deeper retrospective.

Keep the queue entry concise — 4-6 lines max. If this was a trivial or single-question session, still append a one-liner entry so the queue stays complete.
PROMPT
