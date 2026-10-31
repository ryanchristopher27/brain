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

---

# Plan — Agent Dashboard (Pillar C v2)
Date: 2026-07-23
Status: Draft
Brainstorm: inline (mini-grounding folded in)

## Overview
Evolve the `web/` voice visualizer into a **local agent dashboard** — a high-level view of the
agents you control and what they're working on, with the ability to act on them. Explicitly
**not a chat interface**: it shows status and activity, not conversation transcripts. The C2
orb is preserved as the **"active session" panel** inside a larger layout.

This reopens — and deliberately supersedes — the original Pillar C decision that the web
surface would be "a voice visualizer, not a control panel." The user has chosen **full
control**, so the dashboard becomes a real (local-only) control surface.

## Goals & Success Criteria
- **G1 — See the fleet.** One page shows: the live voice session (orb + active persona +
  current task, high-level), the persona roster, background-job history, and scheduled jobs.
- **G2 — Know what's running.** "What they're working on" is truthful — the current voice
  turn, any dashboard-spawned run, and background jobs; each with status.
- **G3 — Act on agents.** Trigger a background job, spawn a persona on a task, stop a running
  run, enable/disable a scheduled job — from the dashboard, safely.
- **G4 — Stay safe.** The control server binds `127.0.0.1` only; write-capable spawns are
  scoped and confirmed; never `--dangerously-skip-permissions`.
- **Success =** open the dashboard, watch a live voice turn in the active-session panel, see the
  last background digest and its report, and kick off a new read-only run from a button.

## Scope
### In Scope
- A local **control server** (backend) that serves the dashboard, hosts the event hub, exposes
  read APIs (roster, jobs, runs) and — phase 2 — action APIs (spawn/stop/schedule).
- Restructured `web/` dashboard: active-session panel (orb), persona roster, jobs, schedule.
- A **run registry** (phase 3) that voice, background jobs, and dashboard-spawned runs write to,
  so activity is unified and live.
- Reuse of the runner safety model for any spawned run.

### Out of Scope (v1)
- **A chat interface** — no conversation transcript UI; high-level status only.
- Observing agents spawned *inside* an interactive Claude Code session (Task tool) — the
  dashboard can't see those unless they write to the registry. Be honest about this.
- Remote/multi-user access, auth beyond local-only bind, hosted deployment.
- Standing "agent daemons" — agents run per-invocation; there is nothing to keep alive.

## Tech Stack & Architecture

### Recommended decisions
| Question | Recommendation | Why |
|----------|----------------|-----|
| Backend | **FastAPI + uvicorn** (in the voice venv) | Clean HTTP action API + websocket + static serving + typed JSON in one place; the stdlib ws-only hub would get unwieldy with a REST/control surface. |
| Frontend | **Keep vanilla JS** (extend current `web/`) | The orb + a handful of panels don't need a framework/build step; the current page is dependency-free and working. React/Vite ruled out (build overhead for a local single-user tool). |
| Where the backend lives | **New top-level `dashboard/`** (Python), consuming the voice event stream | The dashboard spans the whole fleet (agents + voice + jobs), not just voice; keep voice able to run standalone and *publish* to the dashboard when present. |
| "Start an agent" | **Spawn a headless `claude -p` run** (or trigger a job), tracked by the process manager | Personas aren't standing processes; a run is the unit. Reuses the runner pattern. |
| Data model | Agents (personas) + **Runs** (id, agent, task, source, status, times, report, pid) | A "run" unifies voice turns, background jobs, and dashboard-spawned work. |

### Architecture shift
```
        ┌──────────────── dashboard/ (FastAPI) ────────────────┐
        │  event hub (ws)  ·  read API  ·  action API           │
        │  process manager (spawn/stop headless runs)           │
        │  run registry (append-only JSONL, tailed)             │
        └───▲───────────────▲───────────────▲──────────────────┘
   voice daemon        background         web/ dashboard
  (publishes its     runner.sh           (renders panels,
   session events)   (writes runs)        sends actions)
```
The control server becomes the central hub. The voice daemon publishes its session events to it
(instead of hosting its own ws); `web/` renders panels and issues actions. Reality check baked
in: the dashboard reports what it can actually see (voice + background + what it spawns) — it is
not omniscient about in-session Task spawns.

### Dashboard layout (high-level, product register)
- **Active session** (the orb, absorbed): active persona, state, current task one-liner.
- **Personas**: roster from `agents/` — name, posture, tools, last-used.
- **Runs / jobs**: recent runs + background jobs from `~/.claude/brain-bg-logs/` + registry —
  label, agent, status, time, link to report.
- **Schedule**: launchd jobs + next run; enable/disable.

## Milestones
Three phases. Phase 1 ships a real read-only dashboard; 2 adds control; 3 enriches the data.

| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| D1 | Control server foundation | `dashboard/` FastAPI app: serve `web/`, host the ws hub, read APIs (roster, jobs). Voice daemon publishes its events to it (refactor the ws host; keep a standalone fallback) | voice B4 |
| D2 | Dashboard shell + active-session panel | Restructure `web/` into a panel layout; the C2 orb becomes the live "active session" tile (persona · state · current task — not the transcript) | D1 |
| D3 | Fleet & jobs panels (read) | Persona roster (agents/), background-job history + latest report (brain-bg-logs), scheduled-job status (launchd). Read-only | D1 |
| D4 | Action API + process manager | Spawn headless persona/job runs, track status, stop them; safety posture (127.0.0.1-only, scoped tools, confirm, no skip-perms) | D1 |
| D5 | Dashboard controls | Buttons/wiring for run-job / spawn-on-task / stop / enable-schedule, each with a confirm step | D4 |
| D6 | Run registry (richer live tracking) | Append-only run log every surface writes to (voice turns, runner.sh, dashboard spawns, optionally /fleet); dashboard reads unified live activity | D1, D4 |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| A web page that executes agents is a code-exec surface | High | High | Bind `127.0.0.1` only; treat as local-only; write-capable spawns require scoped `--allowed-tools` + a UI confirm; never `--dangerously-skip-permissions`; document it as a control surface |
| Headless write-permission problem resurfaces (spawning Builder/Operator with writes) | Med | High | Default spawns to read-only personas; for writes, reuse the runner pattern (agent read-only, runner writes) or a confined `--add-dir` + explicit allowlist + confirm |
| Refactoring the voice ws host into the control server destabilizes the working voice loop | Med | Med | Keep the voice daemon able to run standalone (own ws) and *publish* to the dashboard only when present; feature-flag the change |
| Scope creep — full control + registry is large | High | Med | Strict phasing; Phase 1 (D1–D3) ships a useful read-only dashboard before any control |
| Dashboard implies omniscience it doesn't have (in-session Task spawns invisible) | Med | Low | Show only truthfully-observable activity; label the registry's coverage; don't fake a live fleet |

## Dependencies
- **New:** `fastapi`, `uvicorn` (voice venv). Frontend stays dependency-free.
- **Present/reused:** voice event emission (B1–B4), `agents/` roster, `runner.sh` + `~/.claude/brain-bg-logs/`, launchd template (A4), the C2 orb.
- **Design:** build the dashboard against the frontend domain (Product register) via `/design`.

## Open Questions
1. **Backend home** — new top-level `dashboard/` (recommended) vs. extending `voice/`? Confirm.
2. **Auth** — local-only `127.0.0.1` bind with no token for v1 (recommended), or a shared-secret
   token even locally?
3. **"Spawn on task" default persona** — Scout (read-only) by default, with write personas
   behind an explicit scoped confirm? (recommended)

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Supersede "not a control panel" | Web surface becomes a **full-control agent dashboard** | User chose full control; explicit reversal of the original Pillar C scope | 2026-07-23 |
| Orb's fate | **Absorbed** as the active-session panel | Preserves the C2 work; the live session is one tile in the dashboard | 2026-07-23 |
| Data source | **Both, phased** — observe now, run registry later | Ship a real read-only dashboard fast; enrich to live unified tracking after | 2026-07-23 |
| Backend | **FastAPI + uvicorn**, new `dashboard/` module | HTTP action API + ws + static in one place; spans more than voice | 2026-07-23 |
| Frontend | **Vanilla JS**, extend `web/` | No build step needed at this scale; current page works | 2026-07-23 |
| Not a chat | High-level status only; no transcript UI | User: "don't make it the chat interface, high level things" | 2026-07-23 |

## Handoff Readiness (for /scaffold)
- Tech stack decided: ✅ FastAPI backend (`dashboard/`) + vanilla-JS `web/`, reusing voice events + brain-bg-logs + agents/ roster.
- Structure clear: ✅ new `dashboard/` backend (hub + APIs + process manager + registry); `web/` becomes panels; voice publishes to the hub.
- Entry points: ✅ `dashboard/` app (serves web/ + ws + API); `web/` panels; voice daemon publish path.
- **Open before scaffold:** Q1–Q3 (all have safe defaults). Phase 1 (D1–D3) is the first shippable slice.

---

## Agent Dashboard — Enhancements & Revisions (v2)
Date: 2026-07-24
Source: /brainstorm (folded into this plan)

### Reframe: the dashboard has TWO axes
1. **Agents & Runs** — who's working, how, and at what cost.
2. **Work Pipeline** — ideas progressing brainstorm → plan → scaffold → build → review →
   reflect.

They unify: **agents are what move pipeline cards forward.** A card in "Build" can show the
Builder actively working it; finishing a run advances the card. The dashboard becomes mission
control for both the fleet *and* the flow of work.

Adopted (all): live activity+cost · approvals inbox · MCP/daemon health · task queue/dispatcher ·
**work-pipeline board** · notifications · quick-action templates · /fleet visualization.
Registry = **SQLite**. Local-API **CSRF/token hardening = mandatory**.

