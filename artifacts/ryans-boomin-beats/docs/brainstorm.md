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
