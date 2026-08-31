# ryans-boomin-beats — session summaries

_Extracted from brain's `updates/queue.md` at 2026-08-31T03:07:02Z._

## 2026-06-05 — ryans-boomin-beats

- Brainstormed, planned, and scaffolded LLM playlist builder feature; migrated full backend from Django to FastAPI; modernized Spotify OAuth from implicit grant to PKCE; profile page working end-to-end
- Patterns: (1) Raising framework migration as a question mid-scaffold-preview is the right time — pausing to evaluate hybrid vs. full migration prevented a messier outcome; (2) Spotify implicit grant is dead for new apps (April 2025) — any new Spotify OAuth integration should start with PKCE; (3) `localhost` blocked as Spotify redirect URI for new apps — must use `127.0.0.1` explicitly, and Vite must be configured to bind to it on macOS; (4) Safe `.get()` defaults throughout Spotipy response parsing — fields aren't guaranteed even on well-documented objects
- Brain improvements: /scaffold should prompt for credentials strategy in the preview (flag hardcoded secrets in config files as an anti-pattern before writing); A FastAPI exception handler that preserves CORS headers on 500s is worth adding to the scaffold template for FastAPI projects

## 2026-06-24 — ryans-boomin-beats

- Massive multi-feature session: full dark redesign (semantic tokens + logo palette), Discover-Similar-Songs fix, persistence layer, custom search w/ cover art, AI radar+scores+tags, and full Spotify account integration (global token, drag-and-drop Playlists panel, Liked Songs, top-track seeds, wiki). Ran brainstorm→plan→scaffool ~5× in one session.
- Patterns: (1) brainstorm→plan→scaffold scales across many sub-features in a single session — each cycle yields decision-locked plans, no mid-build ambiguity; (2) sequence the enabling prerequisite first (global token before any account action) and name it explicitly in the plan to avoid "works on page A, fails on page B"; (3) client-persisted state needs a cache-versioning convention from day one (bump a key suffix on shape change), and "feature doesn't show" should trigger suspicion of stale persisted state before code; (4) when an endpoint returns surprising data, dump the raw upstream response early instead of reasoning about expected shape (caught an undocumented Spotify field rename tracks→items this way).
- Brain improvements: The biggest friction was CSS/visual iteration with no feedback loop — the assistant round-tripped every visual nudge through the user (radar chart took 5+ iterations). /reflect (and the workflow generally) should surface /run or /verify as the default for visual/CSS-heavy work so the assistant can screenshot rendered output. Consider a brain rule: "for CSS/layout changes, offer to launch + screenshot via /run before iterating blind." Also minor: Edit tool whitespace/Unicode (tab inconsistency + → arrow) mismatches forced scripted-edit fallbacks twice.
