#!/usr/bin/env bash
# Hook type: SessionStart
# Whenever you start Claude Code in any project, auto-register it (new or old) in the brain
# project registry and refresh the Obsidian projects vault. Fire-and-forget: never delays or
# breaks a session. The web dashboard reads the registry live, so it needs no refresh.

BRAIN_DIR="/Users/rchristopher/Desktop/Code/brain"
PY="$BRAIN_DIR/voice/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
[ -z "$CWD" ] && CWD="$PWD"

# Skip work inside the brain repo's own vaults / git internals — nothing to register there.
case "$CWD" in
  "$BRAIN_DIR/.git"*) exit 0 ;;
esac

if command -v timeout > /dev/null 2>&1; then RUN="timeout 20"; else RUN=""; fi

OUT=$(cd "$BRAIN_DIR" && $RUN "$PY" -m dashboard.projects_cli sync --path "$CWD" 2>/dev/null)
[ -n "$OUT" ] && echo "[brain] $OUT"
exit 0
