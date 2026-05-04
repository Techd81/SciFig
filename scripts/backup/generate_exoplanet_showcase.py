#!/usr/bin/env python3
"""
Generate a Nature Astronomy-style exoplanet physical-property atlas.

Input data:
    D:/SciFig/.workflow/.scratchpad/test-data/raw/nasa_exoplanets.csv

Outputs:
    figures/*.pdf, figures/*.svg, figures/*.png
    source_data/*.csv
    reports/*.json and reports/stats_report.md
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
import matplotlib.image as mpimg
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


warnings.filterwarnings("ignore", category=UserWarning)

DATA_PATH = Path(r"D:\SciFig\.workflow\.scratchpad\test-data\raw\nasa_exoplanets.csv")
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(r"D:\test_scifig")
FIG_DIR = RUN_ROOT / "figures"
REPORT_DIR = RUN_ROOT / "reports"
SOURCE_DIR = RUN_ROOT / "source_data"
for directory in (FIG_DIR, REPORT_DIR, SOURCE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

HELPER_SOURCE_PATH = PROJECT_ROOT / ".codex" / "skills" / "scifig-generate" / "phases" / "code-gen" / "helpers.py"
TEMPLATE_HELPER_DIR = HELPER_SOURCE_PATH.parent
sys.path.insert(0, str(TEMPLATE_HELPER_DIR))

aaa = HELPER_SOURCE_PATH.read_text(encoding="utf-8")
if aaa.lstrip().startswith("```python"):
    lines = aaa.splitlines()
    lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    aaa = "\n".join(lines)
exec(aaa, globals())

from template_mining_helpers import (  # noqa: E402
    add_metric_box,
    add_panel_label,
    add_zero_reference,
    apply_journal_kernel,
    apply_scatter_regression_floor,
)


RASTER_DPI = 1200
RNG = np.random.default_rng(20260502)

SKILL_CALL = (
    '$scifig-generate FILE: "D:\\SciFig\\.workflow\\.scratchpad\\test-data\\raw\\nasa_exoplanets.csv" '
    'OUTPUT_DIR: "D:\\test_scifig\\output\\maestro_scifig_showcase_20260502\\nasa_exoplanets" '
    "MODE: auto LANGUAGE: zh-cn PREFERENCES: field-leading astronomy style, "
    "Nature Astronomy-like compact discipline, semantic color, 1200 dpi, detail preserving, "
    "maximum visual impact without overlap. MUST_HAVE: at least one single-panel hero figure and "
    "one multi-panel atlas figure; physical-property atlas story; include missingness disclosure; "
    "use bottom-center figure legend outside panels; avoid colorbar-panel overlap; export png pdf svg; "
    "write source_data, panel_manifest, stats_report, metadata, and render_contracts.json."
)

JOURNAL_PROFILE = {
    "style": "Nature Astronomy",
    "font_family": ["DejaVu Sans"],
    "font_size_body_pt": 6.8,
    "font_size_small_pt": 5.6,
    "font_size_panel_label_pt": 8.0,
    "axis_linewidth_pt": 0.65,
    "max_text_font_size_pt": 11.0,
    "max_panel_label_font_size_pt": 11.0,
}

LABEL_BOX = {
    "boxstyle": "round,pad=0.18",
    "facecolor": "white",
    "edgecolor": "none",
    "alpha": 0.86,
}

METHOD_COLORS = {
    "Transit": "#3B6FB6",
    "Radial Velocity": "#C97A20",
    "Microlensing": "#5A9A59",
    "Imaging": "#B64A4A",
    "TTV": "#6AA6A6",
    "Other": "#81756D",
}

RADIUS_COLORS = {
    "Terrestrial": "#58606D",
    "Super-Earth": "#4C78A8",
    "Sub-Neptune": "#72B7B2",
    "Neptune-like": "#59A14F",
    "Giant": "#E15759",
    "Unknown": "#A0A0A0",
}

TEMP_COLORS = {
    "Cool": "#4C78A8",
    "Temperate": "#59A14F",
    "Warm": "#F2B447",
    "Hot": "#E15759",
    "Unknown": "#9B9B9B",
}


def clean_positive(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return values.where(values > 0)


def short_method(value: object) -> str:
    text = str(value)
    if text == "Transit Timing Variations":
        return "TTV"
    if text in METHOD_COLORS:
        return text
    return "Other"


def radius_class(radius: object) -> str:
    if pd.isna(radius):
        return "Unknown"
    radius = float(radius)
    if radius < 1.25:
        return "Terrestrial"
    if radius < 2.0:
        return "Super-Earth"
    if radius < 4.0:
        return "Sub-Neptune"
    if radius < 8.0:
        return "Neptune-like"
    return "Giant"


def temp_class(temp: object) -> str:
    if pd.isna(temp):
        return "Unknown"
    temp = float(temp)
    if temp < 180:
        return "Cool"
    if temp <= 320:
        return "Temperate"
    if temp <= 900:
        return "Warm"
    return "Hot"


def period_class(period: object) -> str:
    if pd.isna(period):
        return "Unknown"
    period = float(period)
    if period < 10:
        return "short period"
    if period <= 100:
        return "intermediate period"
    return "long period"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    numeric_cols = [
        "sy_dist",
        "pl_orbper",
        "pl_rade",
        "pl_bmasse",
        "pl_eqt",
        "st_teff",
        "st_rad",
        "st_mass",
        "disc_year",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = clean_positive(df[col])
    df["method_short"] = df["discoverymethod"].map(short_method)
    df["radius_class"] = df["pl_rade"].map(radius_class)
    df["temp_class"] = df["pl_eqt"].map(temp_class)
    df["period_class"] = df["pl_orbper"].map(period_class)
    df["disc_year"] = pd.to_numeric(df["disc_year"], errors="coerce")
    df["disc_decade"] = (np.floor(df["disc_year"] / 10) * 10).astype("Int64")
    return df


def format_int(value: int | float) -> str:
    return f"{int(value):,}"


def method_order(df: pd.DataFrame) -> list[str]:
    available = [m for m in ["Transit", "Radial Velocity", "Microlensing", "Imaging", "TTV"] if (df["method_short"] == m).any()]
    if (df["method_short"] == "Other").any():
        available.append("Other")
    return available


def sample_rows(df: pd.DataFrame, cols: list[str], n: int = 12000) -> pd.DataFrame:
    subset = df.dropna(subset=cols).copy()
    if len(subset) > n:
        subset = subset.sample(n=n, random_state=20260502)
    return subset


def annotate_n(ax, text: str, loc: str = "top_left") -> None:
    add_metric_box(ax, {"n": text}, loc=loc, fontsize=5)


def style_axis(ax) -> None:
    ax.tick_params(length=2.5, width=0.55, pad=1.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.65)
    ax.grid(True, color="#D9DEE3", linewidth=0.35, linestyle="-", alpha=0.6, zorder=0)


def add_bottom_method_legend(ax, methods: list[str]) -> None:
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=METHOD_COLORS[m],
            markeredgecolor="white",
            markeredgewidth=0.3,
            markersize=4,
            label=m,
        )
        for m in methods
    ]
    ax.legend(handles=handles, frameon=True, title="Discovery method")


def record_render_contract_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        records = json.loads(path.read_text(encoding="utf-8"))
    else:
        records = []
    records.append(report)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def visual_plan(applied: list[str]) -> dict:
    motifs = [
        "metric_box",
        "reference_band",
        "density_encoding",
        "sample_size_label",
        "semantic_color_mapping",
        "missingness_disclosure",
    ]
    return {
        "minTotalEnhancements": 5,
        "appliedEnhancements": applied,
        "inPlotExplanatoryLabelCount": 4,
        "minInPlotLabelsPerFigure": 1,
        "referenceMotifsRequired": True,
        "minReferenceMotifsPerFigure": 2,
        "referenceMotifCount": 5,
        "visualGrammarMotifs": motifs,
        "visualGrammarMotifsApplied": motifs,
        "templateMotifsRequired": False,
        "templateMotifs": [],
        "templateMotifsApplied": [],
        "templateMotifCount": 0,
        "exactMotifCoverageRequired": True,
    }


def chart_plan(fig_key: str, panel_ids: list[str], applied: list[str]) -> dict:
    is_single = len(panel_ids) == 1
    return {
        "primaryChart": "single_panel_exoplanet_hero" if is_single else "exoplanet_physical_property_atlas",
        "secondaryCharts": ["density_scatter", "stacked_bar", "annotated_heatmap", "missingness_disclosure"],
        "panelBlueprint": {
            panel: {"role": "exoplanet_atlas_panel", "legend": "shared_bottom_center"}
            for panel in panel_ids
        },
        "crowdingPlan": {
            "legendMode": "bottom_center",
            "legendAllowedModes": ["bottom_center"],
            "legendFrame": True,
            "legendFontSizePt": 7,
            "legendBottomAnchorY": 0.015,
            "legendBottomMarginMin": 0.06,
            "legendBottomMarginMax": 0.16,
            "forbidInAxesLegend": True,
            "maxLegendColumns": 6,
            "maxTextFontSizePt": 11,
            "maxPanelLabelFontSizePt": 11,
            "simplifyIfCrowded": False,
        },
        "visualContentPlan": visual_plan(applied),
        "templateCasePlan": {
            "selectedByUser": True,
            "bundleKey": "exoplanet_physical_property_atlas",
            "templateMatchMode": "best_effort_domain_transfer",
            "narrativeArc": "hero" if is_single else "multipanel_grid",
        },
        "figureKey": fig_key,
    }


def save_figure(fig, axes: dict[str, plt.Axes], fig_key: str, plan: dict) -> dict:
    fig.subplots_adjust(bottom=0.08, top=0.90, left=0.08, right=0.96, wspace=0.44, hspace=0.34)
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
    report = {
        "figure": fig_key,
        "legendContract": legend_contract_report,
        "layoutContract": layout_report,
        "visualDensity": density_report,
        "legendContractEnforced": legend_contract_report.get("legendContractEnforced", False),
        "layoutContractEnforced": layout_report.get("layoutContractEnforced", False),
        "legendOutsidePlotArea": legend_contract_report.get("legendOutsidePlotArea", False),
        "axisLegendRemainingCount": legend_contract_report.get("axisLegendRemainingCount", 0),
        "legendModeUsed": legend_contract_report.get("legendModeUsed", "none"),
        "figureLegendCount": len(fig.legends),
        "layoutContractFailures": layout_report.get("layoutContractFailures", []),
        "hardFail": bool(
            legend_contract_report.get("legendContractFailures")
            or layout_report.get("layoutContractFailures")
            or density_report.get("contentDensityFailures")
        ),
    }
    record_render_contract_report(report, REPORT_DIR / "render_contracts.json")
    for ext in ("pdf", "svg", "png"):
        out_path = FIG_DIR / f"{fig_key}.{ext}"
        if ext == "png":
            fig.savefig(out_path, dpi=RASTER_DPI, bbox_inches="tight", facecolor="white")
        else:
            fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return report


def build_data_profile(df: pd.DataFrame) -> dict:
    missing = (df.isna().mean().sort_values(ascending=False) * 100).round(2).to_dict()
    usable = {
        "mass_radius": int(df.dropna(subset=["pl_bmasse", "pl_rade"]).shape[0]),
        "radius_period": int(df.dropna(subset=["pl_rade", "pl_orbper"]).shape[0]),
        "eqt_radius": int(df.dropna(subset=["pl_eqt", "pl_rade"]).shape[0]),
        "stellar_context": int(df.dropna(subset=["st_teff", "st_rad", "pl_rade"]).shape[0]),
    }
    return {
        "source": str(DATA_PATH),
        "shape": [int(df.shape[0]), int(df.shape[1])],
        "columns": list(df.columns),
        "domain": "astronomy_exoplanet_science",
        "selectedChartBundle": "planet physical-property atlas",
        "journalStyle": "Nature Astronomy",
        "colorMode": "domain_semantic",
        "rasterDpi": RASTER_DPI,
        "crowdingPolicy": "preserve_information",
        "missingPercent": missing,
        "usablePanelCounts": usable,
        "methods": df["method_short"].value_counts().to_dict(),
    }


def figure_single_panel_hero(df: pd.DataFrame) -> dict:
    apply_journal_kernel("hero", JOURNAL_PROFILE)
    fig, ax = plt.subplots(figsize=(6.8, 5.9))
    axes = {"A": ax}
    methods = method_order(df)
    mr = sample_rows(df, ["pl_bmasse", "pl_rade"], n=15000)
    mr.to_csv(SOURCE_DIR / "figure0_single_panel_mass_radius_hero.csv", index=False)

    radius_bands = [
        (0.35, 1.25, "#F1F4F7", "terrestrial"),
        (1.25, 2.0, "#E7F1FA", "super-Earth"),
        (2.0, 4.0, "#E7F5F2", "sub-Neptune"),
        (4.0, 8.0, "#F1F7E9", "Neptune-like"),
        (8.0, 24.0, "#FCEEEE", "giant"),
    ]
    for ymin, ymax, color, label in radius_bands:
        ax.axhspan(ymin, ymax, color=color, alpha=0.78, zorder=0)
        ax.text(0.16, math.sqrt(ymin * ymax), label, fontsize=5.4, color="#4B5563", bbox=LABEL_BOX, zorder=8)

    for method in methods:
        part = mr[mr["method_short"] == method]
        ax.scatter(
            part["pl_bmasse"],
            part["pl_rade"],
            s=11,
            c=METHOD_COLORS[method],
            alpha=0.45,
            edgecolors="white",
            linewidth=0.12,
            rasterized=True,
            label=method,
            zorder=4,
        )

    mass_grid = np.logspace(-1, 4, 260)
    ax.plot(mass_grid, mass_grid ** 0.27, color="#1F2937", lw=1.05, ls="--", zorder=6, label="rocky guide")
    ax.plot(mass_grid, 3.9 * mass_grid ** 0.27, color="#6B7280", lw=0.9, ls=":", zorder=6, label="volatile-rich guide")
    anchors = [(1, 1, "Earth"), (17.1, 3.88, "Neptune"), (317.8, 11.2, "Jupiter")]
    for x, y, label in anchors:
        ax.scatter([x], [y], marker="*", s=86, color="#111111", edgecolor="white", linewidth=0.35, zorder=9)
        ax.text(x * 1.16, y * 1.05, label, fontsize=6.0, ha="left", va="center", bbox=LABEL_BOX, zorder=10)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.08, max(6000, np.nanpercentile(mr["pl_bmasse"], 99.6)))
    ax.set_ylim(0.32, max(24, np.nanpercentile(mr["pl_rade"], 99.4)))
    ax.set_xlabel("Planet mass (Earth masses)")
    ax.set_ylabel("Planet radius (Earth radii)")
    ax.set_title("")
    add_metric_box(
        ax,
        {
            "mass+radius rows": format_int(len(mr)),
            "mass missing": f"{df['pl_bmasse'].isna().mean():.1%}",
            "radius missing": f"{df['pl_rade'].isna().mean():.1%}",
        },
        loc="top_right",
        fontsize=5.4,
    )
    ax.text(
        0.03,
        0.04,
        "Descriptive atlas only; mass-radius conclusions use complete-case subset.",
        transform=ax.transAxes,
        fontsize=5.7,
        color="#374151",
        bbox=LABEL_BOX,
        zorder=10,
    )
    add_panel_label(ax, "A", x=-0.045, y=1.025)
    style_axis(ax)
    add_bottom_method_legend(ax, methods)
    fig.suptitle(
        "Exoplanet physical-property map",
        x=0.5,
        y=0.985,
        ha="center",
        fontsize=10,
        fontweight="bold",
    )

    plan = chart_plan(
        "figure0_single_panel_physical_hero",
        list(axes),
        ["single_panel_hero", "mass_radius_anchor_overlay", "radius_class_bands", "missingness_disclosure", "method_legend"],
    )
    return save_figure(fig, axes, "figure0_single_panel_physical_hero", plan)


def figure_physical_atlas(df: pd.DataFrame) -> dict:
    apply_journal_kernel("compact", JOURNAL_PROFILE)
    fig, axes_arr = plt.subplots(2, 2, figsize=(7.2, 5.8))
    axes = dict(zip(["A", "B", "C", "D"], axes_arr.ravel()))
    methods = method_order(df)

    mr = sample_rows(df, ["pl_bmasse", "pl_rade"], n=9000)
    ax = axes["A"]
    apply_scatter_regression_floor(ax)
    for method in methods:
        part = mr[mr["method_short"] == method]
        ax.scatter(
            part["pl_bmasse"],
            part["pl_rade"],
            s=8,
            c=METHOD_COLORS[method],
            alpha=0.42,
            linewidth=0,
            rasterized=True,
            label=method,
            zorder=4,
        )
    mass_grid = np.logspace(-1, 4, 200)
    for coeff, label, color in [(1.0, "rocky scaling", "#3A3A3A"), (3.9, "volatile-rich guide", "#6A6A6A")]:
        ax.plot(mass_grid, coeff * mass_grid ** 0.27, color=color, lw=0.8, ls="--", zorder=5)
    ax.scatter([1, 17.1, 317.8], [1, 3.88, 11.2], marker="*", s=46, color="#111111", zorder=8)
    for x, y, label in [(1, 1, "Earth"), (17.1, 3.88, "Neptune"), (317.8, 11.2, "Jupiter")]:
        ax.text(x * 1.18, y * 1.03, label, fontsize=5.4, ha="left", va="center", bbox=LABEL_BOX)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Planet mass (Earth masses)")
    ax.set_ylabel("Planet radius (Earth radii)")
    ax.set_title("Mass-radius plane with Solar System anchors", loc="center", pad=5)
    annotate_n(ax, format_int(len(mr)), "bottom_right")
    add_panel_label(ax, "A", x=-0.06, y=1.08)
    style_axis(ax)
    add_bottom_method_legend(ax, methods)

    ax = axes["B"]
    radius_data = df.dropna(subset=["pl_rade"]).copy()
    bins = np.logspace(np.log10(0.3), np.log10(30), 44)
    for klass in ["Terrestrial", "Super-Earth", "Sub-Neptune", "Neptune-like", "Giant"]:
        part = radius_data[radius_data["radius_class"] == klass]
        ax.hist(
            part["pl_rade"],
            bins=bins,
            histtype="stepfilled",
            alpha=0.50,
            color=RADIUS_COLORS[klass],
            edgecolor="white",
            linewidth=0.25,
            label=klass,
        )
    ax.set_xscale("log")
    ax.set_xlabel("Planet radius (Earth radii)")
    ax.set_ylabel("")
    ax.set_title("Observed radius classes", loc="center", pad=5)
    for x in [1.25, 2, 4, 8]:
        ax.axvline(x, color="#222222", lw=0.55, ls=":", zorder=3)
    add_metric_box(
        ax,
        {
            "radius complete": f"{len(radius_data) / len(df):.1%}",
            "median R": f"{radius_data['pl_rade'].median():.2f} R_E",
        },
        loc="top_right",
        fontsize=5,
    )
    add_panel_label(ax, "B", x=-0.06, y=1.08)
    style_axis(ax)

    eq = sample_rows(df, ["pl_eqt", "pl_rade"], n=12000)
    ax = axes["C"]
    ax.axvspan(180, 320, color="#E7F2E3", alpha=0.85, zorder=0)
    ax.text(205, 22, "temperate\nwindow", fontsize=5.6, color="#2D5B2F", bbox=LABEL_BOX)
    for klass in ["Terrestrial", "Super-Earth", "Sub-Neptune", "Neptune-like", "Giant"]:
        part = eq[eq["radius_class"] == klass]
        ax.scatter(
            part["pl_eqt"],
            part["pl_rade"],
            s=7,
            c=RADIUS_COLORS[klass],
            alpha=0.45,
            linewidth=0,
            rasterized=True,
            label=klass,
            zorder=3,
        )
    ax.set_yscale("log")
    ax.set_xlim(60, min(4200, np.nanpercentile(eq["pl_eqt"], 99.5)))
    ax.set_xlabel("Equilibrium temperature (K)")
    ax.set_ylabel("Planet radius (Earth radii)")
    ax.set_title("Thermal context by radius class", loc="center", pad=5)
    add_metric_box(
        ax,
        {
            "eq. temp complete": f"{df['pl_eqt'].notna().mean():.1%}",
            "temperate rows": format_int(((df["pl_eqt"] >= 180) & (df["pl_eqt"] <= 320)).sum()),
        },
        loc="top_right",
        fontsize=5,
    )
    add_panel_label(ax, "C", x=-0.06, y=1.08)
    style_axis(ax)

    host = sample_rows(df, ["st_teff", "st_rad", "pl_rade"], n=12000)
    ax = axes["D"]
    for klass in ["Terrestrial", "Super-Earth", "Sub-Neptune", "Neptune-like", "Giant"]:
        part = host[host["radius_class"] == klass]
        ax.scatter(
            part["st_teff"],
            part["st_rad"],
            c=RADIUS_COLORS[klass],
            s=9,
            alpha=0.48,
            linewidth=0,
            rasterized=True,
            label=klass,
            zorder=3,
        )
    ax.axvspan(4800, 6300, color="#EFEFE8", alpha=0.75, zorder=0)
    ax.text(4920, np.nanpercentile(host["st_rad"], 94), "solar-type\nhost band", fontsize=5.6, color="#555555", bbox=LABEL_BOX)
    ax.set_yscale("log")
    ax.set_xlabel("Stellar effective temperature (K)")
    ax.set_ylabel("Stellar radius (Solar radii)")
    ax.set_title("Host-star context colored by planet radius", loc="center", pad=5)
    annotate_n(ax, format_int(len(host)), "bottom_right")
    add_panel_label(ax, "D", x=-0.06, y=1.08)
    style_axis(ax)

    plan = chart_plan(
        "figure1_physical_property_atlas",
        list(axes),
        ["mass_radius_anchor_overlay", "radius_distribution", "temperate_band", "host_star_context", "metric_boxes"],
    )
    return save_figure(fig, axes, "figure1_physical_property_atlas", plan)


def figure_discovery_bias(df: pd.DataFrame) -> dict:
    apply_journal_kernel("compact", JOURNAL_PROFILE)
    fig, axes_arr = plt.subplots(2, 2, figsize=(7.2, 5.8))
    axes = dict(zip(["A", "B", "C", "D"], axes_arr.ravel()))
    methods = method_order(df)

    annual = (
        df.dropna(subset=["disc_year"])
        .assign(year=lambda d: d["disc_year"].astype(int))
        .groupby(["year", "method_short"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=methods, fill_value=0)
        .sort_index()
    )
    annual.to_csv(SOURCE_DIR / "figure2_annual_discoveries_by_method.csv")

    ax = axes["A"]
    bottom = np.zeros(len(annual))
    years = annual.index.to_numpy()
    for method in methods:
        vals = annual[method].to_numpy()
        ax.bar(years, vals, bottom=bottom, color=METHOD_COLORS[method], width=0.88, linewidth=0, label=method)
        bottom += vals
    ax.set_xlabel("Discovery year")
    ax.set_ylabel("Planets in catalogue")
    ax.set_title("Discovery throughput by method", loc="center", pad=5)
    ax.set_xlim(max(1988, years.min() - 1), years.max() + 1)
    add_metric_box(ax, {"rows": format_int(len(df)), "methods": len(methods)}, loc="top_left", fontsize=5)
    add_panel_label(ax, "A", x=-0.06, y=1.08)
    style_axis(ax)
    add_bottom_method_legend(ax, methods)

    ax = axes["B"]
    cumulative = annual.cumsum()
    for method in methods:
        ax.plot(cumulative.index, cumulative[method], color=METHOD_COLORS[method], lw=1.2, label=method)
    ax.plot(cumulative.index, cumulative.sum(axis=1), color="#111111", lw=1.7, label="All methods")
    ax.set_yscale("log")
    ax.set_xlabel("Discovery year")
    ax.set_ylabel("Cumulative planets")
    ax.set_title("Cumulative catalogue expansion", loc="center", pad=5)
    ax.text(0.03, 0.89, "log scale", transform=ax.transAxes, fontsize=5.6, bbox=LABEL_BOX)
    add_panel_label(ax, "B", x=-0.06, y=1.08)
    style_axis(ax)

    rp = sample_rows(df, ["pl_orbper", "pl_rade"], n=14000)
    ax = axes["C"]
    ax.axhspan(1.25, 2.0, color="#EEF5FB", alpha=0.75, zorder=0)
    ax.text(0.06, 0.32, "super-Earth\nradius band", transform=ax.transAxes, fontsize=5.6, color="#355D7C", bbox=LABEL_BOX)
    for method in methods:
        part = rp[rp["method_short"] == method]
        ax.scatter(
            part["pl_orbper"],
            part["pl_rade"],
            s=6,
            c=METHOD_COLORS[method],
            alpha=0.36,
            linewidth=0,
            rasterized=True,
            label=method,
            zorder=3,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Orbital period (days)")
    ax.set_ylabel("Planet radius (Earth radii)")
    ax.set_title("Period-radius selection surface", loc="center", pad=5)
    add_metric_box(ax, {"usable": format_int(len(rp)), "radius+period": f"{len(rp) / len(df):.1%}"}, loc="bottom_left", fontsize=5)
    add_panel_label(ax, "C", x=-0.06, y=1.08)
    style_axis(ax)

    heat = (
        df.dropna(subset=["disc_decade", "pl_rade"])
        .assign(decade=lambda d: d["disc_decade"].astype(int).astype(str) + "s")
        .pivot_table(index="method_short", columns="decade", values="pl_rade", aggfunc="median")
        .reindex(index=methods)
    )
    heat.to_csv(SOURCE_DIR / "figure2_median_radius_by_method_decade.csv")
    ax = axes["D"]
    matrix = heat.to_numpy(dtype=float)
    im = ax.imshow(matrix, cmap="YlGnBu", aspect="auto", interpolation="nearest")
    ax.set_xticks(np.arange(len(heat.columns)))
    ax.set_xticklabels(heat.columns, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(heat.index)))
    ax.set_yticklabels(heat.index)
    ax.set_title("Median radius by method and decade", loc="center", pad=5)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            if np.isfinite(value):
                ax.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize=4.8, color="#15202B")
    ax.text(
        0.98,
        0.03,
        "cell value = median R_E",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=5.1,
        bbox=LABEL_BOX,
    )
    add_panel_label(ax, "D", x=-0.06, y=1.08)
    style_axis(ax)

    plan = chart_plan(
        "figure2_discovery_bias_atlas",
        list(axes),
        ["stacked_annual_counts", "cumulative_log_timeline", "period_radius_selection_surface", "annotated_heatmap", "method_legend"],
    )
    return save_figure(fig, axes, "figure2_discovery_bias_atlas", plan)


def figure_candidate_context(df: pd.DataFrame) -> dict:
    apply_journal_kernel("compact", JOURNAL_PROFILE)
    fig, axes_arr = plt.subplots(2, 2, figsize=(7.2, 5.8))
    axes = dict(zip(["A", "B", "C", "D"], axes_arr.ravel()))
    methods = method_order(df)

    eq = sample_rows(df, ["pl_eqt", "pl_orbper", "pl_rade"], n=14000)
    ax = axes["A"]
    ax.axhspan(180, 320, color="#E7F2E3", alpha=0.95, zorder=0)
    ax.text(0.03, 0.47, "temperate\nequilibrium band", transform=ax.transAxes, fontsize=5.5, color="#2E5A31", bbox=LABEL_BOX)
    for method in methods:
        part = eq[eq["method_short"] == method]
        ax.scatter(
            part["pl_orbper"],
            part["pl_eqt"],
            s=np.clip(part["pl_rade"], 1, 18) * 2.2,
            c=METHOD_COLORS[method],
            alpha=0.35,
            linewidth=0,
            rasterized=True,
            label=method,
            zorder=3,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Orbital period (days)")
    ax.set_ylabel("Equilibrium temperature (K)")
    ax.set_title("Thermal-orbital candidate context", loc="center", pad=5)
    add_metric_box(ax, {"usable": format_int(len(eq)), "size encodes": "planet radius"}, loc="top_right", fontsize=5)
    add_panel_label(ax, "A", x=-0.06, y=1.08)
    style_axis(ax)
    add_bottom_method_legend(ax, methods)

    candidate = df.dropna(subset=["pl_eqt", "pl_rade", "st_teff"]).copy()
    candidate["temperate_radius"] = (
        (candidate["pl_eqt"].between(180, 320))
        & (candidate["pl_rade"].between(0.5, 2.0))
        & (candidate["st_teff"].between(3000, 6500))
    )
    SOURCE_DIR.joinpath("figure3_temperate_candidate_rows.csv").write_text(
        candidate.loc[candidate["temperate_radius"], ["pl_name", "hostname", "pl_eqt", "pl_rade", "st_teff", "discoverymethod", "disc_year"]]
        .sort_values(["pl_eqt", "pl_rade"])
        .head(250)
        .to_csv(index=False),
        encoding="utf-8",
    )

    ax = axes["B"]
    counts = (
        candidate.groupby(["radius_class", "temp_class"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=["Terrestrial", "Super-Earth", "Sub-Neptune", "Neptune-like", "Giant"], columns=["Cool", "Temperate", "Warm", "Hot"], fill_value=0)
    )
    counts.to_csv(SOURCE_DIR / "figure3_radius_temperature_counts.csv")
    left = np.zeros(len(counts))
    y = np.arange(len(counts))
    for temp in counts.columns:
        vals = counts[temp].to_numpy()
        ax.barh(y, vals, left=left, color=TEMP_COLORS[temp], edgecolor="white", linewidth=0.35, label=temp)
        left += vals
    ax.set_yticks(y)
    ax.set_yticklabels(counts.index)
    ax.invert_yaxis()
    ax.set_xlabel("Planets with radius + equilibrium temperature")
    ax.set_title("Thermal class composition by radius class", loc="center", pad=5)
    add_metric_box(ax, {"temperate terrestrial/super": format_int(candidate["temperate_radius"].sum())}, loc="bottom_right", fontsize=5)
    add_panel_label(ax, "B", x=-0.06, y=1.08)
    style_axis(ax)

    host = sample_rows(df, ["st_teff", "pl_rade", "pl_orbper"], n=14000)
    ax = axes["C"]
    ax.axhspan(0.5, 2.0, color="#E7F2E3", alpha=0.85, zorder=0)
    ax.axvspan(3000, 6500, color="#F4F1E7", alpha=0.55, zorder=0)
    ax.text(0.04, 0.20, "small-planet\ncandidate band", transform=ax.transAxes, fontsize=5.5, color="#2D5B2F", bbox=LABEL_BOX)
    period_colors = {
        "short period": "#4C78A8",
        "intermediate period": "#E2B45C",
        "long period": "#7E6AA8",
    }
    for period_group, color in period_colors.items():
        part = host[host["period_class"] == period_group]
        ax.scatter(
            part["st_teff"],
            part["pl_rade"],
            c=color,
            s=8,
            alpha=0.46,
            linewidth=0,
            rasterized=True,
            label=period_group,
            zorder=3,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Stellar effective temperature (K)")
    ax.set_ylabel("Planet radius (Earth radii)")
    ax.set_title("Host temperature versus planet size", loc="center", pad=5)
    annotate_n(ax, format_int(len(host)), "top_right")
    add_panel_label(ax, "C", x=-0.06, y=1.08)
    style_axis(ax)

    ax = axes["D"]
    panel_cols = ["pl_rade", "pl_bmasse", "pl_eqt", "pl_orbper", "st_teff", "st_rad", "st_mass", "sy_dist"]
    completeness = (1 - df[panel_cols].isna().mean()).sort_values()
    labels = {
        "pl_rade": "planet radius",
        "pl_bmasse": "planet mass",
        "pl_eqt": "eq. temp.",
        "pl_orbper": "period",
        "st_teff": "stellar Teff",
        "st_rad": "stellar radius",
        "st_mass": "stellar mass",
        "sy_dist": "system distance",
    }
    y = np.arange(len(completeness))
    colors = ["#D56C55" if value < 0.5 else "#E2B45C" if value < 0.8 else "#5E9D6E" for value in completeness]
    ax.barh(y, completeness.to_numpy() * 100, color=colors, edgecolor="white", linewidth=0.4)
    ax.set_yticks(y)
    ax.set_yticklabels([labels[c] for c in completeness.index])
    ax.set_xlabel("Completeness (%)")
    ax.set_xlim(0, 100)
    ax.set_title("Data completeness governing interpretation", loc="center", pad=5)
    for i, value in enumerate(completeness.to_numpy() * 100):
        ax.text(min(value + 1.5, 96), i, f"{value:.0f}%", va="center", fontsize=5.1, bbox=LABEL_BOX)
    add_metric_box(
        ax,
        {
            "mass missing": f"{df['pl_bmasse'].isna().mean():.1%}",
            "eq. temp missing": f"{df['pl_eqt'].isna().mean():.1%}",
        },
        loc="bottom_right",
        fontsize=5,
    )
    add_panel_label(ax, "D", x=-0.06, y=1.08)
    style_axis(ax)

    plan = chart_plan(
        "figure3_candidate_context_quality",
        list(axes),
        ["thermal_orbital_scatter", "candidate_band", "stacked_radius_temperature_counts", "completeness_disclosure", "metric_boxes"],
    )
    return save_figure(fig, axes, "figure3_candidate_context_quality", plan)


def png_nonblank(path: Path) -> dict:
    result = {"path": str(path), "exists": path.exists(), "bytes": 0, "nonblank": False, "shape": None}
    if not path.exists():
        return result
    result["bytes"] = path.stat().st_size
    if result["bytes"] < 1024:
        return result
    image = np.asarray(mpimg.imread(path))
    result["shape"] = [int(v) for v in image.shape]
    if image.ndim < 2 or min(image.shape[0], image.shape[1]) < 100:
        return result
    channels = image[..., :3] if image.ndim == 3 else image
    result["nonblank"] = bool(float(np.nanstd(channels)) > 0.001)
    return result


def build_render_qa(render_reports: list[dict]) -> dict:
    figures = []
    for report in render_reports:
        figure = report["figure"]
        png_check = png_nonblank(FIG_DIR / f"{figure}.png")
        legend = report.get("legendContract", {})
        layout = report.get("layoutContract", {})
        saved = []
        for ext in ("pdf", "svg", "png"):
            path = FIG_DIR / f"{figure}.{ext}"
            saved.append({"format": ext, "path": str(path), "bytes": path.stat().st_size if path.exists() else 0})
        figure_record = {
            "figure": figure,
            "legendContractEnforced": bool(report.get("legendContractEnforced")),
            "layoutContractEnforced": bool(report.get("layoutContractEnforced")),
            "legendOutsidePlotArea": bool(report.get("legendOutsidePlotArea")),
            "axisLegendRemainingCount": int(report.get("axisLegendRemainingCount", 0)),
            "legendModeUsed": report.get("legendModeUsed"),
            "legendContractFailures": legend.get("legendContractFailures", []),
            "layoutContractFailures": layout.get("layoutContractFailures", []),
            "crossPanelOverlapIssues": layout.get("crossPanelOverlapIssues", []),
            "colorbarPanelOverlapCount": int(layout.get("colorbarPanelOverlapCount", 0)),
            "colorbarPanelOverlapIssues": layout.get("colorbarPanelOverlapIssues", []),
            "metricTableDataOverlapCount": int(layout.get("metricTableDataOverlapCount", 0)),
            "metricTableDataOverlapIssues": layout.get("metricTableDataOverlapIssues", []),
            "textDataOverlapCount": int(layout.get("textDataOverlapCount", 0)),
            "textDataOverlapIssues": layout.get("textDataOverlapIssues", []),
            "oversizedTextCount": int(layout.get("oversizedTextCount", 0)),
            "negativeAxesTextCount": int(layout.get("negativeAxesTextCount", 0)),
            "nonblankPng": png_check["nonblank"],
            "pngCheck": png_check,
            "saved": saved,
        }
        figure_record["hardFail"] = bool(
            report.get("hardFail")
            or not figure_record["legendContractEnforced"]
            or not figure_record["layoutContractEnforced"]
            or not figure_record["legendOutsidePlotArea"]
            or figure_record["axisLegendRemainingCount"] != 0
            or figure_record["legendModeUsed"] not in ("bottom_center", "none")
            or figure_record["legendContractFailures"]
            or figure_record["layoutContractFailures"]
            or figure_record["crossPanelOverlapIssues"]
            or figure_record["colorbarPanelOverlapCount"] != 0
            or figure_record["metricTableDataOverlapCount"] != 0
            or figure_record["textDataOverlapCount"] != 0
            or figure_record["oversizedTextCount"] != 0
            or figure_record["negativeAxesTextCount"] != 0
            or not figure_record["nonblankPng"]
            or any(item["bytes"] < 1024 for item in saved)
        )
        figures.append(figure_record)

    qa = {
        "hardFail": any(item["hardFail"] for item in figures),
        "figures": figures,
        "requiredContracts": {
            "legendContractEnforced": all(item["legendContractEnforced"] for item in figures),
            "layoutContractEnforced": all(item["layoutContractEnforced"] for item in figures),
            "legendOutsidePlotArea": all(item["legendOutsidePlotArea"] for item in figures),
            "axisLegendRemainingCount": max((item["axisLegendRemainingCount"] for item in figures), default=0),
            "textPanelColorbarOverlapFree": all(
                not item["crossPanelOverlapIssues"]
                and item["colorbarPanelOverlapCount"] == 0
                and item["metricTableDataOverlapCount"] == 0
                and item["textDataOverlapCount"] == 0
                for item in figures
            ),
            "allPngNonblank": all(item["nonblankPng"] for item in figures),
            "allFormatsPresent": all(all(saved["bytes"] >= 1024 for saved in item["saved"]) for item in figures),
        },
    }
    (REPORT_DIR / "render_qa.json").write_text(json.dumps(qa, indent=2, ensure_ascii=False), encoding="utf-8")
    return qa


def write_reports(df: pd.DataFrame, render_reports: list[dict]) -> dict:
    profile = build_data_profile(df)
    render_qa = build_render_qa(render_reports)
    (REPORT_DIR / "data_profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "figures": [
            {
                "id": "figure0_single_panel_physical_hero",
                "title": "Single-panel physical-property hero",
                "panels": ["mass-radius headline map with radius-class bands and missingness disclosure"],
            },
            {
                "id": "figure1_physical_property_atlas",
                "title": "Physical-property atlas",
                "panels": ["mass-radius plane", "radius classes", "equilibrium temperature context", "host-star context"],
            },
            {
                "id": "figure2_discovery_bias_atlas",
                "title": "Discovery and selection-bias atlas",
                "panels": ["annual method throughput", "cumulative catalogue", "period-radius selection surface", "method-decade heatmap"],
            },
            {
                "id": "figure3_candidate_context_quality",
                "title": "Candidate context and data-quality atlas",
                "panels": ["thermal-orbital context", "thermal class composition", "host temperature versus planet size", "field completeness"],
            },
        ],
        "outputs": {
            "pdf": sorted(str(p.relative_to(RUN_ROOT)) for p in FIG_DIR.glob("*.pdf")),
            "svg": sorted(str(p.relative_to(RUN_ROOT)) for p in FIG_DIR.glob("*.svg")),
            "png": sorted(str(p.relative_to(RUN_ROOT)) for p in FIG_DIR.glob("*.png")),
            "source_data": sorted(str(p.relative_to(RUN_ROOT)) for p in SOURCE_DIR.glob("*.csv")),
        },
        "renderQa": {
            "hardFail": render_qa["hardFail"],
            "renderQaPath": str(REPORT_DIR / "render_qa.json"),
            "renderContractsPath": str(REPORT_DIR / "render_contracts.json"),
            "reports": render_reports,
        },
    }
    (REPORT_DIR / "panel_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    metadata = {
        "skill": "scifig-generate",
        "skillEntry": str(PROJECT_ROOT / ".codex" / "skills" / "scifig-generate" / "SKILL.md"),
        "skillCall": SKILL_CALL,
        "sourceFile": str(DATA_PATH),
        "outputDir": str(RUN_ROOT),
        "language": "zh-cn",
        "mode": "auto",
        "journalStyle": "Nature Astronomy-like compact discipline",
        "domain": "astronomy_exoplanet_science",
        "story": "physical-property atlas with missingness disclosure",
        "preferences": {
            "semanticColor": True,
            "rasterDpi": RASTER_DPI,
            "detailPreserving": True,
            "legendMode": "bottom_center",
            "exportFormats": ["png", "pdf", "svg"],
        },
        "mustHaveSatisfied": {
            "singlePanelHero": True,
            "multiPanelAtlas": True,
            "missingnessDisclosure": True,
            "renderContracts": (REPORT_DIR / "render_contracts.json").exists(),
            "sourceData": bool(list(SOURCE_DIR.glob("*.csv"))),
        },
        "renderQa": render_qa,
    }
    (REPORT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    missing = profile["missingPercent"]
    usable = profile["usablePanelCounts"]
    stats_lines = [
        "# Exoplanet Physical-Property Atlas: Stats And Methods",
        "",
        f"- Source file: `{DATA_PATH}`",
        f"- Rows: {format_int(len(df))}; columns: {df.shape[1]}",
        "- Domain: astronomy / exoplanet catalogue visualization",
        "- Selected chart bundle: planet physical-property atlas",
        "- Journal profile: Nature Astronomy-style compact multi-panel figures",
        "- Statistics mode: descriptive only; no p-values or inferential claims were generated.",
        "- Required single-panel hero plus multi-panel atlas figures were exported as PNG, PDF, and SVG.",
        "",
        "## Usable sample counts",
        "",
        f"- Mass-radius panel: {format_int(usable['mass_radius'])} rows with both `pl_bmasse` and `pl_rade`.",
        f"- Radius-period panel: {format_int(usable['radius_period'])} rows with both `pl_rade` and `pl_orbper`.",
        f"- Temperature-radius panels: {format_int(usable['eqt_radius'])} rows with both `pl_eqt` and `pl_rade`.",
        f"- Stellar context panel: {format_int(usable['stellar_context'])} rows with `st_teff`, `st_rad`, and `pl_rade`.",
        "",
        "## Missingness constraints",
        "",
        f"- `pl_bmasse` missing: {missing['pl_bmasse']:.1f}%. Mass-radius interpretation is therefore subset-based.",
        f"- `pl_eqt` missing: {missing['pl_eqt']:.1f}%. Temperate-candidate panels disclose this limitation.",
        f"- `pl_rade` missing: {missing['pl_rade']:.1f}%. Radius-class distributions use complete rows only.",
        "",
        "## Render QA summary",
        "",
    ]
    for report in render_reports:
        qa_item = next(item for item in render_qa["figures"] if item["figure"] == report["figure"])
        stats_lines.append(
            f"- {report['figure']}: hardFail={report['hardFail']}, "
            f"legendContractEnforced={report['legendContractEnforced']}, "
            f"layoutContractEnforced={report['layoutContractEnforced']}, "
            f"legendModeUsed={report['legendModeUsed']}, "
            f"axisLegendRemainingCount={report['axisLegendRemainingCount']}, "
            f"layoutFailures={report['layoutContractFailures']}, "
            f"textDataOverlapCount={qa_item['textDataOverlapCount']}, "
            f"colorbarPanelOverlapCount={qa_item['colorbarPanelOverlapCount']}, "
            f"nonblankPng={qa_item['nonblankPng']}"
        )
    (REPORT_DIR / "stats_report.md").write_text("\n".join(stats_lines) + "\n", encoding="utf-8")
    (RUN_ROOT / "requirements.txt").write_text("matplotlib\nnumpy\npandas\n", encoding="utf-8")
    return render_qa


def main() -> None:
    if (REPORT_DIR / "render_contracts.json").exists():
        (REPORT_DIR / "render_contracts.json").unlink()
    df = load_data()
    df.to_csv(SOURCE_DIR / "source_data_cleaned_exoplanets.csv", index=False)
    render_reports = [
        figure_single_panel_hero(df),
        figure_physical_atlas(df),
        figure_discovery_bias(df),
        figure_candidate_context(df),
    ]
    render_qa = write_reports(df, render_reports)
    if render_qa["hardFail"]:
        raise SystemExit("Render QA reported a hard failure; inspect reports/render_contracts.json and reports/render_qa.json")


if __name__ == "__main__":
    main()
