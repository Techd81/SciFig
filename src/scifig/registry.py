"""Chart registry and chart metadata."""

from __future__ import annotations

from typing import Callable, Dict, List

ChartGenerator = Callable[..., object]

CHART_KEYS = [
    "violin_strip", "box_strip", "raincloud", "beeswarm", "paired_lines", "dumbbell", "line",
    "training_curve", "model_architecture", "model_architecture_board", "line_ci", "spaghetti",
    "heatmap_cluster", "heatmap_pure", "volcano", "ma_plot", "pca", "umap", "tsne",
    "enrichment_dotplot", "oncoprint", "lollipop_mutation", "rf_classifier_report_board",
    "classifier_validation_board", "roc", "pr_curve", "calibration", "km", "forest",
    "waterfall", "dose_response", "scatter_regression", "correlation", "manhattan", "qq",
    "spatial_feature", "composition_dotplot", "ridge", "bubble_matrix", "stacked_bar_comp",
    "alluvial", "violin_paired", "violin_split", "dot_strip", "histogram", "density", "ecdf",
    "joyplot", "sparkline", "area", "area_stacked", "streamgraph", "gantt",
    "timeline_annotation", "residual_vs_fitted", "scale_location", "cook_distance",
    "leverage_plot", "pp_plot", "bland_altman", "funnel_plot", "pareto_chart",
    "control_chart", "box_paired", "mean_diff_plot", "ci_plot", "dotplot", "adjacency_matrix",
    "heatmap_annotated", "confusion_matrix", "heatmap_triangular", "heatmap_mirrored",
    "cooccurrence_matrix", "circos_karyotype", "gene_structure", "pathway_map", "kegg_bar",
    "go_treemap", "chromosome_coverage", "swimmer_plot", "risk_ratio_plot",
    "caterpillar_plot", "tornado_chart", "nomogram", "decision_curve", "treemap", "sunburst",
    "waffle_chart", "marimekko", "stacked_area_comp", "nested_donut", "chord_diagram",
    "parallel_coordinates", "sankey", "radar", "stress_strain", "phase_diagram",
    "nyquist_plot", "xrd_pattern", "ftir_spectrum", "dsc_thermogram", "species_abundance",
    "shannon_diversity", "ordination_plot", "biodiversity_radar", "likert_divergent",
    "likert_stacked", "mediation_path", "interaction_plot", "bubble_scatter",
    "connected_scatter", "stem_plot", "lollipop_horizontal", "slope_chart", "bump_chart",
    "mosaic_plot", "clustered_bar", "diverging_bar", "grouped_bar", "heatmap_symmetric",
    "violin_grouped",
]

ALIASES = {
    "violin+strip": "violin_strip",
    "box+strip": "box_strip",
    "dot+box": "box_strip",
    "heatmap+cluster": "heatmap_cluster",
    "ridgeline": "ridge",
    # v0.1.5 UX aliases — collapse common short names to the most general
    # variant in CHART_KEYS so ``scifig.plot(df, chart='bar')`` does not
    # require users to pre-disambiguate "grouped" vs "clustered" vs "diverging".
    "bar": "grouped_bar",
    "boxplot": "box_strip",
    "violin": "violin_strip",
    "scatter": "scatter_regression",
    "heatmap": "heatmap_pure",
    "histogram_density": "density",
    "stacked_bar": "stacked_bar_comp",
    "lollipop": "lollipop_horizontal",
}

CHART_GENERATORS: Dict[str, ChartGenerator] = {}


def resolve_chart_key(chart: str) -> str:
    key = ALIASES.get(chart, chart)
    if key not in CHART_KEYS and key not in CHART_GENERATORS:
        raise ValueError(f"Unknown chart '{chart}'. Valid charts: {', '.join(list_charts())}")
    return key


def list_charts() -> List[str]:
    return sorted(set(CHART_KEYS) | set(CHART_GENERATORS))


def register_chart(name: str) -> Callable[[ChartGenerator], ChartGenerator]:
    def decorator(func: ChartGenerator) -> ChartGenerator:
        if not callable(func):
            raise TypeError("Registered chart generator must be callable.")
        if name not in CHART_KEYS:
            CHART_KEYS.append(name)
        CHART_GENERATORS[name] = func
        return func
    return decorator


def get_chart_info(name: str) -> dict[str, str]:
    key = resolve_chart_key(name)
    return {
        "key": key,
        "family": _family_for_key(key),
        "category": _family_for_key(key).replace("_", " ").title(),
        "description": key.replace("_", " ").title(),
    }


def _family_for_key(key: str) -> str:
    if any(token in key for token in ("heatmap", "matrix", "correlation")):
        return "matrix_heatmap"
    if any(token in key for token in ("roc", "pr_", "calibration", "classifier", "training", "model")):
        return "ml_diagnostic"
    if any(token in key for token in ("volcano", "ma_plot", "gene", "chromosome", "manhattan", "qq")):
        return "genomics"
    if any(token in key for token in ("km", "forest", "risk", "swimmer", "nomogram")):
        return "clinical"
    if any(token in key for token in ("line", "area", "stream", "time", "gantt", "spark")):
        return "time_series"
    if any(token in key for token in ("violin", "box", "density", "histogram", "ridge", "ecdf")):
        return "distribution"
    return "general"
