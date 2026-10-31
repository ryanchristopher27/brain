# Brainstorm: LLM Playlist Generation
_Date: 2026-06-04 | Feature: AI-powered playlist builder_

---

## Problem / Opportunity

Ryan's Boomin Beats is a Spotify-integrated web app (SvelteKit + Django) that lets users explore music, search tracks, and get Spotify-seeded recommendations. The existing recommendation engine is constrained to Spotify's own similarity model — it requires a seed track and stays within Spotify's catalog graph.

The opportunity: let users describe what they want in natural language and have an LLM generate a tailored playlist that isn't tied to Spotify's recommendation logic. A user should be able to say "songs for a late-night drive in the rain" or "build me something like Kendrick's moody instrumentals but with more jazz influence" and get a curated, playable result.

---

## Goals

- Natural language prompting (one-shot or conversational) generates a song list
- Songs are validated against Spotify's catalog and surfaced in the app
- User can select individual songs, add the full list as a Spotify playlist, or queue everything to their active player
- Support Claude (Anthropic) and OpenAI as LLM providers via user-supplied API keys
- Session-based key storage initially; persistence deferred to a future auth layer

---

## Audience

Personal / developer use initially — the owner building and running this locally. Designed to scale to shared use later with minimal rework (BYOK already anticipates multi-user scenarios).

---

## Constraints

- **BYOK only:** no app-level LLM key; user must supply their own
- **Session-based key storage** in v1 — no DB writes, no user identity required yet
- **Existing stack:** SvelteKit frontend, Django backend, Spotipy, Python
- **New Spotify OAuth scopes required:**
  - `playlist-modify-private` — create playlists on user's account
  - `user-modify-playback-state` — add songs to active playback queue (requires an active Spotify device)
- Direction C (LLM → Spotify recommendation params) explicitly out of scope — the goal is to escape Spotify's recommendation graph, not stay within it

---

## Ideas & Directions

### Direction A: LLM → Structured Output → Spotify Validation ✅ Selected for v1

1. User writes a prompt (e.g., "moody jazz for 3am")
2. Backend sends prompt (+ chat history for conversation) to the selected LLM
3. LLM returns a structured JSON list: `[{ "title": "...", "artist": "...", "reason": "..." }]`
4. Backend fires parallel Spotify searches for each `{title, artist}` pair
5. Matched songs surface with Spotify track data (album art, ID, URL)
6. Unmatched songs are flagged — user can manually swap them out
7. User acts on the result: select songs, add as playlist, or queue all

**Why this wins:** Fast to build, fast to run (parallel searches), naturally supports conversation (just send message history), and gives the user visibility into misses rather than silently dropping songs.

**Hallucination handling:** For each `{title, artist}`, search Spotify as `track:{title} artist:{artist}`. If top result confidence is low or empty, flag with "Not found on Spotify" — allow user to search and swap manually.

---

### Direction B: LLM + Tool Use / Function Calling (Upgrade Path)

- LLM is given a `search_spotify(query)` tool it calls before adding each song
- Every song in the final list is confirmed to exist before returning
- Higher accuracy, zero hallucinated songs
- More latency (sequential tool calls), more complex plumbing

Not selected for v1 but the natural upgrade path once A is shipped and the "not found" rate is measured.

---

## Architecture

### Backend — New Django Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/llm/connect` | POST | Validate provider + API key, store in Django session |
| `/api/llm/generate-playlist` | POST | Prompt LLM, validate results against Spotify, return merged list |
| `/api/spotify/create-playlist` | POST | Create playlist on user's Spotify account (`playlist-modify-private`) |
| `/api/spotify/queue` | POST | Add songs to active playback queue (`user-modify-playback-state`) |

### Frontend — New SvelteKit Components / Routes

- **LLM settings panel** — provider selector (Claude / OpenAI) + API key input; validate on submit; session persists until reload
- **Chat / prompt interface** — text input, scrollable message history, shows both user prompts and assistant responses
- **Playlist result view** — song cards with album art, title, artist, match status badge, select checkbox
- **Action bar** — "Add All as Playlist", "Queue All", "Add Selected to Playlist", "Queue Selected"

### Spotify OAuth Scope Upgrade

Add to the existing `SCOPE` variable in all Django views:

```
playlist-modify-private user-modify-playback-state
```

Queue endpoint note: `user-modify-playback-state` requires an active Spotify device. If none is active, return a clear error the UI can surface to the user ("Open Spotify on a device first").

---

## LLM Output Format

System prompt instructs the LLM to return only valid JSON in this shape:

```json
[
  {
    "title": "Song Name",
    "artist": "Artist Name",
    "reason": "One sentence on why this fits the prompt"
  }
]
```

The `reason` field displays as subtext or a tooltip on each song card — gives the playlist a curated feel and helps users understand picks they don't recognize.

---

## Conversational Flow

- Frontend maintains a `messages` array: `[{ role: "user" | "assistant", content: "..." }]`
- Each new prompt appends to the array; full history sent to backend on every turn
- LLM receives full history and returns a **complete revised playlist** (not a delta) — simpler to render and avoids merge complexity
- Chat history resets on page reload in v1 (session-based; persistence is a future concern)

---

## Enhancement: Personalization via Account Analysis

The app already has an account analysis feature. The LLM system prompt could optionally include the user's top artists and genres from that feature to bias recommendations toward their actual taste. This is a low-effort, high-impact upgrade to layer on top of the base feature.

---

## Recommendations

**Ship Direction A with Spotify validation.** The LLM generates the list fast, parallel Spotify searches confirm existence, and flagged misses give the user control without blocking them. Conversational mode is a thin layer on top — just maintain message history on the frontend and send it along.

**Start one-shot, add conversation in the same pass.** The only meaningful difference is tracking `messages` state in the Svelte store. Not worth splitting into two releases.

**Use Django session for key storage.** Avoids building any auth or encryption infrastructure in v1. When persistence becomes a goal, that's the moment to introduce user accounts.

---

## Suggested Decisions (All Confirmed)

- [x] BYOK, session-based storage in v1
- [x] Direction A: LLM structured output + Spotify validation pass
- [x] Claude (Anthropic) + OpenAI as supported providers
- [x] Result displayed in app — user can select, add as playlist, or queue
- [x] New Spotify OAuth scopes: `playlist-modify-private`, `user-modify-playback-state`
- [x] One-shot and conversational both supported in v1

---

## Open Questions for /plan

- What does the LLM settings UI look like? Modal, sidebar panel, or a dedicated `/settings` route?
- Where does the chat interface live in the app? New route, drawer, or embedded on an existing page?
- How is the LLM system prompt crafted? What context does it receive beyond the user's message?
- Should the system prompt optionally include the user's top artists/genres from account analysis?
- What's the retry strategy for Spotify search misses before flagging as "not found"? (e.g., try again without `artist:` filter)
- Does conversation history persist across navigation, or only within a single session on one page?
- How many songs should the LLM target by default if the user doesn't specify? (Suggest: 10–15)

---

## Next Steps for /plan

1. Define new Django apps + endpoint signatures in detail
2. Map SvelteKit route/component structure for the new UI
3. Write the LLM system prompt template (including output format enforcement)
4. Define the Spotify search + validation logic (query format, confidence thresholds, retry strategy)
5. Plan the OAuth scope upgrade path and session key storage implementation
6. Decide on UI placement and flow for the chat + result views

---

# Brainstorm: Song Exploration & Discovery (Pillar 1)
_Date: 2026-06-05 | Feature: Explore page — song profile + tag-driven discovery_

---

## Problem / Opportunity

The app has two pillars: song-centric exploration and prompt-based playlist creation. Pillar 2 (LLM playlist builder) is scaffolded. Pillar 1 needs its own feature: given a specific song, show the user what makes it what it is, and let them discover similar songs based on the aspects they care about.

Spotify's recommendations and audio features endpoints are deprecated for new apps, removing the obvious data source. The replacement: **Last.fm as the structured data layer, LLM as the interpretation and discovery engine.**

---

## Goals

- User can search for any song using Spotify's autocomplete
- App builds a rich profile of that song: LLM qualitative analysis + Last.fm tags and metadata
- User selects which aspects (tags) they want to match in discovery
- App generates a list of similar songs based on selected tags + song context
- Results are validated against Spotify and displayed with the same save/queue actions as Pillar 2

---

## Audience

Same as Pillar 2 — personal/developer use initially. The explore page is the primary discovery surface for song-centric users (vs. vibe/prompt-centric users who go to the playlist builder).

---

## Constraints

- Spotify recommendations and audio features endpoints are unavailable for new apps
- Last.fm API requires a free API key (5-minute signup) — added to `.env`
- Discovery stays song-centric on the explore page — free text input belongs to Pillar 2 (playlist builder), not here
- Tag pills are the primary discovery affordance — radar chart deferred to a future visual pass
- Reuse existing playlist builder pipeline for discovery results (same backend endpoints, richer LLM context)

---

## Confirmed Decisions

| Decision | Choice |
|----------|--------|
| Home page | Search-only for now; explore page is the destination. Home page filled in later. |
| Song profile display | Last.fm tag pills + LLM prose analysis. Radar chart deferred. |
| Discovery input | Spotify autocomplete song search — tag selection drives discovery. No free text on this page. |
| Last.fm API | Yes — free key added to project |

---

## Architecture

