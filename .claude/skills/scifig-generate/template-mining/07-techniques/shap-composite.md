# Technique: SHAP Composite

35/94 corpus cases — the largest family. SHAP composites usually combine **3 sub-views**: importance ranking (top), beeswarm (middle), and dependence/local force (bottom or beside).

**Anchor cases:**
- `期刊配图复现 _ Python绘制多面板SHAP蜂群图_1777452005`
- `复现顶刊 _ 拒绝千篇一律的SHAP图，用Matplotlib手绘一张"蜂群+条形"组合图_1777452577`
- `期刊配图复现 _ 手把手教你用 Python 绘制 SHAP 全局与局部解释组合图_1777452973`
- `期刊复现：组合重要性条形图与SHAP蜂群图解析特征的全局预测贡献_1777454956`
- `期刊复现：基于SHAP复合图揭示高能分子特征对性能的全局与局部影响_1777454774`

## Hallmark elements

1. **Mean |SHAP| importance** as horizontal bars or lollipops (left or top)
2. **Beeswarm**: per-sample SHAP value with points jittered vertically per feature
3. **Color = feature value low→high** via `viridis` (or `RdBu_r` for sign emphasis)
4. **Shared y-feature ordering** across all sub-panels (sorted by mean |SHAP|)
5. **Zero reference line** (vertical) to separate positive/negative contribution
6. **Top-N filter** (typically top 10-15 features)

## Full reference: Bar + Beeswarm composite

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

# Pre-computed: shap_values (n_samples, n_features), feature_values (same shape),
# feature_names (n_features,). Sort features by mean |SHAP| desc.
mean_abs = np.abs(shap_values).mean(axis=0)
order    = np.argsort(mean_abs)[::-1][:15]   # top 15
feat_top = [feature_names[i] for i in order]
ypos     = np.arange(len(order))             # 0 = top of chart

# === Layout: 1×2 with 30/70 width ===
fig = plt.figure(figsize=(13, 7))
gs  = GridSpec(1, 2, width_ratios=[0.30, 0.70], wspace=0.05)
ax_bar = fig.add_subplot(gs[0, 0])
ax_bee = fig.add_subplot(gs[0, 1], sharey=ax_bar)

# === Left: importance bars ===
ax_bar.barh(ypos, mean_abs[order],
            color='#7E6148', alpha=0.6,
            edgecolor='black', linewidth=0.6, zorder=2)
ax_bar.set_yticks(ypos)
ax_bar.set_yticklabels(feat_top, fontsize=11)
ax_bar.invert_yaxis()                        # top feature at top
ax_bar.set_xlabel('Mean |SHAP|', fontsize=12)
ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)
ax_bar.set_facecolor('#FAFAFA')

# === Right: beeswarm with feature-value coloring ===
ax_bee.axvline(0, color='black', linewidth=1.0, zorder=4)

def jitter(values, width=0.35):
    """Vertical jitter density-aware: more samples → wider spread."""
    rng = np.random.default_rng(42)
    return (rng.random(len(values)) - 0.5) * width

for i, idx in enumerate(order):
    sv = shap_values[:, idx]
    fv = feature_values[:, idx]
    # Normalize feature value to [0, 1] for cmap
    fv_n = (fv - fv.min()) / (fv.max() - fv.min() + 1e-12)
    ax_bee.scatter(sv, np.full(len(sv), i) + jitter(sv),
                   c=fv_n, cmap='RdYlBu_r', s=10, alpha=0.7,
                   edgecolor='white', linewidth=0.2, zorder=5)

ax_bee.set_xlabel('SHAP value (impact on prediction)', fontsize=12)
ax_bee.tick_params(labelleft=False)
ax_bee.spines['top'].set_visible(False)
ax_bee.spines['right'].set_visible(False)

# === Shared color bar for feature value ===
sm = plt.cm.ScalarMappable(cmap='RdYlBu_r',
                           norm=plt.Normalize(vmin=0, vmax=1))
