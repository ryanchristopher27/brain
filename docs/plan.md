# Plan — Consolidate Frontend Resources into Brain

Date: 2026-06-06
Status: Active
Brainstorm: inline (mini-brainstorm folded in via /plan)

## Overview

Merge the frontend-design resources from two external repos into a single, brain-native
`domains/frontend/` domain that activates automatically on frontend projects and installs
globally through `install/install.sh`.

Sources (both live under `~/Desktop/Code/`):

- **ui-ux-pro-max-skill** (MIT, NextLevelBuilder) — a *data-driven* design suite. Value is a
  queryable knowledge base: CSVs covering 161 color palettes, 57 font pairings, 67 UI styles,
  99 UX guidelines, 25 chart types, ~1900 Google Fonts, plus pure-Python-stdlib BM25 search
  scripts (`core.py`, `search.py`, `design_system.py`) and 6 SKILL.md skills (ui-ux-pro-max,
  design, design-system, ui-styling, brand, slides, banner-design). Ships a TS CLI installer
  we are **not** taking.
- **impeccable** (Apache 2.0, Paul Bakaus) — a *command-driven* design suite. Value is a design
  vocabulary: 1 skill with 23 commands (`craft`, `shape`, `critique`, `audit`, `polish`,
  `animate`, `distill`, …), 7 domain reference files (typography, color-and-contrast,
  spatial-design, motion-design, interaction-design, responsive-design, ux-writing), brand-vs-
  product registers, and a 27-rule deterministic anti-pattern detector (Node `.mjs`). Ships a
  browser extension + live-iteration loop we are **not** taking.

The two are complementary: impeccable is the *opinionated spine* (rules + verbs + linting),
ui-ux-pro-max is the *data backing* (concrete palettes, fonts, styles to pull from). The merge
layers them rather than picking a winner.

## Goals & Success Criteria

**Goals**
- A single `domains/frontend/` domain consolidating both sources, following brain conventions.
- Auto-activates on frontend projects; manually overridable via `domains: frontend` in CLAUDE.md.
- A curated set of design commands (not all 23) backed by always-on domain rules.
- The ui-ux-pro-max CSV knowledge base + Python search usable from within the domain.
- The impeccable anti-pattern detector runnable as an objective design-lint step.

**Success Criteria**
- [x] `domains/frontend/` exists with `README.md`, `detect.md`, `rules.md`, `commands/`,
      `references/`, `cursor-rule.mdc`, plus `data/` + `scripts/` for the ported tooling.
- [x] Frontend domain auto-detects (e.g. `package.json` + a frontend framework) per `detect.md`.
- [x] `install/install.sh` registers the new domain commands globally with no errors. (Auto-synced
      via the brain post-edit hook; verified `~/.claude/commands/design.md` symlink resolves.)
- [x] At least one command invokes the ui-ux-pro-max search and returns CSV-backed results.
- [x] The anti-pattern detector runs against a sample file and reports rule hits.
- [x] No unattributed copying — `LICENSE`/`NOTICE` preserved for both sources.
- [x] `BRAINSTORM.md` updated with the consolidation decision. (Domain has no `workflow/*/spec.md`;
      that convention is for workflow phases, not domains.)

## Scope

### In Scope
- New `domains/frontend/` domain (rules, detection, references, curated commands, Cursor rule).
- Port ui-ux-pro-max **data CSVs + Python search scripts** (the meaningful subset).
- Port impeccable **anti-pattern detector** (`detect.mjs` + detector data).
- Distill both repos' skills/references/commands into brain-native markdown.
- Merge overlapping guidance (typography, color, spacing, motion) into unified references.
- Wire everything through `install/install.sh`; update `BRAINSTORM.md` and domain README index.

### Out of Scope
- ui-ux-pro-max TS CLI (`uipro-cli`) and its installer machinery.
- impeccable browser extension, live-iteration loop/server, Astro website, and its test suite.
- The full 23-command impeccable surface (most fold into rules; only a curated core ship).
- Multi-platform skill exports (windsurf/kiro/gemini/etc.) — brain targets Claude Code + Cursor.
- Rewriting the search engine or detector logic — port as-is, adapt only paths/invocation.

## Tech Stack & Architecture

**Decision: single `domains/frontend/` domain.** (User-selected.) Fills brain's pre-declared
frontend slot; one place to maintain; install.sh already iterates `domains/*/commands/`.

**Layered content model** — impeccable spine + ui-ux-pro-max data:
- `rules.md` = always-on behavior, anchored on impeccable's anti-pattern guidance and registers,
  enriched with ui-ux-pro-max's priority categories (a11y → touch → perf → style → …).