### Explore Page Flow

1. User lands on `/explore`
2. Spotify autocomplete search (reuses existing `/search/` endpoint)
3. User selects a song → app fetches song profile
4. Song profile displays: LLM analysis prose + Last.fm tag pills + metadata (listeners, play count)
5. User selects tags they want to match (pills are toggleable)
6. User clicks "Discover" → backend calls LLM with song context + selected tags → iterative Spotify validation → results displayed
7. User can save as playlist or queue — same `PlaylistResult` component as Pillar 2

### New Backend

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/song/profile/` | GET | Fetch Last.fm data + LLM analysis for a given title + artist |

**`routers/song_profile.py`** — calls Last.fm `track.getInfo`, passes tags + metadata to LLM, returns structured profile

**`services/lastfm_client.py`** — Last.fm API wrapper: `track_info(title, artist)` returns tags, listeners, wiki summary, similar tracks

**LLM system prompt for song analysis:** Given the song title, artist, and Last.fm tags, produce a 2-3 sentence qualitative description of the song — mood, instrumentation, lyrical themes, era, cultural context. Ground the analysis in the provided tags. Return as plain prose (no JSON).

**Discovery reuses existing `/llm/generate-playlist/` endpoint** — the explore page calls it with a richer system context: song title, artist, selected tags, and LLM analysis as grounding.

### New Frontend

| File | Purpose |
|------|---------|
| `routes/explore/+page.svelte` | Main explore page |
| `lib/components/SongSearch.svelte` | Spotify autocomplete — reusable, extracted from home page logic |
| `lib/components/SongProfile.svelte` | Tag pills + LLM prose + Discover button |
| `lib/components/TagPill.svelte` | Selectable/toggleable tag pill |

**Reused from Pillar 2:** `PlaylistResult.svelte`, `SongCard.svelte` — discovery results render identically to playlist builder output.

### Last.fm API

- Endpoint used: `track.getInfo` (title + artist → tags, listeners, play count, wiki summary)
- Fallback: `artist.getTopTags` if track-level tags are sparse
- API key stored in `.env` as `LASTFM_API_KEY`, read via `config.py`
- No auth beyond API key — free tier is sufficient

---

## What's Not Solved Yet (For /plan)

- **Last.fm matching edge cases** — Last.fm takes title + artist as strings; non-English titles, featuring credits, and remaster titles can cause misses. Need a fallback strategy.
- **Sparse data for obscure songs** — Last.fm tags and LLM knowledge both degrade for less-known tracks. Acknowledged as a known limitation; surface gracefully in UI rather than hiding it.
- **Home page interim state** — the home page currently has search + broken recommendations. Decide what it shows while the explore page is being built. Simple landing / nav redirect is fine for now.
- **SongSearch component** — the autocomplete logic currently lives inline in `+page.svelte`. Extracting it to `SongSearch.svelte` makes it reusable across home and explore pages; decide if this extraction happens in this milestone or later.
- **Navigation** — how does a user get from search results to the explore page? Clicking a song in autocomplete results navigates to `/explore?title=...&artist=...&id=...` with query params.

---

## Recommendations

1. **`/explore` as a new dedicated route** — substantial enough for its own page; query params carry song context so URLs are shareable
2. **Last.fm + LLM profile on a single backend call** — `GET /song/profile/` fetches Last.fm data and calls the LLM in parallel, returns both in one response to avoid frontend waterfall
3. **Tag pills as the primary discovery affordance** — all selected tags get passed as context to the existing `/llm/generate-playlist/` endpoint; no new discovery pipeline needed
4. **Extract `SongSearch` component now** — it will be needed on both the home page (eventually) and explore page; cleaner to extract once than copy-paste

---

## Next Steps for /plan

1. Define `GET /song/profile/` endpoint signature and response shape
2. Define `services/lastfm_client.py` interface
3. Map the LLM prompt template for song analysis (inputs: title, artist, tags, wiki summary → output: prose analysis)
4. Define how selected tags are passed to `/llm/generate-playlist/` — new field in request body or modified prompt construction
5. Map the explore page component tree and data flow
6. Decide on home page interim state during this build
7. Plan Last.fm API key addition to `.env`, `config.py`, and `setup.md`

---

# Frontend Redesign — Sleek Dark Theme (2026-06-22)

## Problem / Opportunity
The current frontend is visually inverted from modern music apps: a light-blue background with dark cards, Arial typography, and inconsistent polish across pages (the profile page lags noticeably behind the explore page). The app works end-to-end but doesn't *look* the part. The opportunity is a cohesive visual redesign that reads as sleek and premium — using Spotify's design language as a proven reference, not a pixel-perfect target.

## Goals
- A sleek, polished, cohesive look across the entire app
- Dark, layered surfaces (Spotify-like depth via elevation)
- Use the existing `#5ec9ff` light blue as the single accent color
- Bring every page up to a consistent quality bar
- Keep it tasteful and restrained — premium over busy

## Audience
Primary user is Ryan (personal project), but the design bar is "something you'd be proud to show off."

