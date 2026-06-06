# Reference — Color & Contrast

Deep-dive for palettes, contrast, theming, and color strategy. Read when the work touches color,
accessibility of text, or dark mode. Defaults shift by register — see [register.md](register.md).

## Contrast (accessibility — critical)

- **Verify contrast.** Body text ≥ 4.5:1 against its background; large text (≥18px or bold ≥14px)
  ≥ 3:1. **Placeholder text counts as body — same 4.5:1**, not the muted-gray default. The most
  common failure: muted gray body on a tinted near-white. If it's even close, bump the body color
  toward the ink end of the ramp. Light gray "for elegance" is the single biggest reason AI designs
  feel hard to read. `<!-- rule:skill-color-verify-contrast -->` (detector: `low-contrast`)
- **Gray text on a colored background looks washed out.** Use a darker shade of the background's own
  hue, or a transparency of the text color. `<!-- rule:skill-color-gray-on-color -->` (detector: `gray-on-color`)

## Building a palette (new projects)

- **Use OKLCH throughout.** `<!-- rule:skill-color-use-oklch -->`
- **Pick a color strategy before colors** — four steps on the commitment axis:
  `<!-- rule:skill-color-strategy-commitment -->`
  - **Restrained** — tinted neutrals + one accent ≤10%. Product default.
  - **Committed** — one saturated color carries 30–60% of the surface. Brand identity pages.
  - **Full palette** — 3–4 named roles, each used deliberately. Campaigns, data viz.
  - **Drenched** — the surface IS the color. Brand heroes.
- **Tinted neutrals:** add only 0.005–0.015 chroma toward the brand's hue. Don't default-tint warm
  or cool "because the brand feels that way" — that's the cross-project monoculture move.
  `<!-- rule:skill-color-tinted-neutrals-chroma -->`
- **Theme is never a default.** Not dark "because tools look cool dark," not light "to be safe."
  Write one sentence of physical scene (who, where, what ambient light, what mood); if it doesn't
  force the answer, add detail until it does. `<!-- rule:skill-color-theme-physical-scene -->`

## The cream/sand trap

The warm-neutral band (OKLCH L 0.84–0.97, C < 0.06, hue 40–100) reads as cream/sand/paper
regardless of what you call it — `--paper`, `--cream`, `--sand`, `--linen`, `--ivory` are tells in
themselves. A "warm/editorial/magazine" brief does **not** become a near-white warm-tinted bg.
Carry warmth through accent, type, and imagery — not the body bg. `<!-- rule:skill-color-anti-cream -->`
(detector: `cream-palette`, `ai-color-palette`)

## By register

- **Brand:** permission for Committed / Full / Drenched — use it. Name a real reference before
  picking ("Klim #ff4500 drench", "Stripe purple-on-white restraint"). Unnamed ambition becomes
  beige. Palette IS voice. `<!-- rule:brand-color-strategy-permission --> <!-- rule:brand-color-named-reference -->`
- **Product:** Restrained is the floor. Standardize a **state vocabulary** (hover, focus, active,
  disabled, selected, loading, error, warning, success, info). Accent only for primary actions,
  selection, and state — not decoration. Add a second neutral layer for sidebars/toolbars.
  `<!-- rule:product-color-restrained-default --> <!-- rule:product-color-state-vocab -->`

Absolute ban: **gradient text** (`background-clip: text` + gradient) — solid color only.
`<!-- rule:skill-ban-gradient-text -->` (detector: `gradient-text`)

## Data

```
python3 ../scripts/search.py "<product type>" --domain color      # 161 palettes: full token set (primary/secondary/accent/bg/card/muted/border/destructive…)
```

See also: [register.md](register.md), [typography.md](typography.md), `../rules.md` §1 & §6.
