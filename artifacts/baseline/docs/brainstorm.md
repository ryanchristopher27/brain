# Baseline — Brainstorm

## 2026-10-31

### Problem / Opportunity

WHOOP's app shows each day's scores, but it doesn't make it easy to see your trends against your own norm. You can't ask it open questions, and it can't connect causes (drinks, illness, late meals) to recovery. The WHOOP API doesn't expose the Journal either, so that cause data can't be pulled out.

Baseline now has WHOOP access and a local sync (`npm run sync` → `data/*.json`). The opportunity is to make this data something you can both **look at** and **talk to Claude about**, and to record the context WHOOP leaves out.

### Goals

- See today's state and your trends at a glance, judged against your own baseline.
- Ask Claude questions about the data from anywhere, including your phone, and get answers it works out from the real records.
- Build up your own dataset of daily tags and findings so that questions like "what moves my recovery?" become answerable over time.

### Audience

One person, the owner. Single-user throughout, even once hosted.

### Constraints

- **Data so far:** 56–57 days (Sep 5 – Oct 31, 2026): 56 recovery, 57 sleep, 57 cycles, 78 workouts. That's too few days to support cause-and-effect claims.
- **The API gives summaries only.** There's no continuous heart rate and no Journal.
- **Health data is sensitive.** Hosting needs a real login and an updated privacy policy (`docs/privacy.html`, published as an artifact) before launch.
- **WHOOP rotates refresh tokens.** Only one process may refresh at a time.
- Node 22, no dependencies so far.

#### Data quirks found during the brainstorm

- Some workouts are marked `score_state: "SCORED"` but have `score: null`. Every view has to handle a missing score.
- The first 3 recovery days have `user_calibrating: true`.
- **Sleep need looks wrong.** Summing `sleep_needed` (baseline + debt + strain − naps) gives about 10 h a night, with every one of the 56 nights falling short. Check this against WHOOP's own definition before showing it anywhere.
- WHOOP's days are **cycles** that run from one wake-up to the next, not calendar days. Every record has a `timezone_offset`, and local dates must be computed from it or travel days will shift.

#### First signals (8 weeks, n ≈ 56, so take them loosely)

| Metric | Value |
|---|---|
| Recovery | avg 56; 21 green / 25 yellow / 10 red days; range 6–96 |
| HRV | avg 74 ms; range 22–130 |
| Resting heart rate | avg 57; range 48–80 |
| Sleep | ~6.6 h asleep; performance 73%; consistency 65% |
| Daily strain | avg 11.3 |
| Strain → next-day recovery | correlation −0.24 |
| Sleep length → recovery | correlation 0.19 |
| Workouts | walking 26, running 25, pickleball 9, weightlifting 5, dance 5, tennis 3, other 5 |

### Ideas & Directions

#### Overall shape (agreed): one data layer, two ways in

```
WHOOP API ──sync──▶ Baseline data ──┬──▶ Dashboard      (glance: today + trends)
                    · daily table    └──▶ Claude (MCP)  (ask, derive, save notes)
                    · tags, findings ◀──────────┘
```

The dashboard and Claude read the same tables, so they can't disagree about a number.

#### Daily table (the core data model)

Join cycles, recovery, sleep (not counting naps) and workouts into **one row per local date**: recovery, HRV, resting heart rate, SpO2, skin temperature, hours asleep, sleep performance and consistency, sleep debt, strain, workout count, minutes and sports. Both front ends read from it, and it saves Claude from re-deriving WHOOP's joins in every conversation. Raw records stay available for drill-downs.

#### Dashboard directions

- **A. Today (morning check-in).** Recovery against your baseline, last night's sleep against your sleep need, and a target strain. Designed for a phone first.
- **B. Baseline trends.** HRV, resting heart rate, recovery and skin temperature, each drawn against your rolling 30-day band, with days outside the band highlighted. The view that gives the app its name.
- **C. What moves your recovery.** Correlations between tags or workouts and the next day's recovery. It needs months of data, so it starts as a panel that says how much more data it needs.
- **D. Training log.** Sports, time in each heart-rate zone, and weekly load. Strava could add routes and pace later.
- **E. Sleep.** Debt, consistency, stages, and bedtime drift. Consistency and short sleep are the most actionable signals in the data right now.
- **Findings panel.** Findings Claude saved, pinned on the dashboard, each with its sample size and date range.

#### Claude directions (agreed: available everywhere, and able to save)

1. **Claude Code in `baseline/`.** Works today. Add a `CLAUDE.md` that describes the data and its quirks.
2. **Local MCP server.** Tools over the daily table, for Claude Code and the Claude desktop app.
3. **Hosted MCP server.** Added to claude.ai as a custom connector, so it works on the phone too. Reuses the Trip Fairy remote-MCP pattern.

Rough set of tools: `get_days(start, end)`, `get_workouts(filter)`, `get_sleep(date)`, `add_tag(date, tag, note)`, `list_tags`, `save_finding(text, evidence)`, `list_findings`, `delete_finding`.

#### Tags and findings (agreed: both)

- **Tags:** daily context WHOOP doesn't expose (alcohol, caffeine, sick, travel, late meal, stress). Saved by Claude from conversation, or added on the dashboard.
- **Findings:** conclusions Claude reaches from the data, saved with the evidence behind them (metric, sample size, date range, method), so the dashboard can show how strong each one is.

### Recommendations

1. Build the **daily table first**. It unblocks everything else.
2. **Local first, hosted next.** Get the data model, tags, findings and the MCP tools right on this Mac, then move to hosted storage, the hosted MCP connector, scheduled sync and the hosted dashboard.
3. **Dashboard v1 = Today + Baseline trends + a findings panel**, with sleep folded in. Directions C (correlations) and D (training log, with Strava) come later.
4. Every number shows its source: a WHOOP score or a Baseline calculation. Findings always show their sample size.
5. Not medical advice: a red day is "below your baseline", never a diagnosis.

### Suggested Decisions (confirm before /plan)

- [x] Both a dashboard and Claude access, over one shared data layer
- [x] Claude available everywhere, phone included, so it will eventually be hosted
- [x] Claude can save tags and findings
- [ ] The daily table is the shared data model
- [ ] Order: local data layer → local MCP → hosted (storage, MCP, sync, dashboard)
- [ ] Dashboard v1 scope: Today + Baseline trends + findings
- [ ] Take Today and Baseline trends to Claude Design, along with the real `data/` files

### Open Questions (for /plan)

- **Storage:** SQLite locally, then hosted Postgres (Supabase, which you already use)? Or Postgres from the start, so there's only one schema?
- **Hosting:** Vercel for the dashboard and MCP routes? Sync with a scheduled job, WHOOP v2 webhooks, or both? Where do tokens live, and how is a single refresh enforced?
- **Login:** how the dashboard login and the claude.ai connector's OAuth work for one user. Can the Trip Fairy setup be reused?
- **MCP tools:** a fixed set of tools, or also a read-only query tool so Claude can run its own analyses?
- **Tags:** a fixed list, free text, or a fixed list plus free notes?
- **Sleep need:** confirm how WHOOP defines it before any view uses it.
- **History:** is the WHOOP about 2 months old, or is the API only returning recent data? This decides when direction C is viable.
- **Privacy policy:** update `docs/privacy.html` (hosted storage, Claude access, tags) before going online.

### Next Steps

`/plan` should turn this into milestones: daily table + `CLAUDE.md` → tags/findings storage → local MCP server → Claude Design pass on Today and Baseline trends → hosted storage and sync → hosted MCP connector → hosted dashboard → privacy policy update.
