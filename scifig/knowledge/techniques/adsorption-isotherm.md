# Technique: Adsorption Isotherm Multipanel

Anchor case: `Python复现顶刊CEJ _ 拒绝手绘！如何用代码"量产"高颜值多面板吸附等温线图？_1777452771`.

## Learned Essence

This case is a condition-wise adsorption comparison board, not a generic line chart.

1. Use a 2x3 `GridSpec` storyboard for six temperature / pressure / material conditions.
2. Draw model predictions as continuous curves below observed data.
3. Use semantic method colors: cyan OR support, red IL focal curve, blue hollow experimental markers, black hollow GCMC markers.
4. Treat observations and simulations as top-layer evidence with higher `zorder` than model curves.
5. Put panel IDs in `transAxes` outside the upper-left corner so labels do not drift with data limits.
6. Translate per-panel lower-right source legends into one SciFig bottom-center figure legend.

## Helper Binding

```python
styles = resolve_method_style_map(methods, variant="cej_adsorption")
```

The returned styles include `color`, `marker`, `markerfacecolor`, `markeredgecolor`,
`linestyle`, `zorder`, and `draw`.

## Generator Mapping

`gen_scatter_regression` enters this mode when:

- `panel` / `facet` / `condition` / `temperature` role exists
- `method` / `model` / `algorithm` / `source` role exists
- x and y numeric roles exist
- the template motif or data pattern contains `adsorption_isotherm`

The generator renders the full board in standalone mode and returns the first
axis for compatibility with the existing generator contract.

## QA Contract

- `templateMotifCount` includes `adsorption_isotherm_multipanel`.
- `panelLabelCount` must be at least the number of rendered panels.
- `modelCurveCount` should equal `panel_count * model_curve_series_count` when
  the source supplies complete model curves.
- `hollowMarkerSeriesCount` should cover experiment and simulation overlays.
- Legends must be figure-level bottom-center after finalization.
- Hollow observed/simulation markers must remain above model curves.
