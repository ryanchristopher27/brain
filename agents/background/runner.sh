#!/usr/bin/env bash
# agents/background/runner.sh
# Skeleton headless runner for a single background (Operator) job.
# Scaffold stub — wiring a real scheduled task is milestone A4.
#
# Usage: runner.sh "<task prompt>" [extra allowed tools]
#   e.g. runner.sh "Summarize today's queue.md changes" "Read"

set -euo pipefail

TASK="${1:-}"
EXTRA_TOOLS="${2:-Read,Grep,Glob}"

if [ -z "$TASK" ]; then
  echo "usage: runner.sh \"<task prompt>\" [allowed-tools]" >&2
  exit 1
fi

LOG_DIR="${BRAIN_BG_LOG_DIR:-$HOME/.claude/brain-bg-logs}"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$LOG_DIR/operator_${STAMP}.log"

echo "[runner] $(date) — starting operator job" | tee "$LOG"
echo "[runner] task: $TASK" | tee -a "$LOG"
echo "[runner] allowed tools: $EXTRA_TOOLS" | tee -a "$LOG"

# A4: pin the Operator persona and a scoped allowlist. No --dangerously-skip-permissions.
# The exact flag surface is verified against the installed `claude` CLI in A4.
#
#   claude -p "$TASK" \
#     --agents operator \
#     --allowedTools "$EXTRA_TOOLS" \
#     --output-format stream-json 2>&1 | tee -a "$LOG"

echo "[runner] (stub) not yet wired — see milestone A4" | tee -a "$LOG"