## Constraints
- Keep the existing `#5ec9ff` accent — this is the brand anchor
- SvelteKit component structure already exists; redesign should reuse structure where sound, not rebuild from scratch
- No proprietary fonts (Spotify's Circular is licensed) — use a free geometric sans
- Local dev only; no responsive/mobile mandate beyond what already exists (min-width 800px)

## Ideas & Directions

### Direction A — Token swap + polish (low effort)
Flip global color tokens so the background goes dark and blue becomes accent-only. Most components already use `--color-dark-gray` for cards and `--color-light-blue` for accents, so flipping the page background gets ~70% there. Clean up rough edges after. Fast, low-risk, but stops short of "genuinely polished."

### Direction B — Full Spotify structural clone (high effort)
Dark background + left sidebar nav (Library/Explore/Builder). Closer to how Spotify actually feels, but a big layout restructure that's overkill for a 3-page app with no persistent "now playing" concept.

### Direction C — Dark + top nav, full component rewrite (medium effort) [CHOSEN]
Dark layered background, keep and slim down the top header, full styling pass on every component: typography upgrade, consistent card radius + hover states, refined buttons, spacing rhythm. Bigger than A, smaller than B. Lands the "sleek" goal without a structural rewrite.

## Recommendations
Go with **Direction C**, tuned by the confirmed decisions below:

- **Surfaces:** layered dark — `#0a0a0a` page → `#181818` cards → `#282828` hover. Depth-via-elevation is the biggest "sleek" lever.
- **Accent:** minimal/monochrome. Mostly grayscale dark UI; `#5ec9ff` reserved for active states, primary buttons, and links. Restraint reads as intentional.
- **Typography:** swap Arial → **Inter**. Heading weights 600–700, comfortable body line-height.
- **Components:** full pass — consistent radius, real hover transitions, refined buttons, better spacing. Profile page brought up to explore-page quality.
- **Nav:** keep top header, slim it down, cleaner active state.
- **Motion:** subtle — smooth hover transitions, gentle fades on results loading. Tasteful, not flashy.
- **Scope:** everything this round — global tokens + all pages + every component, one cohesive pass.

## Suggested Decisions (confirmed)
- [x] Direction C — dark, polished, top nav
- [x] Accent intensity: **minimal / monochrome**
- [x] Scope: **everything** (tokens + all pages + all components)
- [x] Motion: **subtle**
- [x] Keep top navigation (no sidebar)
- [x] Typography: Inter (pending final confirmation in plan)

## Open Questions (for /plan to resolve)
- Final font choice: Inter vs. DM Sans (both free, geometric) — lock one
- Exact surface/elevation token values and naming (`--surface-0/1/2`?)
- Whether to introduce semantic tokens (`--surface`, `--text-primary`, `--text-muted`, `--accent`) vs. keep the current raw color names
- Build order across components to minimize churn (design system → shell/header → pages)
- How to handle the legacy `styles.css` light-theme tokens (`--color-bg-0/1/2`, `--color-theme-1/2`) — remove or repurpose
- Profile page is the roughest — does it need structural changes or just restyle?

## Next Steps (what /plan needs)
1. Lock the final type + token system (semantic naming, surface elevation values)
2. Define the build order (design system first, then shell, then pages)
3. Inventory every component + page that needs a pass
4. Decide the legacy `styles.css` cleanup approach
5. Set acceptance criteria for "sleek" (consistency checklist: radius, spacing, hover, type scale)

---

# Cover Art on Playlist Results (2026-06-23)

## Problem / Opportunity
The discovery results (and later the Playlist Builder results) are a plain list of song rows on a flat surface. Album art is available per song but unused at the playlist level. Adding the cover art as a larger visual element would make the results feel richer, more immersive, and more on-brand — without changing the underlying functionality.

## Goals
- Make the playlist/discovery results visually richer using album cover art
- Keep it aesthetically pleasing and cohesive with the sleek dark theme (priority: looks)
- Tie the results visually + semantically to their source (the selected song)
- Stay readable — album art is unpredictable (bright/busy), text must remain legible

## Audience
Personal project; the bar is "something that looks polished enough to show off."

## Constraints
- A generated playlist has **no single cover** — it's many songs with many covers. The chosen anchor is the **selected/reference song's** cover, not the playlist's.
- `PlaylistResult` is shared by Explore discovery results AND the Playlist Builder — changes must be gated/optional so Explore can adopt first.
- **Key prerequisite:** the selected song's cover image is not reliably available today. The search-select path provides `image` (after the recent `search.py` change), but the Explore→ chain rebuilds the next song as `{title, artists, id}` and drops the image, and `/song/profile/` returns no image. The image must be threaded through both selection paths.
- Dark scrim / gradient mask required for text contrast over arbitrary covers.

## Ideas & Directions

### Source image (which cover anchors the visual)
- **Selected/reference song's cover [CHOSEN]** — on Explore, the song you explored from; semantically perfect as the anchor for "similar songs"
- First/top result's cover — simplest, used as the Builder fallback later
- 2×2 mosaic of 4 covers — Spotify-style auto-cover; busier as a background
- Dominant color extracted from art — sleekest ambient look, but needs canvas + CORS work

### Treatment (how it appears)
- **Ambient blurred backdrop + "Based on" band [CHOSEN]** — selected song's cover, heavily blurred at low opacity, bleeding from the top of the results container and fading into `--surface-1` via a gradient mask, dark scrim for readability. Layered on top: a crisp cover thumbnail + "Based on *Song* by Artist" replacing the current "Similar Songs" header.
- Hero header only — crisp cover + meta, no wash (cleanest, less immersive)
- Blurred backdrop only — no crisp header (simplest)

## Recommendations
Build the **ambient blurred backdrop + "Based on" header**, anchored to the **selected song's cover**, scoped to **Explore discovery results** first, with `PlaylistResult` taking an optional cover prop so the Builder can adopt it later (first-song cover).

Rationale: matches the user's "large with opacity in the background" instinct, ties results to their source, stays immersive but readable, and avoids the cost/complexity of color extraction or per-row art treatments. The gradient-masked fade + scrim keeps it tasteful on any cover.

## Suggested Decisions (confirmed)
- [x] Source = selected/reference song's cover
- [x] Treatment = ambient blurred backdrop + crisp "Based on" thumbnail header (aesthetic call delegated to assistant)
- [x] Scope = Explore discovery results now; extend to Playlist Builder later
- [x] Enabling change = thread the selected song's image through search-select + explore-chain paths

## Open Questions (for /plan)
- Builder's later source image: first-song cover vs 2×2 mosaic (defer; note it)
- Backdrop tint: neutral dark scrim (simpler) vs subtle tint toward the cover's dominant color (nicer, more work) — lean neutral for v1
- Exact placement of the "Based on" header: inside `PlaylistResult` vs the Explore page's existing "Similar Songs" header slot
- Fallback when no cover image is available (e.g., older selections): graceful no-backdrop state

## Next Steps (what /plan needs)
1. Define how the selected song's `image` is propagated (SongSearch already; SongCard explore button + `onExploreSong` need to carry it; consider persisting on `selectedSong`)
2. Decide `PlaylistResult` API: optional `coverImage` + `coverLabel`/`coverSubtitle` props
3. Spec the backdrop layering (absolute blurred img, gradient mask, scrim, z-index) within the existing `.result-container`
4. Map the "Based on" header markup + where it lives
5. Acceptance criteria: readable on bright covers, graceful no-image fallback, no layout shift

---

# Deeper Spotify Account Integration (2026-06-23)

## Problem / Opportunity
The app authenticates with Spotify but barely uses the account beyond reading the profile and creating brand-new playlists / queueing. There's a lot of untapped value in the user's actual library: existing playlists, Liked Songs, and top tracks. The throughline for this round is **doing more with the connected account**, led by the top-requested feature: adding songs to *existing* playlists.

## Goals
- Add discovered/explored songs to the user's **existing** playlists (not just new ones)
- Support both **bulk** (discovery results) and **per-song** (individual card) adds
- Let users **save songs to Liked Songs** from the app
- Use the user's **top tracks as discovery seeds** ("explore from what you already love")
- Surface the **Last.fm wiki summary** (already fetched, currently discarded) + basic metadata

## Audience
The signed-in user (personal project); bar is "feels like a first-class Spotify companion."

## Constraints
- **New scopes required** for Liked Songs: `user-library-modify` (write) and `user-library-read` (saved-state indicators). The current PKCE scope set lacks these → **one re-auth (log out / log in)** needed.
- **Enabling prerequisite — global token hydration.** The Spotify `access_token` only loads into the app on the **Profile page** mount. Account actions from Explore/Builder would silently fail until the token hydrates **app-wide on load** (from the localStorage it's already persisted in, with the existing refresh logic). Must be done first.
- **Playlist filtering.** `GET /me/playlists` returns followed playlists the user can't edit. The picker must filter to **owned or collaborative** (owner.id === current user, or collaborative === true), else adds fail.
- Adds use the existing `access_token`-in-body pattern to the FastAPI backend.
- Spotify allows duplicate tracks in a playlist — may want a soft "already added" awareness later (not blocking).

## Ideas & Directions

### Direction 1 — Add to existing playlists [PRIMARY]
- **Backend:** `GET /spotify/playlists/` (list owned/collaborative playlists: id, name, image, track count) and `POST /spotify/add-to-playlist/` (playlist_id, track_ids, access_token → `POST /playlists/{id}/tracks`).
- **Frontend:** a **playlist picker** (modal/popover) listing the user's playlists with cover + name, plus a "New playlist" option (reuses existing create flow). Used by both the bulk action bar and a per-song "add" control on `SongCard`.
- Confirmation + "Open in Spotify" link on success.

### Direction 2 — Save to Liked Songs
- **Scope:** add `user-library-modify` (+ `user-library-read` for indicators) → re-auth.
- **Backend:** `POST /spotify/save-track/` (`PUT /me/tracks`); optional `GET /spotify/saved-contains/` (`GET /me/tracks/contains`, batched) for heart state.
- **Frontend:** heart/save toggle on `SongCard` and the profile header.

### Direction 3 — Explore from your top tracks
- Profile already fetches top tracks. Surface them as **discovery seeds**: on the Explore **idle state** (empty search), show "Your top tracks" as clickable chips/cards that load that song's profile. (Alt: deep-link from the Profile page's top-tracks list into Explore.)
- Requires the top-tracks fetch with the (now global) token.

### Direction 4 — Wiki + metadata
- Display `profile.wiki_summary` (already returned by `/song/profile/`) in a "About" block on the profile.
- Add album + release year (album already on the selected song from search; year needs a track-details call) and optionally **similar artists** (Last.fm `track.getSimilar` / `artist.getSimilar`) — the latter is an extra call, can defer.

## Recommendations
Sequence by dependency + value:
1. **M0 — Enabling:** global token hydration (app-wide) + add `user-library-read`/`user-library-modify` to the auth scopes (triggers re-auth). Prereq for everything else.
2. **M1 — Add to existing playlists** (bulk + per-song) — the primary ask.
3. **M2 — Save to Liked Songs** (+ saved indicators).
4. **M3 — Explore from your top tracks** (idle-state seeds).
5. **M4 — Wiki + metadata** display (wiki is nearly free; metadata depth optional).

Rationale: M0 unblocks all account actions outside Profile; M1 delivers the headline feature; M2–M4 layer on once the token + scopes are in place.

## Suggested Decisions (confirmed)
- [x] Add-to-playlist supports **both bulk + per-song**
- [x] This round includes **all four**: existing-playlist adds, Liked Songs, top-track seeds, wiki/metadata
- [x] Accept **one re-auth** for the new library scopes

## Open Questions (for /plan)
- Playlist picker UX: modal with search/filter (for users with many playlists) vs simple scrollable list
- "Explore from top tracks" placement: Explore idle-state seeds vs Profile→Explore deep-link (or both)
- Metadata depth in v1: wiki + album/year only, or also similar artists (extra Last.fm call)
- Saved-state indicators: include now (needs batched `/me/tracks/contains` + `user-library-read`) or defer the read side
- Re-auth handling: detect missing scope and prompt "reconnect Spotify," or just instruct a manual log out / log in
- Global token: hydrate in `+layout.svelte` vs a dedicated store initializer; reconcile with the Profile page's existing load/refresh logic to avoid double-handling

## Next Steps (what /plan needs)
1. Define the global token-hydration approach and how it reconciles with the Profile page's existing PKCE load/refresh
2. Specify the new scope set + the re-auth UX
3. Backend endpoints: list playlists, add-to-playlist, save-track, (optional) saved-contains
4. Frontend: playlist picker component, per-song add + heart controls on SongCard, idle-state top-track seeds, wiki/metadata block
5. Acceptance criteria: add-to-playlist works from Explore without visiting Profile first; owned/collaborative filtering correct; graceful handling when token/scope missing

---

# Profile Page Revamp — Taste Dashboard (2026-06-24)
Source ideas: docs/ideas.md

## Problem / Opportunity
The profile page is a static stats view: a header card, a standalone controls bar (num-tops + time-period), and two Spotify-style list cards (Top Artists, Top Tracks). The opportunity is to evolve it into a modular "taste dashboard" — integrated controls, consistent song rows, more visualizations, and expandable/independently-scrollable modules.

## Goals
- Integrate the num-tops + time-period controls (not a separate section above the lists)
- Make the tracks list consistent with the rest of the app (reuse SongCard)
- Add visualizations: genre radar, and "taste over time" charts
- Modular layout: minimized summary modules that expand to fill the page (others hide when one is maximized); per-module scroll instead of whole-page scroll

## Audience
The signed-in user exploring their own listening taste (personal project).

## Constraints
- **Genre data is artist-level only** — Spotify tags genres on artists, not tracks. The genre radar is "genres of your top artists, weighted by rank." Label it honestly.
- **LLM-generated scores are expensive at scale** — the radar dimensions are produced per-song by the analysis LLM. Aggregating across top tracks × 3 timeframes = 30–150 LLM calls. Not viable as the default source.
- **Spotify Audio Features API is the ideal source but likely deprecated** — `GET /audio-features?ids=` returns energy/danceability/valence/acousticness/instrumentalness/tempo/etc., batched 100/call. Deprecated for apps created after 2024-11-27; this app is new, so access is uncertain. **Must be tested before designing around it** (this app has already hit deprecation walls: recommendations dead, `/me/playlists` tracks→items rename).
- Existing `/get-profile/` already returns top_artists (with genres) + top_tracks; SongCard expects a `song.spotify.{…}` shape (flat top_tracks need an adapter).

## Ideas & Directions

### A — Integrate the controls
Move num-tops + time-period inline. **Key fork:** global vs per-module timeframe. List/genre modules want one timeframe *filter*; the over-time charts use timeframe as an *axis*. Resolution: a global default timeframe for filter-style modules; the over-time module owns its own axis.

### B — Reuse SongCard for the tracks list
Consistency + free functionality: SongCard already has like / add-to-playlist / explore, so profile top-tracks inherit all the account-integration powers just built. Needs a small adapter from flat top_tracks → `song.spotify` shape.

### C — Modular dashboard
Each section = a module: minimized summary by default, expandable to fill the page (others hide when maximized), per-module internal scroll. This is the structural core and the biggest build — phase it.

### D — Visualizations (Spotify-native first, LLM last)
- **Genre radar** — from top artists' genres, weighted by rank. No extra calls. (cheap)
- **Taste over time** — reframed to use Spotify-native attributes instead of LLM:
  - **Audio features** (energy/danceability/valence/…) *if the app has access* — ideal, one batched call per timeframe.
  - **Popularity** over time — "how mainstream is your taste." (cheap)
  - **Release era** over time — avg track release year per timeframe. (cheap, distinctive)
  - LLM scores only as a last-resort fallback (cached per song, capped at ~top 10) if audio-features is unavailable and the native metrics aren't enough.

## Recommendations
Phase it:
- **P1 — Quick wins:** integrate controls (global timeframe for lists) + reuse SongCard for tracks (+ adapter) + genre radar (artist genres). All cheap, high consistency payoff.
- **P2 — Modular dashboard:** module wrapper with minimize/expand (maximize hides others) + per-module scroll. Convert P1 sections into modules.
- **P3 — Taste over time:** Spotify-native charts (popularity, release era; audio-features if available). LLM fallback only if needed.

**Verify first (gates P3 design):** does this app have **audio-features** access? A single test call decides whether the score/audio radar is cheap (native) or must fall back to popularity/era + optional LLM.

## Suggested Decisions (confirmed)
- [x] Phase the revamp (P1 → P2 → P3)
- [x] Prefer Spotify-native data over LLM for taste charts; LLM is last-resort
- [ ] Global-timeframe-for-lists + over-time-owns-its-axis (proposed; confirm in /plan)

## Open Questions (for /plan)
- **Does the app have audio-features access?** (test before P3) — determines the over-time chart's data source
- Genre radar: count by artist frequency, or rank-weighted? Top how many genres (6 for a clean hexagon)?
- Module layout: fixed 2-col grid of modules? Which modules ship in P2 (Top Tracks, Top Artists, Genre radar, + over-time)?
- Expand interaction: maximize-in-place vs modal-like overlay; how the others "go away"
- Does the genre radar / over-time respect the global timeframe, or always span all?

## Next Steps (what /plan needs)
1. Test audio-features availability for the app (gates P3)
2. Define the SongCard adapter for profile top_tracks (flat → `song.spotify` shape)
3. Spec the genre-aggregation (rank-weighted counts → top 6)
4. Spec the module wrapper (summary/expanded states, hide-others, internal scroll)
5. Decide control placement + global-vs-per-module timeframe

---

# Taste Analytics Expansion (2026-06-24)
Context: leveraging more of the Spotify API within what a post-2024-11-27 app can actually access (see the brain `spotify` domain). Builds on the P2 modular dashboard.

## Problem / Opportunity
The profile dashboard has genres, taste-over-time, and top lists. There's a lot more analytical signal in the data the app *can* read (release dates, artist popularity, genres, recently-played timestamps) — none of it needing the deprecated endpoints. Adding modules is cheap now that the dashboard is modular.

## Goals
- Add four taste-analytics modules: **decade distribution**, **mainstream-ness**, **genre depth + diversity**, **listening clock**
- Stay entirely within available Spotify data (no audio-features / recommendations / related-artists)
- Reuse the P2 module system; keep each module self-contained and scrollable/expandable

## Audience
The signed-in user exploring their own taste (Premium available, but playback is out of scope this round).

## Constraints
- **Track popularity is stripped** for new apps → compute "mainstream-ness" from **artist** popularity (which *is* available).
- **Recently-played needs a new scope** (`user-read-recently-played` → one re-auth) and is capped at the **50 most-recent plays** (a rolling window, not full history) — the listening clock is a "recent snapshot," label it honestly.
- **Genres are artist-level** — genre modules derive from top artists, weighted by rank.
- **Deprecation guardrail:** nothing here uses audio-features, recommendations, or related-artists.
- `/get-profile` top_tracks currently omit `release_date` — must add it for the decade module.

## Ideas & Directions (the four chosen modules)

### 1 — Mainstream-ness (artist popularity)
- Recovers the metric lost in P3 (track popularity is dead) using **avg top-artist popularity** per timeframe → a real line for the taste-over-time chart. Plus a "most obscure / most popular artist" callout for the current timeframe.
- **Data:** top_artists already include `popularity`. Add artist-popularity to the `taste-over-time` endpoint (3 timeframes). No new scope.

### 2 — Decade distribution
- Histogram of the eras your top tracks come from (e.g., 1980s … 2020s) for the selected timeframe.
- **Data:** track `album.release_date` → year → decade bucket. Add `release_date` to `/get-profile` top_tracks. No new scope. Needs a small bar/histogram viz.

### 3 — Genre depth + diversity
- Beyond the radar: a ranked genre breakdown (top N with weights) and a **diversity index** ("how varied is your taste").
- **Data:** top_artists `genres`, rank-weighted (reuse the existing aggregation). No new scope. Could live alongside the genre radar in one module.

### 4 — Listening clock
- Hour-of-day (and/or day-of-week) heatmap of *when* you listen, from recently-played timestamps.
- **Data:** new `GET /spotify/recently-played/` (`user-read-recently-played`, 50-item cap) → aggregate `played_at` into hour/day buckets. **New scope (re-auth).** Needs a heatmap viz.
- Bonus the scope unlocks: "explore from what you just heard" (recently-played as a discovery seed) — note for later, not in scope now.

## Recommendations
Phase by scope cost:
- **TA1 — Mainstream-ness:** extend `taste-over-time` with artist popularity; show as the chart line + obscure/popular callout. (No new scope; also un-flattens the existing taste chart.)
- **TA2 — Decade distribution:** add `release_date` to `/get-profile`; new module with a bar histogram. (No new scope.)
- **TA3 — Genre depth + diversity:** ranked genre bars + diversity index from existing genre aggregation. (No new scope.)
- **TA4 — Listening clock:** add `user-read-recently-played` scope (re-auth) + recently-played endpoint + heatmap module. (New scope — do last.)

Rationale: TA1–TA3 ship without re-auth and reuse existing data/aggregations; TA4 is the one requiring the scope change, so it's sequenced last.

## Suggested Decisions (confirmed)
- [x] Build all four modules
- [x] Accept one re-auth to add `user-read-recently-played` (for TA4)
- [x] Mainstream-ness via artist popularity (track popularity unavailable)
- [x] Stay within available data — no deprecated endpoints
- [x] Premium noted as available, but playback is out of scope this round

## Open Questions (for /plan)
- Decade bucket granularity (decades vs 5-year) and scope (current timeframe vs all-time)
- Genre diversity index formula (unique-count vs normalized entropy of genre weights)
- Listening clock viz: hour-of-day heatmap, day-of-week, or both; how to message the 50-play limit
- Mainstream-ness: fold into the existing taste-over-time chart, or a separate module?
- Chart components: build small BarChart + Heatmap components (reuse TrendChart only for lines)

## Next Steps (what /plan needs)
1. Backend: extend `taste-over-time` (artist popularity), add `release_date` to `/get-profile`, new `recently-played` endpoint
2. Auth: add `user-read-recently-played` to SCOPES (re-auth)
3. Frontend: new dashboard modules (decade, genre-depth, listening-clock) + small bar/heatmap chart components
4. Decide module placement in the 2-col dashboard grid
5. Acceptance: each module renders from real data, degrades gracefully when empty, no deprecated-endpoint calls

---

# Native iOS App (2026-08-03)

## Problem / Opportunity

Boomin Beats is desktop-only by explicit decision, not by neglect — the 2026-06-24 reflect logged
*"no touch support (acceptable, app is min-width 800)"* when choosing HTML5 drag-and-drop for the
Playlists panel. There is no responsive layer to build on. Meanwhile the app's most-used moments
(what am I listening to, build me something for this drive) happen away from a desk.

The opportunity is larger than access. The backend is *accidentally already a mobile API*:
`profile.py`, `song_profile.py`, `llm_playlist.py`, and all of `spotify_actions.py` take the Spotify
access token as a query param or body field and return plain JSON. They are stateless passthroughs.
A native client can call them today with no server changes beyond hosting and one auth fix.

Native also unlocks the things a browser structurally cannot do: a now-playing lock-screen widget,
Siri/Shortcuts playlist generation, and the Spotify iOS SDK's real playback control instead of the
Web API's queue-only surface.

## Goals

- Full functional parity with the web app, on iPhone, from anywhere
- Keep the web app able to run against a **local** model (Ollama) on the Mac
- Native-only capabilities: home/lock-screen widget, App Intents (Siri + Shortcuts), Spotify iOS SDK playback
- Serve as a genuine SwiftUI learning vehicle — rebuild cost is partly the point, not purely waste
- Harden the existing API before a second client depends on it

## Audience

Single user (owner), on personal devices. No App Store release planned; distribution via a paid
Apple Developer account and TestFlight or direct device install. Spotify stays in development mode
(25-user allowlist), which is ample.

## Constraints

**Inherited from the current codebase:**
- Spotify PKCE is client-side with `REDIRECT_URI = 'http://127.0.0.1:5173/profile'` (`spotifyAuth.js:11`) — unusable from iOS
- `PUBLIC_API_URL=http://127.0.0.1:8005` — meaningless on a phone; also blocked by App Transport Security as cleartext
- The BYOK LLM key lives in a Starlette session cookie (`llm_connect.py:36`, read in `llm_playlist.py:30`), relying on `credentials: 'include'` and a CORS allowlist of one origin. Native clients have no origin. `plan.md` already flagged this as Medium-confidence and due for revisit.
- `search.py` and `recommendations.py` use `SpotifyClientCredentials` — the client **secret** can never ship in an iOS binary, so these must stay server-side
- Every chart (`Radar`, `AxisRadar`, `FeatureRadar`, `SongRadar`, `TrendChart`, `BarChart`, `ColumnChart`, `Heatmap`) is layercake + d3 emitting SVG — no port path
- All cross-page state uses the `persisted()` localStorage helper in `stores.js`
- Two areas the last reflect flagged as least-tested: account integration end-to-end, and AI analysis JSON parsing across Groq/Claude/OpenAI

**New constraints introduced by going native + hosted:**
- A publicly reachable backend needs *some* access control; today anything on the internet could burn the Spotify client-credentials quota
- Reuse the **existing Spotify client ID** — audio-features, `/recommendations`, and related-artists access is grandfathered per client ID. Registering a new app for iOS likely loses it.
- iOS cannot do reliable 15-minute background polling (`BGAppRefreshTask` is opportunistic); any scheduled sync must be server-side
- Adding OAuth scopes forces full re-auth — a known recurring gotcha in this project

## Ideas & Directions

### D1 — Backend: one codebase, two deployments

The stated need is "app from anywhere, *and* a local model on the web app." Rather than a hosted
backend tunnelling back to the Mac's Ollama (fragile, and the tunnel becomes a hard dependency of
every LLM request), run **the same FastAPI code in two places**:

| Instance | Serves | LLM providers |
|---|---|---|
| Local (Mac, `:8005`, today's setup) | The web app, unchanged | Ollama / local models, plus remote |
| Hosted (Fly / Render / Railway) | The iOS app | Remote only (Claude / OpenAI / Groq) |

This works because **the backend holds no state** — no DB, no user records; all state is client-side
in `localStorage`. Two stateless instances cannot drift. Selection is a `LLM_BACKEND=local|remote`
config flag, which `ROADMAP.md` Phase 9 already anticipated.

Cost: a second secret store, and the hosted instance needs device auth.

### D2 — Auth: custom-scheme PKCE, shared client ID

iOS runs its own PKCE via `ASWebAuthenticationSession` against a `boominbeats://callback` scheme
registered as an *additional* redirect URI on the existing client ID. Verifier/challenge move from
`crypto.subtle` to CryptoKit; tokens move from `localStorage` to Keychain. Drop `show_dialog: 'true'`
— through `ASWebAuthenticationSession` it forces an extra system prompt on every login.

### D3 — LLM key transport: retire the session cookie

Replace `request.session['llm_api_key']` with an explicit `X-LLM-Provider` / `X-LLM-Key` header pair
read per-request. The web app stores the key in localStorage (it already does, in `llmConfig`); iOS
stores it in Keychain. This removes the cookie/CORS coupling entirely, works identically for both
clients, and stops shipping the key in a signed-but-unencrypted cookie. Do this **before** the
hosted deployment exists.

### D4 — Charts as the SwiftUI learning curve, not a tax

Four radar components are the largest single rewrite, and Swift Charts has no polar chart — they
become hand-drawn `Path` + `GeometryReader` geometry. Framed as cost that's the worst item on the
list; framed as SwiftUI education it's close to the ideal exercise (custom shapes, coordinate math,
animation, `@ViewBuilder` composition). `TrendChart`/`BarChart`/`ColumnChart`/`Heatmap` map cleanly
onto Swift Charts and are the gentle warm-up.

