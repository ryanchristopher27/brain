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

---

# Plan — AI DJ Companion
Date: 2026-10-23
Status: Active
Brainstorm: `docs/brainstorm.md` → "AI DJ Companion (2026-10-17)"
Depth: high-level for DJ1–DJ6; **DJ0 at task level** (it is the immediate next work, and its results
gate DJ2 and DJ5)

---

## Overview

A DJ companion inside the iOS app. Music plays through the host's Spotify, and Boomin Beats gives
them a clean now-playing view with playback control. They build the queue themselves, with
suggestions offered as **moves** (Hold / Lift / Drop / Pivot / Curveball / Bridge) and an
adjustable AI control level. Hosting is the main use, and solo listening works the same way.

This is `ROADMAP.md` goal #4, reframed as a companion: the host builds the queue and the AI
suggests. The design follows the native-iOS plan's rules: one stateless backend, two deployments,
and per-request tokens and keys. **No database is introduced.** All DJ state (queue, settings,
feedback, do-not-play list) lives on the device and is sent to the backend with each request.

**How it relates to the iOS milestones:**
- **P1.5 (now-playing widget):** DJ1 builds the now-playing model the widget would read, so P1.5
  becomes a thin layer on top of it.
- **P3 (playlist builder):** P3 owns the iOS LLM key settings. DJ3 needs them first, so that one
  piece moves forward into DJ3.
- **P6 (iOS SDK playback):** stays an optional later upgrade for DJ1 if the Web API path turns out
  to be too slow (see DJ0.2).

---

## Goals & Success Criteria

| Goal | Success Criteria |
|------|-----------------|
| Clean now-playing + control | Track, artist, art and progress update within ~2s of a change made anywhere (Spotify app, Jam, another device); play/pause/skip/previous work from the app |
| Editable queue | Reorder, remove and insert all work; Spotify never runs dry while the app is in the foreground |
| Useful moves | Every track gets at least 3 move-labelled suggestions, all real Spotify tracks, ready **before** the host opens the panel (prefetched) |
| Adjustable control | All four control-dial modes behave differently; changing adventurousness visibly changes the suggestions |
| Survives a party | A 2-hour session with party mode on: no dead air, no lost queue after briefly backgrounding the app |
| Guest requests (stretch) | Songs guests add via Spotify show up in a Requests inbox and can be approved into position |

---

## Scope

### In Scope
- Now-playing view and playback control (iOS)
- App-owned queue, a Spotify buffer of tracks sent ahead (default 5, adjustable), and party mode
  (keeps the screen awake)
- `/dj/suggest/` backend endpoint: moves → LLM + Last.fm tags → validated Spotify tracks
- Control dial (Whisper / Co-pilot / Autofill / Driver) and an adventurousness slider
- Skip and quick-tap feedback, applied within the session
- Bridge / arc goals ("end up in 90s R&B", "peak energy in 30 min")
- Clean-lyrics toggle and a do-not-play list
- Requests inbox for guest additions (DJ5, lower priority, design depends on the DJ0 result)

### Out of Scope
- Any backend database or server-side session. If the guest-request test fails, the QR-code request
  page fallback is **deferred**, not built here.
- A backend worker that advances the queue while the app is backgrounded (needs stored refresh
  tokens)
- Beatmatching, harmonic mixing, or crossfade control: no audio features, so transition advice stays
  at vibe level
- Providers other than Spotify. Apple Music would be a separate plan.
- The web app. iOS first; the backend endpoint is reusable by the web app later at no extra cost.

---

## Tech Stack & Architecture

**Backend: new `routers/dj.py` and `routers/player.py`, both stateless.**
- `player.py` provides thin wrappers over `/me/player`: state, play, pause, next, previous, and the
  queue read. They reuse the 404 → `no_active_device` / 403 → `premium_required` mapping from
  `queue_songs`. The existing `/spotify/queue/` handles adding tracks.
- `dj.py` exposes `POST /dj/suggest/`. Each request carries the full context: current track, the last
  N played, the upcoming queue, control settings, the feedback signals, the do-not-play list, the
  clean flag, and an optional Bridge target. The flow is Last.fm tags (`lastfm_client.py`) → LLM
  (`llm_client.py`, parsed with `llm_json.py`) → validation through Spotify search
  (`spotify_validator.py`) → moves with tracks.
- The vibe signal comes from Last.fm tags plus the LLM's own estimate. **Not** Spotify genres: the
  P1 result left open whether the Feb 2026 migration removed `artist.genres`, so the DJ doesn't
  depend on them.

**iOS: a `DJ/` feature folder** (picked up automatically by the file-system-synchronized group).
- `NowPlaying`: polls player state, roughly every 2s while the app is in the foreground, plus a
  refresh scheduled at the expected end of the track.
- `QueueStore`: the app-owned queue, persisted to disk so a relaunch doesn't lose it. It **tops up
  the Spotify buffer** to N tracks ahead (default 5, adjustable in Settings) and **reconciles** with Spotify's queue whenever the app
  returns to the foreground.
- `SuggestionStore`: prefetches `/dj/suggest/` on every track change and caches results by track id
  and settings.
- Party mode sets `UIApplication.isIdleTimerDisabled` while it is on.

**Playback path: Web API through the backend (recommended, confirm in DJ0.2).** Chosen over Spotify
App Remote because:
- the backend already handles the player endpoints and the Feb 2026 migration quirks
- App Remote would be the app's first third-party dependency
- App Remote's connection drops when the app is backgrounded, so it doesn't fix the backgrounding
  problem either

App Remote stays the P6 upgrade path if polling feels too slow.

**Why an app-owned queue:** Spotify's queue only accepts additions, both in the Web API and in App
Remote. An editable queue therefore has to live in Boomin Beats, with tracks sent to Spotify only
just before they play. The buffer depth trades resilience against editability: tracks already sent
can't be edited, while a deeper buffer keeps playing longer if the app is suspended. The default is 5
(about 15–20 minutes of music) because hosting values never running dry. To soften the edit cost,
removing or moving a track that is already in the buffer marks it **skip-on-arrival**: when it comes
up while the app is in the foreground, the app calls `next` and plays the track in its new place
later.

---

## Milestones

| # | Milestone | Description | Dependencies |
|---|---|---|---|
| DJ0 | Spikes | Can guest additions be seen in the queue read? Playback path, suggestion latency. Results recorded here. | — |
| DJ1 | Now playing + playback control | `player.py`; iOS now-playing view with play/pause/skip/previous; no-device and Premium errors surfaced | DJ0 |
| DJ2 | App-owned queue | `QueueStore`, buffer top-up, reconcile on return to foreground, reorder/remove/insert UI, party mode | DJ1 |
| DJ3 | Move suggestions | `/dj/suggest/`, the move contract, iOS LLM key settings (moved forward from P3), prefetch + cache, tap to queue | DJ2 |
| DJ4 | Control dial + feedback | Four modes, adventurousness, skip/tap feedback, do-not-play list, clean toggle | DJ3 |
| DJ5 | Requests inbox | Flag Spotify-queue tracks the app didn't send → inbox → approve into position | DJ2, DJ0.1 result |
| DJ6 | Bridge + arc planning | A named destination or an energy arc over N minutes, built on the Driver mode | DJ4 |

DJ5 depends only on DJ2. It can move ahead of DJ3/DJ4 if guest requests become more important.

---

## Task Breakdown — DJ0 (spikes)

Each spike is a short probe against the live API, with the result recorded in this section. Same
approach as the Feb 2026 migration audit: measured, not inferred from docs.

**DJ0.1: Can guest additions be seen in the queue read?** (gates DJ5)
1. Start a Spotify Jam from the host account. Add tracks from a second account.
2. Call `GET /me/player/queue`. Do the guest's tracks appear, and in what order?
3. Queue a track from the host's own Spotify app. Is it distinguishable from tracks coming from the
   playing context (playlist, album, autoplay)? Check whether the response tags context tracks, or
   whether they can be inferred from `currently_playing.context`.
4. Record a verdict: **comparison works** / **works with caveats** (write the caveats down) /
   **doesn't work** (DJ5 drops back to the deferred QR fallback).

**DJ0.2: Playback path** (gates DJ1)
1. Time `GET /me/player` through the hosted and local backends from the Simulator. Target: under
   500 ms end to end.
2. Check how quickly a skip made in the Spotify app shows up through polling every 2s.
3. Verdict: Web API is adequate, or App Remote is needed (which would pull part of P6 forward).

**DJ0.3: Suggestion latency and cost** (shapes DJ3)
1. Prototype the `/dj/suggest/` prompt with the current BYOK providers. Measure time to a validated
   result for 3 moves × 2 tracks each, counting the Spotify validation calls.
2. Note tokens per call. Decide whether prefetching on every track change is affordable or should be
   rate-limited (for example only in Co-pilot mode and above).

**DJ0.4: Verify the hosted instance status** (gates real-world use away from the Mac's network)
1. Check whether P0/D1 (hosted deploy + device key) is live and the iOS app can point at it. If it
   isn't, DJ work proceeds against the local backend, and party use outside home waits on D1.

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Guest additions can't be seen or told apart in the queue read | Medium | Medium (DJ5 only) | DJ0.1 checks before any design work; fallback deferred, core loop unaffected |
| App suspended → buffer runs out → Spotify falls back to autoplay | Medium | Medium | Party mode in the main use case; buffer of 5 by default; reconcile on return to foreground |
| Host plays something directly in Spotify, which breaks the app's queue model | High | Medium | Reconcile treats Spotify as the source of truth for "now playing"; app-owned items are kept, not dropped |
| LLM suggests tracks that don't exist or wrong versions | High | Low | Validate through Spotify search (`spotify_validator.py`); drop tracks that fail, ask for extras to cover drops |
| Suggestion latency at a party | Medium | High | Prefetch on track change; cache; show previous suggestions while new ones load |
| Polling cost / rate limits | Low | Medium | Poll only in the foreground; back off when paused; one host = one user |
| BYOK cost of a prefetch on every track | Medium | Low | DJ0.3 measures it; Whisper mode never prefetches |

---

## Dependencies

- Spotify Premium on the host account (confirmed 2026-08-03)
- Existing iOS scopes already include `user-read-playback-state` and `user-modify-playback-state`, so
  **no re-auth is needed**
- `LASTFM_API_KEY` set on whichever backend instance the iOS app uses
- A BYOK LLM key on iOS (delivered in DJ3, moved forward from P3)
- P0/D1 hosted instance, for use away from the Mac (DJ0.4)
- A second Spotify account for the DJ0.1 Jam test

---

## Open Questions

- Does the do-not-play list sync with the web app eventually? (Not without state; on-device for now.)
- Should approving a guest request ask "next" vs "later", or let the AI choose the position in
  Autofill and above?
- Is a Live Activity on the lock screen worth folding into DJ1, or does it stay with P1.5?
- In Driver mode, does the AI add to the buffer silently, or always show a toast with undo?

---

## Decisions Log

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Platform | iOS first | Hosting = phone in hand; P1 shell exists | 2026-10-17 |
| Product home | Feature of Boomin Beats, not a new app | Reuses auth, LLM, Last.fm, validation, queue endpoint | 2026-10-17 |
| Guest requests | In scope, low priority, through the provider app | Avoids guest accounts and backend state | 2026-10-17 |
| Queue model | App-owned; ~~Spotify buffer of 5 by default~~ **adaptive (2026-10-23, DJ2): 1 track ahead while the app is in the foreground, topped up to N (default 5, Settings 1–10) when it goes to the background**; skip-on-arrival for edits to tracks already in the buffer | Spotify's queue only accepts additions. User chose a deeper buffer than 2–3: never running dry matters more than full editability when hosting | 2026-10-23 |
| Adventurousness | Separate setting from the control dial | Lets the AI act often and stay safe, or act rarely and swing big | 2026-10-23 |
| Guest-request sequencing | After DJ2, not blocking DJ3/DJ4 | Core loop first; DJ5 can move up because it depends only on DJ2 | 2026-10-23 |
| Playback path | Web API through the backend (confirm in DJ0.2) | Already migration-clean; no SDK dependency; App Remote doesn't fix backgrounding | 2026-10-23 |
| State | On-device only; full context in each request | Keeps the backend stateless, which the two-deployment design relies on | 2026-10-23 |
| Vibe signal | Last.fm tags + LLM, not Spotify genres | audio-features/recs are dead; `genres` possibly removed (P1 open question) | 2026-10-23 |
| Milestone prefix | `DJ#` | Avoids colliding with the iOS plan's `P#` ids in the tracker | 2026-10-23 |

### DJ0 result — spikes (2026-10-23)

Measured against the live API from the web app's signed-in session (local backend, MacBook as the
playing device, a 2,480-track playlist with shuffle on). Three of four spikes are closed. The Jam
half of DJ0.1 is deferred.

| Spike | Verdict |
|---|---|
| DJ0.1 Guest additions visible in the queue read | **Partial: comparing queues works, with about a one-song delay.** The Jam half is not run yet. |
| DJ0.2 Playback path | **Web API through the backend is adequate.** App Remote is not needed for DJ1. |
| DJ0.3 Suggestion latency | **About 3s for 6 validated tracks, so prefetch on track change works.** |
| DJ0.4 Hosted instance | **Not live.** D1.3/D1.4 were deferred in P0. DJ work runs against the local backend. |

**DJ0.2 numbers** (median / max over 5 calls, measured from the browser):

| Call | Median | Max |
|---|---|---|
| `GET /me/player` (Spotify direct) | 144 ms | 283 ms |
| `GET /me/player/queue` (Spotify direct) | 392 ms | 550 ms |
| Local backend round trip (`/spotify/recently-played/`) | 266 ms | 435 ms |

`GET /me/player` returns `device`, `shuffle_state`, `smart_shuffle`, `repeat_state`, `is_playing`,
`timestamp`, `context`, `progress_ms`, `item`, `currently_playing_type` and `actions`. That covers
everything the now-playing view needs. Skip-propagation latency was not measured; it was folded
into the deferred Jam session.

**DJ0.1 findings:**
- `GET /me/player/queue` returns `{currently_playing, queue}`, with exactly 20 items. Items are
  plain track objects with **no source marker**: nothing says whether a track was user-queued or
  comes from the playing context.
- `POST /me/player/queue` puts the track at **index 0 immediately**, and the rest of the queue
  shifts down by one. User-queued tracks therefore come before context tracks, in first-in,
  first-out order.
