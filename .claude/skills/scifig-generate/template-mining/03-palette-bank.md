# 实战色谱库 (Palette Bank)

Palettes harvested from the 77 reference cases. **Every palette here is anchored to specific case files** — Phase 3 binds palette names to actual hex codes via this file rather than inventing colors.

## How to use

```python
from .helpers import resolve_palette
palette = resolve_palette("nature_radar_dual")        # returns hex list
palette = resolve_palette("nature_radar_dual", n=4)   # truncate or cycle
```

Phase 2 picks a palette **name**; Phase 3 resolves it to hex via `resolve_palette()`. **Never hard-code hex codes in chart generators**; always go through this file.

## Decision flow (Phase 2)

1. **What does the user need to encode?**
   - 2 conditions/groups → `dual` family
   - 3-6 categorical groups → `categorical_*` family
   - Continuous magnitude (density, importance, value) → `sequential_*`
   - Bipolar signal (positive/negative ALE, SHAP, correlation) → `diverging_*`
   - Feature value low→high (SHAP beeswarm) → `feature_value_lowhigh`

2. **What journal/aesthetic?**
   - Nature top-tier, 2-condition radar/forest → `nature_radar_dual`
   - CEJ/Materials density+marginal → `cej_density_blue`
   - Cell scatter+bar high contrast → `cell_high_contrast_6`
   - Materials Today engineering bars → `materials_porosity_terracotta`
   - Generic muted SCI multi-condition → `morandi_sci_4`

3. **Color semantics?** Bind via `palette_role_map`. Never let observed/predicted swap colors across panels.

---

## 1. Categorical palettes

### `nature_radar_dual` (Nature semiconductor fibre, Vol 626 2024)

```python
[
    "#1F3A5F",  # Navy Blue (Ge / control)
    "#C8553D",  # Crimson  (Si / treatment)
]
```

Source: `绝美！Nature 这张雷达图_1777449664`. **Two-condition contrast** — the tightest palette in the corpus. Use for: hero radar, two-condition forest, predicted vs actual scatter.

### `morandi_sci_4` (universal multi-model)

```python
[
    "#4A6B8A",   # muted slate
    "#5FA896",   # muted teal-green
    "#D9A75A",   # muted amber
    "#B85B5B",   # muted brick
]
```

Source aggregate: `期刊复现：多面板回归预测散点图`, `期刊配图复现 _ Python绘制机器学习"预测-实验"对比图`. Use for: 2-4 model comparison bars/lines, multi-condition box plots, NMDS group colors.

### `cej_vibrant_3` (CEJ density panels)

```python
[
    "#00CED1",   # cyan accent
    "#FF0000",   # accent red
    "#1E90FF",   # dodger blue
]
```

Source: `Python复现顶刊CEJ_拒绝手绘`. Use for: 3-condition density scatter when contrast is the priority.

### `cell_high_contrast_6` (Cell scatter+bar, ScRNA UMAP)

```python
[
    "#1B1B1B", "#D73027", "#4575B4",
    "#1A9850", "#FDAE61", "#7570B3",
]
```

Source: `高级感！Python复刻Cell顶刊散点柱状图`. Use for: 5-6 categorical groups when journal expects bold contrast.

### `materials_porosity_terracotta` (Materials Today double-axis)

```python
[
    "#CFE2F3",   # soft sky bar
    "#9BC2E6",   # mid sky bar edge
    "#F48E66",   # terracotta line/marker
]
```

Source: `如何用Python绘制教科书级的双Y轴组合图`. Use for: dual-axis bar+line where bars are context and the line is the focal signal.

### `npg_4` (Nature Publishing Group muted)

```python
[
    "#E64B35",   # coral
    "#4DBBD5",   # cyan support
    "#00A087",   # teal accent
    "#3C5488",   # steel blue
]
```

Sources: `拒绝默认配色：Python 绘制多模型性能对比图`, several SHAP composites. Use for: 4-model SHAP, multi-method bars.

