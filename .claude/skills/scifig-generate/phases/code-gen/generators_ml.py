"""ML-diagnostic chart generators & classifier boards.

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


def _is_classifier_validation_board(chartPlan, dataProfile=None):
    template_case = (chartPlan.get("templateCasePlan") or chartPlan.get("visualContentPlan", {}).get("templateCasePlan") or {})
    patterns = {str(p).lower() for p in (dataProfile or {}).get("specialPatterns", [])}
    return (
        template_case.get("bundleKey") == "classifier_validation_board"
        or "classifier_validation" in patterns
        or "probability_calibration" in patterns
        or "threshold_tuning" in patterns
    )


def _place_classifier_validation_legend(ax, standalone=False, ncol=2):
    handles, labels = ax.get_legend_handles_labels()
    if not labels:
        return None
    if standalone and ax.figure is not None:
        legend = ax.figure.legend(
            handles, labels,
            loc="lower center", bbox_to_anchor=(0.5, 0.02),
            ncol=min(max(1, ncol), len(labels)), fontsize=5,
            frameon=True, fancybox=True, borderpad=0.25,
            handlelength=1.4, columnspacing=0.8,
        )
        legend.set_gid("scifig_shared_legend")
        legend.get_frame().set_linewidth(0.35)
        legend.get_frame().set_edgecolor("#333333")
        legend.get_frame().set_alpha(0.94)
        try:
            if hasattr(ax.figure, "set_layout_engine"):
                ax.figure.set_layout_engine(None)
            else:
                ax.figure.set_constrained_layout(False)
        except Exception:
            pass
        sp = ax.figure.subplotpars
        ax.figure.subplots_adjust(left=max(sp.left, 0.20), bottom=max(sp.bottom, 0.32), right=min(sp.right, 0.96))
        return legend
    return None


def gen_calibration(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Calibration plot: predicted probability vs observed fraction."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    pred_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label") or roles.get("event")

    if pred_col is None or label_col is None:
        raise ValueError("calibration requires 'score' and 'label' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    is_classifier_board = _is_classifier_validation_board(chartPlan, dataProfile)

    pred = pd.to_numeric(df[pred_col], errors="coerce").clip(0, 1)
    label = pd.to_numeric(df[label_col], errors="coerce")
    valid_rows = pred.notna() & label.notna()
    pred = pred[valid_rows]
    label = label[valid_rows]

    # Bin predictions and compute observed fraction
    bins = np.linspace(0, 1, 11)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    observed = []
    counts = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (pred >= lo) & (pred <= hi if np.isclose(hi, 1.0) else pred < hi)
        counts.append(int(mask.sum()))
        if mask.sum() > 0:
            observed.append(float(label[mask].mean()))
        else:
            observed.append(np.nan)

    observed_arr = np.asarray(observed, dtype=float)
    counts_arr = np.asarray(counts, dtype=float)
    valid = np.isfinite(observed_arr) & (counts_arr > 0)
    ax.plot(bin_centers[valid], observed_arr[valid], "-", color="#1F4E79" if is_classifier_board else "#0072B2", lw=1)
    if is_classifier_board:
        sizes = 18 + (counts_arr / max(float(np.nanmax(counts_arr)), 1.0)) * 56
        ax.scatter(bin_centers, observed_arr, s=sizes, color="#1F4E79",
                   edgecolor="white", linewidth=0.45, zorder=4, label="Calibration bins")
        ece = float(np.nansum((counts_arr[valid] / max(counts_arr.sum(), 1.0)) * np.abs(observed_arr[valid] - bin_centers[valid]))) if valid.any() else np.nan
        band_x = np.linspace(0, 1, 80)
        ax.fill_between(band_x, np.clip(band_x - 0.05, 0, 1), np.clip(band_x + 0.05, 0, 1),
                        color="#F6CFA3", alpha=0.18, linewidth=0, label="±0.05 band")
        if valid.any():
            calib_error = np.where(valid, np.abs(observed_arr - bin_centers), np.nan)
            worst_idx = int(np.nanargmax(calib_error))
            ax.vlines(bin_centers[worst_idx], bin_centers[worst_idx], observed_arr[worst_idx],
                      color="#B00000", lw=0.75, alpha=0.75, zorder=3)
            ax.scatter([bin_centers[worst_idx]], [observed_arr[worst_idx]], s=sizes[worst_idx] + 16,
                       color="#B00000", edgecolor="white", linewidth=0.5, zorder=5, label="Worst bin")
        if np.isfinite(ece):
            ax.text(
                0.05, 0.88, f"ECE={ece:.3f}\nbins={int(valid.sum())}\nn={int(counts_arr.sum())}",
                transform=ax.transAxes, ha="left", va="top", fontsize=5.3,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
                zorder=6,
            )
        _place_classifier_validation_legend(ax, standalone, ncol=3)
    else:
        ax.plot(bin_centers, observed, "o-", color="#0072B2", lw=1, markersize=4)
    # Perfect-fit diagonal — delegate to template_mining_helpers when reachable
    canonical_diagonal = globals().get("add_perfect_fit_diagonal")
    if canonical_diagonal is not None:
        try:
            canonical_diagonal(ax, np.asarray([0.0, 1.0]), np.asarray([0.0, 1.0]),
                               color="#999999", lw=0.5, alpha=1.0)
        except Exception:
            ax.plot([0, 1], [0, 1], "--", color="#999999", lw=0.5)
    else:
        ax.plot([0, 1], [0, 1], "--", color="#999999", lw=0.5)

    ax.set_xlabel("Predicted probability" if standalone or not is_classifier_board else "")
    ax.set_ylabel("Observed fraction" if standalone or not is_classifier_board else "")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    if standalone:
        apply_chart_polish(ax, "calibration")
    return ax


def gen_classifier_validation_board(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Four-panel classifier board: ROC, PR, calibration, and threshold/confusion sidecar."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    columns_lower = {str(c).lower(): c for c in df.columns}

    def _role_or_col(*names):
        for name in names:
            col = roles.get(name)
            if col in df.columns:
                return col
        for name in names:
            col = columns_lower.get(str(name).lower())
            if col in df.columns:
                return col
        return None

    score_col = _role_or_col("score", "probability", "proba", "prediction_score", "y_score", "value")
    label_col = _role_or_col("label", "true_label", "actual_label", "y_true", "event", "class")
    model_col = _role_or_col("model", "algorithm", "estimator", "method")
    selected_col = _role_or_col("selected_model", "focus_model", "is_selected", "selected", "highlight", "winner")
    if score_col is None or label_col is None:
        raise ValueError("classifier_validation_board requires score/probability and binary label columns")

    def _is_rf_model(value):
        label = str(value).lower().replace("-", " ").replace("_", " ")
        collapsed = label.replace(" ", "")
        return "random forest" in label or collapsed in {"rf", "rfr", "randomforest"} or collapsed.startswith("rf")

    def _truthy(value):
        return str(value).strip().lower() in {"1", "true", "yes", "y", "selected", "focus", "winner", "best"}

    def _compact_model_label(value, width=17):
        text = str(value).strip()
        if len(text) <= width:
            return text
        return text[:max(3, width - 3)].rstrip() + "..."

    def _ordered_models(source_df):
        if not model_col or model_col not in source_df.columns:
            return []
        return [str(value) for value in source_df[model_col].dropna().drop_duplicates().tolist()]

    def _choose_selected_model(model_values, source_df):
        requested = (
            chartPlan.get("selectedModel")
            or chartPlan.get("focusModel")
            or chartPlan.get("highlightModel")
            or chartPlan.get("referenceModel")
        ) if isinstance(chartPlan, dict) else None
        if requested:
            requested_text = str(requested).lower()
            for model in model_values:
                if str(model).lower() == requested_text or requested_text in str(model).lower():
                    return model
        if selected_col and selected_col in source_df.columns and model_col in source_df.columns:
            selected_values = source_df[selected_col].dropna().astype(str).tolist()
            for value in selected_values:
                for model in model_values:
                    if value.lower() == str(model).lower() or value.lower() in str(model).lower():
                        return model
            truth_mask = source_df[selected_col].apply(_truthy)
            if truth_mask.any():
                selected_models = source_df.loc[truth_mask, model_col].dropna()
                if len(selected_models):
                    return str(selected_models.iloc[0])
        for model in model_values:
            if _is_rf_model(model):
                return model
        return model_values[0] if model_values else None

    model_values = _ordered_models(df)
    selected_model = _choose_selected_model(model_values, df) if model_values else None
    validation_df = df
    if selected_model and len(model_values) > 1 and model_col in df.columns:
        model_mask = df[model_col].astype(str).eq(str(selected_model))
        if model_mask.any():
            validation_df = df[model_mask].copy()

    work = validation_df[[score_col, label_col]].dropna().copy()
    if work.empty:
        raise ValueError("classifier_validation_board requires non-empty score/label pairs")
    score = pd.to_numeric(work[score_col], errors="coerce").astype(float).clip(0, 1)
    raw_label = work[label_col]
    if pd.api.types.is_numeric_dtype(raw_label):
        label = pd.to_numeric(raw_label, errors="coerce")
        unique_labels = sorted([v for v in label.dropna().unique().tolist()], key=lambda value: str(value))
        positive_label = unique_labels[-1] if unique_labels else 1
        y_true = (label == positive_label).astype(int).to_numpy()
        label_valid = label.notna().to_numpy()
    else:
        unique_labels = sorted(raw_label.dropna().astype(str).unique().tolist())
        positive_label = unique_labels[-1] if unique_labels else "positive"
        y_true = raw_label.astype(str).eq(str(positive_label)).astype(int).to_numpy()
        label_valid = raw_label.notna().to_numpy()
    valid = np.isfinite(score.to_numpy()) & label_valid
    score = score.to_numpy()[valid]
    y_true = y_true[valid]
    if len(score) == 0 or len(np.unique(y_true)) < 2:
        raise ValueError("classifier_validation_board requires both positive and negative labels")

    def _score_label_arrays(source_df):
        if score_col not in source_df.columns or label_col not in source_df.columns:
            return np.array([]), np.array([])
        score_series = pd.to_numeric(source_df[score_col], errors="coerce").astype(float).clip(0, 1)
        raw_label_series = source_df[label_col]
        if pd.api.types.is_numeric_dtype(raw_label_series):
            label_series = pd.to_numeric(raw_label_series, errors="coerce")
            unique_values = sorted([v for v in label_series.dropna().unique().tolist()], key=lambda value: str(value))
            positive_value = unique_values[-1] if unique_values else 1
            y_series = (label_series == positive_value).astype(int)
            valid_mask = score_series.notna() & label_series.notna()
        else:
            unique_values = sorted(raw_label_series.dropna().astype(str).unique().tolist())
            positive_value = unique_values[-1] if unique_values else "positive"
            y_series = raw_label_series.astype(str).eq(str(positive_value)).astype(int)
            valid_mask = score_series.notna() & raw_label_series.notna()
        return score_series[valid_mask].to_numpy(), y_series[valid_mask].to_numpy()

    def _auc_for_frame(source_df):
        scores, labels = _score_label_arrays(source_df)
        if len(scores) == 0 or len(np.unique(labels)) < 2:
            return np.nan
        positives = float(np.sum(labels == 1))
        negatives = float(np.sum(labels == 0))
        if positives == 0 or negatives == 0:
            return np.nan
        order = np.argsort(scores)
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(1, len(scores) + 1, dtype=float)
        positive_rank_sum = float(np.sum(ranks[labels == 1]))
        return (positive_rank_sum - positives * (positives + 1.0) / 2.0) / max(positives * negatives, 1.0)

    model_palette = palette.get("categorical", ["#1F4E79", "#D55E00", "#009E73", "#7A6C8F"])

    def _model_color(model, index):
        label = str(model).lower()
        if _is_rf_model(model):
            return model_palette[0 % len(model_palette)]
        if any(token in label for token in ("xgboost", "xgb", "lightgbm", "gbdt")):
            return model_palette[1 % len(model_palette)]
        if "svm" in label or "support vector" in label:
            return model_palette[2 % len(model_palette)]
        return model_palette[(index + 3) % len(model_palette)]

    display_models = []
    if selected_model:
        display_models.append(selected_model)
    display_models.extend([model for model in model_values if str(model) != str(selected_model)])
    display_models = display_models[:4]
    model_entries = []
    if model_col and model_col in df.columns:
        for idx, model in enumerate(display_models):
            model_frame = df[df[model_col].astype(str).eq(str(model))]
            model_entries.append({
                "label": _compact_model_label(model),
                "color": _model_color(model, idx),
                "selected": selected_model is not None and str(model) == str(selected_model),
                "auc": _auc_for_frame(model_frame),
                "n": int(len(model_frame)),
            })

    if standalone:
        fig, ax = plt.subplots(figsize=(183 / 25.4, 128 / 25.4), constrained_layout=False)
    fig = ax.figure
    ax.set_axis_off()
    if not chartPlan.get("suppressBoardTitle"):
        ax.set_title("Classifier validation board", loc="left", fontsize=8.2, fontweight="bold", pad=7)
    if len(model_entries) > 1 and not chartPlan.get("suppressBoardTitle"):
        selected_label = _compact_model_label(selected_model or model_entries[0]["label"], width=18)
        ax.text(0.055, 0.956, f"selected: {selected_label}   compared={len(model_values)} models",
                transform=ax.transAxes, ha="left", va="top", fontsize=5.2,
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="#333333", linewidth=0.35, alpha=0.92))

    visual_plan = chartPlan.get("visualContentPlan", {}) if isinstance(chartPlan, dict) else {}
    if callable(globals().get("_record_template_motif")):
        _record_template_motif(visual_plan, "classifier_validation_board")
        _record_template_motif(visual_plan, "classification_error_matrix")
        _record_template_motif(visual_plan, "metric_table_in_panel")
    if callable(globals().get("_visual_count")):
        _visual_count(visual_plan, "referenceLineCount")
        _visual_count(visual_plan, "metricBoxCount")

    axes = {
        "roc": ax.inset_axes([0.055, 0.565, 0.405, 0.345]),
        "pr": ax.inset_axes([0.555, 0.565, 0.390, 0.345]),
        "cal": ax.inset_axes([0.055, 0.090, 0.405, 0.350]),
        "thr": ax.inset_axes([0.555, 0.090, 0.390, 0.350]),
    }
    blue = "#1F4E79"
    orange = "#D55E00"
    red = "#B00000"
    gray = "#777777"
    pale = "#F6CFA3"

    def _polish_subaxis(sub_ax, title):
        sub_ax.set_title(title, loc="left", fontsize=6.8, fontweight="bold", pad=3)
        sub_ax.tick_params(labelsize=5.2, length=2.0, width=0.35, pad=1.5)
        for side in ("top", "right"):
            sub_ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            sub_ax.spines[side].set_linewidth(0.45)
            sub_ax.spines[side].set_color("#222222")
        sub_ax.grid(False)

    try:
        from sklearn.metrics import (
            average_precision_score,
            precision_recall_curve,
            roc_auc_score,
            roc_curve,
        )
        fpr, tpr, roc_thresholds = roc_curve(y_true, score)
        roc_auc = roc_auc_score(y_true, score)
        precision, recall, pr_thresholds = precision_recall_curve(y_true, score)
        ap = average_precision_score(y_true, score)
    except Exception:
        order = np.argsort(-score)
        y_sorted = y_true[order]
        tp = np.cumsum(y_sorted == 1)
        fp = np.cumsum(y_sorted == 0)
        pos = max(float((y_true == 1).sum()), 1.0)
        neg = max(float((y_true == 0).sum()), 1.0)
        tpr = np.r_[0, tp / pos, 1]
        fpr = np.r_[0, fp / neg, 1]
        recall = tp / pos
        precision = tp / np.maximum(tp + fp, 1)
        precision = np.r_[1, precision]
        recall = np.r_[0, recall]
        roc_thresholds = np.r_[1.0, score[order], 0.0]
        pr_thresholds = score[order]
        roc_auc = float(np.trapz(tpr, fpr))
        ap = float(np.trapz(precision, recall))

    youden = tpr - fpr
    best_roc_idx = int(np.nanargmax(youden))
    best_roc_threshold = float(roc_thresholds[min(best_roc_idx, len(roc_thresholds) - 1)])
    axes["roc"].plot(fpr, tpr, color=blue, lw=1.15)
    axes["roc"].fill_between(fpr, 0, tpr, color=blue, alpha=0.12, linewidth=0)
    axes["roc"].plot([0, 1], [0, 1], color="#999999", lw=0.55, ls="--")
    axes["roc"].scatter([fpr[best_roc_idx]], [tpr[best_roc_idx]], s=24, color=red, edgecolor="white", linewidth=0.35, zorder=5)
    axes["roc"].set(xlim=(0, 1), ylim=(0, 1), xlabel="FPR", ylabel="TPR")
    axes["roc"].text(0.05, 0.18, f"AUC={roc_auc:.3f}\nthr={best_roc_threshold:.2f}\nn={len(y_true)}",
                     transform=axes["roc"].transAxes, fontsize=5.0, ha="left", va="bottom",
                     bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.94))
    _polish_subaxis(axes["roc"], "A. ROC discrimination")

    f1_curve = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    best_pr_idx = int(np.nanargmax(f1_curve)) if len(f1_curve) else 0
    best_pr_threshold = float(pr_thresholds[min(best_pr_idx, len(pr_thresholds) - 1)]) if len(pr_thresholds) else 0.5
    axes["pr"].plot(recall, precision, color=blue, lw=1.15)
    axes["pr"].fill_between(recall, precision, color=blue, alpha=0.12, linewidth=0)
    axes["pr"].axhline(y=float(y_true.mean()), color="#999999", lw=0.55, ls="--")
    if len(f1_curve):
        axes["pr"].scatter([recall[best_pr_idx]], [precision[best_pr_idx]], s=24, color=red,
                           edgecolor="white", linewidth=0.35, zorder=5)
    axes["pr"].set(xlim=(0, 1), ylim=(0, 1), xlabel="Recall", ylabel="Precision")
    axes["pr"].text(0.05, 0.18, f"AP={ap:.3f}\nF1={np.nanmax(f1_curve):.3f}\nthr={best_pr_threshold:.2f}",
                    transform=axes["pr"].transAxes, fontsize=5.0, ha="left", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.94))
    _polish_subaxis(axes["pr"], "B. Precision-recall")

    bins = np.linspace(0, 1, 11)
    centers = (bins[:-1] + bins[1:]) / 2
    observed = []
    counts = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (score >= lo) & (score <= hi if np.isclose(hi, 1.0) else score < hi)
        counts.append(int(mask.sum()))
        observed.append(float(y_true[mask].mean()) if mask.sum() else np.nan)
    observed = np.asarray(observed, dtype=float)
    counts = np.asarray(counts, dtype=float)
    valid_bins = np.isfinite(observed) & (counts > 0)
    sizes = 18 + (counts / max(float(np.nanmax(counts)), 1.0)) * 58
    axes["cal"].fill_between(np.linspace(0, 1, 60), np.clip(np.linspace(0, 1, 60) - 0.05, 0, 1),
                             np.clip(np.linspace(0, 1, 60) + 0.05, 0, 1), color=pale, alpha=0.18, linewidth=0)
    axes["cal"].plot([0, 1], [0, 1], color="#999999", lw=0.55, ls="--")
    axes["cal"].plot(centers[valid_bins], observed[valid_bins], color=blue, lw=1.0)
    axes["cal"].scatter(centers[valid_bins], observed[valid_bins], s=sizes[valid_bins], color=blue,
                        edgecolor="white", linewidth=0.35, zorder=5)
    ece = float(np.nansum((counts[valid_bins] / max(counts.sum(), 1.0)) * np.abs(observed[valid_bins] - centers[valid_bins]))) if valid_bins.any() else np.nan
    if valid_bins.any():
        worst_idx = int(np.nanargmax(np.where(valid_bins, np.abs(observed - centers), np.nan)))
        axes["cal"].scatter([centers[worst_idx]], [observed[worst_idx]], s=sizes[worst_idx] + 14,
                            color=red, edgecolor="white", linewidth=0.35, zorder=6)
    axes["cal"].set(xlim=(0, 1), ylim=(0, 1), xlabel="Predicted", ylabel="Observed")
    axes["cal"].text(0.05, 0.86, f"ECE={ece:.3f}\nbins={int(valid_bins.sum())}",
                     transform=axes["cal"].transAxes, fontsize=5.0, ha="left", va="top",
                     bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.94))
    _polish_subaxis(axes["cal"], "C. Probability calibration")

    thresholds = np.linspace(0.05, 0.95, 19)
    metrics = []
    for threshold in thresholds:
        pred = score >= threshold
        tp = float(np.sum((pred == 1) & (y_true == 1)))
        fp = float(np.sum((pred == 1) & (y_true == 0)))
        tn = float(np.sum((pred == 0) & (y_true == 0)))
        fn = float(np.sum((pred == 0) & (y_true == 1)))
        precision_t = tp / max(tp + fp, 1.0)
        recall_t = tp / max(tp + fn, 1.0)
        f1_t = 2 * precision_t * recall_t / max(precision_t + recall_t, 1e-12)
        specificity_t = tn / max(tn + fp, 1.0)
        balanced_t = (recall_t + specificity_t) / 2
        metrics.append((threshold, f1_t, balanced_t, tp, fp, tn, fn))
    metrics_arr = np.asarray(metrics, dtype=float)
    best_idx = int(np.nanargmax(metrics_arr[:, 1]))
    best_threshold, best_f1, best_balanced, tp, fp, tn, fn = metrics_arr[best_idx]
    axes["thr"].plot(metrics_arr[:, 0], metrics_arr[:, 1], color=blue, lw=1.15, marker="o", ms=2.4)
    axes["thr"].plot(metrics_arr[:, 0], metrics_arr[:, 2], color=orange, lw=1.0, marker="s", ms=2.2)
    axes["thr"].axvline(best_threshold, color=red, lw=0.65, ls="--")
    axes["thr"].set(xlim=(0, 1), ylim=(0, 1), xlabel="Threshold", ylabel="Score")
    axes["thr"].text(0.08, 0.14, "F1", transform=axes["thr"].transAxes,
                     color=blue, fontsize=4.9, fontweight="bold")
    axes["thr"].text(0.08, 0.22, "Balanced", transform=axes["thr"].transAxes,
                     color=orange, fontsize=4.9, fontweight="bold")
    if chartPlan.get("suppressBoardTitle"):
        sidecar = f"thr={best_threshold:.2f}  F1={best_f1:.2f}\nTP/FP {int(tp)}/{int(fp)}\nFN/TN {int(fn)}/{int(tn)}"
        sidecar_font = 4.55
    else:
        sidecar = f"thr={best_threshold:.2f}\nF1={best_f1:.3f}\nTP {int(tp)} | FP {int(fp)}\nFN {int(fn)} | TN {int(tn)}"
        sidecar_font = 4.9
    axes["thr"].text(0.98, 0.08, sidecar, transform=axes["thr"].transAxes, fontsize=sidecar_font,
                     ha="right", va="bottom",
                     bbox=dict(boxstyle="round,pad=0.24", facecolor="white", edgecolor=gray, linewidth=0.45, alpha=0.95))
    threshold_title = "D. Threshold sweep" if chartPlan.get("suppressBoardTitle") else "D. Threshold + confusion sidecar"
    _polish_subaxis(axes["thr"], threshold_title)

    if standalone:
        if len(model_entries) > 1:
            handles = [
                plt.Line2D(
                    [0], [0], marker="D" if entry["selected"] else "o", linestyle="",
                    markerfacecolor=entry["color"],
                    markeredgecolor="#111111" if entry["selected"] else "white",
                    markeredgewidth=0.55, markersize=4.2,
                    label=("selected: " if entry["selected"] else "") + entry["label"],
                )
                for entry in model_entries
            ]
            legend = fig.legend(
                handles=handles,
                loc="lower center", bbox_to_anchor=(0.5, 0.018),
                ncol=min(4, len(handles)), fontsize=5.0,
                frameon=True, fancybox=True, borderpad=0.25,
                handlelength=1.2, columnspacing=0.8,
            )
            legend.set_gid("scifig_shared_legend")
            legend.get_frame().set_linewidth(0.35)
            legend.get_frame().set_edgecolor("#333333")
            legend.get_frame().set_alpha(0.94)
            fig.subplots_adjust(left=0.05, right=0.98, top=0.91, bottom=0.145)
        else:
            fig.subplots_adjust(left=0.05, right=0.98, top=0.93, bottom=0.09)
    return ax


def gen_pr_curve(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Precision-Recall curve with AUC annotation."""
    standalone = ax is None

    roles = dataProfile.get("semanticRoles", {})
    score_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label")

    if not score_col or not label_col:
        raise ValueError("pr_curve requires 'score' and 'label' in semanticRoles")

    y_true = df[label_col].values
    y_score = df[score_col].values
    is_classifier_board = _is_classifier_validation_board(chartPlan, dataProfile)
    if standalone:
        fig_size = (89 * (1 / 25.4), 75 * (1 / 25.4)) if is_classifier_board else (62 * (1 / 25.4), 62 * (1 / 25.4))
        fig, ax = plt.subplots(figsize=fig_size, constrained_layout=True)

    try:
        from sklearn.metrics import precision_recall_curve, average_precision_score
        precision, recall, thresholds = precision_recall_curve(y_true, y_score)
        ap = average_precision_score(y_true, y_score)

        ax.plot(recall, precision, color="#1F4E79", lw=1.1 if is_classifier_board else 0.8, label=f"AP = {ap:.3f}")
        ax.fill_between(recall, precision, alpha=0.12 if is_classifier_board else 0.1, color="#1F4E79")

        # Baseline
        baseline = y_true.mean()
        ax.axhline(y=baseline, color="#999999", lw=0.4, ls="--", label=f"Baseline = {baseline:.3f}")
        if is_classifier_board and len(thresholds):
            f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
            best_idx = int(np.nanargmax(f1))
            best_threshold = thresholds[best_idx]
            ax.axvline(recall[best_idx], color="#444444", lw=0.55, ls="--", alpha=0.55, zorder=1)
            ax.axhline(precision[best_idx], color="#444444", lw=0.55, ls="--", alpha=0.55, zorder=1)
            ax.scatter([recall[best_idx]], [precision[best_idx]], s=36, color="#B00000",
                       edgecolor="white", linewidth=0.45, zorder=5, label="Best F1 threshold")
            ax.text(
                0.08, 0.18,
                f"AP={ap:.3f}\nF1={f1[best_idx]:.3f}\nthr={best_threshold:.2f}\nn={len(y_true)}",
                transform=ax.transAxes, ha="left", va="bottom", fontsize=5.3,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
                zorder=6,
            )

        if is_classifier_board:
            _place_classifier_validation_legend(ax, standalone, ncol=3)
        else:
            ax.legend(fontsize=5, frameon=False)
    except ImportError:
        ax.text(0.5, 0.5, "scikit-learn required", ha="center", va="center", transform=ax.transAxes)

    ax.set_xlabel("Recall" if standalone or not is_classifier_board else "")
    ax.set_ylabel("Precision" if standalone or not is_classifier_board else "")
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1.05])
    if standalone:
        apply_chart_polish(ax, "pr_curve")
    return ax