### New / revised panels
- **Work Pipeline (Kanban)** — columns = workflow phases; cards = projects/features; a card's
  column is its detected phase (reuse `/status`'s doc-presence detection); cards link to their
  active run(s). This is "the progression of ideas."
- **Activity & cost** — per-run tool-call feed (*Scout is reading X…*) + a spend panel, both from
  the `stream-json` `tool_use` events and `total_cost_usd`/tokens we already parse.
- **Fleet health** — MCP connection status (github/notion/playwright — surfaces the tokens-not-set
  issue from A2), voice-daemon up?, model + permission-mode.

### Approvals inbox — unlocks safe autonomous writes (pays off the B4 debt)
Run write-capable personas headless with `claude -p --permission-prompt-tool <mcp-tool>`; that tool
forwards each tool-approval request to the dashboard, which shows *"Builder wants to Write X —
approve?"* and returns allow/deny. This resolves the "headless `-p` can't prompt for writes" block
we've deferred since B4, and makes Builder/Operator usable under human-in-the-loop control.
**Verify `--permission-prompt-tool` against claude 2.1.167 (a B4-style probe) before building D8.**

### Revised milestones (phased) — extends D1–D6
**Phase 1 · Observe:** D1 control server · D2 shell + orb panel · D3 fleet/jobs + **health** +
**activity** panels · **D7 work-pipeline board (read-only)**
**Phase 2 · Control:** D4 action API + **CSRF/token + audit log (mandatory)** · D5 controls +
**quick-action templates** + **notifications** · **D8 approvals inbox**
**Phase 3 · Enrich:** D6 **SQLite** run registry + **cost/stats** + **/fleet run visualization** ·
**D9 task queue / dispatcher**

| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| D7 | Work-pipeline board | Kanban of phases; cards = projects/features; phase detected via `/status` doc-logic; cards link to runs | D1 |
| D8 | Approvals inbox | `--permission-prompt-tool` → dashboard approve/deny; unblocks autonomous writes (probe the flag first) | D4 |
| D9 | Task queue / dispatcher | Enqueue tasks, assign to personas, watch them drain | D4, D6 |

### Added risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `--permission-prompt-tool` behaves differently than assumed on 2.1.167 | Med | High | Probe it (B4-style) before D8; fall back to the runner "agent read-only, runner writes" pattern if unsupported |
| Pipeline phase-detection is ambiguous (e.g. plan.md + reflect.md both exist) | Med | Med | Reuse `/status` order + a tiebreak; consider a lightweight per-project `.brain-state` marker |
| Multi-project scope for the pipeline | Med | Low | v1 watches the current repo; add configured project roots later |
| Everything-selected = large scope | High | Med | Strict phasing; Phase 1 (D1–D3, D7) still ships a real dashboard before any control |

### Decisions Log (additions)
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Registry storage | **SQLite** | Enables cost/stats/history aggregation the activity panel needs | 2026-07-24 |
| Enhancements adopted | **All** + extras (notifications, quick-actions, /fleet-viz) | User-selected | 2026-07-24 |
| Second axis | **Work-pipeline board** (phase progression) | User addition; reframes dashboard as agents + work-flow mission control | 2026-07-24 |
| Approvals mechanism | `claude -p --permission-prompt-tool` → dashboard | Unblocks safe autonomous writes; verify vs 2.1.167 first | 2026-07-24 |
| Local API security | **Token + Origin/Host check + action audit log** (mandatory) | localhost is reachable by any web page (CSRF); "no auth, local-only" is unsafe | 2026-07-24 |

### Open Questions (additions)
4. **Pipeline scope** — current repo only for v1 (recommended) vs configured project roots? And the
   phase-detection tiebreak rule.
5. **Approvals probe** — confirm `--permission-prompt-tool` behavior on 2.1.167 before committing D8.

---

## Agent Dashboard — Fleet Recon Findings & Revisions
Date: 2026-07-24
Source: /fleet (Scout ×1, Reviewer ×1) + direct CLI probes. Pre-build de-risking.

### ⚠️ D8 reality: `--permission-prompt-tool` does NOT exist on claude 2.1.167 (probed)
`claude --help` has **0 matches** for `permission-prompt-tool`. Available controls are
`--permission-mode {acceptEdits,auto,bypassPermissions,manual,dontAsk,plan}`,
`--allowed-tools`/`--disallowed-tools`. So the **live per-action approvals inbox cannot be built
as specified.** Pivot:
- **D8 → run-level approval.** The dashboard shows a proposed *run* (persona · task · allowed
  tools · target dir) and you approve/deny **the whole run** before it starts — not per tool
  call. Execution then uses `--permission-mode acceptEdits` + tight `--allowed-tools` + a
  confined `--add-dir`. Read-only work keeps the runner pattern (agent read-only, runner writes).
  Never `--dangerously-skip-permissions`.
- Re-verify if the CLI gains `--permission-prompt-tool` later (it exists in the Agent SDK; not
  this CLI). D8 downgrades from "keystone" to "nice-to-have"; it no longer blocks control.

### D1 integration: dashboard SUBSCRIBES to voice (do not invert)
Keep the working voice ws exactly as-is (voice owns `127.0.0.1:8765`, `daemon.py` unchanged). The
dashboard (FastAPI, `127.0.0.1:8766`) opens a **ws client** to voice, receives events, and
re-broadcasts on its own hub. `web/app.js:10` changes its one URL from `:8765` → `:8766`. All
integration complexity lives in the dashboard; the voice loop is untouched and still runs
standalone. (Supersedes the plan's "voice publishes to the control server" wording.)

### Security moves to D1 (not D4) — mandatory at founding
Static **bearer token + `Origin`/`Host` check** on every route and the ws upgrade, from the first
commit, plus an action audit log. The FastAPI app is reachable by any local browser tab the moment
D1 ships; read-only APIs already disclose paths/logs. ~5 lines of middleware.

### Work-pipeline phase detection — LOCKED (D7)
Detection (reused from `/status`, `.claude/commands/status.md:10-19`):
brainstorm=`docs/brainstorm.md` · plan=`docs/plan.md` · scaffold=structure/manifest present ·
build=meaningful source beyond boilerplate · review=`docs/review.md` ·
iterate=`review.md` has a "Resolved This Session" section · reflect=`docs/reflect.md`.
**Tiebreak:** most-advanced phase wins for card placement; show lower completed phases as badges.
Order: Reflect>Iterate>Review>Build>Scaffold>Plan>Brainstorm. A per-project `.brain-phase` file
overrides. Iterate = sub-state of Review. **Project id:** v1 = current repo; v2 = explicit registry
`~/.claude/brain/projects.json` (`{name, root_path}`), no filesystem crawl.

### Confirmed data shapes (probed)
- **Roster (D3):** agent frontmatter = `name, description, tools, model`; body has a `## Posture`
  paragraph. Render tools as the capability/safety chips.
- **Activity feed (D3/D6):** `assistant.message.content[].tool_use` → `.name` + `.input`
  (e.g. `Read {file_path,limit}`). Truthful "what it's doing right now."
- **Cost (D6):** `result.total_cost_usd` + `usage.{input_tokens,output_tokens}`. Real runs cost
  ~$0.02–0.05 each — the spend panel earns its place.
- **Jobs (D3):** `~/.claude/brain-bg-logs/<label>_<YYYYMMDD_HHMMSS>.{log,md}` (log + report).
- **Schedule (D3):** `launchctl list | grep -i brain` for loaded state.

### D6 registry writers — enumerated (SQLite)
Name each writer as its own sub-task: voice daemon (Python, direct), dashboard-spawned runs
(Python, direct), `runner.sh` (via a `brain-registry-append` Python helper — no inline SQLite in
bash). Missing one ⇒ silent partial data.

### Revised Phase 1 build order
**D1** (FastAPI server + bearer-token/Origin security + voice-subscribe proxy) →
**D3** (read panels: roster · jobs · health · activity) →
**D2** (orb absorbed as active-session panel) →
**D7** (pipeline board). Visual checkpoint (human) at D2 + D7. Backend (D1/D3) is the autonomous-
friendly slice; D2/D7 need eyes.

---

## Agent Dashboard — D7 build note
Date: 2026-07-25

**Deviation from the locked "most-advanced-phase-wins" tiebreak** (surfaced by testing against
reality): most-advanced-wins mis-placed actively-cycling projects — brain has a `reflect.md`
from a prior cycle but is *currently* in plan/build, so it wrongly showed in Reflect.

**Revised rule (shipped in D7):** a card's **column = the most-recently-active phase** (the phase
whose artifact was modified last — doc mtime for brainstorm/plan/review/reflect; newest source
mtime for build; manifest mtime for scaffold). The **"reached" badges** on each card preserve the
most-advanced/progress info. `.brain-phase` file override still supported. Projects come from
`~/.claude/brain/projects.json` if present, else sibling dirs containing `docs/plan.md` or
`docs/brainstorm.md`. Verified: brain→plan, ryans-boomin-beats→build.

**Phase 1 COMPLETE:** D1 (server+security+proxy) · D2 (dashboard shell + orb tile) · D3
(agents/jobs/schedule/health panels) · D7 (pipeline board). Remaining (optional, later): D4/D5
(actions + controls), D8 (run-level approval), D6 (SQLite registry), D9 (queue).

---

## Agent Dashboard — Phase 2 Fleet Recon (D4/D6/D8)
Date: 2026-07-26
Source: /fleet (Scout design · Reviewer threat-model · direct CLI probe)

### 🔴 Key probed finding — tool-narrowing is unreliable
- `claude -p --permission-mode acceptEdits --add-dir <dir>` **writes within scope headless, no
  prompt, no denials** → D8 scoped-run + run-level approval is VIABLE.
- `--agent builder --allowed-tools Write` **did NOT confine** the builder — it still ran Bash.
  So **do not rely on `--allowed-tools` to sandbox a persona whose frontmatter has more tools.**
  Confinement model: (a) read-only runs → a read-only persona (scout/operator, frontmatter-
  enforced, verified); (b) write runs → `--add-dir` + `acceptEdits` + **human approval (D8)** +
  audit, NOT tool-narrowing. TODO before shipping write-runs: test `--add-dir` path-escape.

### D6 registry (SQLite, `~/.claude/brain-dashboard/runs.db`, WAL)
- `runs`(id, persona, task, source[voice|background|dashboard], status[running|done|error],
  started_at, ended_at, cost_usd, input_tok, output_tok, report_path, pid) + `events`(run_id, ts,
  kind, data) for the activity feed.
- Writers: dashboard PM (Python direct) · `runner.sh` (via stdlib `registry_append.py`, no-op if
  db absent) · voice daemon (via a client; needs cost extraction — the bridge currently discards
  `result.total_cost_usd`/`usage`, add a `cost` event in `voice/bridge/claude.py`).

### D4 process manager (`dashboard/process_manager.py`)
- `asyncio.create_subprocess_exec` (NOT the sync `ClaudeBridge`); track by run_id→proc; `_drain`
  streams stream-json → hub (live) + registry events; stop via SIGTERM to the process group.

### Security contract (D4/D8 action endpoints — Reviewer) — all under `/api/`, token-guarded
- persona MUST be in a known-agent allowlist (loaded from `agents/personas/`)
- `task` passed as an argv positional, **never** `shell=True`
- `--add-dir` resolved and asserted under a fixed base (`~/Desktop/Code`), reject escapes → 400
- `MAX_CONCURRENT` cap → 429; per-run timeout; `start_new_session` for kill-group
- run IDs = `secrets.token_urlsafe(16)`; D8 approve/deny hold the run `pending`, spawn only on approve
- append-only `audit.jsonl` on spawn/stop/approve/deny; never log full argv/secrets; minimal `env`
- (verified) the existing `guard` middleware already covers action POSTs since they're under `/api/`

### Build order (sequential): D6 → D4 → D8 → D5 (visual checkpoint) → D9

---

# Plan — Graphify Integration (Knowledge-Graph Context for the LLM)

Date: 2026-07-26
Status: Draft
Brainstorm: `docs/brainstorm.md` → "Graphify Integration" section (2026-07-26)

## Overview

Adopt `safishamsi/graphify` to give the LLM a persistent, **queryable** knowledge graph of
your repositories, so Claude stops re-deriving structure every session. The core finding from
brainstorm holds: **this is adopt, not build** — graphify already ships the LLM-facing surface
(an MCP server exposing `query_graph`/`get_neighbors`/`shortest_path`, a Claude Code skill, and
pre-tool-use hooks that push the assistant to query the graph before reading files).

Because the value is unproven until watched running, this plan is **gated and phased**:

- **Phase 0 — Pilot (the gate).** Install, graph one code repo (free/local), live with the
  MCP-query workflow. Decide whether it earns further investment. *No brain code written here.*
- **Phase 1 — Brain wiring (contingent on Phase 0).** A thin `/graph` command, `install.sh`
  registration, a `graphify-out/` convention + gitignore policy, and a freshness policy for
  code repos.
- **Phase 2 — Vault track (contingent + deferred).** On-demand graphing of the plain-markdown
  vault, with cost guardrails. `--obsidian` noted as a future output target only.

The cost/privacy split is the design spine: **code = free + 100% local** (bundled tree-sitter);
**vault = LLM-cost** (prose extraction hits the API and sends semantic descriptions out).

## Goals & Success Criteria

- **G1 — LLM context injection.** Claude can pull the relevant graph neighborhood on demand
  rather than re-exploring. Success = in real sessions, Claude *actually* queries the graph via
  MCP before blind file reads (observed, not assumed).
- **G2 — Prove value before wiring.** A recorded go/no-go after living with the pilot.
- **G3 — Respect the cost/privacy split.** Code graphed freely; vault graphed only deliberately.
- **G4 — Brain-native only if earned.** If wired, it follows brain conventions (command +
  `install.sh` sync, degrade-gracefully).

Success criteria (checkboxes ticked as met):
- [ ] **SC1** — graphify installed; `/graphify .` produces `graphify-out/graph.json` on the pilot repo.
- [ ] **SC2** — MCP server reachable; `query_graph`/`get_neighbors` return real results on the pilot graph.
- [ ] **SC3** — Over a pilot window (~1 week / several real sessions), a recorded observation of
  whether Claude uses graph queries and whether answers improved; plus whether the global
  pre-tool-use hook is helpful or noisy.
- [ ] **SC4** — Explicit go/no-go decision logged (proceed to Phase 1, or stop at plain-adopt).
- [ ] **SC5 (Phase 1, if go)** — `/graph` wrapper + `install.sh` registration + `graphify-out/`
  gitignore convention + code-repo freshness policy live and verified.
- [ ] **SC6 (Phase 2, if pursued)** — vault graphed on-demand with cost surfaced; no automatic
  vault re-graphing.

## Scope

### In Scope
- Installing graphify (`uv tool install graphifyy`; `graphify install`).
- Piloting on **one** code repo; evaluating the MCP-query workflow and the global hook.
- **Contingent:** thin brain wrapper (`/graph`), `install.sh` registration, `graphify-out/`
  git policy, code-repo freshness automation.
- **Contingent/deferred:** vault track with cost guardrails.

### Out of Scope
- Building any graph tooling from scratch (graphify provides it).
- Converting the vault to Obsidian (future; `--obsidian` is only noted).
- Neo4j / graphml / wiki exports; cross-repo merged graphs; `get_pr_impact`/PR flows.
- Cursor wiring (unless trivially free) — Claude Code first.

## Tech Stack & Architecture

- **graphify** (Python 3.10+, installed via `uv`/`pipx`) — the engine. Tree-sitter bundled;
  no external binaries for code extraction.
- **graphify MCP stdio server** — the LLM-facing query layer (the actual "context injection"
  mechanism; query-on-demand, *not* a static blob pasted into `CLAUDE.md`).
- **Brain plumbing (Phase 1 only)** — a `/graph` command in brain's command set + an
  `install.sh` addition, mirroring the frontend-domain "wire external tool, degrade gracefully,
  sync via install.sh" recipe. Freshness via brain's existing hook pattern (git-driven, **not**
  per-edit for the vault).

