
# Update Ideas


### Profile Page Revamp
- Update the controls to be a little more integrated rather than a whole section above the lists of songs and artists.
- Make the songs list look more like the ones in the other pages.
- Make the page more modular and have more charts and things describing the profile.
    - Look at the songs over the different time frames and chart how the scores for each song on aggregate change over time
    - Make the songs and artists have a minimized summary version that can be expanded to be larger and take up most of the page.
    - When maximized, the other modules go away.
    - Make each modular section scrollable rather than making the whole page scrollable.

- Make a radar chart showing the amount you have listened to each of the top genres

## Profile metrics from Spotify (research, 2026-10-29)
Read-only research against the Feb/Mar 2026 Spotify changelogs and the app's own probes
(plan.md 1684-1755). Still useful in Development Mode: top items, recently played, saved tracks,
playlists, followed artists. Dead: audio features/analysis, recommendations, related artists,
popularity, user followers/country/product, batch track/artist fetches.

Top picks (no new scope unless noted):
1. **Check `artist.genres` first.** It's deprecated and iOS saw it empty; the Genres card and
   summary depend on it. Fallback: Last.fm `artist.getTopTags`, cached.
2. **Stored listening history.** Upsert recently-played into a Supabase table on each visit /
   DJ session: a real 90-day listening clock, plays and hours per week, streaks.
3. **Top-item churn across periods.** New this month, long-time favourites, rising/falling
   artists, compared from the three time ranges.
4. **Library stats.** Liked Songs size and growth (`/me/tracks` `total` and `added_at`) and
   playlist stats (`/me/playlists`).
5. **Polish.** Remove the header follower count (removed from `/me` in Feb 2026, so likely
   always 0); add release-year spread / "new music share" and the explicit and length mix.

Later: followed artists (needs `user-follow-read`, a re-login); Last.fm linking for long
scrobble history; Deezer BPM (field and coverage unverified).
Unverified: genres populated, `external_ids` revert in Dev Mode, `/me/following` in Dev Mode,
top items past 50.
