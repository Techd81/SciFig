# Technique: GAM Log-Residual Diagnostic

Anchor case: `复现 Nature _ Python 绘制广义相加模型 (GAM) 拟合与残差诊断组合图_1777452515`.

Use when a relationship panel must explain a wide dynamic-range association and
a paired residual panel must identify hidden positive outliers.

## Hallmark elements

1. **1x2 evidence/diagnosis layout**: left panel establishes the relationship, right panel diagnoses residual anomalies.
2. **Log-log relationship panel**: both axes log-scaled, explicit major ticks, minor locators suppressed.
3. **GAM-like smooth**: spline/loess-style black fit line with a translucent black confidence band underneath.
4. **Three z-order layers**: gray background points, black band/fit, semantic highlight points above.
5. **Shared anomaly palette**: `Non=#B0B0B0`, `Adj=#5FA896`, `In=#FBC15E` across both panels.
6. **Sparse R2 annotation**: bold italic `transAxes` text without a metric-box bbox.
7. **Residual panel**: horizontal zero reference plus the same highlighted anomaly classes.

## Executable mapping

`gen_scatter_regression` enters `gam_log_residual_diagnostic` mode when the
motif is planned or `specialPatterns` contains `gam_residual_diagnostic`.
It fits in log10 space, uses `SplineTransformer + LinearRegression` when
available, falls back to a cubic polynomial, and returns the left axes of the
generated 1x2 board.

Category styling is delegated to `resolve_gam_residual_style_map`, so the
three-layer Nature palette is stable and shared between relationship and
residual panels.

Case-073 duplicate-audit note:

- `复现 Nature _ Python 绘制广义相加模型 (GAM) 拟合与残差诊断组合图_1777452515`
  reappears later in the markdown-learning order, but it is the same source
  already learned in Case-008. Keep the existing
  `gam_log_residual_diagnostic` motif and `scatter_regression` executable
  branch rather than minting a second GAM/residual template.
- The closure evidence lives in
  `.workflow/case_studies/case_073_nature_gam_residual_audit/comparison_report.json`.
  It verifies that Case-008 already captured five reference screenshots, the
  replica, comparison report, runtime probe, and runtime QA for the log-log
  relationship plus residual diagnostic board.

## Discipline rules

| Rule | Reason |
|---|---|
| Fit in log space before plotting on log axes | The visual relationship is multiplicative |
| Suppress minor log ticks | The source figure avoids tick clutter |
| Keep confidence band black at alpha 0.15 | Reads as model uncertainty, not a new group |
| Reuse highlight colors in both panels | The residual story depends on identity preservation |
| R2 text has no bbox | Nature-style sparse annotation; do not over-frame it |

## QA contract

- `gam_log_residual_diagnostic` in `templateMotifsApplied`
- `confidenceBandCount`: >= 1
- `smoothFitLineCount`: >= 1
- `residualDiagnosticPanelCount`: >= 1
- `r2AnnotationCount`: >= 1
- `panelLabelCount`: >= 2
