"""Dedicated ML-family generators for the chart registry.

roc              — ROC curve (TPR vs FPR + diagonal reference)
pr_curve         — Precision-Recall curve
calibration      — Calibration curve (predicted vs observed frequency)
training_curve   — Training / validation loss over epochs
"""

from __future__ import annotations

from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .registry import register_chart


def _get_ax(ax: Any = None) -> Any:
    if ax is not None:
        return ax
    _, new_ax = plt.subplots(figsize=(89 / 25.4, 60 / 25.4), constrained_layout=True)
    return new_ax


def _roles(profile: Any) -> dict[str, str]:
    if hasattr(profile, "semantic_roles"):
        return dict(profile.semantic_roles)
    return dict(profile.get("semanticRoles", profile.get("semantic_roles", {})))


def _categorical_palette(palette: dict[str, Any]) -> list[str]:
    return list(palette.get("categorical",
                           ["#000000", "#E69F00", "#56B4E9", "#009E73",
                            "#F0E442", "#0072B2"]))


def _numeric_columns(df: pd.DataFrame) -> list[str]:
    return [str(c) for c in df.select_dtypes(include=[np.number]).columns]


def _first_valid(df: pd.DataFrame, *candidates: Optional[str]) -> Optional[str]:
    columns = {str(c) for c in df.columns}
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _status(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    return ax


def _binary_score_label(
    df: pd.DataFrame,
    score_col: str,
    label_col: str,
    *,
    probability: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    scores = pd.to_numeric(df[score_col], errors="coerce").to_numpy(dtype=float)
    labels = pd.to_numeric(df[label_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(scores) & np.isfinite(labels)
    if probability:
        valid &= (scores >= 0.0) & (scores <= 1.0)
    scores, labels = scores[valid], labels[valid]
    binary = np.isin(labels, [0.0, 1.0])
    return scores[binary], labels[binary].astype(int)


def _score_label_columns(df: pd.DataFrame, profile: Any) -> tuple[str | None, str | None]:
    roles = _roles(profile)
    numeric = _numeric_columns(df)
    score_col = _first_valid(
        df,
        roles.get("score"),
        roles.get("predicted"),
        roles.get("value"),
        roles.get("x"),
        "y_score",
        "probability",
        "score",
        numeric[0] if numeric else None,
    )
    label_col = _first_valid(
        df,
        roles.get("actual"),
        roles.get("label"),
        roles.get("y"),
        "y_true",
        "target",
        "actual",
        numeric[1] if len(numeric) > 1 else None,
    )
    if label_col == score_col:
        label_col = next((col for col in numeric if col != score_col), None)
    return score_col, label_col


def _binary_frame(df: pd.DataFrame, data_profile: Any) -> tuple[np.ndarray, np.ndarray, str | None]:
    score_col, label_col = _score_label_columns(df, data_profile)
    if score_col not in df.columns or label_col not in df.columns:
        return np.array([]), np.array([], dtype=int), "Need score + label columns"
    scores, labels = _binary_score_label(df, score_col, label_col, probability=True)
    if len(scores) == 0:
        scores, labels = _binary_score_label(df, score_col, label_col)
    if len(scores) == 0:
        return scores, labels, "Need finite score + binary label values"
    if labels.sum() == 0 or labels.sum() == len(labels):
        return scores, labels, "Need both positive and negative labels"
    return scores, labels, None


def _roc_points(scores: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    distinct = np.r_[np.where(np.diff(sorted_scores) != 0)[0], len(sorted_scores) - 1]
    tp = np.cumsum(sorted_labels)[distinct]
    fp = (1 + distinct) - tp
    total_pos = labels.sum()
    total_neg = len(labels) - total_pos
    return np.concatenate([[0.0], fp / total_neg, [1.0]]), np.concatenate([[0.0], tp / total_pos, [1.0]])


def _pr_points(scores: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    distinct = np.r_[np.where(np.diff(sorted_scores) != 0)[0], len(sorted_scores) - 1]
    tp = np.cumsum(sorted_labels)[distinct]
    fp = (1 + distinct) - tp
    precision = tp / (tp + fp + 1e-300)
    recall = tp / (labels.sum() + 1e-300)
    return np.concatenate([[0.0], recall]), np.concatenate([[labels.mean()], precision])


def _simple_auc(x: np.ndarray, y: np.ndarray) -> float:
    order = np.argsort(x)
    return float(np.trapezoid(y[order], x[order]))


# -- ROC curve ----------------------------------------------------------------

@register_chart("roc")
def gen_roc(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
            rc_params: dict[str, Any], palette: dict[str, Any],
            col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """ROC curve (TPR vs FPR) with diagonal AUC=0.5 reference line."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    score_col = roles.get("score") or roles.get("predicted") or roles.get("value") or roles.get("x") or (numeric[0] if numeric else None)
    label_col = roles.get("actual") or roles.get("label") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if score_col not in df.columns or label_col not in df.columns:
        return _status(ax, "ROC", "Need score + label columns")

    scores, labels = _binary_score_label(df, score_col, label_col)
    if len(scores) == 0:
        return _status(ax, "ROC", "Need finite score + binary label values")
    total_pos = int(labels.sum())
    total_neg = int(len(labels) - total_pos)
    if total_pos == 0 or total_neg == 0:
        return _status(ax, "ROC", "Need both positive and negative labels")

    # BUG-12 fix: aggregate by unique score threshold (descending) so curves are
    # invariant to input row order on ties. Previous per-row cumsum produced
    # different curves for label=[1,0] vs [0,1] on tied scores.
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    # Identify last index for each distinct score (run-length on sorted scores).
    distinct = np.r_[np.where(np.diff(sorted_scores) != 0)[0], len(sorted_scores) - 1]
    tps_running = np.cumsum(sorted_labels)[distinct]
    fps_running = (1 + distinct) - tps_running
    tpr = np.concatenate([[0.0], tps_running / total_pos, [1.0]])
    fpr = np.concatenate([[0.0], fps_running / total_neg, [1.0]])
    ax.plot(fpr, tpr, color=colors[5 % len(colors)], lw=1.1, label="ROC")
    ax.plot([0, 1], [0, 1], color="#888888", lw=0.6, ls="--")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


# -- Precision-Recall ---------------------------------------------------------

@register_chart("pr_curve")
def gen_pr_curve(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                 rc_params: dict[str, Any], palette: dict[str, Any],
                 col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Precision-Recall curve."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    score_col = roles.get("score") or roles.get("predicted") or roles.get("value") or roles.get("x") or (numeric[0] if numeric else None)
    label_col = roles.get("actual") or roles.get("label") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if score_col not in df.columns or label_col not in df.columns:
        return _status(ax, "Precision-Recall", "Need score + label columns")

    scores, labels = _binary_score_label(df, score_col, label_col)
    if len(scores) == 0:
        return _status(ax, "Precision-Recall", "Need finite score + binary label values")
    total_pos = int(labels.sum())
    total_neg = int(len(labels) - total_pos)
    if total_pos == 0 or total_neg == 0:
        return _status(ax, "Precision-Recall", "Need both positive and negative labels")
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    distinct = np.r_[np.where(np.diff(sorted_scores) != 0)[0], len(sorted_scores) - 1]
    tp = np.cumsum(sorted_labels)[distinct]
    fp = (1 + distinct) - tp
    precision = tp / (tp + fp + 1e-300)
    recall = tp / (total_pos + 1e-300)
    precision = np.concatenate([[total_pos / len(labels)], precision])
    recall = np.concatenate([[0], recall])
    ax.plot(recall, precision, color=colors[5 % len(colors)], lw=1.1, label="PR curve")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


# -- Calibration curve --------------------------------------------------------

@register_chart("calibration")
def gen_calibration(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                    rc_params: dict[str, Any], palette: dict[str, Any],
                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Calibration curve — predicted probability vs observed frequency,
    with perfect-calibration diagonal reference."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    pred_col = roles.get("score") or roles.get("predicted") or roles.get("value") or roles.get("x") or (numeric[0] if numeric else None)
    label_col = roles.get("actual") or roles.get("label") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if pred_col not in df.columns or label_col not in df.columns:
        return _status(ax, "Calibration", "Need predicted + label columns")

    p, y = _binary_score_label(df, pred_col, label_col, probability=True)
    if len(p) < 5:
        return _status(ax, "Calibration", "Need >=5 valid probability-label pairs")

    edges = np.linspace(0, 1, 8)
    bin_idx = np.digitize(p, edges[1:-1])
    mean_p: list[float] = []
    frac_pos: list[float] = []
    for i in range(len(edges) - 1):
        mask = bin_idx == i
        if mask.sum() > 0:
            mean_p.append(float(p[mask].mean()))
            frac_pos.append(float(y[mask].mean()))
    ax.plot(mean_p, frac_pos, "o-", color=colors[5 % len(colors)], lw=1.1,
            ms=4, label="Calibration")
    ax.plot([0, 1], [0, 1], color="#888888", lw=0.6, ls="--")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title("Calibration", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("classifier_validation_board")
def gen_classifier_validation_board(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                                    rc_params: dict[str, Any], palette: dict[str, Any],
                                    col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Compact classifier board: ROC, PR, calibration, and threshold summary."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    scores, labels, error = _binary_frame(df, data_profile)
    if error:
        return _status(ax, "Classifier validation board", error)
    ax.set_axis_off()
    roc_ax = ax.inset_axes([0.06, 0.54, 0.38, 0.36])
    pr_ax = ax.inset_axes([0.56, 0.54, 0.38, 0.36])
    cal_ax = ax.inset_axes([0.06, 0.08, 0.38, 0.34])
    summary_ax = ax.inset_axes([0.56, 0.08, 0.38, 0.34])

    fpr, tpr = _roc_points(scores, labels)
    recall, precision = _pr_points(scores, labels)
    roc_ax.plot(fpr, tpr, color=colors[5 % len(colors)], lw=1.0)
    roc_ax.plot([0, 1], [0, 1], color="#999999", lw=0.55, ls="--")
    roc_ax.set_title("ROC", fontsize=6, pad=2)
    roc_ax.set_xlabel("FPR", fontsize=5)
    roc_ax.set_ylabel("TPR", fontsize=5)
    roc_ax.tick_params(labelsize=5, length=2)
    _decorate_axes(roc_ax)

    pr_ax.plot(recall, precision, color=colors[1 % len(colors)], lw=1.0)
    pr_ax.axhline(labels.mean(), color="#999999", lw=0.55, ls="--")
    pr_ax.set_title("Precision-Recall", fontsize=6, pad=2)
    pr_ax.set_xlabel("Recall", fontsize=5)
    pr_ax.set_ylabel("Precision", fontsize=5)
    pr_ax.tick_params(labelsize=5, length=2)
    _decorate_axes(pr_ax)

    edges = np.linspace(0, 1, 7)
    bin_idx = np.digitize(np.clip(scores, 0, 1), edges[1:-1])
    mean_p: list[float] = []
    frac_pos: list[float] = []
    for i in range(len(edges) - 1):
        mask = bin_idx == i
        if mask.sum():
            mean_p.append(float(scores[mask].mean()))
            frac_pos.append(float(labels[mask].mean()))
    cal_ax.plot(mean_p, frac_pos, "o-", color=colors[2 % len(colors)], ms=3, lw=0.8)
    cal_ax.plot([0, 1], [0, 1], color="#999999", lw=0.55, ls="--")
    cal_ax.set_title("Calibration", fontsize=6, pad=2)
    cal_ax.set_xlabel("Pred.", fontsize=5)
    cal_ax.set_ylabel("Obs.", fontsize=5)
    cal_ax.tick_params(labelsize=5, length=2)
    _decorate_axes(cal_ax)

    pred = (scores >= 0.5).astype(int)
    tp = int(((pred == 1) & (labels == 1)).sum())
    fp = int(((pred == 1) & (labels == 0)).sum())
    tn = int(((pred == 0) & (labels == 0)).sum())
    fn = int(((pred == 0) & (labels == 1)).sum())
    acc = (tp + tn) / len(labels)
    roc_auc = _simple_auc(fpr, tpr)
    pr_auc = _simple_auc(recall, precision)
    summary_ax.barh([3, 2, 1], [roc_auc, pr_auc, acc],
                    color=[colors[5 % len(colors)], colors[1 % len(colors)], colors[2 % len(colors)]],
                    height=0.55)
    summary_ax.set_yticks([3, 2, 1], ["ROC AUC", "PR AUC", "Accuracy"], fontsize=5)
    summary_ax.set_xlim(0, 1)
    summary_ax.text(0.02, 0.08, f"TP={tp} FP={fp}\nFN={fn} TN={tn}", transform=summary_ax.transAxes,
                    ha="left", va="bottom", fontsize=5)
    summary_ax.set_title("Summary", fontsize=6, pad=2)
    summary_ax.tick_params(labelsize=5, length=2)
    _decorate_axes(summary_ax)

    ax.set_title("Classifier validation board", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("rf_classifier_report_board")
def gen_rf_classifier_report_board(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                                   rc_params: dict[str, Any], palette: dict[str, Any],
                                   col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Random-forest report board with validation curves plus feature importance."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    gen_classifier_validation_board(df, data_profile, chart_plan, rc_params, palette, col_map=col_map, ax=ax)
    importance_ax = ax.inset_axes([0.64, 0.14, 0.30, 0.22])
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    feature_col = _first_valid(df, roles.get("feature_id"), roles.get("label"), "feature", "variable")
    importance_col = _first_valid(df, roles.get("importance"), "importance", "mean_abs_shap", "gain")
    if feature_col in df.columns and importance_col in df.columns:
        frame = df[[feature_col, importance_col]].copy()
        frame[importance_col] = pd.to_numeric(frame[importance_col], errors="coerce")
        frame = frame.replace([np.inf, -np.inf], np.nan).dropna().groupby(feature_col, sort=False)[importance_col].mean()
        frame = frame.sort_values(ascending=True).tail(6)
        if not frame.empty:
            importance_ax.barh(np.arange(len(frame)), frame.to_numpy(dtype=float), color=colors[4 % len(colors)])
            importance_ax.set_yticks(np.arange(len(frame)), [str(idx)[:12] for idx in frame.index], fontsize=5)
            importance_ax.set_title("Importance", fontsize=6, pad=2)
            importance_ax.tick_params(labelsize=5, length=2)
            _decorate_axes(importance_ax)
            return ax
    importance_ax.set_axis_off()
    if numeric:
        importance_ax.text(0.5, 0.5, "Feature importance\nnot provided",
                           ha="center", va="center", fontsize=5, transform=importance_ax.transAxes)
    return ax


# -- Training curve -----------------------------------------------------------

@register_chart("training_curve")
def gen_training_curve(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                       rc_params: dict[str, Any], palette: dict[str, Any],
                       col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Training and validation loss curves over epochs."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    epoch_col = roles.get("epoch") or roles.get("x") or (numeric[0] if numeric else None)
    train_col = roles.get("train_loss") or roles.get("value") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    val_col = roles.get("val_loss") or (numeric[2] if len(numeric) > 2 else None)
    if epoch_col not in df.columns or train_col not in df.columns:
        ax.text(0.5, 0.5, "Need epoch + train_loss columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Training curve", loc="center", fontweight="bold", pad=5)
        return ax

    x = pd.to_numeric(df[epoch_col], errors="coerce")
    y_train = pd.to_numeric(df[train_col], errors="coerce")
    ax.plot(x, y_train, color=colors[5 % len(colors)], lw=1.1, label="Training loss")
    if val_col and val_col in df.columns:
        y_val = pd.to_numeric(df[val_col], errors="coerce")
        ax.plot(x, y_val, color=colors[1 % len(colors)], lw=1.1, ls="--", label="Validation loss")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Training curve", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
