# Reference — UX Writing

Deep-dive for interface copy: labels, buttons, errors, empty states, microcopy. Read when the work
touches words in the UI. Voice shifts by register — see [register.md](register.md).

## Core rules

- **Every word earns its place.** No restated headings, no intros that repeat the title.
  `<!-- rule:skill-copy-every-word-earns -->`
- **Button labels: verb + object.** "Save changes" beats "OK"; "Delete project" beats "Yes." The
  label says what will happen. `<!-- rule:skill-copy-button-verb-object -->`
- **Link text needs standalone meaning.** "View pricing plans" beats "Click here" — screen readers
  announce links out of context. `<!-- rule:skill-copy-link-standalone -->`
- **No em dashes** (and not `--` either). Use commas, colons, semicolons, periods, or parentheses.
  `<!-- rule:skill-copy-no-em-dashes -->` (detector: `em-dash-overuse`)
- **No marketing buzzwords** — streamline / empower / supercharge / leverage / unleash / transform /
  seamless / world-class / enterprise-grade / next-generation / cutting-edge / game-changer /
  mission-critical. Pick a specific noun and a verb describing what the product literally does.
  `<!-- rule:skill-copy-no-buzzwords -->` (detector: `marketing-buzzword`)
- **No aphoristic cadence as default voice.** Don't fall into "serious statement, then punchy short
  negation" as the page's recurring rhythm. If three or more copy blocks land on a short
  rebuttal-shaped sentence, rewrite. Specific, not aphoristic. `<!-- rule:skill-copy-no-aphoristic-cadence -->` (detector: `aphoristic-cadence`)
- **No "X theater" / "actually X" / "not just X, it's Y"** constructions — instant slop. Choose a
  specific noun, not a meta-criticism phrase. `<!-- rule:skill-ban-codex-x-theater -->`

## Patterns

- **Error messages** state what happened and the next action, in plain language — not a code or a
  blame. **Empty states teach** the interface and point to the first action (see
  [interaction-design.md](interaction-design.md)).
- **Alt text is part of the voice** (brand): "Coastal fettuccine, hand-cut, served on the terrace"
  beats "pasta dish". `<!-- rule:brand-imagery-alt-text -->`

## Data

```
python3 ../scripts/search.py "copy label error empty state accessibility" --domain ux   # ux-guidelines: writing-adjacent do/don't
```

See also: [register.md](register.md), [interaction-design.md](interaction-design.md), `../rules.md` "Copy".
