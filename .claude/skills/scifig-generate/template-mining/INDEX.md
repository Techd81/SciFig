# Template Mining — Knowledge Base Index

**Source**: 94 顶刊复刻案例 distilled from all Markdown files under `D:\SciFig\template\` (including `articles`, `articles2`, and `articles3`; Nature, Nature Comms, Nature Nanotechnology, Cell, Advanced Science, CEJ, Materials Today, JECE, JBE, MGEA, etc.). Current extraction records 370 Markdown image references, 325 unique image URLs, and 418 code blocks.

**Purpose**: A queryable knowledge base of the visual-grammar patterns, color systems, layer-stacking recipes, multi-panel layouts, in-axes annotations, and scientific narrative arcs that real top-journal Python figures actually use.

**This index is the only file phases load by default**. Each topic file is loaded on-demand by Phase 2/3 when a specific decision needs it.

## Directory Map

```
template-mining/
├── INDEX.md                        <- this file
├── case-index.json                 machine-readable metadata for 94 cases, including image refs + code blocks
├── 01-rcparams-kernel.md           顶刊审美内核 (the rcParams every chart starts from)
├── 02-zorder-recipes.md            三明治图层法 (per-family layer stacking)
├── 03-palette-bank.md              实战色谱库 (named palettes + case anchors)
├── 04-grid-recipes.md              GridSpec 多面板配方 (R0–R11)
├── 05-annotation-idioms.md         in-axes annotation patterns (I1–I14)
├── 06-narrative-arcs.md            科学叙事弧 (A1–A9 story shapes)
├── CASE_LEARNING_PROTOCOL.md        one-Markdown-at-a-time study and replica protocol
├── 07-techniques/                  per-family deep-dive (loaded only on demand)
│   ├── radar.md
│   ├── shap-composite.md
│   ├── dual-axis.md
│   ├── heatmap-pairwise.md
│   ├── marginal-joint.md
│   ├── ml-model-diagnostics.md
│   ├── time-series-pi.md
│   ├── lollipop-bipolar.md
│   ├── gradient-box.md
│   ├── adsorption-isotherm.md
│   ├── forest-hr-facet.md
│   ├── parity-ci-matrix.md
│   ├── gam-residual-diagnostic.md
│   ├── pls-pm-path-model.md
│   ├── density-parity-matrix.md
│   └── inset-distribution.md
└── _extraction/                    extractor scripts + raw stats (do not load)
    ├── extract.py                  structural extraction (images, code blocks, rcParams, palette, grid, legend, annotation, export)
    ├── enrich.py                   semantic enrichment (narrative arc, signature tricks, image evidence)
    ├── stats.md                    auto-generated frequency tables
    ├── stats.json                  structured stats consumed by helpers
    ├── narratives.md               per-case digest
    ├── palette-harvest.json        per-case hex codes
    └── batch_*.txt                 batch lists for any future agent mining
