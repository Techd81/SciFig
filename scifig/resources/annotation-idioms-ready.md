# Annotation Idioms Ready Snippets

Each idiom below is finalizer-compatible and should be preferred over ad-hoc
`ax.text(...)` or handwritten legend/colorbar placement.

## metric_box

When to use: prediction diagnostics, model fit summaries, and compact cohort
counts.

Helper call:

```python
add_metric_box(ax, {"R2": r2, "RMSE": rmse}, loc="top_left", fontsize=6)
```

Finalizer compatibility: helper-created text uses a managed white bbox and
stable zorder. Do not place metric boxes outside axes with negative
`transAxes` coordinates.

## safe_annotation

When to use: one or two high-priority callouts that annotate a visible datum.

Helper call:

```python
safe_annotate(ax, "selected model", xy=(x0, y0), xytext=(8, 10), textcoords="offset points")
```

Finalizer compatibility: the annotation receives safety bbox and zorder. Avoid
dense repeated annotations; use `auto_relocate_annotations` only when needed.

## p_value_stars

When to use: supplied comparison p-values or precomputed significance labels.

Helper call:

```python
safe_annotate(ax, stars, xy=(x_mid, y_top), ha="center", va="bottom")
```

Finalizer compatibility: stars must come from supplied data. Do not invent
significance labels.

## group_divider

When to use: grouped bars, grouped dot plots, or grouped matrix lanes.

Helper call:

```python
add_group_dividers(ax, divider_positions, orientation="vertical", color="#B0B0B0")
```

Finalizer compatibility: dividers live below labels and above gridlines; keep
them muted and semantic.

## density_scatter

When to use: scatter plots with enough points that overplotting hides density.

Helper call:

```python
density_color_scatter(ax, x, y, cmap="viridis", s=12, alpha=0.75)
```

Finalizer compatibility: include a colorbar only through a reserved layout slot
or the helper colorbar reflow path.

## panel_label

When to use: every plotted panel in multi-panel figures.

Helper call:

```python
add_panel_label(ax, "A", x=-0.12, y=1.05, fontsize=8)
```

Finalizer compatibility: panel labels use managed `gid` and are excluded from
text safety bbox mutation.

## perfect_fit_diagonal

When to use: observed-vs-predicted, calibration, QQ, PP, and similar identity
reference plots.

Helper call:

```python
add_perfect_fit_diagonal(ax, color="#777777", linestyle="--", linewidth=0.6)
```

Finalizer compatibility: reference line zorder should come from the active
zorder recipe.

## zero_reference

When to use: signed effects, ALE/PDP deviations, volcano-like contrasts, and
differential plots.

Helper call:

```python
add_zero_reference(ax, axis="y", color="#777777", linestyle="--", linewidth=0.6)
```

Finalizer compatibility: zero references are semantic data guides, not
decorative gridlines.
