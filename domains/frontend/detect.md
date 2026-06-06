# Detection Signals — Frontend

Claude checks for these signals at session start. If any primary signal is present, the domain
activates. Secondary signals strengthen the match but are not required alone.

## Primary Signals
- `package.json` exists at project root **and** lists a frontend framework dependency
  (`react`, `react-dom`, `next`, `vue`, `svelte`, `@sveltejs/kit`, `astro`, `solid-js`,
  `nuxt`, `@angular/core`).
- A CSS-tooling config is present: `tailwind.config.{js,ts,cjs,mjs}`, `postcss.config.*`,
  or a `components.json` (shadcn/ui).
- Component source files exist: `**/*.tsx`, `**/*.jsx`, `**/*.vue`, `**/*.svelte`.

## Secondary Signals
- A `components/`, `ui/`, `app/`, `pages/`, or `src/components/` directory exists.
- Source files import a UI/styling library (`tailwindcss`, `@radix-ui/*`, `framer-motion`,
  `styled-components`, `@emotion/*`, `clsx`, `class-variance-authority`).
- A design-system surface exists: `design-system/`, `tokens.*`, `theme.*`, or a global CSS
  file with custom properties (`--color-*`, `--space-*`).
- `CLAUDE.md` declares `domains: frontend`.

## Conflicts
- None known. Coexists with other domains (a Next.js + FastAPI repo activates frontend + ml).
  A backend-only or non-UI project should **not** trigger this domain — the primary signals
  intentionally require UI framework/markup presence, not just JavaScript.

## Soft Prerequisites
The domain activates on signal regardless of runtime availability. The bundled tooling needs:
- `python3` (stdlib only) for `scripts/` search + design-system generation.
- `node` for `scripts/detector/` anti-pattern linting.
When a runtime is missing, the matching command falls back to markdown guidance — note it,
don't fail.

## Manual Override
To force-activate this domain regardless of signals, add to the project's `CLAUDE.md`:
```
domains: frontend
```
