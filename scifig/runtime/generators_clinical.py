"""Clinical / survival chart generators (km/forest/swimmer/...).

Stage-2 refactor: function bodies are byte-identical to the pre-refactor
runtime generator_sources map. Consumed via _load_generator_source_map()
source-concatenation (not standalone import); shared role/color helpers
live in generators_distribution, classifier-board helpers in generators_ml.
"""


from math import pi as _pi
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colors import TwoSlopeNorm
from matplotlib.gridspec import GridSpecFromSubplotSpec
from matplotlib.patches import Ellipse
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.optimize import curve_fit
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import gaussian_kde
from scipy.stats import norm
from sklearn.linear_model import LinearRegression
from sklearn.metrics import precision_recall_curve, average_precision_score
from sklearn.metrics import roc_curve, auc
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from statsmodels.nonparametric.smoothers_lowess import lowess
import math as _math
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
import squarify
import textwrap
import warnings


def gen_caterpillar_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Caterpillar plot: ranked effects with confidence intervals, sorted by effect size.

    Operational layer (post-Phase A1): when template_mining_helpers is embedded,
    this generator delegates the forest discipline (markers + asymmetric error bars +
    reference line + per-row estimate(CI) annotation) to add_forest_panel using
    linear scale and reference_line=0.0 (no-effect anchor).
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    estimate_col = roles.get("estimate") or roles.get("value")
    ci_low_col = roles.get("ci_low")
    ci_high_col = roles.get("ci_high")

    if label_col is None or estimate_col is None:
        raise ValueError("caterpillar_plot requires 'label' and 'estimate' in semanticRoles")

    sort_col = roles.get("sort") or estimate_col
    df_sorted = df.sort_values(sort_col).reset_index(drop=True)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df_sorted) * 8) * (1 / 25.4)),
                           constrained_layout=True)

    estimates = df_sorted[estimate_col].astype(float).values
    if ci_low_col and ci_high_col:
        ci_low = df_sorted[ci_low_col].astype(float).values
        ci_high = df_sorted[ci_high_col].astype(float).values
    else:
        se_col = roles.get("se")
        se = df_sorted[se_col].astype(float).values if se_col and se_col in df_sorted.columns else estimates * 0.1
        ci_low = estimates - 1.96 * se
        ci_high = estimates + 1.96 * se
    labels = df_sorted[label_col].astype(str).tolist()

    canonical_forest = globals().get("add_forest_panel")
    if canonical_forest is not None:
        try:
            canonical_forest(ax, estimates, ci_low, ci_high, labels,
                             color="#0072B2",
                             reference_line=0.0,
                             log_scale=False,
                             show_yticklabels=True,
                             annotation_format="{hr:.3g} ({lo:.3g}, {hi:.3g})",
                             title=None)
            ax.set_xlabel("Effect size (95% CI)")
            if standalone:
                apply_chart_polish(ax, "caterpillar_plot")
            return ax
        except Exception:
            pass  # Fall through to inline implementation

    # Inline fallback when add_forest_panel is not embedded
    y_pos = np.arange(len(df_sorted))
    ax.errorbar(estimates, y_pos,
                xerr=[estimates - ci_low, ci_high - estimates],
                fmt="o", color="#0072B2", markersize=4, capsize=3,
                elinewidth=0.6, capthick=0.6, linewidth=0.6)

    ax.axvline(0, color="#999999", lw=0.5, ls="--", alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=5)
    ax.set_xlabel("Effect size (95% CI)")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "caterpillar_plot")
    return ax


