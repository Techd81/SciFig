```python
# ──────────────────────────────────────────────────────────────
# Chart Generator Registry
# Maps chart type keys to generator function names.
# ──────────────────────────────────────────────────────────────

CHART_GENERATORS = {
    "violin_strip": "gen_violin_strip",
    "box_strip": "gen_box_strip",
    "raincloud": "gen_raincloud",
    "beeswarm": "gen_beeswarm",
    "paired_lines": "gen_paired_lines",
    "dumbbell": "gen_dumbbell",
    "line": "gen_line",
    "training_curve": "gen_training_curve",
    "line_ci": "gen_line_ci",
    "spaghetti": "gen_spaghetti",
    "heatmap_cluster": "gen_heatmap_cluster",
    "heatmap_pure": "gen_heatmap_pure",
    "volcano": "gen_volcano",
    "ma_plot": "gen_ma_plot",
    "pca": "gen_pca",
    "umap": "gen_umap",
    "tsne": "gen_tsne",
    "enrichment_dotplot": "gen_enrichment_dotplot",
    "oncoprint": "gen_oncoprint",
    "lollipop_mutation": "gen_lollipop_mutation",
    "roc": "gen_roc",
    "pr_curve": "gen_pr_curve",
    "calibration": "gen_calibration",
    "km": "gen_km",
    "forest": "gen_forest",
    "waterfall": "gen_waterfall",
    "dose_response": "gen_dose_response",
    "scatter_regression": "gen_scatter_regression",
    "correlation": "gen_correlation",
    "manhattan": "gen_manhattan",
    "qq": "gen_qq",
    "spatial_feature": "gen_spatial_feature",
    "composition_dotplot": "gen_composition_dotplot",
    "ridge": "gen_ridge",
    "bubble_matrix": "gen_bubble_matrix",
    "stacked_bar_comp": "gen_stacked_bar_comp",
    "alluvial": "gen_alluvial",

    # Distribution variants (7)
    "violin_paired": "gen_violin_paired",
    "violin_split": "gen_violin_split",
    "dot_strip": "gen_dot_strip",
    "histogram": "gen_histogram",
    "density": "gen_density",
    "ecdf": "gen_ecdf",
    "joyplot": "gen_joyplot",

    # Time series variants (6)
    "sparkline": "gen_sparkline",
    "area": "gen_area",
    "area_stacked": "gen_area_stacked",
    "streamgraph": "gen_streamgraph",
    "gantt": "gen_gantt",
    "timeline_annotation": "gen_timeline_annotation",

    # Statistical / diagnostic (12)
    "residual_vs_fitted": "gen_residual_vs_fitted",
    "scale_location": "gen_scale_location",
    "cook_distance": "gen_cook_distance",
    "leverage_plot": "gen_leverage_plot",
    "pp_plot": "gen_pp_plot",
    "bland_altman": "gen_bland_altman",
    "funnel_plot": "gen_funnel_plot",
    "pareto_chart": "gen_pareto_chart",
    "control_chart": "gen_control_chart",
    "box_paired": "gen_box_paired",
    "mean_diff_plot": "gen_mean_diff_plot",
    "ci_plot": "gen_ci_plot",

    # Matrix / heatmap variants (7)
    "dotplot": "gen_dotplot",
    "adjacency_matrix": "gen_adjacency_matrix",
    "heatmap_annotated": "gen_heatmap_annotated",
    "confusion_matrix": "gen_confusion_matrix",
    "heatmap_triangular": "gen_heatmap_triangular",
    "heatmap_mirrored": "gen_heatmap_mirrored",
    "cooccurrence_matrix": "gen_cooccurrence_matrix",

    # Genomics extended (6)
    "circos_karyotype": "gen_circos_karyotype",
    "gene_structure": "gen_gene_structure",
    "pathway_map": "gen_pathway_map",
    "kegg_bar": "gen_kegg_bar",
    "go_treemap": "gen_go_treemap",
    "chromosome_coverage": "gen_chromosome_coverage",

    # Clinical extended (6)
    "swimmer_plot": "gen_swimmer_plot",
    "risk_ratio_plot": "gen_risk_ratio_plot",
    "caterpillar_plot": "gen_caterpillar_plot",
    "tornado_chart": "gen_tornado_chart",
    "nomogram": "gen_nomogram",
    "decision_curve": "gen_decision_curve",

    # Composition / hierarchical (6)
    "treemap": "gen_treemap",
    "sunburst": "gen_sunburst",
    "waffle_chart": "gen_waffle_chart",
    "marimekko": "gen_marimekko",
    "stacked_area_comp": "gen_stacked_area_comp",
    "nested_donut": "gen_nested_donut",

    # Relationship / network (4)
    "chord_diagram": "gen_chord_diagram",
    "parallel_coordinates": "gen_parallel_coordinates",
    "sankey": "gen_sankey",
    "radar": "gen_radar",

    # Engineering / materials (6)
    "stress_strain": "gen_stress_strain",
    "phase_diagram": "gen_phase_diagram",
    "nyquist_plot": "gen_nyquist_plot",
    "xrd_pattern": "gen_xrd_pattern",
    "ftir_spectrum": "gen_ftir_spectrum",
    "dsc_thermogram": "gen_dsc_thermogram",

    # Ecology / environmental (4)
    "species_abundance": "gen_species_abundance",
    "shannon_diversity": "gen_shannon_diversity",
    "ordination_plot": "gen_ordination_plot",
    "biodiversity_radar": "gen_biodiversity_radar",

    # Psychology / social (4)
    "likert_divergent": "gen_likert_divergent",
    "likert_stacked": "gen_likert_stacked",
    "mediation_path": "gen_mediation_path",
    "interaction_plot": "gen_interaction_plot",

    # Additional variants (12)
    "bubble_scatter": "gen_bubble_scatter",
    "connected_scatter": "gen_connected_scatter",
    "stem_plot": "gen_stem_plot",
    "lollipop_horizontal": "gen_lollipop_horizontal",
    "slope_chart": "gen_slope_chart",
    "bump_chart": "gen_bump_chart",
    "mosaic_plot": "gen_mosaic_plot",
    "clustered_bar": "gen_clustered_bar",
    "diverging_bar": "gen_diverging_bar",
    "grouped_bar": "gen_grouped_bar",
    "heatmap_symmetric": "gen_heatmap_symmetric",
    "violin_grouped": "gen_violin_grouped"
}
```