**Architecture note / significant decision (needs confirmation):** graphify is *cross-cutting*
— it applies to any repo regardless of type — so it fits brain's **universal (L1)** layer as a
command + install step, **not** an L2 `domains/` entry (domains are contextual by project type).
This differs from the frontend work, which was correctly a domain. Recommendation: universal
command + `install.sh`. Flagged in Open Questions for your call.

## Milestones

| # | Milestone | Description | Dependencies | Gate |
|---|-----------|-------------|--------------|------|
| M0 | Install & first graph | `uv tool install graphifyy`; `graphify install`; `/graphify .` on the pilot repo; confirm `graph.json` + MCP reachable | none | — |
| M1 | Live pilot & evaluate | Use across several real sessions; observe graph usage, answer quality, hook noise, cost | M0 | **GO/NO-GO** |
| M2 | Brain wiring | `/graph` wrapper, `install.sh` registration, `graphify-out/` gitignore convention, code-repo freshness policy | M1 = GO | — |
| M3 | Vault track (deferred) | On-demand vault graphing with cost guardrails; `--obsidian` deferred | M2 + explicit opt-in | — |

## Task Breakdown (light — Phase 0 only; deeper on request)

**M0 — Install & first graph**
- Install graphify; run `graphify install`; confirm the skill landed and MCP config registered.
- Pick the pilot repo (see Open Questions); run `/graphify .`; confirm `graphify-out/graph.json`
  and `GRAPH_REPORT.md` generated.
- Add `graphify-out/` to that repo's `.gitignore` for the pilot (simplest; revisit committing
  `graph.json` later).
- Sanity-check MCP: `query_graph`/`get_neighbors` on a known symbol.

