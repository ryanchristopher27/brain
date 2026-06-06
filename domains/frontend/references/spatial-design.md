# Reference — Spatial Design (spacing, layout, grids)

Deep-dive for spacing systems, grids, visual rhythm, and hierarchy. Read when the work touches
layout, spacing, alignment, or z-index. Defaults shift by register — see [register.md](register.md).

## Core rules

- **Vary spacing for rhythm** — generous separations between groups, tight groupings within. Even
  spacing reads as monotonous. `<!-- rule:skill-layout-vary-spacing -->` (detector: `monotonous-spacing`)
- **Cards are the lazy answer.** Use them only when they're truly the best affordance. **Nested
  cards are always wrong.** `<!-- rule:skill-layout-cards-lazy -->` (detector: `nested-cards`)
- **Flexbox for 1D, Grid for 2D.** Don't default to Grid when `flex-wrap` would be simpler.
  `<!-- rule:skill-layout-flex-vs-grid -->`
- **Breakpoint-free responsive grids:** `repeat(auto-fit, minmax(280px, 1fr))`.
  `<!-- rule:skill-layout-auto-fit-grid -->`
- **Semantic z-index scale** (dropdown → sticky → modal-backdrop → modal → toast → tooltip). Never
  arbitrary values like 999 or 9999. `<!-- rule:skill-layout-z-index-scale -->`
- **Don't over-round.** Cards top out at 12–16px radius; full-pill is fine for tags/buttons. 24–40px
  on a card is a common AI tell. `<!-- rule:skill-ban-codex-over-round -->`
- **Don't pair a 1px border with a wide soft shadow** (blur ≥16px) on the same element — the
  "ghost-card" look. Pick one. `<!-- rule:skill-ban-codex-ghost-card -->`

## Avoid the template grids

- **Identical card grids** — same-sized icon+heading+text cards repeated endlessly. `<!-- rule:skill-ban-identical-card-grids -->`
- **The hero-metric template** — big number, small label, supporting stats, gradient accent. `<!-- rule:skill-ban-hero-metric -->`
- **Side-stripe borders** — `border-left/right` > 1px as a colored accent on cards/alerts. Rewrite
  with full borders, background tints, or leading icons. `<!-- rule:skill-ban-side-stripe-borders -->` (detector: `side-tab`, `border-accent-on-rounded`)

## By register

- **Brand:** asymmetric compositions are an option — break the grid intentionally for emphasis.
  Fluid `clamp()` spacing that breathes on larger viewports. For image-led briefs, full-bleed hero
  imagery is canonical. `<!-- rule:brand-layout-asymmetric --> <!-- rule:brand-layout-fluid-spacing -->`
- **Product:** responsive behavior is **structural** (collapse sidebar, responsive table,
  breakpoint-driven columns), not fluid typography. Density is a feature when users need it.
  `<!-- rule:product-layout-responsive-structural -->`

## Data

No dedicated spacing CSV; layout guidance with good/bad examples lives in the UX guidelines, and
pattern-level layout recommendations in the reasoning table:
```
python3 ../scripts/search.py "spacing layout grid" --domain ux        # ux-guidelines: do/don't + code examples + severity
python3 ../scripts/search.py "<ui pattern>" --domain style            # styles: design-system variables, effects
```

See also: [responsive-design.md](responsive-design.md), [register.md](register.md), `../rules.md` §5.
