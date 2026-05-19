# PLS-PM / SEM Path Model

Source anchor: Case 014, `template/articles/期刊图表复现：偏最小二乘路径模型揭示变量间因果与总效应_1777455232.md`.

## Visual Grammar

- Use `mediation_path` as the chart key; do not add a separate registry key.
- Trigger the `pls_pm_path_model` motif when the data has `source` + `target` + `coefficient` / `path_coef`, or when `specialPatterns` includes `pls_pm_path_model`, `sem_path_model`, or `path_model_total_effects`.
- Draw rounded latent-variable nodes and curved directed `FancyArrowPatch` edges.
- Encode positive paths in red `#D73027`, negative paths in blue `#2B6CB0`.
- Map edge linewidth to `1.0 + abs(coef) * 8.0`; arrowhead scale follows the same coefficient magnitude.
- Place `coefficient + significance stars` directly on each path using an opaque white label box.
- Reserve an upper-right inset for horizontal total-effect bars and include a dashed zero reference.
- Add the GoF plaque only when upstream data or prompt supplies it.

## Phase-3 Binding

`gen_mediation_path` must call `draw_pls_pm_path_model` for the PLS-PM/SEM branch and keep the old X -> M -> Y standardized-beta branch as fallback.

Required semantic roles:

- `source`: edge start node.
- `target`: edge end node.
- `coefficient` / `coef` / `path_coef`: signed path coefficient.

Optional roles / visual plan keys:

- `significance` / `sig` / `stars` or `p_value`: path label stars.
- `curvature`: per-edge `arc3,rad` value.
- `total_effect` or `visualContentPlan.plsTotalEffects`: total-effect inset values.
- `visualContentPlan.plsNodePositions`: deterministic node placement.
- `visualContentPlan.plsTargetNode`: target for total effects.
- `visualContentPlan.plsGofText`: GoF annotation.

## QA Counters

Runtime metadata must record:

- `templateMotifsApplied` contains `pls_pm_path_model`.
- `pathEdgeCount` equals the rendered edge count.
- `pathNodeCount` equals the rendered node count.
- `pathPositiveEdgeCount` and `pathNegativeEdgeCount` are both present for signed models.
- `significanceLabelCount` increments once per rendered non-empty significance label.
- `insetCount >= 1` and `totalEffectBarCount >= 1` when total effects are supplied.
- `referenceLineCount >= 1` for the inset zero line.
- `sampleEncodingCount >= 1` for signed color + coefficient linewidth encodings.

## Case-079 Duplicate-Audit Note

- `期刊图表复现：偏最小二乘路径模型揭示变量间因果与总效应_1777455232`
  reappears later in the markdown-learning order, but it is the same source
  already learned in Case-014. Keep the existing `pls_pm_path_model` motif and
  `mediation_path` executable branch rather than minting another path-model
  template.
- The closure evidence lives in
  `.workflow/case_studies/case_079_pls_pm_path_model_audit/comparison_report.json`.
  It verifies that Case-014 already captured the reference images, replica,
  comparison report, runtime probe, and runtime QA for directed paths, signed
  coefficient color/linewidth encoding, significance labels, total-effect
  inset, zero reference, and GoF annotation.