### `cool_summer_4` (Forest plot HR)

```python
[
    "#8DA0CB",   # lavender blue
    "#FC8D62",   # peach
    "#66C2A5",   # mint
    "#FBC15E",   # mustard
]
```

Source: `Python科研绘图复现_绘制多面板分组森林图`. Use for: 4-cohort HR forest, 4-method box plots.

### `tableau10_classic` (matplotlib default — fall-back only)

```python
[
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728",
    "#9467BD", "#8C564B", "#E377C2", "#7F7F7F",
    "#BCBD22", "#17BECF",
]
```

Most-frequent hex `#1F77B4` (10/77 cases). Use only when 6+ groups required and no other palette fits; otherwise prefer the named muted variants above.

---

## 2. Sequential palettes (continuous magnitude)

### `viridis` (8/77 cases — most-used cmap)

For density-colored scatter, SHAP feature value low→high, importance gradient. **Always with `edgecolor='white'` on markers** when overlaying — this is the white-edge trick (7/77).

```python
import matplotlib as mpl
cmap = mpl.colormaps["viridis"]
ax.scatter(x, y, c=feature_value, cmap=cmap, edgecolor="white", linewidth=0.4, s=20)
```

### `GnBu_r` (CEJ density+marginal halo)

Inverted GnBu — bright dense regions on top of dark sparse background. Use with **density-sort** so high-density points draw last.

```python
x_s, y_s, z_s = sort_by_density(x, y)
ax.scatter(x_s, y_s, c=z_s, cmap="GnBu_r", s=2, rasterized=True)
```

### `seq_cool_5`

```python
["#F7FBFF", "#D6EAF8", "#A9CCE3", "#5DADE2", "#21618C"]
```

For low→high categorical risk encoding (low/medium/high), survival risk strata.

### `seq_warm_5`

```python
["#FFF6E8", "#FBD38D", "#F6AD55", "#DD6B20", "#9C4221"]
```

For training metrics, error magnitude, expression intensity.

---

## 3. Diverging palettes (bipolar signal)

### `RdBu_r` (4/77 cases — second-most cmap after viridis)

For correlation matrix, SHAP value sign, ALE main effect. Always center at 0 and pass `vmin=-V, vmax=V` so white = neutral.

```python
import matplotlib as mpl
cmap = mpl.colormaps["RdBu_r"]
norm = mpl.colors.TwoSlopeNorm(vmin=-V, vcenter=0, vmax=V)
sns.heatmap(corr, cmap=cmap, norm=norm, annot=True, fmt=".2f")
```

### `coolwarm` (3/77 cases)

Alternative to RdBu_r. Slightly warmer reds. Use for engineering correlations.

### `bipolar_ALE`

```python
positive = "#C0504D"   # warm brick
negative = "#4F81BD"   # cool steel
zero_ref = "#888888"   # gray reference
```

Source: `期刊复刻：通过双侧棒棒糖图解析特征重要性与ALE主效应方向`. Use for: lollipop bars colored by sign of effect, ALE 1D dependence sign.

```python
colors = ['#C0504D' if v > 0 else '#4F81BD' for v in values]
ax.hlines(y=y_pos, xmin=0, xmax=values, color=colors, linewidth=2.5, zorder=1)
ax.scatter(values, y_pos, color=colors, s=80, edgecolor='white', zorder=2)
ax.axvline(0, color='#888888', linestyle='--', linewidth=1.0, zorder=0)
```

### `red_blue_correlation`

```python
upper_pos = "#B5403A"
upper_neg = "#3B6FB6"
neutral   = "#F7F7F7"
```

Source: `如何用 Python 完美复刻一张"红蓝气泡"相关性分析图`, `期刊复现：基于上三角局部填充饼图的相关性矩阵`. Use for: bubble correlation matrix with red=positive, blue=negative, size=|r|.

---

## 4. Semantic role bindings

