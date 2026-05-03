# Palette Presets

Status: superseded by `templates/template-palette-registry.json`. This file
remains human-readable documentation of palette intent; runtime resolution is
JSON-driven.

Stable palette presets for publication-grade scientific figures.

## Categorical Presets

### `journal_muted_8`

```python
[
    "#1F4E79",  # slate blue
    "#4C956C",  # muted green
    "#F2A541",  # amber
    "#C8553D",  # terracotta
    "#7A6C8F",  # muted purple
    "#2B6F77",  # deep teal
    "#BC4749",  # muted red
    "#6C757D"   # neutral gray
]
```

### `journal_muted_6`

```python
[
    "#1F4E79",
    "#4C956C",
    "#F2A541",
    "#C8553D",
    "#7A6C8F",
    "#6C757D"
]
```

### `ml_model_performance_10`

Template-derived AI/ML palette for Random Forest, XGBoost, LightGBM, GBDT, SVM, KNN, train/test splits, and residual diagnostics. Use when `domainHints.primary == "computer_ai_ml"` or the template case plan includes `ml_model_diagnostics`.

```python
[
    "#4DBBD5",  # RF / cyan anchor
    "#E64B35",  # XGBoost / coral
    "#00A087",  # LightGBM / teal
    "#3C5488",  # GBDT / steel
    "#F39B7F",  # SVM / soft orange
    "#8491B4",  # KNN / lavender gray
    "#91D1C2",  # support green-cyan
    "#DC0000",  # residual / warning red
    "#7E6148",  # secondary model
    "#333333"   # reference line / text
]
```

## Sequential Presets

### `seq_cool`

```python
["#F7FBFF", "#D6EAF8", "#A9CCE3", "#5DADE2", "#21618C"]
```

### `seq_warm`

```python
["#FFF6E8", "#FBD38D", "#F6AD55", "#DD6B20", "#9C4221"]
```

## Diverging Presets

### `div_centered`

```python
["#3B6FB6", "#8FBCE6", "#F7F7F7", "#E6A0A0", "#B5403A"]
```

### `div_expression`

```python
["#2D5AA7", "#9CC4E4", "#F5F5F5", "#F4A582", "#B2182B"]
```

## Colorblind-safe Presets

### `wong_8` (Bang Wong, Nature Methods)

```python
[
    "#000000",  # black
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7"   # reddish purple
]
```

### `okabe_ito_8`

```python
[
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#000000"   # black
]
```

### `genomics_categorical`

```python
[
    "#3B5998",  # upregulated
    "#C8553D",  # downregulated
    "#999999",  # not significant
    "#4C956C",  # pathway A
    "#F2A541",  # pathway B
    "#7A6C8F",  # pathway C
]
```

### `clinical_survival`

```python
[
    "#0072B2",  # treatment arm
    "#C8553D",  # control arm
    "#4C956C",  # subgroup A
    "#F2A541",  # subgroup B
]
```

## Editorial Impact Presets

These palettes are still restrained and colorblind-aware, but provide stronger figure-level hierarchy than the muted defaults.

### `editorial_science_8`

```python
[
    "#0B1F3A",  # near-navy anchor
    "#E64B35",  # high-signal coral
    "#00A087",  # teal
    "#3C5488",  # steel blue
    "#F39B2F",  # amber accent
    "#7E6148",  # muted brown
    "#8491B4",  # lavender gray
    "#4DBBD5"   # cyan support
]
```

### `cell_high_contrast_6`

```python
[
    "#1B1B1B",
    "#D73027",
    "#4575B4",
    "#1A9850",
    "#FDAE61",
    "#7570B3"
]
```

### `single_cell_12`

```python
[
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728",
    "#9467BD", "#8C564B", "#E377C2", "#7F7F7F",
    "#BCBD22", "#17BECF", "#4C78A8", "#F58518"
]
```

## Semantic Mapping Defaults

- `control` -> `#1F4E79`
- `treatment` -> `#C8553D`
- `treated`, `drug`, `stimulated`, `case` -> treatment color unless a domain playbook overrides it
- `rescue` -> `#4C956C`
- `vehicle` -> `#6C757D`
- `train` -> `#4C78A8`
- `test` -> `#E45756`
- `actual`, `observed`, `experimental` -> `#1F4E79`
- `predicted`, `fitted`, `estimated` -> `#C8553D`
- `feature_low` -> cool side of diverging scale
- `feature_high` -> warm side of diverging scale
- `negative_correlation` -> cool side of diverging scale
- `positive_correlation` -> warm side of diverging scale
- `optimal`, `pareto`, `selected` -> `#00A087`
- `low risk` -> lighter sequential tone
- `high risk` -> darker sequential tone
- `down-regulated` -> cool side of diverging scale
- `up-regulated` -> warm side of diverging scale

## Palette Rules

1. Keep categorical mappings stable across all panels in one figure.
2. Use a separate sequential or diverging scale for heatmaps and score gradients.
3. Never encode the same category with different colors across hero and support panels.
4. Test every palette in grayscale; if adjacent groups collapse, increase luminance separation.
5. Reserve very bright accent colors for one or two key highlights only.
6. Sort categories deterministically before assigning fallback colors.
7. If categories exceed the palette length, keep color stable and add marker shape, line style, or facet grouping instead of cycling indistinguishable colors.
8. For visual-impact mode, use one dark anchor, one warm highlight, and one cool support family; do not turn every group into a highlight.
9. Prediction diagnostics use actual/observed as the cool anchor and predicted/fitted as the warm highlight unless the input already defines a validated semantic map.
10. Density-colored scatter may use a sequential scale, but it needs a label or QA-tracked motif counter so it reads as local density instead of decorative color.
11. Feature-importance and SHAP-like views use cool-to-warm low/high feature semantics only when feature-value columns exist; otherwise use neutral ranked bars/lollipops.
12. Use hollow or edged marker variants for sample/source overlays so color remains reserved for the primary scientific variable.
