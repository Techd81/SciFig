# Technique: Dual-Axis Combo

21/94 corpus cases. Pairs a left-axis quantity (typically context: porosity, count, distribution) with a right-axis quantity (typically focal: strength, accuracy, score) on a shared x-axis.

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
    'font.size':         7.0,
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
ax1.set_ylabel('Porosity (%)', color=BAR_EDGE, fontsize=7)

ax2.spines['right'].set_color(LINE_COLOR); ax2.spines['right'].set_linewidth(2)
ax2.spines['top'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.tick_params(axis='y', colors=LINE_COLOR)
ax2.set_ylabel('Strength (MPa)', color=LINE_COLOR, fontsize=7)

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

## Executable mapping: 3x3 histogram + cumulative-frequency grid

Anchor: `期刊图表：双Y轴直方图与累积频率曲线展示HPC数据集多变量分布特征`.

Use this for wide numeric materials / dataset-description tables where the
task asks for independent variable distributions rather than a single
categorical bar-line comparison. Each variable owns a panel; scales are not
shared across panels.

Phase-3 binding:

```python
result = draw_dual_axis_hist_cumfreq_grid(
    df,
    value_cols=["Cement", "BFS", "Fly Ash", "Water", "SP",
                "Coarse Agg", "Fine Agg", "Age", "Strength"],
    nrows=3,
    ncols=3,
    bins=15,
    figsize=(12, 10),
    wspace=0.40,
    hspace=0.35,
    hist_color="gray",
    hist_edgecolor="black",
    hist_alpha=0.70,
    line_color="blue",
)
```

Runtime path: `gen_dual_axis` must call
`draw_dual_axis_hist_cumfreq_grid` when `visualContentPlan` or
`specialPatterns` contains `dual_axis_hist_cumfreq_grid`,
`hist_cumfreq_grid`, or `cumulative_frequency_grid`.

QA signals: left axes gid `scifig_dual_axis_hist_cumfreq_left`, right axes gid
`scifig_dual_axis_hist_cumfreq_right`, histogram patch gid
`scifig_dual_axis_histogram_bar`, cumulative line gid
`scifig_dual_axis_cumulative_frequency_line`, `twinAxisPanelCount == 9`,
`histogramPanelCount == 9`, `cumulativeCurveCount == 9`,
`cumulativeFrequencyYLim == [0, 105]`, and `independentPanelScales=True`.

Case-085 audit note: the later queue pass over this HPC distribution Markdown
was treated as `duplicate_markdown_covered_by_case_020`; keep this separate
from categorical textbook dual-axis bar-line templates.

## Executable mapping: textbook bar + spline dual axis

Anchor: `如何用Python绘制教科书级的双Y轴组合图`.

Use this for categorical x data with one context quantity on the left axis and
one focal quantity on the right axis, especially porosity/strength,
bar/line, or explicit dual-axis/twin-axis prompts.

Phase-3 binding:

```python
result = draw_textbook_dual_axis_bar_line(
    ax,
    df,
    x_col="Group",
    bar_col="Porosity",
    line_col="Strength",
    bar_err_col="Por_Err",
    line_err_col="Str_Err",
    group_splits=[3.5, 8.5, 12.5],
    left_ylim=[0, 20],
    right_ylim=[44, 60],
    palette=["#CFE2F3", "#9BC2E6", "#F48E66"],
    spline_points=300,
    xtick_rotation=90,
)
```

Runtime path: `gen_dual_axis` must call
`draw_textbook_dual_axis_bar_line` when roles include `x`, `bar`/`left_y`, and
`line`/`right_y`.

QA signals: left axes gid `scifig_textbook_dual_axis_left`, right axes gid
`scifig_textbook_dual_axis_right`, `dualAxisEncodingCount >= 1`,
`multiAxisEncodingCount >= 1`, `groupDividerCount` equals supplied/derived
splits, `dualAxisSplinePointCount >= 200`, `combinedLegend=True`,
`dualAxisSpineTinted=True`, `topSpineHidden=True`.

Case-077 duplicate-audit note:

- `如何用Python绘制教科书级的双Y轴组合图_1777451702`
  reappears later in the markdown-learning order, but it is the same source
  already learned in Case-012. Keep the existing
  `textbook_dual_axis_bar_line` motif and `dual_axis` executable branch rather
  than minting another dual-axis template.
- The closure evidence lives in
  `.workflow/case_studies/case_077_textbook_dual_y_axis_audit/comparison_report.json`.
  It verifies that Case-012 already captured four reference screenshots, the
  replica, comparison report, runtime probe, and runtime QA for twinx axes,
  bar/spline layering, group dividers, combined legend, and tinted spines.

## Executable variant: Nature Comms count + proportion dual axis

Anchor: `期刊复现：Nature Comms 双Y轴组合图`.

Use this when categorical habitats/groups carry a neutral count quantity on the
left axis and a focal proportion/ratio/percentage quantity on the right axis.
This variant keeps the line unsmoothed because each marker is an observed
category, not a continuous trend estimate.

Phase-3 binding:

```python
result = draw_textbook_dual_axis_bar_line(
    ax,
    df,
    x_col="Habitat",
    bar_col="Count",
    line_col="Proportion",
    left_ylim=[0, 5000],
    right_ylim=[0, 0.5],
    palette=["#D7E6F5", "#2D2D2D", "#E6553A"],
    line_smoothing=False,
    show_mean_line=True,
    mean_line_label="Mean proportion",
    bar_width=0.78,
    line_width=2.1,
    marker_size=6.5,
    xtick_rotation=45,
)
```

Runtime path: `gen_dual_axis` uses the same helper as Case-012 but switches to
this parameter set when `visualContentPlan.templateMotifs` contains
`nature_comms_dual_axis_bar_line`, `count_proportion_dual_axis`, or
`dual_axis_color_linked`.

QA signals: `dualAxisEncodingCount >= 1`, `multiAxisEncodingCount >= 1`,
`referenceLineCount >= 1`, `dualAxisMeanReferenceLine=True`,
`dualAxisColorLinkedRightAxis=True`, `dualAxisSpineTinted=True`,
`combinedLegend=True`, and `topSpineHidden=True`.

Case-091 audit note: the later queue pass over this Markdown is
`duplicate_markdown_covered_by_case_026`; keep the count/proportion Nature
Comms parameter set rather than the textbook porosity/strength spline variant.

## Variant: Biodegradation kinetics validation board

Anchor: `期刊复现：基于双Y轴折线与动力学误差棒的生物降解实验效能可视化`.

Use this when a microcosm or biodegradation experiment must validate a model
mechanism across long-term operation and short-term kinetics.

- Layout is `2x2`: long-term operation, concentration decay, removal kinetics,
  and stage/zone distribution summary.
- Panel A uses `twinx`: left axis carries influent concentration scatter; right
  axis carries removal-efficiency line/markers.
- Panels B/C use `errorbar(..., fmt="-o"/"-s")` for SMX versus inhibitor
  conditions such as `SMX + ATU`.
- Panel D is a boxplot/replicate summary and must stay separate from the dual
  axis panel because it has different time and statistical semantics.
- Red/blue condition colors stay stable across all mechanism panels.

Case-079 evidence lives in
`.workflow/case_studies/case_079_biodegradation_kinetics_validation/comparison_report.json`.

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

Case-054 `triple_y_mechanical_grid` expands this from one axes into a
Materials Today-style five-panel board:

```python
fig = plt.figure(figsize=(10, 8))
gs = gridspec.GridSpec(2, 6, figure=fig, hspace=0.45, wspace=1.5)
panels = [
    fig.add_subplot(gs[0, 0:2]),
    fig.add_subplot(gs[0, 2:4]),
    fig.add_subplot(gs[0, 4:6]),
    fig.add_subplot(gs[1, 0:3]),
    fig.add_subplot(gs[1, 3:6]),
]

for ax_cs in panels:
    ax_fs = ax_cs.twinx()
    ax_sts = ax_cs.twinx()
    ax_sts.spines["right"].set_position(("outward", 45))

    ax_cs.bar(x, cs, yerr=cs_err, color="#D3D3D3", zorder=2)
    ax_fs.errorbar(x, fs, yerr=fs_err, fmt="o", color="#E67E22", zorder=4)
    ax_sts.errorbar(x, sts, yerr=sts_err, fmt="o", color="#27AE60", zorder=4)

    ax_fs.spines["right"].set_color("#E67E22")
    ax_fs.tick_params(axis="y", colors="#E67E22")
    ax_sts.spines["right"].set_color("#27AE60")
    ax_sts.tick_params(axis="y", colors="#27AE60")
```

Use this only when the data truly contain three unit-incompatible metrics per
category. Runtime gap: the public `grouped_bar` probe validates only a
single-axis fallback; no current generator composes the exact five-panel
triple-y mechanical board in one call.

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

Case-032 learned note: the source pairs Train/Test error bars on the left axis
with a right-axis R2 marker line over the same model ordering. Use the grouped
bar variant only when the left-axis bars are separate generalization/error
metrics and the right-axis line is a score/trend metric. Merge legend handles
from both axes, keep only the left-axis y-grid, hide the top spine, and tint
the right spine/ticks to the line color.

Current runtime status: `.workflow/case_studies/case_032_dual_axis_grouped_bar_line/comparison_report.json`
records a complete 16-bar replica and a passing helper probe, but the public
helper probe still validates a single left-axis bar series plus a right-axis
line. Treat `dual_axis_grouped_bar_line` as learned with a documented grouped
bar implementation gap until a distinct public helper/generator path exists.

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