- `references/` = the merged deep-dive files (typography, color, motion, spatial, interaction,
  responsive, ux-writing), each cross-linking the relevant CSV data.
- `data/` + `scripts/` = ported ui-ux-pro-max knowledge base; commands shell out to it.
- `scripts/detector/` = ported impeccable anti-pattern detector; the audit command shells out.

**Tooling stays in-repo, referenced by path.** `install.sh` symlinks command `.md` files into
`~/.claude/commands/` but does **not** copy `data/`/`scripts/`. So commands must reference the
scripts by their absolute path inside the brain repo (the brain dir is stable). Both ported
toolchains are dependency-light: the Python search is **stdlib-only** (csv/re/math — no pip),
the detector is a self-contained Node `.mjs` (needs `node`). Both documented as soft prereqs in
`detect.md`/`README.md`; commands degrade to pure-markdown guidance if the runtime is absent.

**Commands as one namespaced verb, not six top-level commands.** (Recommended — see Open
Questions.) Mirror impeccable's pattern with a single `/design` (or `/fe`) command that takes a
subcommand: `/design craft`, `/design critique`, `/design audit`, `/design polish`,
`/design shape`, `/design system`. Avoids polluting brain's global command namespace and
collisions with future workflow verbs, while preserving the design vocabulary.

## Milestones

| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| M1 | Domain scaffold | Copy `domains/_template/` → `domains/frontend/`; write README, detect.md skeleton | — |
| M2 | Port data + scripts | Bring ui-ux-pro-max CSV subset + Python search; verify search runs from brain path | M1 |
| M3 | Port detector | Bring impeccable `detect.mjs` + detector data; verify it lints a sample file | M1 |
| M4 | Merge references | Distill + merge the 7 impeccable refs with ui-ux-pro-max data into `references/` | M1, M2 |
| M5 | Author rules.md | Unified always-on rules: impeccable spine + ui-ux-pro-max priority categories | M4 |
| M6 | Curated commands | Single `/design` command w/ curated subcommands wired to scripts + detector | M2, M3, M5 |
| M7 | Detection + Cursor | Finalize `detect.md` signals; write `cursor-rule.mdc` with frontend globs | M5 |
| M8 | Wire + document | Re-run `install.sh`; update `BRAINSTORM.md`, domain README index, attribution | M6, M7 |

## Task Breakdown

### M1 — Domain scaffold
- `cp -r domains/_template domains/frontend`, then fill `README.md` (what it covers / when it fires).
- Draft `detect.md`: primary signals `package.json` + framework dep (react/vue/svelte/next/astro)
  or `tailwind.config.*`, `.tsx/.jsx/.vue/.svelte` files, `components/` dir; manual override
  `domains: frontend`. Note Python/Node as soft prereqs for the tooling.

### M2 — Port data + scripts
- Copy the meaningful CSVs into `domains/frontend/data/`: `styles, colors, typography, charts,
  ux-guidelines, google-fonts, ui-reasoning, products, landing, icons, app-interface,
  react-performance`. Skip `design.csv`/`draft.csv` (large source/draft dumps) pending review.
- Copy `core.py`, `search.py`, `design_system.py` into `domains/frontend/scripts/`; fix the
  `DATA_DIR` relative path if needed; confirm `python3 search.py "dashboard" --domain style` works.

### M3 — Port detector
- Copy impeccable `.claude/skills/impeccable/scripts/detect.mjs` + its `detector/` dir into
  `domains/frontend/scripts/detector/`.
- Smoke-test: `node detect.mjs <sample.css/html>` reports rule hits; record the invocation.

### M4 — Merge references
- For each topic (typography, color, motion, spatial, interaction, responsive, ux-writing):
  take impeccable's reference as the base, fold in ui-ux-pro-max specifics, add a "Data" pointer
  to the relevant CSV + the search command to query it. De-duplicate overlapping rules.
- Carry over impeccable's brand-vs-product register distinction as `references/register.md`.

### M5 — Author rules.md
- Open with the priority ladder (a11y → touch/interaction → performance → style → layout →
  typography/color → motion), each rule phrased as always-on behavior with a "verify with" hook
  (detector rule id or search query). Keep it scannable; deep detail lives in `references/`.

### M6 — Curated commands
- Author `domains/frontend/commands/design.md` (single command, subcommand-dispatched):
  `craft, shape, critique, audit, polish, system`. `audit` calls the detector; `system` calls the
  ui-ux-pro-max design-system generator. Each subcommand reads the matching reference first.
