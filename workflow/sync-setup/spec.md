# /sync-setup — spec

## Intent

The pull side of `/sync`. Working across machines, `/sync` pushes brain from the machine you
used; the other one then needs more than a `git pull`: every project repo, brain's Python deps,
the installer (commands, agents, mods), and a reminder of the state git doesn't carry. Done by
hand that's six or seven steps that are easy to half-do. `/sync-setup` runs them and reports one
table. A utility command, not a workflow phase.

## Behavior

1. Resolve brain from the installed command's symlink (as `/plan` does), falling back to the
   current repo and the known macOS and Windows checkouts. The installer copies rather than
   links commands on Windows, so the symlink alone isn't enough there.
2. `git pull --ff-only` brain, then every repo in this machine's registry
   (`~/.claude/brain/projects.json`), current branch only.
3. List projects in `brain/artifacts/` with no local registry entry — tracked elsewhere, missing
   here.
4. `pip install -r voice/requirements.txt` into `voice/.venv` (creating it if absent). If a
   voice-only package won't build (PortAudio, whisper.cpp — likely on Windows), fall back to the
   dashboard's own packages so the Hub and harness still work.
5. Re-run `install/install.sh`.
6. Check the dashboard, mods and CLI version; say what to restart, restart nothing.
7. Report: a repo table, what needs action, and the per-machine state that doesn't sync
   (registry, team agents, secrets, `/team follow`).

## Boundaries

- **Fast-forward only.** Ahead or diverged repos are reported, never rebased, reset or stashed.
  Pushing stays with `/sync`, so one command moves data each direction.
- Never stops or restarts the user's servers or sessions.
- Doesn't run project-level setup (npm install, env files) — it flags changed lockfiles instead.

## Why a prompt, not a CLI

Unlike `/sync`, nothing here is outward or irreversible: fast-forward pulls, an idempotent
installer, a pip install. The useful part is judgment across many repos in different states —
explaining why one didn't pull and what to do — which a prompt reports better than a script.
If it grows a step that writes to a remote, move that step into a CLI as `/sync` does.
