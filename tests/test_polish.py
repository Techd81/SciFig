"""Tests for the canonical figure-finalizer module ``scifig.polish``.

The polish module is the v0.1.5 single source of truth for the legend contract
finalizer that the skill (``scifig-generate``) used to embed via ``exec()``.
These tests pin the public API surface and the legend-contract behavior.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from scifig import polish


# -- Public API surface --------------------------------------------------------

def test_polish_module_public_api_surface():
    expected = {
        "CROWDING_DEFAULTS",
        "enforce",
        "enforce_figure_legend_contract",
        "sanitize_columns",
        "apply_chart_polish",
        "add_significance_bracket",
        "format_p_value",
        "normalize_axes_map",
        "collect_legend_handles",
        "promote_to_bottom_center_legend",
    }
    assert expected.issubset(set(polish.__all__))
    for name in expected:
        assert hasattr(polish, name), f"polish.{name} missing"


def test_enforce_alias_points_to_enforce_figure_legend_contract():
    assert polish.enforce is polish.enforce_figure_legend_contract


# -- sanitize_columns ----------------------------------------------------------

def test_sanitize_columns_renames_unsafe_identifiers_and_records_map():
    df = pd.DataFrame({"col with space": [1, 2], "2-bad": [3, 4], "fine": [5, 6]})
    df_out, name_map = polish.sanitize_columns(df)
    assert list(df_out.columns) == ["col_with_space", "col_2_bad", "fine"]
    assert name_map == {"col_with_space": "col with space", "col_2_bad": "2-bad"}


def test_sanitize_columns_deduplicates_collisions():
    df = pd.DataFrame({"a b": [1], "a-b": [2]})
    df_out, name_map = polish.sanitize_columns(df)
    assert list(df_out.columns) == ["a_b", "a_b_1"]
    assert name_map["a_b"] == "a b"
    assert name_map["a_b_1"] == "a-b"


# -- apply_chart_polish --------------------------------------------------------

def test_apply_chart_polish_hides_top_right_spines_for_cartesian():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    polish.apply_chart_polish(ax, "scatter")
    assert ax.spines["top"].get_visible() is False
    assert ax.spines["right"].get_visible() is False
    plt.close(fig)


def test_apply_chart_polish_polar_safe_no_keyerror():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="polar")
    polish.apply_chart_polish(ax, "radar")  # must not raise
    plt.close(fig)


def test_apply_chart_polish_anchors_baseline_for_ratio_charts():
    fig, ax = plt.subplots()
    ax.bar(["a", "b"], [3, 5])
    ax.set_ylim(2, 6)
    polish.apply_chart_polish(ax, "bar")
    assert ax.get_ylim()[0] == 0
    plt.close(fig)


# -- format_p_value ------------------------------------------------------------

def test_format_p_value_below_threshold_uses_lt():
    assert polish.format_p_value(0.0001) == "p < 0.001"


def test_format_p_value_above_threshold_uses_two_sig_figs():
    assert polish.format_p_value(0.024) == "p = 0.024"


# -- enforce: legend promotion -------------------------------------------------

def test_enforce_promotes_per_axes_legend_to_single_bottom_center_figure_legend():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="series A")
    ax.plot([0, 1], [1, 0], label="series B")
    ax.legend(loc="upper right")
    assert ax.get_legend() is not None

    report = polish.enforce(fig)

    assert ax.get_legend() is None
    assert len(fig.legends) == 1
    legend = fig.legends[0]
    labels = [t.get_text() for t in legend.get_texts()]
    assert labels == ["series A", "series B"]
    assert report["hasFigureLegend"] is True
    assert report["axisLegendRemainingCount"] == 0
    assert report["legendInputEntryCount"] == 2
    assert report["legendModeUsed"] == "bottom_center"
    assert report["legendFrameApplied"] is True
    assert report["legendContractEnforced"] is True
    assert report["legendContractFailures"] == []
    plt.close(fig)


def test_enforce_returns_no_legend_when_no_handles_present():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])  # no label
    report = polish.enforce(fig)
    assert report["hasFigureLegend"] is False
    assert report["legendInputEntryCount"] == 0
    assert len(fig.legends) == 0
    assert report["legendContractFailures"] == []
    plt.close(fig)


def test_enforce_dedupes_repeated_labels_across_panels():
    fig, axes = plt.subplots(1, 2)
    for ax in axes:
        ax.plot([0, 1], [0, 1], label="shared")
        ax.legend()

    report = polish.enforce(fig)
    assert report["legendInputEntryCount"] == 1  # deduped
    assert len(fig.legends[0].get_texts()) == 1
    plt.close(fig)


def test_enforce_drops_existing_figure_legends_to_keep_exactly_one():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="x")
    fig.legend(loc="upper right")
    fig.legend(loc="upper left")  # second pre-existing
    polish.enforce(fig)
    assert len(fig.legends) == 1
    plt.close(fig)


def test_enforce_strict_mode_raises_when_contract_failure_present(monkeypatch):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="x")

    # Force a fake failure by stubbing the anchor checker.
    def _fake_check(legend):
        return ["outside_right_legend_bbox_anchor"]

    monkeypatch.setattr(polish, "_check_legend_anchor_forbidden", _fake_check)

    with pytest.raises(RuntimeError, match="outside_right_legend_bbox_anchor"):
        polish.enforce(fig, strict=True)
    plt.close(fig)


def test_enforce_respects_custom_fontsize_and_anchor_y():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label="x")
    polish.enforce(fig, crowding_plan={"legendFontSizePt": 9, "legendBottomAnchorY": 0.05})
    legend = fig.legends[0]
    text_size = legend.get_texts()[0].get_fontsize()
    assert text_size == 9
    plt.close(fig)


# -- normalize_axes_map --------------------------------------------------------

def test_normalize_axes_map_auto_discovers_when_none():
    fig, axes = plt.subplots(1, 3)
    axes_map = polish.normalize_axes_map(fig, None)
    assert list(axes_map.keys()) == ["A", "B", "C"]
    assert list(axes_map.values()) == list(axes)
    plt.close(fig)


def test_normalize_axes_map_passes_through_dict_input():
    fig, ax = plt.subplots()
    custom = {"P1": ax}
    out = polish.normalize_axes_map(fig, custom)
    assert out == custom
    plt.close(fig)


# -- add_significance_bracket --------------------------------------------------

def test_add_significance_bracket_emits_bracket_lines_and_p_label():
    fig, ax = plt.subplots()
    initial_lines = len(ax.lines)
    initial_texts = len(ax.texts)
    polish.add_significance_bracket(ax, x1=0, x2=1, y=10, height=2, p_value=0.0009)
    assert len(ax.lines) == initial_lines + 5  # 2 risers + bar + 2 caps
    assert len(ax.texts) == initial_texts + 1
    assert ax.texts[-1].get_text() == "p < 0.001"
    plt.close(fig)
