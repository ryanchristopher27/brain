# Reference — Responsive Design

Deep-dive for mobile-first behavior, fluid design, and device adaptation. Read when the work
targets multiple screen sizes. Defaults shift by register — see [register.md](register.md).

## Core rules

- **Mobile-first.** Build up from the smallest breakpoint; no horizontal scroll; never disable
  zoom; include the viewport meta tag.
- **Test heading copy at every breakpoint.** Long heading words + large `clamp()` scales + narrow
  grids cause headline overflow on tablet/mobile. If it overflows, reduce the clamp max or rewrite
  the copy. The viewport is part of the design. `<!-- rule:skill-ban-text-overflow -->` (detector: `body-text-viewport-edge`)
- **Breakpoint-free grids** where they fit: `repeat(auto-fit, minmax(280px, 1fr))`.
  `<!-- rule:skill-layout-auto-fit-grid -->`

## By register

- **Brand:** fluid spacing and type via `clamp()` that breathes on larger viewports. Art direction
  can shift per breakpoint when the narrative demands it. `<!-- rule:brand-layout-fluid-spacing -->`
- **Product:** responsive behavior is **structural, not fluid typography** — collapse the sidebar,
  make the table responsive, drive columns by breakpoint. A fluid h1 that shrinks in a sidebar
  looks worse, not better; use a fixed rem scale. `<!-- rule:product-layout-responsive-structural --> <!-- rule:product-typo-fixed-rem-scale -->`

## Data

Per-stack responsive idioms live in the stack guidelines; general responsive rules in ux-guidelines:
```
python3 ../scripts/search.py "responsive breakpoint mobile" --domain ux            # general responsive do/don't
python3 ../scripts/search.py "responsive layout" --stack <react|nextjs|vue|svelte|astro|...>   # stack-specific idioms
```

See also: [spatial-design.md](spatial-design.md), [register.md](register.md), `../rules.md` §5.
