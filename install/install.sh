#!/usr/bin/env bash
# brain/install/install.sh
# Wires brain resources into Claude Code and Cursor globally.
# Safe to re-run — idempotent. Backs up before modifying existing configs.

set -euo pipefail

BRAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[brain]${NC} $1"; }
warn()  { echo -e "${YELLOW}[brain]${NC} $1"; }
error() { echo -e "${RED}[brain]${NC} $1"; }

# ── Tool detection ────────────────────────────────────────────────────────────
detect_tools() {
  HAS_CLAUDE=false
  HAS_CURSOR=false

  if [ -d "$HOME/.claude" ]; then
    HAS_CLAUDE=true
    info "Detected: Claude Code (~/.claude)"
  fi

  if [ -d "$HOME/.cursor" ]; then
    HAS_CURSOR=true
    info "Detected: Cursor (~/.cursor)"
  fi

  if [ "$HAS_CLAUDE" = false ] && [ "$HAS_CURSOR" = false ]; then
    error "Neither Claude Code nor Cursor detected. Nothing to install."
    exit 1
  fi
}

# ── Backup ────────────────────────────────────────────────────────────────────
backup_file() {
  local file="$1"
  if [ -f "$file" ]; then
    cp "$file" "${file}.bak_${TIMESTAMP}"
    warn "Backed up: $file → ${file}.bak_${TIMESTAMP}"
  fi
}

# ── Shared: install a single command file ─────────────────────────────────────
install_command_file() {
  local cmd_file="$1"
  local target_dir="$2"
  local label="${3:-}"
  local filename
  filename=$(basename "$cmd_file")
  local target="$target_dir/$filename"

  if [ -f "$target" ]; then
    if diff -q "$cmd_file" "$target" > /dev/null 2>&1; then
      info "  Already current: $filename${label}"
      return
    fi
    backup_file "$target"
  fi

  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    cp "$cmd_file" "$target"
    info "  Copied: $filename → $(basename "$target_dir")/${label}"
  else
    ln -sf "$cmd_file" "$target"
    info "  Linked: $filename → $(basename "$target_dir")/${label}"
  fi
}

# ── Shared: install a single rule file ────────────────────────────────────────
install_rule_file() {
  local rule_file="$1"
  local target_dir="$2"
  local prefix="${3:-brain_}"
  local filename
  filename=$(basename "$rule_file")
  local target="$target_dir/${prefix}${filename}"

  if [ -f "$target" ]; then
    if diff -q "$rule_file" "$target" > /dev/null 2>&1; then
      info "  Already current: ${prefix}${filename}"
      return
    fi
    backup_file "$target"
  fi

  if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    cp "$rule_file" "$target"
    info "  Copied: $filename → ${prefix}${filename}"
  else
    ln -sf "$rule_file" "$target"
    info "  Linked: $filename → ${prefix}${filename}"
  fi
}

