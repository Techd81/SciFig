# Finalizer Auto-corrections

`enforce_figure_legend_contract(...)` in `runtime/helpers.py` runs zero-touch retrofit passes before `audit_figure_layout_contract`. Generators rely on this finalizer rather than reimplementing local fixes.

## Required Behaviors

- `center_figure_titles`: center figure titles; panel letters must use `add_panel_label(...)`.
- `sanitize_figure_text`: replace fragile glyphs with ASCII-safe text.
- `_promote_inaxes_text_safety`: lift in-axes text to `zorder>=20` and add a white bbox unless opted out.
- `_shrink_heatmap_cell_labels`: reformat dense heatmap labels and suppress low-value noise.
- `normalize_axes_map`: include inset axes in single-panel layout audits.
- Overlap checks must hard-fail buried text, label collisions, and oversized text bboxes.

## Protected Artists

Never modify axis chrome, panel labels, heatmap cell labels, or managed `gid` artists (`scifig_metric_box`, `scifig_metric_table`, `scifig_inplot_label`, `scifig_panel_label`). Use `gid="scifig_no_safety_bbox"` for raw text that must not receive a white bbox.

The finalizer does not run `auto_relocate_annotations(...)`; call `safe_annotate(...)` explicitly for dense layouts.

## Lint

Generator source files must not contain `ax.legend(...)` with `bbox_to_anchor=(1.02, 1)` or `(0.5, -X)`. `runtime/source-lint.py` blocks these before code is finalized.

## Fonts

Optional fonts in `assets/fonts/` — see [assets/fonts/README.md](../assets/fonts/README.md). Resolution order: `SCIFIG_FONTS_DIR` → `__SCIFIG_SKILL_ROOT__` → skill-root `assets/fonts/`. Every `font.family` chain must end in `DejaVu Sans`.
