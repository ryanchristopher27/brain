# Brainstorm — Agent Dashboard enhancements
Date: 2026-07-24
Feeds: `docs/plan.md` → "Agent Dashboard (Pillar C v2)" + its "Enhancements & Revisions (v2)"

## Problem / Opportunity
The dashboard plan (v1) covered a control server, the orb-as-active-session panel, roster,
jobs, schedule, control actions, and a run registry. This session pressure-tested it for what
would make it genuinely better before scaffolding — and surfaced a second product axis the
original framing missed.

## The reframe (biggest outcome)
The dashboard has **two axes**, and they unify:
1. **Agents & Runs** — who's working, how, at what cost.
2. **Work Pipeline** — ideas progressing brainstorm → plan → scaffold → build → review →
   reflect (a Kanban board; phase detected via `/status` doc-logic).
Agents are what *move a pipeline card forward*. This turns the dashboard into mission control
for both the fleet and the flow of work.

## Ideas & Directions (all adopted)
- **Live activity + cost** — per-run tool-call feed + spend panel, from `stream-json`
  `tool_use` + `total_cost_usd`/tokens we already parse. Near-free, high signal.
- **Approvals inbox** — `claude -p --permission-prompt-tool` routes tool-approval requests to
  the dashboard (approve/deny). Unlocks safe autonomous writes and pays off the "headless can't
  prompt" debt open since B4. *Must probe the flag against 2.1.167 first.*
- **MCP + daemon health** — connection status for github/notion/playwright (surfaces the A2
  tokens-not-set gap), daemon liveness, model/permission-mode.
- **Task queue / dispatcher** — enqueue tasks, assign to personas, watch them drain (later phase).
- **Work-pipeline board** — the user's addition; the second axis above.
- **Extras** — macOS notifications on job finish/fail/spend; quick-action templates; `/fleet`
  run visualization (parallel personas as concurrent runs).

## Correction folded in (not optional)
**localhost is not private** — any web page you visit can POST to `127.0.0.1:<port>` (CSRF). The
plan's "local bind, no auth" is unsafe. Mandatory: token + `Origin`/`Host` check + an action
audit log on the control API.

## Recommendations / Suggested Decisions (confirmed)
- Registry storage: **SQLite** (enables cost/stats/history).
- Adopt all enhancements + extras; phase strictly so Phase 1 still ships a real read-only
  dashboard (D1–D3, D7) before any control.
- Approvals via `--permission-prompt-tool`, verified before D8.
- Security hardening mandatory in D4.

## Open Questions for /plan (recorded there)
- Pipeline: current repo only (v1) vs configured project roots; phase-detection tiebreak.
- Approvals: probe `--permission-prompt-tool` on claude 2.1.167 before D8.
- Backend home (`dashboard/` recommended), local auth token, default spawn persona (Scout).

## Next Steps
Decisions are folded into `docs/plan.md`. Phase 1 (D1 control server → D2 shell+orb → D3
panels → D7 pipeline board) is the first shippable slice → ready for `/scaffold` once the
Phase-1 open questions have their (safe) defaults confirmed.

---

# Brainstorm — Graphify Integration (Knowledge-Graph Context for the LLM)
Date: 2026-07-26
Status: Draft
Scope: New project — unrelated to the Agent Dashboard section above.

## Problem / Opportunity
Claude re-derives repo structure from scratch every session. A knowledge graph of a repo
gives the LLM a persistent, queryable map of how things connect (calls, imports, inheritance,
doc concepts), cutting re-exploration and grounding answers in real relationships.

The trigger was the `graphify` tool. Key finding after verifying against the actual repo
(`safishamsi/graphify`), not blog summaries: **this is adopt, not build.** Graphify already
ships the LLM-facing surface — an MCP server + Claude Code skill + pre-tool-use hooks. So the
real project is *how to adopt and wire it*, not *how to build a graph tool*.

## Goals
- **Primary:** LLM context injection across the **vault** and **any active high-level code
  repo**. Primarily a tool for the LLM, not a human dashboard.
- **Secondary (free byproducts):** navigation, docs, dependency insight come for free via
  `graph.html` / `GRAPH_REPORT.md` — not pursued for their own sake.

