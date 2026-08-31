# Reflect — LLM Playlist Builder: Brainstorm → Scaffold + FastAPI Migration
Date: 2026-06-05
Type: Session
Phase context: /brainstorm → /plan → cleanup → /scaffold → environment setup → debugging

---

## Accomplished

- Full brainstorm and plan for the LLM playlist builder feature (4 milestones, all decisions confirmed)
- Header nav refactored from brittle if/else chain to array-driven pattern before scaffold
- Full FastAPI migration from Django (7 routers, 2 services, CORS + session middleware)
- 6 new SvelteKit components scaffolded (LLMSettingsPanel, ChatInterface, SongCard, PlaylistResult, PlaylistNameModal, playlist-builder page)
- conda environment, requirements.txt, environment.yml, .env setup with python-dotenv
- Spotify OAuth modernized: implicit grant → Authorization Code + PKCE
- Profile page working end-to-end on new FastAPI backend

---

## What Worked

- **Brainstorm → plan pipeline was tight.** Decisions compounded cleanly. By the time scaffold started, every significant choice was already locked — no mid-scaffold surprises from ambiguity.
- **Catching the FastAPI migration before scaffold.** The user raised it as a question mid-preview. Pausing to think through the hybrid vs. full migration tradeoff (and choosing full migration) was the right call. Django views were thin enough that the migration cost was low; the async benefit for the LLM feature is real.
- **Header cleanup before scaffold.** The if/else nav refactor took five minutes and prevented scaffolding onto a pattern we'd want to change. Small investment, clean result.
- **Reading both auth flows before planning.** The existing code had two separate Spotify auth paths (app credentials for search/recs, user token for profile). Catching that early shaped how the new spotify_actions endpoints were designed.

---

## What Didn't Work

- **Port hardcoding throughout the frontend.** Every fetch call has `http://127.0.0.1:8005` hardcoded. Changing the port required a grep-and-replace across 7 files. Should be a single shared constant or Vite env var.
- **Credentials setup was an afterthought.** The `.env` file and `python-dotenv` setup happened after the user noticed credentials were hardcoded. It should have been part of the scaffold — the scaffold preview even had `config.py` as a file to create, but didn't flag the credentials pattern.
- **CORS error masked a 500.** When the profile endpoint threw `KeyError: 'genres'`, the browser reported it as a CORS error because the 500 response dropped CORS headers. Required an extra round-trip to diagnose (user had to paste the uvicorn traceback). A global FastAPI exception handler that ensures CORS headers survive errors would have surfaced the real cause immediately.

---

## Decisions Reviewed

| Decision | Outcome | Confidence |
|----------|---------|------------|
| FastAPI full migration | Right call — clean, low cost, async benefit is real | High |
| PKCE for Spotify auth | Necessary, not optional — implicit grant is deprecated | High |
| `127.0.0.1` instead of `localhost` | Required by Spotify policy for new apps (April 2025) | High |
| Iterative Spotify validation loop | Solid design — all returned songs are confirmed Spotify tracks | High |
| Session-based LLM key storage | Works for v1; will need revisiting when auth is added | Medium |

---

## Surprises

- **Spotify deprecated the implicit grant flow.** `response_type=token` is dead for new apps as of April 2025. PKCE is now the required approach for SPAs. The existing profile page code would have needed this fix regardless of the new features.
- **`localhost` is blocked as a Spotify redirect URI.** New apps (post-April 2025) must use `http://127.0.0.1` explicitly. This also required updating the Vite config to bind to `127.0.0.1` since macOS resolves `localhost` to `::1` (IPv6), not `127.0.0.1` (IPv4).
- **Spotipy fields aren't guaranteed.** `artist['genres']` threw a `KeyError` — even well-documented Spotify API fields can be absent on specific objects. Safe `.get()` defaults should be used throughout.

---

## Lessons Learned

