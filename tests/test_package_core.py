from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

import scifig
from scifig.cli import main as cli_main
from scifig.ingest import ROLE_ALIASES, profile_data
from scifig.styles import available_profiles, get_profile


def _volcano_df():
    return pd.DataFrame({
        "gene": [f"G{i}" for i in range(12)],
        "log2fc": np.linspace(-2.2, 2.2, 12),
        "padj": np.linspace(0.001, 0.2, 12),
    })


def _group_df():
    return pd.DataFrame({
        "group": ["A"] * 6 + ["B"] * 6,
        "value": [1.0, 1.1, 0.9, 1.2, 1.0, 0.95, 1.8, 1.7, 1.9, 2.0, 1.85, 1.75],
    })


def test_package_public_api_and_version():
    assert scifig.__version__ == "0.2.0"
    assert callable(scifig.plot)
    assert scifig.Figure is not None
    assert hasattr(scifig, "styles")
    assert hasattr(scifig, "polish")
    assert hasattr(scifig, "stats")
    assert hasattr(scifig, "compose")
    assert callable(scifig.list_charts)


def test_chart_registry_exposes_121_callables_and_aliases():
    charts = scifig.list_charts()
    assert len(charts) == 121
    assert "volcano" in charts
    assert scifig.get_chart_info("ridgeline")["key"] == "ridge"
    for key in charts:
        assert key in scifig.CHART_GENERATORS
        assert callable(scifig.CHART_GENERATORS[key])


def test_template_priority_charts_have_dedicated_generators():
    fallback = {
        key
        for key in scifig.list_charts()
        if getattr(scifig.CHART_GENERATORS[key], "__module__", "") == "scifig.charts"
    }
    dedicated = set(scifig.list_charts()) - fallback
    assert {
        "radar",
        "biodiversity_radar",
        "caterpillar_plot",
        "ci_plot",
        "decision_curve",
        "diverging_bar",
        "dotplot",
        "dumbbell",
        "heatmap_annotated",
        "heatmap_mirrored",
        "heatmap_symmetric",
        "heatmap_triangular",
        "lollipop_horizontal",
        "mean_diff_plot",
        "paired_lines",
        "pp_plot",
        "qq",
        "residual_vs_fitted",
        "risk_ratio_plot",
        "scale_location",
        "box_paired",
        "area",
        "bubble_scatter",
        "bump_chart",
        "connected_scatter",
        "cook_distance",
        "funnel_plot",
        "gantt",
        "leverage_plot",
        "ordination_plot",
        "slope_chart",
        "sparkline",
        "stacked_area_comp",
        "streamgraph",
        "tsne",
        "clustered_bar",
        "grouped_bar",
        "marimekko",
        "mosaic_plot",
        "nested_donut",
        "stacked_bar_comp",
        "sunburst",
        "treemap",
        "waffle_chart",
        "composition_dotplot",
        "go_treemap",
        "kegg_bar",
        "likert_divergent",
        "likert_stacked",
        "pareto_chart",
        "shannon_diversity",
        "species_abundance",
        "control_chart",
        "dsc_thermogram",
        "ftir_spectrum",
        "nyquist_plot",
        "phase_diagram",
        "stress_strain",
        "xrd_pattern",
        "adjacency_matrix",
        "alluvial",
        "bubble_matrix",
        "chord_diagram",
        "cooccurrence_matrix",
        "parallel_coordinates",
        "pathway_map",
        "sankey",
        "chromosome_coverage",
        "circos_karyotype",
        "enrichment_dotplot",
        "gene_structure",
        "lollipop_mutation",
        "oncoprint",
        "nomogram",
        "swimmer_plot",
        "timeline_annotation",
        "tornado_chart",
        "dot_strip",
        "ecdf",
        "joyplot",
        "stem_plot",
        "violin_grouped",
        "violin_paired",
        "violin_split",
        "classifier_validation_board",
        "interaction_plot",
        "mediation_path",
        "model_architecture",
        "model_architecture_board",
        "rf_classifier_report_board",
        "spatial_feature",
    }.isdisjoint(fallback)
    assert len(dedicated) == 121


def test_v015_short_name_aliases_resolve():
    """v0.1.5 added common short names so users do not need to disambiguate
    grouped/clustered/diverging variants up front."""
    assert scifig.get_chart_info("bar")["key"] == "grouped_bar"
    assert scifig.get_chart_info("boxplot")["key"] == "box_strip"
    assert scifig.get_chart_info("violin")["key"] == "violin_strip"
    assert scifig.get_chart_info("scatter")["key"] == "scatter_regression"
    assert scifig.get_chart_info("heatmap")["key"] == "heatmap_pure"
    assert scifig.get_chart_info("stacked_bar")["key"] == "stacked_bar_comp"
    assert scifig.get_chart_info("lollipop")["key"] == "lollipop_horizontal"


def test_journal_profiles_are_complete_and_distinct():
    names = available_profiles()
    assert names == ["cell", "jama", "lancet", "nature", "nejm", "science"]
    required = {
        "single_width_mm", "double_width_mm", "max_height_mm", "body_pt",
        "panel_label_pt", "axis_lw_pt", "tick_w_pt", "panel_gap_rel",
        "font_family", "grid", "legend_frame",
    }
    nature = get_profile("nature")
    cell = get_profile("cell")
    assert required <= set(nature)
    assert nature["body_pt"] != cell["body_pt"]


def test_ingestion_profiles_file_and_semantic_roles(tmp_path):
    path = tmp_path / "data.csv"
    _group_df().to_csv(path, index=False)
    df, profile = profile_data(path)
    assert len(ROLE_ALIASES) >= 40
    assert profile.format == "csv"
    assert profile.structure == "tidy"
    assert profile.semantic_roles["group"] == "group"
    assert profile.semantic_roles["value"] == "value"
    assert profile.n_groups == 2
    assert len(df) == 12


