# Brain — Obsidian pilot

This vault points at `.brain/`, so the fleet's task files in [[tasks]] are live-editable
here **without changing anything about how the agents work**. The dashboard + fleet stay the
machine layer; Obsidian is just a human-facing window onto the same markdown.

## Two board views (open either)

- **`Task Board.base`** — native Obsidian Bases board. No plugin needed on current Obsidian.
  Tabs across the top switch between *Doing / Review / Backlog / Done / all*.
- **`Task Board (Dataview).md`** — same board via the Dataview plugin (only if you install it).

Open one, click a row, edit the frontmatter in the right-hand **Properties** panel — you're
editing the exact same file the fleet reads. Status changes here are picked up by the agents;
agent changes show up here on next reindex.

## What this is a test of

You wanted to feel whether Obsidian beats the web dashboard for *browsing and hand-editing*
tasks. It won't replace the **live** agent view (the dashboard streams runs in real time;
Obsidian only shows files at rest). But for reading, filtering, bulk-editing, and linking tasks
to notes, this is the comparison.

## If you want the knowledge side too

The richer win for Obsidian is notes/thinking, which the repo currently lacks. Say the word and
I'll widen the vault to the repo root (or symlink `workflow/*/spec.md`, `BRAINSTORM.md`, domains)
so specs and design docs backlink to each other.

---
*Source of truth = `.brain/tasks/*.md`. This vault adds no new data — only views.*
