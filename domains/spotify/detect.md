# Detection Signals — Spotify

Claude checks for these signals at session start. If any primary signal is present, the domain
activates. Secondary signals strengthen the match but are not required alone.

## Primary Signals
- A dependency manifest lists a Spotify SDK: `spotipy` (Python `requirements.txt` /
  `pyproject.toml` / `environment.yml`), or `spotify-web-api-node`,
  `@spotify/web-api-ts-sdk`, `@spotify/web-api-js` (Node `package.json`).
- Source files import a Spotify SDK: `import spotipy`, `from spotipy...`, or
  `require('spotify-web-api-node')` / `@spotify/web-api-ts-sdk`.
- A `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REDIRECT_URI` env var appears in
  `.env`, `.env.example`, or config.

## Secondary Signals
- Source references `accounts.spotify.com` or `api.spotify.com` (auth/endpoint URLs).
- OAuth scope strings present: `user-top-read`, `playlist-modify-private`, `user-library-read`, etc.
- PKCE flow code (`code_challenge`, `code_verifier`, `response_type=code` against Spotify).
- `CLAUDE.md` declares `domains: spotify`.

## Conflicts
- None. Coexists with `frontend` (a SvelteKit/React + Spotify app activates both) and any
  backend domain.

## Manual Override
To force-activate this domain regardless of signals, add to the project's `CLAUDE.md`:
```
domains: spotify
```
