# Technique: Heatmap Pairwise (n×n)

12/94 corpus cases. The exhaustive correlation matrix layout — Pearson, Spearman, mutual information, scatter matrix.

**Anchor cases:**
- `期刊复现：Nature同款皮尔逊热力图_1777451326`
- `期刊复现：基于上三角局部填充饼图的相关性矩阵_1777455707`
- `期刊配图：基于机器学习的Spearman相关性热力图与模型预测效果组合分析_1777456565`
- `期刊配图：基于高斯核密度的3x3多面板散点图评估混合水文模型模拟性能_1777453582`

## Hallmark elements

1. **n × n grid** with `hspace=wspace=0.05` (tight)
2. **Diagonal panels**: histogram + KDE
3. **Upper triangle**: correlation number on tinted-by-magnitude background, spines hidden
4. **Lower triangle**: hollow-marker scatter with linear fit
5. **Outer-only labels** (left column + bottom row only)
6. **Significance encoding** when p-values supplied (stars or asterisks)
7. **Diverging cmap** for tinted background: `RdBu_r`

## Reference: Nature-style 5×5 Pearson matrix

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, pearsonr
from matplotlib.gridspec import GridSpec
from matplotlib.colors import TwoSlopeNorm
import matplotlib.cm as cm

# Apply compact kernel
plt.rcParams.update({
    'font.family':      ['Arial', 'Times New Roman', 'DejaVu Sans'],
    'mathtext.fontset': 'stix',
    'font.size':        6.5,
    'axes.linewidth':   1.2,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})

features = ['F1', 'F2', 'F3', 'F4', 'F5']
n = len(features)
df = pd.DataFrame(np.random.randn(200, n), columns=features)

fig = plt.figure(figsize=(2.4 * n, 2.4 * n))
gs  = GridSpec(n, n, hspace=0.05, wspace=0.05)
PRIMARY = '#3C5488'
norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
cmap = cm.RdBu_r

for i in range(n):
    for j in range(n):
        ax = fig.add_subplot(gs[i, j])
        x  = df[features[j]].values
        y  = df[features[i]].values

        if i == j:
            # Diagonal: hist + KDE
            ax.hist(x, bins=15, density=True, color='white',
                    edgecolor='black', linewidth=0.8, zorder=1)
            kde = gaussian_kde(x)
            xx  = np.linspace(x.min(), x.max(), 200)
            ax.plot(xx, kde(xx), color=PRIMARY, linewidth=1.8, zorder=3)
            ax.set_yticks([])

        elif i < j:
            # Upper triangle: correlation number on tinted bg
            r, p = pearsonr(x, y)
            ax.set_facecolor(cmap(norm(r)))
            stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
            ax.text(0.5, 0.5, f'{r:.2f}{stars}',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=8, fontweight='bold',
                    color='white' if abs(r) > 0.5 else 'black',
                    zorder=10)
            for s in ax.spines.values():
                s.set_visible(False)
            ax.set_xticks([]); ax.set_yticks([])

        else:
            # Lower triangle: hollow scatter + linear fit
            ax.scatter(x, y, s=12, facecolor='none',
                       edgecolor=PRIMARY, alpha=0.5, linewidth=0.6, zorder=2)
            slope, intercept = np.polyfit(x, y, 1)
            xx = np.linspace(x.min(), x.max(), 100)
            ax.plot(xx, slope * xx + intercept, color='black',
                    linewidth=1.0, zorder=4)

        # Outer-only labels
        if j == 0:
            ax.set_ylabel(features[i], fontsize=12)
        else:
            ax.set_yticklabels([])
        if i == n - 1:
            ax.set_xlabel(features[j], fontsize=12)
        else:
            ax.set_xticklabels([])

# Shared colorbar (outside the matrix)
sm = cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
cax = fig.add_axes([0.92, 0.30, 0.012, 0.40])
cbar = fig.colorbar(sm, cax=cax)
cbar.set_label('Pearson r', fontsize=11)

plt.savefig('pairwise.pdf', dpi=600, bbox_inches='tight')
```

## Variant: Upper-triangle pie correlation

Replace upper-triangle text with a pie wedge whose angle encodes |r| and color encodes sign.

```python
elif i < j:
    r = pearsonr(x, y)[0]
    angle = abs(r) * 360
    color = cmap(norm(r))
    wedge = plt.matplotlib.patches.Wedge(
        center=(0.5, 0.5), r=0.40,
        theta1=90, theta2=90 + angle,
        facecolor=color, edgecolor='black', linewidth=0.5,
        transform=ax.transAxes, zorder=10)
    ax.add_patch(wedge)
    ax.text(0.5, 0.5, f'{r:.2f}', ha='center', va='center',
            transform=ax.transAxes, fontsize=10, zorder=11)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
