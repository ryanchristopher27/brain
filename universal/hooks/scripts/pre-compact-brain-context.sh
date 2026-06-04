#!/usr/bin/env bash
# Hook type: PreCompact
# Injects brain state into the compaction prompt so open questions and session
# history survive summarization

BRAIN_DIR="/Users/rchristopher/Desktop/Code/brain"
QUEUE="$BRAIN_DIR/updates/queue.md"
BRAINSTORM="$BRAIN_DIR/BRAINSTORM.md"

echo "## Brain State — preserve in compaction summary"
echo ""

# Open design questions from BRAINSTORM.md
if [ -f "$BRAINSTORM" ]; then
  OPEN=$(grep "^- \[ \]" "$BRAINSTORM")
  if [ -n "$OPEN" ]; then
    echo "### Open brain design questions:"
    echo "$OPEN"
    echo ""
  fi
fi

# Last 3 queue entries (session history)
if [ -f "$QUEUE" ] && grep -q "^## " "$QUEUE"; then
  FIRST=$(grep -n "^## " "$QUEUE" | tail -3 | head -1 | cut -d: -f1)
  echo "### Recent brain queue entries (last 3 sessions):"
  tail -n +"$FIRST" "$QUEUE"
  echo ""
fi