def gen_rf_classifier_report_board(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Random-forest classifier report: validation board plus feature-importance lane."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    columns_lower = {str(c).lower(): c for c in df.columns}
    import textwrap

    def _role_or_col(*names, contains=()):
        for name in names:
            col = roles.get(name)
            if col in df.columns:
                return col
        for name in names:
            col = columns_lower.get(str(name).lower())
            if col in df.columns:
                return col
        for col in df.columns:
            lowered = str(col).lower()
            if any(token in lowered for token in contains):
                return col
        return None

    score_col = _role_or_col("score", "probability", "proba", "prediction_score", "y_score")
    label_col = _role_or_col("label", "true_label", "actual_label", "y_true", "event", "class")
    partition_col = _role_or_col(
        "table_type", "record_type", "row_type", "source_type", "panel", "kind",
        contains=("table_type", "record_type", "row_type", "source_type")
    )
    feature_col = _role_or_col("feature_id", "feature", "feature_name", "variable", "term", contains=("feature", "variable"))
    importance_col = _role_or_col(
        "importance", "feature_importance", "mean_abs_shap", "gain", "permutation", "shap_value", "value",
        contains=("importance", "mean_abs_shap", "gain", "permutation", "shap")
    )
    model_col = _role_or_col("model", "algorithm", "estimator", contains=("model", "algorithm", "estimator"))
    selected_col = _role_or_col("selected_model", "focus_model", "is_selected", "selected", "highlight", "winner",
                                contains=("selected", "focus", "winner"))
    if score_col is None or label_col is None:
        raise ValueError("rf_classifier_report_board requires score/probability and binary label columns")

    prediction_df = df
    importance_source_df = df
    if partition_col and partition_col in df.columns:
        partition = df[partition_col].astype(str).str.lower()
        prediction_tokens = ("prediction", "validation", "classifier", "probability", "score", "holdout", "test")
        importance_tokens = ("importance", "feature", "shap", "gain", "permutation", "explain")
        prediction_mask = partition.apply(lambda value: any(token in value for token in prediction_tokens))
        importance_mask = partition.apply(lambda value: any(token in value for token in importance_tokens))
        score_label_mask = df[score_col].notna() & df[label_col].notna()
        if prediction_mask.any() or score_label_mask.any():
            prediction_df = df[prediction_mask | score_label_mask].copy()
        if feature_col and importance_col and feature_col in df.columns and importance_col in df.columns:
            feature_mask = df[feature_col].notna() & df[importance_col].notna()
            if importance_mask.any() or feature_mask.any():
                importance_source_df = df[importance_mask | feature_mask].copy()

    def _is_rf_model(value):
        label = str(value).lower().replace("-", " ").replace("_", " ")
        collapsed = label.replace(" ", "")
        return "random forest" in label or collapsed in {"rf", "rfr", "randomforest"} or collapsed.startswith("rf")

    def _truthy(value):
        return str(value).strip().lower() in {"1", "true", "yes", "y", "selected", "focus", "winner", "best"}

    def _compact_model_label(value, width=17):
        text = str(value).strip()
        if len(text) <= width:
            return text
        return text[:max(3, width - 3)].rstrip() + "..."

    def _ordered_models(source_df):
        if not model_col or model_col not in source_df.columns:
            return []
        return [str(value) for value in source_df[model_col].dropna().drop_duplicates().tolist()]

    def _choose_selected_model(model_values, source_df):
        requested = None
        if isinstance(chartPlan, dict):
            requested = (
                chartPlan.get("selectedModel")
                or chartPlan.get("focusModel")
                or chartPlan.get("highlightModel")
                or chartPlan.get("referenceModel")
            )
        if requested:
            requested_text = str(requested).lower()
            for model in model_values:
                if str(model).lower() == requested_text or requested_text in str(model).lower():
                    return model
        if selected_col and selected_col in source_df.columns and model_col in source_df.columns:
            selected_values = source_df[selected_col].dropna().astype(str).tolist()
            for value in selected_values:
                for model in model_values:
                    if value.lower() == str(model).lower() or value.lower() in str(model).lower():
                        return model
            truth_mask = source_df[selected_col].apply(_truthy)
            if truth_mask.any():
                return str(source_df.loc[truth_mask, model_col].dropna().iloc[0])
        for model in model_values:
            if _is_rf_model(model):
                return model
        return model_values[0] if model_values else None

    def _rf_model_matches(value, target):
        value_text = str(value).strip().lower()
        target_text = str(target).strip().lower()
        if not value_text or value_text in {"nan", "none"} or not target_text or target_text in {"nan", "none"}:
            return False
        if value_text == target_text or value_text in target_text or target_text in value_text:
            return True
        return _is_rf_model(value) and _is_rf_model(target)

    model_values = _ordered_models(prediction_df)
    selected_model = _choose_selected_model(model_values, prediction_df) if model_values else None
    selected_prediction_df = prediction_df
    if selected_model and len(model_values) > 1 and model_col in prediction_df.columns:
        model_mask = prediction_df[model_col].astype(str).eq(str(selected_model))
        if model_mask.any():
            selected_prediction_df = prediction_df[model_mask].copy()

    if standalone:
        fig, ax = plt.subplots(figsize=(183 / 25.4, 128 / 25.4), constrained_layout=False)
    fig = ax.figure
    ax.set_axis_off()
    ax.set_title("Random-forest classifier report", loc="left", fontsize=8.4, fontweight="bold", pad=7)

    visual_plan = chartPlan.get("visualContentPlan", {}) if isinstance(chartPlan, dict) else {}
    if callable(globals().get("_record_template_motif")):
        _record_template_motif(visual_plan, "rf_classifier_report_board")
        _record_template_motif(visual_plan, "classifier_validation_board")
        _record_template_motif(visual_plan, "explainability_importance_stack")
        _record_template_motif(visual_plan, "classification_error_matrix")
        _record_template_motif(visual_plan, "metric_table_in_panel")
    if callable(globals().get("_visual_count")):
        _visual_count(visual_plan, "metricBoxCount")
        _visual_count(visual_plan, "panelLabelCount")

    validation_ax = ax.inset_axes([0.025, 0.075, 0.645, 0.840])
    importance_ax = ax.inset_axes([0.725, 0.415, 0.245, 0.445])
    model_ax = ax.inset_axes([0.725, 0.235, 0.245, 0.095])
    summary_ax = ax.inset_axes([0.725, 0.075, 0.245, 0.120])

    validation_plan = dict(chartPlan or {})
    validation_plan["primaryChart"] = "classifier_validation_board"
    validation_plan["suppressBoardTitle"] = True
    validation_plan["templateCasePlan"] = {"bundleKey": "classifier_validation_board"}
    validation_profile = dict(dataProfile)
    validation_profile["df"] = selected_prediction_df
    validation_profile["nObservations"] = len(selected_prediction_df)
    gen_classifier_validation_board(selected_prediction_df, validation_profile, validation_plan, rcParams, palette, col_map=col_map, ax=validation_ax)

    colors = palette.get("categorical", ["#1F4E79", "#D55E00", "#009E73", "#7A6C8F"])
    importance_model_df = importance_source_df
    missing_selected_importance = False
    if selected_model and model_col and model_col in importance_source_df.columns:
        model_labels = importance_source_df[model_col].astype(str).str.strip()
        labeled_importance_mask = importance_source_df[model_col].notna() & ~model_labels.str.lower().isin({"", "nan", "none"})
        selected_importance_mask = pd.Series(
            [_rf_model_matches(value, selected_model) for value in importance_source_df[model_col]],
            index=importance_source_df.index,
        )
        unlabeled_importance_mask = ~labeled_importance_mask
        if selected_importance_mask.any():
            importance_model_df = importance_source_df[selected_importance_mask | unlabeled_importance_mask].copy()
        elif labeled_importance_mask.any():
            importance_model_df = importance_source_df.iloc[0:0].copy()
            missing_selected_importance = True
    if feature_col and importance_col and feature_col in importance_model_df.columns and importance_col in importance_model_df.columns:
        feature_df = importance_model_df[[feature_col, importance_col]].dropna().copy()
        feature_df[importance_col] = pd.to_numeric(feature_df[importance_col], errors="coerce")
        feature_df = feature_df.dropna(subset=[importance_col])
        if not feature_df.empty:
            feature_df = (
                feature_df.groupby(feature_col, as_index=False)[importance_col]
                .mean()
                .assign(_abs=lambda frame: frame[importance_col].abs())
                .nlargest(min(12, feature_df[feature_col].nunique()), "_abs")
                .sort_values("_abs", ascending=True)
            )
    else:
        feature_df = pd.DataFrame()

    def _feature_label(value, width=18, max_lines=2):
        text = str(value).replace("_", " ").replace("/", " / ").strip()
        text = " ".join(text.split())
        if not text:
            return "feature"
        wrapped = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=True)
        if not wrapped:
            wrapped = [text[:width]]
        if len(wrapped) > max_lines:
            wrapped = wrapped[:max_lines]
            wrapped[-1] = wrapped[-1][:max(3, width - 3)].rstrip() + "..."
        return "\n".join(wrapped)

    def _score_label_arrays(source_df):
        if score_col not in source_df.columns or label_col not in source_df.columns:
            return np.array([]), np.array([])
        score_series = pd.to_numeric(source_df[score_col], errors="coerce").astype(float).clip(0, 1)
        raw_label_series = source_df[label_col]
        if pd.api.types.is_numeric_dtype(raw_label_series):
            label_series = pd.to_numeric(raw_label_series, errors="coerce")
            unique_values = sorted([v for v in label_series.dropna().unique().tolist()], key=lambda value: str(value))
            positive_value = unique_values[-1] if unique_values else 1
            y_series = (label_series == positive_value).astype(int)
            valid_mask = score_series.notna() & label_series.notna()
        else:
            unique_values = sorted(raw_label_series.dropna().astype(str).unique().tolist())
            positive_value = unique_values[-1] if unique_values else "positive"
            y_series = raw_label_series.astype(str).eq(str(positive_value)).astype(int)
            valid_mask = score_series.notna() & raw_label_series.notna()
        return score_series[valid_mask].to_numpy(), y_series[valid_mask].to_numpy()

    def _auc_for_frame(source_df):
        scores, labels = _score_label_arrays(source_df)
        if len(scores) == 0 or len(np.unique(labels)) < 2:
            return np.nan
        positives = float(np.sum(labels == 1))
        negatives = float(np.sum(labels == 0))
        if positives == 0 or negatives == 0:
            return np.nan
        order = np.argsort(scores)
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(1, len(scores) + 1, dtype=float)
        positive_rank_sum = float(np.sum(ranks[labels == 1]))
        return (positive_rank_sum - positives * (positives + 1.0) / 2.0) / max(positives * negatives, 1.0)

    def _model_color(model, index):
        label = str(model).lower()
        if _is_rf_model(model):
            return colors[0 % len(colors)]
        if any(token in label for token in ("xgboost", "xgb", "lightgbm", "gbdt")):
            return colors[1 % len(colors)]
        if "svm" in label or "support vector" in label:
            return colors[2 % len(colors)]
        return colors[(index + 3) % len(colors)]

    display_models = []
    if selected_model:
        display_models.append(selected_model)
    display_models.extend([model for model in model_values if str(model) != str(selected_model)])
    display_models = display_models[:4]
    model_entries = []
    if model_col and model_col in prediction_df.columns:
        for idx, model in enumerate(display_models):
            model_frame = prediction_df[prediction_df[model_col].astype(str).eq(str(model))]
            model_entries.append({
                "model": model,
                "label": _compact_model_label(model),
                "color": _model_color(model, idx),
                "selected": selected_model is not None and str(model) == str(selected_model),
                "auc": _auc_for_frame(model_frame),
                "n": int(len(model_frame)),
            })

    model_ax.set_axis_off()
    if len(model_entries) > 1:
        model_ax.text(0.00, 0.98, "F. model competition", transform=model_ax.transAxes,
                      ha="left", va="top", fontsize=6.0, fontweight="bold")
        ys = np.linspace(0.62, 0.12, len(model_entries))
        for y_pos, entry in zip(ys, model_entries):
            marker = "D" if entry["selected"] else "o"
            model_ax.scatter([0.055], [y_pos], s=22 if entry["selected"] else 16, marker=marker,
                             color=entry["color"], edgecolor="#111111" if entry["selected"] else "white",
                             linewidth=0.45, transform=model_ax.transAxes, zorder=4)
            model_ax.text(0.13, y_pos, entry["label"], transform=model_ax.transAxes, ha="left", va="center",
                          fontsize=4.65, fontweight="bold" if entry["selected"] else "normal",
                          color="#111111" if entry["selected"] else "#333333")
            metric = f"AUC {entry['auc']:.2f}" if np.isfinite(entry["auc"]) else f"n={entry['n']}"
            model_ax.text(0.99, y_pos, metric, transform=model_ax.transAxes, ha="right", va="center",
                          fontsize=4.45, color="#111111" if entry["selected"] else "#555555")
    elif selected_model:
        model_ax.text(0.00, 0.72, "F. selected model", transform=model_ax.transAxes,
                      ha="left", va="top", fontsize=6.0, fontweight="bold")
        model_ax.text(0.00, 0.32, _compact_model_label(selected_model, width=24),
                      transform=model_ax.transAxes, ha="left", va="center",
                      fontsize=5.0, fontweight="bold", color="#111111")

    importance_ax.set_title("E. RF feature importance", loc="left", fontsize=6.8, fontweight="bold", pad=3)
    if not feature_df.empty:
        values = feature_df[importance_col].astype(float).to_numpy()
        labels = [_feature_label(value) for value in feature_df[feature_col]]
        denom = max(float(np.nanmax(np.abs(values))), 1e-12)
        scaled = np.abs(values) / denom
        y = np.arange(len(labels))
        bar_colors = [colors[min(len(colors) - 1, int(frac * (len(colors) - 1)))] for frac in scaled]
        importance_ax.barh(y, scaled, color=bar_colors, edgecolor="white", linewidth=0.35, height=0.68)
        importance_ax.set_yticks(y)
        importance_ax.set_yticklabels(labels, fontsize=4.9)
        importance_ax.set_xlim(0, 1.10)
        importance_ax.set_xlabel("Relative importance", fontsize=5.0, labelpad=0.8)
        importance_ax.tick_params(axis="x", labelsize=4.8, length=2, width=0.35)
        importance_ax.tick_params(axis="y", length=0, pad=1.5)
        for yi, value, frac in zip(y, values, scaled):
            importance_ax.text(min(frac + 0.025, 1.03), yi, f"{value:.2g}", va="center", ha="left", fontsize=4.6)
    else:
        empty_message = "Selected RF importance\nnot supplied" if missing_selected_importance and selected_model else "Feature importance\nnot supplied"
        importance_ax.text(0.5, 0.55, empty_message, ha="center", va="center",
                           fontsize=5.6, color="#555555", transform=importance_ax.transAxes)
        importance_ax.set_xticks([])
        importance_ax.set_yticks([])
    for side in ("top", "right"):
        importance_ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        importance_ax.spines[side].set_linewidth(0.45)

    summary_ax.set_axis_off()
    score = pd.to_numeric(selected_prediction_df[score_col], errors="coerce")
    raw_label = selected_prediction_df[label_col]
    if pd.api.types.is_numeric_dtype(raw_label):
        label = pd.to_numeric(raw_label, errors="coerce")
        unique_labels = sorted([v for v in label.dropna().unique().tolist()], key=lambda value: str(value))
        positive_label = unique_labels[-1] if unique_labels else 1
        y_true = (label == positive_label).astype(int)
    else:
        unique_labels = sorted(raw_label.dropna().astype(str).unique().tolist())
        positive_label = unique_labels[-1] if unique_labels else "positive"
        y_true = raw_label.astype(str).eq(str(positive_label)).astype(int)
    valid = score.notna() & y_true.notna()
    score = score[valid].clip(0, 1).to_numpy()
    y_true = y_true[valid].to_numpy()
    thresholds = np.linspace(0.05, 0.95, 19)
    f1_values = []
    for threshold in thresholds:
        pred = score >= threshold
        tp = float(np.sum((pred == 1) & (y_true == 1)))
        fp = float(np.sum((pred == 1) & (y_true == 0)))
        fn = float(np.sum((pred == 0) & (y_true == 1)))
        precision_t = tp / max(tp + fp, 1.0)
        recall_t = tp / max(tp + fn, 1.0)
        f1_values.append(2 * precision_t * recall_t / max(precision_t + recall_t, 1e-12))
    best_idx = int(np.nanargmax(f1_values)) if f1_values else 0
    model_name = "Random Forest"
    if selected_model:
        model_name = "selected: " + _compact_model_label(selected_model, width=16)
    summary_lines = [
        model_name,
        f"n={len(score)}  pos={int(np.sum(y_true == 1))}",
        f"best F1={float(f1_values[best_idx]):.3f}",
        f"thr={float(thresholds[best_idx]):.2f}",
        f"features={len(feature_df) if not feature_df.empty else 0}",
    ]
    if len(model_values) > 1:
        summary_lines.insert(1, f"compared={len(model_values)} models")
    summary_ax.text(0.02, 0.98, "\n".join(summary_lines), transform=summary_ax.transAxes,
                    ha="left", va="top", fontsize=5.4,
                    bbox=dict(boxstyle="round,pad=0.28", facecolor="white", edgecolor="#333333", linewidth=0.45, alpha=0.96))

    if standalone:
        if len(model_entries) > 1:
            handles = [
                plt.Line2D(
                    [0], [0], marker="D" if entry["selected"] else "o", linestyle="",
                    markerfacecolor=entry["color"],
                    markeredgecolor="#111111" if entry["selected"] else "white",
                    markeredgewidth=0.55, markersize=4.2,
                    label=("selected: " if entry["selected"] else "") + entry["label"],
                )
                for entry in model_entries
            ]
            legend = fig.legend(
                handles=handles,
                loc="lower center", bbox_to_anchor=(0.5, 0.018),
                ncol=min(4, len(handles)), fontsize=5.0,
                frameon=True, fancybox=True, borderpad=0.25,
                handlelength=1.2, columnspacing=0.8,
            )
            legend.set_gid("scifig_shared_legend")
            legend.get_frame().set_linewidth(0.35)
            legend.get_frame().set_edgecolor("#333333")
            legend.get_frame().set_alpha(0.94)
            fig.subplots_adjust(left=0.035, right=0.985, top=0.92, bottom=0.145)
        else:
            fig.subplots_adjust(left=0.035, right=0.985, top=0.92, bottom=0.08)
    return ax