**M1 — Live pilot & evaluate**
- Use the repo normally in Claude Code for the pilot window.
- Keep a short note (in this doc's Decisions Log or a scratch file): did Claude query the graph?
  did answers improve? was the global hook helpful or noisy across *other* repos? any cost surprises?
- Record the **GO/NO-GO** in the Decisions Log → drives whether M2 happens.

*(M2/M3 task breakdown intentionally deferred until the pilot returns GO — planning them now
would be planning around an unproven tool.)*

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Global pre-tool-use hook is noisy across all sessions | Med | Med | Pilot explicitly evaluates this (SC3); scope or disable the hook if it annoys |
| Vault graphing runs up API cost | Med | Med | Vault deferred to Phase 2, on-demand only, never auto; `cost.json` watched |
| `graph.json` goes stale / misleads | Med | Med | Incremental `--update`; freshness policy in M2; graph is queried not trusted blindly (confidence tags) |
| Committing `graphify-out/` bloats repos / leaks `cost.json` | Low | Low | Gitignore the dir in the pilot; decide `graph.json`-only commit later |
| Tool immaturity / breaking changes (new tool) | Med | Low | Pilot-first limits blast radius; plain-adopt fallback needs zero brain code |
| Planning wiring around unverified behavior | Med | Med | Gated phases — M2 blocked on M1 = GO (the recurring "stress-test against reality" discipline) |

## Dependencies

- `uv` (or `pipx`) + Python 3.10+ on the machine.
- A pilot code repo (named at M0).
- For any headless `graphify extract` later: an API key (`ANTHROPIC_API_KEY` etc.). In-session
  `/graphify .` needs none — uses the existing model session.

## Open Questions

Recommendations given; **bold = wants your confirmation before it hardens**:
1. **Pilot-first vs. wire now?** → Rec: **pilot-first** (this plan assumes it).
2. **Defer vault to Phase 2?** → Rec: **yes** (paid track; prove value on free code first).
3. **Which pilot repo?** → *Needs your pick.* Suggest a mid-size, actively-worked code repo
   (not brain itself, not the vault) so the graph is meaningful but the blast radius is small.
4. **Integration home (L1 universal command vs L2 domain)?** → Rec: **universal command +
   `install.sh`** (graphify is cross-cutting, not project-type-specific). *Confirm.*
5. **Freshness mechanism?** → Rec: manual `--update` during pilot; **git `post-commit` on code
   repos** in M2; never per-edit on the vault.
6. **`graphify-out/` git policy?** → Rec: **gitignore the whole dir** for the pilot; revisit
   committing `graph.json` for portability in M2. `cost.json`/`cache/` always ignored.
7. **Keep the global hook on during the pilot?** → Rec: **yes** — testing the nudge is the whole
   point of the pilot; scope it only if noisy.

## Decisions Log

| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Build vs. adopt | Adopt graphify | It already ships the MCP/skill/hook surface; building would duplicate it | 2026-07-26 |
| Structure | Gated phases (pilot → wire → vault) | Don't plan wiring around an unproven tool; matches brain's stress-test-against-reality pattern | 2026-07-26 |
| Context mechanism | MCP query-on-demand | Better fit for "tool for the LLM" than a static graph blob in CLAUDE.md; graph.json too big to inject | 2026-07-26 |
| Vault timing | Deferred to Phase 2 | It's the paid/privacy-exposed track; validate free code repos first | 2026-07-26 |
| Integration layer | **Provisional:** universal command + install.sh (pending Q4) | Graphify is cross-cutting, not a project-type domain | 2026-07-26 |

## Handoff Notes (for /scaffold)

- **Phase 0 needs no `/scaffold`** — it's install + run commands, no files authored in brain.
  `/scaffold` becomes relevant only at **M2 (Phase 1)**, and only if the pilot returns GO.
- Tech stack: decided (graphify; no new stack). Entry point (if wired): a `/graph` command
  wrapper. Top-level structure: provisionally universal command + `install.sh` (Open Question 4).
- **Next action is not scaffold — it's the pilot (M0).** Pick the pilot repo (Q3) and run the
  install.

---

## Agent Dashboard — Before Real Use (flagged 2026-07-26)
The dashboard is complete and hardened (127.0.0.1-only, token, persona allowlist, task-as-argv,
`--add-dir` confinement [probe-verified], run-level approval, audit.jsonl, kill-group). But it
**executes agents from a web UI**, so before relying on the write/action endpoints for real work:
1. **Dedicated `/review` security pass** on the action endpoints (spawn/propose/approve/stop/queue).
2. **Narrow the dashboard-spawn default cwd** — currently `~/Desktop/Code`, which let a Scout run
   Glob widely ($0.16/run). Scope spawns to a chosen project dir.
3. Consider a **per-run timeout** and confirm the concurrency cap suits real workloads.
Until then it's verified for local experimentation. (User undecided on real use as of 2026-07-26.)

---

# Plan — Project & Task Tracker (fleet-driven)
Date: 2026-07-26
Status: Draft
Brainstorm: docs/brainstorm.md ("Project & Task Tracker (fleet-driven)", 2026-07-26)

## Overview
Evolve the dashboard from *observing* project state to *owning* it: a personal, self-hosted,
GitLab-style tracker where **a task is a persistent, stateful fleet run**. Projects → tasks/issues
with real status, an append-only update history, and a fleet that pulls and delivers the work.
Builds directly on the completed dashboard (D1–D9): the run registry, process manager (D4), run
approval (D8), and task queue (D9). It closes brain's own loop — `/plan` produces milestones →
those seed tasks → the fleet works them → results flow back as updates → the pipeline board
reflects progress.

## Goals & Success Criteria
- **G1 — Track work statefully.** Projects, tasks/issues with status, assignee, and an append-only
  update log, all in the dashboard.
- **G2 — Fleet delivers tasks.** "Work this task" spawns a scoped, approved fleet run linked to the
  task; on finish the task auto-updates and moves to `review` (never auto-closed).
- **G3 — Modular change tracking.** Every status change, comment, and run-link is an event in the
  task's history (the activity feed).
- **G4 — Composes with what exists.** Tasks nest under the pipeline board (project phase = top
  lens, tasks = drill-down); reuses registry/PM/approval/queue.
- **Success =** create a task, assign it to a persona, click "work," watch the run execute
  (writes gated by approval + scoped dir), and see the task move to `review` with the run linked
  and a summary in its update log.

## Scope
### In Scope (v1 = T1–T5)
- SQLite tables (extend the dashboard DB): `projects`, `tasks`, `task_updates`; task↔run links.
- Task/project CRUD API (token-guarded) + a Kanban/issue board + task detail with update log in `web/`.
- "Work a task" → a scoped D4/D8 run linked to the task; result → update + `review`.
### Out of Scope (v1)
- Backlog auto-pull (v2, T6), planner persona (v3, T8), GitHub issue/PR sync (T7, opt-in later).
- Labels, milestones, subtasks, comment threads, custom fields (add after the lean core).
- Multi-user, auth beyond the existing local token, external hosting.

## Tech Stack & Architecture

### Decisions (carried from brainstorm)
| Question | Choice | Why |
|----------|--------|-----|
| Backing store | **Local SQLite, same DB as the run registry** (`~/.claude/brain-dashboard/runs.db`, new tables) | Task↔run links are the core value → one DB = trivial joins; fast cross-project queries; private/offline. GitHub sync deferred to opt-in. |
| Change history | **Append-only `task_updates` log** | Modular change tracking + activity feed without needing git versioning. |
| Fleet autonomy | **Phased: assign (v1) → backlog-pull (v2) → planner (v3)** | Ships a controllable core; "team" feel arrives at v2 on a solid base. |
| Model | **Lean single `Task` entity (type: task\|issue\|bug)** | Covers projects/tasks/issues/state without labels/milestones/threads. |
| Backend | **Extend `dashboard/` (FastAPI)** — new `dashboard/tracker.py` + endpoints | Reuse token/guard/hub/registry/PM; one server. |
| Frontend | **Extend `web/` vanilla JS** — new board view + task detail | Consistent with the dashboard; no build step. |

### Data model (lean core)
```
projects      (id, name, root_path)                      -- seeded from the pipeline detector / projects.json
tasks         (id, project_id, type[task|issue|bug], title, brief, acceptance,
               status[backlog|ready|doing|review|done], assignee, scoped_dir,
               created_at, updated_at)
task_updates  (id, task_id, ts, kind[created|status|comment|run_linked|result], data)
runs          (+ nullable task_id)                        -- links a fleet run to the task it worked
```
A task's runs = `SELECT * FROM runs WHERE task_id = ?`. Status machine: agents may move a task to
`review`, **never** to `done` (a human or the Reviewer persona closes it).

### Fleet linkage
"Work a task" = a normal process-manager run tagged with `task_id`, persona = assignee, `--add-dir`
= the task's `scoped_dir` (validated under `~/Desktop/Code`), prompt = the task brief + acceptance.
On run finish, a tracker hook appends a `result` update and sets status → `review`. Writers still
pass through D8 approval; read-only assignees auto-run. v2 pull respects that gate.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| T1 | Schema + tracker module | `projects`/`tasks`/`task_updates` tables + nullable `runs.task_id`; `tracker.py` CRUD; seed projects from the pipeline detector | dashboard D6 |
| T2 | Task API | Token-guarded REST: projects list; tasks CRUD; task detail; `/api/tasks/{id}/updates` (add comment / status) | T1 |
| T3 | Board UI | Kanban by status (per-project filter) in `web/`, task create/edit, task detail + update log; reuse pipeline-board CSS | T1, T2 |
| T4 | Work-a-task (assign→run) | `POST /api/tasks/{id}/work` → scoped D4/D8 run (assignee persona, task dir, brief prompt); link run↔task; status→`doing` | T2, D4/D8 |
| T5 | Result → review | On run finish, append a `result` update + move status→`review` (never auto-close); optional Reviewer auto-check | T4 |
| T6 | Backlog pull (v2) | `ready` tasks auto-flow into the D9 queue as capacity frees; writers still gated by approval | T4, D9 |
| T7 | Seed + git links (opt-in) | Parse `/plan` milestone tables → tasks; per-repo GitHub issue/PR sync via the MCP | T2 |
| T8 | Planner persona (v3, deferred) | Decompose a deliverable into tasks and dispatch workers | T6 |

**Phasing:** v1 = **T1–T5** (the shippable slice: tracker + board + assign + run-linking). v2 = T6. Later = T7/T8.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Task→prompt quality drives deliverable quality | High | High | Explicit `brief` + `acceptance` fields; template the run prompt; don't spawn off a bare title |
| Agents auto-closing unverified work | Med | High | Status machine forbids agent→`done`; agents only reach `review`; human/Reviewer closes |
| State-ownership conflicts (you + agent mutate a task) | Med | Med | Append-only log is the truth; single-user → last-write-wins on status is acceptable |
| Per-task write confinement | Med | High | `scoped_dir` must resolve under `~/Desktop/Code`; reuse D8 `--add-dir` + approval; reject escapes |
| Scope creep into a full Linear/GitLab | High | Med | Hard phasing; v1 is T1–T5 only; richness (labels/milestones) explicitly deferred |
| Schema migration on the live registry DB | Low | Med | Additive only (new tables + nullable column); `CREATE TABLE IF NOT EXISTS` |

## Dependencies
- **Reuses:** `dashboard/registry.py` (SQLite), `process_manager.py` (D4/D8 spawn+approval), D9 queue,
  the pipeline detector (`data.read_pipeline`), the token/guard/hub in `server.py`, `web/` board CSS.
- **New:** `dashboard/tracker.py`, tracker endpoints in `server.py`, a board view in `web/`.
- **Opt-in later:** GitHub MCP (already available) for T7 issue/PR sync.

## Open Questions
1. **Status lifecycle** — exact transitions and which are agent- vs user-driven (esp. does T5 auto-move to `review`, and does the Reviewer persona auto-review or just you?).
2. **Per-task scoped dir** — default to the project root, or a per-task subdir / branch?
3. **Seeding format (T7)** — how milestone tables in `docs/plan.md` map to tasks (parse the `| # | Milestone |` table, or a marker?).
4. **Projects source** — a `projects` table seeded once, or computed live from the pipeline detector each read?

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Backing store | SQLite, same DB as the run registry | Task↔run joins; fast; private; GitHub deferred | 2026-07-26 |
| Change history | Append-only `task_updates` | Modular change tracking without git versioning | 2026-07-26 |
| Fleet autonomy | Phased: assign → pull → planner | Controllable core first; team-feel at v2 | 2026-07-26 |
| Model | Lean single `Task` (type field) | Covers tasks/issues/bugs without heavy richness | 2026-07-26 |
| Home | Extend `dashboard/` + `web/` | Reuse registry/PM/approval/queue/token/hub | 2026-07-26 |
| Completion | Agents reach `review`, never `done` | A human/Reviewer verifies deliverables | 2026-07-26 |

## Handoff Readiness (for /scaffold)
- Tech decided: ✅ SQLite tables in the dashboard DB + `dashboard/tracker.py` + FastAPI endpoints + vanilla-JS board.
- Structure clear: ✅ new `tracker.py`, tracker routes in `server.py`, board view in `web/`; links via `runs.task_id`.
- Entry points: ✅ `/api/tasks*` + `/api/projects` + `/api/tasks/{id}/work`; the board view; `tracker.py` CRUD.
- **v1 slice = T1–T5.** Open Questions 1–2 (status lifecycle, scoped dir) are the ones to pin before T4/T5; T1–T3 can start now.

---

## Task Tracker — Revision: cross-device state (2026-07-26)
**Requirement added:** state must travel when the code is pulled on another device.

**Conflict surfaced:** the prior decision (SQLite at `~/.claude/brain-dashboard/runs.db`) lives in
the *home dir*, not the repo → it does NOT travel. **Backing-store decision revised.**

### Revised backing store: git-versioned files, per repo
- **Source of truth = `.brain/tasks/<id>.md` in each project repo** — YAML frontmatter (type, title,
  status, assignee, scoped_dir, brief, acceptance, linked run ids) + an append-only `## Updates`
  section. Committed with the code → travels with `git pull`. One file per task (small, mergeable).
- The dashboard **reads/writes these files directly** (as the pipeline detector already reads
  `docs/`). Cross-project view = scan each known repo's `.brain/tasks/` (bounded).
- **Run registry stays** (device-local run telemetry). A task file records run ids + the durable
  *result* of a run, so the outcome travels even though the ephemeral telemetry doesn't.
- **Change history = the in-file update log + `git diff`/`git log`** — strengthens the "modular
  change tracking" goal.
- More brain-native (mirrors `docs/` + append-only `updates/queue.md`).

### Trade-offs accepted
- No SQL joins / weaker cross-project queries (repo scan instead) — fine for the lean v1.
- Concurrency handled by git; file-per-task keeps merges small.
- State changes must be committed to travel — dashboard writes files, user commits (auto-commit
  deferred).

### Alternative (if "central, not per-repo" is wanted): GitHub Projects/Issues via MCP, or a hosted
DB. Cross-device too, but service-coupled + repo-per-project. Not chosen — user phrasing implies
per-repo, git-carried state.

### Milestone impact
- **T1 changes:** not SQLite tables — instead a **task file format** (`.brain/tasks/*.md`) + a
  `tracker.py` that reads/writes them per repo; `runs.task_id` link → task file references run ids.
- T2/T3/T4/T5 operate on files instead of DB rows (API + board + work-a-task + result→review
  unchanged in shape). T7 GitHub sync becomes a natural extension of the same model.

### Decisions Log (revision)
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Backing store (revised) | **git-versioned `.brain/tasks/*.md` per repo** | Must travel with `git pull`; SQLite-in-home doesn't. More brain-native; git = change history | 2026-07-26 |
| Run registry role | Stays device-local; task file records run ids + durable result | Telemetry is per-device; outcomes must travel | 2026-07-26 |
| Commit model | Dashboard writes files; user commits (auto-commit deferred) | Keep git flow explicit; avoid noisy auto-commits | 2026-07-26 |

### New open question
- **Sync ergonomics:** manual `git commit/push` of task changes for v1, or a dashboard "sync"
  button that commits+pushes the `.brain/tasks/` changes? (Leaning manual for v1.)

---

## T1 — Deep Dive: task file format + `tracker.py`
Date: 2026-07-26 · Depth: deep (the contract the whole tracker builds on)

### File layout (per repo)
```
<project-repo>/.brain/tasks/<id>-<slug>.md     # one file per task; committed (travels with git)
```
- `.brain/tasks/` is **committed** (the point of cross-device). Created lazily on first task.
- One file per task ⇒ creates never conflict; edits to different tasks never conflict.

### Task file format
Scalar-only YAML frontmatter (stdlib-parseable — **no YAML dep**) + markdown body sections.
List-ish data (acceptance, runs, updates) lives in **body sections**, keeping frontmatter trivial
and the whole file human-readable / git-diffable.
```markdown
---
id: 9f3a2b
title: Fix login redirect loop
type: task            # task | issue | bug
status: doing         # backlog | ready | doing | review | done
assignee: builder     # persona name, or empty
scoped_dir: .         # relative to repo root; write-runs confined here (must stay in-repo)
created: 2026-07-26T14:03:00Z
updated: 2026-07-26T14:35:00Z
---

## Brief
Fix the redirect loop after login. Context: the guard re-fires on the callback route…

## Acceptance
- [ ] no loop on login
- [ ] session persists across refresh

## Runs
- r_abc123

## Updates
- 2026-07-26T14:03Z · created
- 2026-07-26T14:20Z · status: backlog → doing
- 2026-07-26T14:35Z · result (r_abc123): patched the redirect guard; tests pass
```
- **Brief + Acceptance are first-class** (mitigates the "task→prompt quality" risk — the run prompt
  = Brief + Acceptance, never a bare title).
- **Updates = append-only log**; each line `<iso-utc> · <kind>: <detail>`. Change history = this log
  **+ `git log`/`git diff`**.
- **Runs** = local-registry run ids that worked this task; the durable *result* is written into
  Updates (so the outcome travels even though run telemetry stays device-local).

### IDs & filenames
- `id = secrets.token_hex(3)` (6 hex chars) — **collision-free across devices without a server**.
- Filename `<id>-<slug>.md`; slug = kebab of title, truncated. Reference a task as `#<id>`.
- **Decision to confirm:** random ids over GitLab-style sequential `#12` — sequential numbers
  collide when two devices create tasks offline (no central assigner). Random trades readability
  of a running number for merge-safety. (The slug keeps filenames human-readable.)

### `dashboard/tracker.py` — read/write API (stdlib only)
Pure functions over the filesystem (testable without a server); reuses `data._project_roots()`
for project discovery.
```python
TASKS_SUBDIR = ".brain/tasks"
STATUSES = ["backlog", "ready", "doing", "review", "done"]

def all_tasks() -> list[dict]                 # cross-project: scan every project root, tag w/ project
def list_tasks(root: Path) -> list[dict]      # one repo
def read_task(root, task_id) -> dict | None
def create_task(root, title, type="task", brief="", acceptance=None,
                assignee="", scoped_dir=".") -> dict
def update_task(root, task_id, **fields) -> dict          # set frontmatter fields; bumps `updated`
def set_status(root, task_id, new_status, actor, note="") -> dict   # validated transition + log
def add_update(root, task_id, kind, detail) -> None       # append a line to ## Updates
def link_run(root, task_id, run_id, result=None) -> None  # add to ## Runs + append a result update
```
- **Parsing:** frontmatter (scalars, stdlib) + body split on `## <Section>` headers. A task is a
  canonical dict; writing **re-serializes deterministically** (fixed field/section order, updates
  preserved+appended) ⇒ localized, clean git diffs.
- **Serialization is idempotent:** read→write with no change produces a byte-identical file (a T1
  test asserts this — guarantees stable diffs).

### Status machine (validated in `set_status`)
```
backlog ⇄ ready → doing → review → done
                    ▲        │
                    └── rework ┘        (review → doing)
any → backlog (park)
```
- **Agents may only reach `review`** — `set_status(actor="agent", new_status="done")` is rejected.
  A human or the Reviewer persona closes (`actor="user"`). This is enforced here, the single choke
  point.

### Cross-project aggregation
`all_tasks()` iterates `data._project_roots()` (already used by the pipeline board), reads each
repo's `.brain/tasks/`, and tags each task with `{project, root}`. Bounded (few repos × few tasks).
A project with no `.brain/tasks/` simply contributes none.

### Acceptance criteria (T1 done when…)
- [ ] Format documented; `create_task` writes a valid `.brain/tasks/<id>-<slug>.md`.
- [ ] Round-trip: create → read_task returns the same dict; **re-serialize is byte-idempotent**.
- [ ] `set_status` enforces the transition graph **and** rejects agent→`done`.
- [ ] `add_update`/`link_run` append to the log; `updated` bumps.
- [ ] `all_tasks()` aggregates across ≥2 repos; missing tracker dir = empty, no error.
- [ ] Verified by unit tests over a temp repo dir — **no server, no git, no network**.

### Files this milestone creates
- `dashboard/tracker.py` (the module above).
- (docs) a short `.brain/README.md` template explaining the format, dropped into a repo on first use.
- No endpoints/UI yet (those are T2/T3).

### Open items rolled to T2+ (not needed for T1)
- Endpoints (`/api/tasks`, `/api/projects`, `/api/tasks/{id}/work`) → T2/T4.
- Board rendering → T3. Sync/commit ergonomics → cross-device revision note.

### T1 decision confirmed (2026-07-26)
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Task IDs | **Random short id** (`secrets.token_hex(3)`, ref `#9f3a2b`) | Collision-free across offline devices (no central assigner); slug keeps filenames readable | 2026-07-26 |

### Tracker decisions confirmed (2026-07-26, post-v1 reflect)
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Auto-review scope | **Write runs only** (read-only → straight to review) | Reviewing a read-only research run has nothing to diff; cheaper | 2026-07-26 |
| Dev server | **`--reload` mode added** to `dashboard.server` | Kills the recurring manual kill+nohup restart friction | 2026-07-26 |

---

# Plan — Workflow ↔ Tracker Integration
Date: 2026-07-26
Status: Draft
Brainstorm: inline (folds the "integrate task CRUD into workflow steps" decision)

## Overview
Wire the brain workflow commands to create and maintain tracker tasks automatically, so the
tracker stays in sync with the work without a manual step. **Docs remain the design record; the
tracker mirrors the actionable, stateful items** seeded from them. Each phase acts **auto + report**
(does it, then tells you). Supersedes the narrow T7 ("seed from /plan") with a broader integration.

## Goals & Success Criteria
- **G1 — Planned work is tracked.** Running `/plan` creates a task per milestone in the tracker.
- **G2 — Building maintains state.** `/build` moves the task it's building doing→review/done and
  links the fleet run.
- **G3 — Reviews and reflects feed the tracker.** `/review` files issues; `/reflect` closes done
  tasks and files "next steps" as backlog.
- **G4 — Idempotent.** Re-running a phase updates existing tasks (by `source` key), never dupes.
- **Success =** run `/plan` on a project → its milestones appear as tracked tasks; `/build` a
  milestone → the task advances + links the run; all without manual tracker edits.

## Scope
### In Scope
- A `source` field on tasks + an idempotent **upsert-by-source** in `tracker.py`.
- A thin **tracker CLI** (`dashboard/tracker_cli.py`) over `tracker.py` — works without the server.
- A "task sync" section added to the `plan`, `build`, `review`, `reflect` command prompts.
- `install.sh` re-sync so the updated commands propagate globally.
### Out of Scope (v1)
- Retroactively seeding the *existing* (mostly-done) plan.md milestones — this wires **going
  forward**; the current open-item backlog is a separate one-time seed.
- `/brainstorm`, `/scaffold`, `/iterate` hooks (add after the core four prove out).
- Markdown-table parsing (the sync is prompt-driven off in-context content, not a parser).
- Sub-tasks, labels, milestones-as-first-class (tracker richness deferred).

## Tech Stack & Architecture

### Mechanism (prompt-driven, CLI-backed)
The workflow commands are AI-run markdown prompts. Each already holds its output in context, so its
prompt instructs the AI to call the tracker CLI to upsert tasks from that content — no parsing.
```
/plan   → for each milestone: tracker_cli upsert --project <p> --source plan:<p>:<id> \
                                   --title <m> --type task --status backlog
/build  → tracker_cli status  --project <p> --id <task> doing|review; tracker_cli link ...
/review → for each finding:   tracker_cli create --project <p> --type bug --title <finding>
/reflect→ tracker_cli status ... done  (closed items);  create backlog tasks for "next steps"
```
- **`source` key** (`plan:<project>:<milestone-id>`) makes upsert idempotent across re-runs.
- **CLI over the API** so it works with the dashboard server down (writes files via `tracker.py`).
- **Auto + report:** the phase performs the sync and prints a task summary; docs are still written.

### Files
- `dashboard/tracker.py` — add `source` to frontmatter + `upsert_task(root, source, **fields)` /
  `find_by_source`.
- `dashboard/tracker_cli.py` — argparse: `create · upsert · status · comment · link · list`;
  resolves project→root via `data._project_roots()` (or `--root`).
- `.claude/commands/{plan,build,review,reflect}.md` — a "## Task sync (tracker)" section each.
- `install.sh` re-run to sync the command changes.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| W1 | Tracker `source` + CLI | Add `source` field + `upsert_by_source` to `tracker.py`; build `tracker_cli.py` (create/upsert/status/comment/link/list); tests | tracker T1 |
| W2 | `/plan` hook | Add task-sync to `plan.md`: upsert a task per milestone (`source=plan:<proj>:<id>`, status backlog); report | W1 |
| W3 | `/build` hook | Add to `build.md`: on building a task → status doing→review/done + link the run | W1 |
| W4 | `/review` hook | Add to `review.md`: findings → issue/bug tasks | W1 |
| W5 | `/reflect` hook | Add to `reflect.md`: close done tasks + file "next steps" as backlog | W1 |

**v1 = W1–W3** (the core loop: plan seeds, build maintains). W4/W5 follow.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Re-running a phase duplicates tasks | High | Med | `source`-key upsert (idempotent create-or-update) |
| Prompt-driven sync isn't guaranteed (AI may skip it) | Med | Med | Make the CLI dead-simple + the instruction explicit + "report" surfaces when it ran; user sees the summary |
| Editing command files changes global behavior | Med | Med | Standard brain flow (edit `.claude/commands/*` + re-run install.sh); test in a fresh session |
| /build vs manual status conflict | Low | Low | Read current status before changing; append-only log preserves history |
| Which project a phase targets | Med | Low | Default to the cwd repo; `--project` overrides |

## Open Questions
1. **Milestone granularity** — one task per milestone row (recommended v1); sub-tasks later?
2. **/build task selection** — does `/build` pull the next `ready` task from the tracker, or just
   update the milestone it's told to build? (Lean: update what's being built; pull later with T6.)