sm.set_array([])
cax = fig.add_axes([0.93, 0.20, 0.012, 0.60])
cbar = fig.colorbar(sm, cax=cax)
cbar.set_label('Feature value', fontsize=11, rotation=270, labelpad=15)
cbar.set_ticks([0, 1]); cbar.set_ticklabels(['Low', 'High'])

plt.tight_layout(rect=[0, 0, 0.92, 1])
plt.savefig('shap_composite.pdf', dpi=600, bbox_inches='tight')
```

## Variant: SHAP + Pie / SHAP + Donut (global contribution share)

When the user wants total-contribution share alongside beeswarm:

```python
# Top-3 importance share + 'other' aggregated
top3 = mean_abs[order[:3]]
other = mean_abs[order[3:]].sum()
share = np.append(top3, other)
labels = feat_top[:3] + ['Others']

ax_pie.pie(share, labels=labels, colors=['#E64B35', '#4DBBD5', '#00A087', '#7F7F7F'],
           wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2),
           startangle=90, textprops={'fontsize': 10})
```

## Executable mapping: bar + beeswarm + inset pie

`gen_dotplot` enters `shap_bar_beeswarm_inset_pie` mode when the figure is
standalone and `visualContentPlan.templateMotifs` or `specialPatterns` contains
`shap_bar_beeswarm_inset_pie`; `shap_composite` with feature-value columns may
also route here. The generator calls `draw_shap_bar_beeswarm_inset_pie`, which
expects a long SHAP table: `feature_id`, `shap_value`, optional `feature_value`,
and optional `category` / `feature_group`.

Layout discipline:

- `GridSpec(1, 4, width_ratios=[1.15, 0.05, 1.20, 0.05], wspace=0.10)`
- left panel: mean `|SHAP|` horizontal bars, one shared feature order
- right panel: density-aware vertical jitter beeswarm, `SHAP value` on x
- colorbar slot: dedicated axes, label `Feature value`, ticks `Low` / `High`
- inset pie: inside the bar panel at `(0.50, 0.20, 0.45, 0.45)`, `gid="scifig_shap_inset_pie"`

Runtime QA signals:

- `templateMotifsApplied` includes `shap_bar_beeswarm_inset_pie`
- `referenceLineCount`, `colorbarSlotCount`, `insetPieCount`, and `sampleEncodingCount` increment
- `sharedFeatureOrdering=True`, `featureValueColorEncoded=True`, and `topFeatureLimit <= 15`

Case-047 compact variant:

- Source layout uses `GridSpec(1, 2, width_ratios=[1, 1.2], wspace=0.15)` and
  a manually positioned inset pie via `fig.add_axes`.
- The left bar colors and inset pie slices must come from the same feature
  category totals; the pie is a category summary of the bar evidence, not a
  separate claim.
- The right beeswarm hides duplicate y labels and relies on the left panel's
  ranked feature order; row mismatches invalidate the explanation.
- The SHAP x-axis is signed model contribution, while feature-value color is
  normalized within each feature row. Do not promote row colors to physical
  causality.
- Runtime status: `dotplot` validates only the right-side feature-value dot
  surface. The full compact bar + inset pie + beeswarm board is learned here as
  a template composition.

## Variant: Global/local bar + beeswarm + colorbar

Use this when the figure should pair global feature importance with local
sample-level SHAP direction without an inset pie, donut, or extra prediction
validation panel.

Required rendering contract:

- Layout: `GridSpec(1, 3, width_ratios=[0.8, 1.2, 0.05], wspace=0.05)`.
- Left panel: horizontal mean `|SHAP|` bars sorted by global importance, with
  bold feature labels and an x-grid behind bars.
- Right panel: beeswarm points use the same feature order and hide duplicate y
  labels; vertical jitter stays within the feature row.
- Reference: one SHAP x=0 vertical line plus dotted horizontal row separators
  keeps local positive/negative effects readable.
- Color: map raw/normalized feature values with `coolwarm` and use a dedicated
  narrow colorbar axis with manual Low/High text and no numeric ticks.
- Runtime boundary: current `dotplot` validates only the right local dot
  surface. Record a gap until a registered one-call generator composes the left
  mean-`|SHAP|` bar panel and narrow colorbar slot.

## Variant: GS-XGBoost grouped bar + beeswarm

Use this when a GS-XGBoost / XGBoost explanation board needs to compress many
binary structure descriptors into one interpretable row while still showing
global mean `|SHAP|` ranking and local SHAP direction.

Required rendering contract:

- Layout: `GridSpec(1, 2, width_ratios=[1, 1.3], wspace=0.35)` with a wide
  right beeswarm lane.
- Preprocess: aggregate same-family binary structure descriptors into one
  `structures_total` or equivalent row before ranking, then sort all features by
  mean `|SHAP|`.
- Left panel: horizontal mean `|SHAP|` bars own the y tick labels and may carry
  dashed physical-group brackets for merged structure, adsorbent descriptors,
  reaction conditions, and porous properties.
- Right panel: beeswarm points use the same feature order, signed SHAP values on
  x, row-local jitter on y, and low-to-high feature-value color semantics.
- Color: use the source blue-low / red-high ramp (`#4A90E2` to `#E94B3C`) and
  mount a narrow inset colorbar outside the beeswarm axis with only Low/High
  labels.
