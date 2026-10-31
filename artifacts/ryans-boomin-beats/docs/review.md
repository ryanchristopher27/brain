# Review — AI DJ Companion DJ0–DJ4 + shared backend fixes
Date: 2026-10-23
Triggered by: ad hoc (pre-commit, after /build of DJ1–DJ4)
Scope: every uncommitted change in the working tree. This is the DJ work (`routers/dj.py`,
`routers/player.py`, `src/ios/BoominBeats/DJ/*`, `RootView`, `SettingsView`, `Config`,
`APIClient`) plus the shared fixes (`spotify_client.py`, `spotify_validator.py`, `llm_client.py`,
`main.py`, `spotify_actions.py`, `PlaylistResult.svelte`). It also includes an **earlier
uncommitted refactor that predates this session**: routing every Spotify client through
`services/spotify_client.py` (`profile.py`, `search.py`, `spotify_actions.py`, part of `main.py`).
Focus: All

## Summary

Healthy. The DJ milestones match the plan, and each deviation was flagged and logged during the
build: the adaptive buffer, the ⋯ menu instead of long-press, and Driver's scope before DJ6. There
are no critical findings. The main gaps are two boundary or robustness issues in `dj.py`, a tracked
token file, and no automated tests for the iOS queue logic.

Critical: 0 | Warning: 4 | Suggestion: 6

## Plan Adherence

- DJ0–DJ4 are built as planned. The results are recorded in `docs/plan.md`, and the tracker tasks
  for DJ1–DJ4 are in review.
- Deviations, all logged: the adaptive buffer (1 in the foreground, N on background) instead of a
  fixed 5; a ⋯ menu instead of long-press for do-not-play; Driver = "keep 3 lined up" until DJ6;
  `_OVERASK` 1→2; Groq `reasoning_effort='low'` (approved by the owner).
- Built but **not exercised live**: drag-to-reorder Up Next, the "Later" swipe, the buffer-depth
  stepper, the no-device and "nothing playing" states, skip detection feeding `skipped`, and the
  DJ0.1 Jam half (deferred by the owner).
- Live verification of DJ3/DJ4 is blocked until about 2026-10-24 21:15 CDT by Spotify's app-wide
  search 429. The fail-fast path is verified.

## Code Quality

- The backend follows the established patterns: thin routers, `services/` for clients, pure
  helpers (`normalize_*`, `select_tracks`, `salvage_truncated`) with unit tests. 61 tests pass.
- iOS follows the `ProfileModel` pattern (`@MainActor @Observable`, models injected through the
  environment). The file-system-synchronized group picked up `DJ/` with no pbxproj churn.
- The `QueueStore` / `SuggestionStore.autopilot` logic is the most intricate code in the change, and
  it has no automated check. The iOS project has no test target.

## Security

- BYOK key: stored in the Keychain on iOS, and in the existing `localStorage` on the web. It travels
  per request, with no server-side storage. ✓
- No secrets were added to source. `.env` stays gitignored. **But `src/web/backend/.cache` (a
  spotipy client-credentials token cache) is tracked despite `.gitignore`.** It was committed in
  `c0e744c`, before the ignore rule existed.
- `/dj/suggest/` validates scalars (`per_move`, `adventurousness`) but not list or string sizes.
- LLM output never reaches the client unvalidated: every suggestion is re-resolved through Spotify
  search and filtered. Prompt injection through track titles can only affect the user's own
  suggestions.
- No injection sinks: no SQL, shell or HTML rendering of model output.

## Findings

### Critical
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| — | — | None | — | — |

