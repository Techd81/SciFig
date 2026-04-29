# 科学叙事弧 (Narrative Arcs)

Phase 2 chooses a **narrative arc** before picking individual chart families. The arc encodes the story shape — how panels relate, which is the hero, what role each support panel plays. All 77 reference cases in the corpus map to one of 10 arcs.

## Arc selection (Phase 2 entry point)

Read the `dataProfile` and ask:

1. **How many distinct claims?**
   - 1 claim, headline figure → `hero` or `single_focus`
   - 2 claims (one main + one diagnostic) → `composite_two_lane` or `marginal_joint`
   - 4-9 parallel claims → `multipanel_grid`
   - n×n exhaustive comparison → `n×n_pairwise`
   - Global summary + local detail → `global_local`
   - Train/test or before/after → `train_test_diagnostic`
   - Two conditions in mirror layout → `mirror_compare`
   - Main panel + zoom/distribution → `inset_overlay`

2. **Bind to chart family / grid recipe** via the table at the end of this file.

3. **Apply the arc-specific motif requirements** (each arc has 2-4 mandatory motifs).

## Frequency in corpus (n=77)

| Arc | Cases | % | Hallmark |
|---|---|---|---|
| `multipanel_grid` | 26 | 34% | dense scaffolding, 4-9 panels of one family |
| `single_focus` | 18 | 23% | one panel, one strong claim |
| `global_local` | 5 | 6% | global summary + local interpretation |
| `n×n_pairwise` | 5 | 6% | exhaustive cross-comparison |
| `marginal_joint` | 4 | 5% | center scatter + top/right marginals |
| `train_test_diagnostic` | 4 | 5% | training fold vs holdout |
| `composite_two_lane` | 4 | 5% | left/right complementary lanes |
| `mirror_compare` | 4 | 5% | bipolar / two-condition mirror |
| `hero` | 4 | 5% | headline single-panel with heavy styling |
| `inset_overlay` | 3 | 4% | main + zoom-in inset |

---

## A1 — `single_focus` / `hero` (29% combined)

One claim, one panel. `hero` differs from `single_focus` only in styling intensity — `hero` panels carry the headline and use polygon polar grid, gradient fills, white-edge markers, in-plot metric box, all together.

**Required motifs (hero):**
- Polygon grid (if polar) or grid removed (`hero` is rarely on default cartesian)
- Layered zorder (3+ tiers)
- White-edge markers
- In-plot metric box or signature label
- Bold panel label (if part of larger figure)

**Required motifs (single_focus):**
- Layered zorder (≥2 tiers)
- At least 1 in-axes annotation (metric box / reference line)

**Grid:** `R0_single_panel` (`figsize=(6.5, 6)` to `(8, 8)`)

**Anchor cases:**
- hero: `绝美！Nature 这张雷达图`, `顶刊复刻：中心挖空+立体高光的雷达图`, `Python绘制堆叠小提琴图`, `用 Python 绘制带"垂直渐变特效"的组合箱线图`
- single_focus: forest plot, single SHAP beeswarm, single dual-axis combo, single density scatter

---

## A2 — `multipanel_grid` (34%)

The most common arc. 4-9 panels of the **same** chart family compared side-by-side (different features, models, conditions).

**Required motifs:**
- Panel labels (a/b/c…) on every panel
- Shared axis where appropriate
- Consistent palette across panels
- One in-axes annotation per panel (zero ref, metric, etc.)

**Grid:**
- 4 panels → `R6_four_panel_band` (1×4) or `R2_two_by_two_storyboard` (2×2)
- 6 panels → `R3_two_by_three_grid` (2×3) — most common
- 9 panels → 3×3 GridSpec
- 12+ panels → `R7_dense_2x6_lineup` (2×6) or 3×4

**Common chart families** (per corpus):
- SHAP dependence panels
- ALE / PDP main effects
- Predicted-vs-actual scatter per model
- Multi-condition box plots
- Multi-feature density scatter

**Anchor cases:**
- `期刊图表复现：多面板SHAP依赖图展示分子特征对自由基反应速率的非线性影响`
- `期刊配图：基于高斯核密度的3x3多面板散点图评估混合水文模型模拟性能`
- `期刊复现：多面板回归预测散点图对比不同模型真实与预测偏差`
- `期刊配图：利用多面板2D-PDP揭示机器学习模型的双变量交互与控制边界`

---

## A3 — `global_local` (6%)

Global summary panel **plus** local-explanation panel. Nearly always SHAP-flavored: global importance bar + local beeswarm/dependence.