- Runtime boundary: current `dotplot` validates only the right SHAP-like point
  surface. Record a gap until a one-call generator composes the grouped bar
  lane, brackets, and inset colorbar.

## Variant: Multi-panel SHAP beeswarm matrix

Use this when one explanation task is repeated across regions, cohorts, or
submodels and each panel must combine global mean `|SHAP|` importance with
sample-level signed SHAP distributions.

Required rendering contract:

- Layout: `GridSpec(2, 6)` with top spans `[0:2]`, `[2:4]`, `[4:6]` and
  bottom centered spans `[1:3]`, `[3:5]`.
- Per panel: create `ax_top = ax_bottom.twiny()` for purple mean `|SHAP|`
  background bars.
- Beeswarm: sort features by panel-local mean `|SHAP|`, compute density-aware
  vertical jitter from SHAP value bins, and color points by normalized feature
  value using `viridis`.
- Reference: repeat a black x=0 line in every panel.
- Colorbar: attach one manual board-level `Feature value` colorbar with Low/High
  ticks; do not add five local colorbars.

QA signals: `activePanelCount == 5`, `twinyAxisCount == 5`,
`shapBarCount > 0`, `shapBeeswarmCount > 0`, `zeroReferenceLineCount == 5`,
`colorbarSlotCount == 1`, `featureValueColorEncoded=True`.

Case-075 duplicate-audit note:

- `复现顶刊 _ 拒绝千篇一律的SHAP图，用Matplotlib手绘一张“蜂群+条形”组合图_1777452577`
  reappears later in the markdown-learning order, but it is the same source
  already learned in Case-010. Keep the existing
  `shap_bar_beeswarm_inset_pie` motif and dotplot/SHAP composite executable
  branch rather than minting another SHAP composite template.
  It verifies that Case-010 already captured the reference images, replica,
  comparison report, runtime probe, and runtime QA for the importance bar,
  SHAP beeswarm, feature-value colorbar, and inset pie.

## Variant: RF EFI + SHAP donut

Use this when RF feature importance and global mean `|SHAP|` are the two
explainability signals:

- The SHAP component is a hollow donut (`wedgeprops.width=0.45`) rather than a
  beeswarm. Treat it as contribution-share evidence only.
- External labels need grey leader lines and collision-aware y spacing; inline
  labels on small slices are not acceptable for dense feature sets.
- Sort the donut by mean `|SHAP|`; do not force it to match the EFI bar order
  unless the source data explicitly asks for rank-aligned reading.
- Keep the unit boundary visible: EFI and mean `|SHAP|` are different
  statistics, so matching ranks are evidence, while absolute values are not
  cross-panel comparable.

