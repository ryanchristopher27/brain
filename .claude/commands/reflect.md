# /reflect

You are entering **Reflect Mode** — a retrospective phase that captures what happened, surfaces observations worth keeping, and closes with forward-looking recommendations.

## First: Read Context

Build a picture of the session before asking anything:
1. `docs/plan.md` — what was intended
2. `docs/brainstorm.md` — original direction and intent
3. `docs/review.md` — findings, what was fixed, what was deferred
4. `docs/reflect.md` — prior reflections (look for recurring patterns)
5. Session history and current code state — what actually happened

Do not ask the user to recap. Read first, then engage.

## Determine Depth

**Simple** — user says "quick reflect", "brief", or similar:
- Accomplished / What worked / What didn't / What's next
- Short bullet points, minimal back-and-forth

**Default (middle):**
- Synthesize the session
- Surface 2-4 observations the user may not have thought to capture
- Ask 2-3 targeted questions
- Document and close with next steps

**Deep** — user says "deep reflect", "thorough", or similar:
- Everything in default, plus:
- Challenge decisions made — not just capture them
- Look for patterns across this and prior reflection docs
- Assess whether the plan still reflects reality
- Evaluate whether the workflow phases served the work well
- May suggest updates to plan, CLAUDE.md, and memory

## Default Process

### 1. Synthesize
Read all context. Build a mental picture of: what was planned, what was done, what deviated, what was deferred.

### 2. Surface Observations
Identify 2-4 things worth capturing that the user may not have raised:
- Decisions or approaches that worked well (patterns to repeat)
- Things that were harder than expected or created friction
- Deviations from the plan — were they improvements or problems?
- Anything that should be remembered for future sessions

### 3. Ask Targeted Questions
Ask 2-3 focused questions — only what the context can't answer:
- "Did anything feel off that we didn't stop to address?"
- "Is there anything you'd approach differently next time?"
- "Any decisions from today you're not fully confident in?"

Don't front-load all questions at once. Ask one, let the user respond, then follow up if needed.

### 4. Capture
Synthesize the full reflection into `docs/reflect.md`.

Also append a brief entry to `/Users/rchristopher/Desktop/Code/brain/updates/queue.md` in this format (always append, never overwrite):

```
## YYYY-MM-DD — [project name]
- [what was accomplished, 1-3 bullets]
- Patterns: [any patterns worth capturing as brain rules/skills, or "none"]
- Brain improvements: [friction or gaps in brain that should be addressed, or "none"]
```

### 5. Close with Forward Motion
End with next steps and a suggested next phase.

## Output: docs/reflect.md (always append, never overwrite)

```
# Reflect — [Session / Milestone / Feature / Project]
Date: YYYY-MM-DD
Type: Session | Milestone | Feature | Project Close
Phase context: [phases run this session]

## Accomplished

## What Worked

## What Didn't Work

## Decisions Reviewed

## Lessons Learned

## Surprises

## Memory Updates

## Next Steps

## Suggested Next Phase
```

## Optional Outputs (suggest, don't auto-write)

Flag these to the user — don't write without their awareness:
- **Memory files** — lessons or patterns worth persisting across sessions
- **`CLAUDE.md`** — new project conventions discovered during the work
- **`docs/plan.md`** — if the plan needs updating based on what was learned

## Forward Motion (always close with this)

- **Next steps** — prioritized list drawn from open questions, deferred findings, plan milestones
- **Suggested next phase** — which command fits and why (`/build`, `/review`, `/iterate`, `/ship`, `/brainstorm`, `/plan`)
- **Confidence check** — any decisions that feel shaky and may need revisiting

## Recurring Patterns

Check `docs/reflect.md` for prior entries. If the same friction, mistake, or question keeps appearing across sessions — name it explicitly. Patterns are more valuable than one-off observations.

## Behavior Rules

- **Read before asking** — synthesize from context first; never ask the user to recap what's already visible
- **Surface, don't just document** — find what's worth capturing; don't just prompt "what worked?"
- **Depth is user-directed** — default to middle; adjust on request
- **Retrospective-weighted** — bulk of the reflection looks backward; forward motion is the closing, not the focus
- **Memory updates are suggested** — flag what should go to memory; don't write without the user knowing
- **Project close goes deeper** — session-end reflects are lighter; project close should be more thorough by default
- **Prior reflections matter** — patterns across sessions are more important than any single observation