```

## Loading Protocol

1. **Always load** `INDEX.md` (this file) before any phase-2/3 decision.
2. **Phase 2** (chart + panel selection):
   - Lookup `case-index.json` to find ≥3 cases with matching `chart_families` or `narrative_arc`.
   - Inspect `images`, `image_evidence`, `code_blocks`, and `visual_signals`; image links embedded in Markdown are evidence even when no standalone image file exists under `template/`.
   - Read `06-narrative-arcs.md` to confirm story shape.
   - Read `04-grid-recipes.md` if `panel_count > 1`.
3. **Phase 3** (code generation):
   - Read `01-rcparams-kernel.md` for the global aesthetic baseline.
   - Read `02-zorder-recipes.md` for the matching chart family.
   - Read `03-palette-bank.md` to bind the chosen palette name to actual hex codes.
   - Read `05-annotation-idioms.md` to apply in-axes labels.
   - Read `07-techniques/<family>.md` only if the chart family appears in the per-family directory.
4. **Phase 4** (render QA): every required motif from the chosen narrative arc + chart family must be present; failures route back to Phase 3.

## Distilled Universal Findings (n=94, regex-verified)

These findings are derived from `_extraction/stats.json` — frequencies are exact and reproducible.

### 0. Markdown image evidence is part of the template, not optional context

| Evidence | Count |
|---|---:|
| Markdown cases learned | 94 |
| Cases with image refs | 82/94 |
| Image refs extracted | 370 |
| Unique image URLs | 325 |
| Cases with code blocks | 93/94 |
| Code blocks analyzed | 418 |

Any template-learning run that only scans standalone image files is incomplete. The corpus stores most visual references as Markdown image links, so Phase 2 and Phase 3 must read `images` / `image_evidence` alongside code-derived signals before selecting a visual grammar.

### 1. The rcParams kernel is dominant but **not** universal

Real frequencies of canonical "顶刊感" tokens:

| Key | Cases declaring | % | Most-used value |
|---|---|---|---|
| `xtick.direction` / `ytick.direction` = `'in'` | 68/94 and 67/94 | 72% / 71% | `'in'` dominates declared values |
| `axes.linewidth` | 70/94 | 74% | `1.5` (56) / `1.2` (11) |
| `font.family` declared | 79/94 | 84% | Times New Roman / Arial dominated |
| `font.size` | 70/94 | 74% | `16` (48) / `14` (18) |
| `mathtext.fontset` = `'stix'` | 62/94 | 66% | `'stix'` (61) |
| `savefig.dpi` declared | 30/94 | 32% | `600` (28) |
| `savefig.bbox` declared | 26/94 | 28% | `'tight'` (25) |

> **Correction note**: Earlier drafts of this index claimed `tick.direction='in'` was 77/77; the current regex-verified count is 68/94 for x ticks and 67/94 for y ticks. Earlier `savefig.dpi=600` claim of "60+/77" was incorrect; real count is 28/94.

The `dpi=600` and `bbox='tight'` are typically supplied at **savefig call time** (rather than in rcParams) in the cases that don't set them globally — Phase 3 should set them in `apply_journal_kernel` regardless.

### 2. zorder layering is the dominant rendering pattern

| Pattern | Cases | % |
|---|---|---|
| Any explicit `zorder=` use | 61/94 | 65% |
| ≥3 distinct zorder levels in same chart | common in dense families | see `_extraction/stats.json` |

See `02-zorder-recipes.md` for per-family recipes.

### 3. Palette is anchored, not invented

Top corpus-wide hex codes (≥2 cases):

| Hex | Cases | Use |
|---|---|---|
| `#1F77B4` | 10 | tableau default; multi-model bars |
| `#D62728` | 6 | tableau default; warning/optimal |
| `#313695`, `#A50026` | 2 each | RdBu/seismic anchors |
| `#4C72B0`, `#4B74B2`, `#4A90E2` | 2 each | seaborn cool blue |
| `#808080`, `#FF7F0E` | 2 each | reference gray, secondary |

But across cases the *named palettes* (e.g. `nature_radar_dual`, `morandi_sci_4`) recur. Bind via `03-palette-bank.md` rather than picking individual hexes.

### 4. Narrative arcs are bounded — only 10 distinct story shapes

| Arc | Cases | Default grid |
|---|---|---|
| `single_focus` | 31 (33%) | R0 |
| `multipanel_grid` | 27 (29%) | R3 (2×3) / R5 (3×3) |
| `marginal_joint` | 5 (5%) | R8 |
| `composite_two_lane` | 5 (5%) | R1 |
| `global_local` | 5 (5%) | R10 (top-wide) |
| `hero` | 5 (5%) | R0 |
| `n×n_pairwise` | 5 (5%) | R5 |
| `train_test_diagnostic` | 4 (4%) | R0 / R1 |
| `mirror_compare` | 4 (4%) | R0 / R1 |
| `inset_overlay` | 3 (4%) | R9 |

See `06-narrative-arcs.md` for the full decision matrix.

### 5. Chart family distribution (multi-label, n=94)

