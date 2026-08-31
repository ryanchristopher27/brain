# Plan — LLM Playlist Builder
Date: 2026-06-04
Status: Active
Brainstorm: docs/brainstorm.md

---

## Overview

Add an AI-powered playlist builder to Ryan's Boomin Beats. Users connect their own Claude or OpenAI API key, describe a playlist in natural language, and the app generates a curated song list validated against Spotify's catalog. Results display in-app; users can select songs, save as a Spotify playlist, or queue everything to their active player. Conversation is supported — users can refine the playlist in follow-up prompts.

---

## Goals & Success Criteria

| Goal | Success Criteria |
|------|-----------------|
| LLM connection | User can select Claude or OpenAI, enter their API key, and have it validated |
| Playlist generation | A natural language prompt produces a list of 10–15 songs matched against Spotify |
| Spotify validation | Backend iterates until every song in the returned playlist is confirmed on Spotify |
| In-app display | Results show album art, title, artist, match status, and the LLM's reason for the pick |
| Conversational refinement | Follow-up prompts refine the playlist using prior message history |
| Spotify actions | "Add as Playlist" saves to user's Spotify; "Queue All" adds to active player |

---

## Scope

### In Scope
- LLM provider selection: Claude (Anthropic) and OpenAI
- BYOK API key input, validated on connect, stored in Django session
- New `/playlist-builder` route in SvelteKit
- LLM settings panel as a header toggle (icon button, opens popover/modal — consistent with account/settings UI pattern)
- One-shot and conversational prompting (same code path, chat history tracked in Svelte store)
- Iterative Spotify validation: backend retries with LLM until target count of fully matched songs is met (max 3 retry rounds)
- Song cards: album art, title, artist, LLM reason, select checkbox — all cards in result are confirmed Spotify matches
- Action bar: "Add All as Playlist", "Queue All", "Add Selected as Playlist"
- "Add as Playlist" and "Add Selected as Playlist" require user to enter a playlist name before submitting
- New Spotify OAuth scopes: `playlist-modify-private`, `user-modify-playback-state`
- New Django apps: `llm_connect`, `llm_playlist`, `spotify_actions`

### Out of Scope
- User auth / persistent key storage (future milestone)
- Direction B (LLM tool use / Spotify search inside the LLM loop) — deferred
- Manual song swap UI (not needed — iterative validation ensures all results are matched)
- Sharing or exporting playlists externally
- Seeding LLM with account analysis data (noted as a quick future win, not v1)

---

## Tech Stack & Architecture

**Backend migrated to FastAPI** (full migration from Django — decision made 2026-06-05):

| Layer | Tech | Notes |
|-------|------|-------|
| Frontend | SvelteKit | New route + components; new Svelte stores |
| Backend | FastAPI + Uvicorn | Full replacement of Django; all existing endpoints migrated |
| Sessions | Starlette SessionMiddleware | Same `request.session` dict interface as Django sessions |
| CORS | FastAPI CORSMiddleware | Replaces per-view CORS headers in old Django views |
| Spotify | Spotipy | Unchanged; sync Spotipy calls wrapped in `asyncio.to_thread` where async matters |
| LLM (Claude) | `anthropic` Python SDK | New dependency |
| LLM (OpenAI) | `openai` Python SDK | New dependency |

**Why FastAPI over Django:** Async-first (parallel Spotify validation, LLM calls), Pydantic request/response validation, automatic OpenAPI docs, cleaner CORS handling. The existing Django views were all thin Spotipy wrappers with no real ORM usage — migration cost is low.

**LLM abstraction:** A single `LLMClient` service class in `services/llm_client.py` wraps both SDKs with a common async interface. Provider-agnostic — router logic never imports anthropic or openai directly.

**Session key storage:** Starlette `SessionMiddleware` (cookie-signed). `POST /llm/connect/` stores `{ provider, api_key }` in `request.session`. All downstream endpoints read from session — key never re-sent from frontend.

**Spotify scope upgrade:** `SCOPE` constant in `config.py` gains `playlist-modify-private user-modify-playback-state`. Users who previously authenticated will need to re-auth — Spotipy handles this automatically.

---

## Project Structure

### Backend Structure (FastAPI — replaces Django)

```
src/web/backend/
├── main.py                        # FastAPI app: middleware, router registration
├── config.py                      # Shared constants: CLIENT_ID, SECRET, SCOPE, REDIRECT_URI
├── requirements.txt               # fastapi, uvicorn, spotipy, anthropic, openai, python-multipart
├── routers/
│   ├── __init__.py
│   ├── search.py                  # GET /search/
│   ├── recommendations.py         # GET /get-recommendations/
│   ├── profile.py                 # GET /get-profile/
│   ├── account_analysis.py        # GET /account-analysis/ (stub — WIP)
│   ├── llm_connect.py             # POST /llm/connect/
│   ├── llm_playlist.py            # POST /llm/generate-playlist/
│   └── spotify_actions.py         # POST /spotify/create-playlist/, POST /spotify/queue/
└── services/
    ├── __init__.py
    ├── llm_client.py              # LLMClient: async Claude + OpenAI abstraction
    └── spotify_validator.py       # Parallel Spotify search, two-pass match logic

# Old Django backend left in place at backend_server/ — safe to delete after migration verified
```

Run command: `uvicorn main:app --reload` (from `src/web/backend/`)

### New Frontend Files (SvelteKit)

```
src/web/frontend/src/
├── routes/
│   └── playlist-builder/
│       └── +page.svelte              # Main playlist builder page
├── lib/
│   └── components/
│       ├── LLMSettingsPanel.svelte   # Provider select + API key input (opened via header toggle)
│       ├── ChatInterface.svelte      # Prompt input + scrollable message history
│       ├── PlaylistResult.svelte     # Song list + action bar
│       ├── SongCard.svelte           # Individual song card (all shown are Spotify-confirmed)
│       └── PlaylistNameModal.svelte  # Name input modal shown before saving a playlist
└── stores.js                         # Add: llmConfig, chatMessages, generatedPlaylist
```

### Updated Files

- `src/web/frontend/src/stores.js` — add `llmConfig`, `chatMessages`, `generatedPlaylist`
- `src/web/frontend/src/routes/Header.svelte` — add LLM settings icon to `.header-actions`
- `src/web/frontend/src/lib/index.js` — export 5 new components

---

## Milestones

| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| M1 | LLM Connect | Backend session storage + frontend settings panel | None |
| M2 | Playlist Generation | LLM prompt → structured output → Spotify validation | M1 |
| M3 | Playlist Builder UI | `/playlist-builder` route, chat interface, song cards | M2 |
| M4 | Spotify Actions | Create playlist + queue endpoints + frontend action bar | M3, new OAuth scopes |

---

## Task Breakdown

### M1 — LLM Connect

**Backend:**
- Create `llm_connect` Django app
- `POST /llm/connect/` view: accepts `{ provider, api_key }`, makes a minimal test call to validate the key, stores in session on success, returns `{ connected: true }` or error
- Register app + URL in `urls.py` and `settings.py`

**Frontend:**
- Add `llmConfig` store: `writable({ provider: 'claude', apiKey: '', connected: false })`
- `LLMSettingsPanel.svelte`: provider radio/select + API key input + "Connect" button; on success sets store, persists connected state in `sessionStorage` so page refresh doesn't lose it
- Add settings toggle to `Header.svelte`: a key/gear icon button in the top-right nav area; shows a green dot indicator when `llmConfig.connected` is true; clicking opens `LLMSettingsPanel` as a popover or modal overlay
- Panel is globally accessible from any page via the header, not tied to `/playlist-builder`

---

### M2 — Playlist Generation

**Backend:**
- Create `llm_playlist` Django app
- `llm_client.py`: `LLMClient` class with `generate(messages, system_prompt) -> str`; dispatches to `anthropic.Anthropic` or `openai.OpenAI` based on session provider
- System prompt: instructs LLM to return only a JSON array of `{ title, artist, reason }` objects; no prose, no markdown wrapping; default 12 songs unless user specifies
- `spotify_validator.py`: for each `{ title, artist }`, searches Spotify as `track:{title} artist:{artist}`; if no result, retries without `artist:` filter; returns a Spotify track object or `None`
- `POST /llm/generate-playlist/` view: orchestrates the iterative validation loop (see below), returns only fully matched songs

**Iterative validation loop** (in the view or a helper):
1. Ask LLM for N songs (where N = requested count, default 12)
2. Run `spotify_validator` on all suggestions in parallel
3. Collect matched songs; collect failed `{ title, artist }` pairs
4. If `len(matched) < N` and retry count < 3: ask LLM for `N - len(matched)` replacements, passing the failed pairs so the LLM avoids re-suggesting them
5. Add any new matches to the pool; repeat from step 3
6. After max retries, return however many matched songs were found; include `requested` and `returned` counts in response so the frontend can notify the user if short

**Response shape:**
```json
{
  "requested": 12,
  "returned": 12,
  "playlist": [
    {
      "title": "Song Name",
      "artist": "Artist Name",
      "reason": "Why this fits the prompt",
      "spotify": {
        "id": "...",
        "title": "...",
        "artists": ["..."],
        "album": "...",
        "image": "...",
        "track_url": "...",
        "duration_ms": 0
      }
    }
  ],
  "messages": [...]
}
```

---

### M3 — Playlist Builder UI

- New route `src/routes/playlist-builder/+page.svelte`
- Add `chatMessages` store: `writable([])` — array of `{ role, content }`
- Add `generatedPlaylist` store: `writable([])` — full playlist result objects
- `ChatInterface.svelte`: text input, send button, scrollable message history display; on submit, POST to `/llm/generate-playlist/` with `{ prompt, messages: $chatMessages }`, update stores on response
- `SongCard.svelte`: album art, title, artist, reason tooltip, select checkbox — no match badge needed since all returned songs are Spotify-confirmed; if `returned < requested`, show a notice above the list ("Could only confirm X of Y songs on Spotify")
- `PlaylistResult.svelte`: renders list of `SongCard`s + action bar; "Add Selected as Playlist" enabled only when at least one card is checked
- `PlaylistNameModal.svelte`: modal with a text input for playlist name + "Save" / "Cancel"; triggered by "Add All as Playlist" and "Add Selected as Playlist" buttons; does not submit until name is non-empty
- Add "Playlist Builder" link to `Header.svelte`

**Page layout:**
```
[ Header — with LLM settings toggle icon (top-right) ]
[ ChatInterface — prompt input + message thread ]
[ PlaylistResult — song cards grid/list ]
[ Action Bar — Add All as Playlist | Queue All | Add Selected as Playlist ]
[ PlaylistNameModal — appears on top when saving ]
```

---

### M4 — Spotify Actions

**OAuth:**
- Append `playlist-modify-private user-modify-playback-state` to `SCOPE` across all backend views (or extract to a shared constant)

**Backend:**
- Create `spotify_actions` Django app
- `POST /spotify/create-playlist/` view: accepts `{ name, track_ids[] }`, creates playlist on user's Spotify account via Spotipy, adds tracks, returns playlist URL
- `POST /spotify/queue/` view: accepts `{ track_ids[] }`, adds each to active playback queue; handles "no active device" with a clear error message
- Register app + URLs

**Frontend:**
- Wire "Add All as Playlist": opens `PlaylistNameModal`; on name submit, calls `/spotify/create-playlist/` with all track IDs; shows success state with link to playlist
- Wire "Add Selected as Playlist": opens `PlaylistNameModal`; on name submit, calls `/spotify/create-playlist/` with only checked track IDs; button disabled if no cards checked
- Wire "Queue All": calls `/spotify/queue/` with all track IDs; handles "no active device" error with user-facing message ("Open Spotify on a device first")

---

## API Shapes

### POST /llm/connect/
```
Request:  { provider: "claude" | "openai", api_key: string }
Response: { connected: true } | { error: string }
```

### POST /llm/generate-playlist/
```
Request:  { prompt: string, messages: [{ role, content }] }
Response: { playlist: PlaylistItem[], messages: Message[] }
Session:  provider + api_key read from session
```

### POST /spotify/create-playlist/
```
Request:  { name: string, track_ids: string[] }
Response: { playlist_url: string, playlist_id: string }
```