**Required motifs:**
- Top/left panel = global (importance ranking, summary statistic)
- Bottom/right panel = local (beeswarm color-coded by feature value, individual force plot)
- Shared y-feature ordering across panels
- Coupled palette (low→high feature value)

**Grid:** `R10_asymmetric_top_wide` for hero global + 2 local; `R1_two_panel_horizontal` (1×2) for global+local pair.

**Anchor cases:**
- `期刊配图复现 _ 手把手教你用 Python 绘制 SHAP 全局与局部解释组合图`
- `期刊复现：基于SHAP复合图揭示高能分子特征对性能的全局与局部影响`
- `期刊复现：组合重要性条形图与SHAP蜂群图解析特征的全局预测贡献`

---

## A4 — `n×n_pairwise` (6%)

Exhaustive cross-comparison. n×n grid where (i, j) shows the joint behaviour of feature i with feature j.

**Required motifs:**
- Diagonal: histogram + KDE (univariate distribution)
- Upper triangle: correlation number on tinted background, spines hidden
- Lower triangle: hollow scatter, alpha 0.6
- Outer-only labels (left column + bottom row)
- `hspace=wspace=0.05` (tight)

**Grid:** `R5_n_by_n_pairwise`.

**Anchor cases:**
- `期刊复现：Nature同款皮尔逊热力图`
- `期刊复现：基于上三角局部填充饼图的相关性矩阵解析合金成分与性能关系`
- `期刊配图：基于高斯核密度的3x3多面板散点图评估混合水文模型模拟性能`

---

## A5 — `marginal_joint` (5%)

Center panel = main relationship; top/right = marginal distributions. Common for density scatter, predicted-vs-actual, residual diagnostics.

**Required motifs:**
- Density-sorted center scatter (`density_color_scatter`)
- Marginal histograms on top + right (`marginal_axes_grid`)
- Perfect-fit diagonal (when predicted-vs-actual)
- Equal-aspect ratio in main panel
- Marginal axes turned off (decoration only)

**Grid:** `R8_main_with_marginal`.

**Anchor cases:**
- `复现 CEJ 顶刊神图_Python 绘制"密度散点+边缘直方图"多面板组合图`
- `Python绘图实战：基于GridSpec构建多面板回归预测与边缘分布组合图`
- `期刊复现：联合等高线热图与边缘分布图验证模型预测精度与参数寻优`
- `期刊复现：通过带边缘密度的联合残差图全面评估预测模型性能`

---

## A6 — `train_test_diagnostic` (5%)

Compares training-fold vs holdout-fold performance. Either a single panel with split colors, or two panels side-by-side.

**Required motifs:**
- Train (`#4C78A8`) vs Test (`#E45756`) palette
- Vertical split line at train/test boundary (time-series only)
- Metric box per fold (R², RMSE)
- Perfect-fit diagonal if predicted-vs-actual

**Grid:** `R0_single_panel` with split-colored points, OR `R1_two_panel_horizontal` (1×2).

**Anchor cases:**
- `期刊图表复现：基于预测区间与训练_测试划分的时序拟合效果对比`
- `期刊复现：基于梯度提升树(GBDT)的多面板预测误差评估图`
- `期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱`

---

## A7 — `composite_two_lane` (5%)

Two parallel lanes that complement each other but address the same scientific question — left = importance ranking, right = effect signature; or top = bar chart, bottom = beeswarm.

**Required motifs:**
- Both panels share the same y-axis order (features ranked by importance)
- Shared palette for the cross-cut categorical variable
- Coupled annotation (zero ref on both)

**Grid:** `R1_two_panel_horizontal` or asymmetric (60/40 width).

**Anchor cases:**
- `复现顶刊_拒绝千篇一律的SHAP图，用Matplotlib手绘一张"蜂群+条形"组合图`
- `期刊复刻：多面板结合XGBoost特征重要性棒棒糖图与SHAP蜂群图`
- `期刊复现：组合重要性条形图与SHAP蜂群图解析特征的全局预测贡献`

---

## A8 — `mirror_compare` (5%)

Two conditions in mirrored layout — bipolar lollipops (`+ALE` right-side, `−ALE` left-side), or mirror radial roses, or top/bottom mirror box.

**Required motifs:**
- Symmetric x-axis or symmetric polar
- Two-color palette tied to sign or condition (`bipolar_ALE` palette)
- Centerline at 0 (`dotted_zero_axhline` or `axvline`)
- Same y-feature order on both sides

**Grid:** `R0_single_panel` (mirror polar) or `R1_two_panel_horizontal` (mirror cartesian).

