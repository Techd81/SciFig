# Technique: Radar / Polar Comparison

6/77 corpus cases. The signature aesthetic of `Nature Vol 626 Fig 3c` (semiconductor fibre) — replicated across the corpus.

**Anchor cases:**
- `绝美！Nature 这张雷达图_1777449664` — the canonical Nature reference
- `顶刊复刻 _ 这种"中心挖空"+"立体高光"的雷达图_1777451060`
- `期刊配图：基于极坐标系的多面板雷达图对比多维环境变量与模型表现_1777454388`
- `期刊复现 _ Python绘制"镜像玫瑰"组合图_1777452890` (mirror radial)

## Hallmark elements (all-of)

1. **Polygon dashed grid** instead of default circular polar
2. **Sandwich layering**: translucent fill (L1) + outline (L2) + error-bar markers (L4)
3. **Two-color bipolar palette** (`#1F3A5F` Navy + `#C8553D` Crimson)
4. **Times New Roman 16pt + axes.linewidth 1.5**
5. **Closed-loop angle array** (append first angle to end so polygon closes)
6. **Axis-by-axis normalization to [0, 1]** (different physical units)

## Full reference implementation

```python
import matplotlib.pyplot as plt
import numpy as np
from math import pi

# === Step 1. Apply the kernel (variant=polar) ===
plt.rcParams.update({
    'font.family':       ['Times New Roman', 'Arial', 'DejaVu Sans'],
    'mathtext.fontset':  'stix',
    'font.size':         7.0,
    'axes.linewidth':    1.5,
    'xtick.direction':   'in',
    'ytick.direction':   'in',
    'grid.linestyle':    '--',
    'grid.alpha':        0.5,
    'savefig.bbox':      'tight',
    'savefig.dpi':       600,
})

# === Step 2. Define axis configuration with physical limits ===
axis_config = {
    'Responsivity':       {'limit': 0.5},
    'NEP':                {'limit': 8.0},
    'Rise time':          {'limit': 4.0},
    '3-dB bandwidth':     {'limit': 400.0},
    'Yield strength':     {'limit': 100.0},
    'Impact strength':    {'limit': 8.0},
    'Torsional strength': {'limit': 360.0},
}
labels  = list(axis_config.keys())
limits  = [axis_config[k]['limit'] for k in labels]
n_axes  = len(labels)

# === Step 3. Closed-loop angles ===
angles = [i / n_axes * 2 * pi for i in range(n_axes)]
angles += angles[:1]                         # CRITICAL: close the loop

# === Step 4. Per-condition normalized values ===
def normalize(values, limits):
    """Map physical values to [0, 1] using per-axis limits."""
    norm = [v / l for v, l in zip(values, limits)]
    return norm + norm[:1]                   # close

raw_ge = [0.45, 7.2, 3.6, 380, 95, 6.8, 340]
raw_si = [0.31, 5.4, 1.8, 215, 78, 4.5, 200]
err_ge = [0.04, 0.5, 0.3, 25, 6, 0.4, 25]
err_si = [0.03, 0.4, 0.2, 20, 5, 0.3, 18]

values_ge = normalize(raw_ge, limits)
values_si = normalize(raw_si, limits)

# === Step 5. Figure + polar axis ===
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, polar=True)

# === Step 6. Polygon dashed grid (replace circular default) ===
ax.spines['polar'].set_visible(False)
ax.grid(False)
for level in [0.25, 0.5, 0.75, 1.0]:
    ax.plot(angles, [level] * len(angles),
            color='black', linestyle='--', linewidth=0.8,
            alpha=0.6, zorder=0)
# radial spokes
for ang in angles[:-1]:
    ax.plot([ang, ang], [0, 1.0], color='black',
            linewidth=0.6, alpha=0.4, zorder=0)

# === Step 7. Sandwich layers (per condition) ===
def plot_condition(ax, angles, values, errors, color, label):
    ax.fill(angles, values, color=color, alpha=0.15, zorder=1)        # L1 cushion
    ax.plot(angles, values, color=color, linewidth=2.5,
            label=label, zorder=5)                                     # L2 wrapper
    err_norm = [e / l for e, l in zip(errors, limits)]
    ax.errorbar(angles[:-1], values[:-1], yerr=err_norm,
                fmt='o', color=color, markersize=8, capsize=4,
                elinewidth=1.5, zorder=10)                             # L4 markers

NAVY    = '#1F3A5F'
CRIMSON = '#C8553D'
plot_condition(ax, angles, values_ge, err_ge, NAVY,    'Ge fibre')
plot_condition(ax, angles, values_si, err_si, CRIMSON, 'Si fibre')

# === Step 8. Tick labels ===
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, fontsize=12)
ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(['', '', '', ''])         # hide radial numbers
ax.set_ylim(0, 1.05)

# === Step 9. Axis-physical-limit annotation (optional but Nature-style) ===
for i, (label, lim) in enumerate(zip(labels, limits)):
    angle_rad = angles[i]
    ax.text(angle_rad, 1.18, f"max={lim}",
            ha='center', va='center', fontsize=9, color='#555')

# === Step 10. Legend outside ===
ax.legend(loc='upper right', bbox_to_anchor=(1.20, 1.10),
          frameon=False, fontsize=12)

plt.tight_layout()
plt.savefig('radar_nature.pdf', dpi=600, bbox_inches='tight')
plt.show()
```

