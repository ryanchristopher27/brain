# /sync — spec

## Intent

A one-shot "snapshot my work to GitHub" command. Brain is the canonical home for every
project's markdown artifacts (`brain/artifacts/`), populated automatically on SessionStart — but
those copies live only in the local brain working tree until pushed. `/sync` closes that gap:
refresh the archive from all tracked projects, commit the artifact changes, and push to the
remote. It is a utility command, not a workflow phase.

## Behavior

Backed by `dashboard/artifacts_cli.py push` (deterministic — the git logic lives in the CLI, not
in an LLM prompt, so `/sync` is reliable and testable):

1. `artifacts.sync_all()` — mirror each registered project's `docs/*.md`, `.brain/tasks/*.md`,
   session summaries, and marked deliverables into `brain/artifacts/<project>/`. Idempotent:
   files carry no volatile timestamps, so an unchanged project yields no diff.
2. Stage only `artifacts/`; commit if changed (`--message` overrides the default).
3. `git push origin HEAD` — current branch (`main`) to `origin`.

## Boundaries

- Stages **only** `artifacts/` — never sweeps in uncommitted code.
- Push moves all pending branch commits to the remote (brings origin current), by design.
- No `--force`; a rejected (non-fast-forward) push is surfaced, not overridden — the user
  reconciles.
- `--dry-run` previews commit + push scope without mutating anything.

## Why deterministic

Commit/push is exactly the kind of irreversible, outward action that should behave identically
every invocation. Keeping it in the CLI (with a `--dry-run`) makes the slash command a thin,
predictable trigger rather than a re-interpreted prompt.