### D5 — The Playlists panel gets *better* on iOS

The panel's touch gap is a limitation of **HTML5** drag-and-drop specifically. SwiftUI's
`.draggable` / `.dropDestination` are touch-native and first-class. Full parity here means parity of
*capability*, not of interaction — the drag-to-playlist workspace should be redesigned for touch
(long-press to lift, drop targets sized for thumbs), and can plausibly feel better than the web
original.

### D6 — Sequencing the native payoff earlier

A now-playing widget depends only on auth plus the Spotify Web API — not on the rest of the app. It
can land immediately after the auth milestone rather than waiting for parity, which puts a
native-only win early instead of at the end of a long rebuild.

## Recommendations

1. **Harden before extending.** Close the two open items from the 2026-06-24 reflect (account
   integration end-to-end; AI JSON parsing across all three providers) before any Swift is written.
   Debugging those through a simulator costs materially more than through a browser console.
2. **Two deployments of one codebase** (D1) — it satisfies "anywhere" and "local model" without a
   tunnel, and the stateless design makes it nearly free.
3. **Header-based LLM key** (D3) as the first code change, landed on the web app first so it's
   proven before iOS depends on it.
4. **Reuse the existing Spotify client ID.** Verify grandfathered endpoint access in the dashboard
   before planning around the radar/recommendations features.
5. **Add a device key to the hosted instance** — a long random secret in `X-Device-Key`, held in
   Keychain, checked by middleware. Not real auth; appropriate for a single-user personal tool, and
   it stops an open endpoint from burning your Spotify and LLM quota.
6. **Pull the widget forward** (D6) so native value arrives before full parity does.
7. **Establish the screenshot loop on day one.** The last two reflects both name visual iteration
   without a feedback loop as the dominant time sink. Simulator screenshots via `xcrun simctl` +
   SwiftUI previews should be set up before the first view is styled.

### Suggested milestone order

| # | Milestone | Notes |
|---|---|---|
| P0 | API hardening + `X-LLM-Key` migration + hosted deploy + device key | Backend only; web app keeps working throughout |
| P1 | SwiftUI shell, Keychain, PKCE via custom scheme, Profile screen | Simplest real surface — learn SwiftUI here |
| P1.5 | Now-playing widget + first App Intent | Early native payoff; depends only on P1 |
| P2 | Search + Explore + song profile + radar chart | The custom `Path` work |
| P3 | Playlist builder: chat, generation, save, queue | Reuses `/llm/generate-playlist/` unchanged |
| P4 | Playlists panel with native drag-and-drop | Touch redesign, not a port |
| P5 | Taste analytics dashboard | Swift Charts |
| P6 | Spotify iOS SDK playback + full Siri/Shortcuts surface | The remaining native-only motivations |

## Suggested Decisions

- **Confirmed:** native SwiftUI (not PWA/wrapper); full functional parity as the end state; harden the API first
- **Recommended, pending confirmation:**
  - Two deployments of one codebase; `LLM_BACKEND=local|remote` flag
  - Header-based LLM key, replacing session cookies, shipped to the web app first
  - Existing Spotify client ID reused with an added `boominbeats://` redirect URI
  - `X-Device-Key` shared secret guarding the hosted instance
  - Widget pulled forward to P1.5
  - Delete the dead code now rather than porting it: `sverdle/`, `Counter.svelte`, `recommendations.svelte`, `backend_server/`, `db.sqlite3`, `/account-analysis/` (returns `{"status": "coming soon"}` behind a live route)

## Open Questions

- Does the existing client ID still have working `/recommendations` and audio-features access? (Test before P2 — `ROADMAP.md` and the analytics brainstorm both already assume some endpoints are deprecated.)
- Spotify iOS SDK auth: can it share the Web API token from the PKCE flow, or does it require its own session? Affects whether P6 is additive or a second auth path.
- Minimum iOS target — 17 vs 18 — gates which SwiftUI and WidgetKit APIs are available.
- Does the web app also become responsive eventually, or does it stay explicitly desktop-only now that a phone client exists? (Recommend: stays desktop-only; the decision is now deliberate rather than a gap.)
- Where does the hosted instance live, and is the free tier's cold-start acceptable for LLM requests that already take seconds?
- Offline behavior: cache last-known profile and playlists, or require connectivity?

