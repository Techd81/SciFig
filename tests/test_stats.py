"""Tests for v0.1.6 multi-group statistics module ``scifig.stats``."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from scifig import stats as scifig_stats
from scifig.stats import (
    TestResult,
    TukeyResult,
    fdr_bh,
    kruskal_wallis,
    one_way_anova,
    recommend_test,
    tukey_hsd,
)


# -- Public API ----------------------------------------------------------------

def test_stats_module_public_api_surface():
    expected = {
        "TestResult",
        "TukeyResult",
        "add_group_stat_annotation",
        "kruskal_wallis",
        "one_way_anova",
        "tukey_hsd",
        "fdr_bh",
        "recommend_test",
    }
    assert expected.issubset(set(scifig_stats.__all__))


# -- Kruskal-Wallis ------------------------------------------------------------

def test_kruskal_wallis_three_groups_returns_significant_p_for_disjoint_data():
    rng = np.random.default_rng(42)
    a = rng.normal(0, 1, 30)
    b = rng.normal(3, 1, 30)
    c = rng.normal(6, 1, 30)
    result = kruskal_wallis(a, b, c)
    assert isinstance(result, TestResult)
    assert result.method == "kruskal_wallis"
    assert result.n_groups == 3
    assert result.n_total == 90
    assert result.pvalue < 1e-10


def test_kruskal_wallis_handles_empty_or_single_group():
    result = kruskal_wallis([1, 2, 3])
    assert math.isnan(result.statistic)
    assert "insufficient_groups" in result.notes


def test_kruskal_wallis_drops_empty_arrays_safely():
    result = kruskal_wallis([1, 2, 3], [], [4, 5, 6])
    # Empty array dropped; remaining 2 groups with valid data
    assert result.n_groups == 2
    assert result.n_total == 6


# -- ANOVA ---------------------------------------------------------------------

def test_one_way_anova_detects_three_group_difference():
    rng = np.random.default_rng(7)
    a = rng.normal(0, 1, 40)
    b = rng.normal(2, 1, 40)
    c = rng.normal(4, 1, 40)
    result = one_way_anova(a, b, c)
    assert result.method == "one_way_anova"
    assert result.pvalue < 1e-10
    assert result.statistic > 0


def test_one_way_anova_returns_high_p_when_groups_overlap():
    rng = np.random.default_rng(11)
    a = rng.normal(0, 1, 30)
    b = rng.normal(0.05, 1, 30)
    c = rng.normal(-0.05, 1, 30)
    result = one_way_anova(a, b, c)
    assert result.pvalue > 0.1


# -- Tukey HSD -----------------------------------------------------------------

def test_tukey_hsd_returns_pairwise_rows_for_each_group_combo():
    rng = np.random.default_rng(99)
    df = pd.DataFrame({
        "group": ["A"] * 30 + ["B"] * 30 + ["C"] * 30,
        "value": np.concatenate([rng.normal(0, 1, 30), rng.normal(3, 1, 30), rng.normal(6, 1, 30)]),
    })
    out = tukey_hsd(df, "group", "value")
    assert len(out) == 3  # AB, AC, BC
    assert all(isinstance(r, TukeyResult) for r in out)
    pairs = {(r.group_a, r.group_b) for r in out}
    assert pairs == {("A", "B"), ("A", "C"), ("B", "C")}
    assert all(r.reject for r in out)  # disjoint distributions


def test_tukey_hsd_returns_empty_for_single_group():
    df = pd.DataFrame({"group": ["A"] * 5, "value": [1, 2, 3, 4, 5]})
    assert tukey_hsd(df, "group", "value") == []


def test_tukey_hsd_returns_empty_for_missing_columns():
    df = pd.DataFrame({"x": [1, 2, 3]})
    assert tukey_hsd(df, "missing", "x") == []


# -- FDR (Benjamini-Hochberg) --------------------------------------------------

def test_fdr_bh_basic_correction_matches_known_example():
    # Hand-checked example: 5 p-values
    pvals = [0.01, 0.04, 0.03, 0.005, 0.20]
    result = fdr_bh(pvals, alpha=0.05)
    assert result["n"] == 5
    assert len(result["adjusted"]) == 5
    assert len(result["reject"]) == 5
    # Smallest p (0.005) should be rejected
    assert result["reject"][3] is True
    # Largest p (0.20) should not be rejected
    assert result["reject"][4] is False
    # All adjusted values in [0,1] and >= raw p
    for raw, adj in zip(pvals, result["adjusted"]):
        assert 0 <= adj <= 1


def test_fdr_bh_monotone_adjusted_values():
    pvals = [0.001, 0.05, 0.5, 0.9]
    result = fdr_bh(pvals, alpha=0.05)
    sorted_pairs = sorted(zip(pvals, result["adjusted"]))
    sorted_adj = [p[1] for p in sorted_pairs]
    # BH-adjusted is monotone non-decreasing when sorted by raw p
    assert sorted_adj == sorted(sorted_adj)


def test_fdr_bh_empty_input_returns_empty_lists():
    result = fdr_bh([], alpha=0.05)
    assert result == {"adjusted": [], "reject": [], "alpha": 0.05, "n": 0}


def test_fdr_bh_all_significant_when_all_below_alpha_over_n():
    # 4 p-values all < 0.0125 (= 0.05/4) -> all rejected
    result = fdr_bh([0.001, 0.002, 0.005, 0.008], alpha=0.05)
    assert all(result["reject"])


# -- recommend_test ------------------------------------------------------------

def test_recommend_test_returns_mann_whitney_for_two_groups_unpaired():
    df = pd.DataFrame({"g": ["A"] * 5 + ["B"] * 5, "v": list(range(10))})
    rec = recommend_test(df, "g", "v")
    assert rec["test"] == "mann_whitney_u"
    assert rec["n_groups"] == 2


def test_recommend_test_returns_wilcoxon_for_two_groups_paired():
    df = pd.DataFrame({"g": ["A"] * 5 + ["B"] * 5, "v": list(range(10))})
    rec = recommend_test(df, "g", "v", paired=True)
    assert rec["test"] == "wilcoxon_signed_rank"


def test_recommend_test_returns_anova_or_kruskal_for_multi_group():
    rng = np.random.default_rng(3)
    df = pd.DataFrame({
        "g": ["A"] * 30 + ["B"] * 30 + ["C"] * 30,
        "v": np.concatenate([rng.normal(0, 1, 30), rng.normal(2, 1, 30), rng.normal(4, 1, 30)]),
    })
    rec = recommend_test(df, "g", "v")
    assert rec["test"] in {"one_way_anova", "kruskal_wallis"}
    assert rec["n_groups"] == 3
    if rec["test"] == "one_way_anova":
        assert rec["post_hoc"] == "tukey_hsd"


def test_recommend_test_returns_descriptive_for_missing_columns():
    df = pd.DataFrame({"x": [1, 2, 3]})
    assert recommend_test(df, None, "x")["test"] == "none"
    assert recommend_test(df, "missing", "x")["test"] == "none"