- Scaffold should prompt for a credentials strategy upfront — hardcoded secrets in config files is a predictable problem worth addressing in the preview, not after.
- A FastAPI global exception handler that re-applies CORS headers is worth adding early. Debugging masked 500s is friction that compounds during a debug session.
- Spotify's policy changes (PKCE, IP literals) will affect any project using their OAuth. Worth flagging in setup docs for anyone starting fresh.

---

## Next Steps

1. **Test home page search and recommendations** — these hit the migrated FastAPI endpoints (`/search/`, `/get-recommendations/`) which haven't been exercised yet
2. **Fix port hardcoding** — extract `http://127.0.0.1:8005` to a Vite env var (`PUBLIC_API_URL`) so changing the port is a one-line change
3. **Add FastAPI global exception handler** — ensure CORS headers survive 500 errors to make future debugging faster
4. **Test the playlist builder end-to-end** — connect LLM key, generate a playlist, verify Spotify validation loop, test save and queue actions
5. **Add new Spotify scopes to the frontend OAuth** — `playlist-modify-private` and `user-modify-playback-state` are in the backend SCOPE config but the frontend's PKCE auth flow needs them too for the spotify_actions endpoints to work

## Suggested Next Phase

`/build` — the scaffold is in place and the profile page is verified working. The next session should drive the feature to a working end-to-end state: fix the port config, exercise the remaining endpoints, and get the playlist builder generating and saving playlists.

---

# Reflect — Redesign + Discovery + Full Spotify Account Integration
Date: 2026-06-24
Type: Session (multi-feature)
Phase context: brainstorm → plan → scaffold (run ~5×), plus heavy build/iterate

## Accomplished
- **Visual redesign (R1–R6):** semantic token system + logo-derived blue→purple palette; Inter; dark layered surfaces; every page/component restyled; profile tables → Spotify-style list rows; subtle motion.
- **Discover Similar Songs made usable:** made LLM analysis aspects selectable (not just Last.fm tags), dissolving the tag gate — discovery is always reachable when an LLM is connected.
- **Persistence:** `persisted()` localStorage store helper; `exploreSession` profile cache (keyed, versioned) so returning to a song doesn't re-query Last.fm/LLM.
- **Custom search autocomplete** with album art (replaced native datalist); **cover-art backdrops** on discovery results and the profile card.
- **AI radar + richer analysis:** analysis template returns JSON (5 text fields + 6 0–100 scores + AI tags); custom dependency-free SVG radar; AI tags merged with Last.fm tags.
- **Full Spotify account integration (M0–M4):** global token hydration (app-wide, shared `spotifyAuth.js`); drag-and-drop Playlists panel (existing + new playlist, per-song "+" with two-mode behavior, bulk); Save to Liked Songs (+ saved-state indicators, new scopes); explore-from-top-tracks seeds; wiki summary + play count display.
- **Polish:** panel margins/corners/z-index, gradient selection highlight (replaced checkbox), panel search, top-offset alignment.

## What Worked
- **Brainstorm→plan→scaffold scaled to many sub-features in one session.** Each cycle produced decision-locked plans; no mid-build ambiguity. The workflow compounds, not just on greenfield.
- **Sequencing M0 (global token) first** was correct — every account action depended on the token being available off the Profile page. Naming it a hard prerequisite in the plan prevented a class of "works on Profile, fails on Explore" bugs.
- **Reusing the existing pipeline instead of new endpoints** (discovery reused `/llm/generate-playlist/`; bulk-add reused the panel pending flow). DRY, less surface.
- **Coupling discoverable aspects to the LLM analysis** — an elegant fix: aspects are always present exactly when discovery is possible.
- **Cache-version bump** (`exploreSession_v2`) as the clean structural fix for stale cached profiles after a shape change.