## Mirror radial variant

For two conditions in true mirror layout (one filling outward, the other inward):

```python
# Condition A: outward (positive radial direction)
ax.bar(angles[:-1], values_a, width=2*pi/n_axes,
       color=NAVY, alpha=0.7, edgecolor='white',
       linewidth=1.2, zorder=5)

# Condition B: inward (negative radial via offset)
ax.bar(angles[:-1], -values_b, width=2*pi/n_axes,
       color=CRIMSON, alpha=0.7, edgecolor='white',
       linewidth=1.2, zorder=5, bottom=0)

# Center hole
ax.set_rorigin(-0.3)
ax.set_rmin(-1.0)
```

Anchor: `期刊复现 _ Python绘制"镜像玫瑰"组合图`.

## Center-hollow variant

For radar with hollow center (`#中心挖空`):

```python
ax.set_rorigin(-0.2)                         # negative = center void
ax.set_rmin(0)
# Add a circle annotation at center to fill visually
center = plt.Circle((0, 0), 0.15, transform=ax.transData._b,
                    facecolor='white', edgecolor='black', linewidth=1.5,
                    zorder=15)
ax.add_artist(center)
```

Anchor: `顶刊复刻 _ "中心挖空"+"立体高光"的雷达图`.

## Multi-panel radar (subplot grid)

Use `R3_two_by_three_grid` for 6-feature radar comparison or `R5_n_by_n_pairwise` for ablation panels.

```python
fig = plt.figure(figsize=(15, 9))
gs  = gridspec.GridSpec(2, 3, hspace=0.40, wspace=0.30)
for k in range(6):
    ax = fig.add_subplot(gs[k // 3, k % 3], polar=True)
    # ... apply polygon-grid + sandwich layers ...
```

Anchor: `期刊配图：基于极坐标系的多面板雷达图对比多维环境变量与模型表现`.

## Common pitfalls

| Pitfall | Why bad | Fix |
|---|---|---|
| Default circular polar grid | Looks "Excel" | Hide + draw polygon dashed grid |
| Forgetting to close angle array | Last segment missing | Append `angles[:1]` after building |
| Same color for both conditions | Cannot distinguish overlap | Use bipolar palette `nature_radar_dual` |
| Filling at full alpha 1.0 | Hides grid + other condition | Alpha 0.15 for fill, full alpha for outline |
| Showing radial number ticks | Clutters | Hide via `set_yticklabels(['',]*4)` |

## QA contract

Phase 4 render-qa requires for radar charts:
- `polarGridReplaced`: True (must hide circular grid + add polygon)
- `closedLoopAngles`: True (last angle equals first)
- `sandwichLayerCount`: ≥3 (fill + outline + markers)
- `paletteIsBipolar`: True if 2-condition radar (auto-detect via category count)
