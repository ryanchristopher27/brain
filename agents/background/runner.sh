#!/usr/bin/env bash
# agents/background/runner.sh
# Run one unattended Operator job and save a report.
#
# Safety model: Operator is read-only (Read/Grep/Glob). The RUNNER writes the output — the
# agent never needs write permission, which is the safe way to run headless/unattended
# (a `claude -p` agent can't interactively approve its own writes). Never uses
# --dangerously-skip-permissions.
#
# Usage: runner.sh "<task prompt>" [label]
#   e.g. runner.sh "Read updates/queue.md and summarize the most recent entry." queue-digest

set -euo pipefail

BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASK="${1:-}"
LABEL="${2:-operator}"
TOOLS="${BRAIN_BG_TOOLS:-Read,Grep,Glob}"   # read-only by default

if [ -z "$TASK" ]; then
  echo "usage: runner.sh \"<task prompt>\" [label]" >&2
  exit 1
fi

OUT_DIR="${BRAIN_BG_DIR:-$HOME/.claude/brain-bg-logs}"   # outside the repo — no git churn
mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$OUT_DIR/${LABEL}_${STAMP}.log"
REPORT="$OUT_DIR/${LABEL}_${STAMP}.md"

CLAUDE_BIN="$(command -v claude || echo claude)"
PY_BIN="$BRAIN_DIR/voice/.venv/bin/python"; [ -x "$PY_BIN" ] || PY_BIN="python3"
REG="$BRAIN_DIR/dashboard/registry_append.py"
RUN_ID="$("$PY_BIN" -c 'import secrets;print(secrets.token_urlsafe(16))' 2>/dev/null || echo "$STAMP")"

cd "$BRAIN_DIR"   # run in the repo so Operator can read project files with relative paths

{
  echo "[runner] $(date) starting '$LABEL'"
  echo "[runner] task : $TASK"
  echo "[runner] tools: $TOOLS (read-only; no --dangerously-skip-permissions)"
  echo "[runner] cwd  : $BRAIN_DIR"
} | tee "$LOG"

# Record the run in the registry (no-op if the dashboard db isn't set up).
"$PY_BIN" "$REG" start --id "$RUN_ID" --persona operator --task "$TASK" --source background >/dev/null 2>&1 || true

# Operator produces the text; the runner persists it.
if RESULT="$("$CLAUDE_BIN" -p "$TASK" \
      --agent operator \
      --allowed-tools "$TOOLS" \
      --output-format text 2>>"$LOG")"; then
  printf '%s\n' "$RESULT" > "$REPORT"
  echo "[runner] ✓ report → $REPORT" | tee -a "$LOG"
  "$PY_BIN" "$REG" finish --id "$RUN_ID" --status done --report_path "$REPORT" >/dev/null 2>&1 || true
else
  echo "[runner] ✗ claude failed (see $LOG)" | tee -a "$LOG"
  "$PY_BIN" "$REG" finish --id "$RUN_ID" --status error >/dev/null 2>&1 || true
  exit 1
fi
