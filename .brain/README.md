# .brain/ — project state that travels with the code

This directory is **committed** to the repo on purpose: pull the code on another machine and its
task state comes with it. Change history = the in-file `## Updates` log **plus** `git log`/`git diff`.

## `tasks/` — one file per task

`tasks/<id>-<slug>.md`. Scalar YAML frontmatter (stdlib-parseable, no YAML dependency) + markdown
body sections. One file per task keeps git merges small (creates never conflict; edits to different
tasks never touch).

```markdown
---
id: 9f3a2b                       # random short id — collision-free across offline devices; ref as #9f3a2b
title: Fix login redirect loop
type: task                       # task | issue | bug
status: doing                    # backlog | ready | doing | review | done
assignee: builder                # a persona name, or empty
scoped_dir: .                    # relative to repo root; a write-run is confined here
created: 2026-07-26T14:03:00Z
updated: 2026-07-26T14:35:00Z
---

## Brief
What to do + the context an agent needs. The run prompt is built from Brief + Acceptance.

## Acceptance
- [ ] criterion one
- [ ] criterion two

## Runs
- r_abc123                       # fleet-run ids (telemetry lives in the local registry)

## Updates
- 2026-07-26T14:03Z · created
- 2026-07-26T14:20Z · status: backlog → doing
- 2026-07-26T14:35Z · result (r_abc123): patched the redirect guard; tests pass
```

## Status machine
```
backlog ⇄ ready → doing → review → done        (review → doing = rework; any → backlog = park)
```
**Agents may only reach `review`.** A human or the Reviewer persona closes a task (`done`). This is
enforced in `dashboard/tracker.py:set_status`.

## Notes
- The dashboard reads/writes these files; you **commit them** as normal git flow (that's how state
  travels). Auto-commit is intentionally deferred.
- Managed by `dashboard/tracker.py` (stdlib-only). Format spec: docs/plan.md → "T1 Deep Dive".
