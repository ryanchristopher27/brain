# Domain Rules — Frontend

These rules apply when the frontend domain is active. They extend universal rules — they do not
replace them. Where a domain rule conflicts with a universal rule, the domain rule takes
precedence for frontend work.

Rules are ordered by a **priority ladder**: when forced to choose, the lower number wins.
Each rule ends with a **verify hook** — `detector:<id>` runs the bundled linter
(`node scripts/detect.mjs --json <files>`), `search:<q>` queries the knowledge base
(`python3 scripts/search.py "<q>" --domain <d>`). These `scripts/...` paths are relative to this
domain dir and are illustrative; the `/design` command resolves the absolute brain-repo path at
runtime (it owns invocation). Deep detail lives in `references/`; this file stays scannable. **Register sets the defaults** — read [`references/register.md`](references/register.md)
on every task.

---

## 1. Accessibility — CRITICAL

- Body text contrast ≥ 4.5:1; large text (≥18px or bold ≥14px) ≥ 3:1. **Placeholder text is body
  text** — same 4.5:1, not a muted gray. Light gray "for elegance" is the #1 reason AI designs read
  as hard to read. → `detector:low-contrast` · [color-and-contrast.md](references/color-and-contrast.md)
- Gray text on a colored background looks washed out — use a darker shade of the background's hue or
  a transparency of the text color. → `detector:gray-on-color`
- Never remove focus rings; every interactive element keeps a visible focus state and an accessible
  name. → [interaction-design.md](references/interaction-design.md)
- Keyboard-operable everything; meaningful alt text; correct heading order (no skipped levels). →
  `detector:skipped-heading` · `search:accessibility --domain ux`

## 2. Touch & Interaction — CRITICAL

- Touch targets ≥ 44×44px with ≥ 8px spacing. No hover-only affordances. → `search:touch target --domain ux`
- Every async action shows loading + error feedback — never an instant (0ms) silent state swap.
  Skeletons for content loading, not center-screen spinners. → [interaction-design.md](references/interaction-design.md)
- Dropdowns/menus must escape clipping containers (`<dialog>`/popover, `position: fixed`, or a
  portal) — not `position: absolute` inside `overflow: hidden|auto`. → `detector` · interaction ref
- **Product:** ship all component states (default, hover, focus, active, disabled, loading, error)
  with a consistent vocabulary across the surface. → [register.md](references/register.md)

## 3. Performance — HIGH

- Reserve space for media (width/height or aspect-ratio) to keep CLS < 0.1; lazy-load below the
  fold; prefer WebP/AVIF. → `search:performance image loading --domain ux`
- Animate `transform`/`opacity`, not layout properties (width/height/top/left). → `detector:layout-transition`
- Don't gate content visibility on a class-triggered transition — it never fires on hidden tabs or
  headless renderers and ships the section blank. → [motion-design.md](references/motion-design.md)

## 4. Style Selection — HIGH

- Match the style to the product type and hold it consistently. Pick by intent, not by reflex. →
  `search:<product type> --domain style` · `search:<product type> --domain product`
- SVG icons, never emoji as UI icons. One consistent icon style across the surface.
- **Run the AI-slop test.** If the theme + palette are guessable from the category alone, rework
  (first-order). If the aesthetic family is guessable from category-plus-anti-reference, rework
  again (second-order). → `detector:ai-color-palette` · [register.md](references/register.md)

## 5. Layout — HIGH

- Vary spacing for rhythm — generous between groups, tight within. → `detector:monotonous-spacing` · [spatial-design.md](references/spatial-design.md)
- Cards are the lazy answer; use them only when truly the best affordance. **Nested cards are always
  wrong.** → `detector:nested-cards`
- Flexbox for 1D, Grid for 2D. Breakpoint-free grids: `repeat(auto-fit, minmax(280px, 1fr))`.
- Semantic z-index scale (dropdown → sticky → modal → toast → tooltip) — never 999/9999.
- Mobile-first; no horizontal scroll; never disable zoom; test heading copy for overflow at every
  breakpoint. → `detector:body-text-viewport-edge` · [responsive-design.md](references/responsive-design.md)
