# Boomin Beats (web): design context

A brief for a design session on the web app. Written 2026-10-26 from the code on `dev`.

## What it is

Ryan's Boomin Beats is a personal music app built around Spotify. It has a SvelteKit web app, a
FastAPI backend and a SwiftUI iOS app. The web app does four things:

- **Explore:** search a song, see its profile, and find similar songs by the qualities you pick.
- **Playlist Builder:** describe a playlist in plain language. AI builds it, checks it against
  Spotify, and you save or queue it.
- **DJ:** an AI DJ companion for hosting a party from a laptop by the speakers. It watches what's
  playing, suggests the next song, and runs a shared queue.
- **Profile:** your listening history as a dashboard (top tracks and artists, genres, eras, taste
  over time).

**Audience:** the owner and up to 4 friends. Spotify's Development Mode caps it there. A public
launch is a later goal, not a current one.

**Bring your own AI:** users connect their own AI provider in a settings popover. The choices
are Claude, OpenAI, Groq and "Your Claude Code", which runs locally with no key.

## Platform constraints

- **Desktop only.** The header has `min-width: 800px`. Nothing below 800px is supported today.
- **Dark only.** There's no light theme.
- **Stack:** SvelteKit 1 and Svelte 4, with plain scoped CSS and no CSS framework. Fonts are Inter
  plus Fira Mono. The DJ grid uses gridstack.js 13.3.0.
- **Spotify Premium and an open Spotify app** are needed for playback control. The web app
  controls Spotify; it doesn't play audio itself.
- **Search budget:** search-as-you-type uses Deezer and Last.fm. Spotify is called only once a
  song is chosen, because its daily search allowance is small. Designs shouldn't add Spotify
  calls per keystroke or per row.
- **Cover art:** some search results, mostly niche uploads, have no cover. Every song row needs a
  placeholder that looks deliberate.

## App shell

- **Header** (fixed, floating):
  - A pill-shaped bar on `--surface-1` with a 20px radius, over a gradient fade.
  - The logo sits on the left.
  - Nav pills in the centre: Explore · Playlist Builder · DJ · Profile. They're uppercase with
    tracked letters. The active pill gets the blue→purple brand gradient.
  - On the right: a "Playlists" toggle and an AI settings button, a circle with ⚙ and a green dot
    when connected.
- **Playlists panel:** docks on the right, 340px wide; the main area shrinks to make room. It
  lists the user's Spotify playlists with search and sort, and songs can be dragged onto a
  playlist to add them.
- **Mini player:** a fixed 64px bar at the bottom of every page except DJ. It shows 40px art,
  title and artist, a thin progress line, back / play-pause / next, the current goal, and an
  "Open DJ" link. It hides when nothing is playing.
- **AI settings popover:** pick a provider and paste a key. It sits under the header.

## Design tokens (`src/routes/styles.css`)

```css
--surface-0: #121212;  /* page */
--surface-1: #242424;  /* cards; matches the logo's plate */
--surface-2: #2e2e2e;  /* hover / raised */
--text-primary: #fff;
--text-muted: rgba(255,255,255,.65);
--text-subtle: rgba(255,255,255,.4);
--accent: #5ec9ff;     /* logo blue: action, links, selection, progress */
--accent-mid: #7b7ff0; /* periwinkle */
--accent-2: #a235ff;   /* logo purple: fills only */
--accent-hover: #8ad8ff;
--brand-gradient: linear-gradient(135deg, var(--accent), var(--accent-2));
--border-subtle: rgba(255,255,255,.08);
--radius: 12px; --radius-sm: 8px; --radius-lg: 20px;
--transition: .15s ease;
/* DJ page only */
--accent-2-text: #c49bff; /* purple text that holds 4.5:1 */
--danger: #ff7a7a; --warning: #ffb454;
```