## Next Steps (what /plan needs)

1. Scope and sequence **P0** concretely — the two hardening items, the `X-LLM-Key` migration across
   `llm_connect.py` / `llm_playlist.py` / `song_profile.py` / `LLMSettingsPanel.svelte`, hosting
   choice, and the device-key middleware
2. Resolve the Spotify dashboard questions (grandfathered endpoints, added redirect URI) — these are
   verification tasks, not design tasks, and they gate P2 and P6
3. Decide the Xcode project shape: separate repo or a `src/ios/` directory alongside `src/web/`
4. Pick the iOS minimum target and the networking approach (hand-rolled `URLSession` client vs. generating one from the FastAPI OpenAPI schema — the latter is already exported)
5. Define acceptance for P1: PKCE login completes, token persists in Keychain across launches, Profile renders real top artists/tracks, and a simulator screenshot loop is in place

---

# AI DJ Companion (2026-10-17)

## Problem / Opportunity

The music apps people already use have two queue modes, and neither one helps. Spotify DJ and
autoplay take over the queue completely. Manual queueing gives no help at all. Nothing sits in
between: an assistant that helps you **build** the queue, suggesting what plays next, while you stay
in charge of what actually goes in.

This is `ROADMAP.md` goal #4 (Natural-language DJ), reframed. The DJ is a companion that suggests
and assists, and the user stays in control of the queue. A chat window that drives playback is not
the goal.

## Goals

- A clean now-playing view with playback control, while music plays through the user's own provider
  (Spotify)
- Suggestions for what to play or queue next, offered as **moves**: some keep the current vibe,
  others change it on purpose
- An adjustable control level, from "only when asked" to "steers toward a goal"
- Hosting as the main use, and equally usable for solo listening by anyone who wants to keep
  control of the queue
- Guest requests are in scope, at lower priority

## Audience

The host: the owner, on their iPhone, at a party, dinner or road trip. Guests never sign in to
Boomin Beats. They interact only through the provider app (for example a Spotify Jam). The
Development Mode user cap therefore doesn't constrain hosting.

## Constraints

- **iOS first.** Builds on the P1 iOS app (PKCE auth, Profile).
- **No Spotify vibe data.** `/recommendations` returns 404 and `/audio-features` returns 403 on this
  client ID (audits in `plan.md`, 2026-08-03). Vibe must come from LLM + Last.fm tags, following the
  pattern `song_profile.py` already uses.
- **Search is capped at 10 results** (February 2026 migration), which is enough to validate a
  handful of suggestions.
- **The Spotify queue is append-only**, both in the Web API and in the iOS SDK (App Remote). The
  queue can be read and added to, but not reordered, removed from or inserted into. The 2026-08-03
  iOS brainstorm expected the SDK to unlock "real" queue control, and it doesn't.
- **iOS suspends backgrounded apps**, so the app cannot reliably send the next track at song end
  while it is in the background.
- **Playback control requires Premium**, which the owner has.
- **The backend is stateless** (no DB). Anything that requires server-side state is a real
  architectural step.
- **BYOK LLM latency.** A party can't wait several seconds for every suggestion.

## Ideas & Directions

### Moves, not songs

Each suggestion is a decision about where the set goes next. Songs fill it in.

| Move | Meaning |
|---|---|
| Hold | Stay on the current vibe (energy, tempo feel, era) |
| Lift / Drop | Raise or lower the energy |
| Pivot | Keep one thread (mood, groove, decade) and change the genre |
| Curveball | Unexpected, but still fits |
| Bridge | One or two songs that get from here to a named destination ("end up in 90s R&B") |

In hosting mode, Bridge grows into **arc planning** ("build to peak energy over the next 30 min").

### Control dial

1. **Whisper.** Suggests only when asked.
2. **Co-pilot.** Always shows 3–5 picks, and the host approves each one.
3. **Autofill.** Fills gaps when the queue runs low, and the host can veto.
4. **Driver.** Builds toward a goal the host sets, and the host steers.

An optional second setting is **adventurousness** (how far suggestions stray), kept separate from
how often the AI acts.

### App-owned queue (recommended)

Boomin Beats holds the real, editable queue: reorder, remove, insert, AI slot-ins. Spotify only ever
gets a **buffer of the next 2–3 tracks**, topped up as songs finish.

- **Backgrounding:** the buffer keeps music playing while the app is suspended, and the app
  reconciles on return. The tradeoff is that tracks already sent to Spotify can't be edited, so a
  deeper buffer is more resilient but gives less control.
- **Party mode:** keeps the screen awake while hosting, which avoids the backgrounding problem in
  the main use case.
- **Rejected for now: a backend worker** that advances the queue. It would work while backgrounded,
  but it needs server-side refresh tokens, which ends the stateless design.

### Guest requests by comparing queues

Guests add songs through the provider app (Spotify Jam, or "Add to queue" on the host's device). The
app knows exactly which tracks it sent to Spotify, so any track in `GET /me/player/queue` that it
didn't send is treated as a guest request. Those go into a **Requests inbox** where the host can
approve (place into the app-owned queue), reposition or dismiss them. This requires no guest
accounts and no backend state.

Fallback if the comparison isn't reliable: a link or QR code to a small web request page. That
reopens the backend-state question.

### Reading the room

Skips and quick "too much / more of this" taps are cheap feedback that steers the next suggestions.
They work for both hosting and solo listening.

### Party safety

A clean-lyrics toggle and a do-not-play list (the `do_not_play` field anticipated in the
`ROADMAP.md` schema).

### Transitions: vibe-level only

Without audio features, BPM and key are LLM estimates. Transition advice stays at the level of "this
lands well after that". It doesn't promise beatmatching or harmonic mixing.

## Recommendations

1. An app-owned queue with a 2–3 track buffer, plus party mode
2. Suggestion engine: LLM + Last.fm tags, validated against Spotify search, extending
   `song_profile.py` rather than starting a new system
3. Build the core loop first (now playing → suggest a move → queue), then the control dial, then the
   Requests inbox
4. Generate suggestions ahead of time, while the current song is playing, so they are ready before
   the host asks

## Suggested Decisions

- **Confirmed:** a feature of Boomin Beats, not a separate app; iOS first; playback through the
  user's provider with in-app control; hosting is the primary use; guest requests are in scope at
  low priority and arrive through the provider app
- **Recommended, pending confirmation:**
  - App-owned queue with a 2–3 track buffer
  - Adventurousness as its own setting, separate from the control dial
  - Guest requests sequenced after the core loop

## Open Questions

- **Test:** do Spotify Jam additions show up in `GET /me/player/queue`? Can tracks queued by a user
  be told apart from tracks coming from autoplay or the current playlist? Guest requests depend on
  both answers.
- Playback path on iOS: Web API through the backend (inherits spotipy's migration handling, per the
  2026-08-03 audit) vs. App Remote (lower latency, and supports subscribing to player state)
- Suggestion latency and cost with BYOK: how far ahead to generate suggestions, and what to cache
- Where the do-not-play list and session feedback live while there's no database (Keychain or
  on-device storage are likely fine for a single host)
- How the queue recovers when the host plays something directly in Spotify, outside the app

## Next Steps (what /plan needs)

1. Run the Jam / `GET /me/player/queue` test first. Its result decides the guest-request design.
2. Pick the iOS playback path and define the polling/subscription loop for now-playing state
3. Specify the move → prompt contract: inputs (recent tracks, Last.fm tags, adventurousness) and
   output schema, reusing `llm_json.py` parsing
4. Define app-owned queue reconciliation: buffer top-up timing, foreground reconcile, and recovery
   from outside edits
5. Acceptance for the first milestone: now-playing view with play/pause/skip, three move-labelled
   suggestions per track, and tap-to-queue landing in the buffer

---

# DJ Companion — Web Design Brief (2026-10-25)

`/design shape` output. This is the contract `/design craft` builds against. It brings the iOS DJ
(DJ1–DJ6) to the SvelteKit web app, at full parity, as a **customizable widget grid** modelled on
Robinhood Legend's layout engine.

## Decisions (confirmed with the owner)

- **Placement:** a new **DJ** nav page, plus a fixed **mini player** bar on every other page.
- **Layout:** a widget grid the user can rearrange, inspired by Robinhood Legend (resize,
  reposition, presets, linking). The **Host** preset (the three-column Option 1) is the default.
- **Primary use:** hosting from a laptop by the speakers. Optimise for glanceability and fast,
  confident taps; detail on demand.
- **Scope:** full parity with iOS.
- **Moves come in both forms:** a combined **Next moves** widget *and* single-move widgets (Toward,
  Hold, Lift, Drop, Pivot, Curveball, Drift).
- **Editing is locked by default.** An **Edit layout** toggle reveals drag handles, resize corners,
  an Add widget menu, and Done. A laptop at a party gets bumped, so no accidental drags.
- **The mini player is fixed,** not customizable.

## Register and stance

**Product register.** The bar is earned familiarity: "would a Spotify or Legend power user trust
this?" The tool disappears into the night. Delight is reserved for one moment (the album-art
ambience, below), never for chrome.

