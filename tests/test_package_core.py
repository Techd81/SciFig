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
    assert scifig.__version__ == "0.1.5"
    assert callable(scifig.plot)
    assert scifig.Figure is not None
    assert hasattr(scifig, "styles")
    assert hasattr(scifig, "polish")
    assert callable(scifig.list_charts)


def test_chart_registry_exposes_121_callables_and_aliases():
    charts = scifig.list_charts()
    assert len(charts) == 121
    assert "volcano" in charts
    assert scifig.get_chart_info("ridgeline")["key"] == "ridge"
    for key in charts:
        assert key in scifig.CHART_GENERATORS
        assert callable(scifig.CHART_GENERATORS[key])


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