- The context playlist is readable (`GET /playlists/{id}/items` → 200). A membership check is
  possible but costs about 50 pages for a 2,480-track playlist, so the track list must be cached
  per context.
- **What this means for DJ5:** the app's buffered tracks sit at the front of the queue. A
  non-app track that appears *between* app tracks is definitely a guest add. A guest add after the
  app's last buffered track can't be distinguished from a context track until the next buffer
  top-up wedges it in, which is about a one-song delay. Checking context membership closes that gap.
- **Still unverified:** whether tracks added by a Jam participant show up in the host's
  `GET /me/player/queue` at all. That needs a second account. **Run it before DJ5 starts.** DJ1–DJ4
  don't depend on it.

**DJ0.3 numbers:** `/llm/generate-playlist/` used as a stand-in for `/dj/suggest/`. A Hold/Lift/Pivot
prompt asking for 6 tracks took 2.9 / 3.5 / 2.8 s, and 6/6 tracks were validated each run. That
includes Spotify validation. Provider: Groq `openai/gpt-oss-120b`. A track lasts about 3–4 minutes,
so prefetching on every track change leaves plenty of headroom.

**Quality note for DJ3:** with only "now playing" as context, the picks were mainstream and
generic (Levitating, Get Lucky). DJ3's request contract must carry recent history, Last.fm tags,
the do-not-play list, and adventurousness to be worth more than autoplay.

**Defect found and fixed (not DJ-related):** `llm_client.py` called Groq model
`llama-3.3-70b-versatile`, which Groq has retired (`404 model_not_found`). **Every Groq-backed
feature was broken**: the playlist builder, song profile analysis, and discovery. Replaced with
`openai/gpt-oss-120b`, the closest available quality match on this key. The other active models
were `openai/gpt-oss-20b` and `qwen/qwen3.8-27b`. The 35 unit tests pass, and the change was
verified live (3/3 runs). The Claude (`claude-sonnet-5`) and OpenAI (`gpt-4o`) model ids were not
re-checked.

**Probe side effect:** one track ("Feeling Good", Michael Bublé) was added to the owner's live
queue during the DJ0.1 test.

### DJ1 result — now playing + playback control (2026-10-23)

Built and verified in the Simulator (iPhone 17 Pro) against the local backend, with the MacBook as
the playing device.

**Backend: `routers/player.py`.**
- `GET /player/state/` returns normalized state: track in the same shape as `/get-profile/` tracks
  but with the *largest* image, device, `context_uri`, progress plus Spotify's `timestamp`, and a
  `disallows` list. It returns `{active: false}` when nothing is playing. Episodes and ads return
  `track: null`.
- `GET /player/queue/` is the queue read (for DJ2/DJ5).
- `POST /player/{play,pause,next,previous}/` return `{ok: true}`, or `{error: ...}` with status 200
  for expected failures, the same convention as `/spotify/queue/`.
- 9 unit tests are in `tests/test_player.py` (44 total, all pass).

**Error mapping fixed relative to the plan.** The plan said to reuse `queue_songs`' 403 →
`premium_required` mapping. Live testing showed that's wrong: a second `pause` returns
**403 with reason `UNKNOWN`** (a restriction violation), not Premium. `player_error` therefore maps
403 to `premium_required` only when `reason == PREMIUM_REQUIRED`, and otherwise to
`restricted` + reason. **`queue_songs` still has the old mapping and will misreport restrictions as
Premium.** ~~That fix is not applied yet.~~ **Fixed the same day:** `queue_songs` now returns
`{**player_error(e), 'queued': n}`. `PlaylistResult.svelte` also gained an `else if (data.error)`
branch. Without it, its final `else` would have shown `restricted` as a *successful* queue.

**iOS: `DJ/NowPlayingModel.swift` and `DJ/NowPlayingView.swift`.** `RootView` is now a `TabView`
(Now Playing first, Profile second).
- Polls every 2s while the scene is active, and wakes about 0.3s after the expected end of the
  track. It polls every 5s when nothing is playing, and stops in the background (`.task(id:
  scenePhase == .active)`).
- Progress is interpolated locally between polls (a `TimelineView` at 0.5s).
- After a command it waits 400 ms and re-reads, because Spotify's state lags briefly. Buttons are
  disabled from `disallows`.

| Check | Result |
|---|---|
| Real track, art, artists, progress, device | ✅ |
| Pause / play from the app | ✅ confirmed by Spotify's own `is_playing` |
| Previous / next from the app | ✅ |
| Skip made outside the app shows up | ✅ within about 2s |
| Backend latency (warm) | 200–300 ms for state and queue, about the same as calling Spotify directly |
| "Nothing playing" / no-device states | ⚠️ built, not exercised live (would need Spotify fully stopped) |

**Cold-start latency:** the first calls right after the uvicorn reload took 7.4s (state) and 10.5s
(queue), then dropped to warm numbers. This is consistent with the stale-pooled-connection behaviour
documented in `services/spotify_client.py`. Worth watching. It's not a DJ1 defect unless it recurs
on a warm process.

### DJ2 result — app-owned queue (2026-10-23)

**Deviation, confirmed by the owner before building:** the buffer is **adaptive**, not a fixed 5.
While the app is in the foreground it keeps 1 track ahead in Spotify, so everything after the next
song stays freely editable. When the scene goes to `.background`, it tops up to
`Config.backgroundBufferDepth` (default 5, adjustable 1–10 in Settings), using a
`beginBackgroundTask` window. Known ceiling: if iOS kills the app with no background transition,
Spotify falls back to autoplay after 1 song.

**What was built (iOS only, no backend changes):**
- `DJ/QueueStore.swift` has two lists: `sent` (handed to Spotify, in order) and `upcoming`.
  - It is persisted to `Application Support/queue.json` on every change.
  - `observe(state)` runs on each track change. Arriving at `sent[i]` drops `sent[0...i]`, skips
    (calls `next`) if that item was marked skip-on-arrival, then tops up.
  - `reconcile(with:)` runs on each return to the foreground. It replays `observe` against the
    current track, then filters `sent` against `GET /player/queue/` in order (so duplicates are
    matched correctly).
  - Top-up counts only non-skipped items, so removing a sent track immediately sends a replacement.
- `DJ/QueueView.swift` is a new **Queue** tab:
  - "Sent to Spotify" section, where a swipe offers Remove or Later (both are skip-on-arrival;
    Later re-adds a copy to the end of Up Next).
  - "Up Next" section with drag-to-reorder and swipe-to-delete.
  - A + button opens a search sheet using `/search/` with a 300 ms debounce.
  - A party-mode toggle (`isIdleTimerDisabled`, deliberately not persisted).
- **Polling moved up** from `NowPlayingView` to `MainTabs` in `RootView.swift`. A tab's own `.task`
  is cancelled when the user switches tabs, which would have stopped top-ups while the Queue tab was
  showing. The models are shared through the environment.
- The Settings screen has a "Queue When Backgrounded" stepper.

**Verified against live Spotify** (checked with `GET /me/player/queue` after each step):

| Check | Result |
|---|---|
| Add 3 tracks in the foreground → exactly 1 sent, 2 kept in Up Next | ✅ |
| Remove a sent track → marked "Will be skipped", replacement sent immediately | ✅ |
| Removed track comes up → auto-skipped within about 1s, next track plays, buffer refills | ✅ |
| Go to the background with 1 sent + 3 waiting → all 4 sent, in order | ✅ |
| 2 tracks play while away → on return, the app drops them and matches Spotify's queue | ✅ (also loaded from disk after relaunch) |
| Party-mode toggle and banner | ✅ UI. The idle-timer effect itself can't be observed in the Simulator. |
| Drag-to-reorder Up Next, "Later" swipe, Settings stepper | ⚠️ built, not exercised |

**Behaviour to know about:** a skip-on-arrival track plays for about 1 second before the poll
catches it (poll interval plus command latency). That's acceptable for hosting, and DJ5 shouldn't
make it worse.

### DJ3 result — move suggestions (2026-10-23)

**Backend: `routers/dj.py`, `POST /dj/suggest/`.**
- Request: `{now_playing, recent[], upcoming[], per_move=2}`. Each entry is a `TrackRef {id, title,
  artist}`.
- Flow:
  1. Last.fm tags for now playing (top 8).
  2. One LLM call returning `{move: [{title, artist, reason}]}` for the five moves (Hold / Lift /
     Drop / Pivot / Curveball). It asks for `per_move + 1` per move so validation drops don't leave
     a move short.
  3. `validate_songs` in parallel.
  4. `select_tracks` drops wrong-artist matches, excluded ids (now playing, recent and upcoming) and
     duplicates across moves. The wrong-artist case comes from the title-only fallback in
     `validate_songs` landing on a different artist's song; artist names are compared ignoring case
     and punctuation, so "Tyler, The Creator" matches "tyler the creator".
- Response: `{moves: [{move, tracks: [{id, title, artists, image, reason}]}], tags, error}`.
- Bridge was deferred to DJ6, since it needs a destination.
- 6 unit tests are in `tests/test_dj.py` (50 total, all pass).

**iOS.**
- `Config.llmProvider` / `Config.llmKey` are stored in the Keychain, using the keys that already
  existed in `Keychain.Key`. Settings has an **AI** section. `APIClient` sends `X-LLM-Provider` /
  `X-LLM-Key` whenever a key is set.
  - This brings forward the "LLM provider/key fields" that the P1 result deferred to P3, as planned.
- `NowPlayingModel.recent` keeps the last 10 tracks seen this session.
- `DJ/SuggestionStore.swift` loads suggestions and caches them per track id. It is prefetched from
  `MainTabs` with `.task(id: track id)`, so it runs whichever tab is showing and a track change
  cancels a stale load.
- `NowPlayingView` is now a `ScrollView`: smaller art, then a **Next Moves** section with a refresh
  button and a + button per pick that queues it through `QueueStore.add`.

| Check | Result |
|---|---|
| No key → helpful prompt instead of an error | ✅ |
| 5 moves × 2 validated picks with reasons, rendered | ✅ every run |
| Quality | ✅ clearly better than the DJ0 stand-in. Picks follow the room (R&B / alt-rap → Solange, Frank Ocean, Masego, Burna Boy, Janelle Monáe), not chart hits. |
| Already-queued tracks never suggested | ✅ |
| Tap + → lands in Up Next (or is sent if the buffer is empty) | ✅ |
| Prefetch on track change while on another tab | ✅ new set ready on arrival, no refresh needed |
| Latency | ⚠️ **about 6.5s** per call (DJ0.3 estimated about 3s). The extra time is the Last.fm lookup plus a larger prompt. Prefetch hides it, but a manual refresh feels slow. |

**Known gap: recent history doesn't survive a relaunch.** `recent` lives in memory, so after a
relaunch a song played earlier can come back as a suggestion. It was observed live: "Redbone"
reappeared as a Pivot. Cheap fix: seed `recent` from the existing `/spotify/recently-played/` on
launch. Not done in DJ3. It fits DJ4, alongside the do-not-play list.

### DJ4 result — control dial + feedback (2026-10-23)

**Decided before building:** until DJ6 adds goals, Driver = keep 3 tracks lined up, choosing the
moves itself.

**Backend (`routers/dj.py`).**
- `SuggestRequest` gains these fields, all optional so a DJ3 client still works: `adventurousness`
  (0–1, shapes the prompt as safe / balanced / bold), `clean`, `liked` / `disliked` / `skipped`,
  `avoid_tracks` and `avoid_artists`.
- Hard filters in `select_tracks`: explicit tracks when `clean`, and do-not-play artists matched
  against *any* credited artist. The prompt asks for both too; the filters are the guarantee.
  `spotify_validator._format_track` now includes `explicit`.
- **History survives relaunch:** the endpoint pulls the user's last 20 Spotify plays
  (`current_user_recently_played`) and merges them with the client's session history. All of them
  are excluded from suggestions; the 15 most recent go into the prompt. This closes the DJ3 gap.
  Caveat: Spotify only logs plays longer than about 30s, so a track auto-skipped after 1s still
  counts as "never played".
- With clean on, the prompt asks for one more per move, because the filter emptied whole moves when
  it asked for only one extra.
- **`salvage_truncated`:** recovers every complete entry from a cut-off reply. A clear
  "reply was cut off" message replaces the raw-JSON error.
- 12 new tests (56 total, all pass).

**iOS.**
- `DJ/DJSettings.swift` (persisted in UserDefaults) holds the mode, adventurousness, clean-only, and
  the do-not-play tracks and artists.
- `NowPlayingModel` tracks session `skipped` (left before halfway, excluding the queue's own
  auto-skips) and `liked` / `disliked`.
- `SuggestionStore`:
  - The cache key includes adventurousness bucket + clean.
  - An in-flight guard keyed by that cache key stops repeated taps from stacking requests, while
    still letting a track change start its own load.
  - `autopilot()` serves Autofill (1 lined up) and Driver (3). Picks are interleaved across moves
    ordered by adventurousness (safe → hold/lift/drop, bold → pivot/curveball first) and marked
    `addedByDJ`.
- `QueueItem.addedByDJ` is **optional** so pre-DJ4 `queue.json` still decodes; synthesized Codable
  ignores default values. Queue rows show a ✦ badge on DJ picks.
- Now Playing has a DJ card (mode picker, Safe↔Bold slider, Clean only), 👎/👍 buttons that refresh
  immediately, and a ⋯ menu per pick: "Never suggest this song / this artist".
- Settings has a **Do Not Play** list with swipe-to-remove.

**Deviation, made during the build:** the plan had "long-press a suggestion" for do-not-play. That
became a visible **⋯ menu** per pick. The context menu couldn't be triggered from the Simulator, and
a visible control is easier to find mid-party anyway.

| Check (live, Simulator) | Result |
|---|---|
| Whisper → no prefetch, "Get moves" button | ✅ |
| Co-pilot → suggestions as in DJ3 | ✅ |
| Autofill with an empty queue → 1 pick added with ✦, sent to Spotify | ✅ |
| Driver → 3 lined up (The Recipe / DNA / Tadow: three different moves) | ✅ |
| 👎 → icon fills, suggestions refresh | ✅ |
| ⋯ → Never suggest artist → appears in Settings › Do Not Play | ✅ |
| Safe vs Bold change the picks (backend, live) | ✅ Safe: Frank Ocean / Leon Bridges / Nina Simone. Bold + clean: Kavinsky / Mazzy Star / James Blake, with avoided artists absent. |
| Cut-off reply → partial moves or a clear message | ✅ both seen live |
| Skip detection feeding `skipped` | ⚠️ built, not observed directly |

