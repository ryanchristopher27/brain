# Spotify Web API — Domain Rules

Expert guidance on the **current** state of the Spotify Web API (knowledge anchored ~2026-06; the API changes, so **verify live** when something looks off — see "Verify empirically"). The single most important fact: **Spotify quietly deprecated a swath of endpoints and stripped fields for apps created after 2024-11-27, and the official docs do not reliably reflect this.** Assume the docs are optimistic; trust the response you actually get.

---

## 1. The 2024-11-27 deprecation wall (read this first)

For apps **created after 2024-11-27** (or not already granted extended access), these are **gone** — they return `403`/`404` even with correct auth and scopes:

- **Audio Features** (`/audio-features`) — energy, danceability, valence, acousticness, tempo, etc.
- **Audio Analysis** (`/audio-analysis`)
- **Recommendations** (`/recommendations`) — the "get recs from seeds" endpoint
- **Related Artists** (`/artists/{id}/related-artists`)
- **Featured Playlists**, **Category's Playlists**
- **30-second previews** — `preview_url` is now `null` on most/all tracks

Empirically also observed on new apps (undocumented):
- **`popularity` is stripped from BOTH track and artist objects** — top-items, `/tracks`, and top-artists all return `popularity: 0`/absent. There is **no popularity signal of any kind** on a new app. Do not build "mainstream-ness" on it. (Possible proxy worth probing: artist `followers.total` — but verify it isn't also stripped before relying on it.)

**Implication:** if you're building anything that wanted audio features, recs, or popularity-based "taste" analysis, design for these being unavailable. Probe at runtime and degrade gracefully (see §6). An LLM scoring tracks is the fallback for audio-feature-like data, but it's slow/costly at scale.

---

## 2. Undocumented field quirks (verified, not in the docs)

- **`/me/playlists` returns the track ref under `items`, not `tracks`.** Shape is still `{href, total}`. Code reading `playlist['tracks']['total']` silently gets `0`. Read `playlist.get('items') or playlist.get('tracks')`.
- **`current_user_top_tracks` items omit `popularity`** (and other "full track" fields you'd expect). `album`, `duration_ms`, `explicit`, `id`, `name`, `artists` are present; `popularity` is not.
- **Fields are not guaranteed even when documented.** `artist['genres']`, `images`, etc. can be absent on specific objects. Always use `.get(key, default)`.
- **Playlist cover:** `images[0].url` is *either* the user's custom image *or* Spotify's auto-generated 4-song mosaic — you don't need to build the mosaic yourself.
- **Genres are artist-level only.** Tracks have no genres. "Genres a user listens to" must be derived from their top **artists'** genres (weight by rank).
- **`release_date`** on a track's album works and is reliable (`"2019-05-17"`, `"2019-05"`, or `"2019"` — take the first 4 chars for the year). Good for "era" analysis when audio features are gone.

---

## 3. Auth (the only flows that work for new apps)

- **Implicit grant (`response_type=token`) is dead** (deprecated April 2025). Do not use.
- **SPAs / browser clients → Authorization Code with PKCE.** No client secret in the browser; PKCE verifier/challenge; refresh tokens work with just `client_id` (no secret) on refresh.
- **App-level / server-to-server (no user) → Client Credentials.** Use for **search, public catalog lookups** — anything not tied to a user. No user login required.
- **Redirect URI: `http://127.0.0.1:<port>/...`, NOT `localhost`.** New apps reject `localhost` as "insecure." On macOS, also bind your dev server to `127.0.0.1` explicitly (it resolves `localhost` to IPv6 `::1`, which won't match).
- **Adding a scope requires re-auth.** An existing token does not gain new scopes — calls needing the new scope return `403` until the user logs out/in. Detect the 403 and prompt "reconnect," don't fail silently.

### Common scopes → what they unlock
| Scope | Enables |
|-------|---------|
| `user-top-read` | `/me/top/{artists,tracks}` |
| `playlist-read-private` | list the user's private playlists |
| `playlist-modify-private` / `playlist-modify-public` | create playlists, add/remove tracks |
| `user-library-read` / `user-library-modify` | read/modify Liked Songs (`/me/tracks`) |
| `user-modify-playback-state` | queue / control playback |
| `user-read-private`, `user-read-email` | profile details |

---

## 4. Best way to get each kind of data

- **Search** → Client Credentials, `GET /search?q=...&type=track`. App-level, no user token. For autocomplete, also surface `album.images` (smallest, `images[-1]`) for thumbnails.
- **User profile** → user token, `GET /me`.
- **Top items** → `GET /me/top/{type}?time_range={short_term|medium_term|long_term}&limit=N`. `short_term`≈4 weeks, `medium_term`≈6 months, `long_term`≈years. Returns *partial* track objects (see §2).
- **A user's playlists** → `GET /me/playlists` (paginate via `next`). Filter to editable: `owner.id == me.id || collaborative`.
- **Add to playlist** → `POST /playlists/{id}/tracks` with track URIs/IDs. **Never call with an empty list — it 400s.** Guard `if track_ids`.
- **Create playlist** → `POST /me/playlists`. (See §5 — spotipy's helper can 403 on new apps.)
- **Liked Songs** → read `GET /me/tracks`, write `PUT/DELETE /me/tracks?ids=`, check membership `GET /me/tracks/contains?ids=` (batch up to 50).
- **Full track details** (where available) → `GET /tracks?ids=` (batch up to 50). Note: still won't give `popularity` on new apps.
- **"Era" of taste** (audio features being gone) → average `album.release_date` year across top tracks per time_range. Cheap, no extra calls, genuinely informative.

### Batch everything
- `/tracks?ids=` → 50 ids/call
- `/audio-features?ids=` → 100 ids/call (if available)
- `/me/tracks/contains?ids=` → 50 ids/call
Don't loop one-at-a-time when a batch endpoint exists.

---

## 5. spotipy (Python) gotchas

- **`SpotifyClientCredentials` for app-level endpoints.** `SpotifyOAuth.get_access_token()` with no cached token tries to **spin up a local HTTP server** to catch the redirect — which throws `OSError: Address already in use` / hangs in a backend. For search/catalog, use `Spotify(auth_manager=SpotifyClientCredentials(...))`.
- **`user_playlist_create()` can 403 on new apps.** Fall back to the raw call: `spotify._post("me/playlists", payload={"name":..., "public": False})`.
- **`playlist_add_items(id, [])`** (empty) → `400`. Guard it.
- **Deprecation/permission failures raise `spotipy.SpotifyException`** with `e.http_status` (403/404). Catch it and degrade to a "feature unavailable" path rather than 500-ing.
- **`current_user_playlists()` / `current_user_top_tracks()`** return the raw JSON — apply the §2 quirks (the `items` vs `tracks` rename, missing `popularity`).

---

## 6. Operating principles (how to work with this API well)

1. **Degrade gracefully.** Wrap deprecated-risk calls (`audio_features`, `recommendations`, `popularity`) in try/except and return `None`/empty so the feature soft-disables instead of crashing. Let the UI adapt to what's present.
2. **Verify empirically before designing around an endpoint.** Don't trust the docs that an endpoint/field exists for *this* app — make one call and **dump the raw response keys**. This session found three field surprises that way. A 30-second probe beats hours of building on a phantom field.
3. **A silently-empty result usually means a stripped field, not "no data."** Zeros across the board (e.g., `popularity: [0,0,0]`) → the field is gone, not the user's library.
4. **Prefer native, cheap data** (genres, release dates, durations, explicit flags, track/artist metadata) over deprecated endpoints or LLM inference. Reach for an LLM only when the native data genuinely can't answer the question.
5. **Surface scope/re-auth problems to the user.** A 403 after adding a scope means "reconnect," not "broken."
6. **CORS masks 500s in browsers.** A backend exception that drops CORS headers shows up as a CORS error in the browser console. Add a global exception handler that preserves CORS headers so the real error is visible.

---

## 7. Quick reference — is it available on a new app?

| Want | Endpoint | New-app status | Use instead |
|------|----------|----------------|-------------|
| Energy/danceability/valence | `/audio-features` | ❌ deprecated | LLM inference, or skip |
| Song recommendations | `/recommendations` | ❌ deprecated | LLM-generated + validate via search |
| Related artists | `/artists/{id}/related-artists` | ❌ deprecated | LLM / genre overlap |
| 30s preview | `track.preview_url` | ❌ usually null | Spotify embed iframe |
| Track/artist popularity | `track.popularity`, `artist.popularity` | ❌ stripped (both) | release-year / duration / explicit / genre signals |
| Search | `/search` | ✅ | — |
| Top tracks/artists | `/me/top/*` | ✅ (partial objects) | — |
| Playlists CRUD | `/me/playlists`, `/playlists/{id}/tracks` | ✅ | mind the `items` rename |
| Liked Songs | `/me/tracks*` | ✅ | — |
| Genres | on artist objects | ✅ | derive from top artists |
| Release date / era | `album.release_date` | ✅ | great audio-features substitute |