# ── Claude Code ───────────────────────────────────────────────────────────────
install_claude_code() {
  info "Installing into Claude Code..."

  local CC_COMMANDS="$HOME/.claude/commands"
  mkdir -p "$CC_COMMANDS"

  # Workflow + utility commands
  for cmd_file in "$BRAIN_DIR/.claude/commands"/*.md; do
    [ -f "$cmd_file" ] || continue
    install_command_file "$cmd_file" "$CC_COMMANDS"
  done

  # Domain commands
  for domain_dir in "$BRAIN_DIR/domains"/*/; do
    local domain_name
    domain_name=$(basename "$domain_dir")
    [ "$domain_name" = "_template" ] && continue
    if [ -d "$domain_dir/commands" ]; then
      for cmd_file in "$domain_dir/commands"/*.md; do
        [ -f "$cmd_file" ] || continue
        install_command_file "$cmd_file" "$CC_COMMANDS" " (domain: $domain_name)"
      done
    fi
  done

  # Subagents (agents/personas + agents/background). Flattened into ~/.claude/agents/
  # by basename — filenames are unique. _template and non-.md files are skipped.
  if [ -d "$BRAIN_DIR/agents" ]; then
    local CC_AGENTS="$HOME/.claude/agents"
    mkdir -p "$CC_AGENTS"
    for agent_file in "$BRAIN_DIR/agents/personas"/*.md "$BRAIN_DIR/agents/background"/*.md; do
      [ -f "$agent_file" ] || continue
      grep -q '^name:' "$agent_file" || continue   # skip READMEs / non-agent docs
      install_command_file "$agent_file" "$CC_AGENTS" " (agent)"
    done
  fi

  # Merge settings.json (hooks + MCPs)
  local BRAIN_SETTINGS="$BRAIN_DIR/.claude/settings.json"
  local CC_SETTINGS="$HOME/.claude/settings.json"

  if command -v jq > /dev/null 2>&1; then
    local base="{}"
    [ -f "$CC_SETTINGS" ] && base=$(cat "$CC_SETTINGS")
    local merged="$base"

    # Merge brain base settings (hooks structure)
    if [ -f "$BRAIN_SETTINGS" ]; then
      backup_file "$CC_SETTINGS"
      merged=$(echo "$merged" | jq -s '.[0] * .[1]' - "$BRAIN_SETTINGS")
      info "  Merged: brain settings → ~/.claude/settings.json"
    fi

    # Merge MCP configs (personal/ + shared/)
    for mcp_file in "$BRAIN_DIR/mcps/shared"/*.json "$BRAIN_DIR/mcps/personal"/*.json; do
      [ -f "$mcp_file" ] || continue
      merged=$(echo "$merged" | jq -s '.[0] * .[1]' - "$mcp_file")
      info "  Merged MCP: $(basename "$mcp_file") → ~/.claude/settings.json"
    done

    echo "$merged" > "$CC_SETTINGS"
  else
    warn "  jq not found — skipping settings.json merge. Install jq to enable this."
  fi

  info "Claude Code install complete."
}

# ── Cursor ────────────────────────────────────────────────────────────────────
install_cursor() {
  info "Installing into Cursor..."

  local CURSOR_RULES="$HOME/.cursor/rules"
  mkdir -p "$CURSOR_RULES"

  # Universal rules
  for rule_file in "$BRAIN_DIR/.cursor/rules"/*.mdc; do
    [ -f "$rule_file" ] || continue
    install_rule_file "$rule_file" "$CURSOR_RULES"
  done

  # Domain rules
  for domain_dir in "$BRAIN_DIR/domains"/*/; do
    local domain_name
    domain_name=$(basename "$domain_dir")
    [ "$domain_name" = "_template" ] && continue
    if [ -f "$domain_dir/cursor-rule.mdc" ]; then
      install_rule_file "$domain_dir/cursor-rule.mdc" "$CURSOR_RULES" "brain_domain_${domain_name}_"
    fi
  done

  # Merge MCP configs (personal/ + shared/)
  local CURSOR_MCP="$HOME/.cursor/mcp.json"
  local mcp_files=()

  for mcp_file in "$BRAIN_DIR/mcps/shared"/*.json "$BRAIN_DIR/mcps/personal"/*.json; do
    [ -f "$mcp_file" ] || continue
    mcp_files+=("$mcp_file")
  done

  if [ "${#mcp_files[@]}" -gt 0 ]; then
    if command -v jq > /dev/null 2>&1; then
      backup_file "$CURSOR_MCP"
      local base="{}"
      [ -f "$CURSOR_MCP" ] && base=$(cat "$CURSOR_MCP")
      local merged="$base"
      for mcp_file in "${mcp_files[@]}"; do
        merged=$(echo "$merged" | jq -s ".[0] * .[1]" - "$mcp_file")
        info "  Merged: $(basename "$mcp_file") → ~/.cursor/mcp.json"
      done
      echo "$merged" > "$CURSOR_MCP"
    else
      warn "  jq not found — skipping MCP merge. Install jq to enable this."
    fi
  fi

  info "Cursor install complete."
}

# ── Uninstall ─────────────────────────────────────────────────────────────────
uninstall() {
  info "Uninstalling brain resources..."

  # Remove Claude Code commands (workflow + domain)
  for cmd_file in "$BRAIN_DIR/.claude/commands"/*.md; do
    [ -f "$cmd_file" ] || continue
    local filename target
    filename=$(basename "$cmd_file")
    target="$HOME/.claude/commands/$filename"
    [ -f "$target" ] || [ -L "$target" ] && rm -f "$target" && info "  Removed: $filename"
  done

  for domain_dir in "$BRAIN_DIR/domains"/*/; do
    local domain_name
    domain_name=$(basename "$domain_dir")
    [ "$domain_name" = "_template" ] && continue
    if [ -d "$domain_dir/commands" ]; then
      for cmd_file in "$domain_dir/commands"/*.md; do
        [ -f "$cmd_file" ] || continue
        local filename target
        filename=$(basename "$cmd_file")
        target="$HOME/.claude/commands/$filename"
        [ -f "$target" ] || [ -L "$target" ] && rm -f "$target" && info "  Removed: $filename (domain: $domain_name)"
      done
    fi
  done

  # Remove subagents
  for agent_file in "$BRAIN_DIR/agents/personas"/*.md "$BRAIN_DIR/agents/background"/*.md; do
    [ -f "$agent_file" ] || continue
    grep -q '^name:' "$agent_file" || continue
    local filename target
    filename=$(basename "$agent_file")
    target="$HOME/.claude/agents/$filename"
    [ -f "$target" ] || [ -L "$target" ] && rm -f "$target" && info "  Removed: $filename (agent)"
  done

  # Remove Cursor rules
  for rule_file in "$BRAIN_DIR/.cursor/rules"/*.mdc; do
    [ -f "$rule_file" ] || continue
    local filename target
    filename=$(basename "$rule_file")
    target="$HOME/.cursor/rules/brain_$filename"
    [ -f "$target" ] || [ -L "$target" ] && rm -f "$target" && info "  Removed: brain_$filename"
  done

  info "Uninstall complete. Settings files were not modified — restore from .bak files if needed."
}

# ── Entry point ───────────────────────────────────────────────────────────────
main() {
  echo ""
  info "brain install — $(date)"
  echo ""

  case "${1:-install}" in
    install)
      detect_tools
      echo ""
      [ "$HAS_CLAUDE" = true ] && install_claude_code && echo ""
      [ "$HAS_CURSOR" = true ] && install_cursor && echo ""
      info "Done. Brain resources are now globally available."
      info "Re-run this script after adding new commands, rules, or domains."
      ;;
    uninstall)
      uninstall
      ;;
    *)
      echo "Usage: install.sh [install|uninstall]"
      exit 1
      ;;
  esac
}

main "$@"
