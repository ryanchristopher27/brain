# Reference — Typography

Deep-dive for type systems, font selection, pairing, and scale. The `/design` command reads this
when the work touches fonts, hierarchy, or sizing. Rules carry their source `rule:` id so the
`audit` command can tie guidance to detector hits. Defaults shift by register — see
[register.md](register.md).

## Core rules

- **Cap font families at 3** (display + body + optional mono). More reads as indecision, not
  richness; one well-tuned family with weight contrast usually beats three competing typefaces.
  `<!-- rule:skill-typo-font-count -->`
- **Pair on a contrast axis** (serif + sans, geometric + humanist), or use one family in multiple
  weights. Don't pair two faces that are similar-but-not-identical. `<!-- rule:skill-typo-font-pairing-contrast -->`
- **Hierarchy through scale + weight**, ≥1.25 ratio between steps. Flat scales (≈1.1×) read as
  uncommitted. `<!-- rule:skill-typo-scale-ratio -->`
- **Body line length 65–75ch.** Data/compact UI can run denser; tables at 120ch+ are fine.
  `<!-- rule:skill-typo-line-length -->`
- **No all-caps body copy.** Reserve uppercase for short labels (≤4 words), the occasional eyebrow,
  and badges. `<!-- rule:skill-typo-no-all-caps-body -->`
- **Hero/display ceiling: `clamp()` max ≤ 6rem (~96px).** 8–11rem reads as comically loud, not
  bold. `<!-- rule:skill-typo-hero-ceiling -->`
- **Display letter-spacing floor: ≥ -0.04em.** Tighter and letters touch; -0.02 to -0.03em is
  plenty for tight grotesque display. `<!-- rule:skill-typo-tracking-floor -->`
- **`text-wrap: balance`** on h1–h3 for even line lengths; **`text-wrap: pretty`** on long prose to
  reduce orphans. `<!-- rule:skill-typo-text-wrap-balance -->`
- **Light type on dark** needs +0.05–0.1 line-height; it reads lighter and wants more air.
  `<!-- rule:brand-typo-light-on-dark-leading -->`

## Font selection procedure (brand register — never skip)

1. Write three concrete brand-voice words — physical-object words ("warm and mechanical and
   opinionated"), not "modern" or "elegant".
2. List the three fonts you'd reach for by reflex. If any are in the reflex-reject list, reject
   them — they're training-data defaults that create monoculture.
3. Browse a real catalog (Google Fonts, Pangram Pangram, Future Fonts, Klim, Velvetyne) for the
   brand *as a physical object* — a museum caption, a 1970s terminal manual, a concert poster.
4. Cross-check: "elegant" isn't necessarily serif, "technical" isn't necessarily sans. If the pick
   matches your original reflex, start over. `<!-- rule:brand-typo-font-selection-procedure -->`

**Reflex-reject fonts** (overused; look further): Inter · Roboto · Fraunces · Newsreader · Lora ·
Crimson · Playfair Display · Cormorant · Syne · Space Grotesk · Space Mono · IBM Plex (Sans/Mono/
Serif) · DM Sans/Serif · Outfit · Plus Jakarta Sans · Instrument Sans/Serif · Geist.
`<!-- rule:brand-typo-reflex-reject-fonts -->` (detector rule: `overused-font`)

## By register

- **Product:** one well-tuned sans often carries everything (headings, buttons, labels, body,
  data). Use a **fixed rem scale** (not fluid `clamp()`) and a tighter ratio (1.125–1.2).
  `<!-- rule:product-typo-one-family --> <!-- rule:product-typo-fixed-rem-scale -->`
- **Brand:** modular fluid `clamp()` scale, ≥1.25 ratio; two families only when the voice needs it.

## Data

Concrete pairings and font metadata live in the knowledge base:
```
python3 ../scripts/search.py "<mood/brand words>" --domain typography     # 57 curated pairings (heading/body, Google Fonts URL, Tailwind config)
python3 ../scripts/search.py "<classification>" --domain google-fonts     # ~1900 families w/ axes, popularity, classifications
```

See also: [register.md](register.md), [color-and-contrast.md](color-and-contrast.md), `../rules.md` §6.
