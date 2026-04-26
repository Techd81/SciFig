# Journal Profiles

Use these profiles as explicit plotting tokens. They define the visual language; the code generator should translate them into rcParams, spacing, and layout decisions.

## Notes On Sources

- `Nature-like` is grounded in official Nature figure guidance. Nature shows both rounded initial-submission canvases (`90/180 mm`) and final-submission-safe widths (`89/183 mm`); this skill uses the tighter `89/183 mm` tokens because they are safer for final artwork planning.
- `Cell-like` is derived from Cell Press guidance emphasizing clarity, sparse text, simple labels, restrained color, and strong figure storytelling. It is not presented as an official Cell regular-figure production spec.
- `Science-like` is a minimal preset for fast visual parsing and low-ink figures.

## Profile Table

| Profile | Canvas tokens | Typography | Line/tick discipline | Panel behavior | Color behavior |
|---------|---------------|------------|----------------------|----------------|----------------|
| `nature` | `single=89 mm`, `double=183 mm`, `max_height=170 mm` | Sans serif, editable, 5-7 pt body text | Thin but visible, no ornamental gridlines, compact tick marks | Avoid unnecessary panels; align scales; labels A/B/C/D bold and compact | Colorblind-safe, muted accents, no rainbow |
| `cell` | Reuse Nature-safe canvas tokens unless user overrides | Sans serif, sparse labels, slightly more whitespace than Nature | Clean axes, minimal framing, little visual noise | Story-first layouts; hero panel plus focused support panels | Restrained accent colors, white background, semantic rather than decorative use |
| `science` | Reuse Nature-safe canvas tokens unless user overrides | Sans serif, compact, efficient | Low-ink plotting, concise legends, minimal axis chrome | Compact layouts for rapid scanning | Mostly muted neutrals plus one or two accents |

## Nature-like Tokens

```python
NATURE_PROFILE = {
    "single_width_mm": 89,
    "double_width_mm": 183,
    "max_height_mm": 170,
    "font_family": ["Arial", "Helvetica", "DejaVu Sans"],
    "font_size_body_pt": 6,
    "font_size_small_pt": 5,
    "font_size_panel_label_pt": 8,
    "axis_linewidth_pt": 0.6,
    "tick_width_pt": 0.6,
    "tick_direction": "out",
    "tick_length_pt": 3,
    "marker_size_pt": 4,
    "line_cap": "round",
    "line_join": "round",
    "legend_frame": False,
    "legend_borderpad": 0.3,
    "grid": False,
    "panel_gap_rel": 0.22,
    "panel_label_offset_xy": [-0.12, 1.05],
    "colorbar_shrink": 0.6,
    "shared_legend_position": "upper center",
    "shared_legend_ncol": "auto"
}
```

## Cell-like Tokens

```python
CELL_PROFILE = {
    "inherits_canvas_from": "nature",
    "font_family": ["Arial", "Helvetica", "DejaVu Sans"],
    "font_size_body_pt": 6.5,
    "font_size_panel_label_pt": 8,
    "axis_linewidth_pt": 0.65,
    "tick_width_pt": 0.55,
    "legend_frame": False,
    "grid": False,
    "panel_gap_rel": 0.28,
    "narrative_bias": "hero_plus_support"
}
```

## Science-like Tokens

```python
SCIENCE_PROFILE = {
    "inherits_canvas_from": "nature",
    "font_family": ["Arial", "Helvetica", "DejaVu Sans"],
    "font_size_body_pt": 6,
    "font_size_panel_label_pt": 8,
    "axis_linewidth_pt": 0.55,
    "tick_width_pt": 0.5,
    "legend_frame": False,
    "grid": False,
    "panel_gap_rel": 0.18,
    "narrative_bias": "compact_pair"
}
```

## Lancet-like Tokens

```python
LANCET_PROFILE = {
    "single_width_mm": 80,
    "double_width_mm": 168,
    "max_height_mm": 170,
    "font_family": ["Helvetica", "Arial", "DejaVu Sans"],
    "font_size_body_pt": 6,
    "font_size_small_pt": 5,
    "font_size_panel_label_pt": 7,
    "axis_linewidth_pt": 0.5,
    "tick_width_pt": 0.5,
    "legend_frame": False,
    "grid": False,
    "panel_gap_rel": 0.20,
    "narrative_bias": "clinical_evidence"
}
```

## NEJM-like Tokens

```python
NEJM_PROFILE = {
    "single_width_mm": 86,
    "double_width_mm": 178,
    "max_height_mm": 170,
    "font_family": ["Arial", "Helvetica", "DejaVu Sans"],
    "font_size_body_pt": 6,
    "font_size_small_pt": 5,
    "font_size_panel_label_pt": 8,
    "axis_linewidth_pt": 0.5,
    "tick_width_pt": 0.5,
    "legend_frame": False,
    "grid": False,
    "panel_gap_rel": 0.22,
    "narrative_bias": "clinical_outcome"
}
```

## JAMA-like Tokens

```python
JAMA_PROFILE = {
    "single_width_mm": 84,
    "double_width_mm": 175,
    "max_height_mm": 170,
    "font_family": ["Arial", "Helvetica", "DejaVu Sans"],
    "font_size_body_pt": 6,
    "font_size_small_pt": 5,
    "font_size_panel_label_pt": 7,
    "axis_linewidth_pt": 0.5,
    "tick_width_pt": 0.5,
    "legend_frame": False,
    "grid": False,
    "panel_gap_rel": 0.20,
    "narrative_bias": "clinical_validation"
}
```

## Profile Selection Rules

1. Start from `nature` when the user asks for submission-safe defaults.
2. Use `cell` when narrative multi-panel composition and restrained editorial styling matter more than strict Nature mimicry.
3. Use `science` when the figure must stay compact, minimal, and fast to scan.
4. Use `lancet` for clinical/medical figures targeting The Lancet family journals.
5. Use `nejm` for high-impact clinical trial figures and medical research.
6. Use `jama` for clinical validation studies and diagnostic accuracy figures.
7. If the user requests exact journal compliance beyond the tokens above, emit a note that final production checks should still be verified against the target journal's current author guide.