**Groq budget: the cut-off replies come from Groq's token limit, not from our code.**
- `openai/gpt-oss-120b` on Groq's on-demand tier allows **8,000 tokens/min**.
- A measured `/dj/suggest/` call used **3,237 tokens, 1,924 of them hidden reasoning**. That's about
  2 calls/min.
- Replies were cut off at about 1,400 characters while the budget was spent, with `finish` still
  reported as `stop` on the successful ones.
- Measured directly against Groq, `reasoning_effort: "low"` cut reasoning from 482 to 30 tokens on a
  comparable prompt, and latency from 3.0s to 2.0s.
- **Pending the owner's OK:** set `reasoning_effort='low'` in `llm_client._generate_groq`. That file
  is shared with the playlist builder and song profile.

**Side effect of testing:** Driver queued DNA and Tadow for real on the owner's account. They're in
Up Next and can be swiped away.

### DJ4 addendum — Groq effort, and the Spotify search rate limit (2026-10-23)

**Groq `reasoning_effort='low'`, applied with the owner's OK** in `llm_client._generate_groq`. This
is shared, so the playlist builder and song profile get it too.
- DJ call: about 6.5s → **about 3s** end to end, with the LLM step at about 2.5s.
- Playlist builder: **1.3s**.
- Direct prompt: about 800 tokens instead of about 3,200.
- Side effect: thinner validated results (11–13 of 15 picks matched, and Curveball came back empty
  twice), so `_OVERASK` went from 1 to **2**.

**Incident: Spotify rate-limited search app-wide for about 23 hours.**
- `GET /v1/search` returned `429` with `Retry-After: 82363` for both the client-credentials token
  and the user token. Player endpoints were unaffected.
- Cause: DJ testing volume. Each `/dj/suggest/` ran 20–50 searches (validation, plus the title-only
  fallback), across many calls in about 20 minutes.
- **Everything that searches is down until about 2026-10-24 21:15 CDT:** DJ suggestions, the
  playlist builder, Explore, and search-to-add on iOS and the web.

**Latent bug the incident exposed: one 429 could hang the backend for hours.**
- urllib3's `Retry.is_retry` honours `Retry-After` on 429 *even when 429 isn't in
  `status_forcelist`*. Read in the urllib3 2.7.0 source.
- spotipy builds its own `Retry`, so every searching request slept for 23h in a worker thread.
- `uvicorn --reload` then couldn't restart, because graceful shutdown waited on those threads. The
  worker had to be `kill -9`'d twice.
- **Fix (`services/spotify_client.py`):** both clients get our own `requests.Session` with spotipy's
  retry policy but `respect_retry_after_header=False` and 5xx-only `status_forcelist`. A 429 now
  raises in about 0.1s.
- **`main.py`:** a `SpotifyException` handler maps 429 to **503 "Spotify is rate-limiting this app
  right now. Try again later."**, with CORS headers. Verified for DJ, search and the playlist
  builder.

**Fewer searches per suggestion (`services/spotify_validator.py`):**
- `validate_songs(..., fallback=False)` skips the title-only second pass. The DJ passes it, because
  `select_tracks` rejects other artists' songs anyway. The playlist builder keeps the fallback.
- A process-lifetime cache keyed by `(title, artist, fallback)` stores misses as well as hits.
  Errors raise before anything is stored, so a 429 is never cached. It's cleared wholesale at 5,000
  entries (ceiling noted in code). The backend stays stateless across restarts.
- 4 tests are in `tests/test_validator_cache.py`.

**Also fixed:** `player_error` maps an expired Spotify token (401) to **401**, not 500, and
`/player/state/` now goes through `player_error`. 1 new test (61 total, all pass).

**Lesson for testing:** budget Spotify searches the way the Groq budget is budgeted. Prefer unit
tests with fakes (as in `test_validator_cache.py`) over live bursts. A live `/dj/suggest/` costs up
to `5 × (per_move + 2)` searches on a cold cache.

### Pre-DJ5 — review W4 + S2 (2026-10-23)

- **W4:** added the `BoominBeatsTests` target (hand-written pbxproj: a synchronized folder, hosted in
  the app, using Swift Testing). The pure logic was extracted and tested:
  `QueueStore.arrival(of:in:)`, `QueueStore.reconciled(_:against:)` and
  `SuggestionStore.autopilotCandidates(...)`. Run with
  `xcodebuild test -scheme BoominBeats -destination 'platform=iOS Simulator,name=iPhone 17 Pro'`.
- **S2:** reconcile drops only the played *prefix* of `sent`, and keeps the trailing unmatched
  tracks when Spotify's 20-item view is full. The naive "keep anything unmatched when full" would
  have been wrong: the playing context nearly always pads the view to 20.

### DJ5 result — Requests inbox (2026-10-23)