### POST /spotify/queue/
```
Request:  { track_ids: string[] }
Response: { queued: number } | { error: "no_active_device" }
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LLM returns malformed JSON | Medium | High — breaks parsing | Wrap parse in try/except; retry once with stricter prompt; return error to user |
| Spotify search misses (hallucinated songs) | High | Low — handled by retry loop | Two-pass search per song + up to 3 LLM retry rounds; LLM told which songs failed; if still short after retries, notify user |
| New OAuth scopes require user re-auth | Certain | Low — expected behavior | Document clearly; Spotipy will redirect automatically when scopes change |
| Queue fails — no active Spotify device | Medium | Low | Return `error: "no_active_device"` with user-facing message: "Open Spotify on a device first" |
| API key stored in session leaks | Low | High | HTTPS in production; session is server-side; key never logged |
| Slow response (LLM + 12 Spotify searches) | Medium | Medium | Parallel Spotify searches; loading state in UI; target <5s total |

---

## Dependencies

**New Python packages:**
```
pip install fastapi uvicorn python-multipart itsdangerous spotipy anthropic openai
```
(`itsdangerous` is required by Starlette's SessionMiddleware; `python-multipart` for form data support)

**Spotify OAuth scope additions (breaking for existing sessions):**
```
playlist-modify-private user-modify-playback-state
```

**Django sessions:** Must be enabled in `settings.py` (`django.contrib.sessions` in `INSTALLED_APPS`, session middleware active). Check existing config — likely already present but unused.

---

## Open Questions

1. ~~Should `LLMSettingsPanel` be accessible from the `Header` (global) or only from the `/playlist-builder` page?~~ **Resolved: header toggle, globally accessible.**
2. ~~How should "Add Selected" work if the user has only selected matched songs vs. a mix?~~ **Resolved: all returned songs are matched (iterative validation); "Add Selected" disabled until at least one card checked.**
3. Should the conversation reset when the user navigates away from `/playlist-builder`? Stores are in-memory so yes by default — acceptable for v1.
4. ~~Default playlist name when saving to Spotify?~~ **Resolved: user must enter a name; no auto-generated default.**

---

## Decisions Log

| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Backend framework | FastAPI (full migration from Django) | Async-first, Pydantic validation, cleaner CORS; Django views were all thin Spotipy wrappers with no ORM — low migration cost | 2026-06-05 |
| Pipeline approach | Direction A: LLM output + Spotify validation | Speed, simplicity; Direction B deferred as upgrade | 2026-06-04 |
| LLM providers | Claude + OpenAI | BYOK; two most common developer accounts | 2026-06-04 |
| Key storage | Django session | No auth system needed in v1; persistence deferred | 2026-06-04 |
| Conversation | One-shot + chat, same code path | Message history is a trivial addition; not worth splitting releases | 2026-06-04 |
| Song default count | 12 | Enough to feel like a real playlist; user can specify differently in prompt | 2026-06-04 |
| Spotify search retry | Two-pass per song + up to 3 LLM retry rounds | Iterative: LLM told which songs failed and asked for replacements; guarantees all returned songs are on Spotify | 2026-06-04 |
| UI placement | Dedicated `/playlist-builder` route | Clean separation; feature is substantial enough to own a page | 2026-06-04 |
| LLM settings panel placement | Header icon toggle (global) | Consistent with account/settings UI patterns; green dot indicator shows connection status | 2026-06-04 |
| Unmatched song handling | Not surfaced to user — backend iterates until all valid | Cleaner UX; user never sees a song that can't be played | 2026-06-04 |
| Playlist name on save | Required user input via modal | No auto-generated names; user intentionally names their playlist before it's created on Spotify | 2026-06-04 |

---

---

# Plan — Song Exploration & Discovery (Pillar 1)
Date: 2026-06-05
Status: Active
Brainstorm: docs/brainstorm.md (section: "Song Exploration & Discovery")

---

## Overview

The explore feature replaces the home page entirely and lives at the root route (`/`). Users search for a specific song via Spotify autocomplete, view a rich profile of that song (Last.fm tags + LLM qualitative analysis), select the aspects they care about, and discover similar songs. Clicking a song in discovery results loads that song's profile on the same page — enabling a natural exploration chain. Discovery output reuses the existing Pillar 2 pipeline (iterative LLM generation + Spotify validation + `PlaylistResult` display). No free-text prompt input on this page — that belongs to the playlist builder.

Nav structure: **Explore | Playlist Builder | Profile**

---

## Goals & Success Criteria

| Goal | Success Criteria |
|------|-----------------|
| Song search | Spotify autocomplete surfaces matching tracks by title |
| Song profile | Page shows Last.fm tags and LLM prose analysis for the selected song |
| Tag selection | User can toggle individual tags on/off to define discovery intent |
| Discovery | "Discover" generates a validated Spotify playlist based on selected tags + song context |
| Actions | User can save discovery results as a playlist or queue them — same as Pillar 2 |

---

## Scope

### In Scope
- Explore page replaces the home page at root route `/` (old `routes/+page.svelte` replaced)
- Two-state page: idle (search bar only) → exploring (song profile + discovery results below)
- Clicking a song in discovery results loads that song's profile on the same page (exploration chain)
- `GET /song/profile/` endpoint — fetches Last.fm data and LLM analysis in parallel
- `services/lastfm_client.py` — Last.fm API wrapper
- `LASTFM_API_KEY` added to `.env`, `.env.example`, and `config.py`
- `SongSearch.svelte` — Spotify autocomplete component (extracted from old home page logic)
- `SongProfile.svelte` — tag pills + LLM prose + Discover button
- `TagPill.svelte` — selectable/toggleable pill
- LLM analysis always shown — structured template fills in when Last.fm data is sparse
- Discovery reuses existing `/llm/generate-playlist/` endpoint with richer context
- Discovery results rendered by existing `PlaylistResult.svelte` + `SongCard.svelte`
- Header nav updated: Home removed, Explore at `/` is the new primary nav item
- `setup.md` updated with Last.fm API key instructions

### Out of Scope
- Free text prompt input on the explore page (belongs to playlist builder)
- Radar chart visualization (deferred to a future visual pass)
- Last.fm similar tracks as a direct discovery source (LLM drives discovery, Last.fm provides context)
- Obscure song handling beyond graceful degradation (LLM fills in with what it knows)

---

## Tech Stack & Architecture

No new tech. Adds Last.fm as a data source alongside existing stack.

| Layer | Addition |
|-------|---------|
| Backend | `routers/song_profile.py`, `services/lastfm_client.py` |
| External API | Last.fm (free, API key only, no OAuth) |
| Frontend | 3 new components, root route replaced |
| Discovery pipeline | Reuses `/llm/generate-playlist/` — no new backend needed |

**Key architectural decision: single `/song/profile/` call does both Last.fm and LLM.**
Last.fm fetch and LLM analysis run in parallel (`asyncio.gather`). Frontend makes one request and gets a complete profile back — no waterfall, no second round-trip.

**Discovery via existing endpoint:**
The explore page calls `/llm/generate-playlist/` with a crafted prompt that includes the song title, artist, LLM analysis, and selected tags. The endpoint is unmodified — richer context flows through the existing `prompt` field.

---

## Project Structure

### New Backend Files

```
src/web/backend/
├── routers/
│   └── song_profile.py          # GET /song/profile/
└── services/
    └── lastfm_client.py         # Last.fm track.getInfo wrapper
```

### Replaced Frontend Files

```
src/web/frontend/src/
└── routes/
    └── +page.svelte             # Replaced: was home page, now explore page
```

### New Frontend Components

```
src/web/frontend/src/lib/components/
    ├── SongSearch.svelte         # Spotify autocomplete (extracted from old home page)
    ├── SongProfile.svelte        # Tag pills + LLM prose + Discover button
    └── TagPill.svelte            # Selectable tag pill
```

### Updated Files

- `config.py` — add `LASTFM_API_KEY`
- `.env` + `.env.example` — add `LASTFM_API_KEY`
- `main.py` — register `song_profile` router
- `lib/index.js` — export 3 new components
- `Header.svelte` — replace "Home" nav entry with "Explore" (same href `/`, new label)
- `docs/setup.md` — Last.fm API key instructions

---

## Milestones

| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| E1 | Last.fm + Profile Endpoint | `lastfm_client.py`, `song_profile.py`, config wired | None |
| E2 | Explore Page + Song Profile UI | Route, `SongSearch`, `SongProfile`, `TagPill` | E1 |
| E3 | Discovery | Wire tag selection → `/llm/generate-playlist/` → `PlaylistResult` | E2, LLM connected |

---

## API Shapes

### GET /song/profile/
```
Request:  ?title=Bohemian+Rhapsody&artist=Queen
Response: {
  "title": "Bohemian Rhapsody",
  "artist": "Queen",
  "tags": [
    { "name": "classic rock", "url": "..." },
    { "name": "epic", "url": "..." }
  ],
  "listeners": 4200000,
  "play_count": 18000000,
  "wiki_summary": "...",      // may be empty string for obscure tracks
  "analysis": "..."           // LLM prose, 2-3 sentences
}
```

**LLM system prompt for song analysis:**
> You are a music expert. Given a song title, artist, and any available listener tags, write a structured analysis covering: Mood, Instrumentation, Lyrical Themes, Era, and Cultural Context. Each field should be 1-2 sentences. If tags are provided, ground your analysis in them. If tags are absent or sparse, use your own knowledge. Return each field as a labeled line (e.g. "Mood: ..."), nothing else.

**Discovery prompt construction (frontend → `/llm/generate-playlist/`):**
```
Using "[title]" by [artist] as a reference point, find 12 songs that share these qualities: [selected tag 1], [selected tag 2], [selected tag 3]. The reference song is: [LLM analysis]. Return songs that genuinely match these specific characteristics.
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Last.fm no match for song | Medium | Low | Return empty tags gracefully; LLM analysis still runs using just title + artist |
| Sparse tags for obscure tracks | High | Low | Show whatever tags exist; if fewer than 3, LLM prompt notes limited data |
| Last.fm API key missing | Low | High | FastAPI startup check; clear error message pointing to setup.md |
| LLM analysis slow (blocks profile load) | Low | Medium | Run Last.fm + LLM in parallel; Last.fm is fast so total latency is ~LLM latency only |
| Discovery results don't match selected tags | Medium | Low | Known LLM limitation; user can re-run or adjust selection |

---

## Dependencies

**New environment variable:**
```
LASTFM_API_KEY=your-lastfm-api-key
```
Get one at: https://www.last.fm/api/account/create (free, instant)

