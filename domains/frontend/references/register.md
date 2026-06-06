# Reference — Register (Brand vs. Product)

**Read this on every `/design` invocation** — skipping it produces generic output. The register
sets the defaults the topic references then adjust. Pick by first match: (1) task cue ("landing
page" vs "dashboard"); (2) the surface in focus; (3) an explicit declaration in project docs.

| | **Brand** — design IS the product | **Product** — design SERVES the product |
|---|---|---|
| **When** | Landing/marketing pages, campaigns, portfolios, long-form, about pages | App UIs, dashboards, settings, data tables, tools, authenticated surfaces |
| **Stance** | Communicate, not transact | Disappear into the task |
| **Slop test** | "Could someone say *AI made this*?" Distinctiveness is the bar. | "Would a power user of Linear/Figma/Notion *trust* this?" Earned familiarity is the bar. |
| **Failure mode** | Timid palettes, average layouts, zero imagery → invisible | Strangeness without purpose: over-decorated buttons, gratuitous motion, display fonts in labels |
| **Type** | Two families when voice needs it; fluid `clamp()` scale, ≥1.25 ratio | Often one family; fixed rem scale; tighter 1.125–1.2 ratio |
| **Color** | Committed / Full / Drenched are on the table — use them; name a reference | Restrained is the floor; standardized state vocabulary; accent only for action/selection/state |
| **Motion** | Ambitious first-load choreography (when it earns it), or deliberate stillness | 150–250ms, conveys state only, no page-load sequences |
| **Components** | Art direction per section permitted | Every state shipped; consistent vocabulary screen-to-screen |

## Brand register — the bar is distinctiveness

Average is no longer findable; restraint *without intent* reads as mediocre. Brand surfaces need a
POV, a specific audience, a willingness to risk strangeness.

- **Name the aesthetic lane before committing** (Klim specimen / Stripe-minimal / Liquid-Death
  maximalism). Then the inverse test: describe what you're about to build the way a competitor
  would describe theirs — if it fits the modal landing page in the category, restart.
  `<!-- rule:brand-typo-reflex-reject-lanes -->`
- **Reflex-reject aesthetic lanes** (currently saturated; need a register reason that *requires*
  them): **Editorial-typographic** — display italic serif + small mono labels + ruled separators +
  monochrome restraint. Don't default here on briefs that aren't literally magazine-shaped.
  `<!-- rule:brand-ban-editorial-default -->`
- **Imagery is required** when the brief implies it (restaurant, hotel, food, travel, fashion,
  photography). Zero images is a bug, not restraint. Use real assets or verified Unsplash
  (`https://images.unsplash.com/photo-{id}?auto=format&fit=crop&w=1600&q=80`) — never colored
  `<div>` placeholders. Search the *physical object*, not the category. `<!-- rule:brand-imagery-required -->`
- **Brand bans:** mono as lazy "technical" shorthand; large rounded icon tiles above every heading;
  single-family-by-reflex; all-caps body; repeated tiny uppercase section kickers.
  `<!-- rule:brand-ban-mono-as-shorthand --> <!-- rule:brand-ban-large-rounded-icons --> <!-- rule:brand-ban-repeated-section-kickers -->`
  (detector: `icon-tile-stack`, `repeated-section-kickers`)

## Product register — the bar is earned familiarity

The tool should disappear into the task. Familiarity is a feature; consistency beats surprise.

- **Permissions product can take:** system fonts and familiar sans (Inter, SF Pro, system-ui);
  standard navigation (top bar + side nav, breadcrumbs, tabs, command palettes); density; the same
  vocabulary screen-to-screen. Delight is saved for moments, not pages.
- **Product bans:** decorative motion that doesn't convey state; inconsistent component vocabulary;
  display fonts in UI labels/buttons/data; reinvented standard affordances; heavy color on inactive
  states; modal as first thought. `<!-- rule:product-ban-display-fonts-ui --> <!-- rule:product-ban-modal-first-thought -->`

## The AI slop test (both registers)

If someone could say "AI made that" without doubt, it failed. Run at two altitudes:
- **First-order:** if the theme + palette are guessable from the category alone, it's the first
  training reflex. Rework the scene sentence and color strategy. `<!-- rule:skill-slop-first-order-check -->`
- **Second-order:** if the aesthetic family is guessable from category-plus-anti-reference ("AI tool
  that's not SaaS-cream → editorial-typographic"), it's the trap one tier deeper. Rework until
  neither answer is obvious. `<!-- rule:skill-slop-second-order-check -->`

## Data

```
python3 ../scripts/search.py "<product type>" --domain product    # 161 product types for matching
python3 ../scripts/search.py "<pattern>" --domain style           # styles tagged by best-for / register fit
python3 ../scripts/search.py "<ui pattern>" --domain ux           # reasoning: pattern → style/color/type + anti-patterns
```

See also: every topic reference defers its register-specific defaults here. `../rules.md` opens with
the shared priority ladder; the Absolute Bans there apply across both registers.
