# /sync-setup

Bring this machine up to date with what's on GitHub: pull brain and every registered project,
refresh brain's Python deps, re-run the installer, and list what doesn't travel through git. The
pull side of `/sync` — run `/sync` on the machine you worked on, then `/sync-setup` on this one.

## Do this

Run each step, keep going past failures, and finish with the report. Never force, reset, stash,
or discard anything — when a repo can't fast-forward, report it and move on.

### 1. Find brain

Known checkouts: macOS `~/Desktop/Code/brain`, Windows `C:\Users\rdash\OneDrive\Desktop\Code\brain`
(Git Bash: `~/OneDrive/Desktop/Code/brain`). Use `python3` on macOS, `python` on Windows.

```bash
PYSYS="$(command -v python3 || command -v python)"
BRAIN="$("$PYSYS" -c "import os;p=os.path.realpath(os.path.expanduser('~/.claude/commands/sync-setup.md'));print(os.path.dirname(os.path.dirname(os.path.dirname(p))))")"
for c in "$BRAIN" "$(git rev-parse --show-toplevel 2>/dev/null)" ~/Desktop/Code/brain ~/OneDrive/Desktop/Code/brain; do
  [ -f "$c/install/install.sh" ] && BRAIN="$c" && break
done
```

The symlink lookup only works on macOS (the installer copies commands on Windows), hence the
fallbacks. If none has `install/install.sh`, stop and ask where brain is checked out.

### 2. Pull brain

```bash
git -C "$BRAIN" fetch --quiet origin && git -C "$BRAIN" status -sb | head -1
git -C "$BRAIN" pull --ff-only
```

- **Behind:** fast-forwards. Note the commit range for the report.
- **Ahead or diverged:** this machine has commits the remote lacks. Don't pull; tell the user to
  run `/sync` here first (it rebases and pushes), then re-run `/sync-setup`.
- **Uncommitted changes in the way:** git refuses; report the files it named.

### 3. Pull every registered project

Projects come from this machine's registry, `~/.claude/brain/projects.json` (a list of
`{name, root_path}`). For each entry whose `root_path` is a git repo with an upstream (skip brain,
already done):

```bash
git -C "$ROOT" fetch --quiet && git -C "$ROOT" rev-list --left-right --count HEAD...@{u}   # ahead  behind
git -C "$ROOT" pull --ff-only   # only when behind > 0 and ahead == 0
```

A project can live inside a larger repo (prediction-market-bot is a folder of `vault`): pull each
repo once even if several projects share it. Pull only the current branch. Same rules as brain: ahead or diverged → report it ("run git push
there first" or "pull --rebase by hand"), don't touch it. No upstream → report "local only".
`root_path` missing → report "not on this machine".

Then compare against brain's archive: every folder under `$BRAIN/artifacts/` (except `README.md`)
is a project tracked on some machine. List those with no registry entry here — they exist
elsewhere but aren't cloned or registered on this machine.

### 4. Python deps

The dashboard, voice daemon, and agent harness share `voice/.venv`. Pick its python
(`$BRAIN/voice/.venv/bin/python`, or `voice/.venv/Scripts/python.exe` on Windows); if neither
exists, create it with `"$PYSYS" -m venv "$BRAIN/voice/.venv"`. Then:

```bash
"$PY" -m pip install -q -r "$BRAIN/voice/requirements.txt"
```

If that fails on a voice-only package (`sounddevice`, `pynput`, `pywhispercpp` need PortAudio and
a compiler; common on Windows), install just what the dashboard and harness need, and report that
the voice daemon isn't set up on this machine:

```bash
"$PY" -m pip install -q $(grep -E '^(fastapi|uvicorn|claude-agent-sdk)' "$BRAIN/voice/requirements.txt" | cut -d'#' -f1)
```

Report packages that were newly installed or upgraded (pip's "Successfully installed" line), or
"already current".

### 5. Re-run the installer

```bash
bash "$BRAIN/install/install.sh"
```

Idempotent: links commands, agents, rules and hooks, merges MCP configs, installs the mods
(`model-router`, `team`) from brain's local marketplace. Summarize what changed (lines that say
Linked / Installed / Copied / Updated), not the "Already current" lines.

### 6. Check the running pieces — don't restart them

- **Dashboard:** `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8766/api/config`. If
  it's up and step 2 or 4 changed anything, tell the user to restart it (`--reload` only picks up
  code edits, not new packages). If it's down, give the start command, run from `$BRAIN`:
  `./voice/.venv/bin/python -m dashboard.server` (Windows: `voice\.venv\Scripts\python -m dashboard.server`).
- **Mods:** if step 2 or 5 touched `mods/`, the user runs `/reload-plugins` in open sessions.
- **Claude Code:** report `claude --version`; suggest `claude update` if the harness's default
  models (`dashboard/harness/runtime.py`) may be newer than this CLI knows.

### 7. Report

One table, then the follow-ups:

| Repo | Branch | Result |
|------|--------|--------|
| brain | main | pulled 3 commits (c0fc1dd..76b902e) |
| Trip Fairy | main | already current |
| baseline | main | local only — no remote |

Then:
- **Needs action** — anything ahead, diverged, blocked by local changes, or missing.
- **What doesn't travel through git** (mention only what applies):
  - The project registry is per machine — a project registers itself the first time a Claude
    Code session opens in its folder.
  - Team agents live in this machine's `~/.claude/brain-dashboard/harness.db`. Their definitions
    did travel: Hub → Team → Library → "Add to the team" recreates them.
  - Dashboard secrets and its token are per machine; the user re-enters secrets in the Hub.
  - `/team follow` is per chat.

## Notes

- Fast-forward only, everywhere. Nothing here creates commits, pushes, or rewrites history —
  pushing is `/sync`'s job.
- Never install or run anything a pulled repo's own scripts ask for beyond the steps above;
  project-level setup (npm install, env files) stays the user's call — mention it if a pull
  changed a lockfile (`package-lock.json`, `requirements.txt`, …).
