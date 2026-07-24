# Reflect — Frontend Domain Consolidation

Date: 2026-06-06
Type: Project Close
Phase context: /plan → /scaffold → /build (M1–M8) → /review ×3 → /reflect

## Accomplished
- Consolidated two external frontend suites (ui-ux-pro-max-skill, impeccable) into `domains/frontend/`
  — brain's first populated L2 domain. All 8 milestones delivered.
- Vendored a dependency-light toolchain: stdlib-Python BM25 search over 12 CSVs + 16 stack files,
  and impeccable's self-contained 82-rule Node anti-pattern detector.
- Authored the brain-native layer: 9 synthesized topic references, a priority-ladder `rules.md` with
  runnable verify-hooks, a single `/design` command (craft·shape·critique·audit·polish·system), a
  Cursor rule, and detection signals. Installed globally via the auto-sync hook; verified end-to-end.

## What Worked
- **The risk table earned its keep.** W2 (script paths break once symlinked) was predicted at plan
  time and closed at exactly the right milestone (M6) with runtime `$FE` resolution.
- **Conditional deferral + re-check.** Deferring S1 with "only matters if M6 wires `--persist`," then
  re-checking that condition in the M8 review, caught a live path-traversal. The discipline paid off.
- **Tooling-first sequencing.** Doing M2/M3 (search + detector) before the content layer meant the
  references and rules could cite real, verified hooks instead of aspirational ones.
- **Pausing on the M4 discrepancy** rather than forcing the plan's stated method — surfaced the
  stale-README problem and got an explicit approval to synthesize.

## What Didn't Work
- **The plan trusted the README, not the source.** M4 was planned around impeccable's advertised "7
  reference files," which don't exist. The pivot was cheap, but a source-tree check at plan time
  would have avoided the mid-build deviation.
- Minor self-inflicted friction: a zsh word-splitting quirk produced false negatives in a validation
  loop (twice) before I switched to `${=var}`.

## Decisions Reviewed
- **Synthesize vs. copy references (M4):** held up. User trusts the synthesized content for now,
  will refine in use. The distillation stayed faithful (preserved `rule:` ids, register splits).
- **Include `data/stacks/` (M2):** correct — `--stack` is documented in the command spec; omitting
  it would have shipped a broken feature.
- **Vendor (not submodule):** correct for decoupling, but it put the burden of security review on us
  — which is how S1 became ours to fix. Accepted tradeoff.
- **Autonomous milestone calls:** user confirmed the pace and decisions were right.

## Lessons Learned
- **Verify external source-of-truth before planning around it.** READMEs advertise intent, not
  current reality — for vendoring work, inspect the actual tree during `/plan`.
- **Re-examine conditionally-deferred findings at the milestone that could trigger them.** A deferred
  finding is a tripwire; wire it to the milestone, don't just file it.
- **Vendoring third-party code transfers its security surface to you.** Budget a security pass per
  vendored component, not just an overall review.

## Surprises
- impeccable's README links to reference files that were refactored away — the guidance now lives in
  `SKILL.src.md` + command-refs.
- The brain `post-edit-install-sync.sh` hook silently kept `/design` installed as I built — M8's
  "install" was already done; I nearly surfaced a redundant manual step.

## Memory Updates (suggested — not yet written)
- **Feedback memory:** the recurring plan→build/scaffold "stress-test against reality" gap (now 3
  sessions running) — strong enough to persist as guidance.
- **Project memory:** brain now has a `frontend` domain; the pattern for adding domains (distill →
  rules+references+detect+cursor-rule, vendor dependency-light w/ attribution) is established.

## Next Steps
1. Commit the work (uncommitted tree: `domains/frontend/`, `docs/`, `BRAINSTORM.md`,
   `domains/README.md`, `.gitignore`) — on a branch per brain git conventions.
2. Dogfood `/design` in a real frontend project; refine the synthesized references in use (Q1).
3. If `design_system.py` is ever refreshed from upstream, re-apply the `_safe_slug()` patch.

## Suggested Next Phase
**Commit, then use it.** The work is reviewed and clean — the natural close is a commit/PR, then
real-world validation. (`/ship` is still deferred in brain, so commit manually for now.)

---

