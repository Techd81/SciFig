# Palette Presets

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

## Semantic Mapping Defaults

- `control` -> `#1F4E79`
- `treatment` -> `#C8553D`
- `rescue` -> `#4C956C`
- `vehicle` -> `#6C757D`
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