| Family | Cases | Deep-dive file |
|---|---|---|
| scatter_regression | 69 | (covered in `02-zorder-recipes.md § scatter-regression`) |
| ALE / PDP | 36 | `07-techniques/lollipop-bipolar.md` covers ALE bipolar |
| SHAP composite | 35 | `07-techniques/shap-composite.md` |
| dual_axis | 21 | `07-techniques/dual-axis.md` |
| forest | 16 | `02-zorder-recipes.md § forest` |
| heatmap | 13 | covered in pairwise + general |
| heatmap_pairwise | 11 | `07-techniques/heatmap-pairwise.md` |
| box / violin | 13 | `07-techniques/gradient-box.md` |
| radar | 8 | `07-techniques/radar.md` |
| density_scatter | 7 | covered in `marginal-joint.md` |
| marginal_joint | 6 | `07-techniques/marginal-joint.md` |

### 6. Top signature tricks (regex-verified)

| Trick | Cases | Idiom doc |
|---|---|---|
| `alpha_layered_scatter` | 24 | `02-zorder-recipes.md` |
| `density_color_scatter` | 16 | `05-annotation-idioms.md § I6` |
| `group_divider_axvline` | 14 | `05-annotation-idioms.md § I3` |
| `raincloud_combo` | 13 | (matches inset overlay + raincloud combo) |
| `metric_text_box` | 12 | `05-annotation-idioms.md § I1` |
| `pvalue_stars_overlay` | 9 | `05-annotation-idioms.md § I5` |
| `axes_inset_overlay` | 8 | `04-grid-recipes.md § R9` |
| `dotted_zero_axhline` | 8 | `05-annotation-idioms.md § I4` |
| `colored_marker_edge` | 8 | `05-annotation-idioms.md § I7` |
| `twin_axes_color_spines` | 7 | `05-annotation-idioms.md § I8` |

## AI / ML Template Routing

Computer, AI, and machine-learning prompts must first check the `ml-model-diagnostics` deep-dive before falling back to generic prediction charts. When user text or `dataProfile` includes Random Forest/RF/RFR, XGBoost, LightGBM, GBDT, classifier/regressor, train/test metrics, AUC/F1/accuracy, RMSE/MAE/R2, SHAP, feature importance, or residual fields, Phase 2 should recommend a template-backed ML bundle and Phase 3 should clone the matching case composition before adapting data labels.

High-value anchors:

- RF triptych: `期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱_1777456409.md`
- RF EFI + SHAP: `期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化_1777456510.md`
- Incremental feature selection: `拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272.md`
- PSO + SHAP optimization: `基于PSO多目标优化与SHAP可解释分析的回归预测模型框架_1777461729.md`

## Style Discipline Rules (consolidated from 94 cases)

| Rule | Frequency | Source |
|------|-----------|--------|
| `xtick.direction='in'`, `ytick.direction='in'` | 68/94 and 67/94 | `01-rcparams-kernel.md` |
| `mathtext.fontset = 'stix'` | 62/94 (66%) | `01-rcparams-kernel.md` |
| `axes.linewidth = 1.5` (hero) or `1.2` (compact) | 67/94 common declared values | `01-rcparams-kernel.md` |
| Use `zorder=` explicitly to stack layers | 61/94 (65%) | `02-zorder-recipes.md` |
| In-plot text annotation with `transform=ax.transAxes` | 34/94 (36%) | `05-annotation-idioms.md` |
| Reference line `axvline`/`axhline` at meaningful X/Y | 28/94 (30%) | `05-annotation-idioms.md` |
| `GridSpec` for non-trivial multi-panel | 19/94 (20%) | `04-grid-recipes.md` |
| `colorbar(...)` for sequential color encoding | 23/94 (24%) | `03-palette-bank.md` |
| Despine top + right (`set_visible(False)` form) | 13/94 (14%) | optional, family-dependent |

> **Correction note**: An earlier draft claimed despine was 64/77; the current verified count is 13/94. Despine is **not** a corpus-universal rule — it's family-dependent (forest plots keep all spines, polar plots replace them entirely).

