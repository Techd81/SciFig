# Template Mining �?Knowledge Base Index

**Source**: 94 顶刊复刻案例 distilled from all Markdown files under `D:\SciFig\template\` (including `articles`, `articles2`, and `articles3`; Nature, Nature Comms, Nature Nanotechnology, Cell, Advanced Science, CEJ, Materials Today, JECE, JBE, MGEA, etc.). Current extraction records 370 Markdown image references, 325 unique image URLs, and 418 code blocks.

**Purpose**: A queryable knowledge base of the visual-grammar patterns, color systems, layer-stacking recipes, multi-panel layouts, in-axes annotations, and scientific narrative arcs that real top-journal Python figures actually use.

**This index is the only file phases load by default**. Each topic file is loaded on-demand by Phase 2/3 when a specific decision needs it.

## Directory Map

```
knowledge/
├── INDEX.md                        <- this file
├── case-index.json                 machine-readable metadata for 94 cases
├── case-evidence.json              bulk evidence (images, code blocks; gitignored)
├── CASE_LEARNING_PROTOCOL.md       one-Markdown-at-a-time study protocol
├── modules/
│   ├── 01-rcparams-kernel.md       rcParams baseline (hero / compact / default)
│   ├── 02-zorder-recipes.md        per-family layer stacking
│   ├── 03-palette-bank.md          named palettes + case anchors
│   ├── 04-grid-recipes.md          GridSpec multi-panel recipes (R0–R11)
│   ├── 05-annotation-idioms.md     in-axes annotation patterns (I1–I14)
│   └── 06-narrative-arcs.md        story shapes (A1–A10)
├── techniques/                     per-family deep-dives (load on demand)
│   ├── radar.md
│   ├── shap-composite.md
│   ├── dual-axis.md
│   ├── heatmap-pairwise.md
│   └── ... (21 technique files)
└── scripts/                        extractor scripts (do not load during plotting)
    ├── extract.py
    ├── enrich.py
    ├── binding_probe.py
    └── stats.md / stats.json
```

## Loading Protocol

1. **Always load** `INDEX.md` (this file) before any phase-2/3 decision.
2. **Phase 2** (chart + panel selection):
   - Lookup `case-index.json` to find �? cases with matching `chart_families` or `narrative_arc`.
   - For deeper evidence (`images`, `image_evidence`, `code_blocks`, `visual_signals`), read the matching case in `case-evidence.json` (local, regenerable; `case-index.json` is the slim routing index). Image links embedded in Markdown are evidence even when no standalone image file exists under `template/`.
   - Read `modules/06-narrative-arcs.md` to confirm story shape.
   - Read `modules/04-grid-recipes.md` if `panel_count > 1`.
3. **Phase 3** (code generation):
   - Read `modules/01-rcparams-kernel.md` for the global aesthetic baseline.
   - Read `modules/02-zorder-recipes.md` for the matching chart family.
   - Read `modules/03-palette-bank.md` to bind the chosen palette name to actual hex codes.
   - Read `modules/05-annotation-idioms.md` to apply in-axes labels.
   - Read `knowledge/techniques/<family>.md` only if the chart family appears in the per-family directory.
4. **Phase 4** (render QA): every required motif from the chosen narrative arc + chart family must be present; failures route back to Phase 3.

## Distilled Universal Findings (n=94, regex-verified)

These findings are derived from `knowledge/scripts/stats.json` �?frequencies are exact and reproducible.

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

Real frequencies of canonical "顶刊�? tokens:

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

The `dpi=600` and `bbox='tight'` are typically supplied at **savefig call time** (rather than in rcParams) in the cases that don't set them globally �?Phase 3 should set them in `apply_journal_kernel` regardless.

### 2. zorder layering is the dominant rendering pattern

| Pattern | Cases | % |
|---|---|---|
| Any explicit `zorder=` use | 61/94 | 65% |
| �? distinct zorder levels in same chart | common in dense families | see `knowledge/scripts/stats.json` |

See `modules/02-zorder-recipes.md` for per-family recipes.

### 3. Palette is anchored, not invented

Top corpus-wide hex codes (�? cases):

| Hex | Cases | Use |
|---|---|---|
| `#1F77B4` | 10 | tableau default; multi-model bars |
| `#D62728` | 6 | tableau default; warning/optimal |
| `#313695`, `#A50026` | 2 each | RdBu/seismic anchors |
| `#4C72B0`, `#4B74B2`, `#4A90E2` | 2 each | seaborn cool blue |
| `#808080`, `#FF7F0E` | 2 each | reference gray, secondary |

