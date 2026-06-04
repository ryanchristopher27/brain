# Hooks

Shell commands that fire automatically on specific Claude Code events. Add hooks here when you have automations to wire in — the install script will pick them up.

---

## How Hooks Work

Hooks are configured in `~/.claude/settings.json` under the `hooks` key. Each hook is a shell command that runs when a specific event fires. Claude Code passes event data via stdin as JSON.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/pre-edit.sh" }]
      }
    ]
  }
}
```

---

## Hook Types

### PreToolUse
Fires before any tool is used. Can inspect or block the tool call.

**Common uses:**
- Warn before editing files outside the expected scope
- Remind about conventions before a write operation
- Log what's about to happen

**Receives via stdin:** tool name, tool input parameters

### PostToolUse
Fires after a tool completes. Cannot block, but can react.

**Common uses:**
- Log what was changed
- Trigger a linter or formatter after a file edit
- Update a changelog or activity log

**Receives via stdin:** tool name, tool input, tool output

### Notification
Fires when Claude sends a message to the user.

**Common uses:**
- Desktop notifications for long-running tasks
- Log conversation milestones

**Receives via stdin:** message content

### Stop
Fires when Claude finishes a response (session end or task complete).

**Common uses:**
- Suggest `/reflect` at natural stopping points
- Run a post-session cleanup script
- Save session summary to a log

**Receives via stdin:** stop reason

### PreCompact
Fires before a long conversation is compacted (summarized to free context). Stdout is **injected directly into the compaction prompt**, making it the mechanism for controlling what survives summarization.

**Common uses:**
- Inject open questions, active decisions, or in-progress state that must not be lost
- Surface project-specific context the summary should emphasize
- Ensure memory or queue state is referenced in the compacted summary

**Receives via stdin:** compaction reason/trigger

**Note:** Unlike other hooks, stdout here is added to the compaction prompt itself — not shown to the user or Claude as a message. Keep output focused and structured so the summarizer can use it.

---

## Adding a Hook

1. Write a shell script in `brain/universal/hooks/scripts/`
2. Add the hook configuration to `brain/.claude/settings.json`
3. Re-run `install/install.sh` to sync settings globally

### Script Template

```bash
#!/usr/bin/env bash
# hooks/scripts/my-hook.sh
# Hook type: PreToolUse | PostToolUse | Notification | Stop
# Fires when: [describe the trigger]

# Read event data from stdin
INPUT=$(cat)

# Extract fields with jq if needed
# TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Your logic here

exit 0  # exit 0 = allow, exit 2 = block (PreToolUse only)
```

### Exit Codes (PreToolUse only)
- `0` — allow the tool call to proceed
- `2` — block the tool call (Claude will see the script's stdout as the reason)

---

## Examples

See `hooks/examples/` for ready-to-use hook scripts covering common patterns.
Nothing in examples/ is active — copy to scripts/ and wire into settings.json to use.
