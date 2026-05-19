# Technique: Radar / Polar Comparison

8/94 corpus cases. The signature aesthetic of `Nature Vol 626 Fig 3c` (semiconductor fibre) — replicated across the corpus.

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

For two conditions in a mirror radial rose layout:

```python
angles_top = np.deg2rad([20, 55, 90, 125, 160])
angles_bottom = np.deg2rad([200, 235, 270, 305, 340])
ax.bar(angles_top, orig_top, width=0.45, color='#33CCFF', zorder=5)
ax.bar(angles_top, simp_top, width=0.45 * 0.7, color='#FFFF99', zorder=10)
ax.bar(angles_bottom, orig_bot, width=0.45, color='#33CCFF', zorder=5)
ax.bar(angles_bottom, simp_bot, width=0.45 * 0.7, color='#FFFF99', zorder=10)

# External scale bar: separate invisible axes, not polar radial tick labels.
ax_scale = fig.add_axes([0.05, 0.4, 0.02, 0.4])
```

### Executable mapping: mirror radial bar board

Route `visualContentPlan.templateMotifs` / `specialPatterns` containing
`mirror_radial_bar_board`, `mirror_radial`, or `mirror_rose` through
`gen_radar`.  The generator must call `draw_mirror_radial_bar_board(...)` and
mark `templateMotifsApplied` for:

- `mirror_radial_bar_board`
- `mirror_radial_bar`
- `external_scale_bar`

The transferable evidence is the top/bottom hemisphere condition split, the
two-width bar overlay (`#33CCFF` original base, `#FFFF99` simplified foreground),
model labels rotated to remain upright, and the external L-shape scale axis.

Case-088 audit note: the later queue pass over this Markdown was treated as
`duplicate_markdown_covered_by_case_023`; keep using the mirror-radial helper
instead of ordinary radar or single-condition polar bar templates.

## Center-hollow variant

Case 001 (`顶刊复刻 _ "中心挖空"+"立体高光"的雷达图`) is learned as a separate radar variant, not just a palette tweak. Its transferable essence is:

- Independent 2x2 polar panels, one metric per panel when scales differ strongly.
- A hollow visual origin: subtract a metric-specific center/baseline before plotting so small differences are magnified.
- Dashed polygon rings plus black spokes; never fall back to circular polar grid.
- Radial tick labels sit on one spoke, not around the whole circle.
- Vertex markers use a three-layer glass stack: colored base, soft white reflection, hard specular point.
- No in-plot legend; panel titles, line colors, and bottom-center shared legend carry the narrative.

Skill helpers:

```python
add_polygon_polar_grid(ax, angles_closed)
add_hollow_polar_center(ax)
add_polar_spoke_tick_labels(ax, tick_values, center=center, angle=angles[0])
scatter_glass_markers(ax, angles, radii, color=color)
```

For radar with hollow center (`#中心挖空`), either request the `hollow_polar_center` / `glass_marker_stack` template motifs or supply `chartPlan["radarAxisCenters"]`:

```python
ax.set_rorigin(-0.2)                         # negative = center void
ax.set_rmin(0)
# Add a circle annotation at center to fill visually
center = plt.Circle((0, 0), 0.15, transform=ax.transData._b,
                    facecolor='white', edgecolor='black', linewidth=1.5,
                    zorder=15)
ax.add_artist(center)
```

## Multi-panel radar (subplot grid)

Use `R3_two_by_three_grid` for 6-feature radar comparison or `R5_n_by_n_pairwise` for ablation panels.

```python
fig = plt.figure(figsize=(15, 9))
gs  = gridspec.GridSpec(2, 3, hspace=0.40, wspace=0.30)
for k in range(6):
    ax = fig.add_subplot(gs[k // 3, k % 3], polar=True)
    # ... apply polygon-grid + sandwich layers ...
```

Case-066 boundary: the article title says multi-panel, but the executable code
builds one polar axis. Learn it as an environment/model metric radar comparison
first, then scale to a multi-panel grid only when the prompt/data supplies
multiple basins, seasons, models, or ablation groups that require separate
polar axes.

Required environmental/model radar contract:

- Use one shared axis order for every condition and every panel.
- Normalize or require values on a common `[0, 1]` radial scale before comparing
  wet/dry seasons, basins, or model-performance profiles.
- Set `theta_offset=np.pi/2` and `theta_direction=-1` so the first metric starts
  at the top and proceeds clockwise.
- Close both the angle array and each condition value array by appending the
  first item.
- Draw condition outlines above translucent fills; alpha around `0.20-0.25`
  preserves overlap readability.
- Put the legend outside the polar axis (`upper right`, `bbox_to_anchor` near
  `(1.3, 1.1)`) when spoke labels are dense.

Case-066 acceptance signals: `axisName == "polar"`, `categoryCount == 6`,
`conditionCount == 2`, `closedLoopAngles == true`, `radialScale == [0, 1]`,
`fillCount == conditionCount`, `lineCount == conditionCount`,
`legendOutside == true`, and `exportDpi == 600`.

Evidence path:

## Manual cartesian model-metric radar

Use this when the source manually constructs a radar chart on a hidden
cartesian axes rather than using `projection="polar"`. This is still a radar
motif, but the implementation contract differs from the polar helpers.

Required manual-radar contract:

- Set equal aspect, fix x/y limits to `[0, 1]`, and hide the default axes.
- Store the radar center and outer radius as normalized figure coordinates.
- Compute spoke angles with an initial `pi / 2` offset so the first metric sits
  at the top.
- Draw dashed polygon grid levels by converting every spoke radius to x/y.
- Require an `axis_scales` min/max pair for every metric before normalizing
  model values.
- Clip normalized values only for visual overflow protection; do not silently
  rescale each model independently.
- Draw each model as a closed polygon line with marker vertices and a
  low-alpha fill.
- Add original-value labels near every vertex when the prompt asks for exact
  performance readability.
- Put long model legends at figure level outside the radar body.

## Common pitfalls

| Pitfall | Why bad | Fix |
|---|---|---|
| Default circular polar grid | Looks "Excel" | Hide + draw polygon dashed grid |
| Forgetting to close angle array | Last segment missing | Append `angles[:1]` after building |
| Same color for both conditions | Cannot distinguish overlap | Use bipolar palette `nature_radar_dual` |
| Filling at full alpha 1.0 | Hides grid + other condition | Alpha 0.15 for fill, full alpha for outline |
| Showing radial number ticks | Clutters | Hide via `set_yticklabels(['',]*4)` |
| Treating hollow-center radar as ordinary radar | Small differences collapse near the center | Supply `radarAxisCenters`, add center cutout, and label one spoke |
| Flat single-layer markers | Loses the pseudo-3D highlight from case 001 | Use `scatter_glass_markers(...)` for hollow-highlight motifs |
| Treating a single-axis article as mandatory multi-panel | Adds empty polar panels | Follow the code evidence first; scale to multiple polar axes only when separate groups require it |

## QA contract

Phase 4 render-qa requires for radar charts:
- `polarGridReplaced`: True (must hide circular grid + add polygon)
- `closedLoopAngles`: True (last angle equals first)
- `sandwichLayerCount`: ≥3 (fill + outline + markers)
- `paletteIsBipolar`: True if 2-condition radar (auto-detect via category count)
