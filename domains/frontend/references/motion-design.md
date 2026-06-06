# Reference — Motion Design

Deep-dive for animation, easing, and reveal patterns. Read when the work adds or fixes motion.
Defaults shift by register — see [register.md](register.md).

## Core rules

- **Motion is intentional, part of the build — not an afterthought.** `<!-- rule:skill-motion-intentional -->`
- **Ease out with exponential curves** (ease-out-quart / quint / expo). No bounce, no elastic.
  `<!-- rule:skill-motion-ease-out-exp -->` (detector: `bounce-easing`)
- **Don't animate CSS layout properties** unless truly needed — animate `transform`/`opacity`.
  `<!-- rule:skill-motion-no-layout-animate -->` (detector: `layout-transition`)
- **Reduced motion is not optional.** Every animation needs a `@media (prefers-reduced-motion:
  reduce)` alternative — typically a crossfade or instant transition. `<!-- rule:skill-motion-reduced-motion -->`
- **No uniform section-fade reflex.** Staggering items within one list is legitimate; the tell is
  one identical entrance applied to every section. Each reveal should fit what it reveals.
  Suppressing the reflex is never a reason to ship a page with *no* motion. `<!-- rule:skill-motion-no-section-fade -->`
- **Reveal safety:** reveal animations must enhance an already-visible default. Don't gate content
  visibility on a class-triggered transition — transitions pause on hidden tabs and headless
  renderers, so the section can ship blank. `<!-- rule:skill-motion-reveal-safety -->`
- **The materials palette is bigger than transform/opacity** — blur, backdrop-filter, clip-path,
  mask, and shadow/glow belong when they materially improve the effect and stay smooth.
  `<!-- rule:skill-motion-materials-palette -->`
- **Reach for libraries** for advanced needs (motion, gsap, anime.js, lenis). `<!-- rule:skill-motion-use-libraries -->`
- **Never animate `<img>` on hover** (incl. Tailwind `group-hover:scale/rotate/translate` on a
  child image). It adds no information and reads as "animated because it could be." Animate the
  card's background, border, or shadow instead. `<!-- rule:skill-interaction-gemini-no-image-hover -->`

## By register

- **Brand:** one well-orchestrated page-load beats scattered micro-interactions — when the brand
  invites it. Some brands skip entrance motion entirely; that restraint is the voice. Ambitious
  first-load choreography is a brand permission. `<!-- rule:brand-motion-one-page-load --> <!-- rule:brand-permission-first-load-motion -->`
- **Product:** 150–250ms on most transitions — users are in flow, don't make them wait for
  choreography. Motion conveys **state** (change, feedback, loading, reveal), not decoration. **No
  orchestrated page-load sequences.** `<!-- rule:product-motion-quick-transitions --> <!-- rule:product-motion-state-not-decoration -->`

## Data

```
python3 ../scripts/search.py "animation motion transition" --domain ux   # ux-guidelines: animation do/don't + severity
```

See also: [interaction-design.md](interaction-design.md), [register.md](register.md), `../rules.md` §7.