## When NOT to Use This Knowledge Base

- **Single quick chart, no journal style required** — the regular `phases/03` flow is fine.
- **User explicitly requested a different aesthetic** (e.g., presentation slide, dashboard) — these patterns are tuned for paper submission.
- **Custom domain not represented in the 94 cases** (e.g. genomics single-cell UMAP, clinical KM) — fall back to `specs/domain-playbooks.md` and don't force a mismatch.

## Adding New Cases

When the user supplies new reference figures or articles:

1. Save markdown anywhere under local ignored `template/` (for example `template/articles4/articles/`). The template corpus is evidence, not a submitted skill payload.
2. Re-run `_extraction/extract.py` then `_extraction/enrich.py` to refresh `case-index.json`, `stats.md`, `narratives.md`.
3. Pick exactly one Markdown case and follow `CASE_LEARNING_PROTOCOL.md`: full read, image/code ledger, local replica, gap comparison, distilled essence.
4. If a new motif emerges, add an entry to `05-annotation-idioms.md` or a new `07-techniques/<name>.md`.
5. If article code should improve generated figures, run `phases/05-template-distill.md` and `specs/template-distillation-contract.md`; promote reusable code into helpers/generators before changing coordinator prose.
6. Don't overwrite distilled patterns silently — append, then mark superseded entries.

## Coordinator Cheat-Sheet

When you find yourself wondering "how would Nature draw this?":

