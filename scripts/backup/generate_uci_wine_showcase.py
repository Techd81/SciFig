#!/usr/bin/env python3
"""
Generate a UCI Wine machine-learning diagnostics showcase bundle.

Input data:
    D:/SciFig/.workflow/.scratchpad/test-data/raw/uci_wine.csv

Outputs:
    figures/*.png, figures/*.pdf, figures/*.svg
    source_data/*.csv
    reports/render_contracts.json, reports/render_qa.json,
    reports/panel_manifest.json, reports/stats_report.md, reports/metadata.json
"""

from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
from PIL import Image, ImageStat
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import f_classif
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler


warnings.filterwarnings("ignore", category=UserWarning)

DATA_PATH = Path(r"D:\SciFig\.workflow\.scratchpad\test-data\raw\uci_wine.csv")
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(r"D:\test_scifig")
SKILL_ROOT = PROJECT_ROOT / ".codex" / "skills" / "scifig-generate"
FIG_DIR = RUN_ROOT / "figures"
REPORT_DIR = RUN_ROOT / "reports"
SOURCE_DIR = RUN_ROOT / "source_data"
for directory in (FIG_DIR, REPORT_DIR, SOURCE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

HELPER_SOURCE_PATH = SKILL_ROOT / "phases" / "code-gen" / "helpers.py"
TEMPLATE_HELPER_DIR = HELPER_SOURCE_PATH.parent
sys.path.insert(0, str(TEMPLATE_HELPER_DIR))

helper_source = HELPER_SOURCE_PATH.read_text(encoding="utf-8")
if helper_source.lstrip().startswith("```python"):
    helper_lines = helper_source.splitlines()[1:]
    if helper_lines and helper_lines[-1].strip() == "```":
        helper_lines = helper_lines[:-1]
    helper_source = "\n".join(helper_lines)
exec(helper_source, globals())

from template_mining_helpers import (  # noqa: E402
    add_metric_box,
    apply_journal_kernel,
    apply_scatter_regression_floor,
)


RASTER_DPI = 1200
RNG = np.random.default_rng(20260502)

SKILL_CALL = (
    '$scifig-generate FILE: "D:\\SciFig\\.workflow\\.scratchpad\\test-data\\raw\\uci_wine.csv" '
    'OUTPUT_DIR: "D:\\test_scifig\\output\\maestro_scifig_showcase_20260502\\uci_wine" '
    "MODE: auto LANGUAGE: zh-cn PREFERENCES: machine-learning dataset diagnostics style, "
    "semantic class colors, 1200 dpi, detail preserving, maximum visual impact without overlap. "
    "MUST_HAVE: at least one single-panel hero figure and one multi-panel feature atlas; infer UCI "
    "wine column names if headerless; include class separation, correlation/feature structure, and "
    "data-quality context; use bottom-center figure legend outside panels; avoid colorbar-panel overlap; "
    "export png pdf svg; write source_data, panel_manifest, stats_report, metadata, and render_contracts.json."
)

JOURNAL_PROFILE = {
    "style": "machine-learning dataset diagnostics",
    "font_family": ["Arial", "Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "font_size_body_pt": 6.7,
    "font_size_small_pt": 5.5,
    "font_size_panel_label_pt": 8.0,
    "axis_linewidth_pt": 0.65,
    "max_text_font_size_pt": 10.5,
    "max_panel_label_font_size_pt": 10.5,
}

FEATURE_COLUMNS = [
    "alcohol",
    "malic_acid",
    "ash",
    "alcalinity_of_ash",
    "magnesium",
    "total_phenols",
    "flavanoids",
    "nonflavanoid_phenols",
    "proanthocyanins",
    "color_intensity",
    "hue",
    "od280_od315_of_diluted_wines",
    "proline",
]

FEATURE_SHORT = {
    "alcohol": "Alcohol",
    "malic_acid": "Malic",
    "ash": "Ash",
    "alcalinity_of_ash": "AlkAsh",
    "magnesium": "Mg",
    "total_phenols": "Phenols",
    "flavanoids": "Flav",
    "nonflavanoid_phenols": "NonFlav",
    "proanthocyanins": "Proanth",
    "color_intensity": "Color",
    "hue": "Hue",
    "od280_od315_of_diluted_wines": "OD280",
    "proline": "Proline",
}

CLASS_COLORS = {
    1: "#E64B35",
    2: "#4DBBD5",
    3: "#00A087",
}

LABEL_BOX = {
    "boxstyle": "round,pad=0.18",
    "facecolor": "white",
    "edgecolor": "none",
    "alpha": 0.88,
}


def fmt_int(value: int | float) -> str:
    return f"{int(round(float(value))):,}"


def fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def class_label(class_id: int) -> str:
    return f"Cultivar {int(class_id)}"


def infer_headerless_uci_wine(raw: pd.DataFrame) -> bool:
    return raw.shape[1] == 14 and set(pd.to_numeric(raw.iloc[:, 0], errors="coerce").dropna().unique()).issubset({1, 2, 3})


def load_data() -> pd.DataFrame:
    raw = pd.read_csv(DATA_PATH, header=None)
    if not infer_headerless_uci_wine(raw):
        maybe = pd.read_csv(DATA_PATH)
        if "class" in maybe.columns and set(FEATURE_COLUMNS).issubset(maybe.columns):
            df = maybe[["class", *FEATURE_COLUMNS]].copy()
        else:
            raise ValueError("Input is neither headerless UCI Wine nor a named UCI Wine table")
    else:
        df = raw.copy()
        df.columns = ["class", *FEATURE_COLUMNS]
    for col in ["class", *FEATURE_COLUMNS]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["class"] = df["class"].astype("Int64")
    df["class_label"] = df["class"].map(lambda v: class_label(int(v)) if not pd.isna(v) else "Missing class")
    return df


def standardized_matrix(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    features = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = df["class"].to_numpy(dtype=int)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(features)
    return x_scaled, y, scaler


def compute_ml_diagnostics(df: pd.DataFrame) -> dict:
    x_scaled, y, _ = standardized_matrix(df)
    pca = PCA(n_components=2, random_state=20260502)
    pca_scores = pca.fit_transform(x_scaled)
    lda = LinearDiscriminantAnalysis(n_components=2)
    lda_scores = lda.fit_transform(x_scaled, y)
    f_values, p_values = f_classif(x_scaled, y)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=20260502)
    model = RandomForestClassifier(n_estimators=400, random_state=20260502, class_weight="balanced_subsample")
    cv_pred = cross_val_predict(model, x_scaled, y, cv=skf)
    balanced_acc = balanced_accuracy_score(y, cv_pred)
    return {
        "x_scaled": x_scaled,
        "y": y,
        "pca": pca,
        "pca_scores": pca_scores,
        "lda": lda,
        "lda_scores": lda_scores,
        "f_values": f_values,
        "p_values": p_values,
        "cv_pred": cv_pred,
        "balanced_accuracy": balanced_acc,
    }


def style_axis(ax, grid_axis: str = "both") -> None:
    ax.tick_params(length=2.5, width=0.55, pad=1.5, labelsize=5.5)
    ax.grid(True, axis=grid_axis, color="#DDE3EA", linewidth=0.35, linestyle="-", alpha=0.65, zorder=0)
    for spine in ax.spines.values():
        spine.set_linewidth(0.65)


def safe_panel_label(ax, label: str) -> None:
    artist = ax.text(
        0.015,
        0.985,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        fontweight="bold",
        color="#222222",
        zorder=30,
    )
    artist.set_gid("scifig_panel_label")


def covariance_ellipse(points: np.ndarray, *, n_std: float = 2.0, **kwargs) -> Ellipse | None:
    if points.shape[0] < 3:
        return None
    cov = np.cov(points.T)
    if not np.all(np.isfinite(cov)):
        return None
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    angle = math.degrees(math.atan2(vecs[1, 0], vecs[0, 0]))
    width, height = 2 * n_std * np.sqrt(np.maximum(vals, 1e-12))
    center = points.mean(axis=0)
    return Ellipse(xy=center, width=width, height=height, angle=angle, **kwargs)


def class_handles() -> list[Line2D]:
    return [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markersize=4.6,
            markerfacecolor=color,
            markeredgecolor="white",
            markeredgewidth=0.45,
            label=class_label(class_id),
        )
        for class_id, color in CLASS_COLORS.items()
    ]


def feature_order_by_correlation(df: pd.DataFrame) -> list[str]:
    corr = df[FEATURE_COLUMNS].corr(method="pearson").fillna(0.0)
    distance = 1 - corr.abs()
    np.fill_diagonal(distance.values, 0)
    condensed = squareform(distance.to_numpy(), checks=False)
    order = leaves_list(linkage(condensed, method="average"))
    return [FEATURE_COLUMNS[int(i)] for i in order]


def build_chart_plan(fig_key: str, panel_ids: list[str], chart_family: str, *, shared_legend: bool = True) -> dict:
    return {
        "primaryChart": chart_family,
        "secondaryCharts": [],
        "panelBlueprint": {
            "layout": {"recipe": "R0_single_panel" if len(panel_ids) == 1 else "R2_two_by_two_storyboard"},
            "panels": [{"id": pid, "role": "panel", "chart": chart_family} for pid in panel_ids],
            "requestedLayout": "single" if len(panel_ids) == 1 else "2x2",
            "finalLayout": "single" if len(panel_ids) == 1 else "2x2",
            "sharedLegend": shared_legend,
            "sharedColorbar": False,
        },
        "crowdingPlan": {
            "legendMode": "bottom_center",
            "legendPlacementPriority": ["bottom_center"],
            "legendAllowedModes": ["bottom_center"],
            "legendFrame": True,
            "legendFontSizePt": 7,
            "legendBottomAnchorY": 0.015,
            "legendBottomMarginMin": 0.06,
            "legendBottomMarginMax": 0.16,
            "maxLegendColumns": 3,
            "legendLabelMaxChars": 26,
            "maxDirectLabelsHero": 4,
            "maxDirectLabelsPerPanel": 4,
            "maxTextFontSizePt": JOURNAL_PROFILE["max_text_font_size_pt"],
            "maxPanelLabelFontSizePt": JOURNAL_PROFILE["max_panel_label_font_size_pt"],
            "minFigureInkFraction": 0.025,
            "maxFigureWhitespaceFraction": 0.88,
            "textDataOverlapThreshold": 0.30,
            "forbidNegativeAxesText": True,
        },
        "visualContentPlan": {
            "figureId": fig_key,
            "minTotalEnhancements": 4 if len(panel_ids) == 1 else 8,
            "minInPlotLabelsPerFigure": 1 if len(panel_ids) == 1 else 4,
            "minReferenceMotifsPerFigure": 2 if len(panel_ids) == 1 else 4,
            "referenceMotifsRequired": True,
            "exactMotifCoverageRequired": True,
            "templateMotifsRequired": False,
            "visualGrammarMotifs": [
                "alpha_layered_scatter",
                "colored_marker_edge",
                "metric_text_box",
                "zero_reference",
            ]
            if len(panel_ids) == 1
            else [
                "panel_labels",
                "consistent_palette",
                "feature_ordering",
                "metric_text_box",
                "zero_reference",
                "correlation_heatmap",
            ],
            "visualGrammarMotifsApplied": [
                "alpha_layered_scatter",
                "colored_marker_edge",
                "metric_text_box",
                "zero_reference",
            ]
            if len(panel_ids) == 1
            else [
                "panel_labels",
                "consistent_palette",
                "feature_ordering",
                "metric_text_box",
                "zero_reference",
                "correlation_heatmap",
            ],
            "appliedEnhancements": [],
            "inPlotExplanatoryLabelCount": 0,
            "referenceMotifCount": 0,
            "templateMotifCount": 0,
        },
        "templateCasePlan": {
            "narrativeArc": "hero" if len(panel_ids) == 1 else "multipanel_grid",
            "templateFamilies": ["ml_model_diagnostics", "marginal_joint", "heatmap_pairwise"],
            "techniqueRefs": [
                "template-mining/07-techniques/ml-model-diagnostics.md",
                "template-mining/07-techniques/marginal-joint.md",
                "template-mining/07-techniques/heatmap-pairwise.md",
            ],
        },
    }


def update_visual_counts(plan: dict, enhancements: list[str], labels: int, motifs: int) -> None:
    visual = plan.setdefault("visualContentPlan", {})
    visual["appliedEnhancements"] = list(dict.fromkeys(enhancements))
    visual["inPlotExplanatoryLabelCount"] = labels
    visual["referenceMotifCount"] = motifs


def validate_png(path: Path) -> dict:
    result = {
        "path": str(path.relative_to(RUN_ROOT)),
        "exists": path.exists(),
        "bytes": int(path.stat().st_size) if path.exists() else 0,
        "width": 0,
        "height": 0,
        "stddev": 0.0,
        "extrema": [0, 0],
        "inkFraction": 0.0,
        "nonblank": False,
        "error": "",
    }
    if not path.exists():
        result["error"] = "missing_png"
        return result
    try:
        with Image.open(path) as img:
            result["width"], result["height"] = [int(v) for v in img.size]
            probe = img.convert("L").resize((256, 256))
            stat = ImageStat.Stat(probe)
            extrema = probe.getextrema()
            arr = np.asarray(probe)
            ink_fraction = float((arr < 245).mean())
        result["stddev"] = float(stat.stddev[0])
        result["extrema"] = [int(extrema[0]), int(extrema[1])]
        result["inkFraction"] = ink_fraction
        result["nonblank"] = bool(
            result["bytes"] > 10000
            and result["width"] > 100
            and result["height"] > 100
            and result["stddev"] > 1.0
            and result["extrema"][0] < result["extrema"][1]
            and result["inkFraction"] > 0.005
        )
    except Exception as exc:  # pragma: no cover - fallback for minimal environments
        result["error"] = str(exc)
        result["nonblank"] = result["bytes"] > 10000
    return result


def save_figure(fig, axes: dict[str, plt.Axes], fig_key: str, plan: dict, *, adjust: dict) -> dict:
    fig.subplots_adjust(**adjust)
    legend_report = enforce_figure_legend_contract(
        fig,
        axes=axes,
        chartPlan=plan,
        journalProfile=JOURNAL_PROFILE,
        crowdingPlan=plan.get("crowdingPlan"),
        strict=False,
    )
    layout_report = audit_figure_layout_contract(
        fig,
        axes=axes,
        chartPlan=plan,
        journalProfile=JOURNAL_PROFILE,
        strict=False,
    )
    density_report = audit_visual_density_contract(plan, strict=False)

    outputs = {}
    for ext in ["png", "pdf", "svg"]:
        out_path = FIG_DIR / f"{fig_key}.{ext}"
        if ext == "png":
            fig.savefig(out_path, dpi=RASTER_DPI, bbox_inches="tight", facecolor="white")
        else:
            fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
        outputs[ext] = str(out_path.relative_to(RUN_ROOT))

    png_check = validate_png(FIG_DIR / f"{fig_key}.png")
    overlap_counts = {
        "legendOverlapCount": len(legend_report.get("overlapIssues", [])),
        "crossPanelOverlapCount": len(layout_report.get("crossPanelOverlapIssues", [])),
        "metricTableDataOverlapCount": int(layout_report.get("metricTableDataOverlapCount", 0)),
        "colorbarPanelOverlapCount": int(layout_report.get("colorbarPanelOverlapCount", 0)),
        "textDataOverlapCount": int(layout_report.get("textDataOverlapCount", 0)),
        "offCanvasArtistCount": int(layout_report.get("offCanvasArtistCount", 0)),
        "oversizedTextCount": int(layout_report.get("oversizedTextCount", 0)),
        "negativeAxesTextCount": int(layout_report.get("negativeAxesTextCount", 0)),
    }
    no_overlap = all(value == 0 for value in overlap_counts.values())
    hard_fail = bool(
        legend_report.get("legendContractFailures")
        or layout_report.get("layoutContractFailures")
        or density_report.get("contentDensityFailures")
        or int(legend_report.get("axisLegendRemainingCount", 0)) != 0
        or legend_report.get("legendModeUsed") not in ["bottom_center", "none"]
        or not legend_report.get("legendContractEnforced", False)
        or not layout_report.get("layoutContractEnforced", False)
        or not no_overlap
        or not png_check["nonblank"]
    )
    report = {
        "figure": fig_key,
        "paths": outputs,
        "legendContract": legend_report,
        "layoutContract": layout_report,
        "visualDensity": density_report,
        "customQa": {
            "hardFail": hard_fail,
            "noLegendPanelOverlap": overlap_counts["legendOverlapCount"] == 0,
            "noCrossPanelTextOverlap": overlap_counts["crossPanelOverlapCount"] == 0,
            "noMetricTableDataOverlap": overlap_counts["metricTableDataOverlapCount"] == 0,
            "noColorbarPanelOverlap": overlap_counts["colorbarPanelOverlapCount"] == 0,
            "noTextDataOverlap": overlap_counts["textDataOverlapCount"] == 0,
            "pngNonblank": png_check["nonblank"],
            "pngCheck": png_check,
            "overlapCounts": overlap_counts,
        },
        "legendContractEnforced": legend_report.get("legendContractEnforced", False),
        "layoutContractEnforced": layout_report.get("layoutContractEnforced", False),
        "legendOutsidePlotArea": legend_report.get("legendOutsidePlotArea", True),
        "axisLegendRemainingCount": legend_report.get("axisLegendRemainingCount", 0),
        "legendModeUsed": legend_report.get("legendModeUsed", "none"),
        "figureLegendCount": len(fig.legends),
        "layoutContractFailures": layout_report.get("layoutContractFailures", []),
        "colorbarPanelOverlapCount": overlap_counts["colorbarPanelOverlapCount"],
        "textDataOverlapCount": overlap_counts["textDataOverlapCount"],
        "hardFail": hard_fail,
    }
    plt.close(fig)
    return report


def figure_class_separation_hero(df: pd.DataFrame, diagnostics: dict) -> tuple[dict, pd.DataFrame]:
    apply_journal_kernel("hero", JOURNAL_PROFILE)
    scores = diagnostics["lda_scores"]
    y = diagnostics["y"]
    plot_df = pd.DataFrame(
        {
            "class": y,
            "class_label": [class_label(v) for v in y],
            "lda1": scores[:, 0],
            "lda2": scores[:, 1],
            "pca1": diagnostics["pca_scores"][:, 0],
            "pca2": diagnostics["pca_scores"][:, 1],
        }
    )
    fig, ax = plt.subplots(figsize=(5.8, 5.25))
    style_axis(ax)
    ax.axhline(0, color="#7F7F7F", linestyle="--", linewidth=0.7, zorder=1)
    ax.axvline(0, color="#7F7F7F", linestyle="--", linewidth=0.7, zorder=1)

    for class_id in sorted(CLASS_COLORS):
        mask = y == class_id
        color = CLASS_COLORS[class_id]
        points = scores[mask]
        ellipse = covariance_ellipse(
            points,
            n_std=1.8,
            facecolor=color,
            edgecolor=color,
            linewidth=1.0,
            alpha=0.13,
            zorder=2,
        )
        if ellipse is not None:
            ax.add_patch(ellipse)
        ax.scatter(
            points[:, 0],
            points[:, 1],
            s=34,
            c=color,
            edgecolors="white",
            linewidths=0.55,
            alpha=0.88,
            label=class_label(class_id),
            zorder=4,
        )
        centroid = points.mean(axis=0)
        ax.scatter(
            [centroid[0]],
            [centroid[1]],
            s=115,
            marker="*",
            c=color,
            edgecolors="#222222",
            linewidths=0.65,
            zorder=8,
        )

    lda_ratio = diagnostics["lda"].explained_variance_ratio_
    add_metric_box(
        ax,
        {
            "n": fmt_int(len(df)),
            "classes": df["class"].nunique(),
            "5-fold RF balanced acc": diagnostics["balanced_accuracy"],
            "LDA variance": f"{lda_ratio[0] * 100:.1f}%/{lda_ratio[1] * 100:.1f}%",
        },
        loc="top_right",
        fontsize=5.4,
        pad=0.18,
    )
    safe_panel_label(ax, "A")
    ax.set_title("UCI Wine cultivar separation: supervised LDA map", fontsize=8.4, fontweight="bold", pad=7, loc="center")
    ax.set_xlabel(f"LD1 ({lda_ratio[0] * 100:.1f}% discriminant variance)")
    ax.set_ylabel(f"LD2 ({lda_ratio[1] * 100:.1f}% discriminant variance)")
    ax.legend(handles=class_handles(), loc="upper center", frameon=False)
    plan = build_chart_plan("uci_wine_class_separation_hero", ["A"], "lda_class_separation_hero")
    update_visual_counts(
        plan,
        [
            "supervised_lda_embedding",
            "class_semantic_colors",
            "white_edge_markers",
            "class_covariance_ellipses",
            "centroid_star_markers",
            "zero_reference_crosshair",
            "metric_text_box",
        ],
        labels=1,
        motifs=4,
    )
    report = save_figure(
        fig,
        {"A": ax},
        "uci_wine_class_separation_hero",
        plan,
        adjust={"left": 0.12, "right": 0.98, "top": 0.90, "bottom": 0.08},
    )
    return report, plot_df


def plot_correlation_panel(ax, df: pd.DataFrame, feature_order: list[str]) -> pd.DataFrame:
    corr = df[feature_order].corr(method="pearson")
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1, interpolation="nearest", zorder=1)
    del im
    labels = [FEATURE_SHORT[f] for f in feature_order]
    ax.set_xticks(np.arange(len(feature_order)))
    ax.set_yticks(np.arange(len(feature_order)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=4.8)
    ax.set_yticklabels(labels, fontsize=4.8)
    ax.tick_params(length=0)
    ax.set_title("Feature correlation structure", fontsize=7.4, fontweight="bold", pad=5, loc="center")
    for spine in ax.spines.values():
        spine.set_visible(False)
    upper = corr.where(np.triu(np.ones(corr.shape), 1).astype(bool)).stack().abs().sort_values(ascending=False)
    top_pairs = upper.head(3)
    pair_lines = [f"{FEATURE_SHORT[a]}-{FEATURE_SHORT[b]}: r={corr.loc[a, b]:.2f}" for (a, b), _ in top_pairs.items()]
    add_metric_box(ax, {"top |r| pairs": "\n".join(pair_lines)}, loc="bottom_right", fontsize=4.7, pad=0.12)
    return corr


def plot_fingerprint_panel(ax, df: pd.DataFrame, diagnostics: dict, feature_order: list[str]) -> pd.DataFrame:
    x_scaled = pd.DataFrame(diagnostics["x_scaled"], columns=FEATURE_COLUMNS)
    x_scaled["class"] = df["class"].to_numpy()
    class_means = x_scaled.groupby("class")[feature_order].mean()
    xs = np.arange(len(feature_order))
    for class_id, row in class_means.iterrows():
        ax.plot(
            xs,
            row.to_numpy(),
            color=CLASS_COLORS[int(class_id)],
            linewidth=1.4,
            marker="o",
            markersize=3.3,
            markeredgecolor="white",
            markeredgewidth=0.35,
            label=class_label(int(class_id)),
            zorder=4,
        )
        ax.fill_between(xs, 0, row.to_numpy(), color=CLASS_COLORS[int(class_id)], alpha=0.055, zorder=1)
    ax.axhline(0, color="#222222", linestyle="--", linewidth=0.75, zorder=3)
    ax.set_xticks(xs)
    ax.set_xticklabels([FEATURE_SHORT[f] for f in feature_order], rotation=35, ha="right", fontsize=4.9)
    ax.set_ylabel("Class mean z-score")
    ax.set_title("Cultivar chemical fingerprints", fontsize=7.4, fontweight="bold", pad=5, loc="center")
    style_axis(ax)
    return class_means.reset_index()


def plot_feature_separation_panel(ax, df: pd.DataFrame, diagnostics: dict) -> pd.DataFrame:
    f_df = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "feature_short": [FEATURE_SHORT[f] for f in FEATURE_COLUMNS],
            "anova_f": diagnostics["f_values"],
            "anova_p": diagnostics["p_values"],
        }
    ).sort_values("anova_f", ascending=False)
    top = f_df.head(9).iloc[::-1].copy()
    y_pos = np.arange(len(top))
    max_f = float(top["anova_f"].max())
    colors = plt.cm.YlGnBu(np.linspace(0.35, 0.88, len(top)))
    ax.hlines(y_pos, 0, top["anova_f"], color="#AAB7C4", linewidth=1.0, zorder=1)
    ax.scatter(top["anova_f"], y_pos, s=42, c=colors, edgecolors="white", linewidths=0.45, zorder=4)
    for idx, (_, row) in enumerate(top.iterrows()):
        ax.text(row["anova_f"] + max_f * 0.015, idx, f"{row['anova_f']:.0f}", va="center", ha="left", fontsize=5.0)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top["feature_short"], fontsize=5.3)
    ax.set_xlabel("ANOVA F-statistic across classes")
    ax.set_title("Top discriminative feature signals", fontsize=7.4, fontweight="bold", pad=5, loc="center")
    ax.set_xlim(0, max_f * 1.16)
    style_axis(ax, grid_axis="x")
    add_metric_box(ax, {"top feature": top.iloc[-1]["feature_short"], "features ranked": len(f_df)}, loc="bottom_right", fontsize=4.8, pad=0.12)
    return f_df