Runtime status: current SHAP fallbacks use `dotplot`/beeswarm or lollipop
importance lanes. The hollow-donut callout layout is a learned template gap.

## Variant: GS-XGBoost grouped SHAP bar + beeswarm

Use this when many binary or structural descriptors should be merged into one
interpretable feature group before plotting the global ranking.

Required rendering contract:

- Asymmetric `GridSpec(1, 2, width_ratios=[1, 1.3], wspace=0.35)`.
- Left lane: mean `|SHAP|` horizontal bars; colors encode physical feature
  groups such as adsorbent descriptors, reaction conditions, merged structure,
  or porous properties.
- Draw dashed bracket annotations outside the bar-axis y labels to identify
  feature groups without repeating the labels in the beeswarm.
- Right lane: SHAP beeswarm using the same feature order, a vertical zero
  reference line, and feature-value color encoding.
- Use a compact inset colorbar beside the beeswarm with ticks `Low` / `High`
  rather than a full extra GridSpec column.

QA signals: `sharedFeatureOrdering=True`, `groupBracketCount >= 1`,
`mergedStructureFeature=True`, `insetColorbarCount == 1`, and
`zeroReferenceLineCount >= 1`.

## Executable mapping: lollipop + SHAP beeswarm board

Use this when a model-explanation table includes feature importance / gain plus
long-form SHAP values. The source uses a 1x2 board with a compact importance
lane at left and a wider SHAP beeswarm lane at right, both sharing the feature
y-axis.

Phase-3 binding:

```python
result = draw_lollipop_shap_beeswarm_board(
    df,
    feature_col="feature_id",
    shap_value_col="shap_value",
    importance_col="importance",
    feature_value_col="feature_value",
    width_ratios=[1.0, 2.5],
    figsize=(12, 6),
    wspace=0.05,
)
```

Runtime path: `gen_dotplot` enters `lollipop_shap_beeswarm_board` mode when the
visual plan or `specialPatterns` includes `lollipop_shap_beeswarm_board`.

QA signals: left axes gid `scifig_lollipop_shap_importance`, right axes gid
`scifig_lollipop_shap_beeswarm`, stem gid `scifig_lollipop_importance_stems`,
point gid `scifig_lollipop_importance_points`, SHAP point gid
`scifig_lollipop_shap_points`, zero-line gid
`scifig_lollipop_shap_zero_reference`, `lollipopLayerCount=1`,
`shapBeeswarmCount=1`, `sharedFeatureOrdering=True`, and
`shapCompositeLayout="subplots(1,2)"`.

Case-086 audit note: the later queue pass over this Markdown was treated as
`duplicate_markdown_covered_by_case_021`; preserve this lollipop-left /
beeswarm-right contract separately from bar-based SHAP composites.

## Executable mapping: bar + standalone pie + summary beeswarm

`gen_dotplot` enters `shap_bar_pie_summary_board` mode when the visual plan or
`specialPatterns` includes `shap_bar_pie_summary_board`. This is distinct from
the Case-010 inset-pie board: the descriptor-category pie is its own panel, not
an inset inside the bar axes. The generator calls
`draw_shap_bar_pie_summary_board`, which expects the same long SHAP table roles:
`feature_id`, `shap_value`, `feature_value`, and `category` / `feature_group`.

Layout discipline:

- `GridSpec(2, 3, width_ratios=[1.2, 0.8, 1.5], height_ratios=[1, 1])`
- panel (a): left mean `|SHAP|` horizontal bars spanning both rows
- panel (b): standalone descriptor category pie in `gs[0, 1]`
- panel (c): right SHAP summary beeswarm spanning both rows
- colorbar: attached to panel (c), label `Feature Value`, ticks `Low` / `High`
- panel labels `(a)`, `(b)`, `(c)` in axes-relative coordinates

Runtime QA signals:

- `templateMotifsApplied` includes `shap_bar_pie_summary_board`
- `standalonePieCount=1`, `piePanelCount=1`, `colorbarSlotCount=1`
- `referenceLineCount=1`, `zeroReferenceLineCount=1`, and `panelLabelCount=3`
- `sharedFeatureOrdering=True`, `featureValueColorEncoded=True`, and `topFeatureLimit <= 15`

Case-084 audit note: the later queue pass over this Markdown was treated as
`duplicate_markdown_covered_by_case_019`; keep using this standalone-pie SHAP
summary board instead of the Case-010 inset-pie variant.

## Variant: Target-wise SHAP mean-importance triptych

Use this when the input supplies precomputed mean absolute SHAP values for
several prediction targets, and the figure's job is to compare target-specific
driver rankings:

- Layout is `1x3` with one target per panel, for example SSA, Vt, and NC.
- Bars are horizontal mean `|SHAP|` rankings. The x-axis is magnitude only; do
  not describe positive/negative SHAP direction or causal feature effects from
  this view.
- Keep independent x-axis limits. Cross-panel comparison is by rank and feature
  identity, not raw bar length.
- Apply `RdYlBu_r` or equivalent warm-to-cool emphasis with local per-panel
  normalization so each target retains its own visual hierarchy.
- Place numeric labels on every bar, using contrast-aware text when labels sit
  inside the bars.
- Runtime status: current `lollipop_horizontal` validates only one ranked
  feature panel. No public generator yet composes the full three-target SHAP
  mean-importance triptych with local normalization and value labels.

## Variant: 上三下二 (top-wide + 2 below) — SHAP global+local hero

```python
fig = plt.figure(figsize=(11, 9))
gs  = GridSpec(2, 2, height_ratios=[1, 1], hspace=0.35, wspace=0.25)
ax_top = fig.add_subplot(gs[0, :])   # full-width: global importance bars
ax_bl  = fig.add_subplot(gs[1, 0])   # bottom-left: beeswarm (top 10 features)
ax_br  = fig.add_subplot(gs[1, 1])   # bottom-right: dependence plot for #1 feature
```

## Variant: Prediction + SHAP/PDP explanation board

Use this when a model-report figure must connect prediction validity to
explanation in one board. This is not a pure SHAP summary; it is a progression
from model performance to attribution.

Rendering contract:

- Layout is an asymmetric `GridSpec(2, 2)` with `height_ratios=[1, 1.2]`.
- Panel A: parity scatter with `y=x` reference, equal aspect, and an in-axes
  `R^2` or metric box.
- Panel B: residual distribution or compact residual diagnostic to expose bias
  not captured by the metric box.
- Panel C: global SHAP importance bars, usually mean `|SHAP|`, sorted by feature
  importance.
- Panel D: local dependence/PDP for the top mechanism feature, with scatter and
  a smooth trend line.

Case-070 boundary: the article code only details GridSpec setup and parity
plotting. Residual, SHAP, and PDP panels are learned from the visual grammar and
should be marked as reconstructed when raw model outputs are absent.

QA signals: `panelCount == 4`, `perfectFitLineCount >= 1`, `metricBoxCount >= 1`,
`residualHistogramCount >= 1`, `shapBarCount > 0`, `pdpScatterCount > 0`,
`pdpTrendLineCount >= 1`, and `exportDpi == 600`.

## Variant: Molecular SHAP + parity evidence board

Use this when molecular descriptor attribution must be tied to prediction
quality rather than shown as a standalone explanation:

- Layout is a heterogeneous `2x2` GridSpec: SHAP beeswarm, global mean-absolute
  SHAP bars, train/test parity, and external validation parity.
- SHAP beeswarm and importance bars should share feature ordering so local
  direction and global magnitude are directly comparable.
- Internal parity needs a perfect-fit diagonal, train/test split colors, and a
  compact metric inset for R2/RMSE or equivalent supplied metrics.
- External validation gets its own parity panel; do not merge it into training
  or testing points if the article/prompt frames it as independent robustness.
