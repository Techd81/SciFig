"""Statistical guardrails for scientific figures.

v0.1.5 shipped only ``add_group_stat_annotation`` (two-group Mann-Whitney).
v0.1.6 extends the module with multi-group hypothesis tests, post-hoc
pairwise comparison, and multiple-comparison correction so generators can
honestly annotate three-or-more-group figures without hand-rolling stats.

Public API:

- :func:`add_group_stat_annotation` - two-group Mann-Whitney bracket (existing)
- :func:`kruskal_wallis` - non-parametric multi-group H test
- :func:`one_way_anova` - parametric one-way ANOVA F test
- :func:`tukey_hsd` - post-hoc pairwise comparison with HSD-adjusted p-values
- :func:`fdr_bh` - Benjamini-Hochberg false discovery rate correction
- :func:`recommend_test` - pick the right test family from group/sample shape
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


__all__ = [
    "TestResult",
    "TukeyResult",
    "add_group_stat_annotation",
    "kruskal_wallis",
    "one_way_anova",
    "tukey_hsd",
    "fdr_bh",
    "recommend_test",
]


# ----------------------------------------------------------------------------
# Result containers
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class TestResult:
    """Generic hypothesis-test result."""
    statistic: float
    pvalue: float
    method: str
    n_groups: int
    n_total: int
    notes: tuple[str, ...] = ()


# Tell pytest not to try to collect this dataclass as a test class
TestResult.__test__ = False  # type: ignore[attr-defined]


@dataclass(frozen=True)
class TukeyResult:
    """Tukey HSD pairwise comparison row."""
    group_a: str
    group_b: str
    mean_diff: float
    pvalue: float
    reject: bool


# ----------------------------------------------------------------------------
# Existing two-group helper (v0.1.5 compat)
# ----------------------------------------------------------------------------

def add_group_stat_annotation(
    ax: Any,
    df: pd.DataFrame,
    group_col: Optional[str],
    value_col: Optional[str],
    mode: str,
) -> list[str]:
    """Annotate a two-group comparison with a Mann-Whitney p-value bracket."""
    if mode == "none" or not group_col or not value_col:
        return []
    if group_col not in df.columns or value_col not in df.columns:
        return []
    groups = [
        pd.to_numeric(part[value_col], errors="coerce").dropna()
        for _, part in df.groupby(group_col, sort=False)
    ]
    if len(groups) != 2 or min(len(g) for g in groups) < 2:
        if mode == "strict":
            return ["statistical_test_degraded_to_descriptive"]
        return []
    try:
        from scipy import stats  # type: ignore[import-untyped]
        p_value = float(stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided").pvalue)
    except Exception:
        return ["statistical_test_unavailable"]
    y_max = max(float(g.max()) for g in groups if len(g))
    y_min = min(float(g.min()) for g in groups if len(g))
    height = max((y_max - y_min) * 0.06, 0.05)
    ax.plot([1, 1, 2, 2], [y_max + height, y_max + 2 * height, y_max + 2 * height, y_max + height],
            color="black", lw=0.6, clip_on=False)
    label = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3g}"
    ax.text(1.5, y_max + 2.2 * height, label, ha="center", va="bottom", fontsize=6, fontstyle="italic")
    ax.set_ylim(top=y_max + 4 * height)
    return []


# ----------------------------------------------------------------------------
# Multi-group hypothesis tests
# ----------------------------------------------------------------------------

def _coerce_group_arrays(groups: Iterable[Any]) -> list[np.ndarray]:
    arrays: list[np.ndarray] = []
    for g in groups:
        arr = np.asarray(pd.to_numeric(pd.Series(g), errors="coerce").dropna(), dtype=float)
        if arr.size:
            arrays.append(arr)
    return arrays


def kruskal_wallis(*groups: Iterable[float]) -> TestResult:
    """Run a Kruskal-Wallis H test on >=2 numeric groups.

    Non-parametric multi-group rank-based extension of the Mann-Whitney U.
    Use when group distributions are non-normal or variances differ.
    """
    arrays = _coerce_group_arrays(groups)
    notes: list[str] = []
    if len(arrays) < 2:
        return TestResult(
            statistic=float("nan"),
            pvalue=float("nan"),
            method="kruskal_wallis",
            n_groups=len(arrays),
            n_total=int(sum(len(a) for a in arrays)),
            notes=("insufficient_groups",),
        )
    if any(len(a) < 2 for a in arrays):
        notes.append("group_with_fewer_than_two_observations")
    try:
        from scipy import stats  # type: ignore[import-untyped]
    except Exception:
        return TestResult(
            statistic=float("nan"),
            pvalue=float("nan"),
            method="kruskal_wallis",
            n_groups=len(arrays),
            n_total=int(sum(len(a) for a in arrays)),
            notes=("scipy_unavailable",),
        )
    h, p = stats.kruskal(*arrays)
    return TestResult(
        statistic=float(h),
        pvalue=float(p),
        method="kruskal_wallis",
        n_groups=len(arrays),
        n_total=int(sum(len(a) for a in arrays)),
        notes=tuple(notes),
    )


def one_way_anova(*groups: Iterable[float]) -> TestResult:
    """Run a one-way ANOVA F-test on >=2 numeric groups.

    Parametric multi-group test. Assumes approximate normality + equal
    variances; use Kruskal-Wallis when those assumptions fail.
    """
    arrays = _coerce_group_arrays(groups)
    notes: list[str] = []
    if len(arrays) < 2:
        return TestResult(
            statistic=float("nan"),
            pvalue=float("nan"),
            method="one_way_anova",
            n_groups=len(arrays),
            n_total=int(sum(len(a) for a in arrays)),
            notes=("insufficient_groups",),
        )
    if any(len(a) < 2 for a in arrays):
        notes.append("group_with_fewer_than_two_observations")
    try:
        from scipy import stats  # type: ignore[import-untyped]
    except Exception:
        return TestResult(
            statistic=float("nan"),
            pvalue=float("nan"),
            method="one_way_anova",
            n_groups=len(arrays),
            n_total=int(sum(len(a) for a in arrays)),
            notes=("scipy_unavailable",),
        )
    f_stat, p = stats.f_oneway(*arrays)
    return TestResult(
        statistic=float(f_stat),
        pvalue=float(p),
        method="one_way_anova",
        n_groups=len(arrays),
        n_total=int(sum(len(a) for a in arrays)),
        notes=tuple(notes),
    )


def tukey_hsd(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    *,
    alpha: float = 0.05,
) -> list[TukeyResult]:
    """Tukey HSD post-hoc pairwise comparison after a significant one-way ANOVA.

    Uses scipy's ``stats.tukey_hsd`` (added in scipy 1.8). Returns a list of
    :class:`TukeyResult` rows for every unique unordered pair of groups.
    """
    if group_col not in df.columns or value_col not in df.columns:
        return []
    groups: dict[str, np.ndarray] = {}
    for name, part in df.groupby(group_col, sort=True):
        arr = np.asarray(pd.to_numeric(part[value_col], errors="coerce").dropna(), dtype=float)
        if arr.size >= 2:
            groups[str(name)] = arr
    if len(groups) < 2:
        return []
    try:
        from scipy import stats  # type: ignore[import-untyped]
    except Exception:
        return []
    labels = list(groups.keys())
    arrays = [groups[k] for k in labels]
    try:
        result = stats.tukey_hsd(*arrays)
    except Exception:
        return []
    out: list[TukeyResult] = []
    pvalues = result.pvalue  # 2D ndarray (n_groups x n_groups)
    means = [float(arr.mean()) for arr in arrays]
    n = len(labels)
    for i in range(n):
        for j in range(i + 1, n):
            p = float(pvalues[i, j])
            mean_diff = means[i] - means[j]
            out.append(
                TukeyResult(
                    group_a=labels[i],
                    group_b=labels[j],
                    mean_diff=mean_diff,
                    pvalue=p,
                    reject=p < alpha,
                )
            )
    return out


# ----------------------------------------------------------------------------
# Multiple comparison correction
# ----------------------------------------------------------------------------

def fdr_bh(pvalues: Iterable[float], *, alpha: float = 0.05) -> dict[str, Any]:
    """Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Returns a dict with:

    - ``adjusted`` : list[float] - BH-adjusted q-values aligned to input order
    - ``reject``   : list[bool]  - True where the adjusted p<=alpha
    - ``alpha``    : float       - the alpha threshold used
    - ``n``        : int         - number of input p-values
    """
    p = np.asarray(list(pvalues), dtype=float)
    if p.size == 0:
        return {"adjusted": [], "reject": [], "alpha": alpha, "n": 0}
    n = p.size
    # Order p-values ascending; remember original positions so we can unsort.
    order = np.argsort(p, kind="mergesort")
    ranked = p[order]
    # BH-adjusted = min over k>=i of n/k * p_(k); enforce monotone decreasing
    # going from largest rank back to smallest, then clip to [0, 1].
    adjusted_sorted = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        candidate = ranked[i] * n / rank
        prev = min(prev, candidate)
        adjusted_sorted[i] = prev
    adjusted = np.empty(n, dtype=float)
    adjusted[order] = np.clip(adjusted_sorted, 0.0, 1.0)
    reject = adjusted <= alpha
    return {
        "adjusted": adjusted.tolist(),
        "reject": reject.tolist(),
        "alpha": float(alpha),
        "n": int(n),
    }


# ----------------------------------------------------------------------------
# Test recommender
# ----------------------------------------------------------------------------

def recommend_test(
    df: pd.DataFrame,
    group_col: Optional[str],
    value_col: Optional[str],
    *,
    paired: bool = False,
) -> dict[str, Any]:
    """Recommend a hypothesis test family from data shape.

    Returns a dict with:

    - ``test`` : suggested test name
    - ``n_groups`` : detected group count
    - ``rationale`` : short string explaining the choice
    - ``post_hoc`` : optional name of the post-hoc test (Tukey HSD when ANOVA is suggested)
    """
    if not group_col or not value_col or group_col not in df.columns or value_col not in df.columns:
        return {"test": "none", "n_groups": 0, "rationale": "missing_columns", "post_hoc": None}
    groups = [
        pd.to_numeric(part[value_col], errors="coerce").dropna()
        for _, part in df.groupby(group_col, sort=False)
    ]
    n_groups = len(groups)
    if n_groups < 2:
        return {"test": "descriptive_only", "n_groups": n_groups, "rationale": "single_group", "post_hoc": None}
    if any(len(g) < 2 for g in groups):
        return {
            "test": "descriptive_only",
            "n_groups": n_groups,
            "rationale": "group_with_fewer_than_two_observations",
            "post_hoc": None,
        }
    # Two-group rule: Mann-Whitney (paired -> Wilcoxon)
    if n_groups == 2:
        return {
            "test": "wilcoxon_signed_rank" if paired else "mann_whitney_u",
            "n_groups": 2,
            "rationale": "two_group_paired" if paired else "two_group_unpaired",
            "post_hoc": None,
        }
    # Multi-group rule: try ANOVA assumptions, fall back to Kruskal-Wallis
    try:
        from scipy import stats  # type: ignore[import-untyped]
        # Shapiro per group (only meaningful for n in [3, 5000]); failure -> non-parametric
        normal_ok = True
        for g in groups:
            if len(g) < 3 or len(g) > 5000:
                normal_ok = False
                break
            _, p_norm = stats.shapiro(np.asarray(g, dtype=float))
            if p_norm < 0.05:
                normal_ok = False
                break
        if normal_ok:
            # Levene equal-variance test
            _, p_levene = stats.levene(*[np.asarray(g, dtype=float) for g in groups])
            if p_levene >= 0.05:
                return {
                    "test": "one_way_anova",
                    "n_groups": n_groups,
                    "rationale": "multi_group_normal_equal_variance",
                    "post_hoc": "tukey_hsd",
                }
    except Exception:
        pass
    return {
        "test": "kruskal_wallis",
        "n_groups": n_groups,
        "rationale": "multi_group_non_normal_or_unequal_variance",
        "post_hoc": None,
    }
