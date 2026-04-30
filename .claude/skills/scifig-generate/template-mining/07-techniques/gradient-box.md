# Technique: Gradient Box

1/77 corpus case (distinctive technique). Vertical-gradient fill inside box-plot rectangles via `imshow` overlay.

**Anchor case:** `顶刊审美 _ 用 Python 绘制带"垂直渐变特效"的组合箱线图_1777451428`.

## Hallmark elements

1. **Imshow gradient** inside each box rectangle
2. **Median line** drawn separately (overlaid with `zorder=3`)
3. **Whiskers** plotted as plain lines (`zorder=2`)
4. **Mean marker** as colored square (`zorder=4`, `marker='s'`)
5. **Hollow jitter scatter** behind the box (`zorder=1`)
6. **Light dashed grid** on y-axis only

## Reference

```python
import matplotlib.pyplot as plt
import matplotlib.colors as mc
import numpy as np

plt.rcParams.update({
    'font.family':      ['Arial', 'Times New Roman'],
    'mathtext.fontset': 'stix',
    'font.size':        6.5,
    'axes.linewidth':   1.2,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})

def draw_gradient_box(ax, x, q1, width, height, color, *, alpha_lo=0.15, alpha_hi=0.95, zorder=2):
    """Fill a rectangle with vertical gradient color."""
    rgba = mc.to_rgba(color)
    alphas = np.linspace(alpha_lo, alpha_hi, 256)
    colors = np.array([(rgba[0], rgba[1], rgba[2], a) for a in alphas])
    cmap = mc.LinearSegmentedColormap.from_list('grad', colors)
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    ax.imshow(grad, extent=(x, x + width, q1, q1 + height),
              aspect='auto', origin='lower', cmap=cmap, zorder=zorder)
    rect = plt.Rectangle((x, q1), width, height, fill=False,
                         edgecolor=color, linewidth=1.2, zorder=zorder + 1)
    ax.add_patch(rect)


# Data
np.random.seed(0)
groups = ['Control', 'Treat A', 'Treat B', 'Treat C']
data = [np.random.normal(loc=10 + i*2, scale=2, size=80) for i in range(4)]
colors = ['#4A6B8A', '#5FA896', '#D9A75A', '#B85B5B']

fig, ax = plt.subplots(figsize=(8, 5.5))

# === Light dashed y-grid (L0) ===
ax.yaxis.grid(True, linestyle='--', color='#E0E0E0', linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

box_w = 0.5
for i, (data_i, color) in enumerate(zip(data, colors)):
    q1, med, q3 = np.percentile(data_i, [25, 50, 75])
    iqr = q3 - q1
    whisker_lo = max(data_i.min(), q1 - 1.5 * iqr)
    whisker_hi = min(data_i.max(), q3 + 1.5 * iqr)

    # === L1: hollow jitter scatter ===
    jx = i + (np.random.random(len(data_i)) - 0.5) * 0.30
    ax.scatter(jx, data_i, s=18, facecolors='none',
               edgecolors=color, alpha=0.6, linewidth=0.6, zorder=1)

    # === L2: gradient box ===
    draw_gradient_box(ax, i - box_w/2, q1, box_w, q3 - q1, color, zorder=2)

    # === L2: whiskers ===
    ax.plot([i, i], [whisker_hi, q3], color=color, lw=1.2, zorder=2)
    ax.plot([i, i], [whisker_lo, q1], color=color, lw=1.2, zorder=2)
    ax.plot([i - 0.15, i + 0.15], [whisker_hi, whisker_hi], color=color, lw=1.2, zorder=2)
    ax.plot([i - 0.15, i + 0.15], [whisker_lo, whisker_lo], color=color, lw=1.2, zorder=2)

    # === L3: median line ===
    ax.plot([i - box_w/2, i + box_w/2], [med, med],
            color=color, lw=2.2, zorder=3)

    # === L4: mean marker (square) ===
    ax.plot(i, data_i.mean(), marker='s', mfc='#F06292', mec='#C2185B',
            markersize=8, zorder=4)

ax.set_xticks(range(len(groups)))
ax.set_xticklabels(groups, fontsize=12)
ax.set_ylabel('Value', fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.savefig('gradient_box.pdf', dpi=600, bbox_inches='tight')
```

## Discipline rules

- Median line `lw=2.2` (slightly thicker than whiskers)
- Mean marker as **pink square** to contrast group color
- Jitter scatter is **hollow** so it doesn't compete with the gradient
- Y-grid `axisbelow=True` so it sits below all artists
- Gradient `alpha_lo=0.15, alpha_hi=0.95` — bottom translucent, top opaque

## QA contract

- `gradientBoxImshow`: True (`imshow` call inside box rectangle)
- `medianLineCount`: 1 per group
- `meanMarkerCount`: 1 per group
- `boxLayerCount`: ≥4 (jitter, gradient, whiskers, median, mean)
