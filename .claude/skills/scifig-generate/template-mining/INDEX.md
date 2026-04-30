# Template Mining — Knowledge Base Index

**Source**: 77 顶刊复刻案例 distilled from `D:\SciFig\template\articles\` (Nature, Nature Comms, Nature Nanotechnology, Cell, Advanced Science, CEJ, Materials Today, JECE, JBE, MGEA, etc.).

**Purpose**: A queryable knowledge base of the visual-grammar patterns, color systems, layer-stacking recipes, multi-panel layouts, in-axes annotations, and scientific narrative arcs that real top-journal Python figures actually use.

**This index is the only file phases load by default**. Each topic file is loaded on-demand by Phase 2/3 when a specific decision needs it.

## Directory Map

```
template-mining/
├── INDEX.md                        <- this file
├── case-index.json                 machine-readable metadata for 77 cases
├── 01-rcparams-kernel.md           顶刊审美内核 (the rcParams every chart starts from)
├── 02-zorder-recipes.md            三明治图层法 (per-family layer stacking)
├── 03-palette-bank.md              实战色谱库 (named palettes + case anchors)
├── 04-grid-recipes.md              GridSpec 多面板配方 (R0–R11)
├── 05-annotation-idioms.md         in-axes annotation patterns (I1–I14)
├── 06-narrative-arcs.md            科学叙事弧 (A1–A9 story shapes)
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
│   └── inset-distribution.md
└── _extraction/                    extractor scripts + raw stats (do not load)
    ├── extract.py                  structural extraction (rcParams, palette, grid, counts)
    ├── enrich.py                   semantic enrichment (narrative arc, signature tricks)
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
   - Read `06-narrative-arcs.md` to confirm story shape.
   - Read `04-grid-recipes.md` if `panel_count > 1`.
3. **Phase 3** (code generation):
   - Read `01-rcparams-kernel.md` for the global aesthetic baseline.
   - Read `02-zorder-recipes.md` for the matching chart family.
   - Read `03-palette-bank.md` to bind the chosen palette name to actual hex codes.
   - Read `05-annotation-idioms.md` to apply in-axes labels.
   - Read `07-techniques/<family>.md` only if the chart family appears in the per-family directory.
4. **Phase 4** (render QA): every required motif from the chosen narrative arc + chart family must be present; failures route back to Phase 3.

## Distilled Universal Findings (n=77, regex-verified)

These findings are derived from `_extraction/stats.json` — frequencies are exact and reproducible.

### 1. The rcParams kernel is dominant but **not** universal

Real frequencies of canonical "顶刊感" tokens:

| Key | Cases declaring | % | Most-used value |
|---|---|---|---|
| `xtick.direction` / `ytick.direction` = `'in'` | 67/77 | 87% | `'in'` (65/67) |
| `axes.linewidth` | 69/77 | 90% | `1.5` (56) / `1.2` (11) |
| `font.family` includes Times New Roman | 53/77 | 69% | `['Times New Roman', 'Arial', ...]` |
| `font.size` | 69/77 | 90% | `16` (48) / `14` (18) |
| `mathtext.fontset` = `'stix'` | 62/77 | 81% | `'stix'` (61) |
| `savefig.dpi` declared | 30/77 | 39% | `600` (28) |
| `savefig.bbox` declared | 26/77 | 34% | `'tight'` (25) |

> **Correction note**: Earlier drafts of this index claimed `tick.direction='in'` was 77/77; the regex-verified count is 67/77 (87%). Earlier `savefig.dpi=600` claim of "60+/77" was incorrect; real count is 28/77 (36%).

The `dpi=600` and `bbox='tight'` are typically supplied at **savefig call time** (rather than in rcParams) in the cases that don't set them globally — Phase 3 should set them in `apply_journal_kernel` regardless.

### 2. zorder layering is the dominant rendering pattern

