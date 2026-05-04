#!/usr/bin/env python3
"""Generate a GTEx sample-quality showcase bundle.

Input data:
    D:/SciFig/.workflow/.scratchpad/test-data/raw/gtex_samples.tsv

Outputs:
    figures/*.png, figures/*.pdf, figures/*.svg
    source_data/*.csv
    reports/render_contracts.json, reports/stats_report.md, reports/panel_manifest.json
    metadata/metadata.json
"""

from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path
from textwrap import wrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


warnings.filterwarnings("ignore", category=UserWarning)

DATA_PATH = Path(r"D:\SciFig\.workflow\.scratchpad\test-data\raw\gtex_samples.tsv")
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(r"D:\test_scifig")
SKILL_ROOT = PROJECT_ROOT / ".codex" / "skills" / "scifig-generate"
FIG_DIR = RUN_ROOT / "figures"
REPORT_DIR = RUN_ROOT / "reports"
SOURCE_DIR = RUN_ROOT / "source_data"
META_DIR = RUN_ROOT / "metadata"
for directory in (FIG_DIR, REPORT_DIR, SOURCE_DIR, META_DIR):
    directory.mkdir(parents=True, exist_ok=True)

HELPER_SOURCE_PATH = SKILL_ROOT / "phases" / "code-gen" / "helpers.py"
TEMPLATE_HELPER_DIR = HELPER_SOURCE_PATH.parent
sys.path.insert(0, str(TEMPLATE_HELPER_DIR))

helper_source = HELPER_SOURCE_PATH.read_text(encoding="utf-8")
if helper_source.lstrip().startswith("```python"):
    lines = helper_source.splitlines()
    lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    helper_source = "\n".join(lines)
exec(helper_source, globals())

from template_mining_helpers import (  # noqa: E402
    add_metric_box,
    add_panel_label,
    add_zero_reference,
    apply_journal_kernel,
)


RASTER_DPI = 1200
RNG = np.random.default_rng(20260502)

JOURNAL_PROFILE = {
    "style": "Nature / genomics sample-QC",
    "font_family": ["DejaVu Sans"],
    "font_size_body_pt": 6.6,
    "font_size_small_pt": 5.2,
    "font_size_panel_label_pt": 8.2,
    "axis_linewidth_pt": 0.65,
    "max_text_font_size_pt": 11.0,
    "max_panel_label_font_size_pt": 11.0,
}

plt.rcParams.update(
    {
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.unicode_minus": False,
    }
)

SEMANTIC_TISSUE_COLORS = {
    "Brain": "#4C78A8",
    "Blood": "#B64A4A",
    "Skin": "#E07B67",
    "Esophagus": "#C97A20",
    "Blood Vessel": "#4E9A97",
    "Adipose Tissue": "#D6A33D",
    "Muscle": "#7B62A3",
    "Heart": "#C44E52",
    "Colon": "#59A14F",
    "Thyroid": "#62B6CB",
    "Lung": "#86A9E6",
    "Nerve": "#5C5B93",
    "Breast": "#CC79A7",
    "Pancreas": "#E6C229",
    "Testis": "#8F7A4A",
    "Stomach": "#9C755F",
    "Prostate": "#6B9AC4",
    "Adrenal Gland": "#B07AA1",
    "Pituitary": "#F28E2B",
    "Liver": "#8CD17D",
    "Ovary": "#E15759",
    "Spleen": "#76B7B2",
    "Small Intestine": "#A0CBE8",
    "Salivary Gland": "#FFBE7D",
    "Uterus": "#D37295",
    "Vagina": "#FABFD2",
    "Kidney": "#499894",
    "Bone Marrow": "#A8577E",
    "Bladder": "#79706E",
    "Cervix Uteri": "#B6992D",
    "Fallopian Tube": "#9D7660",
    "Other": "#9B9B9B",
}

TOP_SCATTER_TISSUES = [
    "Brain",
    "Blood",
    "Skin",
    "Esophagus",
    "Blood Vessel",
    "Adipose Tissue",
    "Muscle",
]

