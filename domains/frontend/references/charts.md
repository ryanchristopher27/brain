# Reference — Charts & Data Visualization

Deep-dive for choosing and building charts. Read when the work visualizes data. This topic is
backed primarily by the knowledge base rather than the impeccable spine.

## Core guidance

- **Pick the chart by the data shape and the question**, not by what looks impressive. Comparison →
  bar; trend over time → line; part-to-whole → stacked bar or treemap (rarely pie); distribution →
  histogram or box; correlation → scatter.
- **Accessibility:** never encode meaning by color alone — add labels, patterns, or direct
  annotation. Provide a table fallback for screen readers. Verify contrast of series colors against
  the plot background (see [color-and-contrast.md](color-and-contrast.md)).
- **Respect data-volume thresholds** — past a certain row count, switch chart type or aggregate.
- **Motion conveys state, not decoration** — count-ups and transitions should clarify change, not
  perform (see [motion-design.md](motion-design.md)).

## Data

The knowledge base maps data shapes to recommended chart types with a11y grades and library picks:
```
python3 ../scripts/search.py "<data shape / question>" --domain chart
# charts.csv columns: Data Type, Best Chart Type, Secondary Options, When to Use, When NOT to Use,
#                      Data Volume Threshold, Color Guidance, Accessibility Grade, A11y Fallback,
#                      Library Recommendation, Interactive Level
```

See also: [color-and-contrast.md](color-and-contrast.md), `../rules.md` §3 (performance) & §1 (a11y).
