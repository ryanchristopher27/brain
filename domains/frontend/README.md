# Domain: Frontend

## What This Domain Covers

Frontend design and implementation quality — visual design, UX, accessibility, and the
craft of shipping production-grade interfaces. It consolidates two external design suites
into one brain-native domain: **impeccable** (an opinionated design spine — rules, design
verbs, and a deterministic anti-pattern detector) backed by **ui-ux-pro-max** (a queryable
knowledge base of color palettes, font pairings, UI styles, UX guidelines, and chart types).

Activates on projects that render a UI: websites, landing pages, dashboards, web apps,
component libraries, and design systems across React, Next.js, Vue, Svelte, Astro, and
Tailwind/shadcn stacks.

## When It Activates

See `detect.md` for the full signal list. Broadly:
- A `package.json` with a frontend framework dependency, a Tailwind/PostCSS config, or
  component source files (`.tsx/.jsx/.vue/.svelte`) are present — or the project declares
  `domains: frontend` in its `CLAUDE.md`.

## What It Changes

- **Rules:** `rules.md` — always-on design behavior, ordered by a priority ladder
  (accessibility → interaction → performance → style → layout → typography/color → motion),
  with each rule tied to a verification hook (a detector rule id or a knowledge-base query).
- **Commands:** `/design` — a single namespaced command with subcommands
  (`craft`, `shape`, `critique`, `audit`, `polish`, `system`).
- **Cursor rules:** `.cursor/rules/brain_domain_frontend_cursor-rule.mdc` (installed from
  `cursor-rule.mdc`), auto-applied via frontend file globs.

## Layout

```
domains/frontend/
├── README.md          This file
├── detect.md          Auto-detection signals
├── rules.md           Always-on design rules (the spine)
├── cursor-rule.mdc    Cursor-native version of the rules
├── NOTICE             Attribution for the consolidated sources
├── commands/
│   └── design.md      The /design command (verb + subcommands)
├── references/        Deep-dive guidance (typography, color, motion, …)
├── data/              ui-ux-pro-max CSV knowledge base
└── scripts/           Search engine (Python) + anti-pattern detector (Node)
```

## Tooling Prerequisites (soft)

The bundled tooling is dependency-light and degrades gracefully — commands fall back to
pure-markdown guidance when a runtime is absent:
- `python3` (standard library only) — `scripts/` knowledge-base search + design-system generator.
- `node` — `scripts/detector/` anti-pattern linting.

## Attribution

This domain vendors curated subsets of two upstream projects. See `NOTICE`.
- ui-ux-pro-max-skill — MIT — https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- impeccable — Apache 2.0 — https://github.com/pbakaus/impeccable
