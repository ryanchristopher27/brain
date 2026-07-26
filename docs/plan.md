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