QC_COLUMNS = [
    "SMRIN",
    "SMTSISCH",
    "SMMAPRT",
    "SMEXPEFF",
    "SMNTRNRT",
    "SMRRNART",
]

QC_LABELS = {
    "SMRIN": "RIN",
    "SMTSISCH": "Ischemia",
    "SMMAPRT": "Mapping",
    "SMEXPEFF": "Exonic",
    "SMNTRNRT": "Intronic",
    "SMRRNART": "rRNA",
}


def format_int(value: int | float) -> str:
    return f"{int(value):,}"


def wrap_label(value: object, width: int = 16) -> str:
    text = str(value)
    return "\n".join(wrap(text, width=width, break_long_words=False)) or text


def tissue_color(tissue: object) -> str:
    return SEMANTIC_TISSUE_COLORS.get(str(tissue), SEMANTIC_TISSUE_COLORS["Other"])


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, sep="\t", low_memory=False)
    source_shape = df.shape
    numeric_cols = [col for col in df.columns if col not in {"SAMPID", "SMTS", "SMTSD", "SMCENTER", "SMNABTCH", "ANALYTE_TYPE"}]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.copy()
    df.attrs["source_shape"] = [int(source_shape[0]), int(source_shape[1])]
    df["SMTSISCH_NONNEG"] = df["SMTSISCH"].where(df["SMTSISCH"] >= 0)
    df["SMTS_TOP_SCATTER"] = np.where(df["SMTS"].isin(TOP_SCATTER_TISSUES), df["SMTS"], "Other")
    df["RNA_TOTAL_FLAG"] = df["ANALYTE_TYPE"].astype(str).eq("RNA:Total RNA")
    return df


def build_tissue_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tissue, group in df.groupby("SMTS", dropna=False):
        row = {
            "SMTS": tissue,
            "n_samples": int(len(group)),
            "n_rin": int(group["SMRIN"].notna().sum()),
            "median_rin": float(group["SMRIN"].median()) if group["SMRIN"].notna().any() else np.nan,
            "q25_rin": float(group["SMRIN"].quantile(0.25)) if group["SMRIN"].notna().any() else np.nan,
            "q75_rin": float(group["SMRIN"].quantile(0.75)) if group["SMRIN"].notna().any() else np.nan,
            "n_ischemia": int(group["SMTSISCH_NONNEG"].notna().sum()),
            "median_ischemia_min": float(group["SMTSISCH_NONNEG"].median()) if group["SMTSISCH_NONNEG"].notna().any() else np.nan,
            "median_mapping_rate": float(group["SMMAPRT"].median()) if group["SMMAPRT"].notna().any() else np.nan,
            "median_exonic_rate": float(group["SMEXPEFF"].median()) if group["SMEXPEFF"].notna().any() else np.nan,
        }
        for col in QC_COLUMNS:
            source_col = "SMTSISCH_NONNEG" if col == "SMTSISCH" else col
            row[f"{col}_missing_pct"] = float(group[source_col].isna().mean() * 100)
        rows.append(row)
    summary = pd.DataFrame(rows).sort_values(["n_samples", "SMTS"], ascending=[False, True]).reset_index(drop=True)
    return summary


