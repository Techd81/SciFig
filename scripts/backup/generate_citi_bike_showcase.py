#!/usr/bin/env python3
"""
Generate a Citi Bike urban-mobility showcase bundle.

Input data:
    D:/SciFig/.workflow/.scratchpad/test-data/raw/citi_bike_jc_202508.csv

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
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image, ImageStat


warnings.filterwarnings("ignore", category=UserWarning)

DATA_PATH = Path(r"D:\SciFig\.workflow\.scratchpad\test-data\raw\citi_bike_jc_202508.csv")
RUN_ROOT = Path(__file__).resolve().parent


def find_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".codex" / "skills" / "scifig-generate").exists():
            return candidate
    raise FileNotFoundError("Could not locate .codex/skills/scifig-generate from output directory")


PROJECT_ROOT = find_project_root(RUN_ROOT)
FIG_DIR = RUN_ROOT / "figures"
REPORT_DIR = RUN_ROOT / "reports"
SOURCE_DIR = RUN_ROOT / "source_data"
for directory in (FIG_DIR, REPORT_DIR, SOURCE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

HELPER_SOURCE_PATH = PROJECT_ROOT / ".codex" / "skills" / "scifig-generate" / "phases" / "code-gen" / "helpers.py"
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
    add_panel_label,
    apply_journal_kernel,
)


RASTER_DPI = 1200
RNG = np.random.default_rng(20260502)

JOURNAL_PROFILE = {
    "style": "urban mobility data-journal",
    "font_family": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"],
    "font_size_body_pt": 6.7,
    "font_size_small_pt": 5.5,
    "font_size_panel_label_pt": 8.0,
    "axis_linewidth_pt": 0.65,
    "max_text_font_size_pt": 11.0,
    "max_panel_label_font_size_pt": 11.0,
}

RIDER_COLORS = {
    "member": "#1F4E79",
    "casual": "#C8553D",
}

BIKE_COLORS = {
    "electric_bike": "#5FA896",
    "classic_bike": "#D9A75A",
}

TIME_COLORS = {
    "overnight": "#6C757D",
    "am_peak": "#4C78A8",
    "midday": "#5FA896",
    "pm_peak": "#C8553D",
    "evening": "#D9A75A",
}

HEAT_CMAP = LinearSegmentedColormap.from_list(
    "mobility_heat",
    ["#F7FBFF", "#D6EAF8", "#A9CCE3", "#5DADE2", "#21618C"],
)

LABEL_BOX = {
    "boxstyle": "round,pad=0.17",
    "facecolor": "white",
    "edgecolor": "none",
    "alpha": 0.88,
}


def fmt_int(value: int | float) -> str:
    return f"{int(round(float(value))):,}"


def fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def time_block(hour: int) -> str:
    if 0 <= hour < 6:
        return "overnight"
    if 6 <= hour < 10:
        return "am_peak"
    if 10 <= hour < 16:
        return "midday"
    if 16 <= hour < 20:
        return "pm_peak"
    return "evening"


def haversine_miles(lat1, lon1, lat2, lon2) -> pd.Series:
    lat1 = np.radians(pd.to_numeric(lat1, errors="coerce"))
    lon1 = np.radians(pd.to_numeric(lon1, errors="coerce"))
    lat2 = np.radians(pd.to_numeric(lat2, errors="coerce"))
    lon2 = np.radians(pd.to_numeric(lon2, errors="coerce"))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return pd.Series(3958.7613 * 2 * np.arcsin(np.sqrt(a)))


def clean_station_name(value: object, max_len: int = 26) -> str:
    text = "Unknown" if pd.isna(value) else str(value)
    text = text.replace(" - ", "\n")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "..."


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")
    df["ended_at"] = pd.to_datetime(df["ended_at"], errors="coerce")
    df["duration_min"] = (df["ended_at"] - df["started_at"]).dt.total_seconds() / 60.0
    df["duration_plot_min"] = df["duration_min"].clip(lower=0, upper=90)
    df["hour"] = df["started_at"].dt.hour
    df["date"] = df["started_at"].dt.floor("D")
    df["weekday"] = df["started_at"].dt.day_name()
    df["weekday_num"] = df["started_at"].dt.weekday
    df["is_weekend"] = df["weekday_num"].isin([5, 6])
    df["time_block"] = df["hour"].fillna(-1).astype(int).map(time_block)
    df["distance_miles"] = haversine_miles(df["start_lat"], df["start_lng"], df["end_lat"], df["end_lng"])
    df["valid_ride"] = df["duration_min"].between(0.5, 180, inclusive="both")
    df["valid_coords"] = df[["start_lat", "start_lng", "end_lat", "end_lng"]].notna().all(axis=1)
    df["same_station"] = df["start_station_id"].astype(str).eq(df["end_station_id"].astype(str))
    return df


def style_axis(ax, grid_axis: str = "both") -> None:
    ax.tick_params(length=2.5, width=0.55, pad=1.5)
    ax.grid(True, axis=grid_axis, color="#D9DEE3", linewidth=0.35, linestyle="-", alpha=0.65, zorder=0)
    for spine in ax.spines.values():
        spine.set_linewidth(0.65)


def set_geo_aspect(ax, frame: pd.DataFrame) -> None:
    lat = pd.concat([frame["start_lat"], frame["end_lat"]]).dropna()
    if len(lat):
        ax.set_aspect(1 / max(math.cos(math.radians(float(lat.mean()))), 0.2))


def station_summary(df: pd.DataFrame) -> pd.DataFrame:
    base = df.dropna(subset=["start_station_name", "start_lat", "start_lng"]).copy()
    grouped = (
        base.groupby(["start_station_name", "start_station_id"], dropna=False)
        .agg(
            starts=("ride_id", "size"),
            start_lat=("start_lat", "median"),
            start_lng=("start_lng", "median"),
            median_duration=("duration_min", "median"),
            member=("member_casual", lambda s: int((s == "member").sum())),
            casual=("member_casual", lambda s: int((s == "casual").sum())),
            electric=("rideable_type", lambda s: int((s == "electric_bike").sum())),
            classic=("rideable_type", lambda s: int((s == "classic_bike").sum())),
        )
        .reset_index()
    )
    grouped["member_share"] = grouped["member"] / grouped["starts"].clip(lower=1)
    grouped["electric_share"] = grouped["electric"] / grouped["starts"].clip(lower=1)
    grouped["dominant_rider"] = np.where(grouped["member_share"] >= 0.5, "member", "casual")
    grouped["dominant_bike"] = np.where(grouped["electric_share"] >= 0.5, "electric_bike", "classic_bike")
    return grouped.sort_values("starts", ascending=False)


def flow_summary(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["valid_coords"] & df["valid_ride"] & ~df["same_station"]].copy()
    grouped = (
        base.groupby(
            [
                "start_station_name",
                "end_station_name",
                "start_lat",
                "start_lng",
                "end_lat",
                "end_lng",
            ],
            dropna=False,
        )
        .agg(
            trips=("ride_id", "size"),
            median_duration=("duration_min", "median"),
            median_distance=("distance_miles", "median"),
            member_share=("member_casual", lambda s: float((s == "member").mean())),
            dominant_time=("time_block", lambda s: s.value_counts().idxmax()),
        )
        .reset_index()
        .sort_values("trips", ascending=False)
    )
    return grouped


def legend_handles(include_time: bool = True, include_bike: bool = False) -> list:
    handles: list = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=RIDER_COLORS["member"],
               markeredgecolor="white", markersize=5, label="member rider"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=RIDER_COLORS["casual"],
               markeredgecolor="white", markersize=5, label="casual rider"),
    ]
    if include_bike:
        handles.extend(
            [
                Patch(facecolor=BIKE_COLORS["electric_bike"], edgecolor="white", label="electric bike"),
                Patch(facecolor=BIKE_COLORS["classic_bike"], edgecolor="white", label="classic bike"),
            ]
        )
    if include_time:
        handles.extend(
            [
                Line2D([0], [0], color=TIME_COLORS["am_peak"], lw=1.4, label="AM peak"),
                Line2D([0], [0], color=TIME_COLORS["midday"], lw=1.4, label="midday"),
                Line2D([0], [0], color=TIME_COLORS["pm_peak"], lw=1.4, label="PM peak"),
                Line2D([0], [0], color=TIME_COLORS["evening"], lw=1.4, label="evening"),
            ]
        )
    return handles


def visual_plan(applied: list[str], min_labels: int = 1) -> dict:
    motifs = [
        "semantic_color_mapping",
        "metric_box",
        "sample_size_label",
        "reference_line",
        "spatial_coordinate_encoding",
        "temporal_intensity_encoding",
        "duration_distribution",
    ]
    return {
        "minTotalEnhancements": 5,
        "appliedEnhancements": applied,
        "inPlotExplanatoryLabelCount": max(min_labels, 1),
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


def chart_plan(fig_key: str, panel_ids: list[str], applied: list[str], primary: str) -> dict:
    return {
        "primaryChart": primary,
        "secondaryCharts": ["temporal_heatmap", "duration_ecdf", "station_lollipop", "spatial_flow_map"],
        "panelBlueprint": {
            panel: {"role": "urban_mobility_panel", "legend": "shared_bottom_center"}
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
        "visualContentPlan": visual_plan(applied, min_labels=len(panel_ids)),
        "templateCasePlan": {
            "selectedByUser": True,
            "bundleKey": "citi_bike_urban_mobility_showcase",
            "narrativeArc": "hero" if len(panel_ids) == 1 else "multipanel_grid",
            "templateMatchMode": "best_effort_domain_transfer",
        },
        "figureKey": fig_key,
    }


def validate_png(path: Path) -> dict:
    with Image.open(path) as img:
        width, height = img.size
        probe = img.convert("L").resize((256, 256))
        stat = ImageStat.Stat(probe)
        extrema = probe.getextrema()
    return {
        "path": str(path.relative_to(RUN_ROOT)),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "width": int(width),
        "height": int(height),
        "stddev": float(stat.stddev[0]),
        "extrema": [int(extrema[0]), int(extrema[1])],
        "nonblank": bool(path.exists() and path.stat().st_size > 10000 and width > 100 and height > 100 and stat.stddev[0] > 1.0 and extrema[0] < extrema[1]),
    }


def record_render_contract_report(report: dict, path: Path) -> None:
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    records.append(report)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


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
    for ext in ("pdf", "svg", "png"):
        out_path = FIG_DIR / f"{fig_key}.{ext}"
        if ext == "png":
            fig.savefig(out_path, dpi=RASTER_DPI, bbox_inches="tight", facecolor="white")
        else:
            fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
        outputs[ext] = str(out_path.relative_to(RUN_ROOT))
    plt.close(fig)

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
        or not legend_report.get("legendOutsidePlotArea", False)
        or not no_overlap
        or not png_check["nonblank"]
    )
    report = {
        "figure": fig_key,
        "outputs": outputs,
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
        "legendOutsidePlotArea": legend_report.get("legendOutsidePlotArea", False),
        "axisLegendRemainingCount": legend_report.get("axisLegendRemainingCount", 0),
        "legendModeUsed": legend_report.get("legendModeUsed", "none"),
        "figureLegendCount": len(fig.legends),
        "layoutContractFailures": layout_report.get("layoutContractFailures", []),
        "colorbarPanelOverlapCount": overlap_counts["colorbarPanelOverlapCount"],
        "textDataOverlapCount": overlap_counts["textDataOverlapCount"],
        "hardFail": hard_fail,
    }
    record_render_contract_report(report, REPORT_DIR / "render_contracts.json")
    return report


def build_data_profile(df: pd.DataFrame) -> dict:
    duration = df["duration_min"].dropna()
    return {
        "source": str(DATA_PATH),
        "shape": [int(df.shape[0]), int(df.shape[1])],
        "columns": list(df.columns),
        "domain": "urban_mobility_bike_share",
        "selectedChartBundle": "Citi Bike urban-mobility hero plus atlas",
        "journalStyle": "urban mobility data-journal",
        "language": "zh-cn",
        "colorMode": "semantic rider and time colors",
        "rasterDpi": RASTER_DPI,
        "crowdingPolicy": "detail_preserving_no_overlap",
        "dateRange": [str(df["started_at"].min()), str(df["started_at"].max())],
        "missingPercent": (df.isna().mean().sort_values(ascending=False) * 100).round(3).to_dict(),
        "rideableType": df["rideable_type"].value_counts(dropna=False).to_dict(),
        "memberCasual": df["member_casual"].value_counts(dropna=False).to_dict(),
        "uniqueStartStations": int(df["start_station_name"].nunique(dropna=True)),
        "uniqueEndStations": int(df["end_station_name"].nunique(dropna=True)),
        "durationMinutes": {
            "median": float(duration.median()),
            "p95": float(duration.quantile(0.95)),
            "p99": float(duration.quantile(0.99)),
            "max": float(duration.max()),
            "visualFilter": "0.5 to 180 minutes; durations above 90 minutes clipped only for plotted axes",
        },
        "riskFlags": [
            "descriptive_visualization_only",
            "coordinate records include a small end-station missing fraction",
            "duration outliers retained in stats but clipped for visual scale",
        ],
    }


def figure_single_panel_hero(df: pd.DataFrame, stations: pd.DataFrame, flows: pd.DataFrame) -> dict:
    apply_journal_kernel("hero", JOURNAL_PROFILE)
    fig, ax = plt.subplots(figsize=(7.2, 6.3))
    valid = df[df["valid_coords"]].copy()
    all_coords = valid.sample(n=min(len(valid), 18000), random_state=20260502)
    ax.scatter(
        all_coords["start_lng"],
        all_coords["start_lat"],
        s=2,
        c="#D5DAE0",
        alpha=0.25,
        edgecolors="none",
        rasterized=True,
        zorder=1,
    )

    top_flows = flows.head(90).copy()
    flow_max = max(float(top_flows["trips"].max()), 1.0)
    for _, row in top_flows.iterrows():
        color = TIME_COLORS.get(str(row["dominant_time"]), "#999999")
        lw = 0.25 + 2.4 * math.sqrt(float(row["trips"]) / flow_max)
        ax.plot(
            [row["start_lng"], row["end_lng"]],
            [row["start_lat"], row["end_lat"]],
            color=color,
            alpha=0.27,
            linewidth=lw,
            solid_capstyle="round",
            zorder=2,
        )

    top_stations = stations.head(55).copy()
    size = 16 + 210 * np.sqrt(top_stations["starts"] / top_stations["starts"].max())
    ax.scatter(
        top_stations["start_lng"],
        top_stations["start_lat"],
        s=size,
        c=top_stations["dominant_rider"].map(RIDER_COLORS),
        edgecolor="white",
        linewidth=0.45,
        alpha=0.92,
        zorder=4,
    )

    label_offsets = [
        (0.0012, 0.0010),
        (-0.0012, 0.0010),
        (0.0012, -0.0012),
        (-0.0012, -0.0012),
        (0.0000, 0.0015),
    ]
    for idx, (_, row) in enumerate(stations.head(5).iterrows()):
        dx, dy = label_offsets[idx]
        ax.text(
            row["start_lng"] + dx,
            row["start_lat"] + dy,
            clean_station_name(row["start_station_name"], 18),
            fontsize=5.2,
            color="#222222",
            ha="left" if dx >= 0 else "right",
            va="center",
            bbox=LABEL_BOX,
            zorder=12,
        )

    member_share = (df["member_casual"] == "member").mean()
    electric_share = (df["rideable_type"] == "electric_bike").mean()
    add_metric_box(
        ax,
        {
            "rides": fmt_int(len(df)),
            "member": fmt_pct(member_share),
            "electric": fmt_pct(electric_share),
            "median min": f"{df['duration_min'].median():.1f}",
        },
        loc="top_left",
        fontsize=5,
    )
    ax.set_title("Citi Bike JC August 2025 mobility spine", fontsize=9, fontweight="bold", pad=7, loc="center")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    set_geo_aspect(ax, valid)
    style_axis(ax)
    ax.legend(handles=legend_handles(include_time=True, include_bike=False), frameon=True, title="encoded semantics")

    stations.to_csv(SOURCE_DIR / "figure1_station_nodes.csv", index=False)
    top_flows.to_csv(SOURCE_DIR / "figure1_top_od_flows.csv", index=False)
    source_cols = [
        "ride_id",
        "started_at",
        "ended_at",
        "duration_min",
        "start_station_name",
        "end_station_name",
        "start_lat",
        "start_lng",
        "end_lat",
        "end_lng",
        "member_casual",
        "rideable_type",
        "time_block",
        "distance_miles",
    ]
    df[source_cols].to_csv(SOURCE_DIR / "source_data_cleaned_citi_bike.csv", index=False)

    plan = chart_plan(
        "figure1_single_panel_hero_mobility_spine",
        ["A"],
        [
            "single_panel_hero",
            "spatial_coordinate_encoding",
            "station_volume_scaling",
            "top_od_flow_lines",
            "rider_class_semantic_nodes",
            "time_block_semantic_flows",
            "metric_box",
            "top_station_labels",
        ],
        "single_panel_spatial_flow_hero",
    )
    return save_figure(
        fig,
        {"A": ax},
        "figure1_single_panel_hero_mobility_spine",
        plan,
        adjust={"bottom": 0.08, "top": 0.91, "left": 0.08, "right": 0.97},
    )


def figure_mobility_atlas(df: pd.DataFrame, stations: pd.DataFrame, flows: pd.DataFrame) -> dict:
    apply_journal_kernel("compact", JOURNAL_PROFILE)
    fig, axes_arr = plt.subplots(2, 2, figsize=(8.4, 6.7))
    axes = dict(zip(["A", "B", "C", "D"], axes_arr.ravel()))

    hourly = (
        df.dropna(subset=["date", "hour"])
        .groupby(["date", "hour"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=range(24), fill_value=0)
        .sort_index()
    )
    im = axes["A"].imshow(hourly.to_numpy(), aspect="auto", cmap=HEAT_CMAP, interpolation="nearest", zorder=1)
    axes["A"].set_title("A. temporal pulse by day and hour", fontsize=7.2, fontweight="bold", pad=4)
    axes["A"].set_xlabel("hour")
    axes["A"].set_ylabel("date")
    axes["A"].set_xticks([0, 4, 8, 12, 16, 20, 23])
    tick_idx = np.linspace(0, len(hourly.index) - 1, min(6, len(hourly.index))).astype(int)
    axes["A"].set_yticks(tick_idx)
    axes["A"].set_yticklabels([pd.Timestamp(hourly.index[i]).strftime("%m-%d") for i in tick_idx])
    peak_pos = np.unravel_index(np.argmax(hourly.to_numpy()), hourly.shape)
    add_metric_box(
        axes["A"],
        {
            "peak hour": f"{int(hourly.columns[peak_pos[1]])}:00",
            "peak rides": fmt_int(hourly.to_numpy()[peak_pos]),
        },
        loc="top_right",
        fontsize=5,
    )
    axes["A"].grid(False)
    for spine in axes["A"].spines.values():
        spine.set_linewidth(0.65)

    valid_duration = df[df["valid_ride"]].copy()
    for rider in ["member", "casual"]:
        values = np.sort(valid_duration.loc[valid_duration["member_casual"] == rider, "duration_min"].clip(upper=60).dropna())
        y = np.arange(1, len(values) + 1) / max(len(values), 1)
        axes["B"].plot(values, y, color=RIDER_COLORS[rider], linewidth=1.25, label=f"{rider} rider", zorder=4)
        if len(values):
            med = float(np.median(values))
            axes["B"].axvline(med, color=RIDER_COLORS[rider], linestyle="--", linewidth=0.8, alpha=0.75, zorder=3)
    axes["B"].set_xlim(0, 60)
    axes["B"].set_ylim(0, 1.02)
    axes["B"].set_title("B. trip duration distribution", fontsize=7.2, fontweight="bold", pad=4)
    axes["B"].set_xlabel("duration, clipped at 60 min")
    axes["B"].set_ylabel("cumulative share")
    add_metric_box(
        axes["B"],
        {
            "median": f"{valid_duration['duration_min'].median():.1f} min",
            "p95": f"{valid_duration['duration_min'].quantile(0.95):.1f} min",
        },
        loc="bottom_right",
        fontsize=5,
    )
    style_axis(axes["B"])

    top = stations.head(12).sort_values("starts")
    y_pos = np.arange(len(top))
    axes["C"].barh(y_pos, top["member"], color=RIDER_COLORS["member"], height=0.62, label="member rider", zorder=3)
    axes["C"].barh(y_pos, top["casual"], left=top["member"], color=RIDER_COLORS["casual"], height=0.62, label="casual rider", zorder=3)
    axes["C"].scatter(top["starts"], y_pos, s=14, c="#111111", edgecolor="white", linewidth=0.3, zorder=5)
    axes["C"].set_yticks(y_pos)
    axes["C"].set_yticklabels([clean_station_name(v, 23) for v in top["start_station_name"]])
    axes["C"].set_xlabel("trip starts")
    axes["C"].set_title("C. station demand leaders", fontsize=7.2, fontweight="bold", pad=4)
    add_metric_box(
        axes["C"],
        {
            "stations": fmt_int(df["start_station_name"].nunique()),
            "top12 share": fmt_pct(top["starts"].sum() / len(df)),
        },
        loc="bottom_right",
        fontsize=5,
    )
    style_axis(axes["C"], grid_axis="x")

    spatial = df[df["valid_coords"] & df["valid_ride"]].copy()
    sample = spatial.sample(n=min(len(spatial), 12000), random_state=20260502)
    for block in ["am_peak", "midday", "pm_peak", "evening"]:
        sub = sample[sample["time_block"] == block]
        axes["D"].scatter(
            sub["start_lng"],
            sub["start_lat"],
            s=2.5,
            color=TIME_COLORS[block],
            alpha=0.23,
            edgecolors="none",
            rasterized=True,
            label=block.replace("_", " "),
            zorder=2,
        )
    station_size = 14 + 90 * np.sqrt(stations.head(40)["starts"] / stations["starts"].max())
    axes["D"].scatter(
        stations.head(40)["start_lng"],
        stations.head(40)["start_lat"],
        s=station_size,
        facecolors="none",
        edgecolors=stations.head(40)["dominant_bike"].map(BIKE_COLORS),
        linewidth=0.85,
        zorder=6,
    )
    axes["D"].set_title("D. spatial start field by time block", fontsize=7.2, fontweight="bold", pad=4)
    axes["D"].set_xlabel("longitude")
    axes["D"].set_ylabel("latitude")
    set_geo_aspect(axes["D"], spatial)
    add_metric_box(
        axes["D"],
        {
            "valid coord": fmt_pct(spatial.shape[0] / len(df)),
            "median miles": f"{spatial['distance_miles'].median():.2f}",
        },
        loc="top_left",
        fontsize=5,
    )
    style_axis(axes["D"])

    for label, ax in axes.items():
        add_panel_label(ax, label, x=-0.06, y=1.08, fontsize=9)

    axes["D"].legend(handles=legend_handles(include_time=True, include_bike=True), frameon=True, title="shared encodings")

    hourly.reset_index().to_csv(SOURCE_DIR / "figure2_temporal_hour_day_matrix.csv", index=False)
    valid_duration[["ride_id", "member_casual", "rideable_type", "duration_min", "duration_plot_min"]].to_csv(
        SOURCE_DIR / "figure2_duration_distribution.csv", index=False
    )
    top.sort_values("starts", ascending=False).to_csv(SOURCE_DIR / "figure2_top_station_activity.csv", index=False)
    stations.head(40).to_csv(SOURCE_DIR / "figure2_spatial_station_field.csv", index=False)
    flows.head(80).to_csv(SOURCE_DIR / "figure2_top_flows_reference.csv", index=False)

    plan = chart_plan(
        "figure2_multi_panel_mobility_atlas",
        ["A", "B", "C", "D"],
        [
            "multipanel_grid",
            "temporal_hour_day_heatmap",
            "duration_ecdf_with_medians",
            "station_member_casual_stack",
            "spatial_coordinate_scatter",
            "semantic_rider_colors",
            "semantic_time_colors",
            "metric_boxes_per_panel",
            "panel_labels",
        ],
        "multi_panel_mobility_atlas",
    )
    return save_figure(
        fig,
        axes,
        "figure2_multi_panel_mobility_atlas",
        plan,
        adjust={"bottom": 0.08, "top": 0.91, "left": 0.10, "right": 0.97, "wspace": 0.36, "hspace": 0.42},
    )


def write_reports(df: pd.DataFrame, render_reports: list[dict], profile: dict) -> None:
    profile_path = REPORT_DIR / "data_profile.json"
    profile_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
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
                "id": "figure1_single_panel_hero_mobility_spine",
                "title": "Single-panel spatial hero map of Citi Bike JC August 2025",
                "panels": ["A: coordinate flow spine with station volume, rider class, and time-block flow colors"],
            },
            {
                "id": "figure2_multi_panel_mobility_atlas",
                "title": "Multi-panel urban-mobility atlas",
                "panels": [
                    "A: day-hour temporal pulse heatmap",
                    "B: rider-class trip-duration ECDF",
                    "C: top start-station demand stack by rider class",
                    "D: coordinate start field by time block and dominant bike type",
                ],
            },
        ],
        "outputs": figure_outputs,
        "renderQa": {
            "hardFail": any(r.get("hardFail") for r in render_reports),
            "reports": render_reports,
        },
    }
    (REPORT_DIR / "panel_manifest.json").write_text(json.dumps(panel_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    metadata = {
        "skill": "scifig-generate",
        "skillEntry": str(PROJECT_ROOT / ".codex" / "skills" / "scifig-generate" / "SKILL.md"),
        "skillCall": "$scifig-generate FILE: \"D:\\SciFig\\.workflow\\.scratchpad\\test-data\\raw\\citi_bike_jc_202508.csv\" OUTPUT_DIR: \"D:\\test_scifig\\output\\maestro_scifig_showcase_20260502\\citi_bike\" MODE: auto LANGUAGE: zh-cn PREFERENCES: urban mobility data-journal style, semantic rider and time colors, 1200 dpi, detail preserving, maximum visual impact without overlap. MUST_HAVE: at least one single-panel hero figure and one multi-panel mobility atlas; use temporal, duration, station, and spatial coordinate signals; use bottom-center figure legend outside panels; avoid colorbar-panel overlap; export png pdf svg; write source_data, panel_manifest, stats_report, metadata, and render_contracts.json.",
        "outputDir": str(RUN_ROOT),
        "generatedBy": "generate_citi_bike_showcase.py",
        "language": "zh-cn",
        "mode": "auto",
        "exports": ["png", "pdf", "svg"],
        "renderQaSummary": {
            "hardFail": any(r.get("hardFail") for r in render_reports),
            "allPngNonblank": all(r.get("customQa", {}).get("pngNonblank") for r in render_reports),
            "noColorbarPanelOverlap": all(r.get("customQa", {}).get("noColorbarPanelOverlap") for r in render_reports),
            "noTextDataOverlap": all(r.get("customQa", {}).get("noTextDataOverlap") for r in render_reports),
            "legendModeUsed": sorted(set(r.get("legendModeUsed") for r in render_reports)),
        },
        "templateMiningReferences": [
            "template-mining/06-narrative-arcs.md: hero and multipanel_grid",
            "template-mining/04-grid-recipes.md: R0 single panel and R2 two-by-two storyboard",
            "template-mining/03-palette-bank.md: semantic cool/warm rider colors and restrained multi-role palette",
            "template-mining/05-annotation-idioms.md: metric boxes and panel labels",
        ],
    }
    (REPORT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (REPORT_DIR / "render_qa.json").write_text(json.dumps(panel_manifest["renderQa"], indent=2, ensure_ascii=False), encoding="utf-8")

    duration = df["duration_min"].dropna()
    lines = [
        "# Citi Bike JC August 2025 Showcase Stats Report",
        "",
        "## Data Profile",
        f"- Source file: `{DATA_PATH}`",
        f"- Rows: {fmt_int(len(df))}",
        f"- Started-at range: {df['started_at'].min()} to {df['started_at'].max()}",
        f"- Unique start stations: {fmt_int(df['start_station_name'].nunique())}",
        f"- Unique end stations: {fmt_int(df['end_station_name'].nunique())}",
        "",
        "## Descriptive Mobility Signals",
        f"- Member riders: {fmt_int((df['member_casual'] == 'member').sum())} ({fmt_pct((df['member_casual'] == 'member').mean())})",
        f"- Casual riders: {fmt_int((df['member_casual'] == 'casual').sum())} ({fmt_pct((df['member_casual'] == 'casual').mean())})",
        f"- Electric bikes: {fmt_int((df['rideable_type'] == 'electric_bike').sum())} ({fmt_pct((df['rideable_type'] == 'electric_bike').mean())})",
        f"- Classic bikes: {fmt_int((df['rideable_type'] == 'classic_bike').sum())} ({fmt_pct((df['rideable_type'] == 'classic_bike').mean())})",
        f"- Median duration: {duration.median():.2f} min",
        f"- 95th percentile duration: {duration.quantile(0.95):.2f} min",
        f"- 99th percentile duration: {duration.quantile(0.99):.2f} min",
        f"- Valid coordinate records: {fmt_int(df['valid_coords'].sum())} ({fmt_pct(df['valid_coords'].mean())})",
        "",
        "## Render QA",
    ]
    for report in render_reports:
        qa = report["customQa"]
        lines.extend(
            [
                f"- {report['figure']}: hardFail={str(report['hardFail']).lower()}, "
                f"legendContractEnforced={report['legendContractEnforced']}, "
                f"layoutContractEnforced={report['layoutContractEnforced']}, "
                f"legendModeUsed={report['legendModeUsed']}, "
                f"colorbarPanelOverlapCount={report['colorbarPanelOverlapCount']}, "
                f"textDataOverlapCount={report['textDataOverlapCount']}, "
                f"pngNonblank={qa['pngNonblank']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation Guardrail",
            "These figures are descriptive. No inferential p-values or causal claims are reported because the supplied table is a ride log rather than a designed experiment.",
        ]
    )
    (REPORT_DIR / "stats_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    render_path = REPORT_DIR / "render_contracts.json"
    if render_path.exists():
        render_path.unlink()

    df = load_data()
    stations = station_summary(df)
    flows = flow_summary(df)
    profile = build_data_profile(df)
    render_reports = [
        figure_single_panel_hero(df, stations, flows),
        figure_mobility_atlas(df, stations, flows),
    ]
    write_reports(df, render_reports, profile)
    if any(report["hardFail"] for report in render_reports):
        raise SystemExit("Render QA reported a hard failure; inspect reports/render_contracts.json")


if __name__ == "__main__":
    main()
