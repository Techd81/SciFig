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


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


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
    score_col = roles.get("score") or roles.get("predicted") or roles.get("x") or (numeric[0] if numeric else None)
    label_col = roles.get("label") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if score_col not in df.columns or label_col not in df.columns:
        ax.text(0.5, 0.5, "Need score + label columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("ROC", loc="center", fontweight="bold", pad=5)
        return ax

    scores = pd.to_numeric(df[score_col], errors="coerce").to_numpy()
    labels = pd.to_numeric(df[label_col], errors="coerce").to_numpy(dtype=int)
    valid = (~np.isnan(scores)) & np.isfinite(scores)
    scores, labels = scores[valid], labels[valid]
    order = np.argsort(-scores)
    tps = labels[order].cumsum()
    fps = (1 - labels[order]).cumsum()
    total_pos = labels.sum()
    total_neg = len(labels) - total_pos
    if total_pos == 0 or total_neg == 0:
        ax.text(0.5, 0.5, "Need both positive and negative labels",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("ROC", loc="center", fontweight="bold", pad=5)
        return ax

    tpr = np.concatenate([[0], tps / total_pos, [1]])
    fpr = np.concatenate([[0], fps / total_neg, [1]])
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
    score_col = roles.get("score") or roles.get("predicted") or roles.get("x") or (numeric[0] if numeric else None)
    label_col = roles.get("label") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if score_col not in df.columns or label_col not in df.columns:
        ax.text(0.5, 0.5, "Need score + label columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Precision-Recall", loc="center", fontweight="bold", pad=5)
        return ax

    scores = pd.to_numeric(df[score_col], errors="coerce").to_numpy()
    labels = pd.to_numeric(df[label_col], errors="coerce").to_numpy(dtype=int)
    valid = (~np.isnan(scores)) & np.isfinite(scores)
    scores, labels = scores[valid], labels[valid]
    order = np.argsort(-scores)
    tp = labels[order].cumsum()
    fp = (1 - labels[order]).cumsum()
    precision = tp / (tp + fp + 1e-300)
    total_pos = labels.sum()
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
    pred_col = roles.get("predicted") or roles.get("x") or (numeric[0] if numeric else None)
    label_col = roles.get("label") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if pred_col not in df.columns or label_col not in df.columns:
        ax.text(0.5, 0.5, "Need predicted + label columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Calibration", loc="center", fontweight="bold", pad=5)
        return ax

    p = pd.to_numeric(df[pred_col], errors="coerce").to_numpy()
    y = pd.to_numeric(df[label_col], errors="coerce").to_numpy(dtype=float)
    valid = (~np.isnan(p)) & (p >= 0) & (p <= 1)
    p, y = p[valid], y[valid]
    if len(p) < 5:
        ax.text(0.5, 0.5, "Need >=5 valid predicted-label pairs",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Calibration", loc="center", fontweight="bold", pad=5)
        return ax

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