**Anchor cases:**
- `期刊复现 _ Python绘制"镜像玫瑰"组合图`
- `期刊复刻：通过双侧棒棒糖图解析特征重要性与ALE主效应方向`
- `进阶绘图：解决"多变量拥挤"痛点——Python 绘制带显著性星号与斜向色条的三角热图`

---

## A9 — `inset_overlay` (4%)

Main panel + small inset that shows a zoom or distribution.

**Required motifs:**
- Main panel renders complete narrative independently
- Inset has opaque white background, thin dark border, zorder ≥ 10
- Inset position: `[0.55, 0.35, 0.40, 0.35]` axes fraction (corpus default)
- Inset turns off legend; main legend stays in main panel

**Grid:** `R9_inset_overlay`.

**Anchor cases:**
- `复现顶刊_Python绘制"主图+嵌入雨云图"组合，完美展示模型泛化能力`
- `期刊复现：Nature Nanotechnology 经典"画中画"组合图`

---

## Cross-arc decision matrix

| Question | If Yes | If No |
|---|---|---|
| Will headline figure carry one claim? | A1 hero | continue |
| 4+ parallel panels of same family? | A2 multipanel_grid | continue |
| SHAP/ALE global+local pair? | A3 global_local | continue |
| Pairwise correlation matrix? | A4 n×n_pairwise | continue |
| Center + marginal distributions? | A5 marginal_joint | continue |
| Train/test diagnostic? | A6 train_test_diagnostic | continue |
| Two complementary lanes (bar + beeswarm)? | A7 composite_two_lane | continue |
| Bipolar / mirror layout? | A8 mirror_compare | continue |
| Main + zoom-in inset? | A9 inset_overlay | A1 single_focus |

## Arc → Recipe → Family quick-bind

| Arc | Default Grid | Default Family | Required Idioms (from `05`) |
|---|---|---|---|
| `hero` | R0 | radar / single dramatic chart | I11 polygon_polar_grid (radar), I7, I13 |
| `single_focus` | R0 | scatter_regression / forest / box | I1, I2 (when scatter_reg), I7 |
| `multipanel_grid` | R3 (2×3) / R5 (3×3) | shap / ale_pdp / scatter_regression | I7, I13, I4 |
| `global_local` | R10 (top-wide) / R1 | shap_composite | I7, I4, shared y-order |
| `n×n_pairwise` | R5 | heatmap_pairwise | I3, hollow scatter, no spines on upper |
| `marginal_joint` | R8 | density_scatter | I6, I2, marginal off |
| `train_test_diagnostic` | R0 / R1 | scatter_regression / time_series_pi | I1, I2, I9 |
| `composite_two_lane` | R1 | shap composite / lollipop+beeswarm | shared y-order, I4 |
| `mirror_compare` | R0 (polar) / R1 | mirror_radial / lollipop bipolar | I4, bipolar palette |
| `inset_overlay` | R9 | scatter_regression + raincloud inset | inset zorder, I7 |

## Helpers contract

```python
def select_narrative_arc(dataProfile: dict, chartPlan: dict) -> str:
    """Return one of the 10 arc keys. Phase 2 calls this before binding charts.

    Heuristics (in priority order):
      - dataProfile.has_train_test_split → 'train_test_diagnostic'
      - chartPlan.requested_inset → 'inset_overlay'
      - chartPlan.has_marginal_distribution → 'marginal_joint'
      - chartPlan.has_correlation_matrix → 'n×n_pairwise'
      - chartPlan.has_shap_global + chartPlan.has_shap_local → 'global_local'
      - chartPlan.bipolar_or_mirror → 'mirror_compare'
      - len(chartPlan.panels) >= 4 and homogeneous family → 'multipanel_grid'
      - len(chartPlan.panels) == 2 with different families → 'composite_two_lane'
      - chartPlan.is_headline → 'hero'
      - default → 'single_focus'
    """

def arc_required_motifs(arc: str) -> list[str]:
    """Return the list of motif keys (from 05-annotation-idioms.md) that are
    mandatory for this arc. Phase 4 QA fails when a required motif is missing."""

def arc_default_grid(arc: str, panel_count: int = 1) -> str:
    """Return the default GridSpec recipe key (from 04-grid-recipes.md)."""
```

## QA contract

`render-qa` (Phase 4) checks:

- `narrativeArcSelected`: every plan must declare an arc key
- `arcMotifCoverage`: every required motif (from `arc_required_motifs`) is applied at least once in the figure
- `arcGridConsistency`: chosen grid must match `arc_default_grid` or be explicitly overridden in plan
- `panelLabelCoverage`: when arc is `multipanel_grid` / `n×n_pairwise` / `composite_two_lane`, all panels have a/b/c labels

Failure → Phase 3 retry with the specific arc-motif gap explained.