**AI-slop check.**
- First-order: "music app → dark + neon". That's the existing brand (logo-derived blue/purple on
  #121212) and the product-register default, so it's kept on purpose, not by reflex.
- Second-order traps refused: aurora gradients, glassmorphism, neon glow, gradient text, identical
  card grids.
- The distinctiveness comes from the **move vocabulary** and **album-art ambience**, not decoration.

## Information architecture

### Widget catalog

Each widget has a header (title + optional actions), a body, and every state shipped.

| Widget | Content | Min size (cols × rows, 12-col grid) | Notes |
|---|---|---|---|
| **Now playing** | Art, title, artists, progress, ⏮ ⏯ ⏭, 👎/👍, device | 3 × 5 | Carries the album-art ambience |
| **DJ controls** | Mode (Whisper / Co-pilot / Autofill / Driver), Safe↔Bold, Clean only | 3 × 3 | |
| **Goal** | None / Destination / Build / Wind down / Peak then cool / Drift, length, progress | 3 × 2 | Can be docked inside DJ controls in Host |
| **Next moves** | All moves stacked; each pick has art, title, artist, reason, ⋯, + | 4 × 6 | Refresh in the header |
| **Single move** (×7 kinds) | One move's picks, same row anatomy | 2 × 3 | Kind chosen when added |
| **Up next** | Sent to Spotify + Up Next, reorder, remove, Later, + Add song (search) | 3 × 5 | ✦ marks DJ-added picks |
| **Requests** | Guest requests with Keep / Later / Decline; a badge count | 3 × 3 | Empty state: "Requests from your Spotify queue show up here." |
| **Song profile** *(pass 2)* | The existing `SongProfile` component for the selected song | 3 × 5 | Linked (below) |
| **Recently played** *(pass 2)* | This session's history | 3 × 3 | |

### Presets

The layout picker in the page header offers presets, plus "Your layout" once one is edited.

- **Host** (default; the Option 1 shape): Now playing + DJ controls + Goal on the left (3 cols),
  Next moves in the middle (6), Requests over Up next on the right (3).
- **Board** (the Option 3 shape): a Now playing banner across the top (12 × 2, a compact variant),
  a row of single-move widgets, and Up next + Requests along the bottom.
- **Focus:** a big Now playing (5) beside Next moves (7). Queue reachable through the mini
  affordance.
- **Reset to Host** is always one click away in the layout menu.

### Linking (pass 2)

Legend's "dynamic linking", scoped down: one link group. **Song profile follows the selection:**
the now-playing track by default; clicking any suggestion or queued row selects it. The selected
row gets the selection treatment (below). No multi-group colour linking; it's overkill here.

### Mini player (other pages)

A fixed 64px bar along the bottom, above any page content: art 40px · title/artist · progress
hairline · ⏮ ⏯ ⏭ · current goal label · "Open DJ" link. It hides when nothing is playing or the
user isn't signed in.

## Grid behaviour

- **gridstack.js** (MIT, no dependencies, drag + resize + `save()` / `load()`), pinned to the latest
  **13.x** (13.3.0). 14.0.0 is a month-old major; adopt it only after checking its changelog.
  Wrapped in one Svelte component; widgets are Svelte components mounted into grid items.
- A 12-column grid with a fixed row height. **Breakpoints:** 12 cols at ≥1280px, 8 at 1024–1279,
  6 at 800–1023. The app's existing desktop-only floor (min-width 800) stays. Below 1280,
  gridstack's column-reflow keeps each widget's order.
- **Edit layout:** widget headers show a drag handle, a bottom-right resize corner, and a remove ×.
  A dashed snap preview appears while dragging. **Done** saves. **Esc** cancels, back to the last
  saved layout.
- **Persistence:** `localStorage` key `djLayout.v1` (layout JSON + preset name). It's per-browser
  convenience state, so a stateless backend is correct; a corrupt or missing value falls back to
  Host.
- **Keyboard:** in edit mode, a focused widget moves with arrow keys and resizes with Shift+arrows.
  An "Add widget" menu adds to the first free slot. That meets `rules:keyboard-operable` without
  needing drag.

## Visual system

Built on the existing tokens in `routes/styles.css` (surfaces 0/1/2, `--accent` blue, `--accent-2`
purple, radius 12/8/20, Inter). No new font family.

- **Colour strategy: restrained.** Neutral surfaces. `--accent` only for action, selection and
  progress. **One meaning per hue across the page:**
  - Accent blue: primary actions (⏯, +, refresh), progress, selection.
  - **Toward/Drift lead move:** `--accent-2` purple. It marks the goal's influence, so it's the only
    purple in the content area.
  - Danger red: Decline and the Requests badge. Success is not used.
- **Album-art ambience (the signature move):** the Now playing widget's background is a
  low-chroma OKLCH tint taken from the cover's dominant colour. It's sampled from the 64px Spotify
  thumbnail on a canvas (CORS-safe through `i.scdn.co`) and clamped to L 0.18–0.24, C ≤ 0.04 so text
  contrast stays ≥ 4.5:1. It crossfades over 400ms on track change, with an instant swap under
  `prefers-reduced-motion`. That's the one atmospheric element; every other widget stays neutral.
- **Type:** Inter (existing). Product scale 1.2: 12 / 14 / 16 / 20 / 24. Track title in Now playing
  is 24/600; widget titles 14/600; reasons 13/400 `--text-muted`. Reasons wrap to 2 lines, never
  truncate mid-word, with the full text in a tooltip. **No uppercase tracked labels** (the
  existing nav pills are left alone, out of scope).
- **Widget chrome:** `--surface-1` body, 12px radius, no shadow. Header 40px with a hairline
  divider. No nested cards: rows inside widgets are bordered rows, not cards.
- **Icons:** one SVG set across the page (Tabler-style outline, same as the mockups). Replaces the
  ⚙ glyph only where the DJ page touches it.

## States (every widget)

Loading: skeleton rows matching the row anatomy (no spinners mid-panel). Empty: an invitation with
a verb. Error: plain sentence plus a retry. Rate-limited: "Spotify is rate-limiting this app right
now. Try again later." Needs key: "Add an AI key in Settings to get suggestions." with a button that
opens the existing LLM settings popover. No device: "Open Spotify on any device to start playback."

## Motion