**Owner decision:** build without the Jam half of DJ0.1. The proven path is someone queuing
straight into Spotify (another phone on the host's account, or the Spotify app). **Whether Jam
guests' adds appear in `GET /me/player/queue` is still unverified.**

**Detection: `QueueStore.detectRequests`, a pure function.** It runs on a ~10s queue poll while the
app is in the foreground, plus on reconcile. A track is a request if either rule fires:
- **Wedged** (the plan's rule): a non-app track sits ahead of one of the app's own `sent` tracks.
  Reliable, but typically one top-up late.
- **Inserted (new):** the track was absent from the previous queue view and now sits before the
  last track the two views share. Context tracks only ever enter the view at its tail, so a mid-view
  newcomer was queued by someone. This catches requests on the next poll, which **removes the
  plan's one-song delay**. The rule is off while `smart_shuffle` is on (Spotify inserts its own
  recommendations mid-queue), so `/player/state/` now returns `smart_shuffle`.

**Inbox: a Requests section at the top of the Queue tab, with a badge on the tab.**
- **Keep:** the track plays where Spotify put it, and it's remembered so it isn't flagged again.
- **Later:** skip on arrival, and re-add the track to the end of Up Next.
- **Decline:** skip on arrival.
- Requests, pending guest skips and kept tracks persist in `queue.json` (optional fields, so
  pre-DJ5 files still decode).

**Two ordering bugs, caught by reasoning and in the live run respectively, now fixed:**
1. After Later, the guest's copy and the app's re-sent copy share a track id. Guest skips are now
   checked *before* `sent` arrival, because the guest copy was queued first and arrives first.
2. When the app's copy followed the skipped guest copy, there was no track-id change, so `observe`
   never ran and the stale `sent` entry blocked top-ups. `skipCurrent` now clears `lastTrackID` so
   the next poll re-observes.

| Check (live, Simulator + Spotify, the guest add done straight through Spotify's API) | Result |
|---|---|
| Insertion rule: guest track queued while the app runs → in the inbox on the next poll, badge 1 | ✅ (twice) |
| No false positives from the playlist's tracks | ✅ |
| Decline → guest track auto-skipped about 2s after it came up, inbox cleared | ✅ |
| Later → guest copy skipped, the app's copy plays, Sent clears (after fix 2) | ✅ |
| Keep | ⚠️ built, not exercised live |
| Smart Shuffle suppression | ⚠️ unit-tested only |
| Jam guests | ❓ unverified (owner deferred the test) |

**Known gaps:**
- A track queued **while the app is closed** isn't caught on launch. There is no previous snapshot
  for the insertion rule, and a wedge needs an app track behind it. Observed live with "12 to 12".
  It's caught later only if the app's next top-up wedges it.
- The queue poll adds about 1 player read every 10s, on top of the 2s state poll. Player endpoints
  weren't rate-limited during the search lockout, but they count against the same app.

7 new detection tests (18 iOS tests in total). Backend: `smart_shuffle` added to
`normalize_playback` and asserted in `test_player`. All 63 backend tests pass.

### Fix — transient refresh failures no longer sign the user out (2026-10-24)

`SpotifySession.refresh()` logged out on *any* failure, so a dropped connection, a Spotify 5xx or a
429 while renewing the token wiped the session. At a party, opening the app with a moment of no
signal would sign the host out. It was found when the Simulator came back logged out after an
overnight gap; whether that instance was transient or a real revocation can't be told.
- `postToken` now throws `TokenError.rejected` (400/401: the grant is gone) or `.unavailable`
  (anything else).
- `refresh()` logs out only on `.rejected`. On anything else it stays `.loggedIn` with the saved
  grant, and `validToken()` retries before the next request.
- 3 tests in `BoominBeatsTests/SessionTests.swift` (23 iOS tests in total).

### DJ6 result — goals, step by step (2026-10-24) — **built, live check pending**

**Owner decisions:**
- Goals are **optional**: a destination, an energy shape (Build to peak / Wind down / Peak then cool
  over 15/30/60 min), **Drift**, or none.
- **No predefined path.** "Sometimes you don't know where you're going or where you'll end up."
  This replaces the plan's "Bridge + arc planning": nothing builds or follows a fixed route.

**Backend (`routers/dj.py`):**
- An optional `Goal` on `SuggestRequest` (bounded; validated kind and shape; `minutes` 5–240).
- `goal_move()` adds one move, ahead of the five standard ones:
  - **toward** for a destination ("one step closer to ‹destination›, part of the way, not all at
    once"), or for an arc via `_arc_step()`, which turns `elapsed_minutes / minutes` into this
    step's instruction (up, down, or hold at the peak or the end).
  - **drift** for no destination: "one step somewhere new, away from where the night has been".
- `normalize_moves` takes the allowed moves per request. 8 new tests (71 in total).

**iOS:**
- `DJGoal`, persisted in `DJSettings`. An arc keeps `startedAt`, and its position is computed at
  request time.
- A Goal row in the DJ card: a menu, a destination prompt, and a 15/30/60 picker plus "n of m min"
  for arcs.
- The cache key includes the goal, and an arc's key moves on every 5 minutes as it progresses.
- Autopilot takes the goal move's picks first (`lead`). Move labels: Toward ("Next step toward
  your goal") and Drift ("Somewhere new").
- 2 new tests (20 iOS tests in total, 23 with the session fix).

**Not verified live:** Spotify search was still rate-limited (until about 2026-10-24 21:20 CDT), so
no Toward or Drift suggestion has been seen end to end yet, and the Goal row hasn't been seen
rendered: the Simulator came back signed out. Run a small, rate-budgeted live check once search
unblocks.

**DJ6 partial live check (2026-10-24 16:20 CDT).** Search was still 429 (`Retry-After: 17989`), so
this covered everything *except* Spotify validation:
- **The LLM step.** The exact `build_prompt` output for each goal (Tadow — Masego playing; Kendrick
  and Solange in history) was sent straight to Groq. The goal move led every reply with the five
  standard moves after it, in 2.7–3.9s.
  - **Destination "90s R&B":** TLC, Tevin Campbell, K-Ci & JoJo, Erykah Badu. ✅ On target, though
    it jumps all the way there instead of "part of the way".
  - **Build arc (33% of 30 min):** Redbone, Otis Redding, a likely-hallucinated Jonas Brothers
    track, an Amy Winehouse remix. ⚠️ **Not reliably higher energy.** At
    `reasoning_effort='low'` the "step energy UP" instruction is followed weakly.
  - **Drift:** Erykah Badu, Bill Withers (live), "Don't You Worry 'Bout a Thing" credited to Teddy
    Pendergrass (it's Stevie Wonder's), and a likely-hallucinated "Cinematic Edit". The direction
    is right (away from hip-hop). The bad entries would be dropped by Spotify validation or the
    artist check, which leaves the move with fewer picks.
- **iOS:** the "Nothing playing" state rendered correctly (a DJ1 gap, now seen). The Goal row
  wasn't reachable, because the DJ card only shows while a track plays.

**Still open:** end-to-end once search unblocks (about 21:20 CDT), the Goal row in the UI, and
whether the arc prompt needs concrete energy markers (tempo, intensity) to steer reliably.

**DJ6 arc prompt tweak + UI check (2026-10-24 ~16:30 CDT).**
- `_arc_step` now uses concrete markers. Up: "a clearly faster tempo, harder drums or more intense
  production … say what makes it higher energy". Down: slower, softer or sparser. Hold-peak and
  hold-low variants too. Re-tested on the same scenario:
  - Run 2: Anderson .Paak "Bubblin'", Lucky Daye, the Justice remix of "Electric Feel", Frank Ocean
    "Nights" (for its beat switch). ✅ Clearly higher energy, with reasons naming tempo and drums.
  - Run 1: the KAYTRANADA remix of "Cranes in the Sky" (good), plus a non-existent Masego track and
    "Redbone — higher BPM" (wrong).
  - Conclusion: much better, not perfect. Spotify validation drops the fake track; a confident
    wrong reason can still slip through.
- **UI, verified in the Simulator:** the Goal row and menu (None / Destination… / Build to peak /
  Wind down / Peak then cool / Drift).
  - Picking **Build to peak** shows "Build to peak · 30 min", the 15/30/60 picker and "0 of 30 min".
  - **Destination…** opens the prompt; "90s R&B" sets "Toward 90s R&B", and the arc picker hides.
  - While search was blocked, suggestions showed the 503 "Spotify is rate-limiting this app right
    now" message, as designed.
- **Still open:** the end-to-end Toward/Drift picks after Spotify validation, once search unblocks
  (about 21:20 CDT).

### DJ6 live check — end to end (2026-10-25 ~12:00 CDT)

Search was unblocked (`200`). Checked in the Simulator against live Spotify, with the iPhone as the
playing device, about 3 suggestion calls in total:

| Goal | Now playing | Lead move (validated on Spotify) | Verdict |
|---|---|---|---|
| Toward 90s R&B | Lemonade (Internet Money, Gunna) | **Toward:** D'Angelo "Untitled (How Does It Feel)", D'Angelo "Brown Sugar" | ✅ on target; other moves fit the trap starting point |
| Drift | Lemonade | **Drift:** Mr.Kitty "After Dark", Kavinsky "Nightcall" ("glides away from rap") | ✅ somewhere new, mood kept |
| Drift (prefetched on track change) | Get You (Daniel Caesar) | boy pablo "Losing You", M83 "Midnight City (Eric Prydz remix)" | ✅ re-planned from the new track automatically |
| Build to peak · 30 min | Hot Blooded (New Constellations) | **Toward:** M83 "Midnight City" ("faster tempo"), Mr.Kitty "After Dark" ("beats accelerate the pace") | ✅ higher energy, and the reasons name it |

The Toward/Drift section leads the list, under the goal's own label and icon, followed by the five
standard moves. Switching goals re-fetches immediately. **DJ6 is verified.**

**Bug found and fixed: a stale error message.** "Session expired. Log in again." appeared once and
never went away, though the session worked (a pause from the app went through, and the icon flipped
on the next poll). `NowPlayingModel` only ever cleared the no-device message. It now tracks whether
`message` came from a failed poll and clears it on the next successful poll. Command errors are
untouched, because they must survive the re-read 400 ms after a command. The single 401 behind it
wasn't reproduced; a token-refresh edge around expiry is the likely cause. Watch for a recurrence.

---

# Plan — DJ Sync, Hosted Deploy, and Web DJ
Date: 2026-10-25
Status: Active (SY0 decisions confirmed 2026-10-25)
Brainstorm: `docs/brainstorm.md` → "DJ Sync Across Devices (2026-10-25)" and "DJ Companion — Web
Design Brief (2026-10-25)"
Depth: high-level for all milestones; **SY1 at task level** (the first build)

## Overview

Three connected pieces, in dependency order:
1. **Sync layer:** a shared `dj_state` per Spotify user in Supabase Postgres, with a Jam-style
   primary device. This is the backend's first persistent state, scoped to DJ state only.
2. **Hosted deploy (finishes P0/D1):** so a physical iPhone can reach the backend away from home
   Wi-Fi.
3. **Web DJ:** the widget-grid design from the brief, built on the sync layer from day one, so it
   is built once rather than twice.

The iOS DJ moves onto the sync layer between 2 and 3.

## Goals & Success Criteria

| Goal | Success criteria |
|---|---|
| One DJ night across devices | An edit on the phone (add, reorder, remove, mode, goal) shows on the web within ~3s, and vice versa |
| Exactly one device drives | Only the primary sends to Spotify. Two open devices never double-queue a track, and never flag each other's sends as requests |
| Clear, Jam-like control | Every device shows who's driving. "Drive from here" moves it in one tap. When the primary goes silent for 60s, participants are told; there's no silent switch |
| Safe under conflict | Simultaneous edits never lose data: the loser of a race re-applies on top of the winner (version + 409) |
| Works offline briefly | A device that loses signal keeps working from its local copy and merges on reconnect. The primary keeps driving |
| Reachable anywhere | The hosted backend is up over TLS behind the device key, and a physical iPhone syncs on cellular |
| Web DJ at parity | Every iOS DJ feature on the web, in the customizable grid, with Host/Board/Focus presets and the mini player |

## Scope

### In scope
- Supabase project, `dj_state` table + migration, RLS enabled
- Backend: `/dj/state` read/write with optimistic concurrency, primary claim + heartbeat, user-id
  resolution from the Spotify token
- The hosted deploy (P0/D1.3–D1.4), with secrets for Spotify, Last.fm, Supabase and the device key
- iOS: a sync client replacing `queue.json`/UserDefaults persistence for synced fields;
  primary/participant gating; the "Driving from…" indicator and Drive from here; migration of the
  existing local queue
- The web DJ per the design brief, pass 1 and pass 2

### Out of scope
- Real-time push (Supabase Realtime, websockets). Version polling is enough at this scale; revisit
  if ~3s feels slow
- Multi-user sessions (guests with their own accounts). Guest requests stay as in DJ5
- Syncing per-device settings: web layout, Appearance, buffer depth, LLM key
- A server-side queue worker. The primary device still does the top-ups, so tokens stay
  per-request

## Tech Stack & Architecture

**Storage: Supabase Postgres, a new project** (not the existing Trip Fairy project, which is a live
app; mixing apps in one database couples their failures and their data). One table:

```
dj_state(
  spotify_user_id  text primary key,
  version          bigint not null default 1,
  state            jsonb  not null,   -- queue, options, feedback, recent
  primary_device   text,              -- device id (uuid, per install / per browser)
  primary_label    text,              -- "iPhone", "MacBook web"
  primary_seen_at  timestamptz,       -- heartbeat
  updated_at       timestamptz not null default now()
)
```

Access is **backend-only** through the service-role key, which never reaches a client. RLS is on
with no policies (deny-all) as defence in depth.

**State document:** `{queue: {sent, upcoming, requests, guestSkips, keptGuests}, options: {mode,
adventurousness, clean, goal, avoidTracks, avoidArtists}, feedback: {liked, disliked, skipped},
recent: [...]}`. The field names match iOS `QueueStore`/`DJSettings`, so the iOS port is
mechanical. Whole-document writes; the document is a few KB.

**API (new router `routers/dj_state.py`):**
- `GET /dj/state` → `{version, state, primary: {device, label, seen_at, online}}`
- `PUT /dj/state` with an `If-Match: <version>` header → `200 {version}`, or **409** with the
  current document. The client re-applies its local change and retries (bounded to 3).
- `POST /dj/primary` with `{device, label}` claims the primary role (always succeeds: that's Drive
  from here).
- The heartbeat rides on existing traffic: the primary's `GET /player/state` carries
  `X-DJ-Device`. The backend refreshes `primary_seen_at` at most every 15s and adds `dj_version`
  to the player-state response. **No extra calls per poll:** clients learn about remote changes
  from the 2s poll they already make, and only fetch `/dj/state` when the version moves.
- **Identity:** the Spotify user id comes from `GET /me` with the bearer token, cached per token
  hash for its lifetime. A client cannot address another user's row.

**Client model (iOS and web share it):** a local copy is the source of truth for rendering. Edits
apply locally, then sync. Remote versions merge in, with the server winning except for the device's
own pending edit, which is re-applied. Only the primary runs top-up, skip-on-arrival, autopilot and
request detection; participants' "add" just edits `upcoming`, and the primary sends it.

**Hosting: Vercel to start (owner's decision, 2026-10-25); the recommendation was Fly.io.** The
owner already has a Vercel account and doesn't want another billed account until the LLC bank
account exists. Revisiting hosting is tracked as a task.
- Vercel caveats to handle in SY2:
  - Check the Hobby tier's current invocation allowance against an estimate (2 devices × 2s poll
    × a 4h party ≈ 14k calls).
  - Set the function `maxDuration` above the `/dj/suggest/` latency (3–7s).
  - The process-lifetime caches (the `/me` user id, the validator) become per-instance. That's
    correct, just less effective.
- Original reasoning, kept for the revisit:  (Docker, an always-on shared-CPU VM). The repo already has the
Dockerfile from D1.
- Ruled out **Render free:** it sleeps after idle, and a 30–60s cold start mid-party is
  unacceptable.
- Ruled out **Vercel:** it's familiar from Trip Fairy, but per-invocation metering fits poorly
  with a 2s poll from every device, and cold starts add latency to `/player/state`.
- **Needs the owner's choice:** Fly needs an account with a card. Expect a small monthly cost for
  the smallest always-on VM; check current pricing before committing.

**Web DJ:** per the design brief (gridstack.js pinned to 13.3.0, a Svelte 4 wrapper, logic in
`src/lib/dj/` with vitest). Built against the sync client from the start.

## Milestones

| # | Milestone | Description | Dependencies |
|---|---|---|---|
| SY0 | Decisions + accounts | Confirm the host, create the Supabase project (cost confirmed first), set the heartbeat/offline numbers, pick the migration rule | — |
| SY1 | Backend sync API | `dj_state` migration, `/dj/state` GET/PUT with version + 409, `/dj/primary`, heartbeat piggyback, user-id resolution, tests | SY0 |
| SY2 | Hosted deploy (P0/D1) | Deploy FastAPI to **Vercel** (Python runtime) with secrets + device key; iOS points at it; verify on a physical iPhone on cellular | SY1 |
| SY3 | iOS on sync | A sync client replaces local persistence for synced fields; primary-only driving; "Driving from…" + Drive from here; feedback/recent synced; local-queue migration; 409 tests | SY1 |
| W1 | Web DJ logic + sync client | Port QueueStore/NowPlaying/Suggestions/DJSettings to `src/lib/dj/` on the sync client; vitest ports of the iOS logic tests | SY1 |
| W2 | Web DJ grid + widgets | gridstack spike → grid shell; the Now playing, DJ controls, Goal, Next moves, Single move, Up next and Requests widgets; Host/Board/Focus presets; Edit layout | W1 |
| W3 | Mini player + ambience + polish | Mini player on other pages, album-art ambience, `/design audit` + `polish` pass | W2 |
| W4 | Web DJ pass 2 | Linking + Song profile widget, Recently played, keyboard move/resize | W3 |

SY2 and SY3 can run in parallel after SY1. W1 needs only SY1; the hosted deploy isn't required for
web-on-localhost.

## Task Breakdown — SY1 (backend sync API)

1. **Migration:** `supabase/migrations/<ts>_dj_state.sql` creates the table above, plus
   `alter table dj_state enable row level security;` (no policies). Applied with the Supabase
   connector after review.
2. **Config:** add `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` to `config.py` and `.env.example`.
   If unset, the sync endpoints return 503 "Sync isn't configured", so the backend still runs
   without them.
3. **`services/dj_store.py`:** the Supabase client (the `supabase` Python package, or `httpx`
   against PostgREST). Functions: `read(user)`, `write(user, state, expected_version)` as an atomic
   conditional update (`where version = expected`, one row affected or a conflict), and
   `claim_primary(user, device, label)`.
4. **`services/spotify_identity.py`:** `user_id(token)` via `/me`, cached by a SHA-256 of the
   token with a TTL of about 50 minutes. The raw token is never logged.
5. **`routers/dj_state.py`:** the three endpoints. Validates the state document with pydantic
   (bounded lists, as in `SuggestRequest`; rejects unknown top-level keys).
6. **Heartbeat piggyback:** `/player/state` accepts an optional `X-DJ-Device`. If it matches the
   primary, `primary_seen_at` is touched at most every 15s, and the response gains `dj_version`.
7. **Tests:** version conflict (two writes from the same base: the second gets a 409 with the
   current document), user scoping (a token for user A can't read B), the unset-config path,
   heartbeat throttling, and request bounds. The store is faked; no live Supabase in unit tests.
8. **One live check** against the real project: read/write/conflict through curl with a real
   token.

**Acceptance:** all tests pass; a live 409 is demonstrated; the backend still starts with no
Supabase config.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Two devices both think they're primary (a claim racing a heartbeat) | Medium | High (double-queue) | The server is authoritative. Each device re-reads `primary.device` from every player-state poll and stops driving within one poll if it's no longer primary |
| A merge loses an edit | Medium | Medium | Whole-document version check plus re-apply of the device's own pending op; tests cover the race |
| Supabase outage mid-party | Low | Medium | The local copy keeps everything working; the primary keeps driving; sync resumes |
| Fly cost or account friction | Low | Low | Pick the smallest VM; the local backend keeps working on home Wi-Fi in the meantime |
| More Spotify API load (`/me` per token) | Low | Medium | The `/me` result is cached per token; the heartbeat rides on the existing poll |
| Request detection confused by the primary switching mid-night | Medium | Low | The `sent` list is in the shared state, so a new primary knows what "the app sent", whichever device sent it |
| gridstack + Svelte 4 friction | Medium | Medium | A spike at the start of W2; the fallback is CSS Grid presets with no free drag (keeps the presets, defers drag/resize) |

## Dependencies

- A Supabase account (the same org as Trip Fairy is fine). The new project's cost must be
  confirmed with the owner before creation.
- A Fly.io account (or the chosen host) with billing.
- The existing Spotify client ID; nothing changes there. The iOS app needs no new scopes.

## Open Questions (SY0) — resolved 2026-10-25
Answers: **Vercel** (revisit later), **a new Supabase project**, **60s offline** (15s heartbeat),
**the first device seeds the server**. The original questions:

1. **Host:** Fly.io (recommended) vs. alternatives.
2. **Supabase:** a new project (recommended) in the existing org. Creation requires a cost check
   for that org.
3. **Heartbeat/offline:** a proposed 15s touch / 60s "stopped driving".
4. **Migration:** proposed. On first sync, if the server has no row, the device uploads its local
   queue and options. If a row exists, the server wins and the device's local queue is discarded
   (one-time notice: "Using the queue from your other device").

## Decisions Log

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Backend state | Supabase Postgres for DJ state only; tokens and keys stay per-request | Owner wants cross-device sync; the shared DB keeps both deployments | 2026-10-25 |
| Driving model | Jam-style primary; participants edit; explicit Drive from here, no silent failover | Owner's choice | 2026-10-25 |
| Synced data | Queue, options, feedback, recent | Owner's choice | 2026-10-25 |
| Sync transport | Version polling piggybacked on `/player/state`; no realtime | Adds no calls per poll; realtime is unnecessary at this scale | 2026-10-25 |
| Concurrency | Whole-document optimistic concurrency (version, 409, re-apply) | Small document; simplest correct option | 2026-10-25 |
| Supabase project | New, separate from Trip Fairy (pending confirmation) | Isolation from a live app | 2026-10-25 |
| Milestone prefixes | `SY#` for sync/deploy, `W#` for web | Distinct from `P#`/`DJ#` in the tracker | 2026-10-25 |
| Host | Vercel to start; revisit (Fly.io) after the LLC bank account | No new billed account yet; Vercel is already set up | 2026-10-25 |
| Supabase project | New project **`boomin-beats`** (ref `dprikmlswldgkzuafcxy`, **us-east-1**, $0/mo free tier), created 2026-10-25 | Isolation from Trip Fairy. us-east-1 because us-west-2 wasn't offered for new projects and it's Vercel's default function region, so the backend and database sit together | 2026-10-25 |
| Offline threshold | 15s heartbeat, 60s "stopped driving" | Rides out brief signal drops | 2026-10-25 |
| Migration | The first device seeds the server; later devices adopt the server's copy | Nobody loses a queue they built | 2026-10-25 |

### SY1 result — backend sync API (2026-10-25)

**Built:**
- **Migration** `supabase/migrations/20261025180000_dj_state.sql`, applied to `boomin-beats`.
  RLS is on with no policies; the advisor's "RLS enabled, no policy" INFO is that intended
  deny-all.
- `services/dj_store.py` talks to Supabase's PostgREST API through **`httpx`**, which was already
  a dependency (the plan allowed either this or the `supabase` package).
  - The conditional update is `PATCH … ?version=eq.N`: zero rows back means Conflict. An insert
    hitting the primary key → 409 → Conflict.
  - `heartbeat()` is filtered on `primary_device`, so a heartbeat racing a takeover can't
    overwrite the new primary.
  - `OFFLINE_AFTER` is 60s and `HEARTBEAT_EVERY` is 15s.
- `services/spotify_identity.py`: the Spotify user id via `/me`, cached by a SHA-256 of the token
  for 50 minutes. The raw token is never stored.
- `routers/dj_state.py`:
  - `GET /dj/state` (version 0 / `state: null` when there's no row).
  - `PUT /dj/state` with `If-Match`: `0` seeds the row and makes the device primary; `N` updates;
    a 409 returns the current document.
  - `POST /dj/primary` (404 if there's no session yet).
  - The pydantic document mirrors the iOS field names. It **forbids unknown fields** and bounds
    every list. Unconfigured → 503 "Sync isn't configured on this server."
- `/player/state/` gains the piggyback: with `X-DJ-Device` it returns
  `dj: {version, primary}` and heartbeats the primary (throttled to 15s). It's best effort: any
  sync failure gives `dj: null` and never breaks player state.
- Config: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SYNC_ENABLED`; `.env.example` documents them.

**Note relative to the plan:** "no extra calls per poll" holds for *clients*. Server-side, a
sync-enabled poll does one Supabase read, plus a heartbeat write at most every 15s.

**Tests:** 15 new in `tests/test_dj_state.py` (86 in total, all pass). They cover seed + primary;
a stale write → 409 with the winner's document; seeding twice → 409; per-user scoping; Drive from
here; claim without a session; validation (unknown fields, bad mode, 201-item list, bad goal);
`If-Match` required; unconfigured → 503; 60s offline / 15s heartbeat boundaries; and the
piggyback degrading to None. Supabase and Spotify are faked.

**Live check against the real project:** read (empty) → seed (v1, primary "MacBook web") → update
(v2) → stale write **409** carrying the winner's "phone edit" → claim (primary "iPhone", version
unchanged) → piggyback `dj: {version: 2, primary: {label: "iPhone", online: true}}`. ✅

**Measured latency** (browser resource timing; an earlier multi-second reading came from a hidden
pane throttling timers):

| Call | Time |
|---|---|
| `/player/state/` without sync | about 230 ms |
| `/player/state/` with sync | 270–310 ms (578 ms first, including the `/me` lookup) |
| `/dj/state` | about 95 ms |
| Supabase read from the Mac | about 100 ms |

**Cleanup:** the live test row was deleted, so the first real device seeds the table.

### SY2 progress (2026-10-25)

- **Vercel facts, from the docs** (`/docs/plans/hobby`, `/docs/frameworks/backend/fastapi`):
  - Hobby includes 1M function invocations, 4 active-CPU hours and 360 GB-hours of memory a
    month, with a 300s max duration.
  - **Exceeding a limit pauses the project for 30 days**; there's no overage billing.
  - Hobby is for **non-commercial, personal use only**. Boomin Beats qualifies as long as it stays
    a personal tool; productizing under Christopher Ventures means Pro (see the hosting revisit
    task).
  - Estimate: about 17k invocations per 4h party with 2 devices; about 150k/month with regular
    use; 1–1.5 CPU-hours; about 25 GB-hours. Comfortable.
- **Prep committed (`d5a3776`):** `vercel.json` (iad1, `main.py` maxDuration 60, tests/Dockerfile/
  .env excluded), pinned `requirements.txt`, and an in-memory app-token cache. `main.py` with a
  top-level `app` is a supported entrypoint, so no code moved.
- **Branching:** production deploys from `main`. `dev` merged `main` (`0c9e694`), keeping the
  dead Django `.pyc` files deleted. **PR #1** (dev → main) is open.
- **Vercel project `boomin-beats-api`** (`prj_CoJ2oMXuNX9OtUn3ClCpqSyFJXE0`, team Christopher
  Ventures), Git-linked, root `src/web/backend`, production branch `main`, no deploy yet.
  `SPOTIFY_CLIENT_ID` and `SUPABASE_URL` are set as plain values.
- **Owner to set (secrets, Sensitive type):** `SPOTIFY_CLIENT_SECRET`, `LASTFM_API_KEY`,
  `SUPABASE_SERVICE_KEY`, and a newly generated `DEVICE_KEY`.
- **The repo is public.** A full-history secret scan found an old 2023 Spotify client secret in the
  Django code. It differs from the current secret (verified by hash), so it was rotated and is
  dead. Nothing live is in the history.
- **New risk found:** the Spotify **search** daily quota (`QUOTA_EXCEEDED`, resets about 21:20
  local) was exhausted again by a morning of Co-pilot prefetch. Tracked as a high-priority bug;
  not part of SY2.

### SY3 result (2026-10-25)
Built in `src/ios/BoominBeats/DJ/`: `SyncDoc.swift` (the shared document, field-level three-way
merge), `DJSync.swift` (pull on a version change, debounced push with If-Match, merge-and-retry on
409 up to 3 times, seed at v0, Drive from here) and `SyncBanner.swift` (on Now Playing and Queue).
Primary-only gating covers top-ups, skip-on-arrival, reconcile, request polling, autopilot, and
history/skip recording. The last role is remembered, so a participant doesn't drive at launch.
Five new tests in `SyncTests.swift`. **Pending:** the live two-device check (iPhone on dev, plus
the simulator).

### W1 result (2026-10-25)
`src/web/frontend/src/lib/dj/`:
- `logic.js`: pure logic, ported one to one, with 23 vitest ports of the iOS tests.
- `dj.js`: one engine over a single synced `doc` store, plus local `player`, `sync` and
  `suggestions` stores.
- `api.js`: `{status, data}` fetch; the LLM key is sent only to `/dj/suggest/`.

Five engine tests run against a fake SY1 backend: seed, participant gating, 409 merge, Drive from
here, and adopting the queue with a notice.

Web-specific choices:
- A hidden tab keeps 5 tracks ahead, because browsers throttle hidden timers. The iOS equivalent is
  the background top-up.
- The device label is `<platform> web`.

**Found and fixed on both clients:** a participant's add waited for the next track change before
the primary sent it. The primary now tops up after adopting remote state.

### W2 result (2026-10-25)
The DJ page is at `/dj/` (a new nav link), built on the W1 engine. gridstack 13.3.0 is wrapped in
`lib/components/dj/Grid.svelte`: Svelte owns each widget's DOM, gridstack only positions it.

**Widgets:**
- Now playing: becomes a one-row banner when the widget is short.
- DJ controls: includes an avoid list you can manage.
- Goal.
- Next moves.
- Single move, one widget per move kind.
- Up next: reorder by dragging, or with Alt+Up/Down on a row's handle. ✦ marks DJ picks, and there's
  an Add song search.
- Requests: a badge count, and Keep/Later/Decline.

**Layout:**
- Presets: Host (the default), Board and Focus, plus "Your layout" once edited.
- Edit layout gives drag, resize, remove and an Add widget menu. Done saves to `djLayout.v1`; Esc
  cancels.

**Checks:** 33 vitest tests pass. svelte-check is clean on the new files. The frontend detector is
clean; it was verified against a known hit.

**Live check** in the browser pane at 1440×900: Host, Board and Focus all lay out correctly, with
suggestions stubbed in the page because Spotify search was locked out. Add widget, Done, reload
persistence, Esc cancel and a real mouse drag all work.

**Deviations from the brief:**
- Host docks Goal inside DJ controls, which the brief allowed, so the album art gets the height.
- Board also includes DJ controls, so the mode stays reachable.
- Now playing's minimum height is 3, not 5, for Board's banner.

**Not verified:** the column breakpoints on a live resize. The pane was hidden, which pauses
ResizeObserver, so it needs a check in a visible window.

**Fixed along the way:**
- A widget added in edit mode saved without an id or size: gridstack's `makeWidget` options replace
  the gs-* attributes rather than merging with them.
- A false "other device" notice: the server fills defaults like `addedByDJ: null`, so the doc
  comparison now ignores key order and nulls.

### W3 result (2026-10-25)
**Mini player** (`MiniPlayer.svelte`): a fixed 64px bar on every page except `/dj/`. It shows the
art, title and artists, a progress hairline, ⏮ ⏯ ⏭, the goal label and an Open DJ link. It sits
beside the docked Playlists panel, and hides when signed out or when nothing is playing. The engine
now starts in `+layout.svelte`, so a driving tab keeps driving on any page.

**Ambience** (`lib/dj/ambience.js`, 4 tests): the cover is sampled at 16×16 on a canvas (`i.scdn.co`
allows cross-origin reads). The colour is averaged in OKLab, weighted by chroma, then clamped to
OKLCH L 0.18–0.24 and C ≤ 0.04. It crossfades over 400ms, and swaps instantly under reduced motion.
Live check: KAYTRANADA's "Need It" gave `oklch(0.200 0.036 80)`, a warm brown.

**Audit:** the frontend detector is clean, and a web-interface-guidelines pass found these, now
fixed:
- placeholders end with "…"
- the destination input is named, with `autocomplete="off"`
- `color-scheme: dark` is set
- targets are 32/36px
- the Add widget menu is anchored to its button
- the duplicate "Up next" subheading is gone

**Breakpoints:** fixed to match the brief. gridstack's `w` is inclusive, so a load at 1024px now gives
8 columns.

**Deferred to W4:**
- A keyboard alternative to dragging widgets (W4's keyboard move/resize).
- Undo for remove/decline (iOS has none either).
- Live-resize breakpoint switching is still unverified, because the pane keeps going hidden.

### W4 result (2026-10-25)
- **Linking:** suggestion, Up next and Recently played rows are buttons that select a song, and the
  selected row is tinted. The **Song profile** widget follows the selection, and otherwise shows
  what's playing. It has a "Show now playing" button to go back.
  - *Deviation:* the widget reuses the `/song/profile/` endpoint and `SongRadar`, not
    `SongProfile.svelte`, because that component writes Explore's session store and would nest a
    card in a widget.
- **Recently played:** the session's synced history, with + to queue a song again.
- **Keyboard move/resize:** in edit mode, a widget's handle moves it with the arrow keys and resizes
  it with Shift+arrows, announced through `aria-live`.
- **Undo** (deferred from W3): a 6s toast after Remove in Up next and after Decline on a request.
- **Prefetch gating**, found live: after W3 every open tab prefetched suggestions on each song
  change. That used up Groq's 200k tokens a day and spent 20–50 Spotify searches per round.
  Suggestions now load only while a DJ page is open, or in Autofill/Driver. This also helps the
  search-quota bug (e2df2d).

**Checks:** 39 vitest tests pass. svelte-check has 19 errors, all in other files (20 before). The
detector is clean on the new files. The live check covered adding both widgets, keyboard nudge with
its announcement, and selecting a row and going back.

### Also added 2026-10-25: "Your Claude Code" AI provider
The local backend runs the owner's `claude` CLI on their Claude subscription, so there's no key and
no bill. It mirrors Trip Fairy's helper: no tools, no MCP servers, project settings only, an empty
temp directory as the working folder, the prompt over stdin, and no saved session.
- It's off on Vercel, off where the CLI is missing, and off when `CLAUDE_CODE=0` is set.
- Choose it in the web app's AI settings. It works only while the backend runs on this Mac.
- **Live:** connecting takes ~3s; a full DJ suggestion round takes ~16s (Groq ~6s) and parses
  cleanly.

### Spotify search quota fix (2026-10-25, tracker e2df2d)
**Cause:** Development Mode has an unpublished quota. It's counted per *developer account* (since
2026-07-23, shared across all Client IDs) and grouped by endpoint. Search runs out daily, and the
reset has come around 21:20 local. Extended quota needs a registered organization with at least
250k MAU, so the fix has to be using less. Each DJ round validated 20–28 picks, on every song
change, from every device and tab.

**Fix:**
- A shared `track_lookup` cache in Supabase (migration `20261026005535`). Matches are kept 30 days,
  misses 7.
- Early-stop validation (`fill_moves`).
- At most 4 searches in flight.
- Prefetch gating on iOS and the web.
- Typeahead waits for 3+ characters and a 350ms pause.

**Tests:** 8 in `test_search_budget.py`. A live round trip against the real table worked (write,
read, delete).

**Still to do:**
- The hosted backend gets this on the next merge to `main`.
- Measure a normal night once the quota resets.

### SY3 live two-device check (2026-10-25)
The web DJ ran in the browser pane on the local backend. The iOS simulator, built from dev
(7163caf), ran on the production Vercel backend. Both use the same Supabase row.

| Step | Result |
|---|---|
| Stale primary on open | The web showed "macOS web stopped driving · Drive from here", an older session; no silent switch. ✓ |
| Drive from here on the web | The simulator showed "Driving from macOS web" within ~2s. ✓ |
| Option change, web → iPhone | Clean only appeared on the simulator. ✓ |
| Mode change, iPhone → web | Co-pilot appeared on the web in **2.9s** (server v18), inside the ~3s goal. ✓ |
| Drive from here on the iPhone | The web showed "Driving from iPhone" in **1.8s**. ✓ |
| Participant add | A song added on the web (now a participant) was sent by the iPhone (the primary) about 7s later. Exactly **one** copy was in Spotify's queue, and **no** false guest request. ✓ |

**Cleanup:** the song is marked to skip on arrival, and the options are back to Whisper with Clean off.

**Found:** the simulator had lost its keychain, so the device-key guard rejected every poll. The app
reported that as "Session expired. Log in again." It now says "The server didn't accept this
device's key. Check Device key in Settings."

**Left for SY2:** the owner's physical iPhone on cellular.

---

# Plan — Quota-Safe Lookups (Deezer display, Spotify at choose time, ISRC identity)
Date: 2026-10-25
Status: Active
Brainstorm: docs/brainstorm.md, "Spotify Quota: Look Up at Queue Time, Songs by ISRC (2026-10-25)"

## Overview
Spotify search is the Development Mode quota bucket that runs out, and Extended Quota (an
organization with ≥250k MAU) is out of reach. This plan moves every *showing* of songs onto
Deezer, which needs no key and no Spotify quota, and keeps Spotify search for the moment a song is
*chosen*: queued, saved, or added to a playlist. Songs gain an `isrc`, the provider-neutral key
that makes the Spotify lookup exact today and lets Apple Music slot in later (the brainstorm's
direction F). It connects to the DJ (DJ0–DJ6), sync (SY1–SY3) and web DJ (W1–W4) plans, and closes
tracker e2df2d.

## Goals & Success Criteria
| Goal | Success criteria |
|---|---|
| A night fits the quota | A 4h / ~60-song session uses **≤ ~1.5 Spotify searches per queued song**, counted in Q4. No search 429 during a normal night |
| Showing costs nothing | DJ rounds, type-ahead and playlist generation make **zero** Spotify searches |
| Same quality | Picks are still checked (exists, right artist), with art and explicit flag. Wrong-artist matches drop (ISRC lookups are exact) |
| Clear misses | A song that isn't on Spotify shows "Not on Spotify" at tap; autopilot moves to its next candidate |
| Ready for Apple Music | Queue, avoid, feedback and cache entries carry `isrc` |

## Scope
### In Scope
- Backend:
  - a Deezer client: search + artist match + cache
  - a resolve service and endpoint (ISRC → Spotify track, title fallback, market-aware)
  - `isrc` on player and recently-played tracks
  - optional `isrc` fields in the sync schema
- DJ: `/dj/suggest/` validates with Deezer. iOS and web picks resolve on tap (with a spinner);
  autopilot resolves before it adds.
- Search: `/search/` returns Deezer results. Web SongSearch (Add song, Explore) and iOS Add to
  Queue resolve the chosen song.
- Playlist builder: generation validates with Deezer; results resolve on add/queue/save.
- A search counter to measure the result.

### Out of Scope
- Apple Music / MusicKit (direction F)
- The Odesli fallback (direction D) and library-first candidates (direction E)
- Backfilling `isrc` on existing synced rows
- Changing Clean only beyond the post-resolve explicit check
- Taste and profile endpoints (they don't search)

## Tech Stack & Architecture
**Deezer** (`services/deezer.py`, httpx):
- `GET https://api.deezer.com/search?q=<title> <artist>&limit=5`, then pick the first result whose
  artist matches (the same fold rule as `_artist_matches`). The strict `artist:"…" track:"…"` syntax
  missed obvious songs in testing, so the loose query plus our own match is the rule.
- Returns `{deezer_id, title, artists, image, explicit, isrc}`. Track search results may lack
  `isrc`; then one `GET /track/{id}` fills it, and is cached.
- Limits: about 50 requests / 5s per IP. Use a semaphore (4) and back off on the 4 error code.

**Resolve** (`services/track_resolver.py`, `POST /tracks/resolve/`):
- Takes `[{isrc?, title, artist}]` and returns `[{track | null}]`.
- Order: process cache → `track_lookup` → Spotify `q=isrc:<isrc>` (one search, exact) → title +
  artist search only when there's no ISRC.
- Uses the app client with `market=<user country>`, so the first match is playable. The country
  comes from `/me`, cached next to the user id in `spotify_identity`.
- A known miss is cached for 7 days, like today.
- Behind the same 4-in-flight cap and search lockout.

**One cache table, namespaced keys:** `track_lookup` (already live) keeps one row per key. The
hashed key gains a namespace, `deezer|title|artist` or `spotify|isrc|<isrc>|<market>`, and `track`
holds that source's record. No migration.

**Identity:**
- Optional `isrc: str | None` (max 15 characters) on `QueueItem`, `GuestRequest`, `TrackRef` and
  `AvoidedTrack` in `routers/dj_state.py`, and in the iOS/web models.
- Picks from `/dj/suggest/` no longer have a Spotify `id`. Clients key them by `isrc` (or Deezer
  id); "queued" and dedupe checks use `isrc` when present.
- `player.py` `_track()` and recently-played add `isrc` from `external_ids`. Exclusion in
  `select_tracks` matches on `isrc`, then on folded title + artist.

**Clean only:** after resolve, if the Spotify version is explicit while Clean only is on, treat it as
a miss ("Explicit version only").

## Milestones
| # | Milestone | Description | Dependencies |
|---|---|---|---|
| Q0 | Spikes | Run after the quota resets. Check that Spotify `isrc:` search returns the right, playable track (several versions, market). Test Deezer coverage and artist matching on ~50 real picks, including "feat." credits. Measure Deezer latency. Read Deezer's API terms | — |
| Q1 | Backend: Deezer + resolve + identity | `deezer.py` (search, match, ISRC fill, cache); `track_resolver.py` + `POST /tracks/resolve/` (market-aware, cached); `isrc` on player/recent tracks and in the sync schema; a search counter; tests with fakes | Q0 |
| Q2 | DJ on Deezer | `/dj/suggest/` validates via Deezer (`fill_moves` with a Deezer validator), picks keyed by `isrc`, exclusion by `isrc`/title. iOS + web: + resolves with a spinner, "Not on Spotify", the clean check; autopilot resolves before adding; queue items carry `isrc`; tests | Q1 |
| Q3 | Search + playlist builder on Deezer | `/search/` → Deezer. Web SongSearch (Add song, Explore) and iOS Add to Queue resolve on select. `generate-playlist` validates via Deezer. PlaylistResult resolves in a batch on add/queue/save, and hearts look up lazily | Q1 |
| Q4 | Measure + close | Count Spotify searches over a real session (target ≤ ~1.5 per queued song, 0 for showing); deploy; close e2df2d | Q2, Q3 |

Q2 and Q3 can run in parallel after Q1.

## Task Breakdown
(mid-level; deepens when each milestone starts)
- **Q0:**
  - Spotify `GET /search?q=isrc:USYAH1600107&type=track&market=US`, for 5 ISRCs with several
    releases.
  - Deezer probe on 50 picks from a Groq/Claude round.
  - Deezer terms: note the commercial-use limits for the later launch.
- **Q1:**
  - Files: `services/deezer.py`, `services/track_resolver.py`, `routers/tracks.py`,
    `services/track_cache.py` (namespaced `key()`), `services/spotify_identity.py` (country),
    `routers/player.py` (`isrc`), `routers/dj_state.py` (optional `isrc`).
  - Tests: `tests/test_deezer.py`, `tests/test_resolver.py`.
  - The counter: a process counter of real Spotify searches, logged per request and exposed in
    `/` health, so Q4 can read it.
- **Q2:**
  - Backend: `routers/dj.py`.
  - iOS: `SuggestionStore.swift` (Pick without a Spotify id), `NowPlayingView.swift` (+ resolve,
    spinner), `QueueStore.swift` / `SyncDoc.swift` (`isrc`), autopilot.
  - Web: `lib/dj/dj.js` (`add` resolves; autopilot), `PickRow.svelte` (spinner, miss state),
    `logic.js` (queued-by-isrc).
- **Q3:**
  - Backend: `routers/search.py`, `routers/llm_playlist.py`.
  - Web: `SongSearch.svelte` (add resolves), `PlaylistResult.svelte` (batch resolve; key by isrc).
  - iOS: `QueueView.swift` `AddTrackView`.
- **Q4:** a real session with the counter; the result goes in the plan; deploy.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Spotify `isrc:` search filter not supported in Dev Mode, or returns unplayable versions | Low–Med | High | Q0 spike first. Market-aware pick; title + artist fallback |
| Deezer misses or wrong artist ("feat.", aliases) | Med | Med | Q0 measures it. Fold match on any credited artist; misses drop like today's Spotify misses |
| Deezer shared-IP limit on Vercel | Med | Med | Cache every lookup (30d/7d); semaphore; back off on error code 4; picks degrade to "not checked" |
| Deezer terms block a commercial launch | Med (later) | Med | Fine for personal use. Re-check before launch; swap display data to Apple Music (F) |
| Clean only: a Deezer pick is clean but the Spotify version is explicit | Med | Low | Post-resolve explicit check → "Explicit version only" |
| Pick IDs change shape (no Spotify id), breaking client keys | Med | Med | One `pickKey()` helper per client; tests on queued/dedupe |
| Tap latency (resolve ~0.3–1s) | Low | Low | Spinner (owner-approved); cache hits are instant |

## Dependencies
- Deezer public API (no key). Spotify Web API (app client, search for resolves only).
- Supabase `track_lookup` (live). Last.fm stays for tags and the song profile.

## Open Questions
- Q0 decides whether the `isrc:` filter is reliable enough to skip the title fallback when an ISRC
  exists.
- Whether to show Deezer's 30s preview in the pick row. Not planned, but free.

## Decisions Log
| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Scope | A + B + C | The same pattern on all three surfaces leaves Spotify search for choosing only (owner) | 2026-10-25 |
| Resolve timing | When a song is added or chosen, with a spinner on tap | Every queue item keeps a Spotify id, so the queue, sync and request logic don't change (owner OK'd the spinner) | 2026-10-25 |
| Cache storage (OQ1) | One `track_lookup` table, namespaced keys | No migration; one TTL policy; the `track` jsonb already holds any shape | 2026-10-25 |
| Existing synced rows (OQ2) | No backfill; `isrc` is optional | They already have Spotify ids; new rows carry `isrc` | 2026-10-25 |
| Market (OQ3) | The user's `/me` country, cached with the user id, as `market` and in the cache key | The first ISRC match must be playable for the person queueing it; a small circle may span countries | 2026-10-25 |
| Autopilot resolves (OQ4) | On the primary device only, as today | Keeps sends single (the review C1 invariant) | 2026-10-25 |
| Art / tags (OQ5) | Deezer for pick art; Last.fm stays for tags and profile | Deezer art is per release; Last.fm tags already drive the prompt | 2026-10-25 |
| Milestone prefix | `Q#` | Distinct from P/DJ/SY/W in the tracker | 2026-10-25 |

### Q0–Q4 results (2026-10-25)
**Q0 spikes:**
- **Deezer:** 60 real DJ picks from three Claude Code rounds. With the shipped matcher (exact title
  after stripping suffixes, artist on any credit, re-uploads rejected, artist top-tracks fallback),
  it found **58/60**. The 2 misses were invented songs (the wrong artist for "Bartier Cardi", and a
  non-existent "Sailing Soul(s)"). Every hit carried an ISRC; p50 300ms.
- **Deezer gaps found along the way:**
  - The strict `artist:"…" track:"…"` syntax returns nothing.
  - Search ranking can hide a real song (Money Trees lost to a sped-up re-upload), hence the
    top-tracks fallback.
  - A 60-request burst hit Deezer's per-IP limit (code 4), hence sliding-window pacing (40 per 5s)
    and retry.
- **Deezer terms:** non-commercial, private or family scope only. Fine for the small circle; a
  public launch needs Deezer's approval or Apple Music (direction F).
- **Spotify `isrc:`** works in Development Mode, one search per song. Compilations are listed first
  (Redbone's album came 8th), so the resolver prefers album, then single, then compilation.
  Re-uploads can share the ISRC (September's only "single" was "sped up + slowed"), so they're
  skipped. The explicit flag matched Deezer for 6/6.

**Two more Development Mode facts (Q4 live):**
- Track objects come **without `external_ids`** (and without `popularity`). Spotify-side tracks
  therefore never carry an ISRC; picks get theirs from Deezer, and exclusion falls back to title +
  artist.
- `market=from_token` requires the **user-read-private** scope (403 otherwise).
- *Deviation from the plan:* the resolver uses the app's credentials with a fixed market
  (`SPOTIFY_MARKET`, default US) instead of the user's `/me` country. Ceiling: a friend abroad
  could get an unplayable version.

**Q4 measurement** (local backend, live Spotify, Claude Code):

| Step | Spotify searches | Before |
|---|---|---|
| DJ suggestion round (9 picks) | **0** | ~10–14 |
| Type-ahead query | **0** | 1 per pause |
| 3 picks looked up | **3** | — |
| Same 3 again | **0** (4ms, cache) | — |

That's **0 for showing, 1 per queued song**, inside the ≤1.5 target. The playlist builder makes 0
at generation and 1 per added song (unit-tested; not run live, to avoid writing to a real
playlist).

**Known quirk:** Deezer type-ahead ranks artist names, so "redbone" lists the band Redbone before
Childish Gambino's song (2nd of 8). Its `track:` filter is worse.

**Also:**
- The old Spotify validator (`services/spotify_validator.py`) was deleted, since nothing uses it.
- Deploy order: the backend goes first, because the sync schema now accepts `isrc`.

### Production check (2026-10-25, after deploy 7a4892f)
- **Deezer from Vercel:** works. A simulator search ran through production in under a second; the
  logs show the Deezer call and **no** Spotify search.
- **Gap, filed:** Deezer search never lists Kendrick Lamar's original "Money Trees" (covers and
  sped-up re-uploads fill the top 10). Type-ahead needs a re-upload filter plus a "Search Spotify"
  fallback that costs 1 search.
- **New finding, filed as High:** production's error report showed **1,157 `/me/player` 429s**
  (20:35–21:13 CDT, previous deployment), about one per 2s poll. Several pollers were hitting the
  same Spotify app: the simulator via production, and the web tabs via the local backend. Player
  calls are rate-limited too, not just search. Next step: back off on 429, and poll slower when not
  driving.
- **Fixed on the way:** the debug launch self-test was deleting the iOS device key on every launch
  (0639617).

### Player polling fix (2026-10-25, tracker 477d21)
**Cause:**
- Every device and web tab polled `/me/player` every ~2s while a song played.
- A Spotify 429 became a plain 500, with `Retry-After` dropped and no client backoff.
- Production logged 1,157 player 429s in 38 minutes. Vercel Hobby keeps 1 hour of logs, so
  Spotify's reason for them (quota vs rolling limit) wasn't recoverable. It's logged from now on.

**Backend:**
- A player 429 locks this instance's player calls for `Retry-After` (capped at 120s), app-wide,
  and answers 503 with `retry_after`.
- Player state is cached for 1.5s per token, so tabs share one Spotify call; commands clear the
  entry.
- Commands map 429 to `{error: 'rate_limited'}`.

**Clients (web and iOS):**
- Poll every 5s while playing; the driver wakes just after a song should end.
- 10s when nothing is playing; 15s for a web tab that isn't the leading tab.
- Back off on failures: `retry_after`, else 5/10/20/40/60s.

**Trade-off (owner to confirm):** cross-device sync now shows changes within about 5s, not the
original ~3s goal. Roughly 2.5× fewer player calls per device, and same-account tabs collapse into
one.

**Live:** a second poll within 1.5s came from the cache (same progress, no Spotify call). Tests:
4 backend, 1 web engine, 1 iOS.

**Production verification (2026-10-25):** after `a9c360a`, production logs show the simulator
polling every ~5.5–6s (was ~2s), with no errors. `ba361a1` silences httpx's per-request INFO
lines, which had been logging Spotify user ids and search terms in request URLs. Its deployment
logs nothing while serving the simulator's polls normally.

### Type-ahead fix: originals first (2026-10-25, tracker 713432)
**Problem:** Deezer's search buried originals under covers and sped-up re-uploads. Kendrick Lamar's
"Money Trees" wasn't in its top 50, though the track is on Deezer.

**Fix:** `/search/` now asks Last.fm `track.search` first, which ranks by popularity:
- Merge duplicate credits, and drop re-uploads unless the query asks for them.
- Fill in the top 6 from Deezer: art, ISRC and explicit flag, with the top-tracks fallback, cached.
  Dedupe again by the resolved id, since one recording appears under several credits.
- Top up from Deezer's own (filtered) search for songs too niche for Last.fm.
- Deezer alone if Last.fm is down; 503 only if both are.
- Still 0 Spotify searches.

**Live:** Money Trees → Kendrick Lamar first. Redbone → Childish Gambino; September → Earth, Wind
& Fire; Tadow → Masego (once); Electric → Alina Baraz. Cold queries take 0.5–2s; cached ~300ms.

**Also:** the Last.fm client moved to HTTPS, since its API key travels in the query string.

**Production check:** on 26dad29, the simulator's search for "money trees" (through production)
lists Kendrick Lamar's original first.

**Small follow-ups:**
- Mid-word queries ("money tre") give weak results until the word is complete, because Last.fm
  matches whole words.
- "(Speed)"-style labels slip past the re-upload filter. A filter on parenthetical labels would
  catch them without hiding songs like "Need for Speed".

### Type-ahead: mid-word queries and "(Speed)" labels (2026-10-25)
**Mid-word:** Last.fm matches whole words only, so partial queries got junk ("septem" → "Septem"
by Hexis), while Deezer matches prefixes well. New order:
1. Popular (≥100k listeners), Deezer-confirmed Last.fm hits, at most 3.
2. Deezer's results.
3. The rest of Last.fm.

Every result must also pass a relevance check: each typed word starts some word of the title or
artist.

**Labels:** one `deezer.is_reupload()` now serves search, Deezer matching and the resolver. It
checks only a title's bracketed or dashed label, plus re-upload account names and album labels,
for speed/slowed/reverb/nightcore/8d/karaoke/instrumental/cover/tribute/bass-boosted, unless the
query asks for that kind. So "(Speed)" is caught, while "Need for Speed" and "Undercover Lover"
are kept.

**Live:** money tre → Rilès / Money Tree; money trees → Kendrick Lamar; redbo → Redbone (and
Childish Gambino 2nd); septem → Earth, Wind & Fire; dancing qu → ABBA. About 0.5–1s.

**Known:** "kendrick lamar money" lists a "Kendrick Lamar - Money Trees" upload by "Music" second.

**Production check:** on 11a951d, the simulator's mid-word search "septem" (through production) lists Earth, Wind & Fire's "September" first.

### Type-ahead: uploads that name an artist (2026-10-25)
"kendrick lamar money" listed "Kendrick Lamar - Money Trees" by "Music" second. Three rules now
drop that kind of upload:
- **"Artist - Song" titles:** dropped when the real recording by that artist is elsewhere in the
  results, or the uploader prefixed its own name. "September - Live" by Earth, Wind & Fire
  survives a band named September.
- **Titles naming the searched artist:** when the query names an artist plus other words, results
  that mention that artist in the title but aren't by them are dropped. That covers parodies,
  "humble by kendrick lamar" and "~ slowed + reverb ~" uploads. "(feat. X)" credits are exempt,
  and a query that is only a name ("september") applies no rule.
- **Upload labels:** "(Official Audio/Video)" and "(Lyrics)" join the re-upload labels.

**Live:**
- kendrick lamar money → Money Trees (Kendrick Lamar) only
- kendrick lamar humble → HUMBLE. only
- drake one dance → One Dance (Drake)
- taylor swift bad blood → Bad Blood, then Taylor's Version

148 backend tests pass.

### Search covers + one row per song (2026-10-25)
- **Covers:** iOS Add to Queue rows show the cover. `/search/` fills in covers for the top 8
  Last.fm hits (was 6), and a hit Deezer can't match uses Last.fm's own image, skipping its grey
  placeholder star. Live: 10/10 results with covers.
- **One row per song per artist:** Deezer lists every release separately, so "Come and Get Your
  Love" appeared five times. Its results now dedupe by song and artist, which also collapses
  "Bad Blood (Taylor's Version)" into "Bad Blood".

**Production check:** on 989ffcd, the simulator's "redbone" search (through production) shows a cover on every row and one "Come and Get Your Love".

---

# Plan — Web Redesign (Claude Design handoff)
Date: 2026-10-27
Status: Active
Brainstorm: inline. The design is the Claude Design handoff in
`docs/design/redesign-2026-10-27/` (README = spec, `Boomin Beats.dc.html` = clickable prototype,
`screenshots/`). The context we gave the design agent is `docs/design-context.md`.

## Overview

A full visual redesign of the SvelteKit web app (`src/web/frontend`):
- immersive colour taken from album art, plus motion while music plays
- glass cards
- denser, shared song rows
- tighter links between Explore, the Builder, the DJ and Profile

The handoff also specifies roughly a dozen new features. We build it in two parts:
- **Part 1, a reskin (R0–R6):** every page restyled to the handoff, keeping today's features.
- **Part 2, features (F1–F5):** the new behaviour, one milestone at a time, after the reskin ships.

## Goals & Success Criteria

- **Matches the screenshots.** Each page matches the handoff at 1280px and at about 924px
  (tablet). Colour, type, spacing, radius and motion all follow the README's tables.
- **Nothing lost.** Every feature that works today still works. That covers search and resolve,
  song profile and Discover, Builder generation, save and queue, drag-to-playlist, the Profile
  modules, and the DJ's sync, presets, Edit layout and mini player. The 52 vitest tests pass.
- **One song row.** A single `SongRow.svelte` replaces the current row variants: `SongCard`, the
  `PlaylistResult` rows, `PickRow`, the `UpNext` rows and the search rows.
- **Motion has an off switch.** Under `prefers-reduced-motion`, nothing drifts, breathes or glows.
  The blobs and visualizer move only while music is playing.
- **Accessible.** Text holds 4.5:1 contrast over glass and blobs (checked over the brightest
  cover hue), and keyboard focus is visible everywhere.
- **The detector is clean.** `/design audit` passes, or each remaining hit is justified. (The
  handoff deliberately uses glass and the gradient, see the Decisions Log.)

## Scope

### In scope (Part 1)

- **Foundations:**
  - Tokens mapped onto the existing names (`--surface-*`, `--accent*`, `--text-*`, plus new ones
    for glass, popovers, success and danger).
  - Geist and Geist Mono via `@fontsource`, replacing Inter and Fira Mono.
  - The motion keyframes (`bbin`, `bbshimmer`, `bbspin`, `bbeq`, `bbbreath`, `bbglow`, `bbpop`,
    `bbdrift`).
  - One stroke icon set, by extending `dj/Icon.svelte` app-wide.
  - The 90% default UI scale.
- **Shell:**
  - A 60px glass header with a segmented icon nav (and a dot on DJ while music plays).
  - The Playlists dock restyled.
  - The mini player restyled: gradient progress line, glow and breathing cover, playing bars.
  - The gear popover restyled. It gets the **AI tab only**; the General tab is F1.
  - Toasts.
- **Song row:** the shared row with rank, cover, ✦, reason, duration, Swap and + → ✓, and drag
  onto playlists. The preview badge is left out until F2.
- **Explore:**
  - Idle: hero tinted by the hovered top track, a 64px glass search, mood chips that go to the
    Builder, and a grid of cover tiles.
  - Song page:
    - a sticky bar with the **Path** trail
    - an immersive hero
    - Tags, "What the AI hears", Sound profile and About on the left
    - a sticky **Your recipe** column on the right
  - The recipe hands off to the Builder.
- **Builder:**
  - Empty: the composer with example chips.
  - Active: two columns (chat | playlist), the 3-step loading card, refine chips (pre-filled
    follow-ups), and a mosaic hero.
  - Also the unmatched-song notice with Swap, and dimming during refines.
- **Profile:**
  - The header with drifting blobs, and a one-sentence summary computed from data we already
    have.
  - An insights row whose actions go to the Builder or DJ.
  - A 12-column module grid with expand.
- **DJ:**
  - Immersive background from the cover's hue.
  - Glass widgets restyled to the handoff's Now playing (100px cover, 40-bar visualizer,
    gradient progress), controls, Next moves (move groups in an auto-fill grid), Requests and
    Up next.
  - A Host preset matching the handoff's 3 | 6 | 3 columns.
  - No page scroll at ≥ 1180px: the grid fills the height and each panel scrolls on its own.
- **Responsive to tablet:**
  - The breakpoints move to the handoff's (desktop ≥ 1180, tablet 760–1179).
  - The header's 800px minimum is removed.
  - The Explore and Builder pages stack below desktop.

### Out of scope (Part 2 milestones, or not planned)

- **F1:** Settings General (text size, compact rows, the Playback animations toggle, Clean only,
  Lower Spotify while previewing) and the first-run flow.
- **F2:** previews.
- **F3:** new DJ features. Night presets, per-move refresh feedback, Familiar ↔ New, DJ mode
  without an AI key, Save tonight's set, Compass + keyboard moves, the Playlist widget, and Up
  next drag reorder + Play now + Undo.
- **F4:** the ⌘K command palette.
- **F5:** the phone layout and bottom tab bar.
- **Not planned:** the prototype's Sidebar nav variant and its Flat page style. The owner chose
  Immersive; the Top bar nav is the default.

## Tech Stack & Architecture

There's no new framework. It stays SvelteKit 1 + Svelte 4 with plain scoped CSS.

- **Tokens.** `routes/styles.css` stays the single token source. Existing names keep their
  meaning and take the handoff's values:
  - `--surface-0` `#0a0a0c`, `--surface-1` `#131316`, `--surface-2` `#24242a`
  - `--text-primary` `#f3f3f5`
  - `--accent` unchanged
  - new: `--glass`, `--glass-blur`, `--popover`, `--success`, `--danger`

  `dj.css`'s page-scoped tokens and controls move up to the global layer, since every page now
  uses the same buttons, segments and toggles.
- **Shared primitives** in `lib/components/ui/`:
  - `SongRow`, `Segmented`, `Toggle`, `GlassCard`
  - `Skeleton` (shimmer)
  - `Visualizer`, `Blobs`, `CoverGlow`
  - `Toast` and a `toast` store

  Pages compose these instead of each styling its own controls.
- **Ambience everywhere.** `lib/dj/ambience.js` already samples a cover's hue for the DJ. It
  becomes the source for the Explore, Profile and DJ backgrounds through a small `hue` store, so
  all three pull from the same sampler.
- **UI scale.** The 90% default goes through CSS `zoom` on `.app`, because the styles are
  px-based and a rem refactor isn't worth it. Risk: gridstack's drag maths under `zoom` (see
  Risks). An R0 spike confirms it, and the fallback is scaling the type tokens instead.
- **DJ grid.** Keep gridstack, presets and Edit layout. The handoff's Host is a preset:
  - Host = 3 | 6 | 3 columns. The handoff has 3 | 6 | 3.4, and 12 columns can't do .4.
  - Desktop fill is a `cellHeight` computed from the viewport height, so the grid fills the
    screen without page scroll.
  - Board and Focus stay; they aren't in the handoff, but they're shipped and nothing replaces
    them.
  - Compass arrives as a preset in F3, as the handoff's repo map suggests.
- **No backend changes in Part 1.** Every new endpoint is in Part 2:
  - F2: Deezer preview URLs and a `/player/volume/` route.
  - F3: move feedback in `/dj/suggest/`, a library seed, a Last.fm fallback, and save-set.

## Milestones

| # | Milestone | Description | Dependencies |
|---|---|---|---|
| R0 | Foundations | Tokens, Geist, global controls (from `dj.css`), keyframes, app-wide icons, `ui/` primitives, `zoom` + gridstack spike | — |
| R1 | Shell | Header + segmented nav, Playlists dock, mini player, AI settings popover, toasts; header min-width removed | R0 |
| R2 | Shared song row | `SongRow.svelte`; replace `SongCard`, `PlaylistResult` rows, `PickRow`, `UpNext` rows, search rows; drag-to-playlist on every row | R0 |
| R3 | Explore | Idle hero + mood chips + cover tiles; song page with Path, hero, recipe column, Builder hand-off | R1, R2 |
| R4 | Builder | Composer, chat \| playlist columns, loading steps, refine chips, mosaic hero, unmatched + Swap | R1, R2 |
| R5 | Profile | Header + blobs, summary sentence, insights row, 12-col module grid | R1, R2 |
| R6 | DJ | Immersive background, glass widgets per handoff, Host preset 3\|6\|3 + fill-height, tablet breakpoints; then `/design audit` + `polish` over Part 1 | R1, R2 |
| F1 | Settings + first run | General tab (text size, compact, motion, clean, duck), persisted; first-run onboarding + empty states | R6 |
| F2 | Previews | Deezer 30s preview via `<audio>`, 15s preview pill, Spotify volume ducking (`/player/volume/`) | R6 |
| F3 | DJ features | Night presets, per-move refresh feedback, Familiar↔New (b951bf), no-key DJ (9341cc), Save tonight's set (9da022), Compass + keys, Playlist widget, Up next reorder/Play now/Undo | R6 |
| F4 | Command palette | ⌘K: songs + Go to; on DJ adds to Up next | R1 |
| F5 | Phone layout | < 760: bottom tab bar, sheet settings, full-width dock, single-column DJ | R6 |

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| CSS `zoom` breaks gridstack drag/resize coordinates | Medium | Medium | Spike in R0; if it breaks, scale the type tokens instead (sizes × 0.9) and leave `zoom` for F1's setting only on non-DJ pages |
| `backdrop-filter` over animated blobs is slow on a laptop at a party | Medium | Medium | Blobs are 3 blurred elements, GPU-transformed only; pause when hidden (`visibilitychange`) and when paused; measure frame time in R6 |
| Text on glass over bright covers drops below 4.5:1 | Medium | Medium | Clamp blob lightness/chroma (as `ambience.js` already does) and test against a white/yellow cover |
| The reskin silently drops a working feature | Medium | High | Each milestone checks the "Nothing lost" list in the browser before review |
| Geist Mono in data-dense places (times, counts) reads worse than tabular Inter | Low | Low | Use `font-variant-numeric: tabular-nums`; judge in R1 |

## Dependencies

- `@fontsource/geist` and `@fontsource/geist-mono` (5.3.0). Self-hosted, so no Google Fonts
  request.
- No new runtime libraries. gridstack stays at 13.3.0.

## Open Questions

1. **DJ grid:** keep the customizable grid? The prototype has no Edit layout, Board or Focus,
   only fixed Host and Compass. The plan keeps the grid (see Tech Stack). Confirm before R6.
2. **The Profile summary sentence** ("mostly rap and R&B, 76% from the 2020s, … around 8pm"):
   build it from the existing profile data, with no AI. That's assumed here.
3. **"Start an evening DJ set" on Profile** needs night presets (F3). Until then it just opens
   the DJ.

## Decisions Log

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Phasing | Reskin first (R0–R6), features after (F1–F5) | About half the handoff is new behaviour with backend work. Restyling with today's features ships a visible win without coupling it to those risks | 2026-10-27 |
| Glass + drifting blobs | Keep, as designed | The owner chose the Immersive direction. This **reverses** the DJ brief's "no glassmorphism / aurora" rule (2026-10-25). Guardrails: blobs move only while playing, off under reduced motion, contrast checked | 2026-10-27 |
| Font | Geist + Geist Mono replace Inter + Fira Mono | Matches the handoff's tight display headlines; self-hosted via `@fontsource` | 2026-10-27 |
| Nav and style variants | Top bar + Immersive only | These are the prototype's defaults. Sidebar and Flat aren't built | 2026-10-27 |
| UI scale | CSS `zoom: 0.9` on `.app` (pending R0 spike) | Styles are px-based; a rem refactor is out of proportion | 2026-10-27 |
| DJ layout | Keep gridstack, presets and Edit layout; Host becomes 3\|6\|3 with fill-height | Already shipped and tested; the handoff's repo map says to add Compass as a preset, which implies the grid stays | 2026-10-27 |
| Handoff in repo | Copied to `docs/design/redesign-2026-10-27/` | The spec should outlive the Downloads folder. The prototype contains the owner's name (mock data), and the repo is public | 2026-10-27 |

### R0 spike result (2026-10-27): no CSS `zoom`

CSS `zoom` breaks gridstack. Under `zoom: 0.9` on `.app`, widgets land in the wrong place after a
resize. Undoing the zoom on the grid and re-applying it inside each widget fixed placement but
not dragging. In a headless Playwright drag, a widget moved with zoom off and stayed put with any
zoom on.

**Decision:** no `zoom`. Part 1 uses the handoff's sizes at 100%. The 90% default text size
(the handoff's "Text size" setting) is now part of F1. It needs a mechanism that leaves the DJ
grid unzoomed, such as a root font-size scale with rem-based type.

### Part 1 result (2026-10-27)

R0–R6 are on `dev`, in commits 4b3e1ae..HEAD. Each page was checked in a headless browser with
mocked backend data at 1280 and 924 wide, then in the signed-in browser with real data.

The audit found and fixed these:
- **Layout animations:** the dock's margin and the genre bars' width animated layout
  properties. Now the page reflows once and the bars use a transform. The detector is clean.
- **Contrast:** `--text-subtle` went from 0.45 to 0.5 for 4.5:1, along with every hard-coded
  35–45% text colour.
- **Guidelines:** curly quotes, real ellipses, `theme-color`, and a skip link.
- **Explore:** a restored song with no Path gets a crumb.

Bugs found on the way:
- The Playlists panel's "New playlist" sent Deezer keys to Spotify without resolving them.
- Profile's expand never re-rendered.
- TrendChart's edge labels clipped.

Not built, and why:
- **Explore Play button:** no play-this-song endpoint.
- **Builder Swap:** the backend never returns unmatched songs.
- **Builder playlist name:** the backend doesn't name playlists, so the name comes from the
  prompt.
- **Profile's "Start an evening DJ set":** opens the DJ; night presets are F3.
- **Explore results:** the per-song heart and Add selected are gone. The Builder keeps the
  heart.
- **Board and Focus:** kept. They aren't in the handoff and nothing replaces them.

Type-check errors dropped from 25 to 3. The 3 left are pre-existing, in `spotifyAuth.js`.

### F1 result (2026-10-27): Settings and first run

- **Settings → General:**
  - Text size: 80–120%, default 90% (the handoff's default).
  - Compact song rows.
  - Clean only. It drives the DJ's synced `clean` option and now also hides explicit songs in
    Builder and Explore results, with a "N hidden" note.
  - Playback animations: pauses the visualizer, bars, cover glow and drifting colour. Spinners
    and skeletons keep moving.
  - Account row with Log out.
  - Reset to defaults.
  - Saved per device under `bb-zoom`, `bb-compact` and `bb-motion`.
- **Settings → AI:** the existing AI panel, now shared with first run through `lib/llm.js` and
  `AiForm`.
- **First run:** Connect Spotify → pick an AI or "Skip for now" → choose where to start.
  - It's saved per step (`bb-onboarding`), so it survives Spotify's sign-in redirect.
  - Logging out brings it back. People already signed in never see it.
- **Deviation, text size:** it multiplies every `font-size` by `--text-scale` rather than
  zooming. CSS zoom breaks the DJ grid (R0 spike), so spacing and control sizes don't scale.
- **Deviation, previewing:** "Lower Spotify while previewing" moves to F2, with the previews.
- **Deviation, AI skip:** the design's "Skip, use Last.fm only" is "Skip for now". A DJ that
  needs no AI key is part of F3.

---

## F3 breakdown: DJ features (2026-10-27)

F3 runs as eight sub-milestones, smallest and frontend-only first. Each is committed and
checked on its own. The live check with real music waits for the owner's OK, because Spotify
quota and AI tokens are real costs.

| # | Sub-milestone | Scope | Backend |
|---|---|---|---|
| F3a | Night presets | Dinner / Pregame / Peak / Afterparty in the DJ toolbar. Each sets Safe↔Bold and the goal (Familiar↔New joins in F3d). Profile's "Start an evening DJ set" opens the DJ with the preset applied | — |
| F3b | Up next editing | Undo on every queue edit (remove, reorder, later, clear), Clear, Play next | — |
| F3c | Per-move refresh + feedback | Each move group gets its own refresh, with "What's off about these?" chips. Only that move is re-asked; the feedback is shown as "Avoiding: …" | `moves` and `feedback` fields on `/dj/suggest/` |
| F3d | Familiar ↔ New | A slider (From your library / Mix / Mostly new), seeded with the listener's top tracks (b951bf) | `familiar` + `library` refs in the prompt |
| F3e | DJ without an AI key | Last.fm similar tracks, checked on Deezer, as a "Like this one" move; the controls show the pick source (9341cc) | A no-LLM branch in `/dj/suggest/` |
| F3f | Save tonight's set | A modal with the name, stats (time played, DJ picks kept, guest requests), the songs played and an optional AI recap, then save to Spotify (9da022) | `description` on create-playlist; a recap prompt |
| F3g | Compass layout | A 3×3 preset around Now playing, with keys: arrows for Lift / Drop / Pivot / Curveball, H for Hold, T for Toward. The card flashes when a key adds a pick | — |
| F3h | Playlist widget | Pick one of your playlists, filter it, + to queue. The Builder's "Start a DJ set from it" sends its songs to Up next | Playlist-tracks route, if one is missing |

**Play next instead of Play now.** True "play now" would mean skipping past songs already sent
to Spotify's queue, which the app can't take back. "Play next" (move the song to the top of Up
next) is honest and safe.

### F2, F4, F5 results (2026-10-28)
Built in parallel by three builders on their own worktrees and branches (f2, f4, f5), merged into
dev, then reviewed together. Tests: frontend 95, backend all OK.
- **F2 Previews:** a 30 s Deezer clip (`GET /preview/`, Deezer only, never cached) through
  `<audio>`, stopping at 15 s. One global preview with a pill (Queue it / Stop). Covers in Explore,
  Builder, DJ moves and search have a play badge. "Lower Spotify while previewing" (General, on by
  default) ducks to 20% via `POST /player/volume/` and restores on stop, end, and page hide/close
  (keepalive). Not wired yet: Up next, Requests, Recent, the Playlist widget, Profile top tracks.
- **F4 Command palette:** ⌘K / Ctrl+K or the header Search button. Recent songs, type-ahead
  matches from 3 characters (debounced, the existing Deezer/Last.fm search), Go to pages and
  Settings. On the DJ page a song goes to Up next; elsewhere it opens in Explore.
- **F5 Phone layout:** breakpoints on effective width (window ÷ text scale) set as `data-bp` /
  `data-narrow` on the root; every 759/1179 media query converted. Phone: bottom tab bar, header
  nav hidden (Search and Playlists icon-only), mini player trimmed, settings sheet, full-width dock,
  16px padding. Below desktop the DJ grid stacks (6 columns tablet, 1 phone), Now playing first in
  Compass and Board. Edit layout is desktop-only.
- **Review fixes:** stacked heights no longer leak into the saved layout; the grid's breakpoints
  scale with text size; a preview right after a restore ducks from the restored volume; Queue it
  can't stick; the dock no longer squeezes the page on phone; panes leave room for the tab bar.
- **Left as is:** `/preview/` answers 503 (not 404) for a Deezer id that doesn't exist, and has no
  per-IP limit (it shares Deezer's rate gate with search). A phone first paints the desktop layout
  until the app starts.
- **Needs a real phone:** the safe-area inset under the tab bar, ducking on the device that's
  playing (some devices refuse volume changes), and volume restore when a tab is killed.

### The moves board stays (2026-10-28, owner request)
The board of moves no longer resets when the song changes or the page reloads. It is saved on the
device (`dj_board`, dropped after 6 h idle like the set log) with the song it was made for; the DJ
toolbar shows "Picks for <song> · New picks for <now playing>" when they differ. Option changes
(Bold, Familiar, goal) still ask for new picks; a failed round keeps the old board. Autofill and
Driver queue from the board and only ask again once they've used every pick on it. **DJ controls
→ "New moves every song"** (this device, off by default) restores the old ask-every-song behaviour.

### Faster DJ picks (2026-10-29)
Measured on the real DJ prompt through `claude -p`: **Opus 39 s** (the CLI's default, which the
helper relay used because it named no model), **Sonnet 13 s**, the `haiku` alias (Haiku 4.5) 94 s
with runaway output, and Haiku 5.5 2.4 s but it returned only one of five moves. One move alone on
Sonnet: ~5 s, and three in parallel finished in ~7 s.
- The relay now names `claude-sonnet-5-5` (`HELPER_MODEL`); the helper passes it to `--model`.
- Rounds ask one move per request, all at once, and each move shows as it lands
  (`fetchBoard`, `mergeMove`, `roundMoves`); Groq stays one request (per-minute token limit).
  `/dj/suggest/` caches recently-played (60 s) and Last.fm track info (10 min) per instance, since
  a round is now 5 requests (10 through the relay).
- Background boards: when the song changes and the board is kept, the new song's board is built
  quietly, so "New picks" is instant; ~45 s before a song ends, the board for the next song the DJ
  sent is built too. Rounds for the same answer are joined, not repeated.

### DJ chat (2026-10-29, owner request)
"Ask the DJ" at the bottom of DJ controls. `POST /dj/chat/` (`routers/dj_chat.py`) sends the
message with the night (now playing, recent, queued), the controls and the current layout plus the
widget catalog through the usual AI path (helper relay included). The AI answers with a reply,
up to 6 songs (checked on Deezer like the moves; + adds to Up next, cover previews) and actions,
validated on the server (`clean_actions`) and again on the page (`layoutFromChat`):
preset, a full custom layout, controls (mode, Safe↔Bold, Familiar↔New), the goal, and
`refresh_moves` (a note added to every move's feedback, then the board is re-asked). The log is
kept on the device (`dj_chat`, last 30), so it survives layout changes and reloads. Real Sonnet:
13 s per message, valid JSON with picks and a valid layout.

### Genres check and listening history (2026-10-29)
- **Genres are empty.** A real Profile load (medium_term, 50 artists) returned `genres: []` for
  all 50 top artists, so Top genres and the genre part of the summary never show. Fix candidate:
  Last.fm `artist.getTopTags`, cached. `/me` `followers.total` still works (29), despite the Feb
  2026 changelog.
- **Listening history** (`listening_history`, migration 20261029160000, applied to boomin-beats).
  One row per play keyed by (user, played_at); RLS on, no policies, backend-only. Saved from
  `/spotify/recently-played/` (Profile) and `POST /history/sync/` (DJ page on open + every
  30 min). `/spotify/recently-played/?tz=` adds `history`: 90-day stats in the caller's local
  time (hours, days, 12 weeks of plays/minutes/artists, streak, top artist). Profile's listening
  clock uses it once it holds more than 50 plays, and a new "Your listening" card shows hours,
  plays, day streak, artists this week and hours per week. Gaps: plays older than the last 50
  when neither Profile nor the DJ was opened in time.
- **Genres fixed with Last.fm** (same day). `/get-profile/` fills empty artist genres from
  Last.fm `artist.getTopTags` (`services/genres.py`), keeping genre-like tags (no artist names,
  nationalities, decades or opinions; "hip-hop"/"hip hop" and "rnb"/"r&b" merged), top 3 per
  artist, cached 30 days in `track_lookup` under a `lastfm-tags` key. Live history check: the
  first Profile load after deploy stored 51 plays.
- **Genres live check:** 49 of 50 top artists got genres, Profile load 1.6 s. Place tags ("north
  carolina") are now filtered, including from cached rows.
- **What's new vs staples** (top-item churn). `GET /spotify/top-churn/` fetches top artists and
  tracks for all three ranges (6 calls, no search, cached 10 min) and compares them
  (`services/churn.py`): new this month (4-week top only), rising (≥10 places higher than over
  6 months), staples (in all three), fading (all-time top, missing from the last 4 weeks). A Profile
  card with Artists/Tracks tabs; artists open a Builder prompt, tracks open in Explore.
- **Your library** (Profile). `GET /spotify/library-stats/`: Liked Songs (`GET /me/tracks`, still
  200 after the Feb 2026 migration) summarised in `services/library.py` (total, liked this year and
  month, likes per month for 12 months, liking since, decades, most-liked artists) plus playlist
  stats (yours, songs in them, biggest, collaborative). A full scan is one request per 50 likes
  (capped at the newest 5,000), cached in `track_lookup` under ('library', user) and rebuilt only
  when the total or newest like changes; otherwise one request per visit. The last Profile row is
  Eras / Your library / Taste over time at 380px.