But across cases the *named palettes* (e.g. `nature_radar_dual`, `morandi_sci_4`) recur. Bind via `modules/03-palette-bank.md` rather than picking individual hexes.

### 4. Narrative arcs are bounded �?only 10 distinct story shapes

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

See `modules/06-narrative-arcs.md` for the full decision matrix.

### 5. Chart family distribution (multi-label, n=94)

| Family | Cases | Deep-dive file |
|---|---|---|
| scatter_regression | 69 | (covered in `02-zorder-recipes.md § scatter-regression`) |
| ALE / PDP | 36 | `knowledge/techniques/lollipop-bipolar.md` covers ALE bipolar |
| SHAP composite | 35 | `knowledge/techniques/shap-composite.md` |
| dual_axis | 21 | `knowledge/techniques/dual-axis.md` |
| forest | 16 | `02-zorder-recipes.md § forest` |
| heatmap | 13 | covered in pairwise + general |
| heatmap_pairwise | 11 | `knowledge/techniques/heatmap-pairwise.md` |
| box / violin | 13 | `knowledge/techniques/gradient-box.md` |
| radar | 8 | `knowledge/techniques/radar.md` |
| density_scatter | 7 | covered in `marginal-joint.md` |
| marginal_joint | 6 | `knowledge/techniques/marginal-joint.md` |

### 6. Top signature tricks (regex-verified)

| Trick | Cases | Idiom doc |
|---|---|---|
| `alpha_layered_scatter` | 24 | `modules/02-zorder-recipes.md` |
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

- RF triptych: `期刊复现：基于随机森�?RF)的多维模型性能评估与预测残差可视化图谱_1777456409.md`
- RF EFI + SHAP: `期刊复现：随机森�?RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化_1777456510.md`
- Incremental feature selection: `拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272.md`
- PSO + SHAP optimization: `基于PSO多目标优化与SHAP可解释分析的回归预测模型框架_1777461729.md`

## Style Discipline Rules (consolidated from 94 cases)

| Rule | Frequency | Source |
|------|-----------|--------|
| `xtick.direction='in'`, `ytick.direction='in'` | 68/94 and 67/94 | `modules/01-rcparams-kernel.md` |
| `mathtext.fontset = 'stix'` | 62/94 (66%) | `modules/01-rcparams-kernel.md` |
| `axes.linewidth = 1.5` (hero) or `1.2` (compact) | 67/94 common declared values | `modules/01-rcparams-kernel.md` |
| Use `zorder=` explicitly to stack layers | 61/94 (65%) | `modules/02-zorder-recipes.md` |
| In-plot text annotation with `transform=ax.transAxes` | 34/94 (36%) | `modules/05-annotation-idioms.md` |
| Reference line `axvline`/`axhline` at meaningful X/Y | 28/94 (30%) | `modules/05-annotation-idioms.md` |
| `GridSpec` for non-trivial multi-panel | 19/94 (20%) | `modules/04-grid-recipes.md` |
| `colorbar(...)` for sequential color encoding | 23/94 (24%) | `modules/03-palette-bank.md` |
| Despine top + right (`set_visible(False)` form) | 13/94 (14%) | optional, family-dependent |

> **Correction note**: An earlier draft claimed despine was 64/77; the current verified count is 13/94. Despine is **not** a corpus-universal rule �?it's family-dependent (forest plots keep all spines, polar plots replace them entirely).

## When NOT to Use This Knowledge Base