| Pattern | Cases | % |
|---|---|---|
| Any explicit `zorder=` use | 58/77 | 75% |
| ≥3 distinct zorder levels in same chart | ~40/77 | ~52% |

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
| `multipanel_grid` | 26 (34%) | R3 (2×3) / R5 (3×3) |
| `single_focus` | 18 (23%) | R0 |
| `global_local` | 5 (6%) | R10 (top-wide) |
| `n×n_pairwise` | 5 (6%) | R5 |
| `marginal_joint` | 4 (5%) | R8 |
| `train_test_diagnostic` | 4 (5%) | R0 / R1 |
| `composite_two_lane` | 4 (5%) | R1 |
| `mirror_compare` | 4 (5%) | R0 / R1 |
| `hero` | 4 (5%) | R0 |
| `inset_overlay` | 3 (4%) | R9 |

See `06-narrative-arcs.md` for the full decision matrix.

### 5. Chart family distribution (multi-label, n=77)

| Family | Cases | Deep-dive file |
|---|---|---|
| scatter_regression | 59 | (covered in `02-zorder-recipes.md § scatter-regression`) |
| ALE / PDP | 29 | `07-techniques/lollipop-bipolar.md` covers ALE bipolar |
| SHAP composite | 26 | `07-techniques/shap-composite.md` |
| dual_axis | 19 | `07-techniques/dual-axis.md` |
| heatmap | 11 | covered in pairwise + general |
| forest | 10 | `02-zorder-recipes.md § forest` |
| box / violin | 11 | `07-techniques/gradient-box.md` |
| heatmap_pairwise | 8 | `07-techniques/heatmap-pairwise.md` |
| radar | 6 | `07-techniques/radar.md` |
| density_scatter | 6 | covered in `marginal-joint.md` |
| marginal_joint | 5 | `07-techniques/marginal-joint.md` |

### 6. Top signature tricks (regex-verified)

| Trick | Cases | Idiom doc |
|---|---|---|
| `alpha_layered_scatter` | 24 | `02-zorder-recipes.md` |
| `group_divider_axvline` | 14 | `05-annotation-idioms.md § I3` |
| `density_color_scatter` | 14 | `05-annotation-idioms.md § I6` |
| `raincloud_combo` | 13 | (matches inset overlay + raincloud combo) |
| `metric_text_box` | 9 | `05-annotation-idioms.md § I1` |
| `axes_inset_overlay` | 8 | `04-grid-recipes.md § R9` |
| `dotted_zero_axhline` | 8 | `05-annotation-idioms.md § I4` |
| `pvalue_stars_overlay` | 7 | `05-annotation-idioms.md § I5` |
| `colored_marker_edge` | 7 | `05-annotation-idioms.md § I7` |
| `twin_axes_color_spines` | 6 | `05-annotation-idioms.md § I8` |

## AI / ML Template Routing

Computer, AI, and machine-learning prompts must first check the `ml-model-diagnostics` deep-dive before falling back to generic prediction charts. When user text or `dataProfile` includes Random Forest/RF/RFR, XGBoost, LightGBM, GBDT, classifier/regressor, train/test metrics, AUC/F1/accuracy, RMSE/MAE/R2, SHAP, feature importance, or residual fields, Phase 2 should recommend a template-backed ML bundle and Phase 3 should clone the matching case composition before adapting data labels.

High-value anchors:

- RF triptych: `期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱_1777456409.md`
- RF EFI + SHAP: `期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化_1777456510.md`
- Incremental feature selection: `拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272.md`
- PSO + SHAP optimization: `基于PSO多目标优化与SHAP可解释分析的回归预测模型框架_1777461729.md`

## Style Discipline Rules (consolidated from 77 cases)

| Rule | Frequency | Source |
|------|-----------|--------|
| `xtick.direction='in'`, `ytick.direction='in'` | 67/77 (87%) | `01-rcparams-kernel.md` |
| `mathtext.fontset = 'stix'` | 62/77 (81%) | `01-rcparams-kernel.md` |
| `axes.linewidth = 1.5` (hero) or `1.2` (compact) | 67/77 (87%) | `01-rcparams-kernel.md` |
| Use `zorder=` explicitly to stack layers | 58/77 (75%) | `02-zorder-recipes.md` |
| In-plot text annotation with `transform=ax.transAxes` | 29/77 (38%) | `05-annotation-idioms.md` |
| Reference line `axvline`/`axhline` at meaningful X/Y | 28/77 (36%) | `05-annotation-idioms.md` |
| `GridSpec` for non-trivial multi-panel | 23/77 (30%) | `04-grid-recipes.md` |
| `colorbar(...)` for sequential color encoding | 20/77 (26%) | `03-palette-bank.md` |
| Despine top + right (`set_visible(False)` form) | 11/77 (14%) | optional, family-dependent |

