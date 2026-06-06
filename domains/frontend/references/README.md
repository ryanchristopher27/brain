# Frontend References

Deep-dive design guidance. The `/design` command reads the reference(s) matching the work before
acting; `rules.md` stays scannable and links here for detail.

> **Status:** built (M4 complete). Synthesized by distilling impeccable's spine (`SKILL.src.md`
> general rules, absolute bans, registers) + topic command-refs into clean topic guides — the 7
> named files the README originally advertised never existed as copyable files (see Decisions Log).
> Each rule keeps its source `rule:` id so the `audit` command can tie guidance to detector hits.

## Files

| File | Covers | Backing data |
|------|--------|--------------|
| `typography.md` | Type systems, font pairing, scale, reflex-reject fonts | `data/typography.csv`, `data/google-fonts.csv` |
| `color-and-contrast.md` | Contrast, OKLCH, color strategy, the cream/sand trap | `data/colors.csv` |
| `spatial-design.md` | Spacing rhythm, grids, z-index, template-grid bans | `data/ux-guidelines.csv`, `data/styles.csv` |
| `motion-design.md` | Easing, reduced motion, reveal safety, materials palette | `data/ux-guidelines.csv` |
| `interaction-design.md` | Component states, focus, dropdown clipping, modals | `data/ux-guidelines.csv` |
| `responsive-design.md` | Mobile-first, overflow, structural vs fluid | `data/ux-guidelines.csv`, `data/stacks/` |
| `ux-writing.md` | Button/link labels, errors, em-dash & buzzword bans | `data/ux-guidelines.csv` |
| `register.md` | Brand-vs-product register (read on every invocation) | `data/products.csv`, `data/styles.csv`, `data/ui-reasoning.csv` |
| `charts.md` | Chart-type selection by data shape | `data/charts.csv` |
