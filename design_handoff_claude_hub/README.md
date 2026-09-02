# Handoff: Claude Hub (account dashboard + command console)

## Overview
A single-user hub for managing everything a person does with Claude: the projects they
have going, the artifacts those projects produced, a kanban board of tasks, an
orchestrator/worker agent pipeline with a voice command dock (Whisper Flow), usage and
spend analytics, and connector health. It is a desktop-first, dense, dark "instrument
panel" — a left nav rail plus one scrolling content pane per view.

## About the Design Files
The file in this bundle (\`Claude Hub.dc.html\`) is a **design reference created in HTML**.
It is a prototype showing intended look and behavior — not production code to copy.
The task is to **recreate these designs in the target codebase's existing environment**
(React, Vue, SwiftUI, native, whatever is already there) using its established patterns,
component library, and styling approach. If no environment exists yet, pick the most
appropriate framework and implement the designs there.

The prototype uses a streaming template runtime (\`support.js\`, inline styles only). Do
not port that runtime. Read the markup for structure and exact values; re-express it in
the target stack. All data in the prototype is hardcoded sample data.

## Fidelity
**High fidelity.** Colors, type, spacing, radii, and interaction states are final and
should be matched. Sample content is illustrative — replace with real data.

## Screens / Views

### Global chrome
- **Root**: \`display: flex; height: 100vh; min-height: 760px\`. Background \`#100F0D\`,
  text \`#E8E4DC\`, font Archivo 14px, \`letter-spacing: -0.01em\`. Designed at 1440×900.
- **Left rail**: fixed \`232px\`, background \`#141310\`, right border \`1px solid #262320\`,
  flex column. Contents top to bottom:
  1. Brand: 22px accent square (radius 5px) + "CLAUDE HUB" in JetBrains Mono 12px/700,
     \`letter-spacing: 0.14em\`. Padding \`20px 18px 16px\`.
  2. Account card: \`#191714\`, border \`1px solid #262320\`, radius 8px, padding
     \`10px 11px\`. Line 1: workspace name, 12.5px/600. Line 2: "Max plan · 4 seats",
     Mono 10.5px, \`#8B857A\`.
  3. Nav: section labels in Mono 9.5px, \`letter-spacing: 0.16em\`, \`#6E6860\`, padding
     \`14px 8px 6px\` — WORKSPACE (Overview, Projects, Board, Artifacts), TOOLS
     (Command, Connectors), ACCOUNT (Usage). Items: full-width buttons, padding
     \`8px 9px\`, radius 7px, 13px/500, 10px gap, leading 6px square dot (radius 2px).
     Idle: transparent bg, \`#A9A398\` text, \`#3A352E\` dot. Active: bg \`#221F1A\`,
     text \`#F2EEE6\`, dot = accent. Hover: bg \`#201E1A\`. Trailing meta count in Mono
     10px \`#6E6860\`.
  4. Footer: top border \`#262320\`, padding \`14px 16px 16px\`. "WEEKLY LIMIT" / "62%"
     row in Mono 10px \`#8B857A\`, then a 5px track (\`#262320\`, radius 3px) filled to
     62% with accent. Below: 6px green dot (\`#6B9E72\`) + "Whisper Flow connected".
- **Header**: bottom border \`#262320\`, background \`#141310\`, padding \`18px 26px 16px\`,
  items aligned to baseline. Left: h1 21px/600 \`letter-spacing: -0.02em\` + subtitle
  12.5px \`#8B857A\` (per-view copy below). Right: search field (border \`1px solid
  #262320\`, bg \`#191714\`, radius 7px, padding \`7px 11px\`, width 250px, leading Mono
  "/" hint, placeholder "Search projects, chats, artifacts") and a primary button
  "Talk to Claude Code" (accent bg, \`#F4F0FF\` text, radius 7px, padding \`8px 14px\`,
  12.5px/600, hover \`brightness(1.18)\`) which navigates to Command and opens the
  transcript drawer.
- **Content pane**: single scroll container, padding \`var(--pad) 26px 34px\` (\`--pad\` =
  20px).

Card baseline used everywhere: background \`#17150F\`, border \`1px solid #262320\`,
radius 10px; hover border \`#3A352E\` (or \`#4A4258\` on interactive/agent cards).
Table baseline: header row bg \`#191714\`, bottom border \`#262320\`, Mono 9.5px
\`letter-spacing: 0.12em\` \`#8B857A\`, padding \`10px 18px\`; body rows padding
\`12–13px 18px\`, divider \`1px solid #201E1A\`, row hover \`#1C1A16\`.

### 1. Overview — "Tuesday, 31 August · 6 active projects, 2 sessions running"
Purpose: land, see today's volume, resume work.
- Four stat tiles, \`grid-template-columns: repeat(4, 1fr)\`, gap 12px, padding
  \`15px 16px 14px\`, background \`#17150F\`. Label Mono 9.5px \`0.14em\` \`#8B857A\`;
  value Mono 27px/600 \`letter-spacing: -0.03em\`; delta 11.5px (green \`#6B9E72\` when
  positive, else \`#8B857A\`). Content: TOKENS TODAY 1.24M / +18% vs. yesterday;
  SPEND TODAY $18.40 / $214 this period (falls back to MESSAGES TODAY 312 when the
  spend flag is off); ACTIVE PROJECTS 6 / 2 sessions running; VOICE MINUTES 47 /
  Whisper Flow, this week.
- "Pick up where you left off" (13px/600) + "3 OPEN SESSIONS" (Mono 10px \`#6E6860\`),
  then three cards (\`repeat(3, 1fr)\`, gap 12): project dot + name 13px/600 + relative
  time; snippet 12.5px \`#A9A398\` line-height 1.5 \`text-wrap: pretty\`; Resume button
  (border \`#3A352E\`, bg \`#201E1A\`, radius 6px, padding \`6px 11px\`, 11.5px/600) +
  surface label in Mono 10.5px.
- Two-column row \`1.4fr 1fr\`, gap 12:
  - "Tokens, last 14 days" + "PEAK 2.1M". 14 bars in a 132px-tall flex row, gap 6px,
    each \`flex: 1\`, radius \`3px 3px 0 0\`; today's bar = accent, recent \`#4A443C\`,
    older \`#38332C\`; hover \`brightness(1.3)\`. Day number under each in Mono 8.5px
    \`#605B54\`. Heights (% of 132px): 42 55 38 61 72 34 29 66 81 94 58 47 70 62.
  - "Recent artifacts": rows with a 30×24 striped thumbnail (repeating-linear-gradient
    135deg \`#201E1A\` 0–4px / \`#262320\` 4–8px, border \`#302C27\`, radius 4px), name
    12.5px/500 ellipsis, Mono 9.5px "KIND · PROJECT", trailing relative time.

### 2. Projects — "Everything you have going, across chat and Claude Code"
Filter chips row (Mono 10.5px, radius 20px, border \`#2E2B27\`, bg \`#191714\`,
\`#A9A398\`): All projects, Has Claude Code, Touched this week, Archived.
Table columns \`2.2fr 1fr 1.5fr 0.7fr 0.9fr 1fr 0.9fr\`: PROJECT (7px project dot +
13px/600 name), KIND, REPO (Mono 11px), ARTIF., TOKENS, LAST ACTIVE, STATUS pill
(Mono 9.5px, radius 4px, padding \`4px 8px\`) — RUNNING \`#1E2C21\`/\`#6B9E72\`,
ACTIVE \`#221F1A\`/\`#C7C1B6\`, IDLE \`#1C1A16\`/\`#7E7870\`, ARCHIVED \`#1C1A16\`/\`#605B54\`.
Rows are clickable (route to project detail — not designed yet).

### 3. Board — "Tasks across every project · drag to move, or say 'move it to done'"
Project filter chips (selected: bg \`#241E33\`, text \`#E4DAFF\`, dot accent) + right-aligned
"N TASKS · N BLOCKED ON YOU" in Mono 10px. Four columns \`repeat(4, 1fr)\`, gap 12,
\`align-items: start\`, min-height 300px: BACKLOG (\`#4A4258\`), IN PROGRESS (accent),
WAITING ON YOU (\`#C4A05F\`), DONE (\`#6B9E72\`). Column header: 7px status dot + Mono
10px \`0.13em\` \`#C7C1B6\` + count, bottom border \`#201E1A\`. Cards: bg \`#1C1A16\`,
border \`#2A2723\`, radius 8px, padding \`11px 12px 10px\`, \`cursor: grab\`, hover
border \`#4A4258\` bg \`#201E1A\`. Card contents: project dot + project name (Mono 9.5px)
+ task id right-aligned; title 12.5px/500 line-height 1.45; footer tag pill (NEEDS YOU
\`#2C2038\`/\`#B79BEA\`, DONE \`#1E2C21\`/\`#6B9E72\`, else \`#221F1A\`/\`#8B857A\`) + meta.
Empty column: dashed \`#2A2723\` placeholder reading "nothing here".
Drag-and-drop between columns is implied by \`cursor: grab\` and the subtitle; it is not
implemented in the prototype — implement real DnD with optimistic reordering.

### 4. Artifacts — "41 artifacts · decks, docs, prototypes and components"
\`grid-template-columns: repeat(auto-fill, minmax(232px, 1fr))\`, gap 14. Card: 116px
striped preview area (repeating-linear-gradient 135deg \`#1C1A16\` 0–6px / \`#221F1B\`
6–12px) with a centered Mono 9.5px \`0.12em\` \`#6E6860\` slot label ("SLIDE 1
THUMBNAIL", "PAGE 1 THUMBNAIL", "FIRST SCREEN", …) — **these are placeholders for real
rendered thumbnails**. Body: name 13px/600 ellipsis; Mono 10px kind + relative time
row; project dot + project 11.5px + "v{n}" right-aligned.

### 5. Command — "Orchestrator moving work through brainstorm, plan, build, review, ship · talk to it below"
The merged agent + voice surface. Three stacked regions:

**a. Orchestrator panel.** Border \`1px solid #3B3153\`, radius 12px, background
\`linear-gradient(180deg, #201A2E 0%, #1A1622 100%)\`, padding \`16px 18px 15px\`,
shadow \`0 0 0 1px #1A1524, 0 12px 30px #0C0A14\`.
- 30px "nucleus" avatar (see Living nucleus below).
- "Orchestrator" 14.5px/600; Mono 10px \`#9C8FBE\` "opus · planning and dispatch ·
  6m 41s uptime".
- Right: three stats (label Mono 9px \`0.14em\` \`#8378A0\`, value Mono 17px/600):
  IN PIPELINE 8, SHIPPED TODAY 9, ESCALATED 1 (\`#C4A05F\`).
- Divider \`1px solid #2C2440\`, then \`1.15fr 1fr\`: CURRENT DIRECTIVE (12.5px
  \`#DED6F2\`, line-height 1.55) and DISPATCH LOG (Mono 10.5px lines; dispatch
  \`→\` \`#B79BEA\`, escalation \`←\` \`#C4A05F\`, ship \`✓\` \`#6B9E72\`).

**b. Pipeline.** "Pipeline" heading + "5 STAGES · 8 WORKERS · 1 ESCALATED TO YOU".
\`grid-template-columns: repeat(5, minmax(0, 1fr))\`, gap 10, \`align-items: start\`.
Stages in order: BRAINSTORM (\`#7B8CC4\`), PLAN (accent), BUILD (accent), REVIEW
(\`#C4A05F\`), SHIP (\`#6B9E72\`). Each column header is a 19px-tall relative block with:
a 9px node circle (\`border: 1px solid stageColor\`, fill \`#1A1622\`, green fill on the
final stage) at \`top: 1px; left: 0\`, and a 1px \`#3B3153\` rail at \`top: 5px\` running
from the node into the next column (\`left: 5px\` on the first, \`left/right: -10px\`
mid-chain so it crosses the gap, zero-width on the last) — together the rails read as
one continuous process line. Below: stage name Mono 9.5px \`0.14em\` and meta Mono 9px
\`#605B54\` ("avg 11m · 2 in flight", "1 escalated to you", "9 shipped today").
Worker cards (gap 9): radius 9px, padding \`11px 12px 12px\`, flex column gap 8,
\`min-width: 0\` on text rows, step line \`overflow-wrap: anywhere\` (the 5-up grid must
not inflate past its container). Contents: 6px glowing state dot + worker name
(Mono 11px/700, ellipsis); project dot + project (11px, ellipsis) + task id right;
current step in Mono 10.5px \`#C7C1B6\` (verb-first: "edit  jobs/reconcile.ts — …");
3px progress track (\`#232019\`) filled with the state color; state pill (Mono 9px) +
elapsed right-aligned. State colors: EXPLORING \`#241E33\`/\`#B79BEA\`/dot \`#7B8CC4\`,
RUNNING \`#241E33\`/\`#B79BEA\`/dot accent, QUEUED \`#1C1A16\`/\`#8B857A\`/dot \`#4A4258\`,
NEEDS YOU \`#2E2818\`/\`#C4A05F\`/dot \`#C4A05F\`, RETRYING \`#2E1D1C\`/\`#B0736F\`/dot
\`#B0736F\`, SHIPPED \`#1E2C21\`/\`#6B9E72\`/dot \`#6B9E72\`. Empty stage: dashed "idle".

**c. Handoffs today** table, columns \`0.7fr 1.5fr 1.1fr 1.6fr 2fr\`: TIME (Mono 10.5px),
WORKER (Mono 11.5px), PROJECT (dot + name), HANDOFF ("build → review", Mono 10.5px
\`#B79BEA\`), RESULT (12px \`#A9A398\`, ellipsis).

**d. Transcript drawer (collapsible, closed by default).** \`grid-template-columns:
1fr 1.15fr\`, gap 12, height 320px, margin-top 26px.
- Left: TRANSCRIPT panel. Header: mic dot (accent while recording, else \`#3A352E\`) +
  Mono 10px label + RECORDING/IDLE right. Body: 15px/1.65 \`#DDD8CE\` dictated text with
  an accent caret \`▍\` while live, plus a Mono 11px \`#605B54\` hint line ("Listening —
  240ms latency, en-US" / "Sent to Claude Code · N words" / "Nothing captured yet…").
  Footer: example command chips \`"run the tests"\`, \`"undo that"\`, \`"switch to ledger"\`.
- Right: CLAUDE CODE panel, bg \`#131210\`, header "~/dev/ledger" + "sonnet · 4 tools"
  (\`#6B9E72\`). Body Mono 11.5px/1.75 lines revealed one at a time, colors: command
  \`#9C7BF0\`, reads \`#7E7870\`, edits \`#6B9E72\`, prose \`#DDD8CE\`, idle \`#4E4A44\`.

**e. Sticky mic dock.** \`position: sticky; bottom: 0\`, margin-top 16, z-index 3,
shadow \`0 -16px 26px #100F0D\`, border \`1px solid #2E2B27\`, radius 10px, bg \`#191714\`,
padding \`13px 18px\`, flex row gap 18, always visible on this view. Contents:
1. 58px nucleus mic button (below).
2. Flexible 44px "starfield" strip: radius 8px, background
   \`radial-gradient(120% 180% at 8% 50%, #221A3A 0%, #17131F 45%, #141210 100%)\`, a
   1px horizontal axis line \`linear-gradient(90deg, #322C48, transparent)\` at 50%, and
   30 equal columns each holding one dot. Per dot when live: vertical position
   \`top: 50 - (level - 0.5) * 78\`%, size \`2.5 + level*4.5\` px, glow blur
   \`3 + level*7\` px, opacity \`0.45 + level*0.55\`, color accent with every 5th dot
   \`#D8CCFF\`. Idle: flat 2px dots, \`#4A4258\`, opacity 0.3, gently staggered.
   Bottom-left ticker (Mono 9.5px \`#9C8FBE\`, single line, ellipsis) shows the **last
   ~9 dictated words while speaking** — the drawer must NOT auto-open when dictation
   starts (that yanked the user to the bottom of the page); after stopping it reads
   "sent to orchestrator · N words · open the transcript to read it back".
3. Right: Mono 10px \`0.12em\` \`#8B857A\` "WHISPER FLOW · LISTENING/READY" and
   "Hold · Space to talk" (11.5px \`#A9A398\`).
4. Drawer toggle button: border \`#3B3153\`, bg \`#241E33\`, text \`#C9B8F2\`, radius 6px,
   padding \`8px 12px\`, Mono 9.5px — "TRANSCRIPT ▴" / "HIDE ▾", hover bg \`#2C2440\`.

**Living nucleus (mic button, 58px; orchestrator avatar, 30px).** Layers, back to front:
1. Two ripple rings: \`inset: -6px\`, 1px accent-violet border, \`om-ripple\` 2.6s
   ease-out infinite, second delayed 1.3s. Opacity 0 when idle, 1 when live.
2. Rotating halo: \`inset: -4px\`, conic gradient (transparent → \`#8B6BE8\` 90° →
   transparent 200° → \`#4A2E8F\` 300°), \`om-spin\` 5.5s linear, \`blur(4px)\`, opacity
   0.18 idle / 0.95 live.
3. Membrane: \`radial-gradient(circle at 36% 28%, #6E52B8 0%, #402C78 32%, #241748 62%,
   #140E24 100%)\`, \`inset 0 0 20px #0C0818\` plus outer glow \`0 0 8px\` idle /
   \`0 0 26px\` live in \`#6D4AC4\`, animated by \`om-wobble\` 7s ease-in-out infinite
   (morphing border-radius + ±3° rotation + 0.985–1.02 scale) so the shape breathes
   rather than sitting as a perfect circle.
4. Cytoplasm swirl: \`inset: 5px\`, conic gradient with \`#9C7BF0\`, \`om-spin-slow\` 9s,
   \`blur(1px)\`, opacity 0.22 idle / 0.7 live.
5. Two orbiting satellites: wrappers at \`inset: 0\` (\`om-spin\` 4.2s) and \`inset: 6px\`
   (\`om-spin-slow\` 6.4s), each with a 3–4px dot (\`#E4DAFF\` / \`#B79BEA\`, 5–6px glow).
   Opacity 0.4 idle / 1 live.
6. Nucleus: \`inset: 12px\` wrapper carrying the **level-reactive** transform
   \`scale(1 + avgLevel * 0.22)\`; inside, a radial white→\`#E4DAFF\`→\`#9C7BF0\` core
   running \`om-nucleus\` 1.9s (scale 0.94–1.12 with sub-pixel drift). Keep the
   audio-reactive scale on the wrapper — a keyframed transform on the same element
   would override it.
7. Nucleolus: \`inset: 17px\`, \`#F6F1FF\`, \`blur(2px)\`, \`om-cilia\` 2.3s opacity pulse.

### 6. Connectors — "MCP servers and integrations available to every session"
\`repeat(auto-fill, minmax(268px, 1fr))\`, gap 12. Card: 8px state dot + name 13px/600 +
right-aligned state in Mono 9.5px tinted to match (CONNECTED \`#6B9E72\`, DEGRADED
\`#C4A05F\`, NEEDS AUTH \`#B0736F\`); note 12px \`#8B857A\` line-height 1.5; footer Mono
10px \`#605B54\` call volume. Items: Whisper Flow, GitHub, Filesystem, Linear,
Postgres (staging), Notion.

### 7. Usage — "Current billing period · 1–31 August"
- Four tiles (same tile spec, value Mono 25px): TOKENS, PERIOD 13.1M / 68% of weekly
  allowance; SPEND, PERIOD $214 / Projected $268 by 31 Aug (or SESSIONS 186 when the
  spend flag is off); CACHE HIT RATE 73% / Saved an estimated $91; VOICE MINUTES 184.
- Two panels \`1fr 1fr\`: "By surface" (Claude Code 7.4M 100%, Chat 3.9M 53%, Voice
  console 1.2M 16%, API / scripts 0.6M 8%) and "By model" (Sonnet 9.2M 100%, Opus 3.1M
  34%, Haiku 0.8M 9%). Each row: name 12px + Mono value \`#8B857A\`, then a 6px track
  (\`#232019\`, radius 3px) filled to \`pct\` with accent / \`#7B8CC4\` / \`#6B9E72\` /
  \`#8A8578\`. Bars are normalized to the largest row, not to 100% of total.
- Per-project table, columns \`2fr 1fr 1fr 1fr 1fr\`: PROJECT, INPUT, OUTPUT,
  CACHE READ, COST (header switches to SHARE and values to percentages when the spend
  flag is off).

## Interactions & Behavior
- **Nav**: click switches the content view; single scroll container per view; scroll
  position resets. Active item styling as above.
- **"Talk to Claude Code"** (header), **Resume** (overview session cards) and
  **TAKE OVER** affordances all route to Command and open the transcript drawer.
- **Mic**: click the nucleus, or press Space while on Command (ignored when focus is in
  an input/textarea, and on \`repeat\` events; \`preventDefault\` so the page doesn't
  scroll). In the prototype dictation is simulated: a ~110ms tick randomizes the 30
  waveform levels and appends one word every other tick; when the script runs out the
  mic stops itself, then Claude Code output lines reveal one per 320ms. In production:
  stream from the real speech source; keep the same visual states (levels, caret,
  RECORDING/IDLE, ticker) and the same rule that **starting to talk never scrolls the
  page or auto-expands the drawer**.
- **Drawer**: toggled only by the TRANSCRIPT/HIDE button (and by the explicit "go to
  command" actions). Closed by default.
- **Dock**: sticky to the bottom of the Command scroll area, always reachable.
- **Board**: cards are drag targets (\`cursor: grab\`); project chips filter every column
  and update the "N TASKS · N BLOCKED ON YOU" counter.
- **Hover states**: cards raise their border to \`#3A352E\`/\`#4A4258\`; table rows go
  \`#1C1A16\`; chart bars \`brightness(1.3)\`; primary button \`brightness(1.18)\`.
- **Animations**: only the nucleus/starfield are animated (durations above). Everything
  else is static — no page transitions, no entrance animations.
- **Responsive**: desktop-first, laid out at 1440×900 and usable to ~1150px. The
  5-column pipeline is the fragile part: it needs \`minmax(0, 1fr)\` tracks and wrapping
  step text. Below ~1000px, plan to collapse the pipeline to a vertical stage list and
  the rail to a permanent icon strip. No mobile design exists yet.
- **Loading / error / empty states**: not designed. Precedents to follow — dashed
  "nothing here"/"idle" placeholders for empty columns and stages; DEGRADED and
  NEEDS AUTH connector states for failures; RETRYING worker state for a failed run.

## State Management
Prototype state (single component):
- \`view\`: 'overview' | 'projects' | 'board' | 'artifacts' | 'agents' (Command) |
  'connectors' | 'usage'.
- \`boardFilter\`: 'all' | project name.
- \`drawerOpen\`: boolean, default false.
- \`mic\`: boolean; \`spoken\`: number of words dictated; \`levels\`: number[30] (0–1);
  \`term\`: count of revealed Claude Code lines; \`tick\`: animation counter.
Timers: one interval while recording (110ms), one after stop (320ms) to reveal terminal
lines; both cleared on unmount, along with the window keydown listener.

Production data needs, by view: projects list with kind/repo/artifact count/token
usage/last-active/status; artifacts with type, version, project, thumbnail; tasks with
project, stage/column, tag, timestamps; orchestrator directive + dispatch log; workers
with stage, state, current step, progress, elapsed, model, token count; handoff events;
usage aggregates by day, surface, model, project; connector health with call volume;
live transcript + Claude Code output streams.

## Design Tokens
Colors — background \`#100F0D\`; rail/header \`#141310\`; card \`#17150F\`; raised
\`#191714\`; active/tag \`#221F1A\`; card-on-card \`#1C1A16\`; terminal \`#131210\`;
borders \`#262320\` (default), \`#201E1A\` (divider), \`#2A2723\`, \`#2E2B27\`, \`#3A352E\`
(hover), \`#4A4258\`; violet chrome \`#3B3153\`, \`#2C2440\`, \`#241E33\`, \`#201A2E\`,
\`#1A1622\`; text \`#E8E4DC\` primary, \`#DDD8CE\`, \`#C7C1B6\`, \`#A9A398\` secondary,
\`#8B857A\` muted, \`#6E6860\` / \`#605B54\` / \`#4E4A44\` faint; on-violet text
\`#DED6F2\` / \`#C9B8F2\` / \`#9C8FBE\` / \`#8378A0\`.
Accent: \`#6D4AC4\` default (user's saved value \`#5A3E7E\`; palette also offers
\`#8B5CF0\`, \`#4A5BA8\`), exposed as \`--accent\` on the root and used for the active
nav dot, primary button, today's chart bar, in-progress states, and the nucleus.
Accent tints: \`#8B6BE8\`, \`#9C7BF0\`, \`#B79BEA\`, \`#C4B0FF\`, \`#D8CCFF\`, \`#E4DAFF\`,
\`#402C78\`, \`#241748\`, \`#140E24\`.
Semantic: green \`#6B9E72\` (on \`#1E2C21\`), amber \`#C4A05F\` (on \`#2E2818\`), red
\`#B0736F\` (on \`#2E1D1C\`), blue \`#7B8CC4\`, sand \`#8A8578\`.
Project colors: Ledger \`#6B9E72\`, Atlas \`#7B8CC4\`, Fieldnotes \`#C4A05F\`, Signal
\`#B0736F\`, Loom \`#8A8578\`, Hub \`#8B6BE8\`, archived \`#5F6E7B\`.
Links: \`#9C7BF0\`, hover \`#BCA4FF\`.
Type — UI: Archivo 400/500/600/700 at 11 / 11.5 / 12 / 12.5 / 13 / 13.5 / 14.5 / 21 /
25 / 27px, tight tracking (\`-0.01em\` body, \`-0.02em\` h1, \`-0.03em\` big numerals).
Data/labels: JetBrains Mono 400/500/700 at 8.5 / 9 / 9.5 / 10 / 10.5 / 11 / 11.5 / 12 /
17 / 22 / 25 / 27px, letter-spacing 0.06–0.16em for all-caps labels.
Spacing: 3 / 5 / 7 / 9 / 10 / 12 / 14 / 16 / 18 / 20 / 26 px; grid gaps 9–14; page
padding \`20px 26px 34px\`.
Radii: 2 (dots/bars) / 4 / 5 / 6 / 7 / 8 / 9 / 10 / 12 / 20 (chips) / 50%.
Shadows: cards flat; orchestrator \`0 0 0 1px #1A1524, 0 12px 30px #0C0A14\`; dock
\`0 -16px 26px #100F0D\`; nucleus \`inset 0 0 20px #0C0818\` + accent glow.
Bars/tracks: 3px (worker), 4px, 5px (rail limit), 6px (usage) heights on \`#232019\` or
\`#262320\`.

## Tweakable props (in the prototype)
\`accent\` (color), \`density\` ('airy' | 'balanced' | 'dense' — currently only wired to
\`--pad\`), \`showSpend\` (boolean; swaps spend tiles/columns for message and share
counts), \`orgName\` (text in the rail account card). Treat \`showSpend\` as a real
product setting for accounts without billing visibility.

## Assets
None. No images, icon fonts, or SVG artwork: every visual is CSS (gradients, conic and
radial gradients, striped placeholders, dots). Artifact thumbnails and the artifact card
previews are **striped placeholders** and should be replaced with real rendered
previews. Fonts are Google Fonts (Archivo, JetBrains Mono) — swap for the codebase's
equivalents if it already has a type system.

## Files
- \`Claude Hub.dc.html\` — the full design: all seven views, the nucleus voice dock, and
  the sample data (in the \`Component\` class near the bottom of the file: \`tasks\`,
  \`script\`, \`termLines\`, \`board()\`, \`agentData()\`, \`renderVals()\`).
- \`support.js\` — prototype runtime only. Do not port.
