# Reference — Interaction Design

Deep-dive for component states, focus, forms, loading, and affordances. Read when the work touches
interactive components or their states. Defaults shift by register — see [register.md](register.md).

## Core rules

- **Touch targets ≥ 44×44px** with ≥ 8px spacing. No hover-only affordances — everything reachable
  by touch and keyboard.
- **Never remove focus rings.** Every interactive element keeps a visible focus state and an
  accessible name.
- **Dropdown clipping:** a `position: absolute` menu inside an `overflow: hidden|auto` container
  gets clipped. Use the native `<dialog>` / popover API, `position: fixed`, or a portal to escape
  the stacking context. `<!-- rule:skill-interaction-dropdown-clipping -->`
- **Every async action shows feedback** — loading and error, never an instant (0ms) silent swap.

## Component states (product register — critical)

Every interactive component ships with: **default, hover, focus, active, disabled, loading,
error**. Don't ship half. `<!-- rule:product-components-all-states -->`

- **Skeleton states** for loading, not spinners in the middle of content. `<!-- rule:product-components-skeleton-loading -->`
- **Empty states that teach** the interface, not "nothing here." `<!-- rule:product-components-empty-states -->`
- **Consistent affordances** across the surface — same button shape, same form-control vocabulary,
  same icon style. If the "save" button looks different in two places, one is wrong.
  `<!-- rule:product-components-consistent-affordances --> <!-- rule:product-ban-inconsistent-components -->`

## Product bans

- **Reinventing standard affordances** for flavor — custom scrollbars, weird form controls,
  non-standard modals. `<!-- rule:product-ban-reinvented-affordances -->`
- **Modal as first thought.** Modals are usually laziness; exhaust inline / progressive
  alternatives first. `<!-- rule:product-ban-modal-first-thought -->`
- **Heavy color / full-saturation accents on inactive states.** `<!-- rule:product-ban-heavy-inactive-color -->`

## Data

```
python3 ../scripts/search.py "form focus state accessibility touch" --domain ux   # ux-guidelines: interaction + a11y do/don't, severity
python3 ../scripts/search.py "<component>" --domain style                          # component-relevant style guidance
```

See also: [motion-design.md](motion-design.md), [ux-writing.md](ux-writing.md), `../rules.md` §1 & §2.