| User intent | Files to load |
|-------------|---------------|
| Predicted vs actual scatter | `01-rcparams-kernel.md`, `02-zorder-recipes.md § scatter-regression`, `05-annotation-idioms.md § I1, I2`, `06-narrative-arcs.md § A1` |
| Parity CI matrix | `04-grid-recipes.md § R2`, `02-zorder-recipes.md § scatter-regression`, `03-palette-bank.md § spt_parity_2`, `07-techniques/parity-ci-matrix.md` |
| Incremental feature selection curve | `07-techniques/ml-model-diagnostics.md § Incremental Feature Selection`, `template-visual-motifs.md § incremental_feature_selection_curve`, `03-palette-bank.md § ml_model_performance_10` |
| Multi-panel SHAP (global + local) | `04-grid-recipes.md § R10`, `06-narrative-arcs.md § A3`, `07-techniques/shap-composite.md` |
| SHAP bar + beeswarm + inset pie | `04-grid-recipes.md § R1`, `07-techniques/shap-composite.md § Executable mapping: bar + beeswarm + inset pie`, `template-visual-motifs.md § shap_bar_beeswarm_inset_pie` |
| XGBoost lollipop + SHAP beeswarm | `07-techniques/shap-composite.md § Executable mapping: lollipop + SHAP beeswarm board`, `template-visual-motifs.md § lollipop_shap_beeswarm_board` |
| SHAP bar + standalone pie + summary | `07-techniques/shap-composite.md § Executable mapping: bar + standalone pie + summary beeswarm`, `template-visual-motifs.md § shap_bar_pie_summary_board` |
| PSO / Pareto + SHAP framework | `07-techniques/ml-model-diagnostics.md § PSO / Pareto Optimization + SHAP`, `07-techniques/radar.md`, `07-techniques/shap-composite.md`, `template-visual-motifs.md § pso_shap_optimization_framework` |
| Mirror radial rose | `06-narrative-arcs.md § A8`, `07-techniques/radar.md § Executable mapping: mirror radial bar board`, `template-visual-motifs.md § mirror_radial_bar_board` |
| Forest plot for clinical effects | `02-zorder-recipes.md § forest`, `04-grid-recipes.md § R6`, `07-techniques/forest-hr-facet.md` |
| Heatmap with pairwise correlation | `04-grid-recipes.md § R5`, `06-narrative-arcs.md § A4`, `07-techniques/heatmap-pairwise.md` |
| Red-blue bubble correlation matrix | `04-grid-recipes.md § R5`, `03-palette-bank.md § materials_teal_salmon_correlation`, `07-techniques/heatmap-pairwise.md § Executable mapping: red-blue bubble correlation matrix`, `template-visual-motifs.md § bubble_correlation_matrix` |
| Two-axis combo (porosity + strength) | `02-zorder-recipes.md § dual-axis`, `05-annotation-idioms.md § I8`, `07-techniques/dual-axis.md` |
| Textbook dual-Y bar + spline | `03-palette-bank.md § materials_porosity_terracotta`, `07-techniques/dual-axis.md § Executable mapping: textbook bar + spline dual axis`, `template-visual-motifs.md § textbook_dual_axis_bar_line` |
| Dual-Y histogram + cumulative grid | `07-techniques/dual-axis.md § Executable mapping: 3x3 histogram + cumulative-frequency grid`, `template-visual-motifs.md § dual_axis_hist_cumfreq_grid` |
| Threshold hump regression | `02-zorder-recipes.md § scatter-regression`, `07-techniques/threshold-regression.md § Executable mapping: hump threshold regression`, `template-visual-motifs.md § hump_threshold_regression` |
| Distance-decay regression | `02-zorder-recipes.md § scatter-regression`, `07-techniques/distance-decay-regression.md` |
| Bayesian ridge + heat strip | `04-grid-recipes.md § R4/R7 variants`, `07-techniques/ridgeline-heatmap.md § Executable mapping: Bayesian ridge heatmap board`, `template-visual-motifs.md § bayesian_ridge_heatmap_board` |
| Adsorption isotherm condition board | `04-grid-recipes.md § R3`, `02-zorder-recipes.md § adsorption-isotherm`, `03-palette-bank.md § cej_vibrant_3`, `07-techniques/adsorption-isotherm.md` |
| Time-series with prediction interval | `02-zorder-recipes.md § time-series`, `05-annotation-idioms.md § I9` |
| GAM log-log + residual diagnostic | `04-grid-recipes.md § R1`, `02-zorder-recipes.md § scatter-regression`, `07-techniques/gam-residual-diagnostic.md` |
| Main + inset residual raincloud | `04-grid-recipes.md § R1/R9`, `03-palette-bank.md § mgea_true_pred_green_orange`, `07-techniques/inset-distribution.md` |
| Radar / polar comparison | `06-narrative-arcs.md § A1 hero`, `07-techniques/radar.md`, `05-annotation-idioms.md § I11` |
| Density scatter + marginal | `04-grid-recipes.md § R8`, `06-narrative-arcs.md § A5`, `07-techniques/marginal-joint.md` |
| Nested model marginal matrix | `04-grid-recipes.md § R8 Variant C`, `03-palette-bank.md § spt_parity_2`, `07-techniques/marginal-joint.md` |
| Gradient-fill box plot | `05-annotation-idioms.md § I12`, `07-techniques/gradient-box.md` |
| Mirror radial / bipolar lollipop | `06-narrative-arcs.md § A8`, `07-techniques/radar.md § Executable mapping: mirror radial bar board`, `07-techniques/lollipop-bipolar.md § Executable mapping: PFI + signed ALE paired lollipops`, `03-palette-bank.md § bipolar_ALE`, `template-visual-motifs.md § mirror_radial_bar_board`, `template-visual-motifs.md § bipolar_lollipop_ale_board` |
| Main + inset distribution | `04-grid-recipes.md § R9`, `06-narrative-arcs.md § A9`, `07-techniques/inset-distribution.md` |

## Re-extraction Protocol

When the article corpus changes:

```bash
cd D:/SciFig
python .claude/skills/scifig-generate/template-mining/_extraction/extract.py
python .claude/skills/scifig-generate/template-mining/_extraction/enrich.py
```

This refreshes `case-index.json`, `stats.md`, `stats.json`, `narratives.md`, `palette-harvest.json`. Then audit this INDEX file's frequency tables and update the section "Distilled Universal Findings" to match the new numbers. For executable improvements, continue with Phase 5, but only after a one-case learning record proves the Markdown was read and replicated.