3. **Existing backlog** — one-time seed of the current open items (separate from this going-forward
   wiring) — do it alongside W1?

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Sync mechanism | Prompt-driven + tracker CLI | Commands hold output in context; avoids fragile markdown parsing | 2026-07-26 |
| Idempotency | `source` key + upsert | Re-running phases updates, never dupes | 2026-07-26 |
| Source of truth | Docs = design record; tracker mirrors | User-selected | 2026-07-26 |
| Autonomy | Auto + report | User-selected | 2026-07-26 |
| Phases wired | plan · build · review · reflect | User-selected (brainstorm/scaffold/iterate later) | 2026-07-26 |

## Handoff Readiness (for /scaffold or /build)
- Tech decided: ✅ `source`+upsert in tracker.py, `tracker_cli.py`, command-prompt hooks, install sync.
- Structure clear: ✅ CLI + per-command "task sync" sections.
- Entry points: ✅ `dashboard/tracker_cli.py`; the four command files.
- **v1 slice = W1–W3.** Open Qs are minor (safe defaults). W1 (source+CLI) is the keystone.

---

# Plan — Agent Harness (multi-agent teams on Claude Code)
Date: 2026-10-31
Status: Draft
Brainstorm: inline (grounding Q&A 2026-10-31; builds on the Fleet + Dashboard + Tracker plans above)

