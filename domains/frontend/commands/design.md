# /design

<!-- Domain: frontend -->
<!-- Purpose: design and iterate production-grade frontend interfaces, backed by the frontend domain's rules, references, knowledge base, and anti-pattern detector. -->

You are running the **/design** command — the frontend domain's single design verb. It dispatches
to a subcommand and always works against the domain's rules, references, and tooling. Real working
code, committed design choices, exceptional craft. You are capable of extraordinary work;
don't hold back, and don't ship prototypes when production-grade is achievable.

## Usage

```
/design <subcommand> [target]
```

Subcommands: `craft` · `shape` · `critique` · `audit` · `polish` · `system`. If no subcommand is
given, infer one from the request (e.g. "fix the spacing" → behave as `polish`/`layout`; "review
this" → `critique`), or default to `craft`. The rest of the argument is the target.

## Resolve the domain path (do this first)

The domain's scripts and references live in the **brain repo**, not the user's project. Resolve
the path once at the start of the session, then reuse `$FE`:

```bash
FE="$(python3 -c "import os;p=os.path.realpath(os.path.expanduser('~/.claude/commands/design.md'));print(os.path.dirname(os.path.dirname(p)))" 2>/dev/null)"
# $FE is the brain frontend domain dir, e.g. /…/brain/domains/frontend
# Fallback if the above is empty (e.g. Windows copy-install): set it to your brain clone:
#   FE="$HOME/Desktop/Code/brain/domains/frontend"
```

Then scripts are `"$FE/scripts/search.py"` and `"$FE/scripts/detect.mjs"`; references are
`"$FE/references/<topic>.md"`. If `python3` or `node` is unavailable, the corresponding tool step
degrades to reference-only guidance — note it, never hard-fail.

## Setup (every invocation, before the subcommand)

1. **Identify the register** and read it — non-optional; skipping it produces generic output. Read
   `"$FE/references/register.md"`. Brand (design IS the product: landing/marketing/portfolio) vs.
   Product (design SERVES the product: app/dashboard/tool). Pick by task cue, then the surface in
   focus.
2. **Read the always-on rules:** `"$FE/rules.md"` (the priority ladder + absolute bans).
3. **Read the matching topic reference(s)** for the work from `"$FE/references/"`: typography,
   color-and-contrast, spatial-design, motion-design, interaction-design, responsive-design,
   ux-writing, charts. Non-optional for the topics your task touches.
4. **Study the existing design system** in the project — read at least one real file (tokens/theme/
   a representative component or page). Reuse what works; branch out only when the UX wins. If the
   project is brand-new with no committed colors, compose a palette in OKLCH per
   color-and-contrast.md.
5. **Query the knowledge base** when you need concrete options (a palette, font pairing, style,
   chart type):
   `python3 "$FE/scripts/search.py" "<query>" --domain <style|color|typography|chart|ux|product|google-fonts> [--stack <stack>]`

## Subcommands

| Subcommand | Intent | Tooling |
|------------|--------|---------|
| `craft`    | Shape → build a feature end-to-end at studio quality (default) | search + detector |
| `shape`    | Plan UX/UI before any code | search |
| `critique` | UX design review — hierarchy, clarity, emotional resonance | — |
| `audit`    | Technical quality scan (a11y, performance, theming, responsive, anti-patterns) | detector |
| `polish`   | Final systematic pass + design-system alignment + shipping readiness | detector |
| `system`   | Generate a tailored design system (pattern + style + palette + type + tokens) | search `--design-system` |

### craft
The full flow. Don't compress the gates.
1. **Shape first** — run the `shape` flow (below) unless the user already supplied a confirmed
   direction. A shape brief is the contract for composition, hierarchy, density, atmosphere, and
   signature moves.
2. **Load references** for every topic the feature touches (setup step 3).
3. **Build to the production bar** — beautiful, responsive, fast, accessible, bug-free, on-brand.
   Real content and copy (ux-writing.md), all component states (interaction-design.md), purposeful
   motion with a reduced-motion path (motion-design.md). No placeholder `<div>`s where imagery
   belongs (register.md, brand).
4. **Iterate visually** — if you can screenshot/run the app, inspect the result against the
   approved direction and fix what's off. If the live result lacks the direction's major
   ingredients, the implementation is wrong.
5. **Self-audit** — run `audit` over the changed files before presenting.
6. **Present** concisely: what was built, the key design decisions, and any follow-ups.

### shape
Plan before code. Don't write implementation here.
1. **Discovery** — establish purpose & audience, content & data, design direction, scope,
   constraints, and explicit anti-goals. Ask only what you can't infer; one tight round.
2. **Direction** — name the aesthetic lane and a real reference (register.md). Pull concrete
   backing via `search.py` (style/color/typography). Run the AI-slop test (first- and second-order)
   before committing.
3. **Brief** — produce a short design brief: register, layout/IA, palette strategy, type system,
   motion stance, signature moves, and what's explicitly out. This brief is the contract `craft`
   builds against.

### critique
UX design review — no code changes.
- Evaluate against the priority ladder and references: visual hierarchy, information architecture,
  cognitive load, clarity, consistency, accessibility, and emotional resonance / distinctiveness
  (the register's slop test).
- Run the detector for objective anchors: `node "$FE/scripts/detect.mjs" --json <files>`.
- Report prioritized findings (most impactful first), each tied to a rule or reference. Note what's
  working, not only what's broken.

### audit
Technical quality scan — diagnose, don't fix (hand fixes to `polish`/`craft`).
1. **Run the detector:** `node "$FE/scripts/detect.mjs" --json <files-or-dirs>` — deterministic
   anti-pattern hits (no LLM, no API key). If `node` is unavailable, audit from `rules.md` manually
   and say so.
2. **Scan five axes:** Accessibility (contrast, focus, keyboard, alt, headings), Performance (CLS,
   lazy-load, animated props), Theming (token consistency, raw hex), Responsive (breakpoints,
   overflow), Anti-Patterns (the detector hits + the absolute bans).
3. **Report:** a short health summary, then findings grouped by severity (each citing the rule id /
   detector id), systemic patterns, and positives. End with recommended next actions.

### polish
Final systematic pass — apply fixes.
1. **Discover the design system** (tokens, theme, components) and assess the current state.
2. **Polish systematically**, in order: visual alignment & spacing → IA & flow → typography → color
   & contrast → interaction states → micro-interactions → copy → icons & imagery → forms → edge &
   error states → responsiveness → performance → code quality. Each step leans on its reference.
3. **Verify:** re-run `audit`; confirm detector is clean (or every remaining hit is justified).
   Clean up dead code and leftover scaffolding before presenting.

### system
Generate a complete design system for a described project:
```bash
python3 "$FE/scripts/search.py" "<project description>" --design-system [-p "<name>"]
# add --persist to write design-system/MASTER.md (+ pages/) into the user's project
```
Present the recommended pattern, style, palette (full token set), typography, key effects, and the
anti-patterns to avoid. Treat the output as a starting contract, then sanity-check it against
register.md and the AI-slop test before the user builds on it.

## Notes
- **Conflicts** between guidance sources resolve in favor of the impeccable spine in `rules.md`;
  the knowledge base supplies concrete backing values (palettes, fonts, styles), not overrides.
- **Folded-in verbs** (bolder, quieter, distill, animate, delight, colorize, typeset, layout,
  harden, onboard, clarify, adapt, overdrive) are named techniques in `rules.md` — apply them by
  name within `craft`/`polish` rather than as separate commands.
- Always prefer the project's existing conventions when they already work.