- **Single quick chart, no journal style required** �?the regular `phases/03` flow is fine.
- **User explicitly requested a different aesthetic** (e.g., presentation slide, dashboard) �?these patterns are tuned for paper submission.
- **Custom domain not represented in the 94 cases** (e.g. genomics single-cell UMAP, clinical KM) �?fall back to `specs/domain-playbooks.md` and don't force a mismatch.

## Adding New Cases

When the user supplies new reference figures or articles:

1. Save markdown anywhere under local ignored `template/` (for example `template/articles4/articles/`). The template corpus is evidence, not a submitted skill payload.
2. Re-run `knowledge/scripts/extract.py` then `knowledge/scripts/enrich.py` to refresh `case-index.json`, `stats.md`, `narratives.md`.
3. Pick exactly one Markdown case and follow `CASE_LEARNING_PROTOCOL.md`: full read, image/code ledger, local replica, gap comparison, distilled essence.
4. If a new motif emerges, add an entry to `modules/05-annotation-idioms.md` or a new `knowledge/techniques/<name>.md`.
5. If article code should improve generated figures, run `phases/05-template-distill.md` and `specs/template-distillation-contract.md`; promote reusable code into helpers/generators before changing coordinator prose.
6. Don't overwrite distilled patterns silently �?append, then mark superseded entries.

## Coordinator Cheat-Sheet

When you find yourself wondering "how would Nature draw this?":