### Warning
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| W1 | `routers/dj.py` `_spotify_recent` | The best-effort history call catches builtin `TimeoutError`/`ConnectionError`, but `requests.exceptions.ReadTimeout`/`ConnectionError` don't subclass them (verified). A slow Spotify history call therefore fails the *whole* suggestion with a 503 instead of being skipped. | Also catch `requests.exceptions.RequestException`. | Fixed pre-commit |
| W2 | `routers/dj.py` `SuggestRequest` / `TrackRef` | Unbounded `recent`/`upcoming`/`liked`/`disliked`/`skipped`/`avoid_*` lists and string lengths. A client can inflate the prompt, which costs the user's LLM budget, and on the hosted instance it sits behind only the device key. | `Field(max_length=…)`: lists ≤ 50, strings ≤ 300. | Fixed pre-commit |
| W3 | `src/web/backend/.cache` | A token cache is tracked in git despite `.gitignore`. It holds a (now expired) app access token, which is in history since `c0e744c`. | `git rm --cached src/web/backend/.cache`. The token is short-lived, so no rotation is needed. | Fixed pre-commit |
| W4 | `src/ios/BoominBeats/DJ/QueueStore.swift`, `SuggestionStore.autopilot` | Order-sensitive logic (arrival trimming, skip-on-arrival, reconcile matching with duplicates, Autofill/Driver targets) has no runnable check. It was only verified by hand in the Simulator. | Add an XCTest target and pure-logic tests with a fake client. → /iterate | Fixed before DJ5 |

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| S1 | `Networking/APIClient.swift` | Sends `X-LLM-Provider`/`X-LLM-Key` on **every** request, not just LLM routes. That widens where the key travels (proxies, future logging) for no benefit. | Attach them only for `dj/`, `llm/` and `song/` paths. | Open |
| S2 | `DJ/QueueStore.reconcile` | `GET /me/player/queue` returns at most 20 items. If more than 20 non-app tracks sit ahead (a busy Jam), still-queued `sent` items get dropped as "played". | Only drop `sent` items when the response has fewer than 20 entries, or keep unmatched ones. | Fixed before DJ5 |
| S3 | `DJ/NowPlayingView.swift` `content()` | The `ScrollView` was wrapped around an un-reindented `VStack`, so it misreads as unbalanced. | Re-indent. | Open |
| S4 | `DJ/SuggestionStore.swift` doc comment | It says a call "takes ~6s", which is stale after `reasoning_effort='low'` (about 3s). | Update the comment. | Open |
| S5 | `routers/spotify_actions.py` | It imports `player_error` from another router. | Move `player_error` to `services/` when next touched. | Open |
| S6 | `DJ/QueueStore.autoSkipped` | Grows for the whole session. | Cap it or prune it on arrival. Trivial. | Open |

## Resolved This Session
- `queue_songs` 403 → "Premium required" mis-mapping. Fixed with `player_error`, and the web
  `PlaylistResult` "unknown error shown as success" bug fixed alongside it.
- Retired Groq model (`llama-3.3-70b-versatile`) → `openai/gpt-oss-120b`.
- Expired Spotify token surfaced as 500 → now 401.
- A Spotify 429 hung workers for the Retry-After duration (about 23h) → own `Session` without
  Retry-After, plus a 429 → 503 handler.
- The DJ title-only fallback wasted searches → `fallback=False`, plus the process cache.

## Carried to /iterate
1. **W4:** XCTest target + `QueueStore`/autopilot tests. Highest value before DJ5, which builds on
   reconcile.
2. **S2:** reconcile's 20-item ceiling. It matters exactly when DJ5 (guest requests) lands.
3. **S1:** scope the LLM headers to LLM routes.
4. S3–S6: tidy-ups, whenever those files are next touched.

None of these block shipping. W1–W3 were fixed before the commit: `requests` exceptions are caught
(with a test), `SuggestRequest` has bounds (lists ≤ 50, strings ≤ 300, with a test), and `.cache`
is untracked with `git rm --cached`. 63 tests pass.

## Follow-up (2026-10-23, before DJ5)
- **W4:** added a `BoominBeatsTests` target to the hand-written pbxproj: a synchronized folder,
  hosted in the app, using Swift Testing. The pure logic was extracted into
  `QueueStore.arrival(of:in:)`, `QueueStore.reconciled(_:against:)` and
  `SuggestionStore.autopilotCandidates(...)`, with 11 tests. Run:
  `xcodebuild test -scheme BoominBeats -destination 'platform=iOS Simulator,name=iPhone 17 Pro'`.