```

Anchor: `期刊复现：基于上三角局部填充饼图的相关性矩阵`.

Runtime gap: current `scifig.plot chart=correlation` validates a signed
color-mapped matrix, but does not yet render triangle-only Wedge pie-glyph
cells or the empty lower-triangle sparse layout.

## Variant: Lower-triangle correlation heatmap with diagonal colorbar

Anchor: `进阶绘图：解决“多变量拥挤”痛点——Python 绘制带显著性星号与斜向色条的三角热图_1777452320`.

Use this when a dense numeric feature table needs a compact Pearson/Spearman
correlation overview and the source asks for a triangular heatmap, significance
stars, grouping brackets, or a diagonal/oblique colorbar.

Required rendering contract:

- Render one square axes, not an n x n subplot matrix.
- Compute correlation and p-value matrices from supplied raw data, or consume
  supplied `r`/`p` matrices; never synthesize significance.
- Mask the upper triangle with `np.triu(..., k=1)` so the lower triangle and
  diagonal remain visible.
- Use a zero-centered red-yellow-blue diverging palette such as
  `#A50026 -> #F46D43 -> #FFFFBF -> #74ADD1 -> #313695`.
- Annotate every rendered cell with `r`, adding `***`, `**`, or `*` only from
  p-values; switch text to white when `abs(r) > 0.6`.
- Draw grouping brackets outside the matrix with `clip_on=False`.
- Draw the diagonal colorbar parallel to the matrix hypotenuse using small
  polygon patches or an equivalent rotated colorbar helper.

Case-073 evidence lives in
`.workflow/case_studies/case_073_triangular_correlation_heatmap/comparison_report.json`.

## Variant: Spearman as ML evidence-board context

Anchor: `期刊配图：基于机器学习的Spearman相关性热力图与模型预测效果组合分析_1777456565`.

Use pairwise-heatmap rules for the correlation panel only when Spearman is one part of a broader ML evaluation board. If the same prompt/data also includes SHAP or feature importance, actual/predicted values, and external validation metrics, route the whole request through `spearman_ml_evaluation_board` in `ml-model-diagnostics.md`.

Correlation-panel contract:

- Draw a full symmetric Spearman matrix, not a diagonal distribution pairplot.
- Annotate every rendered cell with the signed coefficient.
- Add significance stars only from supplied p-values.
- Use a zero-centered diverging norm so positive and negative monotonic associations are visually comparable.
- Keep the colorbar outside the heatmap panel when the panel is embedded in a 2x2 board.

Case-065 evidence lives in
`.workflow/case_studies/case_065_spearman_ml_evaluation_board/comparison_report.json`.
The runtime `heatmap_symmetric` probe validates the correlation panel only; the
full board belongs to `spearman_ml_evaluation_board`.

## Variant: Spearman KDE pairplot matrix

Anchor: `期刊配图复现：基于二维核密度与相关热力图的多变量联合分布矩阵（附代码）_1778681176`.

Use this when a wide numeric table needs one compact matrix that combines
monotonic association strength with two-variable distribution shape. This is
not the Nature Pearson pairwise matrix: the diagonal cells are text labels, the
upper triangle is Spearman `r` on colored tiles, and the lower triangle is
filled 2D KDE contours rather than hollow scatter plus linear fit.

Required rendering contract:

- Layout is an `n x n` subplot matrix with `wspace=0.05` and `hspace=0.05`.
- Diagonal cells hide axes and place the variable name in the center.
- Upper-triangle cells use one signed correlation color scale such as
  `coolwarm` / `Normalize(vmin=-1, vmax=1)` and center the numeric `r` label.
- Lower-triangle cells render `sns.kdeplot(..., fill=True, levels≈8)` or an
  equivalent `gaussian_kde` contour field for each variable pair.
- Do not compare absolute density intensity across lower-triangle panels unless
  the density grids are deliberately normalized together; each pair usually owns
  its local KDE scale.
- Use a single outside Spearman colorbar when space allows.

Case-080 evidence lives in
`.workflow/case_studies/case_080_spearman_kde_pairplot_matrix/comparison_report.json`.

## Executable mapping: red-blue bubble correlation matrix

Anchor: `如何用 Python 完美复刻一张“红蓝气泡”相关性分析图`.

Use this when the prompt or data profile exposes a square correlation matrix,
a long `row` / `column` / `r` table, or a wide numeric table with
correlation/Pearson/Spearman cues.

Required rendering contract:

- Full symmetric grid: one bubble per finite matrix cell, not triangle-only.
- Color encodes signed `r` with `TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)`.
- Palette is `materials_teal_salmon_correlation`: `#8ECFC9`, `#FFFFFF`, `#FA7F6F`.
- Bubble area encodes `abs(r) * 2000`; keep a dark hairline edge for white/near-zero cells.
- Each finite cell gets a centered `"{r:.2f}"` label.
- Axis labels sit at cell centers; x labels rotate 45 degrees; minor ticks draw the pale cell grid.

Phase-3 binding:

```python
result = draw_bubble_correlation_matrix(
    ax,
    corr_long_or_matrix,
    row_col="row",
    col_col="column",
    value_col="r",
    palette=["#8ECFC9", "#FFFFFF", "#FA7F6F"],
    size_scale=2000,
    annotate=True,
    colorbar_label="Pearson r",
)
```