# Reflect — Local Agent Fleet + Voice Interface (plan → scaffold)
Date: 2026-07-21
Type: Milestone (planning + scaffold; build not yet started)
Phase context: /plan → /scaffold → /reflect

## Accomplished
- Planned a 3-pillar initiative (Agent Fleet · Voice · Visualizer) and appended it as a
  versioned section to `docs/plan.md`, with a persona-bound safety model and a lean MCP set.
- Scaffolded 30 files across `agents/`, `mcps/`, `voice/`, `web/` — runnable stubs
  (`python -m voice.daemon` exits 0; MCP JSON valid; `runner.sh` valid).
- Resolved the three interaction-design questions into decisions: headless-CC voice bridge,
  local-first pluggable STT/TTS, personas-as-permission-profiles, `/schedule`-primary.

## What Worked
- **Verified reality before planning** (the recurring lesson, applied): checked `install.sh`
  sync logic, M2 Pro hardware, and installed CLI tools *before* drafting — so the plan named
  the real gap (install.sh has no agents concept) instead of assuming.
- **Reframing beat accepting.** The user's "dashboard" request was redirected from a chat
  clone to a live voice *visualizer*; "voice safety posture" was redirected to persona-bound
  profiles. Both were user course-corrections that improved the design — worth pushing on.
- **One backend, two frontends.** Making the voice core emit events that both audio and web
  consume avoided a second integration — a structural decision that keeps C thin.
- **Scaffold stayed honest.** Behavior-bearing files (install.sh, CLAUDE.md, orchestration
  rule) were deferred to build rather than faked as boilerplate.

## What Didn't Work
- Nothing broke, but the plan front-loaded a lot before a single line ran. The value only
  proves out once A1 wires install.sh + a real headless `claude -p` call is verified.

## Decisions Reviewed
- **Personas = permission profiles** (frontmatter tool allowlists): elegant, but unverified
  that a voice-summoned subagent actually inherits the allowlist as strictly as assumed —
  confirm during A1/B4.
- **Headless `claude -p` bridge:** the whole voice pillar rests on flags not yet verified
  against `claude` 2.1.167. Stubs say so; B4 must verify before relying on them.
- **Lean MCP set:** correct call — most starter MCPs duplicate CC natives; playwright is the
  one real add (ties to the recurring visual-feedback gap).

## Lessons Learned
- The "verify reality first" habit generalizes past vendoring: verify the *host tooling*
  (install.sh, CLI flag surface, hardware) before planning infra around it.
- When a feature request smells like reinventing a solved thing (a chat webpage), name the
  trap and offer the version that fills the actual unmet need.

## Surprises
- The `post-edit-install-sync.sh` hook fires on every Write in brain — same as the frontend
  session. New top-level dirs (`agents/`, `voice/`, `web/`) aren't synced by it yet (A1).

## Memory Updates
- **Project memory (writing now):** brain is becoming a *fleet host* + gaining runtime
  modules (`voice/`, `web/`); status = scaffolded, A1 next.

## Next Steps
1. **A1** — extend `install.sh` (sync `agents/**/*.md` → `~/.claude/agents/`), flesh persona
   bodies, add `agents/` section to `CLAUDE.md`, re-run install, verify via `/agents`.
2. Set `GITHUB_PAT` / `NOTION_TOKEN` before the install run picks up the new MCP configs.

## Suggested Next Phase
**/build A1** — keystone, isolated from the audio stack, unblocks A3/A4 and the voice bridge.

---

# Reflect — Agent Fleet + Voice: A1, A3, B1–B4, C1
Date: 2026-07-23
Type: Milestone (multi — the build-out of the fleet + full voice loop)
Phase context: /build ×7 across two prior /reflect checkpoints

## Accomplished
- **Fleet (A):** A1 (new `agents/` resource type + install.sh sync w/ `name:`-frontmatter
  guard + 4 personas + CLAUDE.md doc), A3 (orchestration rule in universal/rules.md + Cursor
  mirror + `/fleet` command/spec).
- **Voice (B):** B1 (hotkey + mic capture + threaded websocket event stream), B2 (whisper.cpp
  STT, Metal-accelerated), B3 (`say` TTS), B4 (headless `claude -p` bridge — the convergence).