## Audience
Personal use, across multiple repos, in Claude Code (potentially Cursor per brain's cross-tool stance).

## Constraints
- **Cost/privacy split is the spine of the design:**
  - **Code = free + 100% local** (bundled tree-sitter, no API calls, nothing leaves the machine).
  - **Vault = LLM-cost** — prose/markdown/PDF extraction requires a model call and sends
    *semantic descriptions* (not raw text) to the configured model.
- **Vault is plain markdown in git today**, not Obsidian. Obsidian is a *possible future* →
  graphify's `--obsidian` mode is a future output target, not how the vault gets graphed now.
- `graphify install` changes behavior **globally** — its pre-tool-use hook nudges *every*
  Claude Code session toward graph queries. Not destructive, but felt everywhere.
- Python 3.10+, `uv`/`pipx`. In-session `/graphify .` uses the existing model session (no key);
  headless `graphify extract` needs an API key.

## Tool Facts (verified against the repo)
Install: `uv tool install graphifyy` (double-y), then `graphify install` to register the skill.

Output — `graphify-out/`:
| File | What it is |
|------|-----------|
| `graph.json` | Full graph. Nodes: functions/classes/modules, doc concepts, design rationale from `# NOTE:`/`# WHY:`/`# HACK:` comments, community clusters. Edges: calls, inheritance, data flow. Confidence: `EXTRACTED`/`INFERRED`/`AMBIGUOUS`. |
| `GRAPH_REPORT.md` | Highlights, "god nodes," surprising connections, suggested questions. |
| `graph.html` | Interactive browser viz (not for the LLM). |
| `cache/`, `manifest.json`, `cost.json` | Incremental SHA256 cache, portable node registry, API-cost tracking. |

MCP server exposes: `query_graph`, `get_node`, `get_neighbors`, `shortest_path`, `get_pr_impact`.
Freshness: `--update` (incremental), `--watch` (live), `cluster-only` (recluster without re-extract).
Optional exports: `--obsidian`, `--wiki`, Neo4j cypher, graphml.

## Ideas & Directions
- **A — Plain adopt.** `graphify install` once; `/graphify .` per repo by hand; MCP serves
  queries. Zero build. Manual freshness, no cross-repo convention, no brain integration.
- **B — Brain-wired (natural move).** Thin `/graph` command + standardized `graphify-out/`
  convention + `install.sh` registration + freshness policy. Mirrors the frontend-domain recipe.
- **C — Two-track by repo type.** Code repos: local extraction, commit-hook freshness, MCP
  queries — free. Vault: LLM extraction, on-demand only, deferred; `--obsidian` if/when it
  becomes one. Honors the cost/privacy split.

## Recommendations
**Pilot before you wire** — don't plan elaborate integration around a tool not yet watched run.
1. `graphify install` + `/graphify .` on **one code repo** (free, local). Live with the
   MCP-query workflow: does Claude query it? Do answers change? Is the global hook helpful or noisy?
2. **Only then** decide on brain wiring (Direction B).
3. **Vault comes last**, on-demand only, once code repos prove value.

Net: **A as pilot → B if it earns it → C's vault track deferred.**

## Suggested Decisions (confirm before /plan)
1. **Pilot-first vs. commit to brain wiring now** — lean pilot-first.
2. **Defer the vault until code repos prove value** — lean yes (it's the paid track).
3. **Scope of "active repos"** — named fixed list, or a convention (any repo where you run it)?

## Open Questions (for /plan)
- **Freshness mechanism** — git `post-commit` hook vs `--watch` vs manual `--update` (not on
  every edit for the vault).
- **`graphify-out/` git policy** — commit `graph.json` for portability, or gitignore the whole
  dir? (`cost.json`/`cache/` definitely gitignored.)
- **Global pre-tool-use hook** — keep graphify's nudge on for all sessions, or scope it?
- **Integration home** — a new `domains/` entry, a top-level command, or just an `install.sh` addition?

## Next Steps (what /plan needs)
- Confirm the three Suggested Decisions.
- Resolve the four Open Questions (freshness, git policy, hook scope, integration home).
- Pick the pilot repo.

---

# Brainstorm — Project & Task Tracker (fleet-driven)
Date: 2026-07-26
Status: Draft
Feeds: a future `/plan` section; extends the Agent Dashboard (Pillar C v2) in docs/plan.md.

## Problem / Opportunity
The dashboard today **observes** (pipeline board detects project phase from docs, read-only) and
**spawns** ad-hoc fleet runs. The opportunity: turn it into a **stateful work-tracking system** —
projects → tasks → issues with real status, history, and updates — where the fleet is a *team that
pulls work and delivers it*. GitLab-at-work, but personal, self-owned, and wired to the fleet.
Shift: from *detecting* state to *owning* state.

## Goals
- Represent **projects, tasks, issues, and their state** for personal projects, in the dashboard.
- **Modular change/update tracking** — a history of what changed on each item.
- **Fleet as a team** — agents take tasks and produce deliverables, moving task state.
- Nest cleanly under the existing pipeline board (project-phase) as the finer grain within a project.

## Audience
Personal, single-user, across the repos in ~/Desktop/Code. Local-first, private.

## Constraints
- Must integrate with the existing `web/` dashboard (the front end).
- Statefulness = a write path + datastore (the current pipeline is read-only doc-detection).
- Reuse what exists: run registry (D6 SQLite), D4/D8 run+approval, D9 queue, pipeline detector.
- Not all projects are GitHub repos; some data is private → external service can't be the only truth.
- Scope risk: this is a personal Linear/GitLab — must phase to a lean MVP.

## Ideas & Directions

### Backing store (source of truth)
- **A. Local SQLite (recommended).** Extend the run registry: tasks live beside runs, so task↔run
  links and cross-project queries are trivial; rich, fast dashboard. Private/offline. Not
  git-versioned on its own → covered by an append-only updates log.
- **B. File-based in each repo.** Tasks as markdown/YAML (like docs/). Git-versioned, portable,
  diffable. But cross-project queries + fleet-linking + rich UI get painful; concurrent writes tricky.
- **C. GitHub-backed (Issues/Projects via MCP).** Real issues↔branches↔PRs, familiar, portable. But
  ties each project to a GitHub repo + hosted service; not all projects qualify.
- **Recommendation: A as the operational core, with C as an opt-in per-repo sync later** (mirror
  tasks↔issues, link runs↔PRs where a repo exists — where the now-available GitHub MCP earns its place).

### Fleet autonomy (the "team" behavior)
- **v1 — assign explicitly (recommended start).** You (PM) assign task→persona; it becomes a run
  (read-only auto-runs; writes via D8 + scoped dir); on finish it updates the task (→ review, linked
  run, summary). A task = a persistent, stateful fleet run.
- **v2 — backlog pull.** "ready" tasks flow into the D9 queue as capacity frees — feels like a team.
- **v3 — planner persona (defer).** Decomposes a deliverable into tasks and dispatches workers.
  Ambitious; only after v1/v2 are solid; strong guardrails.

### Model richness
- **Lean core (recommended):** `Project → Task(type: task|issue|bug, status[backlog|ready|doing|
  review|done], assignee-persona, scoped-dir, linked-run-ids, phase-tag, agent-brief, acceptance) →
  Updates(append-only event log)`. Covers projects/tasks/issues/state + modular change-tracking.
- **Full tracker (later):** labels, milestones, subtasks, comment threads, branch/PR links.

## Recommendations (converged)
1. **SQLite core** (extend `dashboard/registry.py`'s DB) with `projects`, `tasks`, `task_updates`;
   append-only updates = the change history / activity feed. GitHub sync opt-in later.
2. **Phased fleet autonomy:** assign (v1) → backlog-pull via D9 (v2) → planner (v3, deferred).
3. **Lean model**, one `Task` entity with a `type` field; route completion to `review`, never auto-close.
4. **Seed tasks from `/plan` milestone tables** — brain's planning already produces the task list;
   and seed projects from the pipeline detector + projects.json.
5. **UI:** a Kanban/issue board in `web/` (reuse pipeline-board CSS) + task detail with update log;
   pipeline phase board stays the top-level lens, tasks are the drill-down.

## Suggested Decisions (confirm before /plan)
- Backing store = **local SQLite core**, GitHub sync deferred/opt-in. (confirm)
- Fleet autonomy = **phased, start with explicit assign**. (confirm)
- Model = **lean single Task entity + append-only updates**. (confirm)
- Tasks carry an explicit **agent-brief + acceptance criteria** (not just a title). (confirm)

## Open Questions (for /plan)
- **Task→run lifecycle:** exact status transitions and which are agent-driven vs. user-driven; does
  a finished run auto-move task → review, and does the Reviewer persona auto-review?
- **Scoped dir per task:** default to the project root, or a per-task working dir/branch?
- **Git integration depth (later):** branch-per-task? PR links? which repos opt in?
- **Seeding:** how milestone tables in docs/plan.md map to tasks (parse format / a marker?).
- **Where the code lives:** extend `dashboard/` (tasks module + tables + endpoints + board view).
- **Concurrency:** conflict handling when you and an agent both change a task.

## Next Steps (what /plan needs)
- Confirm the four Suggested Decisions.
- Resolve the task↔run lifecycle + scoped-dir questions (they shape the fleet integration).
- Define the lean schema (projects/tasks/task_updates) and the v1 endpoints + board view.
- Phase it: v1 (tracker + manual assign + run-linking + board) → v2 (backlog pull) → v3 (planner).