- Runtime status: current `dotplot` validates only the SHAP summary lane. A
  public generator does not yet compose the 2x2 SHAP plus parity board.

## Variant: 6-panel SHAP dependence grid (signed-background style)

For each top-6 feature: SHAP value vs feature value, with red/blue signed SHAP background zones:

```python
fig, axes = plt.subplots(2, 3, figsize=(12, 7))
axes = axes.ravel()

for k, feature in enumerate(feature_names[:6]):
    ax = axes[k]
    ax.axhspan(0, 2.5, color='#ffcccc', alpha=0.4, zorder=0)
    ax.axhspan(-2.5, 0, color='#cce5ff', alpha=0.4, zorder=0)
    ax.axhline(0, color='gray', linestyle='--', linewidth=1.5, zorder=1)
    ax.scatter(feature_values[feature], shap_values[feature],
               color='black', s=15, alpha=0.7, zorder=2)
    ax.set_ylim(-2.5, 2.5)
    ax.set_xlabel(feature, fontsize=12, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
```

Executable mapping: `scatter_regression` calls `draw_shap_dependence_background_grid` when long-form data carries `feature_id` + `feature_value` + `shap_value` for multiple features and the motif or profile indicates SHAP dependence/background signed zones. It must draw positive/negative background bands, a dashed zero contribution line, black scatter, uniform y-limits, and no colorbar for this signed-background variant.

Case-082 audit note: the later queue pass over this Markdown was treated as
`duplicate_markdown_covered_by_case_017`; reuse this signed-background SHAP
dependence grid contract rather than adding another SHAP scatter variant.

## Variant: 6-panel SHAP interaction dependence grid

Case-018 uses the same 2x3 long-form SHAP dependence structure but encodes a secondary interaction feature as scatter color:

```python
fig = plt.figure(figsize=(14, 8))
gs = fig.add_gridspec(2, 3, wspace=0.4, hspace=0.3)

scatter = ax.scatter(x_data, shap_values, c=color_data, cmap='coolwarm',
                     s=15, alpha=0.8, edgecolors='none', zorder=2)
ax.axhline(0, color='gray', linestyle='--', linewidth=0.8, zorder=1)
ax.text(-0.15, 1.05, '(a)', transform=ax.transAxes,
        fontsize=12, fontweight='bold', va='bottom')
cbar = fig.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label('Interaction Feature', size=9)
```

Executable mapping: `scatter_regression` calls `draw_shap_interaction_dependence_grid` when long-form data carries `feature_id` + `feature_value` + `shap_value` + `interaction_value` and the motif or profile indicates SHAP interaction dependence. This branch has priority over the signed-background grid.

Case-083 audit note: the later queue pass over this Markdown was treated as
`duplicate_markdown_covered_by_case_018`; reuse the interaction-color SHAP
dependence grid contract, including per-panel colorbars and independent y-scales.

Case-039 global-colorbar variant: `期刊复现：基于多面板组合的SHAP依赖图解析特征对模型预测的非线性影响`
uses a rotated `3x2` SHAP dependence grid with one shared interaction-value
colorbar in a reserved right-side axes. Each panel draws feature value on x,
SHAP value on y, interaction value as `viridis` scatter color, a red dashed
`y=0` semantic baseline, and a quadratic trend with a light-blue confidence
band. Use one global color normalization so identical colors carry identical
interaction-value meaning across all six panels. Runtime status: current
`scatter_regression` validates only a single generic scatter plus OLS trend,
not this 3x2 SHAP interaction grid or global colorbar composition.

## Variant: 2x2 SHAP conversion dependence matrix

Use this when SHAP dependence panels are explicitly organized as prediction
target rows crossed with main-feature columns:

- Layout is `plt.subplots(2, 2, figsize=(15, 10))` with `wspace=0.35` and
  `hspace=0.45`; rows are targets such as CH4 and CO2 conversion, columns are
  main features such as surface area and reaction temperature.