- Cards top out at 12–16px radius; don't pair a 1px border with a ≥16px-blur shadow (ghost-card). →
  `detector:border-accent-on-rounded`

## 6. Typography & Color — MEDIUM

- Cap font families at 3 (display + body + optional mono); pair on a contrast axis. Avoid the
  overused faces (Inter, Roboto, Fraunces, Space Grotesk, …). → `detector:overused-font` · `search:<mood> --domain typography`
- Hierarchy via scale + weight (≥1.25 step ratio); body line length 65–75ch; no all-caps body. →
  `detector:flat-type-hierarchy` · `detector:line-length` · [typography.md](references/typography.md)
- Hero/display `clamp()` max ≤ 6rem; display letter-spacing ≥ -0.04em; use `text-wrap: balance`
  on h1–h3. → `detector:extreme-negative-tracking`
- Use OKLCH; pick a color strategy (restrained → committed → full → drenched) before colors; semantic
  tokens, not raw hex in components. → `search:<product type> --domain color` · [color-and-contrast.md](references/color-and-contrast.md)
- Avoid the cream/sand body-bg default; carry warmth through accent, type, and imagery. → `detector:cream-palette`

## 7. Motion — MEDIUM

- Motion is intentional and part of the build, not decoration. Ease out with exponential curves —
  no bounce/elastic. → `detector:bounce-easing` · [motion-design.md](references/motion-design.md)
- `prefers-reduced-motion` is not optional — every animation needs a crossfade/instant alternative.
- No uniform section-fade reflex; each reveal fits what it reveals. Never animate `<img>` on hover
  (incl. Tailwind `group-hover:scale/rotate` on a child image).
- **Product:** 150–250ms, conveys state only, no orchestrated page-load. **Brand:** ambitious
  first-load choreography is permitted when it earns its place. → [register.md](references/register.md)

---

## Copy

- Every word earns its place; button labels are verb + object ("Save changes", not "OK"); link text
  has standalone meaning. → [ux-writing.md](references/ux-writing.md)
- No em dashes (or `--`); no marketing buzzwords (streamline/empower/supercharge/seamless/…); no
  aphoristic "statement-then-negation" cadence as default voice. → `detector:em-dash-overuse` · `detector:marketing-buzzword` · `detector:aphoristic-cadence`

## Named Techniques

The `/design` command (and the model) can apply these by name; they are folded-in impeccable verbs,
not separate commands. Each adjusts an existing design rather than starting over.

- **bolder / quieter** — amplify a timid design, or tone down an overstimulating one.
- **distill** — strip to essence; remove decoration that doesn't earn its place.
- **animate / delight / overdrive** — purposeful motion, moments of joy, or technically
  extraordinary effects (within the Motion rules above).
- **colorize / typeset / layout** — targeted fixes to color, type, or spatial rhythm.
- **harden / onboard / clarify / adapt** — edge cases & i18n, first-run/empty states, UX copy,
  device adaptation.

## Absolute Bans (both registers)

Match-and-refuse — if you're about to write one of these, rewrite the element with different
structure. The detector flags many of these deterministically.

- **Gradient text** (`background-clip: text` + gradient) — solid color only. → `detector:gradient-text`
- **Side-stripe borders** (`border-left/right` > 1px as a colored accent). → `detector:side-tab`
- **Glassmorphism as default**; the **hero-metric template**; **identical card grids**.
- **Tiny uppercase tracked eyebrow above every section**, and **numbered section markers (01/02/03)**
  as default scaffolding. → `detector:repeated-section-kickers` · `detector:numbered-section-markers`
- **Large rounded icon tiles above every heading** — screams template. → `detector:icon-tile-stack`
- **Text that overflows its container** at any breakpoint — the viewport is part of the design.
- **The trained-in SaaS look:** Inter everywhere, purple→blue gradients, cards in cards, gray text
  on color. If someone could say "AI made that" without doubt, it failed.

## Conflict resolution

On any conflict between sources, the rules here (the impeccable spine) win; the ui-ux-pro-max
knowledge base supplies concrete backing values (palettes, fonts, styles), not overrides.
