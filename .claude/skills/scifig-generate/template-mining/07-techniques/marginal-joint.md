# Technique: Marginal Joint (center scatter + top/right marginals)

5/77 corpus cases. Density scatter or predicted-vs-actual diagnostic with side distributions.

**Anchor cases:**
- `复现 CEJ 顶刊神图_Python 绘制"密度散点+边缘直方图"多面板组合图_1777452838`
- `Python绘图实战：基于GridSpec构建多面板回归预测与边缘分布组合图_1777453032`
- `期刊复现：联合等高线热图与边缘分布图_1777454914`
- `期刊复现：通过带边缘密度的联合残差图_1777454731`

## Hallmark elements

1. **Center panel** = density-colored scatter or contour KDE, density-sorted
2. **Top panel** = histogram of x; height-only, no scaffolding
3. **Right panel** = histogram of y rotated 90°; same color
4. **Perfect-fit diagonal** in center if predicted-vs-actual
5. **Marginal axes off** (`axis('off')`)
6. **Equal aspect ratio** in center panel
7. **Colorbar** on the side, labeled "Density"

## Reference (CEJ-style)

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde

plt.rcParams.update({
    'font.family':      ['Times New Roman', 'Arial'],
    'mathtext.fontset': 'stix',
    'font.size':        14,
    'axes.linewidth':   1.5,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})

# Data: predicted vs actual
np.random.seed(0)
N = 1500
y_actual = np.random.uniform(0, 100, N)
y_pred   = y_actual + np.random.normal(0, 8, N)

# === Density-sort ===
xy = np.vstack([y_actual, y_pred])
z  = gaussian_kde(xy)(xy)
idx = z.argsort()
y_actual_s = y_actual[idx]; y_pred_s = y_pred[idx]; z_s = z[idx]

# === Layout ===
fig = plt.figure(figsize=(8, 8))
gs  = GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
               hspace=0.05, wspace=0.05)
ax_top   = fig.add_subplot(gs[0, 0])
ax_main  = fig.add_subplot(gs[1, 0])
ax_right = fig.add_subplot(gs[1, 1])
ax_corner = fig.add_subplot(gs[0, 1]); ax_corner.axis('off')

# === Center: density scatter ===
sc = ax_main.scatter(y_actual_s, y_pred_s, c=z_s, cmap='GnBu_r',
                     s=8, alpha=0.85, edgecolor='white',
                     linewidth=0.2, rasterized=True, zorder=4)
# Perfect-fit diagonal
lo, hi = min(y_actual.min(), y_pred.min()), max(y_actual.max(), y_pred.max())
pad = (hi - lo) * 0.05
ax_main.plot([lo - pad, hi + pad], [lo - pad, hi + pad],
             'k--', linewidth=1.2, alpha=0.6, zorder=6)
ax_main.set_xlim(lo - pad, hi + pad); ax_main.set_ylim(lo - pad, hi + pad)
ax_main.set_aspect('equal')
ax_main.set_xlabel('Actual')
ax_main.set_ylabel('Predicted')
ax_main.spines['top'].set_visible(False)
ax_main.spines['right'].set_visible(False)

# === Top marginal ===
ax_top.hist(y_actual, bins=60, density=True,
            color='#69b3a2', alpha=0.7, edgecolor='none', zorder=1)
ax_top.axis('off')

# === Right marginal ===
ax_right.hist(y_pred, bins=60, density=True, orientation='horizontal',
              color='#69b3a2', alpha=0.7, edgecolor='none', zorder=1)
ax_right.axis('off')

# === Colorbar ===
cax = fig.add_axes([0.93, 0.18, 0.012, 0.50])
cbar = fig.colorbar(sc, cax=cax)
cbar.set_label('Density', fontsize=11)

# === Metric box on center ===
r2  = 1 - np.sum((y_actual - y_pred)**2) / np.sum((y_actual - y_actual.mean())**2)
rmse = np.sqrt(np.mean((y_actual - y_pred)**2))
ax_main.text(0.05, 0.95, f"$R^2 = {r2:.3f}$\nRMSE = {rmse:.2f}",
             transform=ax_main.transAxes, va='top', ha='left',
             fontsize=12, fontweight='bold',
             bbox=dict(boxstyle='square,pad=0.4', fc='white', ec='black', lw=0.8),
             zorder=20)

plt.savefig('marginal_joint.pdf', dpi=600, bbox_inches='tight')
```

## Variant: Joint contour heatmap

Replace center scatter with `contourf` of 2D KDE for smooth bivariate density.

```python
xx, yy = np.meshgrid(np.linspace(lo, hi, 100), np.linspace(lo, hi, 100))
positions = np.vstack([xx.ravel(), yy.ravel()])
zz = gaussian_kde(np.vstack([y_actual, y_pred]))(positions).reshape(xx.shape)
cf = ax_main.contourf(xx, yy, zz, levels=12, cmap='GnBu_r', zorder=3)
ax_main.contour(xx, yy, zz, levels=12, colors='white', linewidths=0.4, zorder=4)
```

Anchor: `期刊复现：联合等高线热图与边缘分布图`.

## Variant: `make_axes_locatable` (cleaner code)

```python
from mpl_toolkits.axes_grid1 import make_axes_locatable

fig, ax_main = plt.subplots(figsize=(7, 7))
divider = make_axes_locatable(ax_main)
ax_top   = divider.append_axes("top",   size="20%", pad=0.05, sharex=ax_main)
ax_right = divider.append_axes("right", size="20%", pad=0.05, sharey=ax_main)
ax_top.tick_params(labelbottom=False)
ax_right.tick_params(labelleft=False)
```

Cleaner but less control over corner panel. Use for pure marginal-joint without colorbar inside.

## Discipline rules

| Rule | Reason |
|---|---|
| Density-sort the center scatter | Bright dense regions paint last |
| `rasterized=True` on dense scatter | Keep PDF under 5MB |
| Marginal axes `axis('off')` | They're decoration, not data |
| Same color for both marginals | They show the same population |
| Center `set_aspect('equal')` when predicted-vs-actual | Diagonal is meaningful |
| Colorbar separate `add_axes` outside the grid | Don't steal width from main |
| `wspace=hspace=0.05` between marginals and main | Tight composition |

## QA contract

- `marginalAxesCount`: 2
- `densityColorEncodingCount`: ≥1 in center
- `marginalAxesOff`: True (`axis('off')` applied)
- `centerAspectEqual`: True for predicted-vs-actual
- `perfectFitCount`: ≥1 for predicted-vs-actual