## What Didn't Work
- **Diagnostic round-trips through the user's browser console were the dominant time sink.** Cover art "not showing" (stale persisted selection), `track_count: 0` (Spotify field rename), empty-playlist create bug — each needed the user to paste console output. The persistence layer that's a feature also made "code vs. stale data?" ambiguous.
- **CSS/visual work had no feedback loop.** The radar took 5+ iterations (size → layout → viewBox clipping → whitespace → position); the user was the render loop, paying a round-trip per nudge. (Fix: use `/run`/`/verify` to screenshot rendered output.)
- **Edit whitespace/Unicode mismatches** forced a couple of fallbacks to scripted edits (the `→` arrow + inconsistent tabs in PlaylistResult). Minor but recurring.

## Decisions Reviewed
| Decision | Outcome | Confidence |
|----------|---------|-----------|
| Semantic tokens + compat aliases for redesign | Clean migration, instant theme flip, page-by-page component migration | High |
| Logo-derived palette (kept purple) | Cohesive; gradient as accent reads premium | High |
| Persistent right-side panel over modal picker | Right call — workspace + drag-and-drop; more capable than a modal | High |
| localStorage persistence everywhere | Good UX; but caused the stale-state debugging friction | Medium |
| JSON analysis template (scores+tags+text) | Works; depends on LLM returning clean JSON — fence-stripping + validation in place | Medium |
| Drag-and-drop via native HTML5 DnD | Fine for desktop; no touch support (acceptable, app is min-width 800) | Medium |

## Surprises
- **Spotify `/me/playlists` renamed `tracks` → `items`** (still `{href, total}`). Undocumented; required dumping the raw response to find. Anything assuming the old `tracks` shape silently returns 0.
- **`playlist_add_items` rejects an empty list** → created-but-errored playlists (left empty dupes in the account). Guard with `if track_ids`.
- **Adding scopes requires full re-auth** — M2's Liked Songs silently 403'd until log out/in. The prior reflection had already flagged "add new scopes to frontend OAuth," which proved exactly right.

## Lessons Learned
- For client-persisted state, build a **cache-versioning convention from the start** (bump a key suffix on shape change) — and when a feature "doesn't show," suspect stale persisted state before suspecting code.
- **Use `/run` or `/verify` for CSS-heavy work** so the assistant sees rendered output instead of round-tripping visual nudges through the user.
- Keep a running **"Spotify API gotchas"** note (field renames, empty-add, scope re-auth, PKCE/`127.0.0.1`) — these recur and cost time each rediscovery.
- When an endpoint returns surprising data, **dump the raw upstream response early** rather than reasoning about the expected shape.

## Memory Updates (suggested — not yet written)
- **reference:** "Spotify API gotchas for this project" (tracks→items rename; empty `playlist_add_items` rejection; scope changes need re-auth; PKCE + `127.0.0.1`; preview_url deprecated).
- **feedback:** Prefer `/run`/`/verify` (screenshots) for visual/CSS iteration on this app.
- **project:** update `project_ryans_boomin_beats.md` — app now has full account integration; flag account-integration + AI pipeline as the least-tested areas.

## Next Steps
1. **End-to-end test the account integration** (user-flagged as shaky): many playlists, error/403 paths, re-auth, drag + "+" + bulk + liked indicators across Explore and Builder.
2. **Harden the AI analysis pipeline** (user-flagged): verify JSON parsing across providers (Groq/Claude/OpenAI), malformed-output fallback, missing-scores handling.
3. Clean up the empty test playlists left in Spotify from the create bug.
4. Optional M4 extension: album / release year / similar artists (needs extra calls).
5. Delete dead demo code (`recommendations.svelte`, `Counter.svelte`, `sverdle/`, `account_analysis/`) still referencing removed light-theme tokens.

## Suggested Next Phase
`/verify` (or `/run`) — drive the app for real and confirm the account-integration and AI-analysis paths end-to-end, since those are the least-tested and highest-risk areas. This also establishes the screenshot-based visual loop for any follow-up polish.