> **Correction note**: An earlier draft claimed despine was 64/77; the verified count is 11/77. Despine is **not** a corpus-universal rule — it's family-dependent (forest plots keep all spines, polar plots replace them entirely).

## When NOT to Use This Knowledge Base

- **Single quick chart, no journal style required** — the regular `phases/03` flow is fine.
- **User explicitly requested a different aesthetic** (e.g., presentation slide, dashboard) — these patterns are tuned for paper submission.
- **Custom domain not represented in the 77 cases** (e.g. genomics single-cell UMAP, clinical KM) — fall back to `specs/domain-playbooks.md` and don't force a mismatch.

## Adding New Cases

When the user supplies new reference figures or articles:

1. Save markdown under `template/articles/`.
2. Re-run `_extraction/extract.py` then `_extraction/enrich.py` to refresh `case-index.json`, `stats.md`, `narratives.md`.
3. If a new motif emerges, add an entry to `05-annotation-idioms.md` or a new `07-techniques/<name>.md`.
4. If article code should improve generated figures, run `phases/05-template-distill.md` and `specs/template-distillation-contract.md`; promote reusable code into helpers/generators before changing coordinator prose.
5. Don't overwrite distilled patterns silently — append, then mark superseded entries.

## Coordinator Cheat-Sheet

When you find yourself wondering "how would Nature draw this?":

| User intent | Files to load |
|-------------|---------------|
| Predicted vs actual scatter | `01-rcparams-kernel.md`, `02-zorder-recipes.md § scatter-regression`, `05-annotation-idioms.md § I1, I2`, `06-narrative-arcs.md § A1` |
| Multi-panel SHAP (global + local) | `04-grid-recipes.md § R10`, `06-narrative-arcs.md § A3`, `07-techniques/shap-composite.md` |
| Forest plot for clinical effects | `02-zorder-recipes.md § forest`, `04-grid-recipes.md § R6` |
| Heatmap with pairwise correlation | `04-grid-recipes.md § R5`, `06-narrative-arcs.md § A4`, `07-techniques/heatmap-pairwise.md` |
| Two-axis combo (porosity + strength) | `02-zorder-recipes.md § dual-axis`, `05-annotation-idioms.md § I8`, `07-techniques/dual-axis.md` |
| Time-series with prediction interval | `02-zorder-recipes.md § time-series`, `05-annotation-idioms.md § I9` |
| Radar / polar comparison | `06-narrative-arcs.md § A1 hero`, `07-techniques/radar.md`, `05-annotation-idioms.md § I11` |
| Density scatter + marginal | `04-grid-recipes.md § R8`, `06-narrative-arcs.md § A5`, `07-techniques/marginal-joint.md` |
| Gradient-fill box plot | `05-annotation-idioms.md § I12`, `07-techniques/gradient-box.md` |
| Mirror radial / bipolar lollipop | `06-narrative-arcs.md § A8`, `07-techniques/lollipop-bipolar.md`, `03-palette-bank.md § bipolar_ALE` |
| Main + inset distribution | `04-grid-recipes.md § R9`, `06-narrative-arcs.md § A9`, `07-techniques/inset-distribution.md` |

## Re-extraction Protocol

When the article corpus changes:

```bash
cd D:/SciFig
python .claude/skills/scifig-generate/template-mining/_extraction/extract.py
python .claude/skills/scifig-generate/template-mining/_extraction/enrich.py
```

This refreshes `case-index.json`, `stats.md`, `stats.json`, `narratives.md`, `palette-harvest.json`. Then audit this INDEX file's frequency tables and update the section "Distilled Universal Findings" to match the new numbers. For executable improvements, continue with Phase 5 so article code is promoted into helpers/generators and covered by tests.