def test_ingestion_maps_common_ml_score_and_truth_aliases():
    df, profile = profile_data(pd.DataFrame({
        "model": ["A", "A", "B", "B"],
        "fold": [0, 1, 0, 1],
        "y_true": [0, 1, 0, 1],
        "y_score": [0.1, 0.8, 0.2, 0.9],
    }))
    assert len(df) == 4
    assert profile.semantic_roles["score"] == "y_score"
    assert profile.semantic_roles["actual"] == "y_true"


def test_ingestion_maps_common_clinical_aliases():
    _, profile = profile_data(pd.DataFrame({
        "arm": ["A", "B"],
        "time_months": [12.0, 18.0],
        "event_observed": [1, 0],
        "term": ["Age", "Stage"],
        "estimate": [1.2, 0.8],
        "ci_lo": [0.9, 0.5],
        "ci_hi": [1.6, 1.1],
        "dose_um": [0.1, 1.0],
        "outcome": [0.9, 0.4],
    }))
    roles = profile.semantic_roles
    assert roles["survival_time"] == "time_months"
    assert roles["survival_event"] == "event_observed"
    assert roles["estimate"] == "estimate"
    assert roles["ci_low"] == "ci_lo"
    assert roles["ci_high"] == "ci_hi"
    assert roles["dose"] == "dose_um"
    assert roles["response"] == "outcome"


def test_ingestion_maps_explainability_importance_aliases():
    _, profile = profile_data(pd.DataFrame({
        "feature": ["A", "B"],
        "mean_abs_shap": [0.2, 0.5],
    }))
    assert profile.semantic_roles["feature_id"] == "feature"
    assert profile.semantic_roles["importance"] == "mean_abs_shap"


def test_ingestion_maps_paired_before_after_aliases():
    _, profile = profile_data(pd.DataFrame({
        "subject_id": ["S1", "S2"],
        "baseline": [1.0, 1.1],
        "post": [1.4, 1.5],
    }))
    roles = profile.semantic_roles
    assert roles["pair_id"] == "subject_id"
    assert roles["before"] == "baseline"
    assert roles["after"] == "post"


def test_ingestion_maps_scatter_diagnostic_aliases():
    _, profile = profile_data(pd.DataFrame({
        "x": [0.1, 0.2],
        "y": [1.0, 1.1],
        "bubble_size": [10, 20],
        "std_error": [0.2, 0.3],
        "hat_value": [0.05, 0.08],
        "cooks_d": [0.01, 0.02],
    }))
    roles = profile.semantic_roles
    assert roles["size"] == "bubble_size"
    assert roles["std_error"] == "std_error"
    assert roles["leverage"] == "hat_value"
    assert roles["cook_distance"] == "cooks_d"


def test_ingestion_maps_composition_hierarchy_aliases():
    _, profile = profile_data(pd.DataFrame({
        "site": ["Wetland", "Forest"],
        "species": ["A", "B"],
        "count": [42, 35],
        "parent": ["Plants", "Animals"],
        "subgroup": ["Tree", "Bird"],
    }))
    roles = profile.semantic_roles
    assert roles["category"] == "site"
    assert roles["group"] == "species"
    assert roles["weight"] == "count"
    assert roles["parent"] == "parent"
    assert roles["child"] == "subgroup"


def test_ingestion_maps_matrix_row_column_aliases():
    _, profile = profile_data(pd.DataFrame({
        "row": ["R1", "R2"],
        "column": ["C1", "C2"],
        "weight": [3.0, 4.0],
    }))
    roles = profile.semantic_roles
    assert roles["row"] == "row"
    assert roles["column"] == "column"
    assert roles["weight"] == "weight"


def test_ingestion_maps_engineering_materials_aliases():
    _, profile = profile_data(pd.DataFrame({
        "strain": [0.0, 0.1],
        "stress": [0.0, 200.0],
        "two_theta": [20.0, 30.0],
        "intensity": [100.0, 400.0],
        "z_real": [1.0, 2.0],
        "z_imag": [-0.5, -0.8],
        "heat_flow": [0.1, -0.2],
        "wavenumber": [4000.0, 3500.0],
    }))
    roles = profile.semantic_roles
    assert roles["strain"] == "strain"
    assert roles["stress"] == "stress"
    assert roles["two_theta"] == "two_theta"
    assert roles["intensity"] == "intensity"
    assert roles["z_real"] == "z_real"
    assert roles["z_imag"] == "z_imag"
    assert roles["heat_flow"] == "heat_flow"
    assert roles["wavenumber"] == "wavenumber"


def test_ingestion_maps_genomics_track_aliases():
    _, profile = profile_data(pd.DataFrame({
        "gene": ["TP53", "KRAS"],
        "sample_id": ["S1", "S2"],
        "mutation": ["missense", "frameshift"],
        "coverage": [32, 48],
        "feature_type": ["exon", "utr"],
        "start": [100, 200],
        "end": [150, 250],
        "strand": ["+", "+"],
        "gene_count": [12, 8],
        "enrichment_score": [1.6, 1.2],
    }))
    roles = profile.semantic_roles
    assert roles["gene"] == "gene"
    assert roles["sample"] == "sample_id"
    assert roles["alteration"] == "mutation"
    assert roles["coverage"] == "coverage"
    assert roles["feature_type"] == "feature_type"
    assert roles["gene_count"] == "gene_count"
    assert roles["enrichment_score"] == "enrichment_score"


