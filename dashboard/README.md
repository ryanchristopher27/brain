# dashboard — local agent control server

A FastAPI app that serves the `web/` frontend, aggregates live events, and (later) lets you
act on agents. It is the central hub: it **subscribes** to the voice core and re-broadcasts,
so voice stays unchanged and standalone.

```
  voice daemon (8765) ──▶ dashboard (8766) ──▶ web/ frontend
   background runner  ──▶   hub · API · (D4 actions) · (D6 registry)
```

## Security (D1, mandatory)
- Binds `127.0.0.1` only.
- **Host check** on every request (DNS-rebinding protection) — non-localhost `Host` → 403.
- **Origin check** — a present, foreign `Origin` → 403.
- **Token**: a random token (`~/.claude/brain-dashboard/token`, mode 600) is issued via
  `/api/config` (same-origin readable only) and required on the `/ws` upgrade. Future action
  endpoints (D4) will require it too. Cross-origin pages can't read the token (no CORS headers).

## Run
```sh
./voice/.venv/bin/python -m dashboard.server            # http://127.0.0.1:8766
./voice/.venv/bin/python -m dashboard.server --reload   # dev: auto-restart on edits to dashboard/
```
Use `--reload` while developing so backend edits pick up without a manual restart. (Agent runs
spawned before a reload are orphaned — fine for dev.)
Open the URL in a browser. Optionally run `python -m voice.daemon` too — the dashboard picks
up the voice session automatically (the orb reflects it). Without voice, the dashboard still
serves; the voice panel just shows disconnected.

## Endpoints (D1)
| Route | Purpose |
|-------|---------|
| `GET /` | the `web/` frontend |
| `GET /api/config` | `{token, voice_connected}` (same-origin) |
| `GET /api/health` | `{ok, voice_connected}` |
| `WS  /ws?token=…` | live event hub (voice events re-broadcast) |

## Projects registry & status
Which projects brain tracks lives in `~/.claude/brain/projects.json` — a JSON array of
`{name, root_path, status}`. Each project carries a **declared lifecycle status**
(`active · paused · blocked · shipped · archived`) *orthogonal* to its auto-detected
workflow phase (`_detect_phase`). With no registry file, the system falls back to
auto-discovering sibling repos that use the brain workflow.

Manage it with the CLI (no server needed):
```sh
python -m dashboard.projects_cli ls
python -m dashboard.projects_cli add   --name my-proj --path .          # register cwd
python -m dashboard.projects_cli status --name my-proj --to shipped
python -m dashboard.projects_cli vault                                  # (re)build the Obsidian board
```
`/api/projects` returns each project enriched with status + phase + task counts;
`POST /api/projects/{name}/status` sets status; the web pipeline shows a status chip per card.

### Obsidian projects vault
`dashboard/projects_vault.py` materializes one markdown card per project (declared status,
phase, task counts) into a standalone vault (`~/Desktop/Code/brain-projects-vault`) with a
Bases board tabbed by status. Regenerable; anything under a card's `## Notes` heading is
preserved across regenerations. Single source of truth stays `projects.json`.

### Automatic updates (SessionStart hook)
`universal/hooks/scripts/session-start-project-sync.sh` runs `projects_cli sync` on every
Claude Code SessionStart (installed into the **global** `~/.claude/settings.json` by
`install.sh`, so it fires in *any* project). It auto-registers the current project if it's a
real, untracked one — git repo, brain-workflow repo, or one with a build manifest — and
refreshes the Obsidian vault. The web dashboard needs no refresh: phase + task counts are
computed live on each request. So: open Claude in a project → it appears/updates on its own.
Fire-and-forget and never blocks a session. Statuses stay whatever you declared.

## Artifact archive
Brain is the canonical home for every project's **markdown** artifacts. `dashboard/artifacts.py`
copies each project's `docs/*.md`, `.brain/tasks/*.md`, its session summaries (extracted from
`updates/queue.md`), and any `mark`ed deliverables into `brain/artifacts/<project>/`, with a
per-project `INDEX.md` and a top-level catalog `README.md`. Code and working files stay in each
repo; these are brain's copies of record.

Runs automatically inside the SessionStart sync (`projects.sync_cwd` → `artifacts.sync_project`),
so opening any project refreshes its archive. Manual:
```sh
python -m dashboard.artifacts_cli sync --all                 # backfill/refresh every project
python -m dashboard.artifacts_cli mark --project P --file docs/spec.md --note "…"
```
Copies mirror their source (a deleted/renamed original is pruned on next sync). The archive is
plain markdown, so pointing an Obsidian vault at `brain/artifacts/` gives a browsable library.

## Dev dashboard (per-project status + resources)
One page per project answering "how is the app doing / where are its resources" —
`web/devdash.html` (project picker + `?project=<name>` deep link), backed by
`GET /api/devdash/{name}`.

**Resources** — each project declares its external services at
`<project_root>/.brain/resources.json` (schema + loader: `dashboard/resources.py`). No
file yet? The dashboard falls back to a brain-side seed at
`dashboard/seed/<project>.resources.json`. Propose entries for a project with:
```sh
python -m dashboard.resources_cli seed --path /path/to/project            # prints JSON
python -m dashboard.resources_cli seed --path . --out .brain/resources.json
python -m dashboard.resources_cli validate --path .brain/resources.json
```
`seed` only scans (package.json deps, `.env*` names, `vercel.json`, known hostnames in
source) and proposes — always review before trusting it.

**Status** (`dashboard/devstatus.py`), each source optional and failing soft:
- **Git** — branch, last commits, uncommitted count, ahead/behind upstream. No network.
- **Tracker** — task counts by status + what's in review. Reuses `dashboard/tracker.py`.
- **Hosting (Vercel)** — latest production deployment, via the Vercel REST API. Needs a
  token (Vercel tokens aren't read-only — scope it to your team and give it an expiry):
  create one at https://vercel.com/account/tokens, then set `VERCEL_TOKEN`
  (env var) or add it to `~/.claude/brain-dashboard/secrets.json` (flat JSON, mode 600).
- **Database (Supabase)** — project status/region via the Management API. Needs a personal
  access token — it has full access to your Supabase account, so keep it local and give it
  an expiry: https://supabase.com/dashboard/account/tokens → `SUPABASE_ACCESS_TOKEN` (same
  two places).
- **Uptime** — an unauthenticated GET against the project's declared production URL.
- Remote calls (Vercel/Supabase/uptime) are cached 120s in-process. No token is ever
  logged or returned in an API response; `dashboard/secrets_store.py` only reads tokens,
  never writes them.

No Vercel/Supabase token exists yet in this environment — until one is set, those cards
render a clean "not configured" state naming the exact env var and a link to create it.

## Status → milestones
- **D1 ✅** server + Host/Origin/token security + voice-subscribe proxy
- **D3** read panels: roster · jobs · health · activity
- **D2** orb absorbed as the active-session panel
- **D7** work-pipeline board
- **D8 ✅** project registry + declared status + Obsidian projects vault
