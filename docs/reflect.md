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
