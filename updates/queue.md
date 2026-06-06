# Brain Update Queue

Append-only log of session summaries and improvement ideas. Accumulated automatically via the stop hook and /reflect.
Review periodically to identify patterns worth adding as rules, skills, or domains.

---

## 2026-06-04 — prediction_market_bot
- Completed M3 (baseline model), fixed Kalshi fractional API format, scaffolded full dashboard Phase 1 (26 files, FastAPI + Streamlit)
- Patterns: (1) Review step between /plan and /scaffold is high-value — caught 10 gaps before any code was written; (2) For router import errors, grep the importing file for typos before assuming circular imports; (3) "direct import works, chain fails" = typo in the chain, not necessarily circular import
- Brain improvements: The /scaffold skill could prompt for a "review pass" before confirming scaffold — the current flow goes straight from plan preview to "ready to scaffold?" A beat of "have you stress-tested this plan against the current codebase?" would have made the review step an explicit part of the workflow rather than something the user had to ask for separately


## 2026-06-05 — ryans-boomin-beats
- Brainstormed, planned, and scaffolded LLM playlist builder feature; migrated full backend from Django to FastAPI; modernized Spotify OAuth from implicit grant to PKCE; profile page working end-to-end
- Patterns: (1) Raising framework migration as a question mid-scaffold-preview is the right time — pausing to evaluate hybrid vs. full migration prevented a messier outcome; (2) Spotify implicit grant is dead for new apps (April 2025) — any new Spotify OAuth integration should start with PKCE; (3) `localhost` blocked as Spotify redirect URI for new apps — must use `127.0.0.1` explicitly, and Vite must be configured to bind to it on macOS; (4) Safe `.get()` defaults throughout Spotipy response parsing — fields aren't guaranteed even on well-documented objects
- Brain improvements: /scaffold should prompt for credentials strategy in the preview (flag hardcoded secrets in config files as an anti-pattern before writing); A FastAPI exception handler that preserves CORS headers on 500s is worth adding to the scaffold template for FastAPI projects


## 2026-06-06 — brain (frontend domain)
- Consolidated two external suites (ui-ux-pro-max MIT, impeccable Apache-2.0) into `domains/frontend/` — brain's first populated L2 domain: vendored stdlib-Python search + Node anti-pattern detector, 9 synthesized references, priority-ladder rules.md, `/design` command, Cursor rule, detection. All 8 milestones built, reviewed, verified end-to-end.
- Patterns: (1) Re-check conditionally-deferred review findings at the milestone that could trigger them — deferring S1 "until --persist is wired" then re-checking in the final review caught a live path-traversal; (2) Verify external source-of-truth (actual file tree) before planning around it — impeccable's README advertised 7 reference files that don't exist, forcing a mid-build pivot to synthesis; (3) Vendoring third-party code transfers its security surface to you — budget a security pass per vendored component; (4) Plan risk-table items got handled at the right milestones, the one unforeseen risk (source reality) caused the only pivot.
- Brain improvements: (1) RECURRING (3rd session) — the plan→build/scaffold transition wants an explicit "stress-test the plan against reality" beat; this session's variant is that /plan should inspect external/vendored source structure before planning around its README; (2) A reusable "vendoring checklist" (license+NOTICE, dependency audit, security surface, runtime path resolution) would have structured the M2/M3/M8 work that was re-derived ad hoc.