- **S2:** `reconciled` drops only the *played prefix* (everything before the first `sent` track
  still visible). When the view is full (20), it keeps the trailing tracks it can't match. Keeping
  "any unmatched track when the view is full" would have been wrong, because the playing context
  nearly always pads the view to 20. Ceiling: with 20+ non-app tracks ahead, nothing of ours is
  visible, and everything is treated as played.

---

# Review — SY1 backend sync API
Date: 2026-10-25
Triggered by: /build completion (SY1), commit `822070f`
Scope: `routers/dj_state.py`, `services/dj_store.py`, `services/spotify_identity.py`, the
`routers/player.py` piggyback, `config.py`, `supabase/migrations/…_dj_state.sql`,
`tests/test_dj_state.py`
Focus: All, with an emphasis on security (the first persistent server-side state)

## Summary

Sound. All 8 SY1 tasks were built as planned, and the 409/seed/claim/piggyback flow is verified
live. No criticals. One security warning: expired Spotify tokens stay accepted for sync, because
of how long user ids are cached. The "never break player state" guarantee has a gap. The repo's
migration file doesn't match the recorded version.

Critical: 0 | Warning: 4 | Suggestion: 4

## Plan Adherence

- Every SY1 task is done. The deviations are allowed by the plan or noted in the SY1 result:
  `httpx` instead of the `supabase` package; the piggyback costs one server-side DB read per poll.
- The validation is stricter than the plan asked (unknown fields forbidden at every level, not just
  top-level), and that's on purpose.

## Code Quality

- Thin router, store in `services/`, pure helpers (`primary_info`, `heartbeat_due`) unit-tested.
  It matches the existing patterns.
- The happy path of the piggyback (`dj_status` writing a heartbeat when due and returning
  version/primary) is only covered by the live check, not by a test.

## Security

- **No injection:** PostgREST filters go through `httpx` params (URL-encoded), and `eq.` values
  are compared literally. The device id is bounded to 64 characters.
- **Authorization:** rows are keyed by the Spotify id resolved from the caller's own token, so a
  client can't name another user's row. A 409 only ever returns the caller's own document.
- **Secrets:** the service key is server-only (`.env`, gitignored, scan clean). RLS deny-all means
  a leaked anon key can't read the table.
- **Input:** bounded lists and strings and strict schemas. The worst-case document is about 1 MB.
- **Weakness:** see W1. The identity cache outlives tokens.

## Findings

### Critical
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| — | — | None | — | — |

### Warning
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| W1 | `services/spotify_identity.py` `_TTL` | User ids are cached for 50 minutes from *first use*, and `/dj/state` never calls Spotify after that. A token first used near its 1-hour expiry keeps working for sync for up to ~50 minutes **after** it expires, which widens the window a leaked token is useful. | Cut `_TTL` to 5 minutes. That's one `/me` call per device per 5 minutes and bounds expired-token acceptance to 5 minutes. | Fixed |
| W2 | `routers/player.py` `dj_status` ← `user_id()` | `user_id()` only converts `SpotifyException`. A `requests` timeout or connection error from `/me` escapes `dj_status` (which catches `Unavailable` and `HTTPException`), so the **player poll itself fails with 503**. That breaks the documented "sync never breaks player state" guarantee whenever `/me` is slow. | Catch `requests.exceptions.RequestException` in `user_id()` and raise a 503 `HTTPException`. That covers the sync routes too. | Fixed |
| W3 | `supabase/migrations/20261025180000_dj_state.sql` | Supabase recorded the migration as **`20261025175713`**. If the Supabase CLI is ever used (`db push`/`db diff`), it treats the file as unapplied, re-runs it, and fails with "relation already exists". | Rename the file to `20261025175713_dj_state.sql`. | Fixed |
| W4 | `tests/test_dj_state.py` | The piggyback's success path is untested: heartbeat written only when due, `{version, primary}` returned, `{version: 0}` with no row. Only the failure path has a test. | Add 2–3 tests with the fake store and a stubbed `user_id`. | Fixed |

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| S1 | `routers/dj_state.py` endpoint signatures | `current_user` (a Spotify `/me` call) resolves *before* `get_store`, so an unconfigured server spends a Spotify call before answering 503. | Order the dependencies `store` before `user`. | Open |
| S2 | `routers/player.py` `dj_status` | Imports inside the function. There's no import cycle that needs them. | Move them to the module top. | Open |
| S3 | `routers/dj_state.py` `Goal.startedAt` | Free-form string. A malformed date is stored and fails later on a client. | Type it as `datetime` and dump with `model_dump(mode='json')`. | Open |
| S4 | Data handling | Listening history, feedback and do-not-play now persist server-side, and there's no way to delete them. | Add `DELETE /dj/state` ("Clear synced DJ data") in SY3, and mention it in the data notes. | Open |

