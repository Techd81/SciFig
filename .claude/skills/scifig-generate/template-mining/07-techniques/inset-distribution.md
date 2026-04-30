# Technique: Inset Distribution / 画中画

8/77 corpus cases. The "main panel + small inset" pattern that conveys both the trend and the underlying distribution in a single axes.

**Anchor cases:**
- `复现顶刊 _ Python绘制"主图+嵌入雨云图"组合，完美展示模型泛化能力_1777452243`
- `期刊复现：Nature Nanotechnology 经典"画中画"组合图_1777450514`
- `期刊配图：云雨图结合半小提琴与抖动散点展示不同城市化水平的通量差异_1777454339`

## Hallmark elements

1. **Main panel** = primary trend / scatter / time series (independent narrative)
2. **Inset** = secondary perspective (raincloud, mini-violin, distribution histogram, zoom-in)
3. **Inset position** `[0.55, 0.35, 0.40, 0.35]` axes fraction (corpus default — right-center)
4. **Opaque white inset background** so it visually sits "above" the main plot
5. **Thin dark inset border** (~0.8 lw, `#222`)
6. **`zorder=10+`** on the inset itself; inside the inset, restart from `zorder=0`
7. **Main legend stays in main panel**; inset has no legend

## Full reference: Main scatter + raincloud inset

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from scipy.stats import gaussian_kde

# === Kernel ===
plt.rcParams.update({
    'font.family':      ['Times New Roman', 'Arial', 'DejaVu Sans'],
    'mathtext.fontset': 'stix',
    'font.size':        6.5,
    'axes.linewidth':   1.5,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})

# === Data ===
np.random.seed(0)
x      = np.arange(20)
y_true = 2.0 + 0.3 * x + np.random.normal(0, 0.5, 20)
y_pred = 2.0 + 0.3 * x + np.random.normal(0, 0.7, 20)
residuals = y_pred - y_true                  # for the inset distribution

ORANGE = '#FFA500'
GREEN  = '#008000'

# === Main panel ===
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, y_true, color=ORANGE, marker='s', markersize=7,
        linewidth=2.0, label='Actual', zorder=3)
ax.plot(x, y_pred, color=GREEN,  marker='o', markersize=7,
        linewidth=2.0, label='Predicted', zorder=4)
ax.fill_between(x, y_true, y_pred,
                color='#888888', alpha=0.15, linewidth=0, zorder=2,
                label='Residual band')
