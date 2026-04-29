# Workflow Policies

Shared policy tokens for `scifig-generate`. Use this file when Phase 1-4 need thresholds, visual-density defaults, performance budgets, agent delegation, or rendered quality gates. Keep code snippets in phase files aligned with these names instead of introducing new inline constants.

## Data Scale Policy

```python
DATA_SCALE_POLICY = {
    "high_missing_rate_pct": 10,
    "overplotting_rows": 400,
    "point_density_full_max": 400,
    "point_density_alpha_max": 1000,
    "large_matrix_rows": 2000,
    "clusterable_matrix_rows": 500,
    "rare_positive_rate": 0.20,
    "legend_bottom_group_max": 8,
}
```

## Visual Impact Policy

```python
VISUAL_IMPACT_POLICY = {
    "default_mode": "nature_cell_dense",
    "default_density": "high",
    "impact_level": "editorial_science",
    "max_callouts_single": 8,
    "max_callouts_support": 4,
    "max_inline_stats": 4,
    "min_enhancements_per_panel": 2,
    "min_total_enhancements": 4,
    "require_inplot_explanatory_labels": True,
    "min_inplot_labels_per_figure": 1,
    "semantic_callout_mode": "data_derived",
    "use_inset_axes": True,
    "require_stat_provenance": True,
    "no_invented_stats": True,
    "outside_layout_elements": True,
}
```

Visual impact must stay data-derived. Permitted enhancements include sample-size labels, observed quantiles, reference lines, confidence bands from supplied or computed values, inset distributions, rank callouts, model diagnostics, and semantic highlights already justified by `dataProfile` or `statPlan`. Every rendered figure should contain in-plot explanatory labels such as best group, endpoint delta, trend direction, threshold hit count, peak window, or matrix/value summaries; outside metric boxes alone do not satisfy visual impact.

## Crowding And Layout Policy

```python
CROWDING_POLICY = {
    "legend_scope": "figure",
    "legend_priority": ["bottom_center", "top_center", "outside_right"],
    "legend_label_max_chars": 32,
    "max_legend_columns": 6,
    "forbid_in_axes_legend": True,
    "max_direct_labels_hero": 5,
    "max_direct_labels_support": 3,
    "max_bracket_groups": 2,
    "render_retry_limit": 5,
    "layout_reflow_required_on_overlap": True,
    "legend_external_hard_limit": True,
    "axis_legend_hard_fail": True,
    "legend_reflow_strategy": ["margin_adjust", "height_increase", "entry_reduction"],
    "legend_max_height_multiplier": 1.3,
}

LAYOUT_SCORE_WEIGHTS = {
    "panel_count": 2,
    "legend_burden": 3,
    "long_label_burden": 2,
    "colorbar_burden": 2,
    "aspect_ratio_mismatch": 2,
    "story_fit": 4,
}
```

Before Phase 3 locks the plan, score each candidate layout for group count, label length, legend burden, colorbar need, panel count, and chart aspect ratio. Prefer a lower-scoring layout even when it has fewer panels. If a rendered legend or colorbar overlaps the plotting region, reflow before export; do not move legends back inside axes.

## Performance Policy

```python
PERFORMANCE_POLICY = {
    "renderer_cache": True,
    "max_render_retries": 5,
    "adaptive_kde_grid_min": 96,
    "adaptive_kde_grid_max": 300,
    "adaptive_heatmap_cluster_rows": 500,
    "sample_points_preview_max": 5000,
}
```

Generators should precompute grouped subsets once, use adaptive KDE/grid resolution, and avoid repeated `fig.canvas.draw()` calls inside nested layout searches. Expensive rendered checks should share a cached renderer and invalidate it only after layout changes.

## Agent Delegation Policy

Use `Agent` only after the data-status, file-path, and mode gates are complete. Agents must be read-only unless the coordinator explicitly asks for a rewritten artifact. Each agent returns JSON findings that the coordinator merges into phase state.

| Agent | Trigger | Output | Blocking Gates |
|-------|---------|--------|----------------|
| `data-profile-auditor` | Matrix/large data, high missingness, weak replicates, ambiguous roles/domain, survival or dose-response incompleteness | `dataProfile.audit` | unresolved role conflicts, low schema confidence, required clarification |
| `chart-stats-planner` | Multi-panel, custom domain, high-stakes statistics, or requested inferential claims | `chartPlan.delegationReports.stats` | unregistered chart, unsupported statistical assumption, missing replicate/cohort meaning |
| `panel-layout-auditor` | More than two panels, shared legend/colorbar, long labels, many groups | `chartPlan.delegationReports.layout` | overpacked layout, missing legend/colorbar plan, invalid axis linking |
| `palette-journal-auditor` | Domain palette, many categories, grayscale-safe request, journal submission | `chartPlan.delegationReports.palette` | category collisions, poor grayscale contrast, semantic map drift |
| `scientific-color-harmony` | After build_palette_plan in Phase 2 | `chartPlan.delegationReports.color_harmony` | advisory only — perceptual harmony, color-wheel relationships, domain aesthetics |
| `layout-aesthetics` | After build_panel_blueprint in Phase 2 | `chartPlan.delegationReports.aesthetics` | advisory only — whitespace balance, visual weight distribution, panel proportions |
| `content-richness` | After build_visual_content_plan in Phase 2 | `chartPlan.delegationReports.content_richness` | advisory only — annotation density, label informativeness, marker diversity |
| `code-reviewer` | Before Phase 3 completion | `styledCode.codeReview` | syntax/import failures, generator drift, forbidden `loc="best"`, missing metadata/source hooks |
| `rendered-qa` | After script execution and before final outputBundle | `outputBundle.renderQa` | blank/tiny output, overlap, in-axes legend, missing format, non-editable SVG/PDF text |
| `visual-impact-scorer` | After rendered-qa, before outputBundle packaging | `outputBundle.renderQa.impactScore` | impactScore < 40 → warning, impactScore < 20 → hardFail |

Blocking findings route back to the owning phase rather than being buried in the final report.

## Render QA Policy

Phase 4 must produce `render_qa.json` with:

- `legendOutsidePlotArea`
- `axisLegendRemovedCount`
- `axisLegendRemainingCount`
- `sharedColorbarApplied`
- `overlapFailures`
- `contentDensityFailures`
- `blankOrTinyOutputs`
- `editableTextCheck`
- `paletteContrastCheck`
- `visualEnhancementCount`
- `inPlotExplanatoryLabelCount`
- `statProvenanceWarnings`
- `impactScore` (0-100 from visual-impact-scorer agent)

Any hard failure returns to Phase 3 for styling/layout/code or Phase 2 for an overpacked plan. `axisLegendRemainingCount > 0`, `legendOutsidePlotArea == false`, missing in-plot explanatory labels, or `visualEnhancementCount < visualContentPlan.minTotalEnhancements` are hard failures. `impactScore < 20` is a hard fail; `impactScore < 40` is a warning.
