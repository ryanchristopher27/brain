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

---

# Plan — Local Agent Fleet + Voice Interface
Date: 2026-07-19
Status: Draft
Brainstorm: inline (mini-grounding folded in below)

## Overview
Two coupled initiatives that share one backbone:

1. **Agent Fleet** — expand brain from a rules/skills vault into a *fleet host*: a
   curated library of Claude Code **subagents**, a populated set of **MCP servers**,
   **multi-agent orchestration** patterns, and **background/scheduled agents**. All
   brain-native, wired by `install.sh`.
2. **Voice Interface** — talk to Claude instead of typing. Recommended shape: a
   **standalone local voice daemon that drives Claude Code in headless mode**
   (`claude -p`). Architecturally standalone, functionally "voice for Claude Code" —
   because it speaks to the *same* subagents + MCPs the Fleet work produces.
3. **Voice Visualizer** — a local web page that is a **live visual embodiment of the voice
   agent you're talking to**: agent state (listening / thinking / speaking), active persona,
   an animated orb/waveform, and a rolling transcript. It *reflects* the session — it is
   **not** a chat box and **not** a control panel. It's a companion window to the voice.

The coupling is the point: voice is a thin I/O shell over the fleet, and the visualizer is a
thin window over the voice. Build the fleet, and both surfaces inherit it for free.

## Goals & Success Criteria
- **G1 — More agents, reachable.** A curated, installable set of subagents + MCP servers
  live in brain; `install.sh` syncs them globally; `/agents` and MCP tools show them in a
  fresh Claude Code session.
- **G2 — Orchestration.** A documented pattern (rule + role subagents) for fanning one
  request out to several agents in parallel and merging results.
- **G3 — Background agents.** At least one headless/scheduled agent runs a task unattended
  and reports back, with scoped permissions.
- **G4 — Voice round-trip.** Push-to-talk → local STT → Claude (headless, agent-aware) →
  spoken reply, end-to-end on the M2 Pro, no cloud required.
- **G5 — Visualizer mirrors the session.** A local web page shows, in real time, the voice
  agent's state (listening/thinking/speaking), active persona, and live transcript — driven
  off the same voice core, no separate integration.
- **Success = ** one spoken request ("research X and summarize") reaches a subagent through
  the voice daemon, comes back as speech, and the visualizer reflects each state live —
  proving all three surfaces connect.

## Scope
### In Scope
- New `agents/` top-level resource type in brain + install sync to `~/.claude/agents/`.
- A curated seed library of subagents (roles + orchestrator).
- Populating `mcps/shared/` and `mcps/personal/` with real, env-var'd MCP servers.
- An orchestration rule/skill; a background-agent runner + scheduling config.
- A self-contained `voice/` module (local STT via whisper.cpp, TTS via `say`/Piper,
  headless Claude bridge, pluggable cloud backends) that **emits session-state events**.