| User intent | Files to load |
|-------------|---------------|
| Predicted vs actual scatter | `modules/01-rcparams-kernel.md`, `02-zorder-recipes.md § scatter-regression`, `05-annotation-idioms.md § I1, I2`, `06-narrative-arcs.md § A1` |
| Parity CI matrix | `04-grid-recipes.md § R2`, `02-zorder-recipes.md § scatter-regression`, `03-palette-bank.md § spt_parity_2`, `knowledge/techniques/parity-ci-matrix.md` |
| Incremental feature selection curve | `knowledge/techniques/ml-model-diagnostics.md § Incremental Feature Selection`, `template-visual-motifs.md § incremental_feature_selection_curve`, `03-palette-bank.md § ml_model_performance_10` |
| Multi-panel SHAP (global + local) | `04-grid-recipes.md § R10`, `06-narrative-arcs.md § A3`, `knowledge/techniques/shap-composite.md` |
| SHAP bar + beeswarm + inset pie | `04-grid-recipes.md § R1`, `knowledge/techniques/shap-composite.md § Executable mapping: bar + beeswarm + inset pie`, `template-visual-motifs.md § shap_bar_beeswarm_inset_pie` |
| XGBoost lollipop + SHAP beeswarm | `knowledge/techniques/shap-composite.md § Executable mapping: lollipop + SHAP beeswarm board`, `template-visual-motifs.md § lollipop_shap_beeswarm_board` |
| SHAP bar + standalone pie + summary | `knowledge/techniques/shap-composite.md § Executable mapping: bar + standalone pie + summary beeswarm`, `template-visual-motifs.md § shap_bar_pie_summary_board` |
| PSO / Pareto + SHAP framework | `knowledge/techniques/ml-model-diagnostics.md § PSO / Pareto Optimization + SHAP`, `knowledge/techniques/radar.md`, `knowledge/techniques/shap-composite.md`, `template-visual-motifs.md § pso_shap_optimization_framework` |
| Mirror radial rose | `06-narrative-arcs.md § A8`, `knowledge/techniques/radar.md § Executable mapping: mirror radial bar board`, `template-visual-motifs.md § mirror_radial_bar_board` |
| Forest plot for clinical effects | `02-zorder-recipes.md § forest`, `04-grid-recipes.md § R6`, `knowledge/techniques/forest-hr-facet.md` |
| Heatmap with pairwise correlation | `04-grid-recipes.md § R5`, `06-narrative-arcs.md § A4`, `knowledge/techniques/heatmap-pairwise.md` |
| Red-blue bubble correlation matrix | `04-grid-recipes.md § R5`, `03-palette-bank.md § materials_teal_salmon_correlation`, `knowledge/techniques/heatmap-pairwise.md § Executable mapping: red-blue bubble correlation matrix`, `template-visual-motifs.md § bubble_correlation_matrix` |
| Two-axis combo (porosity + strength) | `02-zorder-recipes.md § dual-axis`, `05-annotation-idioms.md § I8`, `knowledge/techniques/dual-axis.md` |
| Textbook dual-Y bar + spline | `03-palette-bank.md § materials_porosity_terracotta`, `knowledge/techniques/dual-axis.md § Executable mapping: textbook bar + spline dual axis`, `template-visual-motifs.md § textbook_dual_axis_bar_line` |
| Dual-Y histogram + cumulative grid | `knowledge/techniques/dual-axis.md § Executable mapping: 3x3 histogram + cumulative-frequency grid`, `template-visual-motifs.md § dual_axis_hist_cumfreq_grid` |
| Threshold hump regression | `02-zorder-recipes.md § scatter-regression`, `knowledge/techniques/threshold-regression.md § Executable mapping: hump threshold regression`, `template-visual-motifs.md § hump_threshold_regression` |
| Distance-decay regression | `02-zorder-recipes.md § scatter-regression`, `knowledge/techniques/distance-decay-regression.md` |
| Bayesian ridge + heat strip | `04-grid-recipes.md § R4/R7 variants`, `knowledge/techniques/ridgeline-heatmap.md § Executable mapping: Bayesian ridge heatmap board`, `template-visual-motifs.md § bayesian_ridge_heatmap_board` |
| Adsorption isotherm condition board | `04-grid-recipes.md § R3`, `02-zorder-recipes.md § adsorption-isotherm`, `03-palette-bank.md § cej_vibrant_3`, `knowledge/techniques/adsorption-isotherm.md` |
| Time-series with prediction interval | `02-zorder-recipes.md § time-series`, `05-annotation-idioms.md § I9` |
| GAM log-log + residual diagnostic | `04-grid-recipes.md § R1`, `02-zorder-recipes.md § scatter-regression`, `knowledge/techniques/gam-residual-diagnostic.md` |
| Main + inset residual raincloud | `04-grid-recipes.md § R1/R9`, `03-palette-bank.md § mgea_true_pred_green_orange`, `knowledge/techniques/inset-distribution.md` |
| Radar / polar comparison | `06-narrative-arcs.md § A1 hero`, `knowledge/techniques/radar.md`, `05-annotation-idioms.md § I11` |
| Density scatter + marginal | `04-grid-recipes.md § R8`, `06-narrative-arcs.md § A5`, `knowledge/techniques/marginal-joint.md` |
| Nested model marginal matrix | `04-grid-recipes.md § R8 Variant C`, `03-palette-bank.md § spt_parity_2`, `knowledge/techniques/marginal-joint.md` |
| Gradient-fill box plot | `05-annotation-idioms.md § I12`, `knowledge/techniques/gradient-box.md` |
| Mirror radial / bipolar lollipop | `06-narrative-arcs.md § A8`, `knowledge/techniques/radar.md § Executable mapping: mirror radial bar board`, `knowledge/techniques/lollipop-bipolar.md § Executable mapping: PFI + signed ALE paired lollipops`, `03-palette-bank.md § bipolar_ALE`, `template-visual-motifs.md § mirror_radial_bar_board`, `template-visual-motifs.md § bipolar_lollipop_ale_board` |
| Main + inset distribution | `04-grid-recipes.md § R9`, `06-narrative-arcs.md § A9`, `knowledge/techniques/inset-distribution.md` |

## Re-extraction Protocol

When the article corpus changes:

```bash
cd D:/SciFig
python scifig/knowledge/scripts/extract.py
python scifig/knowledge/scripts/enrich.py
```

This refreshes `case-index.json`, `stats.md`, `stats.json`, `narratives.md`, `palette-harvest.json`. Then audit this INDEX file's frequency tables and update the section "Distilled Universal Findings" to match the new numbers. For executable improvements, continue with Phase 5, but only after a one-case learning record proves the Markdown was read and replicated.