- **Visualizer (C):** C1 (web page renders live state/persona/role-tagged transcript).
- Net: a working local voice assistant wired to the agent fleet, plus a live visual companion.

## What Worked
- **Hardware-free verification as a discipline.** Nearly every milestone needed something I
  can't drive (mic, Accessibility, a browser, a real voice) — and each got a real end-to-end
  check anyway: `--check` (event stream), `say`+`afconvert` synthetic speech to verify STT,
  `--ask`/`--demo` text-driven paths, a stubbed ws client for the C1 event contract, and a
  dry-run of the agents-sync into a temp dir. This kept every milestone genuinely verified,
  not just "compiles."
- **Verify-reality-first, again.** The `claude` CLI probe confirmed the real flag surface
  (`--agent` singular, stream-json shape, `session_id`, and that `--agent scout` yields a
  read-only session) instead of trusting the stubs' assumptions. It validated the entire
  persona-as-permission-profile model empirically.
- **Dry-run before touching global state.** Testing the agents-sync into a temp dir caught the
  `README.md`-installed-as-an-agent bug before it hit `~/.claude/agents/`.
- **Shared `respond_to()` refactor.** Extracting the response path let the mic loop and the
  new `--demo` mode share one code path — no duplication, and `--demo` became a real test tool.

## What Didn't Work
- **venv isolation stumbles (×2).** `numpy` then `tomli` were present in the mambaforge base
  but missing in the fresh venv, so two runs failed before I installed the full set. Relying
  on base-env leakage bit me.
- **The auto-sync hook is a double-edged sword.** `post-edit-install-sync.sh` re-runs the
  *full* `install.sh` on every brain edit — it merged the personal MCPs into global config
  before tokens were set, re-created the README-agent artifact before the guard existed, and
  spams `.bak` files. Convenient, but it fires more broadly than the change warrants.
- Minor: a transient port-rebind flake on back-to-back `--check` runs; a false-failure from my
  own `__version__` probe line.

## Decisions Reviewed
- **Personas = permission profiles:** now *empirically validated* — `--agent scout`'s session
  had only Read/Grep/Glob/Web tools. The safety model holds headless.
- **Headless `claude -p` bridge (the big architectural bet):** paid off — `--resume` gives
  real session continuity, and voice inherits every persona + MCP with no second integration.
- **Local-first STT (whisper.cpp/Metal):** correct for the M2 Pro — fast, private, accurate.
- **`--verbose` required for stream-json under `--print`:** a concrete detail found by probing,
  not documented in my plan.

## Lessons Learned
- **Treat hardware-free verification paths as first-class deliverables.** When a feature needs
  hardware/permissions/UI the assistant can't drive, build text-driven / stubbed / synthetic-
  input modes *as part of the milestone*. It's the difference between "shipped, untested" and
  "verified" — and it doubles as user-facing test tooling.
- **Verify dependencies inside the actual runtime env**, not the base interpreter — venvs don't
  inherit base packages.
- The "verify reality before building" habit held for a 5th time; this variant was probing a
  CLI's real flag surface + output shape before wiring a subprocess around it.

## Surprises
- The personas already appeared in `claude`'s `--agent` list mid-session — the auto-sync hook
  had propagated them without an explicit install.
- macOS `say` with the *default* voice emits ~5 ms of silence; an explicit voice (Samantha)
  works. System-specific, and it would have looked like an STT failure if not isolated.
- `claude -p ... stream-json` init event is a rich introspection surface (tools, agents,
  mcp_servers, session_id, permissionMode) — useful beyond just parsing the reply.

## Memory Updates
- Project memory kept current through C1 (verified CLI flag surface persisted as fact).
- Candidate brain-level memory: "build hardware-free verification paths" as a feedback rule.

## Next Steps
1. **A4** — Operator scheduled job (closes Pillar A). Decide the write-permission strategy for
   an autonomous background agent that `-p` can't interactively approve.
2. Real-mic test (user-only): grant mic + Accessibility, run the full push-to-talk loop.
3. Optional: C2 (orb animation / per-persona identity via /design), B5 (cloud backends).

## Suggested Next Phase
**/build A4** — finish the fleet, then a real-mic pass to validate the one untested surface.
