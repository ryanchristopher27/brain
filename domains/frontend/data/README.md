# Frontend Knowledge Base (data)

ui-ux-pro-max's CSV design knowledge base. Queried by the search scripts in `../scripts/`, not
read directly by Claude in normal use.

> **Status:** ported (M2 complete). Curated CSVs below are present, plus `stacks/` (16 per-stack
> guideline CSVs) backing `search.py --stack <stack>`.

## CSVs (curated subset)

| File | Contents |
|------|----------|
| `styles.csv` | UI styles with keywords, colors, effects, best-for, a11y, frameworks |
| `colors.csv` | Color palettes by product type (full token set + notes) |
| `typography.csv` | Font pairings (heading/body, mood, Google Fonts URL, Tailwind config) |
| `google-fonts.csv` | Font families with classifications, axes, popularity |
| `charts.csv` | Chart-type recommendations by data shape + a11y guidance |
| `ux-guidelines.csv` | UX rules with do/don't + good/bad code examples + severity |
| `ui-reasoning.csv` | Pattern → style/color/type recommendations + decision rules |
| `products.csv` | Product-type catalog used for matching |
| `landing.csv` | Landing-page section patterns |
| `icons.csv` | Icon-set guidance |
| `app-interface.csv` | App-shell interface patterns |
| `react-performance.csv` | React performance rules |

Plus `stacks/*.csv` — per-stack guidelines (react, nextjs, vue, svelte, astro, swiftui,
react-native, flutter, nuxtjs, nuxt-ui, html-tailwind, shadcn, jetpack-compose, threejs, angular,
laravel).

**Excluded:** `design.csv` and `draft.csv` (large source/draft dumps), `_sync_all.py` (dev build
tooling) — see Decisions Log.