## Resolved This Session
- **W1:** `_TTL` cut to 5 minutes. The docstring now explains why the TTL bounds expired-token
  acceptance.
- **W2:** `user_id()` converts `requests` network errors to a 503 `HTTPException`. There's a test.
- **W3:** the migration was renamed to `20261025175713_dj_state.sql`, matching Supabase's record.
- **W4:** three piggyback tests (no session; version + primary; heartbeat only when due and only
  from the primary) plus the identity network-error test. 90 tests pass.

## Carried to /iterate
1. W1, W2, W3: bounded; recommended before SY2/SY3 build on this.
2. W4: tests to accompany the W2 fix.
3. S1–S3: tidy-ups, cheap to do with the above.
4. S4: fits SY3, where the iOS UI gets a sync section.

# Review — W1–W4 web DJ (+ "Your Claude Code" provider)
Date: 2026-10-25
Triggered by: ad hoc (/review after W4)
Scope: `src/web/frontend/src/lib/dj/`, `lib/components/dj/`, `routes/dj/`, `routes/+layout.svelte`
(the engine and the mini player), the Header/stores/app.d.ts changes; commits 5519b2c..5f45294,
plus the backend Claude Code provider (001e27e).
Focus: All

## Summary
Every W1–W4 item in the plan is built, and the deviations are recorded in the plan's W results.
Logic coverage is good: 39 vitest tests, including the engine tested against a fake SY1 backend.
The two Critical findings both come from the web engine now living app-wide, in every tab and for
as long as the page stays open. That is exactly the "host from a laptop all night" use case.
**Critical: 2 | Warning: 4 | Suggestion: 3**

## Plan Adherence
- **W1:** logic port, sync client and vitest ports are done. Deliberate departure from the brief:
  one `dj.js` engine over a single synced `doc` store instead of four store files. It was recorded
  in the W1 result, and it makes every edit one push.
- **W2:** grid, the seven widget types, the presets and Edit layout are done. The deviations
  (Goal docked in Host, DJ controls in Board, Now playing minimum height 3) are recorded.
- **W3:** mini player, ambience and audit are done.
- **W4:** linking + Song profile, Recently played, keyboard move/resize and undo are done. The
  reimplemented profile widget is recorded.
- **Still open from the plan:** live-resize breakpoint switching is unverified, because the
  browser pane was hidden.
- **Goal "Exactly one device drives … never double-queue":** broken by C1 below for two tabs in
  the same browser.

## Code Quality
- Clear separation between pure logic (`logic.js`, `layout.js`, `ambience.js`) and stateful code,
  and all three pure modules have tests.
- Comments explain *why* (quota, Spotify quirks, iOS parity) consistently.
- Gaps: grid wrapper behaviour (save/add/nudge) and the components have no automated tests. Both
  bugs found while building W2 lived there and were caught only by hand.

## Security
- **XSS:** no `{@html}` anywhere. Track text and reasons render as text. Image URLs only go into
  `<img src>` and a CORS image load.
- **Claude Code:**
  - `create_subprocess_exec` runs with no shell.
  - The prompt goes over stdin.
  - `--tools ""`, `--strict-mcp-config` and project-only settings mean prompt injection from track
    names can't act.
  - Disabled on Vercel.
  - The local backend still sits behind CORS preflight for JSON and custom headers.
- **LLM key:** sent only to the app's own backend, for `dj/suggest` and `song/profile`. Storing it
  in localStorage is the existing BYOK design and was not re-flagged.
- No secrets in the diff. Nothing new is logged.

## Findings