def build_data_profile(df: pd.DataFrame, tissue_summary: pd.DataFrame) -> dict:
    missing = (df.isna().mean().sort_values(ascending=False) * 100).round(2).to_dict()
    negative_ischemia = int((df["SMTSISCH"] < 0).sum(skipna=True))
    source_shape = df.attrs.get("source_shape", [int(df.shape[0]), int(df.shape[1])])
    return {
        "source": str(DATA_PATH),
        "format": "tsv",
        "shape": source_shape,
        "analysisShapeWithDerivedColumns": [int(df.shape[0]), int(df.shape[1])],
        "domain": "genomics_sample_quality",
        "semanticRoles": {
            "sample_id": "SAMPID",
            "broad_tissue": "SMTS",
            "detailed_tissue": "SMTSD",
            "rna_integrity": "SMRIN",
            "ischemic_time": "SMTSISCH",
            "sequencing_mapping_rate": "SMMAPRT",
            "exonic_rate": "SMEXPEFF",
        },
        "nBroadTissues": int(df["SMTS"].nunique(dropna=True)),
        "nDetailedTissues": int(df["SMTSD"].nunique(dropna=True)),
        "analyteTypes": df["ANALYTE_TYPE"].value_counts(dropna=False).to_dict(),
        "broadTissueCounts": df["SMTS"].value_counts(dropna=False).to_dict(),
        "missingPercent": missing,
        "negativeIschemiaValuesTreatedAsMissing": negative_ischemia,
        "warnings": [
            "SMTSISCH contains negative values; negative ischemic times were treated as missing for visualization.",
            "Sequencing alignment metrics are mostly available for RNA:Total RNA rows; descriptive panels avoid inferential claims.",
        ],
        "workflowPreferences": {
            "mode": "auto",
            "language": "zh-cn",
            "journalStyle": "top-journal genomics sample-QC",
            "colorMode": "semantic tissue colors",
            "rasterDpi": RASTER_DPI,
            "crowdingPolicy": "detail preserving",
            "exportFormats": ["png", "pdf", "svg"],
        },
        "tissueSummaryRows": int(tissue_summary.shape[0]),
    }


def style_axis(ax, grid_axis: str = "x") -> None:
    ax.tick_params(length=2.4, width=0.55, pad=1.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.62)
    if grid_axis:
        ax.grid(True, axis=grid_axis, color="#D9DEE3", linewidth=0.32, linestyle="-", alpha=0.7, zorder=0)
    ax.set_axisbelow(True)


def visual_plan(applied: list[str]) -> dict:
    motifs = [
        "metric_box",
        "sample_size_label",
        "median_iqr_summary",
        "reference_line",
        "semantic_color_mapping",
        "missingness_disclosure",
    ]
    return {
        "minTotalEnhancements": 5,
        "appliedEnhancements": applied,
        "inPlotExplanatoryLabelCount": 3,
        "minInPlotLabelsPerFigure": 1,
        "referenceMotifsRequired": True,
        "minReferenceMotifsPerFigure": 2,
        "referenceMotifCount": 6,
        "visualGrammarMotifs": motifs,
        "visualGrammarMotifsApplied": motifs,
        "templateMotifsRequired": False,
        "templateMotifs": [],
        "templateMotifsApplied": [],
        "templateMotifCount": 0,
        "exactMotifCoverageRequired": True,
    }


def chart_plan(fig_key: str, primary: str, panel_ids: list[str], applied: list[str], legend: bool) -> dict:
    return {
        "primaryChart": primary,
        "secondaryCharts": ["tissue_quality_summary", "missingness_heatmap", "sample_qc_scatter"],
        "narrativeArc": "hero" if len(panel_ids) == 1 else "multipanel_grid",
        "panelBlueprint": {
            panel_id: {"role": "GTEx sample quality QC", "legend": "shared_bottom_center" if legend else "none"}
            for panel_id in panel_ids
        },
        "crowdingPlan": {
            "legendMode": "bottom_center" if legend else "none",
            "legendAllowedModes": ["bottom_center"] if legend else ["none"],
            "legendFrame": True,
            "legendFontSizePt": 7,
            "legendBottomAnchorY": 0.015,
            "legendBottomMarginMin": 0.06,
            "legendBottomMarginMax": 0.16,
            "forbidInAxesLegend": True,
            "maxLegendColumns": 4,
            "maxTextFontSizePt": 11,
            "maxPanelLabelFontSizePt": 11,
            "simplifyIfCrowded": True,
            "colorbarMode": "none",
            "textDataOverlapThreshold": 0.30,
        },
        "visualContentPlan": visual_plan(applied),
        "templateCasePlan": {
            "selectedByUser": True,
            "bundleKey": "gtex_sample_quality_showcase",
            "templateMatchMode": "best_effort_domain_transfer",
        },
        "figureKey": fig_key,
    }


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def validate_png(path: Path) -> dict:
    result = {"path": str(path), "exists": path.exists(), "nonblank": False, "fileSizeBytes": 0, "inkFraction": 0.0, "error": ""}
    if not path.exists():
        result["error"] = "missing_png"
        return result
    result["fileSizeBytes"] = int(path.stat().st_size)
    try:
        from PIL import Image

        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((320, 320))
            arr = np.asarray(img).astype(np.int16)
            nonwhite = np.any(arr < 245, axis=2)
            result["inkFraction"] = float(nonwhite.mean())
            result["nonblank"] = bool(result["fileSizeBytes"] > 4096 and result["inkFraction"] > 0.005)
    except Exception as exc:  # pragma: no cover - fallback for minimal environments
        result["error"] = str(exc)
        result["nonblank"] = result["fileSizeBytes"] > 4096
    return result


