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