QA signals: `templateMotifsApplied` includes `bubble_correlation_matrix`,
`correlationBubbleCount > 0`, `correlationBubbleCellCount == n*n`,
`correlationNumericTextCount == n*n`, `colorbarSlotCount >= 1`, and the main
axis gid is `scifig_bubble_correlation_matrix`.

Case-076 duplicate-audit note:

- `如何用 Python 完美复刻一张“红蓝气泡”相关性分析图_1777451587`
  reappears later in the markdown-learning order, but it is the same source
  already learned in Case-011. Keep the existing `bubble_correlation_matrix`
  motif and heatmap-pairwise correlation evidence rules rather than minting a
  second bubble-matrix template.
- The closure evidence lives in
  `.workflow/case_studies/case_076_red_blue_bubble_correlation_audit/comparison_report.json`.
  It verifies that Case-011 already captured four reference screenshots, the
  replica, comparison report, runtime probe, and runtime QA for signed color,
  absolute-correlation bubble area, per-cell labels, and the matrix colorbar.

## Variant: upper significance / lower bubble correlation matrix

Anchor: `告别枯燥表格！Python绘制超吸睛的相关性气泡图_1778681959`.

Case-097 evidence lives in
`.workflow/case_studies/case_097_upper_sig_lower_bubble_correlation/comparison_report.json`.

Use this when the matrix intentionally splits semantics by triangle: lower
triangle encodes correlation strength as bubbles, while upper triangle prints
the significance marker and coefficient.

Rendering contract:

- Compute both Spearman `r` and p-value matrices for the same feature order.
- Leave the diagonal blank unless the prompt explicitly asks for variable names.
- Draw lower-triangle bubbles with radius proportional to `abs(r)`; the source
  uses `0.3 * abs(r)`.
- Draw upper-triangle text as significance marker plus formatted coefficient.
- Map both text color and bubble fill through one signed diverging color scale,
  typically `seismic` over `[-1, 1]`.
- Keep a colorbar for signed `r`, a bubble-size legend for `|r|`, and a separate
  significance legend for p-value thresholds.

QA signals: `lower_triangle_bubble_count == n * (n - 1) / 2`,
`upper_triangle_text_count == n * (n - 1) / 2`,
`significance_text_count == upper_triangle_text_count`,
`diagonal_blank == true`, `colorbar_count == 1`,
`bubble_size_legend_count == 1`, and `significance_legend_count == 1`.

Case-093 duplicate-audit note:

- `期刊复现：Nature同款皮尔逊热力图_1777451326` reappears later in the
  markdown-learning order, but it is the same source already learned in
  Case-028. Keep the `nature_pearson_pairwise_matrix` bundle with diagonal
  histogram/KDE cells, upper Pearson tiles, lower hollow scatter + fit cells,
  and outer-only labels.
- The closure evidence lives in
  `.workflow/case_studies/case_093_nature_pearson_pairwise_matrix_audit/comparison_report.json`.

## Variant: Layered model-increment heatmap matrix

Use this when the data contains row groups such as stations/cohorts, two
baselines per group, several model rows, and several metric columns. The visual
grammar is not an n x n correlation grid; it is a row-wise comparison board.

Required rendering contract:

- Layout is `GridSpec(n_groups, 3)` with `width_ratios=[1, 1, 0.05]`.
- The first two columns are equal-width heatmaps with identical row/column order.
- The third column is a narrow colorbar axis for that row, not an overlaid inset.
- Signed deltas use one symmetric absolute limit across the full board and a
  zero-centered diverging norm with `RdBu_r`.
- Cells have white separators (`linewidth` about 1.5) and centered numeric labels.
- Greek metric labels such as alpha and beta should use mathtext on x ticks.

QA signals: `layeredHeatmapMatrix` true, `heatmapPanelCount == n_groups * 2`,
`rowColorbarCount == n_groups`, `divergingNormCentered` true,
`gridWidthRatios == [1, 1, 0.05]`, and `cellAnnotationCount` equals the number
of rendered cells.

Anchor: `期刊配图复现：Python 绘制多面板分层热力图矩阵`.

## Discipline rules

- `hspace=wspace=0.05` — must be tight
- Layered model-increment heatmaps use `wspace=0.10`, `hspace=0.30`, and a row colorbar column; do not force them into the n x n pairwise spacing rule.
- Outer-only labels (else clutter)
- Tinted background uses `TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)` — center at 0
- For model-increment boards, compute `vmin=-limit`, `vmax=limit` from one board-level absolute limit; never normalize each row independently.
- Bubble-correlation variant uses bubble area for `abs(r)` and signed color for `r`; do not add an imshow layer underneath.
- Text color flips to white when |r| > 0.5 (contrast)
- Significance stars only when p-values supplied; never invent
- Lower-triangle markers are **hollow** (`facecolor='none'`) so cells with many points stay readable

## QA contract

- `tightSpacing`: `hspace ≤ 0.10` and `wspace ≤ 0.10`
- `outerOnlyLabels`: True
- `divergingNormCentered`: cmap norm has `vcenter=0`
- `significanceStarsOnlyIfP`: stars present iff p-value column in dataProfile
- `bubbleCorrelationMatrix`: if planned, `correlationBubbleCellCount == n*n`