def gen_roc(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """ROC curve with AUC annotation and confidence band."""
    standalone = ax is None
    from sklearn.metrics import roc_curve, auc

    roles = dataProfile.get("semanticRoles", {})
    score_col = roles.get("score") or roles.get("value")
    label_col = roles.get("label") or roles.get("event")

    if score_col is None or label_col is None:
        raise ValueError("roc requires 'score' and 'label' in semanticRoles")

    y_true = df[label_col].values
    y_scores = df[score_col].values

    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)
    is_classifier_board = _is_classifier_validation_board(chartPlan, dataProfile)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 75 * (1 / 25.4)),
                           constrained_layout=True)

    color = "#1F4E79" if is_classifier_board else "#0072B2"
    ax.plot(fpr, tpr, color=color, lw=1.15 if is_classifier_board else 1, label=f"ROC AUC = {roc_auc:.3f}")
    # Chance diagonal — delegate to template_mining_helpers when reachable
    # (encodes the corpus-anchored 'random classifier reference' for ROC panels)
    canonical_diagonal = globals().get("add_perfect_fit_diagonal")
    if canonical_diagonal is not None:
        try:
            canonical_diagonal(ax, np.asarray([0.0, 1.0]), np.asarray([0.0, 1.0]),
                               color="#999999", lw=0.5, alpha=1.0)
            # Register legend entry via proxy (canonical helper has no label kwarg)
            ax.plot([], [], color="#999999", lw=0.5, ls="--", label="Chance")
        except Exception:
            ax.plot([0, 1], [0, 1], color="#999999", lw=0.5, ls="--", label="Chance")
    else:
        ax.plot([0, 1], [0, 1], color="#999999", lw=0.5, ls="--", label="Chance")
    ax.fill_between(fpr, 0, tpr, alpha=0.12 if is_classifier_board else 0.1, color=color)
    if is_classifier_board and len(thresholds):
        youden = tpr - fpr
        best_idx = int(np.nanargmax(youden))
        best_threshold = thresholds[best_idx]
        if np.isfinite(best_threshold):
            ax.axvline(fpr[best_idx], color="#444444", lw=0.55, ls="--", alpha=0.55, zorder=1)
            ax.axhline(tpr[best_idx], color="#444444", lw=0.55, ls="--", alpha=0.55, zorder=1)
            ax.scatter([fpr[best_idx]], [tpr[best_idx]], s=36, color="#B00000",
                       edgecolor="white", linewidth=0.45, zorder=5, label="Best threshold")
            callout_x = 0.62 if standalone else 0.05
            ax.text(
                callout_x, 0.18,
                f"AUC={roc_auc:.3f}\nthr={best_threshold:.2f}\nn={len(y_true)}",
                transform=ax.transAxes, ha="left", va="bottom", fontsize=5.3,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="#333333", linewidth=0.4, alpha=0.93),
                zorder=6,
            )

    ax.set_xlabel("False Positive Rate" if standalone or not is_classifier_board else "")
    ax.set_ylabel("True Positive Rate" if standalone or not is_classifier_board else "")
    if is_classifier_board:
        _place_classifier_validation_legend(ax, standalone, ncol=3)
    else:
        ax.legend(loc="lower right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "roc")
    return ax


def gen_training_curve(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Neural-network training history with validation gap and best-epoch callout."""
    standalone = ax is None
    import numpy as np
    import pandas as pd
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    columns_lower = {str(c).lower(): c for c in df.columns}
    display = globals().get("_display_col", lambda col, mapping=None: str(col))

    def _col(*names):
        for name in names:
            if name in roles and roles[name] in df.columns:
                return roles[name]
        for name in names:
            key = str(name).lower()
            if key in columns_lower:
                return columns_lower[key]
        return None

    epoch_col = _col("epoch", "epochs", "step", "iteration", "iter", "batch", "x", "time")
    metric_role = _col("metric")
    value_col = _col("value", "score", "y")
    split_col = _col("split", "phase", "subset", "group")
    model_col = _col("model", "run", "fold", "seed", "optimizer")
    if epoch_col is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        epoch_col = numeric_cols[0] if numeric_cols else None
    if epoch_col is None:
        raise ValueError("training_curve requires an epoch, step, or iteration column")

    work = df.copy()
    metric_cols = []
    if metric_role and value_col and metric_role in work.columns and value_col in work.columns:
        index_cols = [epoch_col]
        if split_col and split_col in work.columns:
            index_cols.append(split_col)
        if model_col and model_col in work.columns:
            index_cols.append(model_col)
        wide = work.pivot_table(index=index_cols, columns=metric_role, values=value_col, aggfunc="mean").reset_index()
        wide.columns = [str(c) for c in wide.columns]
        work = wide
        columns_lower = {str(c).lower(): c for c in work.columns}

    def _match_cols(tokens, exclude=()):
        matches = []
        for col in work.columns:
            key = str(col).lower()
            if col == epoch_col or col in exclude:
                continue
            if not pd.api.types.is_numeric_dtype(work[col]):
                continue
            if any(token in key for token in tokens):
                matches.append(col)
        return matches

    loss_cols = _match_cols(("loss", "cross_entropy", "ce"), exclude=(value_col,))
    score_cols = _match_cols(("accuracy", "acc", "auc", "f1", "precision", "recall"), exclude=(value_col,))
    preferred = [
        "train_loss", "training_loss", "loss", "val_loss", "validation_loss", "test_loss",
        "train_accuracy", "training_accuracy", "accuracy", "val_accuracy", "validation_accuracy",
        "val_auc", "auc", "f1", "val_f1",
    ]
    ordered = []
    for key in preferred:
        col = columns_lower.get(key)
        if col in loss_cols + score_cols and col not in ordered:
            ordered.append(col)
    for col in loss_cols + score_cols:
        if col not in ordered:
            ordered.append(col)
    metric_cols = ordered[:6]
    if not metric_cols:
        numeric_cols = [c for c in work.select_dtypes(include="number").columns if c != epoch_col]
        metric_cols = numeric_cols[:4]
    if not metric_cols:
        raise ValueError("training_curve requires loss, accuracy, auc, f1, or numeric metric columns")

    if standalone:
        fig, ax = plt.subplots(figsize=(105 * (1 / 25.4), 72 * (1 / 25.4)),
                               constrained_layout=True)

    fallback = palette.get("categorical", ["#1F4E79", "#C8553D", "#4C956C", "#F2A541", "#7A6C8F", "#2B6F77"])
    line_styles = ["-", "--", "-.", ":", "-", "--"]
    ordered_work = work.sort_values(epoch_col)
    x = pd.to_numeric(ordered_work[epoch_col], errors="coerce").to_numpy(dtype=float)
    finite_x = np.isfinite(x)
    x = x[finite_x]
    line_records = []
    for idx, col in enumerate(metric_cols):
        y = pd.to_numeric(ordered_work[col], errors="coerce").to_numpy(dtype=float)[finite_x]
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.sum() < 2:
            continue
        key = str(col).lower()
        is_validation = any(token in key for token in ("val", "valid", "test"))
        is_score = any(token in key for token in ("acc", "auc", "f1", "precision", "recall"))
        color = fallback[idx % len(fallback)]
        lw = 1.25 if is_validation else 0.95
        marker = "o" if is_validation else None
        markevery = max(1, int(mask.sum() / 7))
        ax.plot(
            x[mask], y[mask],
            color=color,
            lw=lw,
            ls=line_styles[idx % len(line_styles)],
            marker=marker,
            markersize=2.8,
            markevery=markevery,
            label=display(col, col_map),
            alpha=0.96 if is_validation else 0.78,
            zorder=4 if is_validation else 3,
        )
        line_records.append((col, key, x[mask], y[mask], is_score, color))

    train_loss_col = next((col for col in metric_cols if "loss" in str(col).lower() and not any(t in str(col).lower() for t in ("val", "valid", "test"))), None)
    val_loss_col = next((col for col in metric_cols if "loss" in str(col).lower() and any(t in str(col).lower() for t in ("val", "valid", "test"))), None)
    if train_loss_col and val_loss_col:
        train = pd.to_numeric(ordered_work[train_loss_col], errors="coerce").to_numpy(dtype=float)[finite_x]
        val = pd.to_numeric(ordered_work[val_loss_col], errors="coerce").to_numpy(dtype=float)[finite_x]
        gap_mask = np.isfinite(x) & np.isfinite(train) & np.isfinite(val)
        if gap_mask.sum() >= 2:
            ax.fill_between(x[gap_mask], train[gap_mask], val[gap_mask],
                            color="#B00000", alpha=0.08, linewidth=0, label="generalization gap")

    decision = None
    if val_loss_col:
        y = pd.to_numeric(ordered_work[val_loss_col], errors="coerce").to_numpy(dtype=float)[finite_x]
        mask = np.isfinite(x) & np.isfinite(y)
        if mask.any():
            pos = int(np.nanargmin(y[mask]))
            decision = ("best val loss", x[mask][pos], y[mask][pos], "#B00000")
    if decision is None:
        score_records = [rec for rec in line_records if rec[4]]
        if score_records:
            col, key, xs, ys, _, color = score_records[-1]
            pos = int(np.nanargmax(ys))
            decision = (f"best {display(col, col_map)}", xs[pos], ys[pos], color)
    if decision is not None:
        label, best_x, best_y, color = decision
        ax.axvline(best_x, color="#333333", lw=0.65, ls="--", alpha=0.62, zorder=1)
        ax.scatter([best_x], [best_y], s=38, color=color, edgecolor="white", linewidth=0.55, zorder=7)
        ax.text(
            0.98, 0.07, f"{label}\nepoch={best_x:g}\nvalue={best_y:.3g}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.2,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                      edgecolor="#333333", linewidth=0.45, alpha=0.92),
            zorder=8,
        )

    if line_records:
        first = line_records[0]
        last_delta = first[3][-1] - first[3][0]
        ax.text(0.04, 0.94, f"training history\ncurves={len(line_records)}\nΔ={last_delta:+.2g}",
                transform=ax.transAxes, ha="left", va="top", fontsize=5.2,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                          edgecolor="#CCCCCC", linewidth=0.35, alpha=0.88))

    ax.set_xlabel(display(epoch_col, col_map))
    ax.set_ylabel("Metric value")
    ax.xaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.25)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.3, alpha=0.20)
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        if standalone and ax.figure is not None:
            legend = ax.figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02),
                                      ncol=min(4, len(labels)), fontsize=5, frameon=True,
                                      fancybox=True, borderpad=0.25, handlelength=1.6, columnspacing=0.8)
            legend.set_gid("scifig_shared_legend")
            legend.get_frame().set_linewidth(0.35)
            legend.get_frame().set_edgecolor("#333333")
            legend.get_frame().set_alpha(0.94)
            try:
                if hasattr(ax.figure, "set_layout_engine"):
                    ax.figure.set_layout_engine(None)
                else:
                    ax.figure.set_constrained_layout(False)
            except Exception:
                pass
            sp = ax.figure.subplotpars
            ax.figure.subplots_adjust(left=max(sp.left, 0.16), bottom=max(sp.bottom, 0.30), right=min(sp.right, 0.96))
        else:
            ax.legend(loc="upper right", ncol=min(4, len(labels)),
                      frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "training_curve")
    return ax
