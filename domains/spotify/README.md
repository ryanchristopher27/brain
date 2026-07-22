# Domain: Spotify

## What This Domain Covers
Working with the **Spotify Web API** — auth flows, available vs. deprecated endpoints, the
real (often undocumented) state of fields and responses, and the best way to fetch each kind
of data. It encodes hard-won knowledge that the official docs don't reflect, especially the
2024-11-27 deprecation wall and several field quirks verified empirically (the `/me/playlists`
`tracks`→`items` rename, `popularity` stripped from track objects, audio-features/recommendations
gone for new apps).

## When It Activates
See `detect.md` for the full signal list. Broadly:
- A Spotify SDK (`spotipy`, `spotify-web-api-node`, `@spotify/web-api-ts-sdk`) in the deps or imports.
- `SPOTIFY_CLIENT_ID` / redirect URI / OAuth scopes in config or source.

## What It Changes
- **Rules:** `rules.md` — what's deprecated, the field quirks, the only working auth flows
  (PKCE for SPAs, client-credentials for app-level, `127.0.0.1` not `localhost`), the best
  endpoint for each data need, spotipy gotchas, and the operating principle to **probe the
  live response and degrade gracefully** rather than trust the docs.
- **Commands:** none yet.
- **Cursor rules:** `.cursor/rules/spotify.mdc`

## Maintenance
The Spotify API changes. When a project hits a new quirk or a previously-dead endpoint comes
back, update `rules.md` (especially §1 deprecation wall and §2 field quirks) and re-run
`install/install.sh`.