These bindings are **the same across all 77 cases** — never invert them across panels in a single figure.

```python
palette_role_map = {
    # Comparison axis
    "control":          "#1F4E79",
    "treatment":        "#C8553D",
    "rescue":           "#4C956C",
    "vehicle":          "#6C757D",

    # Train/test split (time series PI, predicted vs actual)
    "train":            "#4C78A8",
    "test":             "#E45756",

    # Modeling diagnostic
    "actual":           "#1F4E79",     # cool anchor
    "observed":         "#1F4E79",
    "experimental":     "#1F4E79",
    "predicted":        "#C8553D",     # warm highlight
    "fitted":           "#C8553D",

    # Density and feature value
    "feature_low":      "<cool side of viridis>",
    "feature_high":     "<warm side of viridis>",

    # Correlation sign
    "negative_correlation": "#4F81BD",
    "positive_correlation": "#C0504D",

    # Pareto / optimization
    "optimal":          "#00A087",
    "pareto":           "#00A087",
    "dominated":        "#7F7F7F",

    # SHAP / ALE sign
    "shap_positive":    "#C0504D",
    "shap_negative":    "#4F81BD",

    # Risk encoding
    "low_risk":         "<lighter sequential>",
    "high_risk":        "<darker sequential>",

    # Genomics
    "up_regulated":     "<warm side of diverging>",
    "down_regulated":   "<cool side of diverging>",
}
```

## 5. White-edge marker trick

7/77 cases use `edgecolor='white', linewidth=0.4` on scatter to crisp up density-colored points. This is the cheapest readability multiplier in the corpus — apply by default whenever scatter is overlaid on a colored background or has `cmap=`.

```python
ax.scatter(x, y, c=values, cmap="viridis", s=20,
           edgecolor="white", linewidth=0.4, zorder=4)
```

## 6. Anti-palette: things to never use

| Anti-pattern | Frequency in corpus | Replace with |
|---|---|---|
| Default `tab10` rainbow for >5 groups | 0/77 (corpus actively avoids) | `morandi_sci_4` + marker shape |
| `jet` colormap | 1/77 (mistake case) | `viridis` or `RdBu_r` |
| Pure red `#FF0000` for >1 group | 0/77 | `#C8553D` or `#D73027` |
| Saturated rainbow palette | 0/77 | `cool_summer_4` or `npg_4` |
| Different color for same role across panels | 0/77 | bind via `palette_role_map` once |

## 7. Helpers contract

```python
def resolve_palette(name: str, n: int | None = None,
                    journalProfile: dict | None = None) -> list[str]:
    """Return a hex list for a named palette.

    name: any key from this file (e.g. 'nature_radar_dual', 'morandi_sci_4').
    n:    if given, truncate or cycle to length n.
    journalProfile: if provides palette overrides, those win.

    Raises KeyError when the name is not in the bank — callers MUST NOT
    silently fall back to matplotlib defaults; the goal is determinism.
    """
```

```python
def role_color(role: str, palette: list[str] | None = None) -> str:
    """Lookup a semantic role from palette_role_map and return the hex.
    palette is used only when the mapping references the active palette
    (e.g. feature_low → palette[0])."""
```

## 8. Source anchors (validated against case-index.json)

Hex codes in this file all appear in **at least one** of the 77 cases. The most-used hex codes corpus-wide (≥2 cases):

| Hex | Cases | Used as |
|---|---|---|
| `#1F77B4` | 10 | tableau default; multi-model bars |
| `#D62728` | 6 | tableau default; warning/optimal accent |
| `#313695`, `#A50026` | 2 each | RdBu/seismic palette anchors |
| `#4C72B0`, `#4B74B2`, `#4A90E2` | 2 each | seaborn-style cool blue |
| `#808080` | 2 | reference gray |
| `#FF7F0E` | 2 | tableau default; secondary highlight |

To regenerate the full ranked list: see `_extraction/stats.md` § "Top 60 palette hex codes".