def gen_ci_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Confidence interval plot for multiple estimates.

    Displays horizontal CI bars for each estimate row.  Expects columns for
    estimate (point value), lower CI bound, and upper CI bound.  Optionally
    accepts a label column for y-axis tick names.  A vertical reference line
    at x = 0 is drawn when the interval spans zero.

    Operational layer (post-Phase A1): when template_mining_helpers is embedded,
    this generator delegates to add_forest_panel with linear scale + reference_line=0
    so each CI panel matches the corpus-anchored forest discipline (per-row
    estimate(CI) annotation column on the right edge).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    est_col = roles.get("estimate") or roles.get("value") or roles.get("y")
    lower_col = roles.get("ci_lower") or roles.get("lower")
    upper_col = roles.get("ci_upper") or roles.get("upper")
    label_col = roles.get("label") or roles.get("group") or roles.get("x")

    if est_col is None or lower_col is None or upper_col is None:
        raise ValueError("ci_plot requires 'estimate', 'ci_lower', and 'ci_upper' in semanticRoles")

    n = len(df)
    fig_height = max(60, 12 * n + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    estimates = df[est_col].astype(float).values
    lowers = df[lower_col].astype(float).values
    uppers = df[upper_col].astype(float).values
    if label_col and label_col in df.columns:
        labels = df[label_col].astype(str).tolist()
    else:
        labels = [str(i + 1) for i in range(n)]
    color = palette.get("categorical", ["#0072B2"])[0]

    canonical_forest = globals().get("add_forest_panel")
    if canonical_forest is not None:
        try:
            canonical_forest(ax, estimates, lowers, uppers, labels,
                             color=color,
                             reference_line=0.0,
                             log_scale=False,
                             show_yticklabels=True,
                             annotation_format="{hr:.3g} ({lo:.3g}, {hi:.3g})",
                             title=None)
            ax.set_xlabel("Estimate (95 % CI)")
            if standalone:
                apply_chart_polish(ax, "ci_plot")
            return ax
        except Exception:
            pass  # Fall through to inline implementation

    # Inline fallback when add_forest_panel is not embedded
    y_pos = np.arange(n)
    for i in range(n):
        ax.plot([lowers[i], uppers[i]], [i, i], color=color, linewidth=0.8,
                solid_capstyle="round", zorder=2)
        ax.plot(estimates[i], i, "o", color=color, markersize=4, zorder=3)

    # Reference line at zero if interval spans it
    if lowers.min() < 0 < uppers.max():
        ax.axvline(0, color="black", linewidth=0.5, linestyle="--", zorder=1)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=5)
    ax.set_xlabel("Estimate (95 % CI)")
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if standalone:
        apply_chart_polish(ax, "ci_plot")
    return ax


def gen_dose_response(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Dose-response curve with optional EC50/IC50 annotation."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 62 * (1 / 25.4)), constrained_layout=True)

    # Apply L0 floor: light dashed grid + despine BEFORE drawing scatter so grid sits at zorder=0
    canonical_floor = globals().get("apply_scatter_regression_floor")
    if canonical_floor is not None:
        try:
            canonical_floor(ax, grid_axis="both")
        except Exception:
            ax.grid(True, linestyle="--", color="#E0E0E0", linewidth=0.6, alpha=0.6, zorder=0)
            ax.set_axisbelow(True)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
    else:
        ax.grid(True, linestyle="--", color="#E0E0E0", linewidth=0.6, alpha=0.6, zorder=0)
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    roles = dataProfile.get("semanticRoles", {})
    dose_col = roles.get("dose")
    response_col = roles.get("response") or roles.get("value")
    group_col = roles.get("group")

    if not dose_col or not response_col:
        raise ValueError("dose_response requires 'dose' and 'response' in semanticRoles")

    if group_col and group_col in df.columns:
        groups = df[group_col].unique().tolist()
        color_map = _extract_colors(palette, groups)
        fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])
        for i, grp in enumerate(groups):
            sub = df[df[group_col] == grp].sort_values(dose_col)
            color = color_map.get(grp, fallback_colors[i % len(fallback_colors)])
            ax.scatter(sub[dose_col], sub[response_col], s=10, color=color, label=display_label(grp, col_map),
                      edgecolor="white", lw=0.3, zorder=3)
            # Fit 4PL if scipy available
            try:
                from scipy.optimize import curve_fit
                def four_pl(x, bottom, top, ec50, hill):
                    return bottom + (top - bottom) / (1 + (ec50 / x) ** hill)
                popt, _ = curve_fit(four_pl, sub[dose_col].values, sub[response_col].values,
                                   p0=[sub[response_col].min(), sub[response_col].max(),
                                       sub[dose_col].median(), 1], maxfev=5000)
                x_fit = np.logspace(np.log10(sub[dose_col].min()), np.log10(sub[dose_col].max()), 100)
                ax.plot(x_fit, four_pl(x_fit, *popt), color=color, lw=0.8, alpha=0.8)
            except Exception:
                pass
        ax.legend(fontsize=4.5, markerscale=2, frameon=False)
    else:
        sub = df.sort_values(dose_col)
        ax.scatter(sub[dose_col], sub[response_col], s=10, color="#1F4E79", edgecolor="white", lw=0.3)

    ax.set_xlabel(display_label(dose_col, col_map))
    ax.set_ylabel(display_label(response_col, col_map))
    ax.set_xscale("log")
    if standalone:
        apply_chart_polish(ax, "dose_response")
    return ax