- A `web/` visualizer: local page that renders the live voice-agent state, active persona,
  animated orb/waveform, and rolling transcript (built with brain's `frontend` domain).
- Docs: CLAUDE.md updates, BRAINSTORM.md decision entries, README/MCP tables.

### Out of Scope (v1)
- Wake-word / always-listening (push-to-talk only for v1).
- Barge-in / mid-response interruption.
- **A chat webpage** — the visualizer reflects the voice session; it is not a text-chat UI.
- **A fleet control panel** — the visualizer displays, it does not trigger/drive agents.
- Cloud-hosted / remote fleet. Everything runs on this machine.
- Voice-initiated destructive tool use without confirmation (safety — see Risks).

## Tech Stack & Architecture

### Recommended decisions (from grounding)
| Question | Recommendation | Why |
|----------|----------------|-----|
| Voice mode | Standalone daemon driving **headless Claude Code** (`claude -p --output-format stream-json`) | Injecting into the interactive TUI is brittle; headless is scriptable and *inherits every subagent + MCP* from the fleet work. Best of both the options you picked. |
| STT/TTS | **Local-first, pluggable.** STT = whisper.cpp (Metal-accel on M2 Pro, `small.en`/`base.en`); TTS = macOS `say` baseline → Piper optional. Cloud (Deepgram/ElevenLabs/OpenAI) selectable via env. | Privacy, zero per-use cost, M2 Pro handles it; matches brain's local-first ethos while leaving a quality upgrade path. |
| Where it lives | **Per-piece.** Agent configs (subagents, MCP JSON, orchestration rules, bg-agent config) → *inside brain*. Voice daemon → new top-level `voice/` module *in the brain repo* but self-contained (own venv/deps), not treated as brain "resources." | brain is a config vault — subagents/MCPs are exactly its job; a running daemon with audio/binary deps is a different animal but should still be one `install.sh` away and agent-aware. |
| Daemon language | **Python** (mambaforge python3 present) | Strongest local-ML + audio ecosystem; trivial `claude -p` subprocess. Node available as fallback. |

### Component map
```
brain/
├── agents/                     # NEW resource type (mirrors commands/)
│   ├── _template/agent.md
│   ├── personas/               # Scout, Reviewer (collaborative) · Builder (autonomous)
│   └── background/             # Operator + headless/scheduled agent defs + runner
├── mcps/
│   ├── shared/                 # (lean — most starter MCPs duplicate CC natives)
│   └── personal/               # github, notion, playwright (env-var secrets, gitignored)
├── universal/rules.md          # + orchestration ("when/how to fan out") rule
├── voice/                      # NEW voice core: audio I/O + bridge + event stream
│   ├── daemon.py               # hotkey → capture → STT → claude -p → TTS
│   ├── stt/  tts/  bridge/     # pluggable backends behind one interface
│   ├── server.py               # local websocket/HTTP — emits session-state events
│   ├── config.toml  .env.example
│   └── requirements.txt / setup
├── web/                        # NEW Pillar C: live visualizer (not chat, not control)
│   ├── index.html + app        # orb/waveform + state + persona + rolling transcript
│   └── (built via brain frontend domain / /design)
└── install/install.sh          # EXTEND: sync agents/ → ~/.claude/agents/; voice bootstrap
```

### Data flow
`hotkey ▸ mic capture ▸ whisper.cpp (STT) ▸ claude -p (agent-aware, resumes session) ▸ stream tokens ▸ say/Piper (TTS)`
In parallel, the voice core emits state events (`listening → thinking → speaking`, active
persona, partial transcript) over a **local websocket**; the `web/` visualizer subscribes
and renders them. One backend, two frontends (audio + visual) — no second integration.

### Personas (safety = which agent you summon, not a global switch)
Each persona is a subagent whose tool allowlist is enforced in frontmatter — posture is
structural, not trust-based. Voice defaults to **Scout**; autonomous personas are summoned
explicitly.
| Persona | Posture | Tools | Use |
|---------|---------|-------|-----|
| **Scout** | Collaborative, read-only | Read/Grep/Glob, web, search | Default for voice — research, explain, propose |
| **Reviewer** | Collaborative, read + comment | Read + PR comments | Critique, review diffs |
| **Builder** | Autonomous, scoped | Read/Write/Edit/Bash within a project | Multi-step tasks, logs everything |
| **Operator** | Autonomous, background | Tightest scope + full logging | Unattended/scheduled jobs (A4) |

## Milestones
Three pillars. A3/A4 depend on A1; the voice bridge (B4) is where A and B converge; the
visualizer (C) is a thin window over B4's event stream. A and B build in parallel until B4;
C follows B4.

| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| A1 | Agent resource type + personas | Add `agents/` + `_template`; extend `install.sh` to symlink `*.md` → `~/.claude/agents/`; document in CLAUDE.md; author the **Scout / Reviewer / Builder** personas with frontmatter tool allowlists | install.sh |
| A2 | MCP fleet (lean) | Populate `mcps/personal/` with **github, notion, playwright** (env-var secrets); README table; verify merge + tools appear. Skip natives-duplicating MCPs (filesystem/fetch/git/memory) | — |
| A3 | Orchestration layer | A universal rule on when/how to fan personas out & merge results; optional `/fleet` verb; Scout/Builder as the parallelizable workers | A1 |
| A4 | Background agents | **Operator** persona (tightest scope + logging); schedule via Claude Code **`/schedule`** (primary); launchd→`claude -p` wrapper only as escape hatch; one working unattended task | A1, A2 |
| B1 | Voice daemon skeleton | `voice/` module: push-to-talk hotkey, mic capture (sounddevice+portaudio), audio plumbing, config.toml, env backend selection | — |
| B2 | Local STT | whisper.cpp integration (install + model), transcribe captured audio | B1 |
| B3 | TTS | `say` baseline + optional Piper; speak text; incremental/streamed playback | B1 |
| B4 | Claude bridge (convergence) | Wire daemon → `claude -p` streaming headless with session continuity; **defaults to the Scout persona** (read-only); Builder/Operator summoned by explicit spoken command. Emit **session-state events** (`server.py` websocket) so surfaces can subscribe. Voice now reaches all A1–A3 agents + A2 MCPs | B1–B3, A1–A2 |
| B5 | Cloud backends (stretch) | Optional Deepgram STT / ElevenLabs/OpenAI TTS adapters behind the same interface, env-gated | B4 |
| C1 | Voice visualizer | `web/` page subscribes to the B4 event stream; renders agent state (listening/thinking/speaking), active persona, and rolling transcript. Local-only page | B4 |
| C2 | Visual polish (stretch) | Animated orb/waveform tied to audio level; per-persona visual identity (Scout vs Builder). Built via `/design` (frontend domain) | C1 |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Voice-driven headless agent runs tool calls with no human to approve prompts | High | High | v1 voice sessions run a **constrained permission profile** (read-mostly + explicit spoken confirmation before writes/commands); no `--dangerously-skip-permissions` |
| whisper.cpp / portaudio build friction on macOS | Med | Med | Prefer Homebrew formulae (`whisper-cpp`, `portaudio`) or `pywhispercpp`; validate in B2 early before wiring |
| Local STT+LLM+TTS latency = awkward UX | Med | Med | Stream Claude tokens and speak incrementally; keep STT model small (`base.en`); allow cloud STT swap (B5) |
| MCP secret sprawl / leaked tokens | Med | High | brain's env-var-only rule + `personal/.gitignore` already enforce this; keep all creds in shell profile |
| Background agents writing unattended | Med | High | Scoped allowlist, dry-run first, full logging, start read-only |
| `install.sh` has no agents concept — regressions | Low | Med | Extend it mirroring the existing command-symlink path; idempotent + backup already built in |

## Dependencies
- **System (to install):** `whisper-cpp` (or `pywhispercpp`), `portaudio`, optionally `piper-tts`, `ffmpeg`, `jq` (already required by install.sh — verify present).
- **Present:** `claude` 2.1.167, `say`, `python3` (mambaforge), `node`.
- **Accounts/tokens (personal MCPs):** GitHub PAT, Notion token — env vars only.
- **macOS permissions:** Microphone + Accessibility (for global hotkey) grants for the daemon.

## Open Questions
_Resolved 2026-07-19: MCP shortlist (lean: github/notion/playwright), safety model
(persona-bound permission profiles), scheduling (`/schedule` primary). See Decisions Log._
1. **Other daily services?** — Beyond GitHub/Notion/Playwright, is there another service you
   live in (Linear, Slack, a database) worth an MCP? If so it's a quick add to A2.
2. **Push-to-talk key** — pick a global hotkey (default suggestion: a Fn/hyper key).
   Wake-word deferred to post-v1.
3. **Repo boundary** — confirm the `voice/` daemon lives *in the brain repo* (recommended)
   vs a separate repo.

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Voice architecture | Standalone daemon over **headless Claude Code** | Scriptable + inherits all fleet agents/MCPs; avoids brittle TUI injection | 2026-07-19 |
| STT/TTS | Local-first (whisper.cpp + `say`/Piper), cloud pluggable via env | Privacy, no per-use cost, M2 Pro is capable, local-first ethos | 2026-07-19 |
| Where it lives | Agent configs in brain; `voice/` self-contained module in brain repo | brain hosts config; daemon is runtime but stays one install away | 2026-07-19 |
| Daemon language | Python | Best local-audio/ML story; simple `claude -p` subprocess | 2026-07-19 |
| Agent resource type | New `agents/` top-level dir synced by install.sh | Mirrors existing commands pattern; closes the install.sh gap | 2026-07-19 |
| MCP shortlist | Lean: **github + notion + playwright**; skip filesystem/fetch/git/memory | Most starter MCPs duplicate Claude Code natives; only external-reach + browser access add real capability (browser ties to the recurring visual-feedback gap) | 2026-07-19 |
| Safety model | **Persona-bound permission profiles**, not a global posture; enforced via subagent tool frontmatter | Scales cleaner — Scout/Reviewer read-only, Builder/Operator autonomous+scoped; voice defaults to Scout | 2026-07-19 |
| Background scheduling | Claude Code **`/schedule`** primary; launchd→`claude -p` only as escape hatch; skip cron | `/schedule` is fleet-aware + near-zero plumbing; launchd reserved for jobs that must fire with CC closed; cron superseded on macOS | 2026-07-19 |
| Web surface (Pillar C) | **Live voice visualizer, not a chat or control panel**; shares the voice core via a local event stream; built with brain's frontend domain | A chat webpage would rebuild claude.ai worse; the unmet need is a visual embodiment of the voice session. One backend, two frontends avoids a second integration | 2026-07-19 |

## Handoff Readiness (for /scaffold)
- Tech stack decided: ✅ Python voice daemon + whisper.cpp/`say` + headless `claude -p`; local websocket event stream; `web/` visualizer via frontend domain; markdown subagents + JSON MCPs + bash install glue.
- Top-level structure clear: ✅ `agents/`, populated `mcps/`, `voice/`, `web/`, extended `install.sh`.
- Entry points identified: ✅ `voice/daemon.py` + `voice/server.py` (voice + event stream), `web/index.html` (visualizer), `agents/personas/*` + `agents/background/` (fleet), `install.sh` (wiring).
- **No hard blockers** — all three remaining open questions have safe defaults. Ready for /scaffold once you confirm them.