def plot_quality_panel(ax, df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    class_counts = df["class"].value_counts().sort_index()
    feature_missing = df[FEATURE_COLUMNS].isna().mean()
    duplicate_rows = int(df.duplicated(subset=["class", *FEATURE_COLUMNS]).sum())
    quality_rows = [
        ("Rows retained", n, 100.0),
        ("Numeric features complete", int((1 - feature_missing.mean()) * len(FEATURE_COLUMNS)), (1 - feature_missing.mean()) * 100),
        ("Missing cells absent", int(df[FEATURE_COLUMNS].isna().sum().sum() == 0), 100.0 if df[FEATURE_COLUMNS].isna().sum().sum() == 0 else 0.0),
        ("Duplicate rows absent", int(duplicate_rows == 0), 100.0 if duplicate_rows == 0 else 0.0),
    ]
    q_df = pd.DataFrame(quality_rows, columns=["check", "value", "score_percent"])
    y_pos = np.arange(len(q_df))
    ax.barh(y_pos, q_df["score_percent"], color="#DDEAE8", edgecolor="#8BA9A5", height=0.56, zorder=2)
    ax.scatter(q_df["score_percent"], y_pos, s=32, color="#4A6B8A", edgecolor="white", linewidth=0.45, zorder=5)
    for idx, row in q_df.iterrows():
        ax.text(min(row["score_percent"] + 2, 96), idx, f"{row['score_percent']:.0f}%", va="center", ha="left", fontsize=5.2)
    class_text = " / ".join(f"C{int(k)}={int(v)}" for k, v in class_counts.items())
    ax.text(
        0.03,
        0.08,
        f"Class balance: {class_text}\nMissing feature cells: {int(df[FEATURE_COLUMNS].isna().sum().sum())}",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=5.2,
        bbox=LABEL_BOX,
        zorder=20,
    )
    ax.set_yticks(y_pos)
    ax.set_yticklabels(q_df["check"], fontsize=5.4)
    ax.set_xlim(0, 105)
    ax.set_xlabel("Quality check score (%)")
    ax.set_title("Data-quality context", fontsize=7.4, fontweight="bold", pad=5, loc="center")
    style_axis(ax, grid_axis="x")
    return q_df.assign(class_balance=class_text, duplicate_rows=duplicate_rows)


def figure_feature_atlas(df: pd.DataFrame, diagnostics: dict) -> tuple[dict, dict[str, pd.DataFrame]]:
    apply_journal_kernel("compact", JOURNAL_PROFILE)
    feature_order = feature_order_by_correlation(df)
    fig, axes_grid = plt.subplots(2, 2, figsize=(8.6, 6.95))
    ax_a, ax_b, ax_c, ax_d = axes_grid.ravel()
    corr = plot_correlation_panel(ax_a, df, feature_order)
    class_means = plot_fingerprint_panel(ax_b, df, diagnostics, feature_order)
    f_scores = plot_feature_separation_panel(ax_c, df, diagnostics)
    quality = plot_quality_panel(ax_d, df)
    for label, ax in zip(["A", "B", "C", "D"], [ax_a, ax_b, ax_c, ax_d]):
        safe_panel_label(ax, label)
    ax_b.legend(handles=class_handles(), loc="upper center", frameon=False)
    plan = build_chart_plan("uci_wine_feature_atlas", ["A", "B", "C", "D"], "feature_structure_atlas")
    update_visual_counts(
        plan,
        [
            "clustered_correlation_heatmap",
            "top_correlation_metric_box",
            "class_fingerprint_lines",
            "zero_reference_line",
            "anova_f_lollipop",
            "feature_value_labels",
            "data_quality_score_bars",
            "class_balance_context",
            "shared_bottom_legend",
        ],
        labels=5,
        motifs=6,
    )
    report = save_figure(
        fig,
        {"A": ax_a, "B": ax_b, "C": ax_c, "D": ax_d},
        "uci_wine_feature_atlas",
        plan,
        adjust={"left": 0.08, "right": 0.98, "top": 0.93, "bottom": 0.08, "wspace": 0.34, "hspace": 0.38},
    )
    sources = {
        "atlas_correlation_matrix": corr.reset_index(names="feature"),
        "atlas_class_fingerprints": class_means,
        "atlas_feature_separation_scores": f_scores,
        "atlas_quality_summary": quality,
    }
    return report, sources


def build_data_profile(df: pd.DataFrame, diagnostics: dict) -> dict:
    missing_rate = df[["class", *FEATURE_COLUMNS]].isna().mean().sort_values(ascending=False)
    pca_var = diagnostics["pca"].explained_variance_ratio_
    lda_var = diagnostics["lda"].explained_variance_ratio_
    return {
        "source": str(DATA_PATH),
        "format": "csv",
        "structure": "headerless UCI Wine table",
        "shape": [int(df.shape[0]), 14],
        "columns": ["class", *FEATURE_COLUMNS],
        "inferredColumnNames": True,
        "semanticRoles": {
            "class": "target_label",
            "features": FEATURE_COLUMNS,
        },
        "domainHints": ["machine_learning", "classification_dataset", "chemometric_wine_features"],
        "nGroups": int(df["class"].nunique()),
        "nObservations": int(len(df)),
        "classCounts": {class_label(int(k)): int(v) for k, v in df["class"].value_counts().sort_index().items()},
        "missingPercent": (missing_rate * 100).round(4).to_dict(),
        "riskFlags": [
            "classic benchmark table; descriptive diagnostics only",
            "class labels are cultivar IDs, not clinical groups",
            "no missing feature cells detected" if df[FEATURE_COLUMNS].isna().sum().sum() == 0 else "missing feature values detected",
        ],
        "selectedChartBundle": "ML dataset diagnostics hero plus feature atlas",
        "journalStyle": JOURNAL_PROFILE["style"],
        "language": "zh-cn",
        "colorMode": "semantic class colors",
        "rasterDpi": RASTER_DPI,
        "crowdingPolicy": "detail_preserving_no_overlap",
        "pcaExplainedVariance": [float(v) for v in pca_var],
        "ldaExplainedVariance": [float(v) for v in lda_var],
        "rf5FoldBalancedAccuracy": float(diagnostics["balanced_accuracy"]),
    }


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_reports(df: pd.DataFrame, diagnostics: dict, reports: list[dict], data_profile: dict) -> None:
    figure_outputs = {
        "pdf": sorted(str(p.relative_to(RUN_ROOT)) for p in FIG_DIR.glob("*.pdf")),
        "svg": sorted(str(p.relative_to(RUN_ROOT)) for p in FIG_DIR.glob("*.svg")),
        "png": sorted(str(p.relative_to(RUN_ROOT)) for p in FIG_DIR.glob("*.png")),
        "source_data": sorted(str(p.relative_to(RUN_ROOT)) for p in SOURCE_DIR.glob("*.csv")),
    }
    panel_manifest = {
        "source": str(DATA_PATH),
        "figures": [
            {
                "id": "uci_wine_class_separation_hero",
                "type": "single-panel hero figure",
                "title": "Supervised class-separation map for UCI Wine",
                "panels": [
                    {
                        "panel": "A",
                        "description": "LDA1/LDA2 scatter with semantic cultivar colors, class covariance ellipses, centroids, zero references, and RF cross-validation metric box.",
                        "source_data": "source_data/uci_wine_hero_lda_scores.csv",
                    }
                ],
            },
            {
                "id": "uci_wine_feature_atlas",
                "type": "multi-panel feature atlas",
                "title": "UCI Wine feature structure and quality atlas",
                "panels": [
                    {"panel": "A", "description": "Clustered Pearson correlation matrix for the 13 inferred chemical features."},
                    {"panel": "B", "description": "Class-wise standardized chemical fingerprints with shared cultivar legend."},
                    {"panel": "C", "description": "ANOVA F-statistic lollipop ranking for class-separating features."},
                    {"panel": "D", "description": "Dataset completeness, duplicate, missingness, and class-balance context."},
                ],
            },
        ],
        "outputs": figure_outputs,
        "renderQa": {
            "hardFail": any(report["hardFail"] for report in reports),
            "reports": reports,
            "renderContractsPath": str(REPORT_DIR / "render_contracts.json"),
        },
    }
    write_json(REPORT_DIR / "panel_manifest.json", panel_manifest)
    write_json(REPORT_DIR / "render_qa.json", panel_manifest["renderQa"])
    metadata = {
        "skill": "scifig-generate",
        "skillEntry": str(SKILL_ROOT / "SKILL.md"),
        "skillCall": SKILL_CALL,
        "outputDir": str(RUN_ROOT),
        "generatedBy": Path(__file__).name,
        "mode": "auto",
        "language": "zh-cn",
        "exports": ["png", "pdf", "svg"],
        "dataProfile": data_profile,
        "renderQaSummary": {
            "hardFail": any(report["hardFail"] for report in reports),
            "allPngNonblank": all(report["customQa"]["pngNonblank"] for report in reports),
            "noLegendPanelOverlap": all(report["customQa"]["noLegendPanelOverlap"] for report in reports),
            "noCrossPanelTextOverlap": all(report["customQa"]["noCrossPanelTextOverlap"] for report in reports),
            "noTextDataOverlap": all(report["customQa"]["noTextDataOverlap"] for report in reports),
            "noColorbarPanelOverlap": all(report["customQa"]["noColorbarPanelOverlap"] for report in reports),
            "legendModeUsed": sorted(set(report["legendModeUsed"] for report in reports)),
        },
        "templateMiningReferences": [
            "template-mining/06-narrative-arcs.md: hero and multipanel_grid",
            "template-mining/04-grid-recipes.md: R0 single-panel and R2 two-by-two storyboard",
            "template-mining/03-palette-bank.md: npg_4 semantic class colors",
            "template-mining/05-annotation-idioms.md: metric boxes, zero references, white-edge markers",
            "template-mining/07-techniques/ml-model-diagnostics.md: classifier dataset diagnostics",
        ],
    }
    write_json(REPORT_DIR / "metadata.json", metadata)

    class_counts = df["class"].value_counts().sort_index()
    f_scores = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "anova_f": diagnostics["f_values"],
            "anova_p": diagnostics["p_values"],
        }
    ).sort_values("anova_f", ascending=False)
    lines = [
        "# UCI Wine ML-Diagnostics Showcase Stats Report",
        "",
        "## 数据概况",
        f"- Source file: `{DATA_PATH}`",
        f"- Rows x columns: {len(df):,} x 14",
        "- Header inference: headerless UCI Wine schema was detected; canonical feature names were applied.",
        f"- Classes: {', '.join(f'C{int(k)}={int(v)}' for k, v in class_counts.items())}",
        f"- Feature missing cells: {int(df[FEATURE_COLUMNS].isna().sum().sum())}",
        f"- Duplicate full rows: {int(df.duplicated(subset=['class', *FEATURE_COLUMNS]).sum())}",
        "",
        "## 描述性 ML 诊断",
        f"- PCA variance, first two components: {diagnostics['pca'].explained_variance_ratio_[0] * 100:.1f}% / {diagnostics['pca'].explained_variance_ratio_[1] * 100:.1f}%",
        f"- LDA discriminant variance: {diagnostics['lda'].explained_variance_ratio_[0] * 100:.1f}% / {diagnostics['lda'].explained_variance_ratio_[1] * 100:.1f}%",
        f"- RandomForest 5-fold balanced accuracy: {diagnostics['balanced_accuracy']:.3f}",
        f"- Top discriminative feature by ANOVA F: {FEATURE_SHORT[f_scores.iloc[0]['feature']]} (F={f_scores.iloc[0]['anova_f']:.2f})",
        "",
        "## Render QA",
    ]
    for report in reports:
        qa = report["customQa"]
        lines.append(
            f"- {report['figure']}: hardFail={str(report['hardFail']).lower()}, "
            f"legendContractEnforced={str(report['legendContractEnforced']).lower()}, "
            f"layoutContractEnforced={str(report['layoutContractEnforced']).lower()}, "
            f"legendModeUsed={report['legendModeUsed']}, "
            f"colorbarPanelOverlapCount={report['colorbarPanelOverlapCount']}, "
            f"textDataOverlapCount={report['textDataOverlapCount']}, "
            f"pngNonblank={str(qa['pngNonblank']).lower()}"
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "These figures are descriptive diagnostics for a labeled benchmark dataset. The report uses data-derived cross-validation, LDA/PCA, correlation, and ANOVA summaries, but does not introduce causal or experimental claims.",
        ]
    )
    (REPORT_DIR / "stats_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    render_path = REPORT_DIR / "render_contracts.json"
    if render_path.exists():
        render_path.unlink()
    df = load_data()
    diagnostics = compute_ml_diagnostics(df)
    data_profile = build_data_profile(df, diagnostics)

    df[["class", "class_label", *FEATURE_COLUMNS]].to_csv(SOURCE_DIR / "uci_wine_inferred_source.csv", index=False)
    pd.DataFrame(diagnostics["pca"].components_, columns=FEATURE_COLUMNS).to_csv(SOURCE_DIR / "uci_wine_pca_loadings.csv", index=False)
    pd.DataFrame(diagnostics["lda"].scalings_[: len(FEATURE_COLUMNS), :2], index=FEATURE_COLUMNS, columns=["LD1", "LD2"]).reset_index(names="feature").to_csv(
        SOURCE_DIR / "uci_wine_lda_feature_scalings.csv",
        index=False,
    )

    hero_report, hero_source = figure_class_separation_hero(df, diagnostics)
    hero_source.to_csv(SOURCE_DIR / "uci_wine_hero_lda_scores.csv", index=False)
    atlas_report, atlas_sources = figure_feature_atlas(df, diagnostics)
    for name, source in atlas_sources.items():
        source.to_csv(SOURCE_DIR / f"{name}.csv", index=False)

    reports = [hero_report, atlas_report]
    write_json(REPORT_DIR / "render_contracts.json", reports)
    write_reports(df, diagnostics, reports, data_profile)
    failures = [report["figure"] for report in reports if report["hardFail"]]
    if failures:
        raise SystemExit(f"Render QA failed for: {failures}; inspect {REPORT_DIR / 'render_contracts.json'}")
    print(json.dumps({"status": "completed", "figures": [report["figure"] for report in reports], "output": str(RUN_ROOT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