def gen_forest(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Forest plot for effect sizes with confidence intervals.

    Anchor cases (template corpus):
      - Python科研绘图复现_绘制多面板分组森林图展示生存分析风险比(HR)_1777453520
      - 期刊配图复现_Python绘制机器学习预测-实验对比图 (clinical forest panels)

    Required visual grammar (from knowledge/modules/02-zorder-recipes.md § forest +
    template_mining_helpers.add_forest_panel):
      1. Dashed reference line at null effect (HR=1, OR=1, β=0)
      2. Log-scale x axis when effect_kind in ('hr', 'or', 'rr')
      3. Per-row HR (CI) annotation column at right edge using axes-fraction
      4. Marker size large enough for hero panels (markersize=9)
      5. White marker edge for separation (markeredgecolor='white', mew=0.6)
      6. Light dotted x grid (zorder=0)

    Defers to template_mining_helpers.add_forest_panel when reachable; falls
    back to inline drawing if helpers were not embedded.
    """
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    columns_lower = {str(c).lower(): c for c in df.columns}

    def _role_or_column(*names):
        for name in names:
            value = roles.get(name)
            if value in df.columns:
                return value
            if isinstance(value, str) and value.lower() in columns_lower:
                return columns_lower[value.lower()]
            if name in columns_lower:
                return columns_lower[name]
        return None

    label_col = _role_or_column("label", "term", "feature", "group")
    estimate_col = _role_or_column("estimate", "value", "hr", "ratio", "hazard_ratio")
    ci_low_col = _role_or_column("ci_low", "lower", "low", "lcl")
    ci_high_col = _role_or_column("ci_high", "upper", "high", "ucl")
    se_col = _role_or_column("se", "stderr", "std_error")
    panel_col = _role_or_column("panel", "facet", "disease", "outcome", "cohort", "condition")
    model_col = _role_or_column("model", "series", "adjustment", "model_name")

    visual_plan = chartPlan.get("visualContentPlan")
    if not isinstance(visual_plan, dict):
        visual_plan = {}
        chartPlan["visualContentPlan"] = visual_plan
    template_motifs = {
        str(m).lower()
        for m in (visual_plan.get("templateMotifs") or chartPlan.get("templateMotifs") or [])
    }
    patterns = {str(p).lower() for p in dataProfile.get("specialPatterns", [])}
    forest_tokens = " ".join(
        str(v).lower()
        for v in [
            panel_col or "",
            model_col or "",
            estimate_col or "",
            dataProfile.get("domain", ""),
            *template_motifs,
            *patterns,
        ]
    )
    use_faceted_hr_forest = (
        standalone
        and bool(panel_col) and panel_col in df.columns
        and bool(model_col) and model_col in df.columns
        and bool(estimate_col) and estimate_col in df.columns
        and bool(ci_low_col) and ci_low_col in df.columns
        and bool(ci_high_col) and ci_high_col in df.columns
        and panel_col != model_col
        and (
            "faceted_hr_forest" in template_motifs
            or "hr_forest" in patterns
            or ("forest" in forest_tokens and ("hr" in forest_tokens or "hazard" in forest_tokens))
        )
    )

    if use_faceted_hr_forest:
        plot_df = df[[panel_col, model_col, estimate_col, ci_low_col, ci_high_col]].copy()
        for col in (estimate_col, ci_low_col, ci_high_col):
            plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")
        plot_df = plot_df.dropna(subset=[panel_col, model_col, estimate_col, ci_low_col, ci_high_col])
        plot_df = plot_df[(plot_df[estimate_col] > 0) & (plot_df[ci_low_col] > 0) & (plot_df[ci_high_col] > 0)]
        if plot_df.empty:
            raise ValueError("faceted_hr_forest requires positive panel/model/hr/lower/upper rows")
        panels = plot_df[panel_col].dropna().astype(str).unique().tolist()[:4]
        models = plot_df[model_col].dropna().astype(str).unique().tolist()
        style_fn = globals().get("resolve_forest_model_style_map")
        model_styles = (
            style_fn(models, variant="nature_hr_adjustment")
            if style_fn is not None else {}
        )
        ncols = max(1, len(panels))
        fig, axes = plt.subplots(
            1, ncols, figsize=(3.5 * ncols, 4.0),
            sharey=True, constrained_layout=False,
        )
        axes = np.atleast_1d(axes).tolist()
        y_positions = np.arange(len(models))[::-1]
        x_min = max(0.01, float(plot_df[ci_low_col].min()) * 0.90)
        x_max = float(plot_df[ci_high_col].max()) * 1.08
        handles_by_label = {}
        for ax_idx, (sub_ax, panel_value) in enumerate(zip(axes, panels)):
            panel_df = plot_df[plot_df[panel_col].astype(str) == str(panel_value)]
            for model_idx, model_name in enumerate(models):
                rows = panel_df[panel_df[model_col].astype(str) == str(model_name)]
                if rows.empty:
                    continue
                row = rows.iloc[0]
                hr = float(row[estimate_col])
                lo = float(row[ci_low_col])
                hi = float(row[ci_high_col])
                if hi < lo:
                    lo, hi = hi, lo
                style = dict(model_styles.get(str(model_name), {}))
                color = style.get("color", "#8DA0CB")
                handle = sub_ax.errorbar(
                    x=hr, y=y_positions[model_idx],
                    xerr=[[max(hr - lo, 0.0)], [max(hi - hr, 0.0)]],
                    fmt=style.get("marker", "o"),
                    color=color, ecolor=color,
                    elinewidth=style.get("elinewidth", 2.0),
                    capsize=style.get("capsize", 4),
                    markersize=style.get("markersize", 8),
                    markerfacecolor=style.get("markerfacecolor", color),
                    markeredgecolor=style.get("markeredgecolor", "white"),
                    markeredgewidth=style.get("markeredgewidth", 0.6),
                    zorder=style.get("zorder", 10),
                )
                handles_by_label.setdefault(str(model_name), handle.lines[0])
            sub_ax.axvline(x=1.0, color="#777777", linestyle="--", linewidth=1.0, zorder=0)
            sub_ax.set_title(str(display_label(panel_value, col_map) if col_map else panel_value),
                             fontsize=8.5, fontweight="bold", pad=10)
            sub_ax.set_xlim(x_min, x_max)
            sub_ax.set_yticks(y_positions)
            if ax_idx == 0:
                sub_ax.set_yticklabels([str(m) for m in models], fontsize=7)
            else:
                sub_ax.tick_params(labelleft=False)
            sub_ax.tick_params(axis="y", length=0)
            sub_ax.tick_params(axis="x", labelsize=7, length=3)
            sub_ax.spines["top"].set_visible(False)
            sub_ax.spines["right"].set_visible(False)
            sub_ax.set_xlabel("Hazard ratio (95% CI)", fontsize=7.5)
        if handles_by_label:
            legend_labels = [m for m in models if str(m) in handles_by_label]
            fig.legend(
                [handles_by_label[str(m)] for m in legend_labels],
                [str(m) for m in legend_labels],
                loc="upper center", bbox_to_anchor=(0.5, 0.98),
                ncol=min(3, len(legend_labels)), frameon=False, fontsize=8,
                handlelength=1.8,
            )
        fig.subplots_adjust(wspace=0.10, top=0.78, left=0.09, right=0.98, bottom=0.18)
        planned_motifs = visual_plan.setdefault("templateMotifs", [])
        if "faceted_hr_forest" not in planned_motifs:
            planned_motifs.append("faceted_hr_forest")
        globals().get("_record_template_motif", lambda *args, **kwargs: None)(
            visual_plan, "faceted_hr_forest"
        )
        count_fn = globals().get("_visual_count", lambda *args, **kwargs: None)
        for _ in axes:
            count_fn(visual_plan, "referenceLineCount")
        return axes[0]

    if label_col is None or estimate_col is None:
        raise ValueError("forest requires 'label' and 'estimate' in semanticRoles")

    estimates = df[estimate_col].astype(float).values
    if ci_low_col and ci_high_col and ci_low_col in df.columns and ci_high_col in df.columns:
        ci_low = df[ci_low_col].astype(float).values
        ci_high = df[ci_high_col].astype(float).values
    elif se_col and se_col in df.columns:
        se = df[se_col].astype(float).values
        ci_low = estimates - 1.96 * se
        ci_high = estimates + 1.96 * se
    else:
        se = np.maximum(np.abs(estimates) * 0.1, 1e-9)
        ci_low = estimates - 1.96 * se
        ci_high = estimates + 1.96 * se
    labels = [display_label(v, col_map) if col_map else str(v)
              for v in df[label_col].values]

    # ─── Detect effect kind: HR/OR/RR (positive only, log-scale + ref=1)
    # vs. β / mean diff (signed, linear scale + ref=0).
    effect_kind = (chartPlan.get("forestEffectKind")
                   or dataProfile.get("forestEffectKind") or "").lower()
    if not effect_kind:
        col_lower = str(estimate_col).lower()
        if any(token in col_lower for token in ("hr", "ratio", "rr", "or", "odds", "hazard")):
            effect_kind = "hr"
        elif np.all(estimates > 0) and np.all(ci_low > 0):
            effect_kind = "hr"
        else:
            effect_kind = "beta"
    log_scale = (effect_kind == "hr")
    reference_line = 1.0 if log_scale else 0.0

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4),
                                         max(40, len(df) * 9) * (1 / 25.4)),
                               constrained_layout=False)

    # Resolve color from palette plan first (chart-aware -> npg_4 default)
    color = (palette.get("categoryMap", {}).get("default")
             or (palette.get("categorical") or ["#3C5488"])[0])

    # ─── Defer to template_mining_helpers when reachable (Phase A1) ────────
    add_forest_panel = globals().get("add_forest_panel")
    if add_forest_panel is not None:
        try:
            annotation_format = ("{hr:.2f} ({lo:.2f}-{hi:.2f})" if log_scale
                                  else "{hr:+.2f} ({lo:+.2f},{hi:+.2f})")
            add_forest_panel(
                ax, estimates, ci_low, ci_high, labels,
                color=color,
                reference_line=reference_line,
                log_scale=log_scale,
                show_yticklabels=True,
                annotation_format=annotation_format,
                title=None,
            )
            ax.set_xlabel(("Hazard ratio (95% CI)" if effect_kind == "hr"
                            else "Effect size (95% CI)"))
            if standalone:
                fig = ax.figure
                try:
                    if hasattr(fig, "set_layout_engine"):
                        fig.set_layout_engine(None)
                    else:
                        fig.set_constrained_layout(False)
                except Exception:
                    pass
                fig.subplots_adjust(left=0.30, right=0.92, top=0.94, bottom=0.20)
                apply_chart_polish(ax, "forest")
            return ax
        except Exception:
            pass  # fall through to inline path

    # ─── Inline fallback (when helpers were not embedded) ─────────────────
    y_pos = np.arange(len(df))
    ax.xaxis.grid(True, linestyle=":", color="#E0E0E0", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.axvline(reference_line, color="#888888", lw=1.0, ls="--", zorder=1)
    xerr = [estimates - ci_low, ci_high - estimates]
    ax.errorbar(estimates, y_pos, xerr=xerr, fmt="o",
                color=color, ecolor=color,
                elinewidth=2, capsize=4, markersize=9,
                markeredgecolor="white", markeredgewidth=0.6, zorder=10)
    ann_fmt = ("{hr:.2f} ({lo:.2f}-{hi:.2f})" if log_scale
                else "{hr:+.2f} ({lo:+.2f},{hi:+.2f})")
    for i, (hr, lo, hi) in enumerate(zip(estimates, ci_low, ci_high)):
        ax.text(0.99, y_pos[i], ann_fmt.format(hr=hr, lo=lo, hi=hi),
                transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=6, color="#222",
                family="monospace", zorder=15,
                bbox=dict(boxstyle="round,pad=0.15", fc="white",
                          ec="none", alpha=0.85))
    if log_scale:
        ax.set_xscale("log")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6)
    ax.invert_yaxis()
    ax.set_xlabel("Hazard ratio (95% CI)" if effect_kind == "hr"
                   else "Effect size (95% CI)")
    if standalone:
        fig = ax.figure
        try:
            if hasattr(fig, "set_layout_engine"):
                fig.set_layout_engine(None)
            else:
                fig.set_constrained_layout(False)
        except Exception:
            pass
        fig.subplots_adjust(left=0.30, right=0.92, top=0.94, bottom=0.20)
        apply_chart_polish(ax, "forest")
    return ax


def gen_km(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Kaplan-Meier survival curve with optional at-risk table."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    time_col = roles.get("time") or roles.get("duration")
    event_col = roles.get("event") or roles.get("status")
    group_col = roles.get("group")

    if time_col is None or event_col is None:
        raise ValueError("km requires 'time' and 'event' in semanticRoles")

    color_map = _extract_colors(palette, df[group_col].unique() if group_col else [None])
    fallback_colors = palette.get("categorical", ["#000000", "#E69F00", "#56B4E9", "#009E73"])

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    def _km_curve(times, events):
        """Compute KM survival estimate."""
        unique_times = np.sort(times[events == 1].unique())
        n_at_risk = len(times)
        surv = [1.0]
        t_points = [0]
        for t in unique_times:
            d = ((times == t) & (events == 1)).sum()
            n = (times >= t).sum()
            if n > 0:
                surv.append(surv[-1] * (1 - d / n))
                t_points.append(t)
        return np.array(t_points), np.array(surv)

    if group_col:
        for i, (name, grp) in enumerate(df.groupby(group_col)):
            col = color_map.get(name, fallback_colors[i % len(fallback_colors)])
            t_km, s_km = _km_curve(grp[time_col], grp[event_col])
            ax.step(t_km, s_km, where="post", color=col, lw=1, label=str(name))
    else:
        t_km, s_km = _km_curve(df[time_col], df[event_col])
        ax.step(t_km, s_km, where="post", color="#000000", lw=1)

    ax.set_xlabel("Time")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(0, 1.05)
    if group_col:
        ax.legend(frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "km")
    return ax


def gen_nomogram(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified nomogram: linear scale with point markers for prediction models."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    score_col = roles.get("score") or roles.get("value")

    if label_col is None or score_col is None:
        raise ValueError("nomogram requires 'label' and 'score' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), max(40, len(df) * 14) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = np.arange(len(df))
    labels = df[label_col].values
    scores = df[score_col].values

    for i in range(len(df)):
        # Draw horizontal scale line with tick marks
        ax.plot([0, 100], [y_pos[i], y_pos[i]], color="#CCCCCC", lw=1)
        for tick in np.linspace(0, 100, 6):
            ax.plot([tick, tick], [y_pos[i] - 0.2, y_pos[i] + 0.2], color="#999999", lw=0.5)
        # Mark the score value on the scale
        if np.isscalar(scores[i]) and 0 <= scores[i] <= 100:
            ax.plot(scores[i], y_pos[i], "o", color="#D55E00", markersize=6, zorder=5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_xlim(-5, 105)
    ax.set_xlabel("Points")
    ax.set_ylim(-0.5, len(df) - 0.5)
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "nomogram")
    return ax


def gen_risk_ratio_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Risk ratio forest plot (HR / OR with 95 % CI).

    Horizontal forest plot showing hazard ratios or odds ratios with
    confidence intervals for each subgroup.  A vertical reference line at 1
    (no effect) is drawn.  Optionally annotates p-values on the right margin.

    Operational layer (post-Phase A1): when template_mining_helpers is embedded,
    this generator delegates to add_forest_panel for log-scale + reference_line=1
    + per-row HR(CI) annotation column. The p-value annotation column is added
    on top of the canonical forest discipline.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group") or roles.get("x")
    est_col = roles.get("estimate") or roles.get("value") or roles.get("y")
    lo_col = roles.get("ci_lower") or roles.get("lower")
    hi_col = roles.get("ci_upper") or roles.get("upper")
    p_col = roles.get("p_value") or roles.get("pvalue")

    if est_col is None or lo_col is None or hi_col is None:
        raise ValueError("risk_ratio_plot requires 'estimate', 'ci_lower', 'ci_upper' in semanticRoles")

    n = len(df)
    fig_height = max(60, 12 * n + 24) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    estimates = df[est_col].astype(float).values
    lowers = df[lo_col].astype(float).values
    uppers = df[hi_col].astype(float).values
    if label_col and label_col in df.columns:
        labels = df[label_col].astype(str).tolist()
    else:
        labels = [str(i + 1) for i in range(n)]
    color = palette.get("categorical", ["#0072B2"])[0]

    used_canonical = False
    canonical_forest = globals().get("add_forest_panel")
    if canonical_forest is not None:
        try:
            canonical_forest(ax, estimates, lowers, uppers, labels,
                             color=color,
                             reference_line=1.0,
                             log_scale=True,
                             show_yticklabels=True,
                             annotation_format="{hr:.2f} [{lo:.2f}, {hi:.2f}]",
                             title=None)
            used_canonical = True
        except Exception:
            used_canonical = False

    if not used_canonical:
        # Inline fallback when add_forest_panel is not embedded
        y_pos_inline = np.arange(n)
        for i in range(n):
            ax.plot([lowers[i], uppers[i]], [i, i], color=color, linewidth=0.8,
                    solid_capstyle="round", zorder=2)
            ax.plot(estimates[i], i, "D", color=color, markersize=4, zorder=3)

        ax.axvline(1, color="black", linewidth=0.6, linestyle="--", zorder=1)
        ax.set_yticks(y_pos_inline)
        ax.set_yticklabels(labels, fontsize=5)

        # Per-row HR(CI) annotation column at right margin
        x_max = ax.get_xlim()[1]
        for i in range(n):
            ci_text = f"{estimates[i]:.2f} [{lowers[i]:.2f}, {uppers[i]:.2f}]"
            ax.text(x_max * 1.05, i, ci_text, fontsize=4, va="center", ha="left",
                    color="#333", transform=ax.get_yaxis_transform())

    # P-value annotation column (additional to forest discipline)
    if p_col and p_col in df.columns:
        x_max = ax.get_xlim()[1]
        p_x = x_max * 1.45
        ax.text(p_x, n + 0.3, "p", fontsize=5, fontstyle="italic", fontweight="bold",
                va="bottom", ha="center", transform=ax.get_yaxis_transform())
        for i, (_, row) in enumerate(df.iterrows()):
            pval = row[p_col]
            p_text = "<0.001" if pval < 0.001 else f"{pval:.3g}"
            ax.text(p_x, i, p_text, fontsize=4, va="center", ha="center",
                    transform=ax.get_yaxis_transform())

    ratio_label = chartPlan.get("ratioLabel", "Risk ratio")
    ax.set_xlabel(f"{ratio_label} (95 % CI)")
    if not used_canonical:
        ax.invert_yaxis()
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    if standalone:
        apply_chart_polish(ax, "risk_ratio_plot")
    return ax


def gen_swimmer_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Swimmer plot: horizontal bars for treatment duration with event markers.

    Each row is a patient.  A horizontal bar spans from start to end (e.g.
    treatment start/stop).  Optional marker columns encode events such as
    response, progression, or adverse events with distinct shapes/colors.

    Expects in semanticRoles: id (patient label), start, end, and optionally
    group (arm/cohort).  Event markers are read from columns whose names are
    listed in chartPlan.get("eventColumns", []).
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    id_col = roles.get("id") or roles.get("label") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end") or roles.get("y") or roles.get("value")
    arm_col = roles.get("arm") or roles.get("cohort")

    if id_col is None or start_col is None or end_col is None:
        raise ValueError("swimmer_plot requires 'id', 'start', and 'end' in semanticRoles")

    df = df.sort_values(start_col).reset_index(drop=True)
    n = len(df)
    fig_height = max(60, 10 * n + 20) * (1 / 25.4)
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), fig_height),
                           constrained_layout=True)

    arms = df[arm_col].unique().tolist() if arm_col and arm_col in df.columns else [None]
    arm_colors = _extract_colors(palette, [a for a in arms if a is not None])

    for i, (_, row) in enumerate(df.iterrows()):
        arm = row[arm_col] if arm_col and arm_col in df.columns else None
        color = arm_colors.get(arm, palette["categorical"][0]) if arm else palette["categorical"][0]
        ax.barh(i, row[end_col] - row[start_col], left=row[start_col],
                height=0.6, color=color, edgecolor="white", linewidth=0.4, zorder=2)

    event_cols = chartPlan.get("eventColumns", [])
    event_markers = ["o", "s", "^", "D", "P", "X"]
    for j, ecol in enumerate(event_cols):
        if ecol not in df.columns:
            continue
        marker = event_markers[j % len(event_markers)]
        for i, (_, row) in enumerate(df.iterrows()):
            val = row[ecol]
            if pd.notna(val) and val != 0:
                xpos = val if isinstance(val, (int, float)) else row[end_col]
                ax.scatter(xpos, i, marker=marker, s=18,
                           color=palette["categorical"][(j + 1) % len(palette["categorical"])],
                           edgecolor="white", linewidth=0.3, zorder=3)

    ax.set_yticks(range(n))
    ax.set_yticklabels(df[id_col].astype(str).tolist(), fontsize=5)
    ax.set_xlabel("Time")
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    if event_cols:
        handles = []
        for j, ecol in enumerate(event_cols):
            marker = event_markers[j % len(event_markers)]
            handles.append(plt.Line2D([0], [0], marker=marker, color="w",
                           markerfacecolor=palette["categorical"][(j + 1) % len(palette["categorical"])],
                           markersize=4, label=ecol))
        ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "swimmer_plot")
    return ax


def gen_tornado_chart(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Tornado diagram for sensitivity analysis: horizontal bars showing variable impact."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    label_col = roles.get("label") or roles.get("group")
    low_col = roles.get("low") or roles.get("ci_low")
    high_col = roles.get("high") or roles.get("ci_high")
    base_col = roles.get("base") or roles.get("value")

    if label_col is None or low_col is None or high_col is None:
        raise ValueError("tornado_chart requires 'label', 'low', and 'high' in semanticRoles")

    # Sort by bar width (largest impact first)
    df_sorted = df.copy()
    df_sorted["_width"] = (df_sorted[high_col] - df_sorted[low_col]).abs()
    df_sorted = df_sorted.sort_values("_width", ascending=True).reset_index(drop=True)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), max(40, len(df_sorted) * 10) * (1 / 25.4)),
                           constrained_layout=True)

    y_pos = np.arange(len(df_sorted))
    base = df_sorted[base_col].values if base_col else np.zeros(len(df_sorted))

    for i in range(len(df_sorted)):
        low = df_sorted[low_col].iloc[i]
        high = df_sorted[high_col].iloc[i]
        ax.barh(y_pos[i], high - base[i], left=base[i], height=0.6,
                color="#0072B2", alpha=0.7, edgecolor="none")
        ax.barh(y_pos[i], low - base[i], left=base[i], height=0.6,
                color="#D55E00", alpha=0.7, edgecolor="none")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted[label_col].values, fontsize=5)
    ax.set_xlabel("Impact on outcome")
    if standalone:
        apply_chart_polish(ax, "tornado_chart")
    return ax


def gen_waterfall(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Waterfall plot: ordered patient/response values."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    value_col = roles.get("value") or roles.get("response")
    label_col = roles.get("label") or roles.get("subject_id")

    if value_col is None:
        raise ValueError("waterfall requires 'value' in semanticRoles")

    values = np.sort(df[value_col].values)[::-1]

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    colors = ["#0072B2" if v <= -30 else "#999999" if v <= 20 else "#D55E00" for v in values]
    ax.bar(range(len(values)), values, color=colors, width=0.7,
           linewidth=0.3, edgecolor="white")
    # Zero baseline — delegate to template_mining_helpers when reachable
    canonical_zero_ref = globals().get("add_zero_reference")
    if canonical_zero_ref is not None:
        try:
            canonical_zero_ref(ax, axis="y", color="black", lw=0.5, ls="-", zorder=1)
        except Exception:
            ax.axhline(0, color="black", lw=0.5)
    else:
        ax.axhline(0, color="black", lw=0.5)

    ax.set_xlabel("Patient")
    ax.set_ylabel("Response (%)")
    if standalone:
        apply_chart_polish(ax, "waterfall")
    return ax
