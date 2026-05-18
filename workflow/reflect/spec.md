# Phase: Reflect

## Overview
A retrospective phase that captures what happened, surfaces observations the user may not have thought to record, updates memory with lessons and decisions, and ends with forward-looking recommendations. Weighted toward the retrospective but always closes with next steps.

Can be invoked at any point: end of session, end of a milestone, after a feature is complete, or at project close. Automatically suggested at session end and milestone completions — never forced.

---

## Trigger
User invokes `/reflect` manually. Auto-suggested (not forced) by:
- `/build` at milestone completion
- Natural session-end signals (user says "done for now", "signing off", "that's enough for today")

---

## Input

**Reads to build context before reflecting:**
- `docs/plan.md` — what was intended
- `docs/brainstorm.md` — original intent and direction
- `docs/review.md` — findings, what was fixed, what was deferred
- `docs/reflect.md` — prior reflections (for continuity, patterns across sessions)
- Session history — what was actually done this session
- Current code state — what exists now vs. what existed before

---

## Depth Levels

### Simple (user requests "quick reflect" or "brief reflection")
- What was accomplished?
- What worked, what didn't?
- What's next?
- Minimal doc output — a few bullet points appended to `docs/reflect.md`

### Default (middle)
- Actively surfaces observations from the session — things the user might not have captured themselves
- Asks a small number of targeted questions to draw out lessons
- Documents findings, decisions, and patterns
- Closes with prioritized next steps

### Deep (user requests "deep reflect" or "thorough reflection")
- Challenges decisions made during the session — not just captures them
- Explores patterns across this session and prior reflections
- Considers whether the plan still reflects reality
- Evaluates process: did the workflow phases serve the work well?
- May suggest updates to multiple artifacts (plan, CLAUDE.md, memory, brainstorm)

---

## Process (Default Depth)

1. **Synthesize the session** — read context, build a picture of what happened without asking
2. **Surface observations** — identify 2-4 things worth noting that the user may not have raised:
   - Decisions that worked out well (patterns to repeat)
   - Things that were harder than expected
   - Deviations from the plan and whether they were improvements or problems
   - Anything that surprised or should be captured for future sessions
3. **Ask targeted questions** — 2-3 focused questions to draw out what only the user knows:
   - "Did anything feel off that we didn't stop to address?"
   - "Is there anything you'd approach differently next time?"
   - "Any decisions from today you're not fully confident in?"
4. **Capture** — synthesize into the reflection doc
5. **Forward motion** — end with recommended next steps and suggested next phase

---

## What It Produces

### Always: `docs/reflect.md` (append, never overwrite)

```
# Reflect — [Session / Milestone / Feature / Project]
Date: YYYY-MM-DD
Type: Session | Milestone | Feature | Project Close
Phase context: [what phases were run this session]

## Accomplished
[What was built, fixed, or decided this session]

## What Worked
[Patterns, approaches, or decisions that went well — worth repeating]

## What Didn't Work
[Friction points, wrong turns, or things to approach differently]

## Decisions Reviewed
[Significant decisions made — do they still feel right in retrospect?]

## Lessons Learned
[Technical, process, or domain knowledge gained]

## Surprises
[Anything unexpected — scope, complexity, behavior, feedback]

## Memory Updates
[What was captured to memory this session — or what should be]

## Next Steps
[Prioritized recommendations for what comes next]

## Suggested Next Phase
[/build | /review | /iterate | /ship | /brainstorm | /plan — whichever fits]
```

### On Suggestion (not default):
- **Memory files** — update `~/.claude/projects/.../memory/` with lessons, patterns, feedback
- **`CLAUDE.md`** — add new project conventions discovered during the work
- **`docs/plan.md`** — flag if the plan needs updating based on what was learned

---

## Forward Motion Section

Always end with:
- **Next steps** — prioritized list of what should happen next, drawn from open questions, deferred findings, and plan milestones
- **Suggested next phase** — which command makes sense to run next and why
- **Confidence check** — note any outstanding decisions that feel shaky and may need revisiting

---

## Auto-Suggestion Behavior

**At milestone completion (from `/build`):**
> "Milestone complete. Consider running `/reflect` to capture what was learned before moving forward."

**At session-end signals:**
> "Looks like you're wrapping up. Running `/reflect` before closing will capture today's progress and set up the next session."

Both are suggestions only. User can dismiss and move on.

---

## Behavior Notes

- **Read before asking** — synthesize from available context first; don't ask the user to recap what's already visible
- **Surface, don't just document** — actively identify what's worth capturing; don't just ask "what worked?"
- **Depth is user-directed** — default to the middle; go simpler or deeper when asked
- **Retrospective-weighted** — the bulk of the reflection looks backward; next steps are a closing section, not the focus
- **Prior reflections inform this one** — check `docs/reflect.md` for patterns across sessions; note if the same friction keeps appearing
- **Memory updates are suggested, not automatic** — flag what should go to memory; don't write it without the user knowing
- **Project close reflections go deeper by default** — a session-end reflect is lighter; a project-close reflect should be more thorough