## Overview
Turn brain's one-shot fleet runs into a **standing team of named, long-lived agents** that
message each other, work your projects, and are watched and steered from the Hub. Two kinds of
agent: **workflow agents** (one per phase — brainstorm, plan, build, review, reflect) and
**project experts** (one per app, primed on that project's docs, tasks and memory). They support
all four patterns: plan→build→review pipelines, debate/second opinion, a standing team per
project that pulls tracker tasks, and read-only research swarms with a lead.

What exists and is reused: persona files + install sync (`agents/`), `process_manager.py`
(spawn, confinement, approvals, audit, kill-group), `registry.py` (runs + cost, SQLite WAL), the
tracker (tasks as the unit of work), the services runner, and the Hub's Command view (today a
mostly-static Orchestrator panel). The new work is a **session runtime**, a **message bus**, a
**permission gate**, and the **Hub team view**.

## Goals & Success Criteria
- **G1 — Long-lived agents.** Create a named agent (role, project, scope, model, budget); it keeps
  its context across many turns and survives a dashboard restart (resume by session id).
  ✅ when a planner remembers a decision from 20 turns earlier after a restart.
- **G2 — Agents talk freely, with limits.** Any agent can message any other; every message lands
  in one log. ✅ when a planner→builder→reviewer loop completes a tracker task with no human
  relay, and a deliberately looping pair is stopped by the cap.
- **G3 — Scoped autonomy.** Builders edit freely inside their assigned folder; anything outside,
  `git push`, and destructive commands wait for you in the Hub. ✅ when an out-of-scope write is
  held for approval (probe-verified, not assumed).
- **G4 — Watch and steer.** One Hub view: roster with live status, conversation timeline, message
  any agent, pause/stop, approvals, spend per agent. ✅ when a whole session is run from the Hub.
- **G5 — Bounded cost.** Per-agent budget and per-thread turn cap enforced centrally; spend visible.

## Scope
### In Scope
- Session runtime for long-lived agents (start, message, pause, resume, stop).
- Message bus (agent↔agent, you↔agent) + persisted conversation log.
- Permission gate: scope folders, held actions, write-scope locks so two writers never overlap.
- Guardrails: budget, turn caps, hop limits, global kill switch.
- Hub "Team" view in the Command tab.
- Agent library: workflow agents + per-project experts; create/edit from the Hub.
- Team templates for the four patterns.