- Fold the remaining ~18 impeccable verbs (animate, distill, bolder, quieter, …) into `rules.md`
  as named techniques the command can apply, rather than separate commands.

### M7 — Detection + Cursor
- Finalize `detect.md`; write `cursor-rule.mdc` with `globs:` for frontend file types so Cursor
  auto-applies the rules natively.

### M8 — Wire + document
- Re-run `install/install.sh`; confirm the `design` command registers and detection works.
- Preserve attribution: keep both source `LICENSE`s, add a `NOTICE` crediting ui-ux-pro-max (MIT)
  and impeccable (Apache 2.0) in `domains/frontend/`.
- Update `BRAINSTORM.md` (decision + structure) and `domains/README.md` "Existing Domains" table.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Script paths break once commands are symlinked into `~/.claude` | Med | Med | Reference scripts by absolute brain-repo path; test post-install, not just in-repo |
| Python/Node missing on a machine | Med | Low | Soft prereq; commands degrade to markdown guidance, never hard-fail |
| Two sources contradict (e.g. font-count, spacing rules) | High | Med | Impeccable spine wins on conflicts; note exceptions in `rules.md` |
| Licensing/attribution lost in the merge | Low | High | Dedicated M8 task; preserve LICENSE + add NOTICE before any commit |
| Command name collisions in global namespace | Med | Med | Single namespaced `/design` command instead of 6 top-level verbs |
| Scope creep from impeccable's 1886 files | Med | Med | Strict allowlist: only detector + refs; everything else out of scope |

## Dependencies
- `python3` (stdlib only) — ui-ux-pro-max search/design-system scripts.
- `node` — impeccable anti-pattern detector.
- `jq` — already required by `install.sh` for settings merge.
- Source repos remain available locally during the port (read-only; not git submodules).

## Open Questions
_All resolved 2026-06-06 — see Decisions Log. None blocking._

## Decisions Log

| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Target structure | Single `domains/frontend/` | User-selected; fills brain's frontend slot; install.sh ready | 2026-06-06 |
| What to port | Markdown baseline + ui-ux-pro-max data/scripts + impeccable detector | User-selected; skip live browser loop | 2026-06-06 |
| Command count | Curated core set, rest → rules | User-selected; keeps command list focused | 2026-06-06 |
| Skip CLI/extension/site | Out of scope | User wants the *resources*, not the delivery infra | 2026-06-06 |
| Conflict resolution | Impeccable spine wins; ui-ux-pro-max backs with data | Impeccable is opinionated + anti-pattern-tied; UPM is reference data | 2026-06-06 |
| Command namespacing | Single `/design` w/ subcommands | Avoid global namespace pollution / future collisions | 2026-06-06 |
| Curated subcommands | `craft, shape, critique, audit, polish, system` | Confirmed; highest-value verbs, rest fold into rules | 2026-06-06 |
| Extra UPM skills | brand → register reference; slides/banner → out of scope | Not core "frontend dev"; brand register is reused | 2026-06-06 |
| design.csv / draft.csv | Skip | Large source/draft dumps, not the curated knowledge base | 2026-06-06 |
| Vendor vs submodule | Copy the curated subset in | Simpler; decouples brain from upstream churn | 2026-06-06 |
| M2: include `data/stacks/` | Yes (16 per-stack CSVs, 264K) | Plan's flat CSV list missed the subdir; `--stack` is documented in the command spec — omitting it ships a broken feature | 2026-06-06 |
| M4: synthesize refs vs copy | Synthesize from spine + topic command-refs | impeccable's 7 named topic ref files don't exist (stale README link); content lives in SKILL.src.md + command-refs. User-approved | 2026-06-06 |
| M6: script-path resolution (W2) | `/design` resolves `$FE` via `realpath` of the symlinked command file, w/ absolute fallback | Closes the plan's path-break risk; works through install.sh symlink (verified). Rules/refs paths stay illustrative | 2026-06-06 |

## Handoff Readiness (for /scaffold)
- Tech stack decided: ✅ markdown + ported Python (stdlib) + Node detector under `domains/frontend/`.
- Top-level structure clear: ✅ `domains/frontend/{README,detect,rules,cursor-rule}.md +
  commands/ + references/ + data/ + scripts/`.
- Entry points identified: ✅ `commands/design.md` (the verb), `rules.md` (always-on), search +
  detector scripts (the tooling). All open questions resolved — **ready for /scaffold.**