- Every panel maps `x=feature_value`, `y=shap_value`, and `c=secondary_feature`
  with `RdYlBu_r`; the colorbar is local to that panel and labeled Secondary
  Feature.
- Draw a black nonlinear trend line in every panel to summarize the main
  effect, then a gray dashed `y=0` line to preserve positive/negative SHAP
  contribution semantics.
- Interpretation boundary: SHAP values are model attributions, not absolute
  conversion rates or causal intervention effects. Do not compare color depth
  across panels unless the same secondary feature and normalization are shared.

Runtime status: current `scatter_regression` validates only one dependence-like
scatter panel; no public generator composes the full 2x2 target-by-feature
conversion matrix with four local colorbars.

## Variant: SHAP PDP threshold panel array

Use this when SHAP partial-dependence rows carry feature id, feature value,
SHAP contribution, and optionally an interaction/context value:

- Layout is a horizontal `1xN` panel array. Each variable keeps its own x-axis
  units while sharing the same SHAP-contribution interpretation.
- Every panel must draw a dashed `y=0` baseline so positive and negative model
  contributions remain legible.
- Scatter points may be colored by a secondary interaction value; the colorbar
  is contextual and must not replace the SHAP contribution axis.
- Add threshold annotations only where the provided data support the threshold
  region. Do not infer sparse intervals as hard physical cutoffs.
- Runtime status: current `scatter_regression` validates generic scatter plus
  OLS only. It does not yet provide the SHAP baseline, nonlinear smooth,
  interaction colorbar, threshold callout, or 1xN composition.

Case-094 audit note: `期刊复现：SHAP依赖图解析环境因子对目标变量的影响方向与程度_1777454034`
was already learned as Case-029. Despite the title, the visual grammar is a
single-panel SHAP summary/beeswarm: sorted features, vertical SHAP=0 reference,
coolwarm feature-value points, and Low/High colorbar. Do not route this source
to the SHAP dependence grid unless the user asks for feature-value-vs-SHAP
panels.

Case-030 learned note: `期刊复现：SHAP蜂群图解析环境因子对目标变量的影响方向与程度_1777455105`
is the explicit environmental SHAP summary variant. It reinforces the same
single-panel contract as Case-029 but makes the global-importance ordering
rule explicit: sort features by mean `|SHAP|`, keep the dashed x=0 contribution
divider, color points by raw feature value, and use Low/High colorbar ticks as
the runtime `dotplot` probe passes the structural contract, with documented
wording/colorbar tick gaps.

## Discipline rules (universal across the 26 cases)

| Rule | Why |
|---|---|
| Sort features by mean |SHAP| descending; ALL sub-panels share that order | Reader's eye tracks one ranking |
| `cmap='RdYlBu_r'` or `'viridis'` for feature value | Cool-low to warm-high is universal |
| `axvline(0)` at SHAP=0 with `linewidth=1.0` | Sign separator |
| Marker `edgecolor='white', linewidth=0.2` | Crispness on dense beeswarm |
| Top-N filter typically 10-15 | Anything more is unreadable |
| Alpha 0.7 on scatter | Density visible, individual points still legible |
| Color bar labeled "Feature value" with Low / High ticks only | Not 0-1 numbers |

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Different feature order across panels | Sort once, share via `sharey=ax_bar` |
| Showing all 100 features | Top-15 max; rest collapsed to "Others" in pie variant |
| Using rainbow cmap for feature value | Use `RdYlBu_r` (diverging) or `viridis` (sequential) |
| Forgetting zero line | Sign of contribution becomes ambiguous |
| Color bar inside data area | Always outside the data rectangle, dedicated `add_axes` |

## QA contract

Phase 4 render-qa requires for SHAP composite:
- `sharedFeatureOrdering`: y-axis order identical across all sub-panels
- `zeroReferenceCount`: ≥1 (the `axvline(0)`)
- `colorbarLabelPresent`: 'Feature value' or equivalent
- `topFeatureLimit`: ≤15 (else readability fails)
- `featureValueColorEncoded`: scatter has `c=` parameter
