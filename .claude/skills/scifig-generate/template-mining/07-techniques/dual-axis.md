# Technique: Dual-Axis Combo

19/77 corpus cases. Pairs a left-axis quantity (typically context: porosity, count, distribution) with a right-axis quantity (typically focal: strength, accuracy, score) on a shared x-axis.

**Anchor cases:**
- `如何用Python绘制教科书级的双Y轴组合图_1777451702`
- `期刊复现：Nature Comms 双Y轴组合图_1777450693`
- `期刊复现：双Y轴分组柱状与折线组合图评估多模型预测性能_1777455934`
- `期刊图表：双Y轴直方图与累积频率曲线展示HPC数据集多变量分布特征_1777454431`
- `期刊配图复现 _ Python绘制"趋势+分布"时序混合图_1777451814`

## Hallmark elements

1. **Bar on left axis** (context, typically light blue/gray)
2. **Line + markers on right axis** (focal, typically warm color)
3. **Tinted spines** matching data color
4. **Smooth-spline interpolation** of the right-axis line (cubic spline or Bézier)
5. **Group dividers** (`axvline` dashed gray) when categorical x splits into groups
6. **Error bars** on both axes when error columns supplied

## Full reference implementation

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

# === Apply the kernel (variant=hero) ===
plt.rcParams.update({
    'font.family':       ['Times New Roman', 'Arial', 'DejaVu Sans'],
    'mathtext.fontset':  'stix',
    'font.size':         16,
    'axes.linewidth':    1.5,
    'xtick.direction':   'in',
    'ytick.direction':   'in',
    'savefig.bbox':      'tight',
    'savefig.dpi':       600,
})

# === Data ===
labels    = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']
porosity  = np.array([8.2, 7.5, 6.8, 5.2, 4.7, 4.1, 3.4, 2.9, 2.5])
porosity_err = np.array([0.4, 0.4, 0.3, 0.3, 0.3, 0.2, 0.2, 0.2, 0.1])
strength  = np.array([42, 48, 56, 67, 72, 78, 82, 88, 94])
strength_err = np.array([3, 4, 4, 5, 5, 5, 6, 6, 6])

x = np.arange(len(labels))

# === Color palette (Materials Today porosity-terracotta) ===
BAR_FACE   = '#CFE2F3'    # soft sky
BAR_EDGE   = '#9BC2E6'
LINE_COLOR = '#F48E66'    # terracotta

# === Figure + twin axes ===
fig, ax1 = plt.subplots(figsize=(10, 5.5))
ax2 = ax1.twinx()

# === L1: bars on ax1 (background) ===
ax1.bar(x, porosity, width=0.65, yerr=porosity_err,
        capsize=5, color=BAR_FACE, edgecolor=BAR_EDGE,
        linewidth=1.5, error_kw={'linewidth': 1.0, 'ecolor': '#666'},
        zorder=2, label='Porosity (%)')

# === L2: group divider lines ===
group_splits = [2.5, 5.5]
for x_split in group_splits:
    ax1.axvline(x=x_split, color='gray', linestyle='--',
                linewidth=1.5, alpha=0.6, zorder=1)

# === L3: smooth spline line on ax2 ===
x_smooth = np.linspace(x.min(), x.max(), 200)
spline   = make_interp_spline(x, strength, k=3)
y_smooth = spline(x_smooth)
ax2.plot(x_smooth, y_smooth, color=LINE_COLOR, linewidth=2.8,
         zorder=3, label='Strength (MPa)')

# === L4: data markers + error bars on ax2 (top) ===
ax2.errorbar(x, strength, yerr=strength_err, fmt='o',
             color=LINE_COLOR, markersize=10, capsize=5,
             elinewidth=2, markeredgecolor='white',
             markeredgewidth=0.8, zorder=4)

# === Tinted spines + ticks per axis (the dual-axis tell) ===
ax1.spines['left'].set_color(BAR_EDGE);   ax1.spines['left'].set_linewidth(2)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.tick_params(axis='y', colors=BAR_EDGE)
ax1.set_ylabel('Porosity (%)', color=BAR_EDGE, fontsize=14)

