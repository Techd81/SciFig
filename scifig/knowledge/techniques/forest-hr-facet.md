# Forest HR Facet Board

Anchor case: `Python科研绘图复现_绘制多面板分组森林图展示生存分析风险比(HR)_1777453520`.

## Learned Essence

1. Use a 1x4 `sharey=True` horizontal board for outcome-wise HR comparison.
2. Keep Model 1-3 rows aligned across all panels and show y labels only once.
3. Draw `HR=1.0` as the repeated dashed statistical decision spine in every panel.
4. Encode 95% CI as asymmetric `xerr` around each HR point, not as symmetric error.
5. Use stable adjustment-tier colors: muted blue, orange-red, green.
6. Put the model legend at figure level above the panels.

## Helper Binding

```python
styles = resolve_forest_model_style_map(models, variant="nature_hr_adjustment")
```

The returned styles include `color`, marker face/edge settings, `elinewidth`,
`capsize`, `markersize`, and `zorder`.

## Generator Mapping

`gen_forest` enters this mode when:

- `panel` / `facet` / `disease` / `outcome` role exists
- `model` / `series` / `adjustment` role exists
- HR/ratio estimate plus lower and upper CI columns exist
- the template motif or data pattern contains `faceted_hr_forest` / `hr_forest`

The generator renders the full board in standalone mode and returns the first
axis for compatibility with the existing generator contract.

## QA Contract

- `templateMotifCount` includes `faceted_hr_forest`.
- `referenceLineCount` equals the number of outcome panels.
- No per-panel legends; only one shared figure legend.
- CI columns must come from data. Do not synthesize confidence intervals.