Product stance: 150–250ms, state only. Exponential ease-out. Specifically: row insert/remove in
queues (height + opacity, FLIP via Svelte's `animate:flip`); the + button turns into ✓ (150ms);
the ambience crossfade (400ms, the one exception, because it is the state change); the edit-mode
reveal (handles fade in 150ms). Nothing animates on page load. Reduced motion gets instant swaps.

## Copy

Sentence case; verb + object buttons ("Add song", "Edit layout", "Reset to Host"). No em dashes in
UI strings. Move summaries are reused from iOS ("Raise the energy", "Somewhere new").

## Data and logic (implementation notes for craft)

The web app has **none of the iOS queue logic yet.** Port it to `src/lib/dj/`, keeping the iOS
structure so it can be tested the same way:
- `queueStore.js`: sent/upcoming, adaptive buffer (1 ahead; there's no "background" on the web, so
  a `visibilitychange` hidden event tops up to N), skip-on-arrival, `reconciled()`,
  `detectRequests()` and `arrival()` as pure functions, all persisted to `localStorage`.
- `nowPlaying.js` (2s poll, track-change detection, recent/liked/disliked/skipped),
  `suggestions.js` (prefetch, cache key incl. settings + goal, in-flight guard, autopilot), and
  `djSettings.js`.
- Port the iOS `QueueLogicTests` cases to **vitest** for the pure functions.
- The backend needs no changes: `/player/*`, `/dj/suggest/`, `/spotify/queue/`, `/search/` already
  cover the web.

## Out of scope

Mobile/responsive web below 800px · multiple link groups · syncing layouts across devices · a
theme or light mode for the web (the web app is dark-only today) · restyling the existing pages'
nav and gradient headline (noted: the Explore headline uses gradient text, which the frontend rules
ban; fix it separately).

## Risks and open questions

1. **Two hosts at once.** If the iOS app *and* the web DJ are both open, each runs its own queue
   store and both send tracks to Spotify, so each will see the other's sends as guest requests.
   Recommend: only one active "DJ host". The web shows a banner ("The DJ is also running on another
   device") when it sees non-app tracks it can't explain, and offers "Take over". Needs a decision
   before craft.
2. **The grid library's fit with Svelte 4 + SvelteKit 1.** Gridstack is vanilla JS, so mounting
   Svelte widgets into its DOM nodes must be done in `onMount`. Spike this first.
3. **Groq/Spotify budgets** are unchanged: prefetch stays one call per track change no matter how
   many move widgets are on screen. All move widgets read the same `suggestions` store.

## Build passes (suggested for /plan)

1. **Pass 1:** the `src/lib/dj/` logic port with vitest; the grid shell (gridstack spike); the Now
   playing, DJ controls, Goal, Next moves, Single move, Up next and Requests widgets; the Host,
   Board and Focus presets; Edit layout; the mini player; the album-art ambience.
2. **Pass 2:** linking + the Song profile widget, Recently played, keyboard move/resize polish, and
   the two-host takeover.

---

# DJ Sync Across Devices (2026-10-25)

## Problem

The queue and the DJ options live on each device, so the iPhone and the web DJ can't share a
night. Worse, if both run at once, each treats the other's sends as guest requests. The owner
wants the queue and the DJ options synced across devices.

## Decision reversed: the backend is no longer stateless

The no-database design (native iOS brainstorm D1; DJ plan "State: on-device only") is **replaced
for DJ state.** Everything else (Spotify tokens, LLM keys) stays per-request and stateless.

## Confirmed decisions

- **Storage: Supabase Postgres.** One `dj_state` row per Spotify user. Both the local (Mac) and
  hosted backends point at the same database, which keeps the two-deployment design: the web can
  stay on the local backend with Ollama while the phone uses the hosted one, and they still sync.
- **Driving model: like a Spotify Jam.**
  - The device that starts the DJ session is the **primary**. It's the only one that sends tracks
    to Spotify (buffer top-up, skip-on-arrival, Autofill/Driver queuing) and the only one that
    runs request detection.
  - Every other device is a **participant** with full editing: queue add/reorder/remove, Keep /
    Later / Decline on requests, mode, Safe↔Bold, clean only, goal, do-not-play, 👍/👎.
  - It's always labelled: "Driving from this iPhone" or "Driving from MacBook web".
  - **No silent failover.** If the primary's heartbeat stops for ~60s, participants see "Your
    iPhone stopped driving" with **Drive from here**; one tap moves the primary role. A
    participant can also tap Drive from here at any time.
- **Synced:** the queue (sent, upcoming, requests, guest skips, kept guests), the DJ options (mode,
  adventurousness, clean, goal, do-not-play), **session feedback** (liked, disliked, skipped), and
  **recent history**.
- **Not synced:** the web DJ layout, Appearance, the background buffer depth, and the LLM key.
  These are per-device by nature.
- **Include the hosted backend deploy (P0/D1)** so a physical iPhone syncs away from home Wi-Fi.

## Mechanics (recommended, to be finalised in /plan)

- **Identity:** keyed by Spotify user id. The backend resolves it from the bearer token
  (`GET /me`, cached per token), so no new accounts and a client can't write another user's row.
- **Endpoints:** `GET /dj/state` → `{version, state, primary}`, and `PUT /dj/state` with
  `If-Match: <version>`, which returns **409** with the current document on conflict. The client
  re-applies its edit and retries. Plus `POST /dj/primary` (claim) and a heartbeat.
- **Granularity:** whole-document writes. The document is small (a queue of tens of items plus
  settings).
- **Change pickup:** each client checks the version on the poll it already runs (~2s), and only
  fetches the full state when the version changes. Supabase Realtime is a possible later upgrade
  but not needed.
- **Offline:** a device keeps a local copy and queues its edits; on reconnect it merges with the
  409 retry loop. The primary keeps driving from its local copy if Supabase is briefly unreachable.
- **Security:** the Supabase service key lives server-side only (`.env` / host secrets), never in a
  client. Row access is enforced in the backend by the resolved user id. RLS is enabled as defence
  in depth.

## Impact on existing work

- **iOS:** `QueueStore` and `DJSettings` persistence switches from `queue.json`/UserDefaults to the
  sync layer (with the local copy kept as a cache). Request detection and top-ups gated to the
  primary. A new primary/participant indicator and Drive from here.
- **Web DJ (design brief above):** the `src/lib/dj/` port is built on the sync layer from the
  start. The "two hosts at once" risk in the brief is resolved by this design.
- **Backend:** the first persistent store. Tests for the version/409 logic and the user-id
  scoping.

## Open questions for /plan

1. Hosting choice for P0/D1 (Fly, Render, Railway) and cold-start tolerance.
2. Supabase project: new, or an existing one (the connector is available in this environment).
3. Heartbeat interval and the offline threshold (proposed 15s heartbeat / 60s offline).
4. Migration: first launch after the update uploads the device's existing local queue, or starts
   empty.

---

# Spotify Quota: Look Up at Queue Time, Songs by ISRC (2026-10-25)

## Problem / Opportunity
Spotify's Development Mode quota is unpublished and counted per developer account (since
2026-07-23, shared by all of an account's Client IDs). **Search** is the bucket that runs out; the
player, queue and profile calls survived every lockout.

Every screen that *shows* songs also searches Spotify:
- DJ pick validation, about 10–14 searches per round even after the 2026-10-25 fixes
- song search as you type (Add song, Explore)
- the playlist builder's validation

Extended Quota Mode requires a registered organization with ≥250k monthly active users, so raising
the quota isn't an option. Showing songs must cost no Spotify quota, and only queueing one may.

## Goals
- A 4-hour, ~60-song night stays well inside the daily search quota: about 1 Spotify search per
  queued song.
- No loss of quality. Picks are still checked to exist with the right artist, and still show art,
  artist and the explicit flag.
- Song identity that doesn't depend on a provider (ISRC), so Apple Music can be added for a public
  launch without migrating saved data.

## Audience
The owner plus a small circle (Development Mode allows the owner and 4 users). Public use is the
later goal, through Apple Music (direction F).

## Constraints
- Queueing on Spotify needs a Spotify track ID, and only Spotify search provides one.
- Deezer's public API: no key, about 50 requests per 5 seconds **per IP**. Its terms target
  non-commercial use, which suits personal use; re-check before a public launch.
- The synced document's schema is strict (`routers/dj_state.py`). Adding fields means a matching
  server, iOS and web change.
- A clean edit has its own ISRC, so "Clean only" keeps today's rule (skip explicit picks) instead of
  swapping versions.

## Evidence
Deezer found **19 of 20** typical DJ picks with the right artist, plus the explicit flag, with no
key (2026-10-25). The one miss was probably a "feat." credit defeating a naive artist match. Deezer
track records include an ISRC; `bpm` is often 0.

## Ideas & Directions

### A. Look up on Spotify only when a song is added (chosen)
- `/dj/suggest/` checks picks against **Deezer** (existence, artist match, art, explicit, ISRC)
  instead of Spotify.
- Tapping + (or autopilot adding a song) does one exact Spotify lookup by ISRC, cached in
  `track_lookup`. A short spinner on the button is fine (owner, 2026-10-25).
- The lookup happens **when the song is added to Up next**, not when it's sent to Spotify. Every
  queue item then always has a Spotify `trackID`, so guest-request detection, skip-on-arrival and
  sync don't change.
- Misses (on Deezer, not on Spotify) show "Not on Spotify"; autopilot moves to its next candidate.

### B. Deezer for typing and browsing (chosen)
Add song, Explore and the playlist builder search **Deezer** as you type. A song is looked up on
Spotify only when it's chosen: queued, added to a playlist or saved. The playlist builder does a
batch of exact ISRC lookups at "add to playlist" time.

### C. Songs identified by ISRC (chosen)
- Picks, the synced queue, the cache and feedback entries gain an `isrc`. The Spotify `trackID`
  stays as the playable handle.
- One ISRC can map to several Spotify tracks (album, single, compilation, other regions): take the
  first one playable in the user's market.
- Fall back to a title + artist search only when a song has no ISRC.
- The cache keys on ISRC, so a song is looked up once per 30 days across every device.

### D. Odesli fallback while search is locked out (optional, later)
Turns a Deezer link into a Spotify link on Odesli's quota. About 10 requests a minute without a key
(a key is free by email). It would keep queueing working through a lockout.

### E. Candidates from songs the app already knows (optional, later)
Give the AI the user's top tracks, recently played and cached tracks, which already have Spotify
IDs. Picks from that list cost no search.

### F. Apple Music for the public launch (direction only)
- MusicKit gives full queue control (insert, reorder, remove), which would replace the
  app-owned-queue workaround.
- It needs an Apple Music subscription per listener, MusicKit JS for the web, and the $99/yr Apple
  Developer Program.
- The ISRC identity from C is the bridge between the two providers.

## Recommendations
Build **A + B + C** as one plan: the same pattern on three surfaces, leaving Spotify search for
queueing only. D and E are optional follow-ups; F is the public-launch direction.

## Suggested Decisions
- Deezer is the source for display and existence checks; Spotify is used only to resolve a song
  being queued. *(confirmed)*
- Resolve when the song is added to Up next; a spinner on tap is acceptable. *(confirmed)*
- `isrc` is added alongside the Spotify `trackID`, not instead of it.
- Clean only keeps the skip-explicit rule.
- Deezer results are cached too, because of the shared-IP limit on Vercel.

## Open Questions (for /plan)
1. Does `track_lookup` store both kinds of row (title|artist → Deezer match, ISRC → Spotify track),
   or should there be a second table?
2. Rows synced before this change have no `isrc`. Leave them as they are (they already have Spotify
   IDs), or backfill?
3. The lookup's market: does `market=from_token` stay right when the hosted backend serves other
   people in the small circle?
4. Where autopilot's resolve lives: on the primary device only (as today), which keeps sends single?
5. Last.fm vs Deezer for art and tags. Keep Last.fm for tags and use Deezer for art?
6. Not in this scope, but it gates "small circle on iPhone": TestFlight needs the paid Apple
   Developer Program (the same card question as hosting).

## Next Steps (what /plan needs)
- Milestones across the backend (Deezer client and cache, `/dj/suggest/`, resolve endpoint), iOS
  and web (picks, tap to queue, Add song/Explore, playlist builder) and the schema (the `isrc`
  field).
- A measurable check: count Spotify searches over a real session.