**No new Python packages** — Last.fm API is a simple REST call; use `httpx` (already available via FastAPI's ecosystem) or `urllib` directly.

---

## Open Questions

~~1. Should `SongSearch.svelte` also replace the search on the home page?~~ **Resolved: explore page IS the home page at `/`.**
~~2. Sparse Last.fm data — show LLM analysis or notice?~~ **Resolved: always show LLM analysis using structured template.**
~~3. Clicking discovery results — navigate or stay on page?~~ **Resolved: loads new song profile on same page (exploration chain).**

---

## Decisions Log

| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Discovery data source | Last.fm tags + LLM interpretation | Spotify audio features deprecated; Last.fm is free, stable, and tag-based data maps to how users actually think about music | 2026-06-05 |
| Song profile endpoint | Single endpoint, parallel Last.fm + LLM calls | Avoids frontend waterfall; one request, complete response | 2026-06-05 |
| Discovery pipeline | Reuse `/llm/generate-playlist/` | No new backend needed; richer prompt context is the only difference | 2026-06-05 |
| Visualization | Tag pills only, radar chart deferred | Tag data is categorical not numeric; pills are honest to the data; radar revisited when numeric data available | 2026-06-05 |
| Free text on explore page | Out of scope | Belongs to playlist builder (Pillar 2); explore page is song-centric only | 2026-06-05 |
| Home page | Replaced by explore page at `/` | Old home page had no purpose after recommendations deprecated; explore is the primary surface | 2026-06-05 |
| Nav structure | Explore \| Playlist Builder \| Profile | Home removed; Explore at root is the app's primary entry point | 2026-06-05 |
| Discovery result click | Load new song profile on same page | Creates natural exploration chain; no navigation away from the page | 2026-06-05 |
| LLM analysis when data sparse | Structured template always shown | LLM fills in Mood/Instrumentation/Era/Themes/Context from its own knowledge; consistent format regardless of Last.fm data quality | 2026-06-05 |

---

# Plan — Frontend Redesign: Sleek Dark Theme
Date: 2026-06-22
Status: Draft
Brainstorm: docs/brainstorm.md (Frontend Redesign — Sleek Dark Theme, 2026-06-22)

## Overview
A full visual redesign of the SvelteKit frontend to a sleek, dark, layered theme — Spotify's design language as reference, not a pixel-perfect clone. Keep the existing `#5ec9ff` light blue as the single accent. The app's structure and functionality are unchanged; this is purely a styling/typography/polish pass across every page and component, plus a foundational token system to make it cohesive and maintainable.

## Goals & Success Criteria
- **Cohesive dark theme** — layered surfaces (`#0a0a0a` → `#181818` → `#282828`) across the whole app
- **Monochrome accent discipline** — blue only for active states, primary actions, and links; everything else grayscale
- **Typography upgrade** — Inter replaces Arial; consistent type scale
- **Subtle motion** — smooth hover transitions, gentle load fades
- **Quality parity** — every page meets the same bar; profile page no longer lags
- **Success = the consistency checklist passes** (see Acceptance Criteria): one radius scale, one spacing rhythm, one type scale, consistent hover behavior, zero purple, zero light-theme remnants

## Scope
### In Scope
- Global token system (semantic tokens + Inter font)
- Shell: `+layout.svelte`, `Header.svelte`, `styles.css`
- Explore page (`+page.svelte`) + SongSearch, SongProfile, TagPill
- Playlist Builder (`playlist-builder/+page.svelte`) + ChatInterface, PlaylistResult, SongCard, PlaylistNameModal
- Profile page (`profile/+page.svelte`) — restyle (structural changes only if needed for parity)
- LLMSettingsPanel popover
- Removal of purple hover color across all 9 files
- Removal/repurposing of legacy light-theme tokens in `styles.css`

### Out of Scope
- Backend changes (none required)
- New features or layout restructure (no sidebar — top nav stays)
- Responsive/mobile work beyond existing `min-width: 800px`
- Dead-code deletion of unused legacy components (Counter, Radar*, recommendations, sverdle, account_analysis) — noted as a separate cleanup, not part of this redesign

## Tech Stack & Architecture
- **No new stack** — SvelteKit, scoped `<style>` blocks per component, CSS custom properties in `styles.css :root`
- **Font:** add `@fontsource/inter` (matches existing `@fontsource/fira-mono` pattern; no licensing concerns, unlike Spotify's Circular). DM Sans was the alternative — Inter chosen for its proven UI legibility and tighter metrics.
- **Token strategy (the foundation):** introduce **semantic tokens** in `:root`, and alias the existing raw color names to them so components keep working during migration:
  ```
  --surface-0: #0a0a0a;   /* page background */
  --surface-1: #181818;   /* cards */
  --surface-2: #282828;   /* hover / raised */
  --text-primary: #ffffff;
  --text-muted: rgba(255,255,255,0.65);
  --text-subtle: rgba(255,255,255,0.4);
  --accent: #5ec9ff;
  --accent-hover: #8ad8ff;   /* replaces purple hovers */
  --border-subtle: rgba(255,255,255,0.08);
  --radius: 12px;

  /* backward-compat aliases — let old components render correctly mid-migration */
  --color-dark-gray: var(--surface-1);
  --color-light-blue: var(--accent);
  --color-purple: var(--accent-hover);   /* neutralizes purple immediately */
  ```
  Reasoning: aliasing `--color-purple` to `--accent-hover` instantly removes purple app-wide in one line, even before each component is individually migrated. Components then migrate from raw names → semantic names page by page without breakage.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| R1 | Design system foundation | Semantic tokens, Inter font, surface/elevation scale, compat aliases, base element styles in `styles.css` + `+layout.svelte` dark background | — |
| R2 | Shell | Redesign `Header.svelte` (slim, clean active state) and layout chrome | R1 |
| R3 | Explore page | `+page.svelte` + SongSearch, SongProfile, TagPill | R1, R2 |
| R4 | Playlist Builder | `playlist-builder/+page.svelte` + ChatInterface, PlaylistResult, SongCard, PlaylistNameModal | R1, R2 |
| R5 | Profile page | Restyle `profile/+page.svelte` to parity (the roughest page) | R1, R2 |
| R6 | Polish & cleanup | Migrate remaining raw tokens → semantic, remove compat aliases + legacy light-theme tokens, motion pass, consistency audit | R2–R5 |

## Task Breakdown

### R1 — Design system foundation
- Install `@fontsource/inter`; import in `styles.css`; set `--font-body` to Inter
- Replace `:root` token block with semantic tokens + compat aliases (above)
- Set page background to `--surface-0` in `+layout.svelte` (remove the light-blue `.app`/`main` backgrounds and the light radial-gradient body background in `styles.css`)
- Define base styles: link color → `--accent`, type scale (h1/h2/body), default border + radius vars
- Verify app still renders (compat aliases should keep every component working, now dark + purple-free)

### R2 — Shell
- `Header.svelte`: slim height, refined nav buttons, cleaner active state (filled accent vs. ghost), settings gear + connected dot restyle, popover container
- Confirm fixed-header spacing still works with new page background

### R3 — Explore page
- `+page.svelte`: idle "What are you in the mood for?" state + compact searching state, discovery header, status/error notices
- `SongSearch`: searchbar on `--surface-1`, accent focus ring
- `SongProfile`: card on `--surface-1`, section labels, analysis fields, discover button (primary accent), loading state
- `TagPill`: selected = filled accent; idle = subtle outline; hover = `--accent-hover` (no purple)

### R4 — Playlist Builder
- `ChatInterface`: messages, settings bar (Songs count input), prompt textarea, send button
- `PlaylistResult`: result container, action bar (primary/secondary/clear-destructive buttons), notices
- `SongCard`: album art, title/artist, reason tooltip, explore button, checkbox accent
- `PlaylistNameModal`: dark modal surface, inputs, buttons

### R5 — Profile page
- Login button state, profile header card, top-artists / top-tracks tables, parameter selectors (count + time period), logout button
- Bring spacing/typography/hover to parity; restructure only if tables look off on dark

### R6 — Polish & cleanup
- Migrate all components from raw color names → semantic tokens
- Remove compat aliases and legacy light-theme tokens (`--color-bg-0/1/2`, `--color-theme-1/2`, light gradient)
- Subtle motion pass: hover transitions (150ms), gentle fade-in on results/profile load
- Consistency audit against acceptance criteria

## Acceptance Criteria (the "sleek" checklist)
- [ ] One radius scale (`--radius`, optionally `--radius-sm/lg`) used everywhere
- [ ] One spacing rhythm (consistent multiples)
- [ ] One type scale; Inter applied globally; no Arial
- [ ] Layered surfaces consistent (page/card/hover)
- [ ] Accent used only for active states, primary actions, links
- [ ] Zero purple remaining
- [ ] Zero light-theme remnants (no light backgrounds/gradients)
- [ ] Hover states consistent across all interactive elements
- [ ] Profile page visually on par with Explore

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Component-by-component migration leaves inconsistent intermediate states | Med | Low | Compat aliases keep everything coherent (dark + purple-free) from R1 onward; migration is cosmetic refinement, not breakage |
| Profile tables look broken on dark backgrounds | Med | Med | R5 allows structural tweaks if restyle alone isn't enough |
| Removing light-theme tokens breaks an unaudited legacy component (Radar, sverdle) | Low | Low | Those are out-of-scope/unused; verify they're not routed before removing tokens, else leave a token stub |
| Accent-only discipline makes UI feel flat/monotonous | Low | Med | Use surface elevation + `--accent-hover` brightening for depth instead of extra colors |

## Dependencies
- `@fontsource/inter` (new npm dep)
- No backend or API changes

## Open Questions
- Keep `--accent-hover` as a brighter blue (`#8ad8ff`), or make hovers purely surface-elevation based (no color shift)? (Lean: brighter blue for interactive affordance.)
- Should the profile data tables become card/list rows (more Spotify-like) or stay tabular? Resolve in R5 once seen on dark.
- Remove unused legacy components now or defer? (Defer — separate cleanup task.)

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Visual direction | Dark, top-nav, full component pass (Direction C) | Lands "sleek" without structural rewrite; sidebar overkill for 3 pages | 2026-06-22 |
| Accent intensity | Minimal / monochrome | Restraint reads as premium; blue is the brand anchor | 2026-06-22 |
| Scope | Everything (tokens + all pages + all components) | One cohesive pass avoids mismatched intermediate look | 2026-06-22 |
| Motion | Subtle | Tasteful polish without distraction | 2026-06-22 |
| Font | Inter via @fontsource | Free, proven UI legibility; matches existing fontsource pattern | 2026-06-22 |
| Token system | Semantic tokens + backward-compat aliases | Foundation for cohesion; aliases enable safe page-by-page migration and instant purple removal | 2026-06-22 |
| Purple hover color | Remove (alias to --accent-hover) | Directly follows from monochrome decision; purple spans 9 files | 2026-06-22 |

### Revision 1 — Logo-derived palette + profile list rows (2026-06-22)

**Two decisions from the initial draft are overridden (intentional, user-directed):**

1. **Accent intensity: monochrome → logo-derived brand palette.** The Boomin Beats logo is a blue→purple gradient cube on a `#242424` plate. The app's two existing tokens (`#5ec9ff`, `#a235ff`) *are* the logo colors, so purple is **kept and promoted** to a full palette member rather than removed. Adds a periwinkle mid-tone and a brand gradient.

2. **Profile tables: tabular → Spotify-like list rows.** Resolves the R5 open question. Top Artists / Top Tracks become hoverable list rows (rank · art · name · meta) instead of HTML tables.

**Revised token system** (replaces the monochrome block in Tech Stack & Architecture):
```
--surface-0: #121212;   /* page background (darker than logo plate) */
--surface-1: #242424;   /* cards — matches logo plate, header blends in */
--surface-2: #2e2e2e;   /* hover / raised */
--text-primary: #ffffff;
--text-muted: rgba(255,255,255,0.65);
--text-subtle: rgba(255,255,255,0.4);
--accent:     #5ec9ff;   /* logo blue — primary accent, links, active */
--accent-mid: #7b7ff0;   /* logo gradient midpoint (periwinkle) */
--accent-2:   #a235ff;   /* logo purple — secondary accent */
--brand-gradient: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
--accent-hover: #8ad8ff; /* brightened blue for hover affordance */
--border-subtle: rgba(255,255,255,0.08);
--radius: 12px;

/* backward-compat aliases */
--color-dark-gray:  var(--surface-1);
--color-light-blue: var(--accent);
--color-purple:     var(--accent-2);   /* purple retained, no longer neutralized */
```

**Where the gradient/purple are used (deliberate, still restrained):**
- `--brand-gradient`: primary buttons (Discover, Connect, Send), active nav state, key headings/section accents
- `--accent-2` (purple): secondary hover/active accents, selected-state variety, focus rings on alternating elements
- `--accent` (blue): default accent, links, most active states, icons
- Restraint still applies — gradient is a highlight element, not a background wash

**Impact on milestones:**
- R1: token block above (not the monochrome version); add gradient + periwinkle
- R5: rebuild profile tables as list-row components (structural change, now confirmed)
- R6: do **not** remove purple; remove only legacy *light-theme* tokens (`--color-bg-0/1/2`, `--color-theme-1/2`, light gradient)

**Decisions Log additions:**
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Accent intensity (override) | Logo-derived blue→purple palette + gradient | Logo colors == existing brand tokens; cohesive, distinctive; purple kept | 2026-06-22 |
| Purple (override) | Keep & promote to palette member | Reverses earlier removal; it's a core logo hue | 2026-06-22 |
| Page vs card surface | Page #121212, cards #242424 (logo plate) | Header/logo blend seamlessly; Spotify-like elevation | 2026-06-22 |
| Profile tables | Spotify-like list rows | Resolves R5 open question; more modern, on-brand | 2026-06-22 |

**Revision 1 — confirmations (2026-06-22):**
- Eyeballed hexes accepted as-is (periwinkle `#7b7ff0`, page `#121212`, etc.) — tune live during R1 if needed
- Gradient usage: **recommended scope confirmed** — primary buttons (Discover, Connect, Send), active nav state, and select heading/section accents. Status: planning complete, ready for /scaffold (R1).

---

# Plan — Discover Similar Songs (make it work)
Date: 2026-06-22
Status: Draft
Brainstorm: inline (grounded from code trace + clarifying Qs)

## Overview
The "Discover Similar Songs" flow on the Explore page is wired end-to-end (SongProfile → `onDiscover` → `/llm/generate-playlist/` → Spotify validation → results → explore-chain), but it's effectively unusable: the Discover button is gated on selecting at least one tag, and tags come *only* from Last.fm. Songs Last.fm doesn't tag (or any setup without a Last.fm key) produce zero pills, so the button stays permanently disabled. This plan makes discovery usable by also making the LLM analysis aspects selectable.

## Goals & Success Criteria
- **Discovery is reachable for any song**, not just well-tagged Last.fm songs
- Users can select from **LLM analysis aspects (Mood, Instrumentation, Lyrical Themes, Era, Cultural Context)** in addition to Last.fm tags
- Selected aspects meaningfully shape the discovery results (the LLM receives the aspect *values*, not just labels)
- The explore-chain still works (clicking a result loads its profile)
- **Success = with an LLM connected, you can always select aspects and get a validated similar-songs list, even with no Last.fm tags**

## Scope
### In Scope
- Make LLM analysis fields selectable in `SongProfile.svelte`
- Merge tag selections + aspect selections into one selection model
- Enable the Discover button when *anything* is selected
- Build a richer discovery prompt (tags + aspect label:value pairs) in `+page.svelte`
- Empty/disabled-state copy so it's clear what to do

### Out of Scope
- A dedicated backend discovery endpoint (reuse `/llm/generate-playlist/` — it already does the LLM + Spotify-validate loop)
- Changing the validation/retry engine
- Discovery without an LLM (the endpoint requires one by design)
- Tuning the analysis prompt itself (separate concern)

## Tech Stack & Architecture
- **No backend changes.** Reuse `POST /llm/generate-playlist/` — it already takes a free-form `prompt` + `count` and returns validated, deduped songs. The only change is *how the prompt is built* on the frontend.
- **Key design decision — couple discoverable aspects to the LLM analysis.** Discovery needs an LLM (endpoint 401s otherwise); whenever an LLM is connected, `song_profile` returns the 5 analysis fields. So aspect selection is always available exactly when discovery is possible. This dissolves the Last.fm-tag gate without adding a fallback path.
- **Selection model:** `SongProfile` tracks two sets — `selectedTags` (existing) and `selectedAspects` (new, keyed by analysis label). At discover time it emits a structured payload `{ tags: string[], aspects: {label,value}[] }` via `onDiscover`, instead of today's flat tag-name array.
- **Prompt construction** moves to a small richer builder in `+page.svelte onDiscover`: reference song + bulleted aspect `label: value` lines + tag list + an instruction to exclude the reference track.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| D1 | Selectable analysis aspects | Make the 5 analysis fields toggle-able in SongProfile; add `selectedAspects`; enable Discover when tags **or** aspects selected | — |
| D2 | Richer discovery prompt | Change `onDiscover` payload to `{tags, aspects}`; build prompt from both; exclude reference song | D1 |
| D3 | Polish & states (optional) | Clearer disabled/empty copy ("Select tags or aspects above"); selected-count reflects both; verify explore-chain | D1, D2 |

## Task Breakdown

### D1 — Selectable analysis aspects (SongProfile.svelte)
- Add `selectedAspects = new Set()` keyed by field label
- Render each parsed analysis field as a toggle (clickable row / pill) with a selected visual state (accent border/fill, matching TagPill language)
- `toggleAspect(label)` add/remove from set
- Discover button `disabled` = `selectedTags.size === 0 && selectedAspects.size === 0`
- Button label count reflects tags + aspects combined

### D2 — Richer discovery prompt (SongProfile + +page.svelte)
- Change `onDiscover` to emit `{ tags: Array.from(selectedTags), aspects: parsedFields.filter(f => selectedAspects.has(f.label)) }`
- In `+page.svelte onDiscover({tags, aspects})`:
  - Build aspect lines: `aspects.map(a => `- ${a.label}: ${a.value}`).join('\n')`
  - Build tag line: `tags.length ? `Shared tags: ${tags.join(', ')}` : ''`
  - Prompt: reference song + "find N songs that share these qualities:" + aspect lines + tag line + "Do not include the reference song itself."
  - Keep `count` (12) and the existing 401 handling

### D3 — Polish (optional)
- Disabled-state helper text under the button
- Ensure `onExploreSong` resets both selection sets (already resets profile on new song)
- Manual pass: song with tags, song without tags, explore-chain hop

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM connected but analysis generation failed (no fields, no tags) → still disabled | Low | Low | Rare; if it happens the disabled copy tells the user to pick something. Could later add a "discover from whole song" fallback button |
| Aspect values are long → bloated prompt | Low | Low | Values are 1–2 sentences by the analysis prompt's own constraint; fine for a single request |
| Results include the reference song | Med | Low | Explicit "exclude the reference song" instruction; validator already dedupes by Spotify id |
| Selected aspects don't visibly change results | Low | Med | Pass aspect *values* (not just labels) so the LLM has concrete signal |

## Dependencies
- An LLM connected (Groq/Claude/OpenAI) — already required for discovery
- Existing `/llm/generate-playlist/`, `validate_songs`, `song_profile` — unchanged

## Open Questions
- Should discovery be allowed with **nothing** selected (pure "find similar to this song")? Current plan keeps selection required, now satisfiable via aspects. Easy to relax later.
- Should Last.fm tags and analysis aspects be visually merged into one "Select aspects" section, or stay as two labeled groups? (Lean: two groups — tags are descriptors, aspects are richer analysis.)

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Backend changes | None — reuse generate-playlist | Endpoint already does LLM + validate + dedupe; DRY | 2026-06-22 |
| Root fix | Make LLM analysis aspects selectable | Removes the Last.fm-tag gate; aspects always present when discovery is possible | 2026-06-22 |
| Prompt location | Frontend (onDiscover) | Minimal change; consistent with current design | 2026-06-22 |
| Pass labels or values | Aspect label + value | Gives the LLM concrete similarity signal | 2026-06-22 |

---

# Plan — Cover Art on Playlist Results
Date: 2026-06-23
Status: Draft
Brainstorm: docs/brainstorm.md (Cover Art on Playlist Results, 2026-06-23)

## Overview
Add the selected song's album cover as an immersive visual on the Explore discovery results: a heavily-blurred, low-opacity backdrop that bleeds from the top of the results container and fades into the surface, with a dark scrim for readability, plus a crisp cover thumbnail + "Based on *Song* by Artist" header. Built so `PlaylistResult` takes an optional cover, letting the Playlist Builder adopt it later. Purely presentational — no functional changes to discovery/validation.

## Goals & Success Criteria
- Discovery results show the selected song's cover as a tasteful blurred backdrop + crisp "Based on" header
- Cohesive with the dark theme; readable on any cover (bright/busy/dark)
- `PlaylistResult` gains an **optional** cover API so Explore opts in and the Builder can later
- **Success = with a song selected, discovery results render the blurred backdrop + "Based on" header; readable on a bright cover; graceful no-backdrop fallback when no image; no layout shift**

## Scope
### In Scope
- Thread the selected song's `image` through the selection paths so `$selectedSong.image` is reliable
- Optional cover props on `PlaylistResult` (`coverImage`, `coverTitle`, `coverSubtitle`)
- Blurred backdrop + scrim + gradient-mask fade inside `.result-container`
- Crisp thumbnail "Based on …" header
- Wire Explore page to pass the selected song's cover/labels

### Out of Scope
- Playlist Builder adoption (deferred; structure for it but don't wire — no reference song, would use first-song cover)
- Dominant-color extraction / color-adaptive tint (v1 uses neutral dark scrim)
- 2×2 mosaic covers
- Per-row art treatment changes (SongCard rows already show thumbnails)

## Tech Stack & Architecture
- **Pure frontend, no backend changes.** `search.py` already returns `image`; `song.spotify.image` exists on result rows.
- **Enabling change — thread the cover through selection:** today `onSongSelect` (search path) carries `image`, but the Explore→ chain drops it: `SongCard`'s explore button emits `{title, artists, id}` and `onExploreSong` rebuilds the same. Fix: include `image: song.spotify.image` in the explore payload and preserve it in `onExploreSong`. `$selectedSong` is already a persisted store, so the cover persists across nav/reload for free.
- **`PlaylistResult` optional cover API:** new props `coverImage` (string), `coverTitle`, `coverSubtitle`. When `coverImage` is set, render the backdrop layer + "Based on" header; when absent, render exactly as today (Builder unaffected until wired).
- **Layering inside `.result-container`** (already `position: relative`-able): an absolutely-positioned blurred `<img>` (or background div) at low opacity, `filter: blur(40px)`, masked with a `linear-gradient` so it fades downward, under a dark scrim, with content above via `z-index`. Container gets `overflow: hidden` and keeps its border-radius.
- **Readability:** scrim is a semi-opaque `--surface-1`/black gradient over the blur, independent of cover brightness — no per-image logic needed.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| C1 | Thread cover through selection | Carry `image` in explore-chain payload + `onExploreSong`; confirm search path; `$selectedSong.image` reliable | — |
| C2 | Cover backdrop in PlaylistResult | Optional cover props; blurred backdrop + scrim + mask; crisp "Based on" header; no-image fallback | C1 |
| C3 | Wire Explore results | Pass `coverImage`/title/subtitle from `$selectedSong`; reconcile with existing "Similar Songs" header | C1, C2 |

## Task Breakdown

### C1 — Thread cover through selection
- `SongCard.svelte`: explore button payload → add `image: song.spotify.image`
- `+page.svelte onExploreSong`: include `image: song.image` when setting `$selectedSong`
- Verify `onSongSelect` (search) already carries `image` (it does post-`search.py` change)
- No change needed to persistence — `$selectedSong` already persisted

### C2 — Cover backdrop in PlaylistResult
- Add props: `export let coverImage = null; export let coverTitle = ''; export let coverSubtitle = '';`
- `.result-container`: `position: relative; overflow: hidden`
- Backdrop layer (only `{#if coverImage}`): absolutely-positioned blurred image, low opacity, `mask-image`/gradient fade top→down, dark scrim overlay
- Header layer (only `{#if coverImage}`): crisp thumbnail + `coverTitle` / `coverSubtitle` ("Based on …"), above the song list, `z-index` over backdrop
- Ensure song list + action bar sit above the backdrop (`position: relative; z-index`)
- Fallback: `coverImage` null → no backdrop/header, current layout intact

### C3 — Wire Explore results
- `+page.svelte`: pass `coverImage={$selectedSong.image}`, `coverTitle="Based on {$selectedSong.title}"`, `coverSubtitle={artist}` to `PlaylistResult`
- Decide the existing "Similar Songs" `discovery-header`: replace with the in-card "Based on" header, or keep as a section label above — lean: move "Based on" into the card, drop the separate header
- Manual check: bright cover readability, no-image selection fallback, nav-away/return still shows backdrop (persisted)

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Bright/busy cover hurts text contrast | Med | Med | Fixed dark scrim gradient over the blur, independent of image |
| Older persisted `$selectedSong` lacks `image` | Med | Low | `{#if coverImage}` fallback → renders today's layout, no error |
| Blur/large image causes layout shift or jank | Low | Low | Absolute positioning out of flow; fixed container height behavior unchanged; `overflow: hidden` |
| Spotify image CORS when blurred via CSS | Low | Low | CSS `filter` on `<img>`/background doesn't taint or need CORS (no canvas); fine |
| Builder accidentally shows a cover | Low | Low | Props optional + unset on Builder until explicitly wired |

## Dependencies
- `search.py` returning `image` (already shipped)
- `$selectedSong` persisted store (already shipped)

## Open Questions
- "Similar Songs" header: fold into the in-card "Based on" header (lean yes) or keep both?
- Backdrop intensity (blur radius / opacity) — tune visually during C2
- Builder source image when later adopted (first-song vs mosaic) — deferred

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Source image | Selected/reference song's cover | Semantically anchors "similar songs"; user choice | 2026-06-23 |
| Treatment | Blurred ambient backdrop + crisp "Based on" header | Aesthetic + immersive + readable; user delegated the call | 2026-06-23 |
| Scrim approach | Fixed neutral dark scrim (no color extraction) | Readable on any cover without canvas/CORS complexity in v1 | 2026-06-23 |
| Scope | Explore results now; Builder later via optional props | User direction; gated API keeps Builder unaffected | 2026-06-23 |
| Backend | No changes | image already available end-to-end | 2026-06-23 |

---

# Plan — Add to Existing Playlists (Playlist Picker)
Date: 2026-06-23
Status: Draft
Brainstorm: docs/brainstorm.md (Deeper Spotify Account Integration, 2026-06-23)

## Overview
Let users add songs to their **existing** Spotify playlists — both in bulk (discovery/builder results) and per-song (individual cards) — via a reusable **playlist picker** modal. The picker lists the user's editable playlists with cover + name, includes a "New playlist" escape hatch (reusing the existing create flow), and appends the chosen tracks. Focus of this plan is the picker UX; the app-wide token hydration it depends on is carried as a prerequisite (M0).

## Goals & Success Criteria
- A reusable **PlaylistPicker** that opens from the results action bar (bulk) and from a song card (per-song)
- Lists only **editable** playlists (owned or collaborative) with cover thumbnail, name, track count
- **Search/filter** field for users with many playlists
- "New playlist" option preserves the current create-new flow
- Adds tracks via Spotify; clear success ("Added to *Playlist*" + open link) and failure states
- **Success = from the Explore page (without visiting Profile first), I can add all/selected discovery songs OR a single song to an existing playlist, and see it reflected in Spotify**

## Scope
### In Scope
- **M0 (prerequisite):** hydrate the Spotify `access_token` app-wide on load (currently Profile-only)
- Backend: list editable playlists; add tracks to a playlist
- `PlaylistPicker.svelte` modal (search, list, new-playlist, states)
- Wire bulk add (PlaylistResult action bar) + per-song add (SongCard) to the picker
- Reuse `PlaylistNameModal` for the "New playlist" path

### Out of Scope
- Save to Liked Songs / saved indicators (M2 — needs new scopes)
- Explore-from-top-tracks (M3), wiki/metadata (M4)
- Removing/reordering tracks in playlists; playlist management
- Duplicate-detection / "already in playlist" warnings (note as future nicety)

## Tech Stack & Architecture
- **No new deps.** Reuses the existing `access_token`-in-body pattern to FastAPI + spotipy.
- **M0 — global token (prerequisite).** Move the localStorage token load (`spotify_access_token` / `spotify_refresh_token` / `spotify_expires_at`) + refresh-if-expired logic out of the Profile page into an app-wide init (`+layout.svelte onMount`, writing the `access_token` store). The Profile page keeps owning the *login/PKCE exchange*; the layout just hydrates/refreshes an existing session so `$access_token` is populated everywhere. Avoid double-handling by having Profile call the same shared helper.
- **Backend endpoints (`spotify_actions.py`):**
  - `GET /spotify/playlists/?access_token=…` → fetch `/me` (id) + paginate `/me/playlists`, filter to `owner.id === me.id || collaborative`, return `[{id, name, image, track_count}]`.
  - `POST /spotify/add-to-playlist/` `{playlist_id, track_ids, access_token}` → `playlist_add_items(playlist_id, [spotify:track:…])`. 401 when token missing/expired.
- **PlaylistPicker component (reusable):** props `trackIds: string[]`, `contextLabel: string` (e.g. "12 songs" or "Flashing Lights"), `onClose`, `onAdded`. Owns: fetch playlists on open, search filter, row click → add, "New playlist" → existing `PlaylistNameModal` → create. Lives at the `PlaylistResult` level (which already holds the playlist + `access_token`); `SongCard` fires `onAddToPlaylist(trackId)` up to open it for one song.
- **Picker UX (recommended):** centered modal, dark surface; header "Add to playlist" + context subtitle; sticky **search input**; a pinned **"+ New playlist"** row at top; scrollable list of playlist rows (cover, name, track count); loading / empty ("No editable playlists") / error / not-connected states. Chosen over an inline dropdown because users can have many playlists and need search + clear affordance for the new-playlist path.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| M0 | Global token hydration | Load/refresh Spotify token app-wide so account actions work off the Profile page | — |
| M1a | Backend endpoints | List editable playlists + add-to-playlist | M0 |
| M1b | PlaylistPicker component | Modal: search, list, new-playlist, states | M1a |
| M1c | Wire bulk + per-song | Action-bar adds + SongCard add button open the picker | M1b |

## Task Breakdown

### M0 — Global token hydration
- Extract token load + refresh into a shared helper (e.g., `lib/spotifyAuth.js`): `hydrateToken()` reads localStorage, refreshes if expired, sets `$access_token`.
- Call it in `+layout.svelte onMount`.
- Refactor Profile page to use the shared helper (keep PKCE code-exchange there).
- Verify `$access_token` is set on Explore without visiting Profile.

### M1a — Backend
- `GET /spotify/playlists/`: `me = sp.me()`, paginate `sp.current_user_playlists()`, filter editable, map to `{id, name, image, track_count}`.
- `POST /spotify/add-to-playlist/`: validate token (401 if absent), `sp.playlist_add_items(playlist_id, uris)`; return `{added, playlist_url}`.

### M1b — PlaylistPicker.svelte
- On open: GET playlists (loading → list / empty / error).
- Search filter (client-side on name).
- Pinned "+ New playlist" → `PlaylistNameModal` → `POST /spotify/create-playlist/` (existing).
- Row click → `POST /spotify/add-to-playlist/` → success state ("Added to *Name*" + open link) → `onAdded`.
- States: not-connected (no token) → prompt to log in on Profile.

### M1c — Integration
- `PlaylistResult`: action bar "Add All as Playlist" / "Add Selected as Playlist" → open picker with the relevant ids (replaces direct create-new; create still reachable via picker's New-playlist).
- `SongCard`: add a "+"/"Add to playlist" control → fires `onAddToPlaylist(song.spotify.id)`; `PlaylistResult` opens the picker for that single id.
- Keep "Queue All" and "Clear" as-is.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Token not present off Profile page | High (today) | High | M0 makes it global — hard prerequisite, sequenced first |
| `/me/playlists` includes uneditable followed playlists | High | Med | Filter to `owner.id === me.id || collaborative` server-side |
| Many playlists → long list / pagination | Med | Low | Paginate server-side; client search filter |
| Expired token mid-action | Med | Med | M0 refresh-on-load; 401 → "reconnect on Profile" message |
| Duplicate track added | Med | Low | Allowed by Spotify; defer dedupe warning (note as future) |

## Dependencies
- Existing PKCE auth + persisted Spotify token (Profile page)
- `playlist-read-private`, `playlist-modify-public/private` scopes (already granted)
- spotipy `current_user_playlists`, `playlist_add_items`

## Open Questions
- Picker success: close immediately with a toast, or stay open to add to multiple playlists?
- Per-song add control icon/placement on `SongCard` (next to Explore →?)
- Should the selected song on the **profile** also get an add control, or cards only this round?
- Pagination UX if a user has >50 playlists (load-more vs fetch-all server-side)

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Picker UX | Modal with search + pinned "New playlist" | Scales to many playlists; clear create escape hatch | 2026-06-23 |
| Token hydration | App-wide in layout, shared helper | Account actions must work off Profile; avoid double-handling | 2026-06-23 |
| Picker ownership | Lives in PlaylistResult; SongCard fires callback up | PlaylistResult already holds playlist + token; avoids global state | 2026-06-23 |
| New-playlist path | Reuse existing PlaylistNameModal + create endpoint | No duplication; create stays reachable | 2026-06-23 |

### Revision 1 — Persistent right-side Playlists panel + drag-and-drop (2026-06-23)

**Overrides the "modal picker" decision.** Instead of a modal, the add-to-playlist surface is a **toggleable, persistent panel docked to the right edge of the screen**, available on every page, with drag-and-drop as the primary add mechanism.

**Design:**
- **Toggle ("Playlists Mode"):** a button in the header (alongside the ⚙ gear). Toggling it opens/closes the right panel. State lives in a **persisted store** (`playlistsPanelOpen`) so it stays open across navigation and reloads.
- **Placement & persistence:** the panel + toggle live in **`+layout.svelte`** so they persist no matter which page (Explore / Builder / Profile) is active.
- **Layout behavior:** panel is **fixed to the right edge**; when open, the main content area gets a `margin-right` equal to the panel width so songs and tiles are both visible (required for drag-and-drop). Slim width (~260–300px).
- **Tile grid:** playlists shown as a **2-column (or 3-col) grid flowing top→bottom**, vertically scrollable. Each tile = **cover image** (`playlist.images[0]` — Spotify's custom or auto 4-song mosaic), **name** (truncated), **track count**.
- **Drag-and-drop add:** song elements (discovery `SongCard`s and the profile's selected song) are `draggable`; dropping one on a playlist tile appends that track (native HTML5 DnD via `dataTransfer` carrying the track id; tiles are drop targets with drag-over highlight). DnD works across component boundaries since it's DOM-level. Desktop-only (app is min-width 800) — acceptable.
- **Per-song "+" icon (retained):** a "+"/add control on each `SongCard` as a non-drag path. Recommended behavior: clicking "+" opens the panel (if closed) and enters a brief "pick a playlist for *this song*" mode where a tile click adds it. (Exact interaction = open question.)
- **New-playlist path:** a "+ New playlist" tile/button at the top of the grid → reuses existing `PlaylistNameModal` + create endpoint.

**State / data:**
- `playlistsPanelOpen` (persisted store) — toggle state.
- `userPlaylists` (store) — fetched once on first open / login, cached; refetch on demand (e.g., after creating a playlist). Lives app-wide (layout-driven).
- Adds use the global `$access_token` (M0) — reinforces M0 as prerequisite.

**Revised milestones (supersede M1b/M1c):**
| # | Milestone | Description |
|---|-----------|-------------|
| M0 | Global token hydration | Unchanged prerequisite |
| M1a | Backend endpoints | List editable playlists (with images) + add-to-playlist — unchanged |
| M1b' | Playlists panel | Header toggle + persisted store + layout-docked slim panel + tile grid + content-shift |
| M1c' | Drag-and-drop + per-song add | Draggable songs, tile drop targets, add-on-drop; "+" icon fallback path; new-playlist tile |

**Decisions Log additions:**
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Add surface (override) | Persistent right-side panel, not a modal | User vision; always-available, supports drag-and-drop, scales as a workspace | 2026-06-23 |
| Persistence/placement | Panel + toggle in `+layout.svelte`, persisted open state | Must persist across all pages and reloads | 2026-06-23 |
| Open-panel layout | Shift main content left (margin-right), not pure overlay | Drag-and-drop needs songs + tiles visible simultaneously | 2026-06-23 |
| Tile cover | Use `playlist.images[0]` | Spotify already returns custom image or 4-song mosaic | 2026-06-23 |
| Primary add UX | Drag song → drop on tile; "+" icon as fallback | Matches user's drag vision; keeps a click path | 2026-06-23 |

**New open questions (for /scaffold or deeper plan):**
- Per-song "+" interaction: open panel + "pick a playlist for this song" mode, vs a small anchored popover list, vs just opening the panel for manual drag
- Grid columns: fixed 2, fixed 3, or responsive to panel width
- Panel width + whether it's user-resizable (likely fixed for v1)
- Drag affordance on the profile's selected song (drag the cover thumbnail?) vs cards-only in v1
- Refetch strategy for `userPlaylists` after an add (update track_count optimistically?) 
- Mobile/touch: out of scope (desktop min-width 800) — confirm

### Revision 2 — "+" interaction + grid columns locked (2026-06-23)

**Per-song "+" behavior is toggle-state-dependent:**

| Playlists Mode toggle | Click "+" on a song |
|---|---|
| ON (panel open) | **Anchored popover** at the card — compact quick-picker; click a playlist → added; panel unaffected |
| OFF (panel closed) | **Panel opens** (transient "peek") in "pick a playlist for *this song*" mode → click a tile → added → **panel auto-closes again** |

Rule of thumb: **the toggle is the single source of "stay open" intent.** "+" with the toggle off is a temporary peek that closes after the add (also closes on Esc / click-away if nothing is picked). Drag-and-drop applies only while the panel is open.

**Tile grid:** start with **2 columns** (fixed) for v1.

**Decisions Log additions:**
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| "+" when toggle ON | Anchored popover quick-picker at the card | Panel's already a workspace; in-place add is fastest, no mode | 2026-06-23 |
| "+" when toggle OFF | Transient panel open ("pick a playlist for this song"), auto-close after add | Toggle is the only "stay open" control; "+" is a just-in-time peek | 2026-06-23 |
| Tile grid columns | Fixed 2 columns (v1) | Slim panel; simple to start; can revisit | 2026-06-23 |

---

# Plan — Profile Page Revamp (Taste Dashboard)
Date: 2026-06-24
Status: Draft
Brainstorm: docs/brainstorm.md (Profile Page Revamp — Taste Dashboard, 2026-06-24)

## Overview
Evolve the profile page from a static stats view into a modular taste dashboard. Phased: **P1** delivers the quick, high-consistency wins (integrated controls, SongCard-based track list, genre radar); **P2** adds the modular layout (expand/collapse, hide-others, per-module scroll); **P3** adds taste-over-time charts from Spotify-native data (gated on an audio-features availability test). This plan details P1; P2/P3 are scoped at a high level.

## Goals & Success Criteria
- Controls (num-tops + time-period) integrated into a compact inline toolbar, not a standalone section
- Top-tracks list reuses **SongCard**, inheriting like / add-to-playlist (and explore)
- A **genre radar** showing the user's most-listened genres (from top artists, rank-weighted)
- **Success (P1) = profile shows SongCard-based tracks with working like/add, a genre radar reflecting top artists, and inline controls that re-fetch on change — visually consistent with the rest of the app**

## Scope
### In Scope (P1)
- Generalize `SongRadar` into a reusable axes-driven radar; migrate the song-profile usage
- Adapter: profile `top_tracks` (flat) → SongCard's `{ spotify: {…} }` shape; render tracks via SongCard
- Genre aggregation (client-side, from `top_artists[].genres`, rank-weighted) → top 6 → genre radar
- Replace the standalone controls bar with a compact inline toolbar (global timeframe + num-tops)

### Out of Scope (P1 — later phases)
- **P2:** module wrapper (summary/expanded states, maximize-hides-others, per-module scroll)
- **P3:** taste-over-time charts; the audio-features availability test
- LLM-based aggregate scoring (last-resort fallback only, P3)
- Changes to `/get-profile/` beyond what's already returned

## Tech Stack & Architecture
- **No backend changes for P1.** `/get-profile/` already returns `top_artists` (with `genres`, `popularity`, `images`, `url`) and `top_tracks` (`title, artists, id, image, duration_ms, explicit, track_url, album`).
- **Generalize `SongRadar`** → accept `axes: [{label, value}]` + optional `max` (defaults to 100 or the max value). The current 6 fixed dimensions become a caller-provided array. The song-profile passes its 6 score axes; the genre radar passes top-6 genre axes (max = top genre's weight). One component, two uses. Keeps the existing visual (gradient fill, tight viewBox, label+value).
- **SongCard adapter** — map each `top_track` to `{ spotify: { id, title, artists, album, image, track_url, duration_ms } }` (no `reason`). SongCard's like (`onSaveToggle`) and add (`pendingAdd`/drag) already work app-wide via the global token. `onExplore` wires to navigate to Explore with that song selected (`$selectedSong = {…}; goto('/')`).
- **Genre aggregation** (client-side): for each top artist at rank `i` (0-based), add weight `(N - i)` to each of its genres; sum per genre; take top 6 by weight. Rank-weighting approximates "how much you listen," not raw frequency. Render via the generalized radar (max = top genre weight).
- **Controls** — a slim inline toolbar (right-aligned in a header row) holding the time-period + num-tops selectors; **global** (drives the lists + genre radar via the existing `getProfile()` re-fetch). The over-time charts (P3) will own their own axis.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| PR1 | Generalize radar | `SongRadar` → axes-driven; migrate song-profile (no visual regression) | — |
| PR2 | Tracks as SongCard | Adapter + render top_tracks via SongCard; like/add/explore | — |
| PR3 | Genre radar | Aggregate top artists' genres (rank-weighted, top 6); render via PR1 | PR1 |
| PR4 | Integrate controls | Compact inline toolbar (global timeframe + num-tops); remove standalone bar | PR2 |
| P2 | Modular dashboard | Module wrapper: summary/expand, maximize-hides-others, per-module scroll | PR1–PR4 |
| P3 | Taste over time | Native-data charts (popularity, era; audio-features if available) | audio-features test |

## Task Breakdown (P1)

### PR1 — Generalize the radar
- Change `SongRadar` props to `axes: [{label, value}]`, optional `max`
- Compute geometry from `axes.length` (already parameterized by `order.length` — generalize to the passed array); scale by `value / max`
- Update `SongProfile` to pass its 6 score fields as `axes`
- Verify the song profile radar looks identical

### PR2 — Top tracks as SongCard
- `toSongCardShape(track)` adapter → `{ spotify: { id, title, artists, album, image, track_url, duration_ms } }`
- Replace the profile's `top_tracks` list-row markup with `{#each}` of `SongCard`
- Wire `onSaveToggle` (batch saved-state check like PlaylistResult) and add (default works)
- `onExplore` → set `$selectedSong` + `goto('/')`
- Keep Top Artists as list rows for now (no SongCard equiv for artists)

### PR3 — Genre radar
- `aggregateGenres(top_artists)` → rank-weighted counts → top 6 `{label, value}`
- Handle sparse data: if < 3 distinct genres, hide the radar (a radar needs ≥3 axes) and show a small note
- Render `<SongRadar axes={genreAxes} max={topWeight} />` in a "Top genres" section

### PR4 — Integrate controls
- Build a compact toolbar component (or inline) with the time-period + num-tops selectors styled like the panel's sort controls
- Place it in a header row (e.g., above the lists, right-aligned, slim) — not the full-width standalone bar
- Keep the existing `setNumberOfTops`/`setTimePeriod` → `getProfile()` re-fetch wiring
- Remove the old `.top-parameters-div` bar

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Radar generalization regresses the song profile radar | Med | Med | Keep visuals identical; verify song profile after refactor |
| Sparse/empty genres for some artists/users | Med | Low | Rank-weighted sum tolerates gaps; hide radar if < 3 genres |
| SongCard adapter shape mismatch | Low | Med | top_tracks already has all needed fields; `reason` optional |
| Explore-from-profile cross-page nav state | Low | Low | Reuse `$selectedSong` store + `goto('/')`; it's already persisted |
| Global timeframe vs over-time axis confusion (P3) | Low | Low | Decided: global drives filter-modules; over-time owns its axis |

## Dependencies
- Existing `/get-profile/`, global token (M0), SongCard with like/add (M1–M2), `$selectedSong` store
- P3 only: a valid audio-features test result

## Open Questions
- Genre aggregation: rank-weighted (planned) vs raw frequency — confirm the weighting feels right once rendered
- Exact toolbar placement (per-list header vs one page-level toolbar)
- Whether Top Artists should also become card-style rows (no current artist-card component)
- **P3 gate:** does the app have audio-features access? (test before planning P3 in detail)

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Phasing | P1 quick wins → P2 modular → P3 over-time | Brainstorm; de-risks the expensive part | 2026-06-24 |
| Radar reuse | Generalize SongRadar to axes-driven | One component for song + genre radars; DRY | 2026-06-24 |
| Track rows | Reuse SongCard via adapter | Consistency + free like/add/explore | 2026-06-24 |
| Genre weighting | Rank-weighted sum, top 6 | Approximates listening share better than raw count | 2026-06-24 |
| Timeframe control | Global for filter-modules; over-time owns its axis | Resolves the filter-vs-axis tension | 2026-06-24 |
| Taste-chart data | Spotify-native first, LLM last-resort | Sidesteps the LLM cost problem | 2026-06-24 |

---

# Plan — Taste Analytics Expansion
Date: 2026-06-24
Status: Draft
Brainstorm: docs/brainstorm.md (Taste Analytics Expansion, 2026-06-24)

## Overview
Add four taste-analytics modules to the profile dashboard — **mainstream-ness**, **decade distribution**, **genre depth + diversity**, **listening clock** — using only data a post-2024-11-27 Spotify app can read. Reuses the P2 modular dashboard. TA1–TA3 ship with no new scope; TA4 adds `user-read-recently-played` (one re-auth).

## Goals & Success Criteria
- Four modules rendering from real Spotify-native data, no deprecated endpoints
- Recover the "mainstream-ness" metric (lost in P3) via artist popularity
- **Success = each module shows real, non-empty data for a logged-in user; the dashboard stays modular/scrollable; nothing calls audio-features/recommendations/related-artists**

## Scope
### In Scope
- TA1: artist-popularity "mainstream-ness" (extend taste-over-time) + obscure/popular artist callout
- TA2: decade distribution (add `release_date` to `/get-profile`; new Eras module + BarChart)
- TA3: genre depth + diversity (ranked bars + diversity index, folded into the Genres module)
- TA4: listening clock (new scope + `recently-played` endpoint + Heatmap module)
- Small reusable chart components: `BarChart`, `Heatmap`

### Out of Scope
- Playback / Web Playback SDK (deferred; Premium available but not this round)
- Recently-played as a discovery seed (TA4 scope unlocks it; not built here)
- Full listening history (Spotify caps recently-played at 50)
- Anything via deprecated endpoints

## Tech Stack & Architecture
- Reuses the P2 `DashboardModule` system and the existing per-timeframe `/get-profile` + all-timeframe `/spotify/taste-over-time` data flow.
- **TA1 — Mainstream-ness:** extend `taste-over-time` to also fetch top **artists** per timeframe and return `artist_popularity: [p1,p2,p3]`. Frontend adds it as the taste chart's 0–100 line (folds into the existing "Taste over time" module; era drops to a stat). "Most obscure / most popular artist" comes from the current-timeframe `/get-profile` top_artists.
- **TA2 — Decade distribution:** add `release_date` to `/get-profile` top_tracks; client buckets years into decades for the selected timeframe; render via a new `BarChart`.
- **TA3 — Genre depth + diversity:** reuse the existing rank-weighted genre aggregation (full list, not just top 6) → ranked `BarChart` + a **diversity index** (normalized entropy of genre weights → 0–100). Folds into the Genres module alongside the radar.
- **TA4 — Listening clock:** add `user-read-recently-played` to SCOPES (re-auth). New `GET /spotify/recently-played/` → `/me/player/recently-played?limit=50` → aggregate `played_at` into hour-of-day (0–23) and day-of-week buckets. Render via a new `Heatmap`. Label "based on your last 50 plays."
- **New components:** `BarChart.svelte` (reused by TA2 + TA3), `Heatmap.svelte` (TA4). `TrendChart` stays line-only.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| TA0 | Verify artist popularity | Confirm `artist.popularity` is NOT stripped (one check) — gates TA1 | — |
| TA1 | Mainstream-ness | Artist popularity in taste-over-time + chart line + obscure/popular callout | TA0 |
| TA2 | Decade distribution | `release_date` in get-profile; Eras module + BarChart | — |
| TA3 | Genre depth + diversity | Ranked genre bars + diversity index in Genres module | — |
| TA4 | Listening clock | New scope + recently-played endpoint + Heatmap module | re-auth |

## Task Breakdown

### TA0 — Verify artist popularity (gate)
- Hit `/get-profile` (or the extended endpoint) and confirm top_artists `popularity` is non-zero. We proved *track* popularity is stripped but never confirmed *artist* popularity. If it's also 0 → drop TA1's mainstream line and use a different proxy (or cut it).

### TA1 — Mainstream-ness
- `taste-over-time`: per timeframe, `current_user_top_artists(limit=20, time_range)`, avg `popularity` → `artist_popularity[]`.
- Frontend: taste chart series = artist popularity (0–100) line; keep era + length + explicit as stat trends.
- Callout: most obscure (min popularity) / most popular (max) artist from current top_artists.

### TA2 — Decade distribution
- Backend: add `release_date` to `/get-profile` top_tracks mapping.
- Frontend: `decadeBuckets(top_tracks)` → {1980s: n, …}; render `BarChart`. Respects the global timeframe.

### TA3 — Genre depth + diversity
- Reuse `aggregateGenres` but return the full ranked list + total weight.
- Diversity index: normalized Shannon entropy of genre weights → 0–100 ("varied" vs "focused").
- Render ranked `BarChart` (top ~8) + the index inside the Genres module (with the radar).

### TA4 — Listening clock
- `spotifyAuth.js`: add `user-read-recently-played` to SCOPES (note: re-auth required).
- Backend: `GET /spotify/recently-played/` → fetch 50, bucket `played_at` (parse ISO → local hour/day), return `by_hour[24]` + `by_day[7]`.
- Frontend: `Heatmap` (hour-of-day primary; day-of-week secondary) in a new "Listening clock" module; label the 50-play window.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Artist popularity also stripped** (like track popularity) | Med | High for TA1 | TA0 verifies first; if gone, drop the mainstream line / use a proxy |
| recently-played 50-cap → sparse/empty clock | Med | Med | Honest labeling; hide module if <~10 plays |
| `played_at` timezone (UTC vs local) skews the clock | Med | Low | Parse to the user's local time on the client |
| Genres sparse → weak diversity index | Low | Low | Index handles small N; hide if <3 genres |
| Dashboard gets crowded (6 modules) | Low | Low | 2-col grid + expand/collapse already handles it |

## Dependencies
- P2 dashboard, `/get-profile`, `/spotify/taste-over-time`, global token, existing genre aggregation
- TA4: `user-read-recently-played` scope (re-auth)

## Open Questions
- Listening clock viz: hour-of-day bars + separate day-of-week, or a single day×hour grid heatmap?
- Diversity index formula: normalized entropy (planned) vs simple distinct-genre count
- Decade granularity: decades (planned) vs 5-year buckets; current timeframe (planned) vs all-time
- Mainstream-ness: confirmed folding into the taste module (vs its own) — OK?

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Mainstream metric | Artist popularity (not track) | Track popularity stripped; artist may be available (TA0 gate) | 2026-06-24 |
| Mainstream placement | Fold into taste-over-time module | It's a time series; recovers that chart's line | 2026-06-24 |
| Genre depth placement | Fold into the Genres module | Radar + breakdown + diversity in one place | 2026-06-24 |
| Diversity index | Normalized Shannon entropy → 0–100 | Captures spread better than a raw count | 2026-06-24 |
| Decade buckets | Decades, current timeframe | Cleanest histogram; respects the controls | 2026-06-24 |
| New components | BarChart (TA2+TA3), Heatmap (TA4) | TrendChart is line-only; bars/heatmap are distinct | 2026-06-24 |
| Scope sequencing | TA1–TA3 (no scope) before TA4 (re-auth) | Defer the re-auth to last | 2026-06-24 |

### TA0 result — artist popularity is stripped (2026-06-24)
**Verified:** `/get-profile` top_artists `popularity` → `[0,0,0,…]`. Artist popularity is stripped for this app, just like track popularity. There is no popularity signal available.

**Decision: drop TA1 (mainstream-ness).** No viable popularity proxy to ship. The taste-over-time chart stays as the **release-year (era)** line + stat trends (its current state). Possible future probe: artist `followers.total` as a mainstream proxy — but that's a separate verification, not in scope now.

**Revised milestone set:** TA2 (decade distribution) → TA3 (genre depth + diversity) → TA4 (listening clock). TA2/TA3 carry no new scope; TA4 needs the re-auth.

**Brain skill updated:** `domains/spotify/rules.md` + `cursor-rule.mdc` now note popularity is stripped from BOTH track and artist objects (re-run `install/install.sh` to propagate the Cursor rule).

---

# Plan — Native iOS App
Date: 2026-08-03
Status: Active
Brainstorm: `docs/brainstorm.md` → "Native iOS App (2026-08-03)"
Depth: high-level for P1–P6; **P0 at task level** (it is the immediate next work)

---

## Overview

Add a native SwiftUI iOS app with full functional parity to the web app, reachable from anywhere,
while the web app keeps the ability to run against a local model on the Mac. The backend is already
an accidental mobile API — `profile.py`, `song_profile.py`, `llm_playlist.py`, and `spotify_actions.py`
take the Spotify token per request and return plain JSON — so the server work is small relative to
the client rebuild.

**P0 is backend-only and ships before any Swift is written.** It closes the two open items from the
2026-06-24 reflect, migrates the LLM key off session cookies, and stands up the hosted instance. The
web app keeps working throughout.

---

## Goals & Success Criteria

| Goal | Success Criteria |
|------|-----------------|
| Harden before extending | Account integration and AI-analysis paths exercised end-to-end; failures fixed, not just observed |
| Decouple the LLM key from cookies | `/llm/*`, `/song/profile/`, `/llm/generate-playlist/` work from a client with no cookie jar and no origin |
| App works from anywhere | Hosted FastAPI instance reachable over TLS, guarded by a device key |
| Web app keeps a local-model path | Local instance still serves `:5173`; `ENABLE_LOCAL_LLM` gates Ollama-backed providers |
| Full iOS parity (end state) | Profile, Explore, Builder, Playlists panel, analytics — all native |
| Native-only payoff | Now-playing widget, App Intents/Siri, Spotify iOS SDK playback |
| SwiftUI learning value | Charts rebuilt by hand rather than wrapped in a WebView |

---

## Scope

### In Scope
- P0: API hardening, `X-LLM-Key` migration, hosted deployment, device-key middleware, dead-code removal
- P1–P6: native SwiftUI client to full functional parity, plus widget / App Intents / iOS SDK playback
- Spotify PKCE via `ASWebAuthenticationSession` + custom URL scheme, tokens in Keychain
- Two deployments of one FastAPI codebase (local for web, hosted for iOS)

### Out of Scope
- Making the web app responsive. It stays deliberately desktop-only (min-width 800) — the phone is
  now the mobile surface. Revisit only if the two clients diverge in an annoying way.
- App Store release. Personal distribution via a paid developer account / TestFlight.
- Adding Ollama itself. P0 only leaves the door open (`ENABLE_LOCAL_LLM`); wiring it is separate work.
- Any database. The backend stays stateless — that property is what makes two deployments free.

---

## Tech Stack & Architecture

**Backend: one codebase, two deployments.** Chosen over a hosted-backend-tunnelling-to-Ollama design
because the tunnel would become a hard dependency of every LLM request, and over local-only because
"from anywhere" was a stated goal. Works because there is no shared state to drift.

| Instance | Serves | Guard | LLM providers |
|---|---|---|---|
| Local (Mac, `:8005`) | The web app | none (localhost) | Remote + local (Ollama, later) |
| Hosted (Fly/Render/Railway) | The iOS app | `X-Device-Key` | Remote only |

**LLM key transport.** `X-LLM-Provider` + `X-LLM-Key` headers, read per request via a FastAPI
dependency. Replaces `request.session` in three routers and `credentials: 'include'` in four
frontend files. Chosen over keeping cookies because a native client has no origin, and over a
server-side keystore because that would introduce the state the two-deployment design depends on
not having.

**Hosted-instance auth.** A long random secret in `X-Device-Key`, checked by middleware, stored in
iOS Keychain. Not real multi-user auth — appropriate for a single-user tool, and it stops an open
endpoint from burning the Spotify client-credentials quota and inviting traffic against BYOK keys.
Middleware is a no-op when `DEVICE_KEY` is unset, so local dev is unaffected.

**iOS.** SwiftUI, minimum target TBD (17 vs 18 — gates WidgetKit and Charts APIs). Networking via
`URLSession` with a hand-rolled thin client, or generated from the exported OpenAPI schema (decide
in P1). Tokens and keys in Keychain; cross-screen state in SwiftData/UserDefaults, replacing the
`persisted()` localStorage helper.

**Charts.** Swift Charts for bar/column/trend/heatmap. The four radar components become hand-drawn
`Path` + `GeometryReader` — Swift Charts has no polar chart. Treated as the SwiftUI learning
centerpiece rather than as a cost to avoid.

---

## Milestones

| # | Milestone | Description | Dependencies |
|---|---|---|---|
| P0 | Backend hardening + hosted deploy | Close reflect items, `X-LLM-Key` migration, hosted instance, device key, dead-code removal | — |
| P1 | SwiftUI shell + auth + Profile | Xcode project, PKCE via custom scheme, Keychain, Profile screen, screenshot loop | P0 |
| P1.5 | Now-playing widget + first App Intent | Early native payoff; needs only auth + Spotify Web API | P1 |
| P2 | Search + Explore + song profile + radar | The custom `Path` chart work | P1, V1 |
| P3 | Playlist builder | Chat, generation, save, queue — reuses `/llm/generate-playlist/` unchanged | P1 |
| P4 | Playlists panel | Native `.draggable`/`.dropDestination`; touch redesign, not a port | P3 |
| P5 | Taste analytics dashboard | Swift Charts rebuild of the profile modules | P2 |
| P6 | Spotify iOS SDK playback + full Siri surface | The remaining native-only motivations | P1.5, V1 |

---

## Task Breakdown — P0 (backend only)

### V1 — Spotify dashboard verification *(do first; gates P2 and P6)*
These are verification tasks, not design tasks. Both can be answered in the developer dashboard and
a couple of curl calls.

- **V1.1** Confirm the existing client ID still returns data from `/recommendations` and audio-features.
  Test `GET /get-recommendations/?trackId=<known id>` against the running local backend. If it 404s
  or returns empty, P2's radar and `recommendations.py` need rescoping before they're planned.
- **V1.2** Add `boominbeats://callback` as a second redirect URI on the **existing** client ID.
  Do not register a new Spotify app — grandfathered endpoint access follows the client ID.
- **V1.3** Note whether the Spotify iOS SDK can consume the Web API token from the PKCE flow or needs
  its own session. Decides whether P6 is additive or a second auth path.

### H1 — Account integration end-to-end *(reflect Next Step 1)*
- **H1.1** Exercise the Playlists panel against an account with many playlists: drag-to-add, per-song
  `+` in both modes, bulk add, panel search, liked-state indicators — on both Explore and Builder.
- **H1.2** Walk the error paths: expired token, 403 from missing scope, empty `track_ids`
  (`playlist_add_items` rejects an empty list — confirm the guard in `spotify_actions.py` holds),
  full re-auth after logout.
- **H1.3** Delete the empty test playlists the earlier create bug left in the Spotify account.
- **H1.4** Fix what H1.1–H1.2 surface.

### H2 — AI analysis pipeline *(reflect Next Step 2)*
- **H2.1** Verify JSON parsing across all three providers (Claude, OpenAI, Groq) in both
  `song_profile.py::_parse_analysis` and `llm_playlist.py`. The playlist loop currently swallows a
  parse failure with a bare `continue` — confirm that degrades sensibly rather than silently
  returning a short playlist.
- **H2.2** Handle malformed output and missing `scores` explicitly rather than falling through to
  `_empty_analysis()` with no signal to the user.
- **H2.3** Refresh model IDs in `services/llm_client.py`: `claude-sonnet-4-6` → `claude-sonnet-5`.
  In `routers/llm_connect.py`, `claude-haiku-4-5-20251001` → the `claude-haiku-4-5` alias. No other
  changes needed — the call sites pass no `temperature` or `thinking`, so nothing else breaks.

### K1 — `X-LLM-Key` migration *(the change iOS strictly requires)*
Land this on the web app first so it's proven before a second client depends on it.

- **K1.1** Add a `get_llm_credentials` FastAPI dependency reading `X-LLM-Provider` / `X-LLM-Key`,
  raising 401 when absent.
- **K1.2** Backend: `llm_connect.py` becomes stateless validation only (no `request.session` writes);
  `llm_playlist.py:26-27` and `song_profile.py:105-106` take the dependency instead of session reads.
  `/llm/status/` either drops or becomes a pure echo of the header.
- **K1.3** Remove `SessionMiddleware` and `SESSION_SECRET_KEY` from `main.py` / `config.py` once no
  router reads `request.session`.
- **K1.4** Frontend: send the headers from `llmConfig` and drop `credentials: 'include'` in
  `LLMSettingsPanel.svelte`, `ChatInterface.svelte`, `SongProfile.svelte`, `routes/+page.svelte`.
- **K1.5** Verify the full BYOK flow still works from the browser after the change.

### D1 — Hosted deployment + device key
- **D1.1** `DEVICE_KEY` in config; middleware rejecting requests without a matching `X-Device-Key`.
  No-op when `DEVICE_KEY` is unset, so the local instance is unaffected.
- **D1.2** Widen CORS from the single hardcoded origin to a config-driven list (native clients send
  no origin, but the hosted instance still serves nothing else — keep it tight).
- **D1.3** Pick a host and deploy. Secrets: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`,
  `LASTFM_API_KEY`, `DEVICE_KEY`.
- **D1.4** Confirm the hosted instance answers `/get-profile/` and `/search/` with a real token, over
  TLS, from off the LAN.

### C1 — Delete dead code *(reflect Next Step 5)*
`sverdle/`, `Counter.svelte`, `recommendations.svelte`, the svelte-welcome images, `backend_server/`,
`manage.py`, `db.sqlite3`, and the `/account-analysis/` route + `routes/account_analysis/` page
(the endpoint returns `{"status": "coming soon"}`). Do this before P1 so none of it gets ported.

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `/recommendations` + audio-features already dead on this client ID | Medium | High — P2's radar and Explore depend on them | V1.1 tests it first; if dead, rescope P2 around Last.fm tags + LLM scores, which `song_profile.py` already produces |
| A new Spotify app loses grandfathered endpoint access | Low (avoidable) | High | V1.2 — add a redirect URI to the existing client ID; never register a new app |
| Hosted instance abused / quota burned | Medium | Medium | D1.1 device key; keep CORS tight; monitor Spotify quota |
| Radar `Path` math eats the P2 schedule | Medium | Medium | Ship P2 with bar-style score meters first; radar as a follow-up within P2 |
| SwiftUI visual iteration repeats the CSS feedback-loop problem | High | Medium | Simulator screenshots via `xcrun simctl` + previews set up in P1 before any styling |
| Scope fatigue — parity is a months-long build | Medium | Medium | P1.5 front-loads a native-only win; each milestone ships something usable |
| Spotify iOS SDK needs its own auth session | Medium | Low | V1.3 answers it; P6 is last either way |

---

## Dependencies

- Existing Spotify client ID with an added `boominbeats://` redirect URI
- Paid Apple Developer account (device install beyond the 7-day free-provisioning window)
- A hosting account (Fly / Render / Railway)
- Xcode 16+; iOS minimum target decision
- Unchanged: `spotipy`, `anthropic` / `openai` / `groq` SDKs, Last.fm API key

---

## Open Questions

- iOS minimum target: 17 or 18? Gates WidgetKit and Swift Charts APIs.
- Xcode project location: `src/ios/` alongside `src/web/`, or a separate repo?
- Networking layer: hand-rolled `URLSession` client, or generated from the exported OpenAPI schema?
- Which host, and is free-tier cold start acceptable for LLM requests that already take seconds?
- Offline behavior: cache last-known profile/playlists, or require connectivity?
- Does `/llm/status/` survive the K1 migration, or get deleted?

---

## Decisions Log

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Native vs responsive PWA | Native SwiftUI | All four motivations present — widgets/Siri, iOS SDK playback, SwiftUI learning, phone access. Any one alone would have favored the PWA | 2026-08-03 |
| Backend location | One codebase, two deployments | Satisfies "anywhere" + "local model on web" without a tunnel; free because the backend is stateless | 2026-08-03 |
| LLM key transport | `X-LLM-Provider` / `X-LLM-Key` headers | Native clients have no origin; also retires a signed-not-encrypted cookie holding an API key. Revisits the Medium-confidence call in the 2026-06-04 plan | 2026-08-03 |
| Hosted auth | `X-Device-Key` shared secret | Single-user tool; real auth is unjustified, but an open endpoint is not acceptable | 2026-08-03 |
| Spotify app registration | Reuse existing client ID | Grandfathered endpoint access follows the client ID | 2026-08-03 |
| Sequencing | Harden before building the client | Both least-tested layers are ones an iOS client would depend on; simulator debugging costs more than browser debugging | 2026-08-03 |
| Widget position | P1.5, not P6 | Depends only on auth; front-loads native payoff ahead of full parity | 2026-08-03 |
| Web app responsiveness | Stays desktop-only | The 2026-06-24 min-width-800 decision becomes deliberate rather than a gap | 2026-08-03 |
| Playlists panel on iOS | Redesign for touch, not port | HTML5 DnD lacks touch; SwiftUI `.draggable` is touch-native and can be better than the original | 2026-08-03 |
| Model IDs | `claude-sonnet-5`, `claude-haiku-4-5` | Call sites pass no `temperature`/`thinking`, so it's a pure ID swap | 2026-08-03 |

### V1 result — deprecated endpoints confirmed dead, but nothing live depends on them (2026-08-03)

**V1.1 — probed the existing client ID (`a70007…0bc0`) directly via client-credentials:**

| Endpoint | Status | Notes |
|---|---|---|
| `/v1/search` | **200** | Works — `search.py` is fine |
| `/v1/tracks/{id}` | **200** | Works, but `popularity: None` and `preview_url: None` (matches the TA0 finding) |
| `/v1/recommendations` | **404** | Dead |
| `/v1/audio-features/{id}` | **403** | Dead |
| `/v1/artists/{id}/related-artists` | **403** | Dead |

**Live impact: none.** Two reasons —

1. `/get-recommendations/` is called by exactly one file, `lib/components/recommendations.svelte`, which is
   imported only by the unused `lib/index.js` barrel. It is dead demo code already on C1's delete list.
2. Audio features were already defended: `spotify_actions.py:154-174` comments the deprecation and degrades
   to `audio_features=None`. The profile page's `audioSeries` renders empty rather than breaking.

So the 404/403s describe endpoints the running app does not depend on. **No rescoping needed.**

**Correction to the brainstorm and to this plan's risk table.** Two claims were wrong, and both reduce scope:

- *"Every chart is built on layercake + d3 emitting SVG."* Only the **dead** components are. `layercake`,
  `d3-scale`, and `d3-shape` are imported by exactly two files — `FeatureRadar.svelte` and `Radar.svelte` —
  both of which are layercake's own demo example, still rendering baseball pitch data (`radarScores.js`
  exports `{name: 'Allison', fastball: 10, change: 0, slider: 4, …}`). Every **live** chart — `SongRadar`,
  `TrendChart`, `BarChart`, `ColumnChart`, `Heatmap` — is hand-rolled dependency-free SVG/CSS.
- *"P2's radar and Explore depend on audio-features."* They don't. The live radar is `SongRadar.svelte`,
  fed by the **LLM-generated** 0–100 scores from `song_profile.py` (Energy, Danceability, Positivity,
  Acousticness, Intensity, Tempo) and by genre counts on the profile page. It is unaffected by any Spotify
  deprecation.

**Consequences:**

- **Risk "recommendations + audio-features already dead" — retired.** Confirmed dead, confirmed harmless.
- **Risk "radar `Path` math eats the P2 schedule" — downgraded.** `SongRadar.svelte` is a single component
  with its geometry already solved in explicit constants (`cx=170, cy=145, maxR=84, levels=[.25,.5,.75,1]`).
  That is close to a direct transcription into a SwiftUI `Path`, not a from-scratch derivation. The
  bar/column/trend/heatmap components are likewise plain SVG/CSS, so P5 maps onto Swift Charts cleanly.
- **C1's delete list grows** — add `FeatureRadar.svelte`, `Radar.svelte`, `AxisRadar.svelte`,
  `radarScores.js`, and the now-unused `lib/index.js` barrel; then drop `layercake`, `d3-scale`, and
  `d3-shape` from `package.json`. This removes the frontend's only three runtime dependencies.
- **New P0 task — H2.4:** `recommendations.py` is a live router whose upstream endpoint returns 404. Delete
  the router alongside `recommendations.svelte` rather than leaving a broken route registered in `main.py`.

**V1.3 — Spotify iOS SDK auth:** `SPTAppRemote` accepts an externally obtained token — the documented
pattern is `appRemote.connectionParameters.accessToken = <token>`, and nothing requires that token to come
from `SPTSessionManager`. So **P6 is additive**: the app's own PKCE session feeds playback control, with no
second auth path. Still to verify at P6 time: whether app-remote requires the Spotify app installed and a
Premium account (the auth doc doesn't cover it; both are likely).

**V1.2 — still open, and it's yours to do:** add `boominbeats://callback` as a second redirect URI on the
**existing** client ID at developer.spotify.com. Do not register a new app.

### H2 result — parsing hardened; two live bugs found (2026-08-03)

**Done:** H2.1, H2.2, H2.3, H2.4. Verified by 35 synthetic tests (`python -m unittest discover tests`
from `src/web/backend`) plus a live reload + route check. Nothing committed.

**New `services/llm_json.py`.** Single `extract_json()` shared by the playlist and song-profile paths.
The previous inline `removeprefix('```json').removeprefix('```').removesuffix('```')` handled fenced
output only; it fell through to a silent empty result on the most common real failure — prose wrapped
around the JSON (`Here is the analysis:\n{...}`), which Groq/Llama emits constantly. The replacement
strips fences (```` ``` ````/`~~~`, with or without a language tag), then falls back to scanning for the
first balanced `{...}`/`[...]`, tracking string state and escapes so braces inside `"reason"` text don't
break the scan. Raises `LLMParseError` carrying a 300-char snippet of the offending output.

**`routers/song_profile.py`:**
- Score keys now matched **case-insensitively** — a model returning `"energy"` for `"Energy"` previously
  produced a partial dict, failed the `len(parsed_scores) == len(SCORE_KEYS)` check, and silently killed
  the entire radar.
- `_coerce_score()` accepts `85`, `85.0`, and `"85"`, and **rejects `bool`** — `isinstance(True, int)` is
  `True`, so `"Energy": true` used to be stored as `1`.
- Still requires all six axes before rendering (a partial set draws a misleading shape), but now reports
  *which* are missing instead of failing silently.
- New response field **`analysis_error`**. Previously "no LLM connected" and "LLM connected but the call
  or the parse failed" were both `has_llm: false` and indistinguishable to the frontend and to the user.
  `null` = not connected; a string = connected and something went wrong.
- Failures log to uvicorn (`[song-profile] …`) rather than vanishing.

**`routers/llm_playlist.py`:**
- The bare `except Exception: continue` swallowed provider errors, JSON errors, and network failures
  identically. Now separated, each logged, and the last one retained.
- New `_normalize_suggestions()` guards `validate_songs()`, which indexes `suggestion['title']` directly
  and would raise mid-request on a malformed entry. It also unwraps `{"playlist": [...]}` /
  `{"songs": [...]}` / `tracks` / `results` / `items`, and a bare single-song object — all shapes models
  return when they ignore "respond ONLY with a valid JSON array".
- New response field **`error`**, non-null when the run ends short. An all-attempts-failed run previously
  returned an empty playlist with HTTP 200 and no explanation.

**Bug 1 — malformed retry prompt (fixed).** If attempt 0 failed to parse, `failed` was still `[]`, so
attempt 1 sent `The following songs could not be found on Spotify: . Suggest 12 different replacement
songs…` — an empty list interpolated into the prompt. A parse/call failure now re-asks the original
request with a JSON-format reminder; only a genuine Spotify miss produces the "not found" prompt.

**Bug 2 — the Last.fm API key is invalid (NOT fixed — needs a new key).**

```
GET ws.audioscrobbler.com/2.0/ → HTTP 403
{"message":"Invalid API key - You must be granted a valid key by last.fm","error":10}
```

The key in `backend/.env` is **19 characters; Last.fm keys are 32**. Every song profile has been silently
returning zero tags, zero listeners, zero play count, and no wiki summary — `if 'error' in data: return
_empty()` swallowed it whole. `lastfm_client.py` now logs the API error code, an unset key, and request
failures separately. **Action: regenerate the key at last.fm/api/accounts and replace `LASTFM_API_KEY`.**
This invalidates the "wiki summary + play count display" line in the 2026-06-24 reflect — that feature is
currently dead in the running app.

**Flagged, deliberately not changed — `song_profile.py` calls the LLM twice.** `asyncio.gather` runs
Last.fm and a tag-less analysis concurrently; if Last.fm returns tags, the analysis is re-run grounded in
them and the first result is discarded. Today this costs nothing *because Last.fm is dead* and the second
call never fires. **Fixing the Last.fm key will silently double per-profile token spend.** The tradeoff is
latency (one sequential call after Last.fm resolves) vs. cost (two parallel calls, one wasted) — a product
decision, so it was left alone. Revisit at the same time as the key.

**H2.3 model IDs:** `claude-sonnet-4-6` → `claude-sonnet-5` (`services/llm_client.py`);
`claude-haiku-4-5-20251001` → `claude-haiku-4-5` (`routers/llm_connect.py`). Pure ID swaps — the call
sites pass no `temperature` or `thinking`, so no breaking changes applied. OpenAI (`gpt-4o`) and Groq
(`llama-3.3-70b-versatile`) left as-is.

**H2.4:** deleted `routers/recommendations.py` and its `main.py` registration; `/get-recommendations/` is
gone from the route table. `recommendations.svelte` and `lib/index.js` remain for C1 to remove as a set.

**Testing note.** The BYOK design means the server never holds provider keys, so cross-provider coverage
is synthetic — `tests/test_llm_parsing.py` encodes the malformed shapes (fenced, prose-wrapped, wrapped in
an object, lowercase score keys, string scores, `true` as a score, missing axes, array-instead-of-object,
entries missing title/artist). Uses stdlib `unittest`; no new dependency.

**Still open in H2:** one live pass per provider (Claude / OpenAI / Groq) with real keys, confirming each
round-trips a song profile and a playlist generation. A few minutes in the browser once connected to each.

### K1 result — session cookie retired, LLM key moved to headers (2026-08-03)

**Done:** K1.1–K1.4. K1.5 (browser BYOK round-trip) needs a real key and is the only step left.
Verified against the running local instance; nothing committed.

**New `services/llm_auth.py`.** Two FastAPI dependencies over `X-LLM-Provider` / `X-LLM-Key`:

- `get_llm_credentials` — required; raises 401 with an actionable message. Used by `/llm/generate-playlist/`.
- `get_optional_llm_credentials` — returns `None` when absent, so `/song/profile/` keeps degrading to
  Last.fm-only data instead of failing.

Both normalise the provider to lowercase and reject anything outside `claude|openai|groq` with a 400 that
names the valid values (previously an unknown provider reached `LLMClient.generate` and surfaced as a
generic `ValueError`).

**`routers/llm_connect.py` — rewritten as pure validation.** It checks the key against the provider and
discards it; the `request.session['llm_api_key']` write is gone. Returns `{connected, provider}`.

**`/llm/status/` deleted.** It only reported whether the server session held a provider. With no session
there is nothing to report, and the client already knows — `grep` confirmed nothing in the frontend called
it. Restorable as a pure header echo if the iOS client ever wants a connectivity ping.

**`main.py` / `config.py`.** `SessionMiddleware` and `SESSION_SECRET_KEY` removed (also from
`.env.example`; an existing `.env` can drop the line, nothing reads it). `allow_credentials=True` dropped
from CORS — no cookies cross the boundary now.

**Frontend — new `lib/llmHeaders.js`.** Reads the existing `llmConfig` store and returns the two headers,
or `{}` when nothing is connected. Applied in `ChatInterface.svelte`, `SongProfile.svelte`, and
`routes/+page.svelte`; `LLMSettingsPanel.svelte` drops `credentials: 'include'` from the connect call.
Needs the `@returns {Record<string, string>}` JSDoc — without it TypeScript infers the empty branch as
`{'X-LLM-Provider'?: undefined}`, which is not a valid `HeadersInit`, and svelte-check errors at all three
call sites.

**Verification:**

| Check | Result |
|---|---|
| No headers → `/llm/generate-playlist/` | 401, actionable detail |
| `X-LLM-Provider: gemini` | 400, lists valid providers |
| No headers → `/song/profile/` | 200, degrades, `analysis_error: null` |
| Valid provider + syntactically-valid bogus key | `authentication_error: API key is invalid` **from Anthropic** |
| `python -m unittest discover tests` | 35 pass |
| `npm run check` | 25 → 22 errors; zero mention `llmHeaders` (22 is the pre-existing baseline) |

The bogus-key row is the load-bearing one: a 401 raised by Anthropic rather than by our own dependency
proves the header travels end to end. It also demonstrated H2's error surfacing in the same response —
`returned: 0` with a populated `error` field rather than a silent empty playlist.

**Consequence for users:** the old session cookie is meaningless, so the LLM key must be re-entered once
in the settings panel. There is no migration path and none is needed — the key was always client-held.

**Open question resolved:** `/llm/status/` does not survive the migration (was listed under Open Questions
in the 2026-08-03 plan).

**Remaining in P0:** H1 (account integration — needs a browser session), D1 (hosted deploy + device key),
C1 (dead-code sweep, expanded by the V1 findings). K1.5 folds into whichever session next has a key to hand.

### Spotify February 2026 migration audit (2026-08-03)

Triggered mid-H1 by repeated 403s on Liked Songs. Root cause was Spotify's
[February 2026 Web API migration](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide),
which applies to **Development Mode apps**. Every endpoint below was probed against the live API with a
real user token — this table is measured, not inferred from the docs.

**Result: the backend was already migration-clean.** spotipy 2.26.0 had migrated ahead of us.

| Endpoint | Probe | App uses it? |
|---|---|---|
| `GET /me/library/contains` | 200 | ✅ via spotipy — the new saved-check |
| `PUT` / `DELETE /me/library` | 200 | ✅ via spotipy — the new save/unsave |
| `POST /playlists/{id}/items` | 400 (route exists) | ✅ spotipy's `playlist_add_items` targets `/items` |
| `POST /me/playlists` | 400 (route exists) | ✅ our `_post("me/playlists")` |
| `POST /me/player/queue` | 400 (route exists) | ✅ |
| `/me`, `/me/top/{artists,tracks}`, `/me/playlists`, `/me/player/recently-played` | 200 | ✅ |
| `GET /me/tracks/contains` | **403 removed** | not used |
| `PUT` / `DELETE /me/tracks` | **403 removed** | not used |
| `GET` / `POST /playlists/{id}/tracks` | **403 removed** | not used |
| `POST /users/{id}/playlists` | **403 removed** | not used — we use `me/playlists` |
| `GET /tracks?ids=` (batch) | **403 removed** | not used |
| `GET /search?limit=50` | **400 Invalid limit** (cap is now 10) | not used — default 10 / `limit=1` |
| `GET /audio-features` | **403** | used in `taste-over-time`; already degrades to `None` |
| `GET /me/library?limit=1` | 405 | write-only path; library reads still use `GET /me/tracks` (200) |

Response-shape changes were already absorbed: `p.get('items') or p.get('tracks')` covers the playlist
`tracks`→`items` rename, and `artist.get('popularity', 0)` absorbs the removed field.

**Correction to the record.** Mid-investigation this session, `current_user_saved_tracks_*` was
misdiagnosed as a spotipy bug (its `me/library` path looked wrong against pre-migration docs) and
"fixed" to `me/tracks/*` — which the migration *removed*. That change was the only thing that broke
Liked Songs; the resulting 403 was then misread a second time as stale OAuth scopes. Both wrong.
`user-library-read` was provably granted the whole time (`GET /me/tracks` returned 200 with the same
token). The revert is in place with a comment warning against re-applying the same "fix".

**The new library API, for reference** — keyed by Spotify **URIs**, passed as a **query parameter**:

```
GET    /v1/me/library/contains?uris=spotify:track:<id>[,...]   -> [true,false,...]
PUT    /v1/me/library?uris=spotify:track:<id>[,...]            -> 200
DELETE /v1/me/library?uris=spotify:track:<id>[,...]            -> 200
```

A JSON body is rejected: `PUT /me/library` with `{"uris": [...]}` returns
`400 Missing required field: uris`.

**Defect found and fixed (not migration-related).** `profile.py` indexed
`track['album']['images'][2]` unguarded — a 500 waiting for the first album art with fewer than three
sizes, and inconsistent with the guarded indexing everywhere else in the codebase. Now falls back to
the smallest available image. Verified 50/50 top tracks still resolve an image; 35 tests pass.

**Chunking retained** at 50 ids per saved-tracks request. The profile view sends exactly 50, so it sat
one track from the cap.

**Closes TA0.** `popularity` is removed API-wide by this migration, so there is no popularity signal to
recover for any app. The mainstream-ness module (TA1) stays dropped for a documented reason rather than
an observed-empty field.

**Premium requirement — confirmed satisfied.** The migration requires the app owner to hold active
Spotify Premium or a Development Mode app stops working. Owner has Premium (confirmed 2026-08-03). This
is also a hard prerequisite for P6 (Spotify iOS SDK playback control).

**Other constraints noted, not currently binding:** new Development Mode apps are capped at 5 users
(existing apps grandfathered); browse endpoints, artist top-tracks, other users' data, and `/markets`
are removed — none are used here.

**Implication for the iOS plan.** P2's Explore work was already replanned around this in the V1 block;
this audit confirms nothing further is at risk. The iOS client should call the same endpoints through
the backend rather than hitting Spotify directly, so it inherits spotipy's migration handling for free
— one more argument against the "no backend, iOS talks to Spotify directly" option rejected in the
brainstorm.

### H1 result — account integration exercised end to end (2026-08-04)

Driven from the browser with the backend teed to a log the assistant tailed, so failures were diagnosed
from server-side evidence rather than pasted console output. That setup is the reason this session found
four defects instead of one — worth repeating.

**Coverage (from the request log):**

| Endpoint | Calls | Outcome |
|---|---|---|
| `/spotify/saved-contains/` | 16 | 15 × 200, 1 × 500 (pre-fix "Too many uris") |
| `/spotify/queue/` | 12 | 200; final attempts genuinely queued |
| `/get-profile/` | 11 | 200 |
| `/spotify/playlists/` | 10 | 200 |
| `/spotify/taste-over-time/`, `/spotify/recently-played/` | 5 each | 200 |
| `/llm/generate-playlist/` | 2 | 200 |
| `/spotify/add-to-playlist/`, `/create-playlist/`, `/save-track/` | 4 | 200 |
| `/song/profile/` | 1 | 200, no warnings |

**Zero app-level warnings across the whole session** — no JSON parse failures, no Last.fm errors, no
unhandled exceptions. H2's parsing hardening handled a real provider response without needing any of its
fallback paths, and the `&` in a song title round-tripped correctly.

#### Bugs found and fixed

**1. `saved-contains` chunk size (500).** `_SAVED_TRACKS_LIMIT` was 50, inherited from the pre-migration
`/me/tracks` endpoints. The new `/me/library/contains` cap is lower — 50 URIs returns
`400 Too many uris requested`. Only surfaced with the profile view's full 50-track payload; earlier
8-id tests passed. The exact cap is undocumented and unprobeable (tokens no longer appear in the log),
so `_batched()` starts at 20 and halves on rejection, **remembering the reduced size** for later chunks.
Verified against simulated caps of 50/20/10/5/1 — always returns all results, order preserved, non-"too
many" errors still propagate. Confirmed live: 15 clean calls after the fix, no halving needed, so the
real cap is ≥ 20.

**2. Queue error classified by message text (500).** `queue_songs` matched on `'NO_ACTIVE_DEVICE' in str(e)`
or `'Player command failed' in str(e)`. Spotify returns **404 with at least two different messages** for
the same condition — `"Player command failed: No active device found"` and a bare `"Not found."` — and the
second fell through to a 500. Now branches on `e.http_status` (404 → `no_active_device`, 403 →
`premium_required`). Same failure mode as reading strings instead of structure elsewhere this session.

**3. Missing `user-read-playback-state` scope.** The app requested `user-modify-playback-state` (write)
but never its read counterpart, so `/me/player` and `/me/player/devices` returned
`401 "Permissions missing"`. Consequence: "Queue All" could never enumerate devices, target one via
`device_id`, or explain *why* a queue failed — only an opaque 404. Present since playback control shipped.
Added to `SCOPES`; **requires a full logout/login**, since a refresh preserves the original grant's scopes.
With it granted, Spotify also began returning the structured `"reason": "NO_ACTIVE_DEVICE"` field it had
been withholding.

**4. Unguarded `images[2]` in `profile.py`.** A 500 waiting for the first album art with fewer than three
sizes, inconsistent with the guarded indexing used elsewhere. Now falls back to the smallest available.

**Also landed:** partial queue runs report how many tracks were queued before the device dropped, instead
of reading as total failures, and the frontend surfaces that plus a distinct Premium message.

#### Not a bug

The original "Open Spotify on a device first" report was **correct behaviour**. The root cause was
environmental: every device on the account is an Amazon Echo or FireTV, and Alexa-initiated playback does
not register as an active Spotify Connect device the Web API can target. `GET /me/player` returned `204`
(nothing playing) while music was audibly playing. Starting playback in the Spotify **desktop app or web
player** registers an active device and queueing then succeeds — confirmed working.

#### Follow-up worth scoping (not done)

**Device picker for Queue All.** Now that devices are enumerable, "Queue All" could list them and pass an
explicit `device_id` rather than depending on an implicit active device — likely transferring playback
(`PUT /me/player`) first for an idle target. All seven of this account's devices report
`is_restricted: false`, so targeting may work, but Echo behaviour is untested. This is a feature, not a
fix; it would make the app usable with the speakers actually in the house.

**Queue is N sequential round-trips.** Spotify has no batch queue endpoint, so a 12-track queue is 12
sequential calls. The fix would be concurrency, not batching.

#### Status

H1 steps 1–7 pass. **Step 8 (deleting the leftover empty test playlists) is outstanding.** P0 is otherwise
complete apart from the deferred deploy (D1.3/D1.4).

### V1.2 closed — iOS redirect URI registered (2026-08-04)

`boominbeats://callback` added as a second redirect URI on the **existing** Spotify client ID
(`a700071d…0bc0`); the web app's `http://127.0.0.1:5173/profile` was left in place. Verified by issuing a
real PKCE authorize request against that redirect — Spotify rendered the consent screen rather than
`INVALID_CLIENT: Invalid redirect URI`. No new app was registered, so grandfathered endpoint access is
preserved.

This value must stay byte-identical in three places: Spotify's dashboard, `Config.redirectURI`
(`src/ios/BoominBeats/Config.swift`), and `CFBundleURLSchemes` in `src/ios/Info.plist`. Spotify does not
normalise case or trailing slashes.

**V1 is now fully closed.** V1.3 (Spotify iOS SDK accepts an externally obtained token) was answered in the
V1 result block; P6 remains additive rather than a second auth path.

### P1 result — iOS app running against the live backend (2026-08-04)

All P1 acceptance criteria met. Verified in the Simulator (iPhone 17 Pro, iOS 26.3) against the local
backend, not just compiled.

| Criterion | Result |
|---|---|
| Project builds | ✅ zero errors/warnings |
| PKCE login via `boominbeats://callback` | ✅ |
| Token persists across launches | ✅ relaunch went straight to Profile, no re-login |
| Profile renders real data | ✅ top artists + tracks |
| Time-range switching re-fetches | ✅ `long_term` → `short_term` observed in the backend log |
| Screenshot loop | ✅ `xcrun simctl io … screenshot` |

**Toolchain.** Xcode 26.3, Swift 6.2.4, iOS 26 deployment target, no third-party dependencies.
`project.pbxproj` is hand-written using a **file-system-synchronized root group**, so new files are picked
up from disk and the project file doesn't churn — worth preserving; it's the main reason the pbxproj
stayed reviewable without xcodegen.

**Two build-system traps, both cost real time — do not rediscover them:**

1. **Keychain needs the `keychain-access-groups` entitlement even in the Simulator.** Building with
   `CODE_SIGNING_ALLOWED=NO` skips applying `CODE_SIGN_ENTITLEMENTS`, and every `SecItemAdd` then fails
   `-34018 errSecMissingEntitlement`. Since `postToken()` writes the token, login fails at the last step.
   Confirmed by A/B-ing signed vs unsigned builds against a startup self-test — not by reasoning.
   Note `codesign -d --entitlements` shows an *empty dict* on a working Simulator build, so that dump is
   not a reliable check; the functional test is.
2. **`Info.plist` and the entitlements file must live outside the synchronized folder.** Inside it they
   are also copied as bundle resources, producing `Multiple commands produce … Info.plist`.

Also: a plain `-scheme` build fails with "iOS 26.2 is not installed" when only the SDK (not the runtime)
is present. `-target … -sdk iphonesimulator26.2` compiles fine — useful for compile-only verification
before a simulator runtime is available.

**Diagnostics.** A `#if DEBUG` Keychain self-test runs at launch and logs a write/read/delete round-trip,
readable from the host:

```
xcrun simctl spawn "iPhone 17 Pro" log show --last 1m --info --debug \
  --predicate 'subsystem == "com.ryanchristopher.boominbeats"' --style compact
```

`log show` omits info-level entries without `--info --debug`. This is the text-driven path for verifying
behaviour that can't be clicked, and it's what turned the Keychain failure into a one-line answer.

**Error-message defect fixed along the way.** `Keychain.Error` had no `LocalizedError` conformance, so a
failure surfaced as `"Keychain.Error error 0"` — the enum case index, not the `OSStatus`. It now reports
the status and Apple's own description, with a specific hint for `-34018`.

**Open question raised by the running app.** No genres render under any artist, and the view only hides
that line when `artist.genres` is empty. If the February 2026 migration removed `genres` from the artist
object — as it did `popularity` and `followers` — then the **web app's genre radar and genre-depth
modules are silently empty too**, and P5 would inherit it. Unverified; needs one call to settle.

**Not yet done in P1:** the Settings screen's LLM provider/key fields (deferred to P3, which is where
they're first needed).