def test_radar_generator_renders_template_backed_polar_chart():
    df = pd.DataFrame({
        "cohort": ["A", "A", "A", "A", "B", "B", "B", "B"],
        "metric": ["Accuracy", "Stability", "Compactness", "Fidelity"] * 2,
        "score": [0.82, 0.72, 0.66, 0.91, 0.75, 0.86, 0.79, 0.68],
    })
    fig = scifig.plot(df, chart="radar", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(ax, "name", "") == "polar"
        assert len(ax.lines) >= 6
        assert len(ax.collections) >= 2
        assert [label.get_text() for label in ax.get_xticklabels()] == [
            "Accuracy", "Compactness", "Fidelity", "Stability",
        ]
    finally:
        plt.close(fig)


def test_biodiversity_radar_wide_metrics_render_as_polar_profile():
    df = pd.DataFrame({
        "site": ["Wetland", "Forest"],
        "shannon": [0.86, 0.71],
        "simpson": [0.77, 0.69],
        "richness": [42, 35],
        "evenness": [0.64, 0.58],
    })
    fig = scifig.plot(df, chart="biodiversity_radar", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(ax, "name", "") == "polar"
        assert (ax.get_title() or "") == "Biodiversity radar"
        assert len(ax.lines) >= 6
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["heatmap_triangular", "heatmap_symmetric", "heatmap_mirrored", "heatmap_annotated"])
def test_pairwise_heatmap_template_generators_use_diverging_correlation_grammar(chart_key):
    rng = np.random.default_rng(12)
    base = rng.normal(0.0, 1.0, 36)
    df = pd.DataFrame({
        "F1": base,
        "F2": base * 0.8 + rng.normal(0.0, 0.2, 36),
        "F3": -base * 0.6 + rng.normal(0.0, 0.3, 36),
        "F4": rng.normal(0.0, 1.0, 36),
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert len(ax.images) == 1
        image = ax.images[0]
        assert image.get_cmap().name == "RdBu_r"
        assert getattr(image.norm, "vcenter", None) == 0.0
        assert len(ax.texts) >= 4
        assert "heatmap" in (ax.get_title() or "").lower()
    finally:
        plt.close(fig)


def test_ml_curves_use_y_score_y_true_aliases():
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "model": ["A"] * 30 + ["B"] * 30,
        "fold": [0, 1, 2] * 20,
        "y_true": [1] * 30 + [0] * 30,
        "y_score": np.concatenate([rng.normal(0.8, 0.08, 30), rng.normal(0.2, 0.08, 30)]),
    })
    fig = scifig.plot(df, chart="pr_curve", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert len(ax.lines) >= 1
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["classifier_validation_board", "rf_classifier_report_board"])
def test_classifier_board_generators_render_validation_panels(chart_key):
    rng = np.random.default_rng(23)
    df = pd.DataFrame({
        "model": ["RF"] * 40,
        "y_true": [1] * 20 + [0] * 20,
        "y_score": np.concatenate([rng.normal(0.82, 0.08, 20), rng.normal(0.22, 0.08, 20)]).clip(0, 1),
        "feature": [f"F{i % 5}" for i in range(40)],
        "mean_abs_shap": np.tile([0.5, 0.4, 0.3, 0.2, 0.1], 8),
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_ml"
        assert len(ax.child_axes) >= 4
        assert "Need " not in " ".join(text.get_text() for axis in fig.axes for text in axis.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["roc", "pr_curve"])
def test_classifier_curves_report_invalid_binary_inputs(chart_key):
    df = pd.DataFrame({"score": [0.1, 0.4, np.nan, np.inf], "label": [2, 3, 1, 0]})
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert len(ax.lines) == 0
        assert "binary label" in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_calibration_filters_invalid_probabilities_and_labels():
    df = pd.DataFrame({"score": [-0.1, 1.2, np.nan, np.inf, 0.5], "label": [0, 1, 0, 1, 2]})
    fig = scifig.plot(df, chart="calibration", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert len(ax.lines) == 0
        assert "valid probability-label pairs" in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_km_uses_survival_role_aliases_before_numeric_fallback():
    df = pd.DataFrame({
        "age": [60, 61, 62, 63, 64, 65],
        "arm": ["A", "A", "A", "B", "B", "B"],
        "time_months": [3, 6, 9, 4, 8, 12],
        "event_observed": [1, 0, 1, 1, 0, 1],
    })
    fig = scifig.plot(df, chart="km", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert len(ax.lines) >= 2
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_forest_uses_estimate_ci_roles_before_numeric_fallback():
    df = pd.DataFrame({
        "weight": [100, 120, 90],
        "term": ["Age", "Stage", "Treatment"],
        "estimate": [1.1, 0.8, 1.4],
        "ci_low": [0.7, 0.5, 1.0],
        "ci_high": [1.2, 1.1, 2.0],
    })
    fig = scifig.plot(df, chart="forest", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        ci_lines = [line for line in ax.lines if line.get_linestyle() != "--"]
        assert len(ci_lines) >= 3
        assert np.allclose(ci_lines[0].get_xdata(), [0.7, 1.2])
        assert [tick.get_text() for tick in ax.get_yticklabels()] == ["Age", "Stage", "Treatment"]
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["caterpillar_plot", "risk_ratio_plot", "ci_plot"])
def test_ci_family_generators_use_template_forest_grammar(chart_key):
    df = pd.DataFrame({
        "term": ["Age", "Stage", "Treatment"],
        "estimate": [1.1, 0.8, 1.4],
        "ci_low": [0.7, 0.5, 1.0],
        "ci_high": [1.2, 1.1, 2.0],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_clinical"
        assert len([line for line in ax.lines if line.get_linestyle() != "--"]) >= 3
        assert len(ax.collections) >= 3
        assert [tick.get_text() for tick in ax.get_yticklabels()]
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
        if chart_key == "risk_ratio_plot":
            assert ax.get_xscale() == "log"
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["qq", "pp_plot"])
def test_distribution_diagnostics_use_perfect_fit_reference(chart_key):
    rng = np.random.default_rng(11)
    df = pd.DataFrame({
        "actual": np.linspace(0.0, 1.0, 30),
        "predicted": np.linspace(0.0, 1.0, 30) + rng.normal(0.0, 0.08, 30),
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_diagnostics"
        assert len(ax.collections) >= 1
        assert any(line.get_linestyle() == "--" for line in ax.lines)
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["residual_vs_fitted", "scale_location"])
def test_residual_diagnostics_use_prediction_roles(chart_key):
    fitted = np.linspace(0.2, 2.0, 24)
    residual = np.sin(fitted * 3.0) * 0.08
    df = pd.DataFrame({
        "predicted": fitted,
        "actual": fitted + residual,
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_diagnostics"
        assert len(ax.collections) >= 1
        assert any(line.get_linestyle() == "--" for line in ax.lines)
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["lollipop_horizontal", "diverging_bar"])
def test_ranked_effect_generators_use_bipolar_zero_reference(chart_key):
    df = pd.DataFrame({
        "feature": ["Texture", "Area", "Compactness", "Symmetry"],
        "importance": [0.42, -0.31, 0.18, -0.09],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_ranked"
        assert any(line.get_linestyle() == "--" for line in ax.lines)
        assert len(ax.collections) >= (1 if chart_key == "lollipop_horizontal" else 0)
        assert len(ax.patches) >= (4 if chart_key == "diverging_bar" else 0)
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_dotplot_generator_uses_shap_feature_ordering_and_color_values():
    df = pd.DataFrame({
        "feature": ["A", "A", "B", "B", "C", "C"],
        "shap_value": [0.32, -0.21, 0.12, 0.18, -0.08, 0.04],
        "feature_value": [0.9, 0.2, 0.8, 0.7, 0.1, 0.3],
    })
    fig = scifig.plot(df, chart="dotplot", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["dotplot"], "__module__", "") == "scifig.generators_ranked"
        assert len(ax.collections) >= 1
        assert len(ax.collections[0].get_offsets()) == 6
        assert any(line.get_linestyle() == "--" for line in ax.lines)
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_decision_curve_generator_uses_threshold_net_benefit_roles():
    df = pd.DataFrame({
        "model": ["RF"] * 5 + ["GBM"] * 5,
        "threshold": list(np.linspace(0.1, 0.9, 5)) * 2,
        "net_benefit": [0.18, 0.22, 0.21, 0.17, 0.11, 0.14, 0.19, 0.18, 0.13, 0.08],
    })
    fig = scifig.plot(df, chart="decision_curve", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["decision_curve"], "__module__", "") == "scifig.generators_ranked"
        assert len(ax.lines) >= 3
        assert any(line.get_linestyle() == "--" for line in ax.lines)
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["paired_lines", "dumbbell", "box_paired", "mean_diff_plot"])
def test_paired_comparison_generators_use_subject_level_links(chart_key):
    df = pd.DataFrame({
        "subject_id": [f"S{i}" for i in range(6)],
        "baseline": [1.0, 1.2, 0.8, 1.1, 0.9, 1.3],
        "post": [1.4, 1.3, 1.1, 1.5, 1.0, 1.7],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_distribution"
        assert len(ax.lines) >= (3 if chart_key == "mean_diff_plot" else 6)
        assert "No plottable columns" not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["dot_strip", "violin_grouped", "ecdf", "joyplot"])
def test_distribution_variant_generators_render_grouped_samples(chart_key):
    df = pd.DataFrame({
        "group": ["A"] * 6 + ["B"] * 6,
        "value": [1.0, 1.1, 0.9, 1.2, 1.0, 1.3, 1.8, 1.7, 1.9, 2.0, 1.85, 1.75],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_distribution"
        assert len(ax.collections) + len(ax.lines) >= 1
        assert "No plottable columns" not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["violin_paired", "violin_split"])
def test_violin_specialized_generators_render_paired_or_split_samples(chart_key):
    if chart_key == "violin_paired":
        df = pd.DataFrame({
            "subject_id": [f"S{i}" for i in range(8)],
            "baseline": [1.0, 1.2, 0.8, 1.1, 0.9, 1.3, 1.05, 0.95],
            "post": [1.4, 1.3, 1.1, 1.5, 1.0, 1.7, 1.2, 1.1],
        })
    else:
        df = pd.DataFrame({
            "group": ["Control"] * 8 + ["Treatment"] * 8,
            "value": [1.0, 1.1, 0.9, 1.2, 1.0, 1.3, 0.95, 1.05,
                      1.7, 1.8, 1.6, 1.9, 1.75, 1.85, 1.65, 1.95],
        })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_distribution"
        assert len(ax.collections) + len(ax.lines) >= 2
        assert "No plottable columns" not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_stem_plot_generator_renders_stems_and_baseline():
    df = pd.DataFrame({
        "time": [0, 1, 2, 3, 4],
        "value": [0.2, -0.1, 0.4, 0.1, 0.5],
    })
    fig = scifig.plot(df, chart="stem_plot", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["stem_plot"], "__module__", "") == "scifig.generators_distribution"
        assert len(ax.lines) >= 1
        assert len(ax.collections) >= 1
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["tsne", "ordination_plot"])
def test_embedding_generators_render_distinct_projection_axes(chart_key):
    rng = np.random.default_rng(19)
    df = pd.DataFrame({
        "group": ["A"] * 8 + ["B"] * 8,
        "f1": rng.normal(0, 1, 16),
        "f2": rng.normal(1, 1, 16),
        "f3": rng.normal(2, 1, 16),
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_scatter"
        assert len(ax.collections) >= 1
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
        assert ("t-SNE" in ax.get_xlabel()) if chart_key == "tsne" else ("Axis" in ax.get_xlabel())
    finally:
        plt.close(fig)


def test_interaction_plot_generator_renders_group_response_profiles():
    df = pd.DataFrame({
        "cohort": ["A", "A", "A", "B", "B", "B"],
        "time": [0, 1, 2] * 2,
        "value": [1.0, 1.2, 1.4, 0.9, 1.3, 1.8],
    })
    fig = scifig.plot(df, chart="interaction_plot", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["interaction_plot"], "__module__", "") == "scifig.generators_scatter"
        assert len(ax.lines) >= 2
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_spatial_feature_generator_renders_coordinate_value_map():
    df = pd.DataFrame({
        "spatial_x": [0.0, 1.0, 0.0, 1.0],
        "spatial_y": [0.0, 0.0, 1.0, 1.0],
        "expression": [0.2, 0.5, 0.8, 0.4],
    })
    fig = scifig.plot(df, chart="spatial_feature", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["spatial_feature"], "__module__", "") == "scifig.generators_scatter"
        assert len(ax.collections) >= 1
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["bubble_scatter", "connected_scatter"])
def test_scatter_embedding_generators_use_xy_and_size_roles(chart_key):
    df = pd.DataFrame({
        "cohort": ["A", "A", "B", "B"],
        "x": [0.1, 0.4, 0.2, 0.7],
        "y": [1.0, 1.4, 1.2, 1.9],
        "bubble_size": [10, 40, 20, 80],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_scatter"
        assert len(ax.collections) + len(ax.lines) >= 1
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["funnel_plot", "leverage_plot", "cook_distance"])
def test_scatter_diagnostic_generators_use_reference_guides(chart_key):
    df = pd.DataFrame({
        "estimate": [0.2, 0.1, -0.05, 0.3, -0.2, 0.15],
        "std_error": [0.2, 0.25, 0.3, 0.18, 0.35, 0.22],
        "residual": [0.1, -0.05, 0.2, -0.1, 0.04, -0.02],
        "hat_value": [0.05, 0.08, 0.12, 0.18, 0.09, 0.06],
        "cooks_d": [0.01, 0.03, 0.08, 0.12, 0.02, 0.04],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_scatter"
        assert len(ax.collections) + len(ax.lines) >= 1
        assert any(line.get_linestyle() in {"--", ":"} for line in ax.lines)
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["area", "stacked_area_comp", "streamgraph", "sparkline"])
def test_time_series_area_generators_use_time_value_roles(chart_key):
    df = pd.DataFrame({
        "cohort": ["A"] * 4 + ["B"] * 4,
        "week": [0, 1, 2, 3] * 2,
        "value": [1.0, 1.2, 1.5, 1.7, 0.8, 1.0, 1.1, 1.4],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_time_series"
        assert len(ax.collections) + len(ax.lines) >= 1
        assert "No plottable" not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_line_ci_uses_explicit_ci_bounds_before_sem_fallback():
    df = pd.DataFrame({
        "time": [0, 1, 2],
        "value": [1.0, 1.2, 1.5],
        "ci_low": [0.8, 1.0, 1.25],
        "ci_high": [1.2, 1.45, 1.8],
    })
    fig = scifig.plot(df, chart="line_ci", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["line_ci"], "__module__", "") == "scifig.generators_time_series"
        assert len(ax.collections) >= 1
        vertices = ax.collections[0].get_paths()[0].vertices
        assert vertices[:, 1].min() <= 0.8
        assert vertices[:, 1].max() >= 1.8
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_gantt_generator_uses_start_end_roles():
    df = pd.DataFrame({
        "task": ["Collect", "Train", "Validate"],
        "start": [0, 2, 5],
        "end": [2, 5, 7],
    })
    fig = scifig.plot(df, chart="gantt", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["gantt"], "__module__", "") == "scifig.generators_time_series"
        assert len(ax.patches) >= 3
        assert "No plottable" not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["bump_chart", "slope_chart"])
def test_rank_trajectory_generators_use_grouped_time_values(chart_key):
    df = pd.DataFrame({
        "cohort": ["A", "A", "A", "B", "B", "B", "C", "C", "C"],
        "week": [0, 1, 2] * 3,
        "value": [0.8, 1.0, 1.3, 1.1, 1.05, 1.0, 0.9, 1.2, 1.1],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_time_series"
        assert len(ax.lines) >= 3
        assert "No plottable" not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["grouped_bar", "clustered_bar", "stacked_bar_comp"])
def test_composition_bar_generators_use_category_group_weight_roles(chart_key):
    df = pd.DataFrame({
        "site": ["Wetland", "Wetland", "Forest", "Forest", "Grassland", "Grassland"],
        "species": ["A", "B", "A", "B", "A", "B"],
        "count": [42, 28, 35, 22, 30, 18],
        "richness": [7, 4, 6, 3, 5, 2],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_composition"
        assert len(ax.patches) >= 6
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "chart_key",
    ["waffle_chart", "treemap", "mosaic_plot", "marimekko", "nested_donut", "sunburst"],
)
def test_composition_hierarchy_generators_render_part_whole_geometry(chart_key):
    df = pd.DataFrame({
        "site": ["Wetland", "Wetland", "Forest", "Forest", "Grassland", "Grassland"],
        "species": ["A", "B", "A", "B", "A", "B"],
        "count": [42, 28, 35, 22, 30, 18],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_composition"
        minimum_patches = 3 if chart_key == "treemap" else 4
        assert len(ax.patches) >= minimum_patches
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["species_abundance", "shannon_diversity", "composition_dotplot"])
def test_ecology_composition_generators_use_site_species_counts(chart_key):
    df = pd.DataFrame({
        "site": ["Wetland", "Wetland", "Forest", "Forest", "Grassland", "Grassland"],
        "species": ["Acer", "Quercus", "Acer", "Quercus", "Acer", "Quercus"],
        "count": [42, 28, 35, 22, 30, 18],
        "richness": [7, 4, 6, 3, 5, 2],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_composition"
        assert len(ax.patches) + len(ax.collections) >= 1
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["go_treemap", "kegg_bar", "pareto_chart"])
def test_omics_enrichment_composition_generators_render_ranked_terms(chart_key):
    df = pd.DataFrame({
        "pathway": ["MAPK", "PI3K", "Apoptosis", "Cell cycle", "Metabolism"],
        "count": [18, 14, 11, 9, 6],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_composition"
        assert sum(len(axis.patches) for axis in fig.axes) >= 1
        if chart_key == "pareto_chart":
            assert sum(len(axis.lines) for axis in fig.axes) >= 1
        assert "Need " not in " ".join(text.get_text() for axis in fig.axes for text in axis.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["likert_stacked", "likert_divergent"])
def test_likert_generators_render_response_share_bars(chart_key):
    df = pd.DataFrame({
        "question": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2"],
        "response": ["Disagree", "Neutral", "Agree"] * 2,
        "count": [12, 8, 30, 18, 10, 22],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_composition"
        assert len(ax.patches) >= 6
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["sankey", "alluvial", "chord_diagram", "pathway_map"])
def test_network_flow_generators_render_relationship_geometry(chart_key):
    df = pd.DataFrame({
        "source": ["Input", "Input", "Filter", "Filter", "Model"],
        "target": ["Filter", "Model", "Model", "Report", "Report"],
        "weight": [18, 12, 9, 7, 14],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_network"
        assert len(ax.patches) + len(ax.lines) >= 3
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_parallel_coordinates_generator_renders_multivariate_profiles():
    df = pd.DataFrame({
        "cohort": ["A", "A", "B", "B"],
        "accuracy": [0.82, 0.76, 0.88, 0.91],
        "latency": [12.0, 14.0, 18.0, 17.0],
        "memory": [4.2, 4.8, 6.1, 5.7],
    })
    fig = scifig.plot(df, chart="parallel_coordinates", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["parallel_coordinates"], "__module__", "") == "scifig.generators_network"
        assert len(ax.lines) >= 4
        assert ax.get_ylim()[0] <= 0.0 and ax.get_ylim()[1] >= 1.0
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_model_architecture_generator_renders_node_link_topology():
    df = pd.DataFrame({
        "source": ["Input", "Encoder", "Encoder", "Head"],
        "target": ["Encoder", "Attention", "Head", "Output"],
        "weight": [1.0, 2.0, 1.5, 1.0],
    })
    fig = scifig.plot(df, chart="model_architecture", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["model_architecture"], "__module__", "") == "scifig.generators_network"
        assert len(ax.patches) >= 4
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_model_architecture_board_generator_renders_storyboard_support_axes():
    df = pd.DataFrame({
        "source": ["Input", "Encoder", "Encoder", "Head"],
        "target": ["Encoder", "Attention", "Head", "Output"],
        "weight": [1.0, 2.0, 1.5, 1.0],
        "latency_ms": [3.4, 5.2, 2.1, 1.0],
        "memory_mb": [128, 256, 192, 64],
    })
    fig = scifig.plot(df, chart="model_architecture_board", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["model_architecture_board"], "__module__", "") == "scifig.generators_network"
        support_axes = list(ax.child_axes)
        assert len(support_axes) == 3
        titles = [
            title
            for child in support_axes
            for title in (child.get_title(), child.get_title(loc="left"), child.get_title(loc="right"))
        ]
        assert any("architecture topology" in title for title in titles)
        assert any("metric profile" in title for title in titles)
        assert any("edge signal" in title for title in titles)
        assert sum(len(child.patches) for child in support_axes) >= 8
        text = " ".join(text.get_text() for axis in [ax, *support_axes] for text in axis.texts)
        assert "Need " not in text
    finally:
        plt.close(fig)


def test_mediation_path_generator_renders_coefficients():
    x = np.linspace(-1, 1, 12)
    df = pd.DataFrame({
        "x": x,
        "mediator": 0.6 * x + np.linspace(-0.1, 0.1, 12),
        "y": 0.3 * x + 0.5 * (0.6 * x) + np.linspace(0.05, -0.05, 12),
    })
    fig = scifig.plot(df, chart="mediation_path", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["mediation_path"], "__module__", "") == "scifig.generators_network"
        assert len(ax.patches) >= 8
        text = " ".join(text.get_text() for text in ax.texts)
        assert "indirect" in text
        assert "Effect summary" in text
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["adjacency_matrix", "cooccurrence_matrix", "bubble_matrix"])
def test_matrix_relationship_generators_render_dedicated_matrix_grammar(chart_key):
    df = pd.DataFrame({
        "row": ["A", "A", "B", "C"],
        "column": ["B", "C", "C", "A"],
        "weight": [5.0, 2.0, 4.0, 3.0],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_matrix"
        assert len(ax.images) + len(ax.collections) >= 1
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_chromosome_coverage_generator_renders_depth_track():
    df = pd.DataFrame({
        "chromosome": ["chr1"] * 5 + ["chr2"] * 5,
        "position": list(range(1, 6)) * 2,
        "coverage": [12, 18, 15, 21, 17, 9, 11, 14, 13, 16],
    })
    fig = scifig.plot(df, chart="chromosome_coverage", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["chromosome_coverage"], "__module__", "") == "scifig.generators_genomics"
        assert len(ax.lines) >= 2
        assert len(ax.collections) >= 2
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["circos_karyotype", "gene_structure"])
def test_genomic_interval_generators_render_track_blocks(chart_key):
    df = pd.DataFrame({
        "chromosome": ["chr1", "chr1", "chr2", "chr2"],
        "feature_type": ["exon", "intron", "exon", "utr"],
        "start": [100, 180, 80, 150],
        "end": [160, 240, 130, 210],
        "coverage": [3.0, 1.0, 4.0, 2.0],
        "strand": ["+"] * 4,
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_genomics"
        assert len(ax.patches) >= 4
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_enrichment_dotplot_generator_renders_term_score_bubbles():
    df = pd.DataFrame({
        "pathway": ["MAPK", "PI3K", "Apoptosis", "Cell cycle"],
        "enrichment_score": [1.8, 1.4, 1.1, 0.9],
        "gene_count": [18, 12, 9, 7],
        "padj": [0.001, 0.02, 0.04, 0.08],
    })
    fig = scifig.plot(df, chart="enrichment_dotplot", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["enrichment_dotplot"], "__module__", "") == "scifig.generators_genomics"
        assert len(ax.collections) >= 1
        assert any(line.get_linestyle() == "--" for line in ax.lines)
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_oncoprint_generator_renders_gene_sample_alteration_matrix():
    df = pd.DataFrame({
        "gene": ["TP53", "TP53", "KRAS", "EGFR", "EGFR"],
        "sample_id": ["S1", "S2", "S1", "S2", "S3"],
        "mutation": ["missense", "truncating", "missense", "amplification", "deletion"],
    })
    fig = scifig.plot(df, chart="oncoprint", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["oncoprint"], "__module__", "") == "scifig.generators_genomics"
        assert len(ax.images) == 1
        assert ax.get_xlabel().startswith("Samples")
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_lollipop_mutation_generator_renders_position_stems():
    df = pd.DataFrame({
        "position": [120, 175, 210, 330],
        "count": [3, 8, 5, 2],
        "mutation": ["R175H", "R248Q", "G245S", "R337C"],
    })
    fig = scifig.plot(df, chart="lollipop_mutation", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["lollipop_mutation"], "__module__", "") == "scifig.generators_genomics"
        assert len(ax.lines) >= 1
        assert len(ax.collections) >= 1
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_swimmer_plot_generator_renders_subject_followup_bars():
    df = pd.DataFrame({
        "patient": ["P1", "P2", "P3", "P4"],
        "start_time": [0, 0, 1, 2],
        "end_time": [8, 6, 10, 7],
        "arm": ["A", "A", "B", "B"],
    })
    fig = scifig.plot(df, chart="swimmer_plot", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["swimmer_plot"], "__module__", "") == "scifig.generators_clinical"
        assert len(ax.patches) >= 4
        assert len(ax.collections) >= 1
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


@pytest.mark.parametrize("chart_key", ["tornado_chart", "nomogram"])
def test_clinical_sensitivity_generators_render_dedicated_bars_and_scales(chart_key):
    df = pd.DataFrame({
        "term": ["Age", "Stage", "Marker", "Dose"],
        "low": [-0.3, -0.6, -0.2, -0.4],
        "high": [0.4, 0.8, 0.3, 0.5],
        "baseline": [0.0, 0.0, 0.0, 0.0],
        "score": [20, 45, 35, 55],
    })
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_clinical"
        assert len(ax.patches) + len(ax.lines) + len(ax.collections) >= 4
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_timeline_annotation_generator_renders_event_markers():
    df = pd.DataFrame({
        "time": [0, 2, 5, 9],
        "event": ["Enroll", "Dose", "Scan", "Response"],
        "cohort": ["A", "A", "B", "B"],
    })
    fig = scifig.plot(df, chart="timeline_annotation", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["timeline_annotation"], "__module__", "") == "scifig.generators_time_series"
        assert len(ax.lines) >= 1
        assert len(ax.collections) >= 1
        assert "No plottable" not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_stress_strain_generator_renders_peak_marker():
    df = pd.DataFrame({
        "strain": np.linspace(0, 0.22, 24),
        "stress": np.r_[np.linspace(0, 420, 18), np.linspace(415, 360, 6)],
    })
    fig = scifig.plot(df, chart="stress_strain", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["stress_strain"], "__module__", "") == "scifig.generators_engineering"
        assert len(ax.lines) >= 1
        assert len(ax.collections) >= 1
    finally:
        plt.close(fig)


def test_phase_diagram_generator_renders_phase_groups():
    df = pd.DataFrame({
        "composition": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        "temperature": [300, 330, 360, 390, 420, 450],
        "phase": ["alpha", "alpha", "beta", "beta", "gamma", "gamma"],
    })
    fig = scifig.plot(df, chart="phase_diagram", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS["phase_diagram"], "__module__", "") == "scifig.generators_engineering"
        assert len(ax.collections) >= 1
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    ("chart_key", "df"),
    [
        ("nyquist_plot", pd.DataFrame({"z_real": [1, 2, 3, 4], "z_imag": [-0.4, -0.9, -1.1, -0.8]})),
        ("xrd_pattern", pd.DataFrame({"two_theta": [10, 20, 30, 40, 50], "intensity": [5, 80, 12, 120, 20]})),
        ("ftir_spectrum", pd.DataFrame({"wavenumber": [4000, 3200, 2400, 1600, 800], "absorbance": [0.1, 0.4, 0.2, 0.6, 0.25]})),
        ("dsc_thermogram", pd.DataFrame({"temperature": [20, 60, 100, 140], "heat_flow": [0.1, -0.2, 0.3, -0.1]})),
        ("control_chart", pd.DataFrame({"sample": [1, 2, 3, 4, 5], "measurement": [10.0, 10.2, 9.8, 10.1, 10.3]})),
    ],
)
def test_engineering_curve_generators_render_domain_specific_guides(chart_key, df):
    fig = scifig.plot(df, chart=chart_key, style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert getattr(scifig.CHART_GENERATORS[chart_key], "__module__", "") == "scifig.generators_engineering"
        assert len(ax.lines) >= 1
        if chart_key == "ftir_spectrum":
            left, right = ax.get_xlim()
            assert left > right
        if chart_key in {"dsc_thermogram", "control_chart"}:
            assert any(line.get_linestyle() == "--" for line in ax.lines)
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_dose_response_uses_dose_alias_and_filters_nonfinite_rows():
    df = pd.DataFrame({
        "batch": [1, 1, 1, 1, 2, 2],
        "dose_um": [0.1, 1.0, 10.0, 100.0, np.inf, -1.0],
        "outcome": [0.95, 0.7, 0.35, 0.12, 0.5, np.inf],
    })
    fig = scifig.plot(df, chart="dose_response", style="nature", stats="none")
    try:
        ax = fig.axes[0]
        assert ax.get_xscale() == "log"
        assert len(ax.collections) >= 1
        assert len(ax.collections[0].get_offsets()) == 4
        assert "Need " not in " ".join(text.get_text() for text in ax.texts)
    finally:
        plt.close(fig)


def test_plot_returns_matplotlib_figure_and_validates_chart():
    fig = scifig.plot(_volcano_df(), chart="volcano", style="nature")
    assert isinstance(fig, plt.Figure)
    with pytest.raises(ValueError, match="Unknown chart"):
        scifig.plot(_volcano_df(), chart="not_a_chart")
    plt.close("all")


def test_plot_auto_and_export_writes_companion_files(tmp_path):
    out = tmp_path / "fig.svg"
    result = scifig.plot(_volcano_df(), chart="auto", style="cell", output=out)
    assert Path(result) == out
    assert out.exists()
    assert (tmp_path / "metadata.json").exists()
    assert (tmp_path / "requirements.txt").exists()


def test_builder_api_renders_multipanel(tmp_path):
    out = tmp_path / "multi.pdf"
    result = (
        scifig.Figure(style="nature")
        .add_panel(chart="volcano", data=_volcano_df(), position=(0, 0))
        .add_panel(chart="box_strip", data=_group_df(), position=(0, 1))
        .compose(recipe="story_board_2x2")
        .render(output=out)
    )
    assert Path(result) == out
    assert out.exists()
    assert (tmp_path / "metadata.json").exists()


def test_cli_help_list_and_plot(tmp_path, capsys):
    assert cli_main(["list-charts"]) == 0
    listed = capsys.readouterr().out
    assert "volcano" in listed
    data_path = tmp_path / "data.csv"
    _volcano_df().to_csv(data_path, index=False)
    out = tmp_path / "cli.png"
    assert cli_main(["plot", str(data_path), "--chart", "volcano", "--style", "nature", "-o", str(out)]) == 0
    assert out.exists()


def test_all_registered_charts_generate_without_stub_failures():
    df = pd.DataFrame({
        "group": ["A", "A", "B", "B"],
        "value": [1.0, 1.1, 2.0, 2.1],
        "x": [0.0, 1.0, 0.0, 1.0],
        "y": [1.0, 2.0, 2.0, 3.0],
        "log2fc": [-1.2, 1.3, 0.2, 2.1],
        "padj": [0.01, 0.02, 0.5, 0.001],
        "score": [0.1, 0.8, 0.2, 0.9],
        "actual": [0, 1, 0, 1],
        "time": [0, 1, 0, 1],
    })

    failed = []
    for chart in scifig.list_charts():
        try:
            fig = scifig.plot(df, chart=chart, style="nature", stats="none")
            fig.canvas.draw()
            plt.close(fig)
        except Exception as exc:  # noqa: BLE001 - report every chart failure together
            failed.append((chart, str(exc)))

    assert failed == []


def test_auto_chart_cli_and_tiff_export(tmp_path):
    data_path = tmp_path / "auto.csv"
    _volcano_df().to_csv(data_path, index=False)
    out = tmp_path / "auto.tiff"
    assert cli_main(["plot", str(data_path), "--chart", "auto", "--style", "science", "-o", str(out)]) == 0
    assert out.exists()
    assert out.stat().st_size > 1024


def test_v017_integer_column_names_are_coerced_to_strings():
    """Integer-keyed columns must round-trip through scifig.plot without KeyError."""
    import matplotlib
    matplotlib.use("Agg")
    df = pd.DataFrame({1: [1.0, 2.0, 3.0, 4.0], 2: [4.0, 5.0, 6.0, 7.0]})
    fig = scifig.plot(df, chart="scatter")
    assert fig is not None
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_v017_inf_values_in_scatter_regression_do_not_warn():
    """Infinite values must be filtered before the OLS computation."""
    import matplotlib
    matplotlib.use("Agg")
    import warnings as _warnings
    df = pd.DataFrame({
        "x": [1.0, float("inf"), 3.0, 4.0, 5.0],
        "y": [2.0, 5.0, 6.0, 8.0, 10.0],
    })
    with _warnings.catch_warnings():
        _warnings.simplefilter("error", RuntimeWarning)
        fig = scifig.plot(df, chart="scatter_regression")
    assert fig is not None
    import matplotlib.pyplot as plt
    plt.close(fig)