### Critical
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| C1 | `lib/dj/dj.js` (device id in localStorage) | Two tabs in one browser share the same `dj_device_id`, so **both** think they're the primary. Both send the same Up next track to Spotify (a double-queue). Each then sees the other's sends as guest requests, breaking the plan's "exactly one device drives" goal. Opening a second tab (DJ page + Explore) is enough. | Elect one driving tab per browser with the Web Locks API (`navigator.locks.request('boomin-beats-dj-driver', …)`, held until the tab closes). Driving actions check `isPrimary && tabLeader`; the next tab takes over when the leader closes. | Fixed |
| C2 | `lib/spotifyAuth.js`, `routes/+layout.svelte` | The Spotify token is only refreshed on page load. A DJ page left open goes stale about 1 hour into a party, and the engine then 401s on every poll: no playback state, no top-ups. | Re-hydrate on a timer, with a margin before expiry (e.g. every 60s, refreshing within 2 min of `expires_at`), and also as soon as the engine sees a 401. | Fixed |

### Warning
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| W1 | `components/dj/SongProfile.svelte` (`$: load(key, song)`) | Re-runs on every player poll, because `song` is a new object each time. While a profile is loading (≈16s with Claude Code), each poll starts **another** `/song/profile/` call, so about 8 LLM + Last.fm calls per song. | Skip `load` when the key is unchanged (track a `loadingKey`). | Fixed |
| W2 | `lib/dj/dj.js` `pull()` (and iOS `DJSync.pull`) | A local edit made while the GET is in flight is overwritten by `apply(server)` and never pushed, because doc == base afterwards. Small window, but the edit is silently lost. | Snapshot the doc before the GET. If it changed by the time the response lands, apply `merge(snapshot, current, server)` and push. | Fixed |
| W3 | `lib/dj/dj.js` `push()` | Only 200 and 409 are handled. A 422 (client/server schema drift) or a persistent 5xx drops every push silently, and the UI still says "synced". | Set `sync.status = 'error'` with a short message on other statuses, and stop claiming synced. | Fixed |
| W4 | `routes/+layout.svelte` | The engine starts when a token appears but never stops. After sign-out it keeps polling and 401s every few seconds. | `$: $access_token ? dj.start() : dj.stop()` (client only). | Fixed |

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|---|---|---|---|
| S1 | `components/dj/Grid.svelte` | `save`/`add`/`nudge` have no automated test. Both W2 grid bugs (lost size on add, inclusive breakpoints) were found only by hand. | Add a jsdom vitest for the wrapper, or a Playwright smoke test of Edit layout → Done → reload. | Fixed |
| S2 | `lib/dj/dj.js` (doc hydration) | `{...emptyDoc(), ...stored}` is a shallow merge, so a stored doc from an older shape can lack nested fields (e.g. `options.avoidArtists`) and crash `.some`. | Deep-merge the stored doc onto `emptyDoc()` section by section. | Fixed |
| S3 | `services/claude_code.py` | No limit on concurrent `claude` processes. A burst (several tabs, profile + suggest) spawns one each. | A module-level `asyncio.Semaphore(2)` around `run`. | Fixed |

## Resolved This Session
All nine were fixed on 2026-10-25, each with a test:
- **C1:** Web Locks elect one driving tab per browser (`drives() = isPrimary && tabLeader`); the
  next tab takes over when the leader closes.
- **C2:** the token is refreshed within 2 min of expiry, on a 60s timer and immediately after a
  401.
  - **Found while fixing it:** concurrent refreshes spent Spotify's rotating refresh token twice,
    and the loser signed the user out. `hydrateToken` is now single-flight, and only
    `invalid_grant` ends the session.
- **W1:** Song profile loads once per song.
- **W2:** `pull()` merges an edit made during the GET, on the web and in iOS `DJSync`.
- **W3:** rejected pushes set `sync.status = 'error'`, shown in the banner.
- **W4:** the engine stops on sign-out.
- **S1:** the grid's save/nudge maths moved to the tested `completeSaved`/`nudgeBox`.
- **S2:** `withDefaults` merges the stored doc section by section.
- **S3:** at most 2 concurrent `claude` processes.

## Carried to /iterate
- None.