### Out of Scope (v1)
- Cloud/remote agents (everything runs on this machine).
- Agents spawning new agents on their own (you or a template creates agents; agents only message).
- Voice-driven team control (the voice daemon can later become one more "you" input).
- Cross-machine sync of live state (definitions travel via git; live sessions don't).

## Tech Stack & Architecture

### Recommendation: Python Claude Agent SDK inside the dashboard  ⚠️ needs your confirmation
`claude-agent-sdk` (PyPI, 0.2.176) installed into `voice/.venv`, driven by the existing FastAPI
dashboard. Each agent = one long-lived `ClaudeSDKClient`.

Why it fits — each of these is a gap the plain CLI doesn't close:
- **Long-lived sessions** with programmatic send/receive (no hand-rolled stream-json plumbing).
- **In-process custom tools** (SDK MCP server) → the bus tools (`send_message`, `list_agents`,
  `post_update`) run inside the dashboard, so the dashboard sees and routes every message.
- **Per-action permission callback** (`can_use_tool`) → the scoped-autonomy rule (G3) and
  write-scope locks become code. The CLI has no equivalent: `--permission-prompt-tool` was absent
  on 2.1.167, and `--allowed-tools` was probe-shown **not** to confine a persona.
- **Hooks** for turn counting, budget checks and logging.

Alternatives considered:
| Option | Verdict |
|--------|---------|
| Raw `claude -p --input-format stream-json` subprocesses (extend `process_manager.py`) | **Fallback.** Verified to exist on 2.1.289, no new dependency — but bus tools need a separate MCP server process, and per-action permission needs workarounds. Use only if H0 fails. |
| Native background agents (`claude --bg` + built-in `SendMessage`/`ListAgents`) | **Ruled out as the core.** Least code, but there is no CLI command to inject a message into a background session from outside, so the Hub can't message agents, enforce caps, or reliably log. Revisit if Claude Code adds one. |
| TypeScript Agent SDK as a separate service | Ruled out — second runtime next to the Python dashboard for no gain. |

### Shape
```
Hub (web/) ──HTTP/WS──▶ dashboard/server.py
                          └─ dashboard/harness/
                               runtime.py   AgentSession: ClaudeSDKClient per agent; start/send/pause/resume/stop
                               bus.py       in-process MCP tools + routing + inbox queues + caps
                               gate.py      can_use_tool: scope check, held actions, scope locks
                               store.py     SQLite (same DB style as registry.py): agents, threads, messages, holds
                               library.py   load agent definitions (brain agents/ + project .brain/agents/)
```
- **Definitions live in git, live state lives at home.** Workflow agents: `agents/workflow/*.md`
  in brain. Project experts: `<project>/.brain/agents/*.md` (travels with the repo, like tasks).
  Session ids, messages, spend: `~/.claude/brain-dashboard/harness.db`.
- **Delivery model.** A message to a busy agent is queued and delivered as its next turn; an idle
  agent wakes on delivery. Each message carries a thread id and hop count.
- **Tracker stays the unit of work.** Agents claim tasks, post updates and move status through
  the existing tracker API (agents may reach `review`, never `done` — unchanged rule).
- **Model routing.** Each agent pins its own model/effort. The `model-router` mod must not
  override harness sessions (see Risks).

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| H0 | SDK spike | Install `claude-agent-sdk`; probe: long-lived client with a brain persona + per-agent model, subscription auth, in-process tool call, `can_use_tool` blocking an out-of-scope write, budget stop, resume after restart, router-mod interaction. Go/no-go vs stream-json fallback | — |
| H1 | Session runtime + store | `harness/runtime.py` + `store.py`: create/start/send/pause/resume/stop named agents; persist roster, session ids, messages, spend; endpoints under `/api/harness/*`; events onto the existing hub websocket | H0 |
| H2 | Message bus | `bus.py`: `send_message(to, text, thread?)`, `list_agents()`, `post_update(task?)` tools; inbox queue + wake-on-delivery; thread ids, hop counts; per-thread turn cap and per-agent budget enforced centrally | H1 |
| H3 | Permission gate | `gate.py`: free edits inside scope folders; outside-scope writes, `git push`, destructive commands → held for Hub approval (reuse D8 approval pattern); write-scope locks; global kill switch; audit to `audit.jsonl` | H1 |
| H4 | Hub Team view | Command view becomes the team surface: roster lanes (status, model, spend), conversation timeline, composer to message any agent, pause/stop, approvals inbox, create-agent form | H1, H2, H3 |
| H5 | First team end-to-end | Planner (Opus) + builder (cheaper model) + reviewer on one project: takes a tracker task to `review` with no human relay; loop-cap and out-of-scope probes pass | H2, H3, H4 |
| H6 | Agent library | Workflow agents (one per phase, wrapping the existing commands' intent) + project experts seeded from each project's CLAUDE.md, docs, tasks and memory; create/edit definitions from the Hub | H5 |
| H7 | Team templates | One-click teams for the four patterns: pipeline, debate, standing project team (pulls tracker backlog), research swarm with lead | H6 |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Runaway loops / spend from free messaging | High | High | Per-thread turn cap, hop count, per-agent budget, global kill switch — all enforced in the bus, not by prompt. H5 includes a deliberate loop probe |
| Permission gate leaks (assumed confinement that isn't real) | Med | High | Probe in H0 and H5, as with D8. Never rely on `--allowed-tools`; gate every tool call in `can_use_tool` and keep the `--add-dir` confinement as a second layer |
| `model-router` mod rewrites harness agents' models | High | Med | H0 checks it; fix by having the router skip when a harness env flag is set (or load harness sessions without user plugins) |
| SDK auth or version drift vs installed CLI | Med | Med | H0 verifies subscription auth; pin the SDK version; stream-json fallback kept documented |
| Context bloat in long-lived agents | Med | Med | Rely on Claude Code auto-compaction; agents post durable state to tracker tasks so a fresh session can rebuild |
| Two writers editing the same files | Low (with locks) | High | Write-scope locks in the gate: a scope can be held by one writer at a time |
| Concurrency vs existing fleet runs | Med | Low | Share one concurrency budget with `process_manager` (`MAX_CONCURRENT`) |

## Dependencies
- `claude-agent-sdk` (Python, PyPI) → `voice/.venv` (pending H0 go).
- Claude Code CLI ≥ 2.1.289 (installed).
- Existing: `dashboard/` server + websocket hub, `registry.py`, `process_manager.py` approval pattern, tracker API, `agents/` personas.

## Open Questions
1. **Confirm the SDK recommendation** (vs the stream-json fallback). Blocks H1.
2. Default models per role: planner Opus 5.5 / builder Sonnet 5.5 / reviewer Sonnet 5.5 / scouts Haiku 5.5? (proposed)
3. Default caps: per-agent budget (proposed $2/day), per-thread turn cap (proposed 20), hop limit (proposed 8)?
4. Should idle project experts stay running, or stop when idle and resume on a new message? (proposed: stop when idle and resume by session id — no cost while idle)

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Agent topology | Free messaging, with limits | User choice; limits enforced centrally make it safe | 2026-10-31 |
| Writer autonomy | Free inside a scoped folder; outside-scope, push, destructive → Hub approval | User choice; matches how the work actually flows, keeps irreversible actions human-gated | 2026-10-31 |
| Use cases | All four patterns (pipeline, debate, standing team, research swarm) | User choice; drives workflow agents + project experts + templates | 2026-10-31 |
| Message bus owner | Dashboard-owned (in-process tools), not native SendMessage | No external injection into native background sessions → Hub couldn't message, cap or log | 2026-10-31 |
| Runtime | Python Agent SDK (pending H0 + confirmation) | Long-lived clients, in-process tools, per-action permission callback | 2026-10-31 |
| Definitions vs state | Definitions in git (brain `agents/workflow/`, project `.brain/agents/`); live state in `~/.claude/brain-dashboard/harness.db` | Same split as the tracker: what should travel goes in git, runtime churn stays local | 2026-10-31 |
| Agents creating agents | Out of scope for v1 | Keeps cost and topology predictable; templates cover the need | 2026-10-31 |

## Handoff Readiness (for /scaffold or /build)
- Tech decided: ⚠️ pending confirmation of the SDK runtime (H0 spike proves it either way).
- Structure clear: ✅ `dashboard/harness/` (runtime, bus, gate, store, library); definitions in `agents/workflow/` + `<project>/.brain/agents/`.
- Entry points: ✅ `dashboard/server.py` (`/api/harness/*`), `web/hub.js` Command view.
- **First slice = H0 → H1.** H0 is a half-day probe and decides the runtime before anything is built.

## Agent Harness — Revision 1 (2026-10-31)

### Answers folded in
1. **Runtime: Python Agent SDK — confirmed.** Stream-json stays the documented fallback only.
2. **Models: defaults accepted, plus per-agent control and dynamic routing.** Every agent has a
   model setting, editable from the Hub at any time, in one of two modes:
   - **Pinned** — a fixed model + effort (defaults: planner Opus 5.5, builder/reviewer Sonnet 5.5,
     scouts Haiku 5.5).
   - **Auto** — per-turn routing between light / standard / deep tiers, using the same rules +
     classifier rubric as the `model-router` mod (one shared rubric file, not two copies). Each
     agent can set its own tier→model map and a floor/ceiling (e.g. a reviewer never below
     standard). The chosen model and the reason are shown on every turn in the timeline.
   The harness owns model choice for its sessions; the `model-router` mod skips them.
3. **Usage: runs on your normal Claude Code account.** The SDK drives the installed `claude` CLI,
   which is logged in with your claude.ai subscription (checked: `authMethod: claude.ai`, no
   `ANTHROPIC_API_KEY` in the environment). So agent work counts against your plan's usage
   limits, not a separate API bill. Consequences:
   - The harness must **never set `ANTHROPIC_API_KEY`** for agent sessions — that would silently
     switch them to API billing. H0 verifies the SDK picks up the subscription login; the session
     runtime strips the variable defensively.
   - **Budgets become usage guardrails**, not money: the SDK's reported cost is a dollar-equivalent
     measure of usage. Caps protect your weekly limit from a runaway team. The Hub shows team usage
     beside the weekly-limit meter already in the rail.
4. **Idle agents: stop when idle, resume on demand.** An idle agent's process is closed after a
   short idle window (proposed 10 min); its session id is kept, and the next message resumes it
   with full context. No usage or memory while idle; long-lived in behaviour, not in process.

### Milestone changes
| # | Change |
|---|--------|
| H0 | Also verify: subscription auth through the SDK; switching model mid-session (else resume with a new model per turn); router mod skips harness sessions |
| H1 | Adds the per-agent model setting (pinned / auto, tier map, floor/ceiling) and idle stop + resume |
| H2 | Adds auto routing per delivered turn (shared rubric with `model-router`) |
| H4 | Adds a model control on each roster lane and the per-turn model/reason in the timeline; team usage next to the weekly-limit meter |

### Decisions Log (additions)
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Runtime | Python Agent SDK (confirmed) | User confirmed; H0 still proves it | 2026-10-31 |
| Model control | Per-agent pinned or auto, editable live from the Hub | User wants adjustable + dynamic models | 2026-10-31 |
| Routing logic | Reuse `model-router`'s rules + rubric via one shared file | One source of truth for "how hard is this" | 2026-10-31 |
| Billing | Subscription via the CLI's claude.ai login; never pass an API key | User wants it on their normal account | 2026-10-31 |
| Caps | Usage guardrails (dollar-equivalent), not spend | Subscription isn't billed per call; caps protect the weekly limit | 2026-10-31 |
| Idle agents | Stop after idle window, resume by session id | No usage while idle, same context on return | 2026-10-31 |

### Open questions (remaining)
- Idle window length (proposed 10 min) and default caps ($2-equivalent/day per agent, 20 turns per
  thread, hop limit 8) — fine to tune after H5.

## Agent Harness — H0 results (2026-10-31): GO on the Python Agent SDK
`claude-agent-sdk==0.2.176` in `voice/.venv` (pinned in `voice/requirements.txt`). Probe suite:
`./voice/.venv/bin/python -m dashboard.harness.probe_sdk` — **9/9 pass**; re-run after SDK or
Claude Code upgrades.

| Probe | Result |
|-------|--------|
| auth | Runs on the claude.ai subscription (`apiKeySource: none`); `ANTHROPIC_API_KEY` stripped from session env |
| persona | `extra_args={"agent": "scout"}` gives the read-only tool set |
| pinned-model | Session runs on the model it's given |
| bus-tool | In-process MCP tool (`send_message`) is called and the dashboard sees the arguments |
| gate | `can_use_tool` allowed a write inside scope and blocked one outside (file not created) |
| set-model | `client.set_model()` switches model mid-session — auto routing can switch per turn without a restart |
| resume | A fresh client with `resume=<session_id>` recalls earlier context — idle stop + resume works |
| budget | `max_budget_usd` ends the session with `error_max_budget_usd` |
| router-skip | Passes only with the fix below |

Findings that change the build:
- **The `model-router` mod loads inside SDK sessions and overrode both the pinned model and
  `set_model()`** (a pinned Haiku session ran on Opus). Fix, no mod change needed: harness
  sessions pass `settings={"enabledPlugins": {"model-router@brain": false}}`. H1 bakes this in.
- **`allowed_tools` entries bypass `can_use_tool`** (the SDK warns: a whole-tool allow
  auto-approves before the callback). The gate must either keep gated tools out of
  `allowed_tools` or enforce via a `PreToolUse` hook. H3 uses the hook so no allow rule
  (including ones in settings files) can shadow it.
- The SDK runs its own bundled CLI (2.1.316), not the installed 2.1.289. Auth and `~/.claude`
  config are shared, so this is fine; note it when debugging version-specific behaviour.
- Probe cost was a few cents of usage-equivalent on Haiku/Sonnet.

## Agent Harness — H1 done (2026-10-31): session runtime + store
- `dashboard/harness/store.py` — SQLite `~/.claude/brain-dashboard/harness.db`: `agents` (persona, project,
  brief, scope, model settings, session id, paused, usage) + `messages` (role, sender, text, model, cost).
- `dashboard/harness/runtime.py` — `Harness` + per-agent `Session`: inbox handled one turn at a time;
  connect on demand, close after 10 min idle, resume by session id; pinned/auto model settings
  (auto clamps to floor/ceiling; per-turn classification is H2) with live `set_model`; teammate
  messages arrive as `[from <name>]`; events on the hub websocket as `{"type":"harness", ...}`.
- Baseline gate (PreToolUse hook): read tools, read-only git, bus tools, and writes inside scope are
  allowed; everything else denied with a reason logged to the timeline. H3 adds Hub approvals + locks.
- API: `GET/POST /api/harness/agents`, `PATCH/DELETE /api/harness/agents/{name}`,
  `GET …/{name}/messages`, `POST …/{name}/message`, `POST …/{name}/{pause|resume|stop}`.
- Tests: `./voice/.venv/bin/python -m dashboard.harness.test_runtime` (9, fake SDK client, no usage).
- Live-verified through the API: Haiku→Sonnet switch mid-session, stop then resume recalls context,
  in-scope write allowed, out-of-scope Write and Bash denied by the hook (files not created).
- Observed cost: a Sonnet turn on a fresh session is ~$0.10 equivalent (Claude Code system prompt + tools
  load each connect). Worth watching when caps are set in H2; keeping sessions warm while busy helps.

## Agent Harness — H2 done (2026-10-31): message bus, limits, auto routing
- **Bus:** each session gets an in-process MCP server with `send_message(to, text)` and `list_agents()`.
  A user message starts a thread (hop 0); each agent-to-agent hand-off carries the thread and hop+1.
  Teammate messages arrive labelled `[from <name>]` with a reminder that plain replies go to the user's
  timeline and answers go back via `send_message`. (Live run without the reminder: the answerer replied
  to the timeline only, and the asker never got the answer.)
- **Personas get the bus tools:** a persona's `tools:` is an allowlist, so `--agent scout` hid the bus.
  The harness now defines a session-local `harness-<persona>` copy (same prompt and tools, plus the bus
  tools) via `ClaudeAgentOptions.agents`. Fake-client tests couldn't catch this; the live run did.
- **Limits, enforced in code:** hop limit 8 per chain, 20 agent turns per thread, daily usage cap per
  agent (default $2-equivalent, `limits.daily_usd`, editable via PATCH). Hitting the daily cap parks the
  message and pauses the agent; the SDK also gets `max_budget_usd` = today's remainder so one turn
  can't overrun. Refusals go back to the sending agent as tool errors.
- **Auto routing:** shares the model-router mod's rules, moved to `mods/model-router/hooks/rules.ts`
  (strict-JSON object both the mod and `dashboard/harness/routing.py` read; the mod engine can't import
  `.json`). Undecided messages → standard (no classifier call: a session start costs more than it saves).
  Every assistant message records `route` (e.g. `auto: light (git)`, or the floor/ceiling clamp).
- **Deferred to H5:** `post_update` (tracker updates from agents) — lands with the first real team.
- Tests: 14 in `dashboard.harness.test_runtime` (bus relay with threads/hops, runaway ping-pong stopped
  at the hop limit, daily-cap park + resume, per-turn auto routing). Mod: validates, 12/12 tests.
  Live: two Haiku agents completed an ask → answer → report round trip (hops 0→1→2), about half a cent.

## Agent Harness — H3 done (2026-10-31): permission gate
- **Three-way gate** (PreToolUse hook, `runtime.gate_decision`):
  - *Allow:* read tools, bus tools, read-only git, writes inside scope, commands approved "always" for that agent.
  - *Hold for you:* writes outside scope, any other command (`git push` and destructive commands flagged
    by kind), any unrecognised tool. The turn waits; the Hub decides; unanswered holds expire as denied
    after 15 min (hook timeout set past that). The agent is told not to retry a denied action.
  - *Deny:* `Task`/`Agent` (agents don't spawn agents in v1).
- **"Always" approvals:** exact command, per agent, plain commands only — push and destructive commands
  are asked every time.
- **Writer scope locks:** checked when a scope is set (create/update): two writer personas can't share or
  nest folders (409 naming the other agent). Read-only personas never lock. Deleting an agent frees it.
- **Kill switch:** denies everything waiting, pauses every agent, interrupts live turns, closes sessions.
- **Holds** persist in `holds` (status pending/approved/denied/expired; pending ones expire on restart).
  Deleting an agent or stopping the server denies its waiting holds so no hook hangs.
- **Audit:** hold decisions, denials and kills go to `~/.claude/brain-dashboard/audit.jsonl`.
- API: `GET /api/harness/holds?status=pending`, `POST /api/harness/holds/{id}/{approve|deny}` (`{"always": bool}`),
  `POST /api/harness/kill`. Agent views gain `state: "waiting"` + `hold` id, and `always`.
- Tests: 20 in `dashboard.harness.test_runtime` (approve+always then auto-allow, deny, expiry, push never
  "always", locks incl. nesting and release, kill switch, delete releases a waiting hold).
- Live (Haiku builder): `echo` command held → approved "always" → ran; the second run went through with
  no hold; overlapping writer scope refused. The agent declined the out-of-scope write itself, so that
  hold path is covered by the tests (same code path as the command hold) rather than live.
- Fixed during H3: test runs were writing to the real audit log; the audit sink is now injectable and
  tests use their own. Entries from three earlier test runs remain in the real log (not removed).

## Agent Harness — H4 done (2026-10-31): Hub Team view
- **Placement deviation:** a dedicated **Team** view (sidebar, TOOLS) rather than rebuilding Command.
  A long-lived conversation needs the full-height list/detail layout the app dashboards use; Command
  keeps the voice dock and pipeline.
- **Bar:** agents / working / used-today pills, "waiting on you" when holds are pending, New agent,
  Stop everything (kill switch, with confirm).
- **Approvals:** one card per pending hold (agent, kind, exact command or path, reason) with Allow,
  Always allow (plain commands only) and Deny. Push and destructive holds are tinted red.
- **Roster lanes:** state dot (pulses while working, amber when waiting), persona, model or "auto",
  usage today vs the daily cap, queued count.
- **Agent detail:** state badge, Pause/Resume, Put to sleep (close process, resume on next message),
  Delete; "Model and limits" (pinned model, or auto with never-below/never-above; effort; daily cap);
  conversation timeline (you, teammates with hand-off number, agent replies with model / route / cost
  chips, tool calls, gate notes); composer (Enter sends).
- **Live:** harness websocket events update lanes, header and timeline without redrawing forms; a
  15 s poll backs them up. Sidebar shows the team count or "N waiting"; the rail shows TEAM TODAY usage
  under the weekly limit.
- Verified in the browser against real Haiku agents: create from the form, message and watch the
  reply stream in, approve a held command from its card, switch a builder to auto with a ceiling,
  Stop everything (denied the waiting hold, paused both), delete from the UI. No console errors.

## Agent Harness — H5 done (2026-10-31): first team end-to-end
- **Tracker tools on the bus:** `read_task(task)` and `post_update(task, text, status?)` on the agent's own
  project. Agents may move tasks to `doing` or `review` only; `done` is refused (tracker rule unchanged).
  Updates are logged as `agent <name>: …` on the task and as a `tracker` line in the agent's timeline.
- **Live team run** (trial task in a sandbox folder, script standing in for the user at the approval cards,
  approving only `python` runs of the sandbox tests):
  - h5-planner (Opus, read-only) read the task, moved it to doing, sent h5-builder the files and acceptance
    criteria; h5-builder (Sonnet, scoped to the sandbox) wrote both files, ran the test after approval, and
    reported back; the planner asked h5-reviewer (Sonnet) to review; reviewer replied APPROVE; the planner
    posted a summary and moved the task to review. **57 s, ~$0.36 total, no human relay.**
  - The reviewer's chained `cd … && cat … && python …` was denied by the stand-in's narrow policy; it
    reviewed by reading instead and said so, and the planner's report to the user flagged that only the
    builder had run the tests. Honest reporting held up across three agents.
  - Independently re-ran the tests and the acceptance cases: pass.
- **Live probes:** runaway loop (two agents told never to stop) cut off at the hop limit after 9 turns /
  24 s / under $0.01; out-of-scope Write held with the right kind and reason, denied, file not created,
  agent didn't retry.
- Trial task, sandbox and agents removed afterwards. Tests: 21 harness tests + all dashboard suites pass.
- **Learned for H6/H7:** a reviewer that should run tests needs either its commands pre-approved
  ("always") or a narrower persona allowing test runs; worth a "reviewer can run tests in scope" option.