ax.set_xlabel('Sample index', fontsize=7)
ax.set_ylabel('Value', fontsize=7)
ax.legend(loc='upper left', frameon=False, fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# === Inset: raincloud (half-violin + box + jitter) ===
inset_rect = [0.55, 0.55, 0.40, 0.35]        # x, y, width, height (axes frac)
ax_ins = ax.inset_axes(inset_rect, zorder=10)
ax_ins.set_facecolor('white')
ax_ins.patch.set_alpha(0.95)
for sp in ax_ins.spines.values():
    sp.set_linewidth(0.8); sp.set_color('#222')

# === Half-violin (KDE shape) ===
kde = gaussian_kde(residuals)
v_y = np.linspace(residuals.min() - 0.5, residuals.max() + 0.5, 200)
v_x = kde(v_y)
v_x = v_x / v_x.max() * 0.4                  # normalize width
ax_ins.fill_betweenx(v_y, 0, v_x, color=GREEN, alpha=0.4, linewidth=0, zorder=1)
ax_ins.plot(v_x, v_y, color=GREEN, linewidth=1.5, zorder=2)

# === Box (right-of-violin) ===
q1, med, q3 = np.percentile(residuals, [25, 50, 75])
iqr = q3 - q1
whisker_lo = max(residuals.min(), q1 - 1.5 * iqr)
whisker_hi = min(residuals.max(), q3 + 1.5 * iqr)
box_x = 0.5
ax_ins.add_patch(plt.Rectangle((box_x - 0.05, q1), 0.10, q3 - q1,
                               facecolor='white', edgecolor=GREEN,
                               linewidth=1.2, zorder=3))
ax_ins.plot([box_x - 0.05, box_x + 0.05], [med, med],
            color=GREEN, linewidth=2, zorder=4)
ax_ins.plot([box_x, box_x], [whisker_lo, q1], color=GREEN, linewidth=1, zorder=3)
ax_ins.plot([box_x, box_x], [q3, whisker_hi], color=GREEN, linewidth=1, zorder=3)

# === Jitter scatter (right of box) ===
rng = np.random.default_rng(42)
jx = box_x + 0.15 + rng.random(len(residuals)) * 0.15
ax_ins.scatter(jx, residuals, s=15, color=GREEN, alpha=0.5,
               edgecolor='white', linewidth=0.3, zorder=5)

ax_ins.axhline(0, color='black', linestyle='--', linewidth=0.8, zorder=4)
ax_ins.set_xlim(0, 0.85)
ax_ins.set_xticks([])
ax_ins.set_ylabel('Residual', fontsize=10)
ax_ins.tick_params(labelsize=9)
ax_ins.set_title('Residual distribution', fontsize=10, pad=4)

plt.tight_layout()
plt.savefig('inset_distribution.pdf', dpi=600, bbox_inches='tight')
```

## Variant: Zoom-in inset on cluster region

For "main scatter + zoomed cluster" (Nature Nanotechnology style):

```python
ax.scatter(x_all, y_all, c='#888', s=15, alpha=0.4, zorder=2)
ax.scatter(x_cluster, y_cluster, c='#C8553D', s=30, alpha=0.8,
           edgecolor='white', linewidth=0.4, zorder=4)

# Inset on the right showing zoomed cluster
ax_ins = ax.inset_axes([0.60, 0.55, 0.35, 0.35], zorder=10)
ax_ins.scatter(x_cluster, y_cluster, c='#C8553D', s=60,
               edgecolor='white', linewidth=0.6, zorder=4)
ax_ins.set_xlim(x_cluster.min() - 0.1, x_cluster.max() + 0.1)
ax_ins.set_ylim(y_cluster.min() - 0.1, y_cluster.max() + 0.1)
ax_ins.set_facecolor('white')
ax_ins.patch.set_alpha(0.97)
for sp in ax_ins.spines.values():
    sp.set_linewidth(0.8); sp.set_color('#222')

# Connector lines to indicate the zoom
ax.indicate_inset_zoom(ax_ins, edgecolor='#222', linewidth=0.8, alpha=0.6)
```

Anchor: `期刊复现：Nature Nanotechnology 经典"画中画"组合图`.

## Variant: Three-distribution inset (city-gradient flux)

For raincloud comparing N conditions inside the inset:

```python
ax_ins = ax.inset_axes([0.05, 0.55, 0.40, 0.40], zorder=10)
positions = np.arange(len(conditions))
colors = ['#4A6B8A', '#5FA896', '#D9A75A']

for i, (cond, color) in enumerate(zip(conditions, colors)):
    data = subgroups[cond]
    # Half-violin
    kde = gaussian_kde(data)
    yy = np.linspace(data.min(), data.max(), 200)
    xx = kde(yy); xx = xx / xx.max() * 0.35
    ax_ins.fill_betweenx(yy, i, i + xx, color=color, alpha=0.4, zorder=1)
    # Strip jitter
    jx = (np.random.random(len(data)) - 0.5) * 0.15 + i - 0.20
    ax_ins.scatter(jx, data, s=10, color=color, alpha=0.6,
                   edgecolor='white', linewidth=0.2, zorder=4)
```

Anchor: `期刊配图：云雨图结合半小提琴与抖动散点展示不同城市化水平的通量差异`.

## Discipline rules

| Rule | Reason |
|---|---|
| Inset position `[0.55, 0.35, 0.40, 0.35]` (right-center) is corpus default | Empirical — least conflict with main legend top-left |
| Opaque white inset background (alpha 0.95+) | Sits visually above main plot |
| Thin dark border (`#222`, lw 0.8) | Inset identity; not heavy frame |
| `zorder=10` on inset; restart 0–9 inside | Avoids accidental overlap with main artists |
| No inset legend | Title or sub-axis label conveys context |
| Inset font 9–10pt (smaller than main 13–14pt) | Visual hierarchy |
| Inset title at `pad=4` (close to top) | Compactness |

## Position alternatives

When right-center conflicts with main data:

| Position | Rect | When |
|---|---|---|
| Right-center (default) | `[0.55, 0.35, 0.40, 0.35]` | Main data clusters bottom-left |
| Right-top | `[0.55, 0.55, 0.40, 0.35]` | Main legend at top-left, data spread |
| Top-left | `[0.05, 0.55, 0.35, 0.40]` | Right side busy; data clusters bottom |
| Bottom-right | `[0.55, 0.05, 0.40, 0.30]` | Top reserved for title/main legend |

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Inset transparent → blends with main plot | `set_facecolor('white')`, `patch.set_alpha(0.95)` |
| Inset with default zorder | Sits *under* main artists; explicitly `zorder=10` |
| Inset legend duplicates main | Remove inset legend, use title or short ax label |
| Inset axis labels too large | Use `fontsize=9–10`, `tick_params(labelsize=9)` |
| Inset border too thick | `lw=0.8`, color `#222` (not pure black) |

## QA contract

- `insetZorderAtLeast`: 10
- `insetOpaqueBackground`: True (`patch.alpha ≥ 0.9` and `facecolor='white'`)
- `insetBorderApplied`: spine width 0.6–1.0, color in dark gray range
- `noInsetLegend`: True
- `insetFontSizeSmaller`: inset font ≤ main font - 3pt