def save_figure(fig, axes: dict[str, plt.Axes], fig_key: str, plan: dict, *, bottom: float, top: float, left: float, right: float, wspace: float = 0.28, hspace: float = 0.32) -> dict:
    fig.subplots_adjust(bottom=bottom, top=top, left=left, right=right, wspace=wspace, hspace=hspace)
    legend_contract_report = enforce_figure_legend_contract(
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
    paths = {}
    for ext in ("pdf", "svg", "png"):
        out_path = FIG_DIR / f"{fig_key}.{ext}"
        if ext == "png":
            fig.savefig(out_path, dpi=RASTER_DPI, bbox_inches="tight", facecolor="white")
        else:
            fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
        paths[ext] = str(out_path)
    png_check = validate_png(Path(paths["png"]))
    report = {
        "figure": fig_key,
        "paths": paths,
        "legendContract": legend_contract_report,
        "layoutContract": layout_report,
        "visualDensity": density_report,
        "pngValidation": png_check,
        "legendContractEnforced": legend_contract_report.get("legendContractEnforced", False),
        "layoutContractEnforced": layout_report.get("layoutContractEnforced", False),
        "legendOutsidePlotArea": legend_contract_report.get("legendOutsidePlotArea", True),
        "axisLegendRemainingCount": legend_contract_report.get("axisLegendRemainingCount", 0),
        "legendModeUsed": legend_contract_report.get("legendModeUsed", "none"),
        "figureLegendCount": len(fig.legends),
        "layoutContractFailures": layout_report.get("layoutContractFailures", []),
        "colorbarPanelOverlapCount": layout_report.get("colorbarPanelOverlapCount", 0),
        "textDataOverlapCount": layout_report.get("textDataOverlapCount", 0),
        "crossPanelOverlapIssues": layout_report.get("crossPanelOverlapIssues", []),
        "hardFail": bool(
            legend_contract_report.get("legendContractFailures")
            or layout_report.get("layoutContractFailures")
            or density_report.get("contentDensityFailures")
            or not png_check.get("nonblank")
        ),
    }
    plt.close(fig)
    return report


def figure_quality_hero(df: pd.DataFrame, tissue_summary: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    apply_journal_kernel("hero", JOURNAL_PROFILE)
    plot_df = tissue_summary.dropna(subset=["median_rin"]).sort_values("median_rin", ascending=True).copy()
    plot_df["y"] = np.arange(len(plot_df))
    fig, ax = plt.subplots(figsize=(6.9, 8.4))
    y = plot_df["y"].to_numpy()
    q25 = plot_df["q25_rin"].to_numpy()
    q75 = plot_df["q75_rin"].to_numpy()
    med = plot_df["median_rin"].to_numpy()
    colors = [tissue_color(t) for t in plot_df["SMTS"]]
    sizes = 18 + 62 * np.sqrt(plot_df["n_samples"].to_numpy() / plot_df["n_samples"].max())
    ax.hlines(y, q25, q75, color="#B8C0CC", linewidth=2.2, zorder=2, alpha=0.9)
    ax.scatter(med, y, s=sizes, c=colors, edgecolor="white", linewidth=0.55, zorder=4)
    ax.axvline(7.0, color="#222222", linestyle=(0, (3, 2)), linewidth=0.75, zorder=1)
    ax.axvline(float(df["SMRIN"].median()), color="#7C4D79", linestyle="-", linewidth=0.75, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels([wrap_label(t, 18) for t in plot_df["SMTS"]], fontsize=5.4)
    ax.set_xlim(4.7, 9.7)
    ax.set_xlabel("RNA integrity number (SMRIN): median with interquartile range")
    ax.set_title("GTEx tissue-level RNA integrity landscape", fontsize=9.8, pad=5)
    style_axis(ax, "x")
    add_panel_label(ax, "A", x=-0.045, y=1.015, fontsize=8.2)
    add_metric_box(
        ax,
        {
            "samples": format_int(len(df)),
            "broad tissues": int(df["SMTS"].nunique()),
            "median RIN": f"{df['SMRIN'].median():.1f}",
            "RIN missing": f"{df['SMRIN'].isna().mean() * 100:.1f}%",
        },
        loc="bottom_right",
        fontsize=5.2,
    )
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#4C78A8", markeredgecolor="white", markersize=4.6, label="Tissue median"),
        Line2D([0], [0], color="#B8C0CC", linewidth=2.2, label="Interquartile range"),
        Line2D([0], [0], color="#222222", linestyle=(0, (3, 2)), linewidth=0.8, label="RIN 7 reference"),
        Line2D([0], [0], color="#7C4D79", linewidth=0.8, label="Global median"),
    ]
    ax.legend(handles=handles, frameon=True, title="QC encoding")
    plan = chart_plan(
        "gtex_sample_quality_hero",
        "single_panel_tissue_rin_landscape",
        ["A"],
        ["median_iqr_summary", "sample_size_scaled_markers", "reference_line", "metric_box", "semantic_tissue_colors", "all_tissues_preserved"],
        legend=True,
    )
    report = save_figure(fig, {"A": ax}, "gtex_sample_quality_hero", plan, bottom=0.07, top=0.94, left=0.255, right=0.975)
    source = plot_df[
        ["SMTS", "n_samples", "n_rin", "median_rin", "q25_rin", "q75_rin", "n_ischemia", "median_ischemia_min"]
    ].copy()
    return report, source


def figure_qc_atlas(df: pd.DataFrame, tissue_summary: pd.DataFrame) -> tuple[dict, dict[str, pd.DataFrame]]:
    apply_journal_kernel("compact", JOURNAL_PROFILE)
    top_tissues = tissue_summary.head(16)["SMTS"].tolist()
    top_summary = tissue_summary[tissue_summary["SMTS"].isin(top_tissues)].copy()
    top_summary = top_summary.sort_values("n_samples", ascending=True)
    fig, axes_arr = plt.subplots(2, 2, figsize=(10.3, 7.35))
    ax_a, ax_b, ax_c, ax_d = axes_arr.ravel()

    # A: sample-count scaffold by broad tissue.
    colors = [tissue_color(t) for t in top_summary["SMTS"]]
    ax_a.barh(np.arange(len(top_summary)), top_summary["n_samples"], color=colors, edgecolor="white", linewidth=0.45, zorder=3)
    ax_a.set_yticks(np.arange(len(top_summary)))
    ax_a.set_yticklabels([wrap_label(t, 15) for t in top_summary["SMTS"]], fontsize=5.0)
    ax_a.set_xlabel("Samples")
    ax_a.set_title("Broad tissue coverage", fontsize=8.2, pad=4)
    style_axis(ax_a, "x")
    add_panel_label(ax_a, "A", x=-0.055, y=1.025, fontsize=8.2)
    add_metric_box(ax_a, {"top tissues": len(top_tissues), "shown samples": format_int(top_summary["n_samples"].sum())}, loc="bottom_right", fontsize=4.9)

    # B: median RIN and IQR by the same tissue set.
    rin_df = tissue_summary[tissue_summary["SMTS"].isin(top_tissues)].dropna(subset=["median_rin"]).sort_values("median_rin", ascending=True)
    y = np.arange(len(rin_df))
    ax_b.hlines(y, rin_df["q25_rin"], rin_df["q75_rin"], color="#B8C0CC", linewidth=2.0, zorder=2)
    ax_b.scatter(rin_df["median_rin"], y, c=[tissue_color(t) for t in rin_df["SMTS"]], s=28, edgecolor="white", linewidth=0.45, zorder=4)
    ax_b.axvline(7.0, color="#222222", linestyle=(0, (3, 2)), linewidth=0.7, zorder=1)
    ax_b.set_yticks(y)
    ax_b.set_yticklabels([wrap_label(t, 15) for t in rin_df["SMTS"]], fontsize=5.0)
    ax_b.set_xlim(5.2, 9.5)
    ax_b.set_xlabel("SMRIN median [IQR]")
    ax_b.set_title("RNA integrity distribution", fontsize=8.2, pad=4)
    style_axis(ax_b, "x")
    add_panel_label(ax_b, "B", x=-0.055, y=1.025, fontsize=8.2)
    add_metric_box(ax_b, {"RIN observed": format_int(df["SMRIN"].notna().sum()), "median": f"{df['SMRIN'].median():.1f}"}, loc="bottom_right", fontsize=4.9)

    # C: single-cell-like cloud for ischemic time vs RIN, colored by broad tissue.
    scatter_df = df.dropna(subset=["SMRIN", "SMTSISCH_NONNEG"]).copy()
    if len(scatter_df) > 9000:
        scatter_df = scatter_df.sample(9000, random_state=20260502)
    for tissue in TOP_SCATTER_TISSUES + ["Other"]:
        part = scatter_df[scatter_df["SMTS_TOP_SCATTER"] == tissue]
        if part.empty:
            continue
        ax_c.scatter(
            part["SMTSISCH_NONNEG"],
            part["SMRIN"],
            s=5,
            alpha=0.23 if tissue != "Other" else 0.11,
            color=tissue_color(tissue),
            edgecolors="none",
            rasterized=True,
            label=tissue,
            zorder=2,
        )
    ax_c.axhline(7.0, color="#222222", linestyle=(0, (3, 2)), linewidth=0.72, zorder=1)
    ax_c.set_xlim(0, np.nanpercentile(df["SMTSISCH_NONNEG"], 99.2))
    ax_c.set_ylim(2.0, 10.1)
    ax_c.set_xlabel("SMTSISCH non-negative ischemic time")
    ax_c.set_ylabel("SMRIN")
    ax_c.set_title("Integrity across ischemic time", fontsize=8.2, pad=4)
    style_axis(ax_c, "both")
    add_panel_label(ax_c, "C", x=-0.055, y=1.025, fontsize=8.2)
    add_metric_box(
        ax_c,
        {
            "points shown": format_int(len(scatter_df)),
            "negative ischemia removed": format_int((df["SMTSISCH"] < 0).sum(skipna=True)),
        },
        loc="bottom_left",
        fontsize=4.8,
    )
    ax_c.legend(frameon=True, title="SMTS")

    # D: missingness matrix for priority QC variables by tissue.
    miss_df = tissue_summary[tissue_summary["SMTS"].isin(top_tissues)].copy()
    miss_df = miss_df.sort_values("n_samples", ascending=False)
    matrix = miss_df[[f"{col}_missing_pct" for col in QC_COLUMNS]].to_numpy(dtype=float)
    image = ax_d.imshow(matrix, cmap="Greys", vmin=0, vmax=100, aspect="auto", interpolation="nearest", zorder=1)
    ax_d.set_xticks(np.arange(len(QC_COLUMNS)))
    ax_d.set_xticklabels([QC_LABELS[col] for col in QC_COLUMNS], rotation=35, ha="right", fontsize=5.1)
    ax_d.set_yticks(np.arange(len(miss_df)))
    ax_d.set_yticklabels([wrap_label(t, 14) for t in miss_df["SMTS"]], fontsize=4.9)
    ax_d.set_title("QC field missingness by tissue", fontsize=8.2, pad=4)
    ax_d.tick_params(length=0, pad=1.5)
    for spine in ax_d.spines.values():
        spine.set_linewidth(0.62)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            if np.isfinite(value) and (value < 5 or value > 45):
                color = "white" if value > 45 else "#222222"
                ax_d.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=3.8, color=color, zorder=3)
    add_panel_label(ax_d, "D", x=-0.055, y=1.025, fontsize=8.2)
    add_metric_box(ax_d, {"cells": matrix.size, "darker": "more missing"}, loc="bottom_right", fontsize=4.8)
    image.set_gid("scifig_qc_missingness_matrix")

    plan = chart_plan(
        "gtex_sample_qc_atlas",
        "multipanel_gtex_qc_atlas",
        ["A", "B", "C", "D"],
        [
            "panel_labels",
            "sample_count_bars",
            "median_iqr_summary",
            "reference_line",
            "sample_cloud",
            "missingness_matrix",
            "metric_boxes",
            "semantic_tissue_colors",
        ],
        legend=True,
    )
    report = save_figure(
        fig,
        {"A": ax_a, "B": ax_b, "C": ax_c, "D": ax_d},
        "gtex_sample_qc_atlas",
        plan,
        bottom=0.08,
        top=0.935,
        left=0.14,
        right=0.985,
        wspace=0.34,
        hspace=0.38,
    )
    sources = {
        "atlas_tissue_counts": top_summary[["SMTS", "n_samples", "n_rin", "median_rin", "q25_rin", "q75_rin"]].copy(),
        "atlas_scatter_sample": scatter_df[["SAMPID", "SMTS", "SMTSD", "SMRIN", "SMTSISCH", "SMTSISCH_NONNEG", "SMTS_TOP_SCATTER"]].copy(),
        "atlas_missingness": miss_df[["SMTS", "n_samples"] + [f"{col}_missing_pct" for col in QC_COLUMNS]].copy(),
    }
    return report, sources


def write_stats_report(df: pd.DataFrame, tissue_summary: pd.DataFrame, reports: list[dict], data_profile: dict) -> None:
    source_shape = df.attrs.get("source_shape", [int(df.shape[0]), int(df.shape[1])])
    lines = [
        "# GTEx sample-quality showcase stats report",
        "",
        "## Input",
        f"- Source file: `{DATA_PATH}`",
        f"- Rows x columns: {source_shape[0]:,} x {source_shape[1]:,}",
        f"- Broad tissues (SMTS): {df['SMTS'].nunique(dropna=True):,}",
        f"- Detailed tissues (SMTSD): {df['SMTSD'].nunique(dropna=True):,}",
        "",
        "## Key QC variables",
    ]
    for col, label in [("SMRIN", "RNA integrity"), ("SMTSISCH", "Ischemic time"), ("SMMAPRT", "Mapping rate"), ("SMEXPEFF", "Exonic rate"), ("SMNTRNRT", "Intronic rate")]:
        series = df[col] if col != "SMTSISCH" else df["SMTSISCH_NONNEG"]
        lines.append(
            f"- {col} ({label}): n={series.notna().sum():,}, missing={series.isna().mean() * 100:.1f}%, median={series.median():.3g}"
        )
    lines.extend(
        [
            f"- Negative SMTSISCH values treated as missing: {(df['SMTSISCH'] < 0).sum(skipna=True):,}",
            "",
            "## Figure QA summary",
        ]
    )
    for report in reports:
        lines.append(
            f"- {report['figure']}: hardFail={str(report['hardFail']).lower()}, "
            f"legendContractEnforced={str(report['legendContractEnforced']).lower()}, "
            f"layoutContractEnforced={str(report['layoutContractEnforced']).lower()}, "
            f"colorbarPanelOverlapCount={report['colorbarPanelOverlapCount']}, "
            f"textDataOverlapCount={report['textDataOverlapCount']}, "
            f"pngNonBlank={str(report['pngValidation']['nonblank']).lower()}"
        )
    lines.extend(
        [
            "",
            "## Statistical interpretation",
            "All panels are descriptive QC visualizations. No inferential p-values, effect sizes, or causal claims were introduced.",
            "Tissue colors are semantic and held constant across hero and atlas figures.",
        ]
    )
    (REPORT_DIR / "stats_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_panel_manifest(reports: list[dict]) -> list[dict]:
    manifest = [
        {
            "figure": "gtex_sample_quality_hero",
            "type": "single-panel hero figure",
            "panels": [
                {
                    "panel": "A",
                    "title": "GTEx tissue-level RNA integrity landscape",
                    "data": "SMTS grouped SMRIN median and interquartile range; point size encodes tissue sample count.",
                    "source_data": "source_data/gtex_sample_quality_hero.csv",
                }
            ],
            "exports": reports[0]["paths"],
        },
        {
            "figure": "gtex_sample_qc_atlas",
            "type": "multi-panel QC atlas",
            "panels": [
                {"panel": "A", "title": "Broad tissue coverage", "data": "SMTS sample counts", "source_data": "source_data/atlas_tissue_counts.csv"},
                {"panel": "B", "title": "RNA integrity distribution", "data": "SMRIN median and IQR by SMTS", "source_data": "source_data/atlas_tissue_counts.csv"},
                {"panel": "C", "title": "Integrity across ischemic time", "data": "SMRIN vs non-negative SMTSISCH", "source_data": "source_data/atlas_scatter_sample.csv"},
                {"panel": "D", "title": "QC field missingness by tissue", "data": "Missingness percentage for selected QC fields", "source_data": "source_data/atlas_missingness.csv"},
            ],
            "exports": reports[1]["paths"],
        },
    ]
    write_json(REPORT_DIR / "panel_manifest.json", manifest)
    return manifest


def main() -> None:
    df = load_data()
    tissue_summary = build_tissue_summary(df)
    data_profile = build_data_profile(df, tissue_summary)
    tissue_summary.to_csv(SOURCE_DIR / "tissue_quality_summary.csv", index=False)
    df[["SAMPID", "SMTS", "SMTSD", "ANALYTE_TYPE", "SMRIN", "SMTSISCH", "SMTSISCH_NONNEG", "SMCENTER", "SMMAPRT", "SMEXPEFF", "SMNTRNRT", "SMRRNART"]].to_csv(
        SOURCE_DIR / "gtex_sample_qc_selected_source.csv",
        index=False,
    )

    hero_report, hero_source = figure_quality_hero(df, tissue_summary)
    hero_source.to_csv(SOURCE_DIR / "gtex_sample_quality_hero.csv", index=False)
    atlas_report, atlas_sources = figure_qc_atlas(df, tissue_summary)
    for name, source in atlas_sources.items():
        source.to_csv(SOURCE_DIR / f"{name}.csv", index=False)

    reports = [hero_report, atlas_report]
    write_json(REPORT_DIR / "render_contracts.json", reports)
    panel_manifest = write_panel_manifest(reports)
    write_stats_report(df, tissue_summary, reports, data_profile)
    metadata = {
        "skill": "scifig-generate",
        "skillEntry": str(SKILL_ROOT / "SKILL.md"),
        "skillCall": '$scifig-generate FILE: "D:\\SciFig\\.workflow\\.scratchpad\\test-data\\raw\\gtex_samples.tsv" OUTPUT_DIR: "D:\\test_scifig\\output\\maestro_scifig_showcase_20260502\\gtex_samples" MODE: auto LANGUAGE: zh-cn PREFERENCES: genomics sample-QC top-journal style, semantic tissue colors, 1200 dpi, detail preserving, maximum visual impact without overlap. MUST_HAVE: at least one single-panel hero figure and one multi-panel QC atlas; use tissue/sample quality variables such as SMTS, SMTSD, SMRIN, SMTSISCH when available; use bottom-center figure legend outside panels; avoid colorbar-panel overlap; export png pdf svg; write source_data, panel_manifest, stats_report, metadata, and render_contracts.json.',
        "dataProfile": data_profile,
        "figures": [report["paths"] for report in reports],
        "panelManifest": panel_manifest,
        "renderQaPass": all(not report["hardFail"] for report in reports),
    }
    write_json(META_DIR / "metadata.json", metadata)
    failures = [report for report in reports if report["hardFail"]]
    if failures:
        raise SystemExit(f"Render QA failed for: {[report['figure'] for report in failures]}")
    print(json.dumps({"status": "completed", "figures": [report["figure"] for report in reports], "output": str(RUN_ROOT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
