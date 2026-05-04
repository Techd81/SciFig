# Finalizer-Safe Template Contract

This is the canonical contract every Phase-3 generator must follow.

## Required imports

Generator code should use helper APIs and registry files instead of local
defaults:

```python
from template_mining_helpers import (
    apply_journal_kernel,
    resolve_palette,
    role_color,
    build_grid,
    apply_zorder_recipe,
    add_metric_box,
    safe_annotate,
    add_panel_label,
    add_perfect_fit_diagonal,
    add_zero_reference,
)
```

Registry-backed resources:

- `templates/template-palette-registry.json`
- `templates/layout-recipes-ready.json`
- `templates/zorder-recipes-ready.json`

## Banned patterns

| Pattern | Do not use | Use instead |
|---------|------------|-------------|
| Outside-right legends | `ax.legend(..., bbox_to_anchor=(1.02, 1))` | collect handles/labels and let `enforce_figure_legend_contract` create the bottom-center figure legend |
| Negative-bottom legends | `ax.legend(..., bbox_to_anchor=(0.5, -0.24))` | reserve a bottom legend slot through the layout recipe |
| Left/right titles | `ax.set_title("A", loc="left")` or `fig.suptitle(..., ha="left")` | centered titles plus `add_panel_label(..., x=-0.06, y=1.08, fontsize=9)` for panel letters |
| Fragile label glyphs | `R⊕`, `M⊕`, `log₁₀`, `—` | `Earth radii`, `Earth masses`, `log10`, `-` |
| Inline palette lists | `colors = ["#1F3A5F", "#C8553D"]` | `colors = resolve_palette("nature_radar_dual")` |
| Ad-hoc zorder defaults | `zorder=999` | semantic layers passed to `apply_zorder_recipe(...)` |
| Handwritten finalizer replacements | local `def enforce_figure_legend_contract(...)` | embedded `phases/code-gen/helpers.py` finalizer |

## Required finalizer hooks

Every generated script must end each saved figure with this sequence:

```python
axes_map = normalize_axes_map(fig, axes_map)
legend_contract_report = enforce_figure_legend_contract(
    fig, axes_map, chartPlan, journalProfile
)
layout_report = audit_figure_layout_contract(
    fig, axes_map, chartPlan, journalProfile, strict=False
)
record_render_contract_report("figure1", chartPlan, legend_contract_report)
editable_export_report = export_editable_svg_bundle(
    fig,
    "figure1",
    Path("output"),
    axes=axes_map,
    chartPlan=chartPlan,
    raster_dpi=workflowPreferences.get("rasterDpi", 300),
    normalized_formats=workflowPreferences.get("exportFormats", ["pdf", "svg"]),
    strict=True,
)
```

The exported SVG is not an ordinary side artifact. It is the editable canonical
source: text stays as `<text>`, movable components get stable SVG IDs, and any
requested PNG is rendered from that SVG so the raster output matches the
editable file. PDF also uses the SVG renderer when available; otherwise the
helper records a PDF fallback warning rather than blocking SVG-only workflows.

The generator payload should preserve shared legend intent:

```python
styledCode["sharedLegend"] = chartPlan.get("sharedLegend", False)
```

Cycle-24 audit fields are required in persisted runtime reports:

- `audited_axes_count`
- `textTextOverlapCount`
- `bboxDataCoverageOverflowCount`
- `editable_svg_manifest.json`
- `svg_render_qa.json`
- `pngSource == "editable_svg" | "edited_svg"` when PNG is requested

## Generator opt-outs

Reserved `gid` values:

- `scifig_metric_box`
- `scifig_metric_table`
- `scifig_inplot_label`
- `scifig_panel_label`
- `scifig_no_safety_bbox`

Use opt-outs only when the helper contract already covers readability. Raw text
without a white safety bbox must be rare and documented in the generator.

## Source-side lint integration

After editing any split generator source, run:

```powershell
python phases/code-gen/source-lint.py
```

Any hit from `BANNED_LEGEND_PATTERNS` blocks finalization.