**Logo:** `src/lib/images/BoominBeatsLogo.jpg` (a mark on a #242424 plate) and
`BoominBeatsTextLogo.jpg`. The palette comes from the logo's blue-to-purple gradient.

**Shared DJ controls** (`dj.css`):
- 36px icon buttons, and 36px buttons with a hairline border on `--surface-2`.
- The primary button is solid `--accent` with near-black text.
- Segmented controls sit on `--surface-0`, with the active segment on `--surface-2`.
- Focus is a 2px `--accent` outline.

## Pages

### Explore (`/`)

**Idle state:**
- The headline "What are you in the mood for?", which uses gradient text. That breaks our own
  rules and is known.
- A song search bar with type-ahead. Rows show cover, title and artist.
- "Top track seeds": your own top tracks as starting points.

**After you choose a song:**
- The search bar compacts and gets a ✕ to clear.
- A **Song profile** card appears with:
  - title and artist
  - tags, which you tap to select
  - an AI "Analysis" list of aspects, also selectable
  - a "Sound profile" radar chart
  - an "About" section

  Selecting tags or aspects and pressing Discover gets 12 similar songs. They show as a playlist
  result with a cover header ("Similar songs based on…"). Clicking any result makes it the new
  profile, so you can keep exploring.

**States:** "Finding songs..." while it loads. If no AI is connected, it says "Connect an AI
account using the ⚙ icon".

### Playlist Builder (`/playlist-builder/`)

- A chat input: "Describe your playlist… (e.g. 'late night jazz for studying')", plus a song count
  setting.
- The result is a playlist with a song card per track. Songs it couldn't match are flagged, so the
  user can swap them.
- Actions: save as a Spotify playlist (a name modal), add to the queue, or drag a song onto the
  Playlists panel.
- Supports follow-up messages that refine the playlist.

### Profile (`/profile/`)

- Logged out: a single "Login with Spotify" button.
- Header: avatar, display name, follower count, Log Out.
- A period control: three chips for short, medium and long term.
- A dashboard of modules. Each module scrolls on its own and can expand to take over the page;
  the others hide. The modules are:
  - **Top Tracks:** song cards with save and explore.
  - **Top Artists:** a numbered table with image, name and genres.
  - **Top Genres:** radar, diversity score ("eclectic / balanced / focused") and bar chart.
  - **Eras:** a column chart by decade.
  - **Taste over time:** a trend chart, plus average song length and release year per period.
  - **Listening clock:** a heatmap.
- `docs/ideas.md` notes the owner wants the controls integrated better and the track list to match
  the other pages.

### DJ (`/dj/`): the newest and most designed page

A widget grid modelled on Robinhood Legend. Editing is locked by default: **Edit layout** shows
drag handles, resize corners, remove ✕, an "Add widget" menu and Done. Esc cancels. The layout
saves per browser.

**Presets:**
- **Host** (default):
  - Now playing, with DJ controls under it, on the left (3 cols).
  - Next moves in the middle (6 cols).
  - Requests over Up next on the right (3 cols).
- **Board:**
  - A compact Now playing banner across the top.
  - A row of single-move widgets.
  - Up next, Requests and controls along the bottom.
- **Focus:** a big Now playing beside Next moves.

**Widgets:**

| Widget | Content |
|---|---|
| Now playing | Art, title (24/600), artists, progress, back/play/next, less like this / more like this, device. The background is a low-chroma tint from the cover's colour, crossfading over 400ms (the one atmospheric element on the page). |
| DJ controls | Mode, Safe↔Bold, Clean only, an "Avoiding N songs, N artists" list. Goal can dock inside it. |
| Goal | None / Destination / Build to peak / Wind down / Peak then cool / Drift, with length and progress |
| Next moves | Every move kind stacked, 2–3 picks each. Refresh button in the header. |
| Single move | One move kind's picks |
| Up next | Songs already sent to Spotify, then upcoming ones. Reorder, remove, "Later", "+ Add song" (search). ✦ marks songs the DJ picked. |
| Requests | Songs that appeared in the Spotify queue that the app didn't add (guests). Keep / Later / Decline. The count badge is red. |
| Song profile | The Explore profile for the selected song. Click any row to select it. |
| Recently played | This session's history |

**Song row:** art, title, artist, then a reason on up to 2 lines in muted 13px text. A ⋯ menu,
and a + button that turns into ✓ once queued.

**Move vocabulary** (the app's signature, shared with iOS):
- **Hold:** keep the vibe
- **Lift:** raise the energy
- **Drop:** give the room a breather
- **Pivot:** change genre, keep a thread
- **Curveball:** something unexpected
- **Toward:** next step toward your goal (purple, the only purple in the content area)
- **Drift:** somewhere new

**Modes:**
- **Whisper:** suggests only when you ask.
- **Co-pilot:** always has moves ready; you pick.
- **Autofill:** adds a pick when the queue runs dry. Remove it to veto.
- **Driver:** keeps 3 songs lined up and chooses the moves itself. Set a goal to steer it.

**Sync:**
- The queue and settings sync across devices (web and iPhone) through the backend.
- Only one device is "primary" and actually sends songs to Spotify. The others edit.
- A banner says which device is driving and offers "Drive from here".

**States** (every widget has all of them):
- Loading shows skeleton rows, never spinners.
- Empty shows an invitation with a verb.
- Error shows a plain sentence and a retry.
- Rate-limited: "Spotify is rate-limiting this app right now. Try again later."
- No AI key: "Add an AI key in Settings to get suggestions." with a button.
- No device: "Open Spotify on any device to start playback."

## Design stance already agreed (DJ brief, `docs/brainstorm.md`)

- **Product register:** the tool should disappear into the night. Familiarity a Spotify or Legend
  power user would trust. Glanceable, with fast, confident taps.
- **Restrained colour, one meaning per hue:**
  - Blue means action, progress and selection.
  - Purple means the goal's influence.
  - Red means decline and alerts.
  - Success green isn't used. The settings dot is the one exception.
- **Refused:** aurora gradients, glassmorphism, neon glow, gradient text, and identical card grids.
- **Widget chrome:** a `--surface-1` body, 12px radius, no shadow. The header is 40px with a
  hairline. Rows are bordered, not cards inside cards.
- **Type scale:** 1.2 (12 / 14 / 16 / 20 / 24). Sentence case. No uppercase tracked labels on the
  DJ page; the older nav pills still use them.
- **Icons:** one outline SVG set (Tabler-style).
- **Motion:** 150–250ms with exponential ease-out, for state changes only. Nothing animates on page
  load. Reduced motion gets instant swaps.
- **Copy:** buttons are verb + object ("Add song", "Edit layout", "Reset to Host"). No em dashes
  in UI strings.

## Known inconsistencies (good design-session targets)

1. **Two eras of style.**
   - The DJ page follows the newer brief: sentence case, an SVG icon set, restrained colour.
   - Explore, Playlist Builder and Profile are older: uppercase tracked nav pills, a ⚙ glyph,
     gradient headline text, and ad hoc spacing.
   - The nav and header predate the brief.
2. **Song rows differ** across Explore search, playlist results, Profile's Top Tracks and the DJ.
3. **Profile** controls feel bolted on. Its alt text and empty states are rough.
4. **No responsive design below 800px.** It's out of scope today, but worth deciding for later.
   The iPhone app covers mobile.
5. **Placeholder covers** for songs with no art are a plain block today.

## Upcoming features to design for (filed ideas)

- **Save tonight's set** as a Spotify playlist at the end of a session, with an optional AI recap.
- **DJ picks seeded from your library,** with a Familiar ↔ New slider.
- **A DJ mode that needs no AI key,** built on Last.fm's similar tracks.
- Later ideas: night presets (dinner / pregame / peak / afterparty), taste memory across nights,
  and Apple Music as a second provider (song identity is already provider-neutral, by ISRC).

## Screenshots (in the design pack)

Captured 2026-10-26 at a 1280×800 viewport and saved at 800×500. Explore idle is at 1440×900.
The DJ shots (05–08, 13–15) were taken with a song playing and suggestions loaded. The Explore and
Playlist Builder shots were taken before an AI key was connected, so their AI parts show the
no-key state.

| File | Shows |
|---|---|
| `01-explore-idle.jpg` | Explore: gradient headline, search, "start from your top tracks" grid |
| `02-explore-search-typeahead.jpg` | Type-ahead results for "redbone" |
| `03-explore-song-profile.jpg` | Song profile (tags, About, Discover button disabled, no-AI notice) |
| `04-playlist-builder-empty.jpg` | Playlist Builder before a prompt |
| `05-dj-host.jpg` | DJ, Host preset: Now playing with album-art tint, Next moves (Hold/Lift/Drop picks with reasons), Up next, the "Driving from iPhone" sync banner |
| `06-dj-board.jpg` | DJ, Board preset: compact Now playing banner, single-move widgets |
| `07-dj-focus.jpg` | DJ, Focus preset |
| `08-dj-edit-layout.jpg` | DJ in Edit layout mode (handles, ✕, resize corners, Add widget / Reset / Cancel / Done) |
| `09-playlists-panel.jpg` | The docked Playlists panel over Explore |
| `10-ai-settings-popover.jpg` | AI settings popover |
| `11-profile-top.jpg` | Profile: header, period chips, Top Tracks / Top Artists / Eras |
| `12-profile-lower.jpg` | Profile scrolled: Taste over time, Listening clock |
| `13-dj-moves-loading.jpg` | Next moves loading (skeleton rows) |
| `14-dj-whisper-get-moves.jpg` | Next moves in Whisper mode, waiting for "Get moves" |
| `15-mini-player-on-explore.jpg` | The mini player bar at the bottom of Explore |

Not captured: a generated playlist, the AI song analysis on Explore, and the Requests widget with
a guest request in it.

## Files to look at

- `src/web/frontend/src/routes/`
  - `+layout.svelte`, `Header.svelte`, `styles.css`
  - `+page.svelte` (Explore), `playlist-builder/`, `profile/`, `dj/`
- `src/web/frontend/src/lib/components/`
  - shared: `SongCard`, `SongSearch`, `SongProfile`, `PlaylistResult`, `PlaylistsPanel`,
    `ChatInterface`, `LLMSettingsPanel`, the charts
  - DJ: `dj/*` (widgets, `dj.css`, `Icon.svelte`, `MiniPlayer.svelte`)
- `src/web/frontend/src/lib/dj/layout.js`: the widget catalog, presets and move summaries.
- `docs/brainstorm.md`: the section "DJ Companion — Web Design Brief (2026-10-25)".
