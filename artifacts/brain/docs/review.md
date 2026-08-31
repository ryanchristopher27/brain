# Review — Frontend Domain (whole-domain, post-M8)

Date: 2026-06-06
Triggered by: /review after M8 completion (capstone)
Scope: `domains/frontend/` — full domain (M1–M8)
Focus: All (Plan Adherence · Code Quality · Security)

## Summary

The consolidation is complete and sound. All 8 milestones delivered per plan; both deviations were
flagged and logged. This capstone pass found 2 fresh issues — a leftover template token and a
now-reachable path-traversal in the persist path — **both fixed and verified this session**. No
issues remain open that block use.

**Critical: 0 · Warning: 0 open (2 fixed) · Suggestion: 2 open (cosmetic)**

## Plan Adherence

- Every in-scope item built: domain scaffold, vendored data+search (M2), vendored detector (M3),
  9 synthesized references (M4), priority-ladder rules (M5), `/design` command (M6), detection +
  Cursor rule (M7), wiring + docs (M8).
- Architecture matches the plan: single `domains/frontend/`, impeccable spine + ui-ux-pro-max data,
  tooling vendored & dependency-light & degrade-gracefully, scripts referenced by resolved path.
- Out-of-scope respected: no CLI, browser extension, website, live-loop, or full 23-command surface.
- Deviations (both logged in `docs/plan.md` Decisions Log): included `data/stacks/` (M2);
  synthesized references rather than copying nonexistent files (M4). Both user-approved.

## Code Quality

- Structure follows brain's domain template (README, detect, rules, cursor-rule, commands/,
  references/, plus data/ + scripts/ for tooling). Index + BRAINSTORM updated.
- Verified mechanically across the domain: all internal cross-links resolve; all 23 cited
  `detector:` ids valid; all 7 `--domain` values valid; all 9 references named in `design.md`
  exist; `.mdc` frontmatter valid YAML; rules.md ↔ cursor-rule.mdc section parity.
- Vendored detector carries dormant browser/visual engines (part of the import closure; documented
  in scripts/README). Not dead-code-removable without patching upstream files — left as-is.

## Security

- Scripts: no eval/exec/shell/subprocess/network/pickle; no hardcoded paths; no secrets (verified
  M2). File writes only under opt-in `--persist`.
- **S1 (path traversal) — found reachable, fixed.** M6 surfaced `--persist` in `design.md`, making
  the unsanitized `project_name`/`page` path-building exploitable (a `../` name could escape
  `cwd/design-system/`). Added a `_safe_slug()` helper (brain-local patch, commented for
  provenance) used at both write sites. Verified: `../../escape attempt` writes to
  `design-system/escape-attempt/`, nothing escapes; generator still works.

## Findings

### Critical
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| — | — | none | — | — |

### Warning
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| W3 | `commands/design.md:8` | Leftover impeccable `{{model}}` template token; brain doesn't template commands so it renders literally | Replace with plain prompt text | ✅ Fixed this session |
| S1 | `scripts/design_system.py` (persist) | Path traversal via `project_name`/`page` (only spaces replaced); reachable via `/design system --persist` | Slugify names before path use | ✅ Fixed this session (`_safe_slug`) |

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| S2 | `docs/plan.md` | M-checkboxes | Tick success criteria | ✅ Done in M8 |
| S3 | rules/refs | Path snippets illustrative | Note added in M6 | ✅ Done |

## Resolved This Session
- **W3** — removed `{{model}}` token from `design.md`.
- **S1** — hardened `design_system.py` persist paths with `_safe_slug()`; traversal verified blocked.

## Prior Findings (carried forward, from incremental reviews)
- **W1** (M2) — `.gitignore` for `__pycache__` → ✅ fixed in M2.
- **W2** (M5) — script-path base → ✅ resolved in M6 (`$FE` runtime resolution, verified via symlink).

## Carried to /iterate
- Nothing blocking. Optional only: if upstream `design_system.py` is ever refreshed from
  ui-ux-pro-max, re-apply the `_safe_slug()` patch (it's marked with a provenance comment).