ax2.spines['right'].set_color(LINE_COLOR); ax2.spines['right'].set_linewidth(2)
ax2.spines['top'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.tick_params(axis='y', colors=LINE_COLOR)
ax2.set_ylabel('Strength (MPa)', color=LINE_COLOR, fontsize=14)

# === Group labels above the dividers ===
group_centers = [(0+1+2)/3, (3+4+5)/3, (6+7+8)/3]
group_names   = ['Family A', 'Family B', 'Family C']
y_top = ax1.get_ylim()[1] * 1.05
for cx, name in zip(group_centers, group_names):
    ax1.text(cx, y_top, name, ha='center', va='bottom',
             fontsize=12, fontweight='bold', color='#444')

# === X-axis ticks ===
ax1.set_xticks(x)
ax1.set_xticklabels(labels, rotation=0)

# === Legend (combined from both axes) ===
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper left',
           bbox_to_anchor=(0.02, 0.98), frameon=False,
           fontsize=11)

plt.tight_layout()
plt.savefig('dual_axis.pdf', dpi=600, bbox_inches='tight')
```

## Variant: Histogram + cumulative frequency

For distributional dual-axis (HPC data analysis case):

```python
ax1.bar(bin_centers, counts, width=bin_width*0.9,
        color='#9CC4E4', edgecolor='#3B6FB6', alpha=0.7, zorder=2)
ax1.set_ylabel('Count', color='#3B6FB6')

ax2.plot(bin_centers, cumfreq, color='#B5403A', linewidth=2.5,
         marker='o', markersize=6, zorder=3)
ax2.set_ylabel('Cumulative %', color='#B5403A')
ax2.set_ylim(0, 105)
```

Anchor: `期刊图表：双Y轴直方图与累积频率曲线展示HPC数据集多变量分布特征`.

## Variant: Triple-Y axis (rare; 1 case in corpus)

When 3 quantities must share x:

```python
fig, ax1 = plt.subplots(figsize=(10, 5.5))
ax2 = ax1.twinx()
ax3 = ax1.twinx()
ax3.spines['right'].set_position(('outward', 60))    # offset 3rd axis

ax1.bar(x, y1, color=C1, zorder=2)
ax2.plot(x, y2, color=C2, linewidth=2.5, zorder=3)
ax3.plot(x, y3, color=C3, linewidth=2.5, linestyle='--', zorder=4)

# Tint each spine
for axx, side, color in [(ax1, 'left', C1), (ax2, 'right', C2), (ax3, 'right', C3)]:
    axx.spines[side].set_color(color); axx.spines[side].set_linewidth(2)
    axx.tick_params(axis='y', colors=color)
```

Anchor: `期刊配图复现 _ Matplotlib 挑战"多面板+三Y轴"组合图`.

## Variant: Grouped bars + line on twinx

When left axis has multiple categories (3-4 model errors as bars, right axis = R²):

```python
n_models = 4
width = 0.18
xs = np.arange(len(samples))

for i, model in enumerate(models):
    offset = (i - n_models/2 + 0.5) * width
    ax1.bar(xs + offset, errors[model], width=width,
            color=npg_4[i], edgecolor='white', linewidth=0.5,
            alpha=0.85, zorder=2, label=f'{model} error')

ax2.plot(xs, r2_scores, color='#1F1F1F', linewidth=2.5,
         marker='D', markersize=8, zorder=4, label='R² overall')
```

Anchor: `期刊复现：双Y轴分组柱状与折线组合图评估多模型预测性能`.

## Discipline rules

| Rule | Reason |
|---|---|
| Bars sit on left axis (context); line+markers on right axis (focal) | Bar = ground state, line = trend reader's eye follows |
| Tint each spine to its data color | Eliminates "which axis owns this?" ambiguity |
| Top spine always off | Reduce frame noise |
| When using spline, sample to 200 points then plot | Crisp curve, raw markers preserve data |
| Combine legends manually (`get_legend_handles_labels`) | matplotlib doesn't merge twin axes legends |
| Outer-only group labels above the figure | Inside-data text fights with bars |

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Both axes default black | Tint spines |
| Two legends (one per axis) | Manual merge |
| Bars and line same color | Use `materials_porosity_terracotta` palette |
| Right-axis ticks overlap left-axis labels | Increase right margin via `subplots_adjust` |
| Spline overshooting at ends | Use `bc_type='natural'` or clip values |

## QA contract

- `dualAxisSpineTinted`: each axis spine color matches its data color
- `combinedLegend`: only one legend visible
- `groupDividerCount`: ≥1 when categorical groups detected in x
- `topSpineHidden`: True
- `errorBarSymmetry`: error bars present on both axes when error columns supplied
