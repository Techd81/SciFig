from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import gridspec
from matplotlib.colors import LinearSegmentedColormap


ROOT = Path(r"D:\test_scifig")
SKILL_ROOT = ROOT / ".codex" / "skills" / "scifig-generate"
INPUT_FILE = Path(r"D:\SciFig\.workflow\.scratchpad\test-data\raw\uci_power.csv")
OUTPUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUTPUT_DIR / "figures"
SOURCE_DIR = OUTPUT_DIR / "source_data"
REPORT_DIR = OUTPUT_DIR / "reports"
RENDER_CONTRACT_PATH = REPORT_DIR / "render_contracts.json"

for directory in (FIG_DIR, SOURCE_DIR, REPORT_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def read_executable_helper(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    stripped = source.strip()
    if stripped.startswith("```"):
        lines = source.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        source = "\n".join(lines) + "\n"
    return source


globals()["__SCIFIG_SKILL_ROOT__"] = str(SKILL_ROOT)
for helper_file in (
    SKILL_ROOT / "phases" / "code-gen" / "template_mining_helpers.py",
    SKILL_ROOT / "phases" / "code-gen" / "helpers.py",
):
    helper_source = read_executable_helper(helper_file)
    exec(compile(helper_source, str(helper_file), "exec"), globals())


JOURNAL_PROFILE = {
    "style": "energy_telemetry_signal_processing_showcase",
    "journalName": "Energy telemetry and signal-processing journal style",
    "font_family": ["DejaVu Sans"],
    "font_size_pt": 7,
    "font_size_axis_pt": 7,
    "font_size_panel_label_pt": 9,
    "max_text_font_size_pt": 12,
    "max_panel_label_font_size_pt": 10,
    "axes_linewidth": 0.85,
    "savefig_dpi": 1200,
}

CROWDING_PLAN = {
    "crowdingPolicy": "preserve_information",
    "overlapPriority": "clarity_first",
    "legendMode": "bottom_center",
    "legendAllowedModes": ["bottom_center"],
    "legendFrame": True,
    "legendFontSizePt": 7,
    "legendBottomAnchorY": 0.015,
    "legendBottomMarginMin": 0.06,
    "legendBottomMarginMax": 0.16,
    "maxTextFontSizePt": 12,
    "maxPanelLabelFontSizePt": 10,
    "colorbarMode": "none",
}

PALETTE = {
    "active": "#1F4E79",
    "active_light": "#A9CCE3",
    "reactive": "#6C757D",
    "voltage": "#C8553D",
    "voltage_light": "#F4A582",
    "intensity": "#2A9D8F",
    "sub1": "#4A6B8A",
    "sub2": "#D9A75A",
    "sub3": "#B85B5B",
    "residual": "#8D99AE",
    "grid": "#D8DEE9",
    "neutral": "#222222",
}

HEATMAP_CMAP = LinearSegmentedColormap.from_list(
    "load_semantic",
    ["#F7FBFF", "#D6EAF8", "#8FBBDD", "#3C7FB1", "#C8553D"],
)


def configure_style() -> None:
    apply_journal_kernel(variant="compact", journalProfile=JOURNAL_PROFILE)
    plt.rcParams.update(
        {
            "font.family": ["DejaVu Sans"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.titlesize": 8,
            "axes.labelsize": 7,
            "xtick.labelsize": 6,
            "ytick.labelsize": 6,
            "legend.fontsize": 7,
            "savefig.dpi": 1200,
            "savefig.bbox": "tight",
        }
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def fmt_value(value: float, suffix: str = "") -> str:
    if not np.isfinite(value):
        return "n/a"
    if abs(value) >= 1000:
        return f"{value / 1000:.1f}k{suffix}"
    if abs(value) >= 100:
        return f"{value:.0f}{suffix}"
    if abs(value) >= 10:
        return f"{value:.1f}{suffix}"
    return f"{value:.2f}{suffix}"


def style_axes(ax, grid_axis: str = "y") -> None:
    ax.grid(
        axis=grid_axis,
        color=PALETTE["grid"],
        linewidth=0.45,
        linestyle="--",
        alpha=0.75,
        zorder=0,
    )
    apply_chart_polish(ax, "line")


def add_letter(ax, label: str) -> None:
    add_panel_label(ax, label, x=-0.045, y=1.025, fontsize=9)


def load_and_derive() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    raw = pd.read_csv(
        INPUT_FILE,
        sep=";",
        na_values=["?"],
        low_memory=False,
    )
    raw["datetime"] = pd.to_datetime(
        raw["Date"] + " " + raw["Time"],
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce",
    )
    numeric_columns = [
        "Global_active_power",
        "Global_reactive_power",
        "Voltage",
        "Global_intensity",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3",
    ]
    for column in numeric_columns:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")
    raw = raw.dropna(subset=["datetime", *numeric_columns]).copy()
    raw = raw.sort_values("datetime").reset_index(drop=True)
    raw["date"] = raw["datetime"].dt.floor("D")
    raw["month"] = raw["datetime"].dt.to_period("M").dt.to_timestamp()
    raw["hour"] = raw["datetime"].dt.hour
    raw["minute_of_day"] = raw["datetime"].dt.hour * 60 + raw["datetime"].dt.minute
    raw["active_energy_wh"] = raw["Global_active_power"] * 1000.0 / 60.0
    raw["sub_total_wh"] = raw[["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]].sum(axis=1)
    raw["residual_wh"] = (raw["active_energy_wh"] - raw["sub_total_wh"]).clip(lower=0)
    raw["voltage_deviation"] = raw["Voltage"] - raw["Voltage"].median()

    daily = (
        raw.groupby("date", as_index=False)
        .agg(
            active_mean_kw=("Global_active_power", "mean"),
            active_p10_kw=("Global_active_power", lambda s: s.quantile(0.10)),
            active_p90_kw=("Global_active_power", lambda s: s.quantile(0.90)),
            voltage_mean=("Voltage", "mean"),
            voltage_p05=("Voltage", lambda s: s.quantile(0.05)),
            voltage_p95=("Voltage", lambda s: s.quantile(0.95)),
            intensity_mean=("Global_intensity", "mean"),
            sub1_wh=("Sub_metering_1", "sum"),
            sub2_wh=("Sub_metering_2", "sum"),
            sub3_wh=("Sub_metering_3", "sum"),
            residual_wh=("residual_wh", "sum"),
            total_wh=("active_energy_wh", "sum"),
        )
        .sort_values("date")
    )
    daily["active_14d_kw"] = daily["active_mean_kw"].rolling(14, min_periods=1).mean()
    daily["voltage_14d"] = daily["voltage_mean"].rolling(14, min_periods=1).mean()
    daily["submeter_share"] = np.where(
        daily["total_wh"] > 0,
        (daily["sub1_wh"] + daily["sub2_wh"] + daily["sub3_wh"]) / daily["total_wh"] * 100.0,
        np.nan,
    )

    hourly = (
        raw.groupby("hour", as_index=False)
        .agg(
            active_mean_kw=("Global_active_power", "mean"),
            active_p10_kw=("Global_active_power", lambda s: s.quantile(0.10)),
            active_p90_kw=("Global_active_power", lambda s: s.quantile(0.90)),
            voltage_mean=("Voltage", "mean"),
            intensity_mean=("Global_intensity", "mean"),
            sub1_wh=("Sub_metering_1", "sum"),
            sub2_wh=("Sub_metering_2", "sum"),
            sub3_wh=("Sub_metering_3", "sum"),
            residual_wh=("residual_wh", "sum"),
            total_wh=("active_energy_wh", "sum"),
        )
        .sort_values("hour")
    )
    for column in ["sub1_wh", "sub2_wh", "sub3_wh", "residual_wh"]:
        hourly[f"{column}_share"] = np.where(hourly["total_wh"] > 0, hourly[column] / hourly["total_wh"] * 100.0, 0)

    month_hour = (
        raw.groupby(["month", "hour"], as_index=False)
        .agg(
            active_mean_kw=("Global_active_power", "mean"),
            voltage_mean=("Voltage", "mean"),
            intensity_mean=("Global_intensity", "mean"),
        )
    )
    heatmap = month_hour.pivot(index="month", columns="hour", values="active_mean_kw").sort_index().fillna(0)

    monthly = (
        raw.groupby("month", as_index=False)
        .agg(
            active_mean_kw=("Global_active_power", "mean"),
            active_kwh=("active_energy_wh", lambda s: s.sum() / 1000.0),
            voltage_mean=("Voltage", "mean"),
            voltage_p05=("Voltage", lambda s: s.quantile(0.05)),
            intensity_mean=("Global_intensity", "mean"),
            sub1_kwh=("Sub_metering_1", lambda s: s.sum() / 1000.0),
            sub2_kwh=("Sub_metering_2", lambda s: s.sum() / 1000.0),
            sub3_kwh=("Sub_metering_3", lambda s: s.sum() / 1000.0),
            residual_kwh=("residual_wh", lambda s: s.sum() / 1000.0),
        )
        .sort_values("month")
    )
    monthly["metered_kwh"] = monthly[["sub1_kwh", "sub2_kwh", "sub3_kwh"]].sum(axis=1)
    monthly["metered_share"] = np.where(monthly["active_kwh"] > 0, monthly["metered_kwh"] / monthly["active_kwh"] * 100.0, np.nan)

    sample = raw.sample(n=min(60000, len(raw)), random_state=42).sort_values("datetime")
    source_profile = pd.DataFrame(
        {
            "metric": [
                "rows_after_dropna",
                "start_datetime",
                "end_datetime",
                "mean_active_power_kw",
                "p95_active_power_kw",
                "mean_voltage_v",
                "p05_voltage_v",
                "mean_global_intensity_a",
                "metered_share_pct",
            ],
            "value": [
                len(raw),
                raw["datetime"].min().isoformat(),
                raw["datetime"].max().isoformat(),
                raw["Global_active_power"].mean(),
                raw["Global_active_power"].quantile(0.95),
                raw["Voltage"].mean(),
                raw["Voltage"].quantile(0.05),
                raw["Global_intensity"].mean(),
                (raw[["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]].sum().sum() / raw["active_energy_wh"].sum()) * 100.0,
            ],
        }
    )

    derived = {
        "daily": daily,
        "hourly": hourly,
        "month_hour": month_hour,
        "heatmap": heatmap,
        "monthly": monthly,
        "sample": sample,
        "source_profile": source_profile,
    }
    return raw, derived


def chart_plan(name: str, axes_count: int, families: list[str], narrative_arc: str) -> dict:
    return {
        "name": name,
        "primaryChart": families[0],
        "secondaryCharts": families[1:],
        "statMethod": "descriptive telemetry summaries; no inferential p-values",
        "multipleComparison": "not applicable",
        "panelBlueprint": {
            "panelCount": axes_count,
            "layout": "R0_single_panel" if axes_count == 1 else "R2_two_by_two_storyboard",
            "narrativeArc": narrative_arc,
            "legend": "bottom_center_outside_panels",
        },
        "crowdingPlan": dict(CROWDING_PLAN),
        "visualContentPlan": {
            "mode": "nature_cell_dense",
            "density": "high",
            "impactLevel": "editorial_science",
            "minTotalEnhancements": 8 if axes_count > 1 else 5,
            "minInPlotLabelsPerFigure": 1,
            "appliedEnhancements": [
                "time_series_quantile_band",
                "rolling_average",
                "peak_callouts",
                "metric_boxes",
                "hour_month_heatmap",
                "voltage_intensity_density_sample",
                "sub_metering_stacked_energy",
            ],
            "visualGrammarMotifsApplied": [
                "layered_zorder",
                "metric_text_box",
                "shared_legend_bottom",
                "reference_lines",
                "panel_labels",
                "semantic_load_colors",
            ],
            "templateMotifsApplied": [
                narrative_arc,
                "time_series_band",
                "multipanel_grid" if axes_count > 1 else "single_focus",
            ],
        },
        "palettePlan": {
            "palette": "energy semantic load colors",
            "active_power": PALETTE["active"],
            "voltage": PALETTE["voltage"],
            "sub_metering_1": PALETTE["sub1"],
            "sub_metering_2": PALETTE["sub2"],
            "sub_metering_3": PALETTE["sub3"],
        },
    }


def record_render_contract_report(
    stem: str,
    plan: dict,
    legend_report: dict,
    layout_report: dict,
    saved: list[dict] | None = None,
    hard_fail: bool | None = None,
    png_validation: dict | None = None,
) -> None:
    crowding_plan = dict(plan.get("crowdingPlan", {}))
    crowding_plan.update(
        {
            key: value
            for report in (legend_report, layout_report)
            for key, value in report.items()
            if key.endswith("Count")
            or key.endswith("Failures")
            or key.endswith("Issues")
            or key
            in {
                "legendContractEnforced",
                "layoutContractEnforced",
                "legendOutsidePlotArea",
                "legendModeUsed",
                "legendFrameApplied",
                "figureLegendCount",
                "axisLegendRemainingCount",
                "figureWhitespaceFraction",
                "figureInkFraction",
                "maxFigureWhitespaceFraction",
                "minFigureInkFraction",
            }
        }
    )
    contract_record = {
        "figure": stem,
        "chartPlanName": plan.get("name"),
        "primaryChart": plan.get("primaryChart"),
        "secondaryCharts": plan.get("secondaryCharts", []),
        "panelBlueprint": plan.get("panelBlueprint", {}),
        "crowdingPlan": crowding_plan,
        "visualContentPlan": plan.get("visualContentPlan", {}),
        "legendContractReport": legend_report,
        "layoutContractReport": layout_report,
        "saved": saved or [],
        "pngValidation": png_validation or {},
        "hardFail": bool(hard_fail) if hard_fail is not None else None,
    }
    existing: list[dict] = []
    if RENDER_CONTRACT_PATH.exists():
        try:
            loaded = json.loads(RENDER_CONTRACT_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = loaded
        except json.JSONDecodeError:
            existing = []
    existing = [item for item in existing if item.get("figure") != stem]
    existing.append(json_safe(contract_record))
    RENDER_CONTRACT_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def save_figure(fig, axes, stem: str, plan: dict, qa_records: list[dict]) -> list[dict]:
    axis_map = {chr(ord("A") + i): ax for i, ax in enumerate(axes)}
    legend_report = enforce_figure_legend_contract(
        fig,
        axes=axis_map,
        chartPlan=plan,
        journalProfile=JOURNAL_PROFILE,
        crowdingPlan=CROWDING_PLAN,
        strict=False,
    )
    layout_report = audit_figure_layout_contract(
        fig,
        axes=axis_map,
        chartPlan=plan,
        journalProfile=JOURNAL_PROFILE,
        strict=False,
    )
    pre_save_hard_fail = bool(
        (not legend_report.get("legendContractEnforced"))
        or (not layout_report.get("layoutContractEnforced"))
        or int(legend_report.get("axisLegendRemainingCount", 0)) > 0
        or legend_report.get("legendContractFailures", [])
        or layout_report.get("layoutContractFailures", [])
    )
    record_render_contract_report(stem, plan, legend_report, layout_report, saved=[], hard_fail=pre_save_hard_fail)

    saved = []
    for ext in ("pdf", "svg", "png"):
        path = FIG_DIR / f"{stem}.{ext}"
        fig.savefig(path, dpi=1200, bbox_inches="tight")
        saved.append({"format": ext, "path": str(path), "bytes": path.stat().st_size})

    png_path = FIG_DIR / f"{stem}.png"
    img = mpimg.imread(png_path)
    nonblank = bool(np.nanstd(img) > 0.001 and img.shape[0] >= 300 and img.shape[1] >= 300)
    record = {
        "figure": stem,
        "legendContractEnforced": bool(legend_report.get("legendContractEnforced")),
        "layoutContractEnforced": bool(layout_report.get("layoutContractEnforced")),
        "legendOutsidePlotArea": bool(legend_report.get("legendOutsidePlotArea", True)),
        "axisLegendRemovedCount": int(legend_report.get("axisLegendRemovedCount", 0)),
        "axisLegendRemainingCount": int(legend_report.get("axisLegendRemainingCount", 0)),
        "figureLegendCount": int(legend_report.get("figureLegendCount", 0)),
        "legendFrameApplied": bool(legend_report.get("legendFrameApplied", False)),
        "legendModeUsed": legend_report.get("legendModeUsed", "none"),
        "legendContractFailures": legend_report.get("legendContractFailures", []),
        "layoutContractFailures": layout_report.get("layoutContractFailures", []),
        "crossPanelOverlapIssues": layout_report.get("crossPanelOverlapIssues", []),
        "colorbarPanelOverlapCount": int(layout_report.get("colorbarPanelOverlapCount", 0)),
        "metricTableDataOverlapCount": int(layout_report.get("metricTableDataOverlapCount", 0)),
        "textDataOverlapCount": int(layout_report.get("textDataOverlapCount", 0)),
        "negativeAxesTextCount": int(layout_report.get("negativeAxesTextCount", 0)),
        "oversizedTextCount": int(layout_report.get("oversizedTextCount", 0)),
        "offCanvasArtistCount": int(layout_report.get("offCanvasArtistCount", 0)),
        "figureWhitespaceFraction": float(layout_report.get("figureWhitespaceFraction", 1.0)),
        "figureInkFraction": float(layout_report.get("figureInkFraction", 0.0)),
        "nonblankPng": nonblank,
        "pngShape": list(img.shape),
        "saved": saved,
    }
    record["hardFail"] = bool(
        (not record["legendContractEnforced"])
        or (not record["layoutContractEnforced"])
        or record["axisLegendRemainingCount"] > 0
        or record["legendContractFailures"]
        or record["layoutContractFailures"]
        or record["crossPanelOverlapIssues"]
        or record["colorbarPanelOverlapCount"] > 0
        or record["metricTableDataOverlapCount"] > 0
        or record["textDataOverlapCount"] > 0
        or record["negativeAxesTextCount"] > 0
        or record["oversizedTextCount"] > 0
        or record["offCanvasArtistCount"] > 0
        or (not record["nonblankPng"])
    )
    record_render_contract_report(
        stem,
        plan,
        legend_report,
        layout_report,
        saved=saved,
        hard_fail=record["hardFail"],
        png_validation={"nonblankPng": nonblank, "pngShape": list(img.shape)},
    )
    qa_records.append(record)
    plt.close(fig)
    return saved


def figure_single_panel_hero(derived: dict[str, pd.DataFrame], qa_records: list[dict]) -> list[dict]:
    daily = derived["daily"].copy()
    peak_idx = daily["active_14d_kw"].idxmax()
    sag_idx = daily["voltage_p05"].idxmin()
    peak_day = daily.loc[peak_idx]
    sag_day = daily.loc[sag_idx]

    fig, ax = plt.subplots(figsize=(8.2, 5.4), constrained_layout=False)
    ax.fill_between(
        daily["date"],
        daily["active_p10_kw"],
        daily["active_p90_kw"],
        color=PALETTE["active_light"],
        alpha=0.42,
        linewidth=0,
        label="Daily P10-P90 active power",
        zorder=1,
    )
    ax.plot(
        daily["date"],
        daily["active_14d_kw"],
        color=PALETTE["active"],
        lw=1.6,
        label="14-day active power mean",
        zorder=4,
    )
    voltage_scaled = (
        (daily["voltage_14d"] - daily["voltage_14d"].mean())
        / max(daily["voltage_14d"].std(), 1e-9)
        * daily["active_14d_kw"].std()
        + daily["active_14d_kw"].mean()
    )
    ax.plot(
        daily["date"],
        voltage_scaled,
        color=PALETTE["voltage"],
        lw=1.15,
        alpha=0.95,
        label="Voltage mean, z-scaled to load axis",
        zorder=5,
    )
    ax.axvline(peak_day["date"], color=PALETTE["active"], lw=0.85, ls="--", alpha=0.8, zorder=6)
    ax.axvline(sag_day["date"], color=PALETTE["voltage"], lw=0.85, ls="--", alpha=0.8, zorder=6)
    y_top = max(float(daily["active_p90_kw"].max()), float(voltage_scaled.max()))
    ax.text(
        peak_day["date"],
        y_top * 0.95,
        f"peak load\n{pd.Timestamp(peak_day['date']).strftime('%Y-%m')}",
        ha="center",
        va="top",
        fontsize=6.1,
        bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=PALETTE["active"], lw=0.55, alpha=0.92),
        zorder=20,
    )
    ax.text(
        sag_day["date"],
        y_top * 0.78,
        f"voltage low\n{pd.Timestamp(sag_day['date']).strftime('%Y-%m')}",
        ha="center",
        va="top",
        fontsize=6.1,
        bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=PALETTE["voltage"], lw=0.55, alpha=0.92),
        zorder=20,
    )
    ax.set_title("Household power telemetry hero: load envelope and voltage stability", loc="center", fontweight="bold", pad=5)
    ax.set_xlabel("Day / month")
    ax.set_ylabel("Active power (kW), with voltage z-scaled")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for tick in ax.get_xticklabels():
        tick.set_rotation(30)
        tick.set_ha("right")
    style_axes(ax, "y")
    add_metric_box(
        ax,
        {
            "Records": fmt_value(float(derived["source_profile"].loc[0, "value"])),
            "Mean kW": fmt_value(float(daily["active_mean_kw"].mean())),
            "P95 kW": fmt_value(float(derived["source_profile"].loc[4, "value"])),
            "Metered": f"{float(derived['source_profile'].loc[8, 'value']):.1f}%",
        },
        loc="top_right",
        fontsize=6,
    )
    ax.legend(loc="upper right", frameon=False)
    add_letter(ax, "A")
    fig.suptitle("UCI household electric power consumption, 2006-2010", x=0.5, y=0.985, ha="center", fontsize=10, fontweight="bold")
    fig.subplots_adjust(left=0.13, right=0.985, top=0.88, bottom=0.11)
    plan = chart_plan(
        "single_panel_energy_load_hero",
        1,
        ["time_series_band", "voltage_overlay"],
        "hero",
    )
    return save_figure(fig, [ax], "fig0_single_panel_energy_load_hero", plan, qa_records)


def figure_load_atlas(derived: dict[str, pd.DataFrame], qa_records: list[dict]) -> list[dict]:
    hourly = derived["hourly"].copy()
    heatmap = derived["heatmap"].copy()
    monthly = derived["monthly"].copy()
    sample = derived["sample"].copy()

    fig = plt.figure(figsize=(10.4, 8.0), constrained_layout=False)
    gs = gridspec.GridSpec(2, 2, figure=fig, wspace=0.28, hspace=0.36)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    hours = hourly["hour"].to_numpy()
    ax_a.fill_between(
        hours,
        hourly["active_p10_kw"],
        hourly["active_p90_kw"],
        color=PALETTE["active_light"],
        alpha=0.42,
        linewidth=0,
        label="P10-P90 active power",
        zorder=1,
    )
    ax_a.plot(hours, hourly["active_mean_kw"], color=PALETTE["active"], lw=1.55, label="Mean active power", zorder=4)
    ax_a.plot(hours, hourly["voltage_mean"] - hourly["voltage_mean"].mean() + hourly["active_mean_kw"].mean(), color=PALETTE["voltage"], lw=1.1, label="Voltage deviation, shifted", zorder=5)
    peak_hour = int(hourly.loc[hourly["active_mean_kw"].idxmax(), "hour"])
    ax_a.axvline(peak_hour, color=PALETTE["active"], lw=0.8, ls="--", alpha=0.75, zorder=6)
    ax_a.set_title("Circadian load signature", loc="center", fontweight="bold", pad=4)
    ax_a.set_xlabel("Time of day (hour)")
    ax_a.set_ylabel("Active power (kW)")
    ax_a.set_xlim(0, 23)
    ax_a.set_xticks(np.arange(0, 24, 4))
    style_axes(ax_a, "y")
    add_metric_box(
        ax_a,
        {
            "Peak hour": f"{peak_hour:02d}:00",
            "Mean kW": fmt_value(float(hourly["active_mean_kw"].mean())),
            "Voltage span": f"{hourly['voltage_mean'].min():.1f}-{hourly['voltage_mean'].max():.1f} V",
        },
        loc="top_left",
        fontsize=5.8,
    )

    heat_data = heatmap.to_numpy(dtype=float)
    vmax = max(1.0, np.nanpercentile(heat_data, 99.0))
    ax_b.imshow(heat_data, aspect="auto", interpolation="nearest", cmap=HEATMAP_CMAP, vmin=0, vmax=vmax, zorder=2)
    ax_b.set_title("Month-hour active power atlas", loc="center", fontweight="bold", pad=4)
    ax_b.set_xlabel("Hour")
    ax_b.set_ylabel("Month")
    ax_b.set_xticks(np.arange(0, 24, 4))
    ax_b.set_xticklabels([str(v) for v in range(0, 24, 4)])
    y_ticks = np.arange(0, len(heatmap.index), 6)
    ax_b.set_yticks(y_ticks)
    ax_b.set_yticklabels([pd.Timestamp(heatmap.index[i]).strftime("%Y-%m") for i in y_ticks])
    for spine in ax_b.spines.values():
        spine.set_linewidth(0.6)
    add_metric_box(
        ax_b,
        {
            "Color": "mean kW",
            "Max cell": fmt_value(float(np.nanmax(heat_data))),
            "Median": fmt_value(float(np.nanmedian(heat_data))),
        },
        loc="top_left",
        fontsize=5.7,
    )

    sample = sample.sort_values("Global_intensity")
    ax_c.scatter(
        sample["Voltage"],
        sample["Global_intensity"],
        c=sample["Global_active_power"],
        cmap=HEATMAP_CMAP,
        s=3.0,
        alpha=0.22,
        edgecolors="none",
        rasterized=True,
        zorder=2,
    )
    ax_c.axvline(
        sample["Voltage"].quantile(0.05),
        color=PALETTE["voltage"],
        lw=0.8,
        ls="--",
        label="Voltage p05",
        zorder=5,
    )
    ax_c.axhline(
        sample["Global_intensity"].quantile(0.95),
        color=PALETTE["intensity"],
        lw=0.8,
        ls="--",
        label="Intensity p95",
        zorder=5,
    )
    corr = sample[["Voltage", "Global_intensity"]].corr().iloc[0, 1]
    ax_c.set_title("Voltage sag versus intensity", loc="center", fontweight="bold", pad=4)
    ax_c.set_xlabel("Voltage (V)")
    ax_c.set_ylabel("Global intensity (A)")
    style_axes(ax_c, "both")
    add_metric_box(
        ax_c,
        {
            "Sample": f"{len(sample):,}",
            "r(V,I)": f"{corr:.2f}",
            "V p05": f"{sample['Voltage'].quantile(0.05):.1f}",
        },
        loc="top_right",
        fontsize=5.7,
    )

    x = np.arange(len(monthly))
    bottom = np.zeros(len(monthly))
    stacked_specs = [
        ("Sub-meter 1", "sub1_kwh", PALETTE["sub1"]),
        ("Sub-meter 2", "sub2_kwh", PALETTE["sub2"]),
        ("Sub-meter 3", "sub3_kwh", PALETTE["sub3"]),
        ("Residual", "residual_kwh", PALETTE["residual"]),
    ]
    for label, column, color in stacked_specs:
        ax_d.bar(x, monthly[column], bottom=bottom, color=color, width=0.72, label=label, edgecolor="white", linewidth=0.25, zorder=2)
        bottom += monthly[column].to_numpy()
    ax_d.plot(x, monthly["active_kwh"], color=PALETTE["active"], lw=1.25, label="Total active kWh", zorder=5)
    ax_d.set_title("Monthly sub-metering allocation", loc="center", fontweight="bold", pad=4)
    ax_d.set_xlabel("Month")
    ax_d.set_ylabel("Energy (kWh)")
    tick_idx = np.arange(0, len(monthly), 6)
    ax_d.set_xticks(tick_idx)
    ax_d.set_xticklabels([pd.Timestamp(monthly.iloc[i]["month"]).strftime("%Y-%m") for i in tick_idx], rotation=30, ha="right")
    style_axes(ax_d, "y")
    add_metric_box(
        ax_d,
        {
            "Metered mean": f"{monthly['metered_share'].mean():.1f}%",
            "Total kWh": fmt_value(float(monthly["active_kwh"].sum())),
            "Months": str(len(monthly)),
        },
        loc="top_left",
        fontsize=5.7,
    )

    for label, ax in zip(["A", "B", "C", "D"], [ax_a, ax_b, ax_c, ax_d]):
        add_letter(ax, label)
    fig.suptitle("Load atlas: time-of-day, month, voltage, intensity and sub-metering structure", x=0.5, y=0.985, ha="center", fontsize=10, fontweight="bold")
    fig.subplots_adjust(left=0.09, right=0.985, top=0.91, bottom=0.11)
    plan = chart_plan(
        "multi_panel_energy_load_atlas",
        4,
        ["time_series_band", "hour_month_heatmap", "density_scatter", "stacked_energy_bar"],
        "multipanel_grid",
    )
    return save_figure(fig, [ax_a, ax_b, ax_c, ax_d], "fig1_multi_panel_load_atlas", plan, qa_records)


def write_reports(raw: pd.DataFrame, derived: dict[str, pd.DataFrame], figures: list[dict], qa_records: list[dict]) -> None:
    daily = derived["daily"]
    hourly = derived["hourly"]
    monthly = derived["monthly"]
    source_profile = derived["source_profile"]

    daily.to_csv(SOURCE_DIR / "daily_power_voltage_submetering.csv", index=False)
    hourly.to_csv(SOURCE_DIR / "hourly_time_of_day_profile.csv", index=False)
    derived["month_hour"].to_csv(SOURCE_DIR / "month_hour_active_power.csv", index=False)
    monthly.to_csv(SOURCE_DIR / "monthly_submetering_energy.csv", index=False)
    derived["sample"][
        [
            "datetime",
            "Global_active_power",
            "Voltage",
            "Global_intensity",
            "Sub_metering_1",
            "Sub_metering_2",
            "Sub_metering_3",
            "residual_wh",
        ]
    ].to_csv(SOURCE_DIR / "voltage_intensity_sample.csv", index=False)
    source_profile.to_csv(SOURCE_DIR / "source_profile.csv", index=False)

    render_contract_loaded = RENDER_CONTRACT_PATH.exists() and RENDER_CONTRACT_PATH.stat().st_size > 2
    render_qa = {
        "hardFail": any(record["hardFail"] for record in qa_records) or (not render_contract_loaded),
        "renderContractReportLoaded": render_contract_loaded,
        "renderContractReportPath": str(RENDER_CONTRACT_PATH),
        "figures": qa_records,
        "requiredContracts": {
            "legendContractEnforced": all(record["legendContractEnforced"] for record in qa_records),
            "layoutContractEnforced": all(record["layoutContractEnforced"] for record in qa_records),
            "axisLegendRemainingCount": sum(record["axisLegendRemainingCount"] for record in qa_records),
            "colorbarPanelOverlapCount": sum(record["colorbarPanelOverlapCount"] for record in qa_records),
            "textDataOverlapCount": sum(record["textDataOverlapCount"] for record in qa_records),
            "metricTableDataOverlapCount": sum(record["metricTableDataOverlapCount"] for record in qa_records),
            "allPngNonblank": all(record["nonblankPng"] for record in qa_records),
            "renderContractReportLoaded": render_contract_loaded,
        },
    }
    (REPORT_DIR / "render_qa.json").write_text(json.dumps(json_safe(render_qa), indent=2), encoding="utf-8")

    panel_manifest = {
        "bundle": "uci_power_energy_load_telemetry_showcase",
        "inputFile": str(INPUT_FILE),
        "figures": figures,
        "panels": [
            {
                "figure": "fig0_single_panel_energy_load_hero",
                "panel": "A",
                "role": "single-panel hero",
                "chart": "daily active power quantile band with voltage stability overlay",
                "dataSource": str(SOURCE_DIR / "daily_power_voltage_submetering.csv"),
                "signals": ["day/month", "active power", "voltage", "sub-metering share"],
            },
            {
                "figure": "fig1_multi_panel_load_atlas",
                "panel": "A",
                "role": "time-of-day load signature",
                "chart": "hourly active power band plus shifted voltage profile",
                "dataSource": str(SOURCE_DIR / "hourly_time_of_day_profile.csv"),
                "signals": ["time-of-day", "active power", "voltage"],
            },
            {
                "figure": "fig1_multi_panel_load_atlas",
                "panel": "B",
                "role": "month-hour atlas",
                "chart": "month by hour active power heatmap without panel-overlapping colorbar",
                "dataSource": str(SOURCE_DIR / "month_hour_active_power.csv"),
                "signals": ["month", "hour", "active power"],
            },
            {
                "figure": "fig1_multi_panel_load_atlas",
                "panel": "C",
                "role": "voltage-intensity diagnostic",
                "chart": "sampled density-like scatter colored by active power",
                "dataSource": str(SOURCE_DIR / "voltage_intensity_sample.csv"),
                "signals": ["voltage", "global intensity", "active power"],
            },
            {
                "figure": "fig1_multi_panel_load_atlas",
                "panel": "D",
                "role": "sub-metering allocation",
                "chart": "monthly stacked sub-metering and residual energy with total active kWh overlay",
                "dataSource": str(SOURCE_DIR / "monthly_submetering_energy.csv"),
                "signals": ["month", "sub-metering 1", "sub-metering 2", "sub-metering 3", "residual load"],
            },
        ],
        "renderQa": str(REPORT_DIR / "render_qa.json"),
        "renderContracts": str(RENDER_CONTRACT_PATH),
    }
    (REPORT_DIR / "panel_manifest.json").write_text(json.dumps(json_safe(panel_manifest), indent=2), encoding="utf-8")

    metadata = {
        "skill": "scifig-generate",
        "skillEntry": str(SKILL_ROOT / "SKILL.md"),
        "inputFile": str(INPUT_FILE),
        "inputSha256": file_sha256(INPUT_FILE),
        "outputDir": str(OUTPUT_DIR),
        "language": "zh-cn",
        "mode": "auto",
        "preferences": "energy telemetry and signal-processing journal style, semantic load colors, 1200 dpi, detail preserving, maximum visual impact without overlap",
        "dataProfile": {
            "format": "semicolon-delimited CSV",
            "structure": "minute-level household energy telemetry",
            "nObservationsAfterDropna": int(len(raw)),
            "dateRange": [raw["datetime"].min().isoformat(), raw["datetime"].max().isoformat()],
            "semanticRoles": {
                "time": ["Date", "Time", "datetime", "hour", "month"],
                "primaryValue": "Global_active_power",
                "voltage": "Voltage",
                "intensity": "Global_intensity",
                "subMetering": ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"],
            },
            "riskFlags": ["descriptive telemetry only; no replicate-based inference"],
        },
        "outputBundle": {
            "figures": figures,
            "sourceData": sorted(str(path) for path in SOURCE_DIR.glob("*.csv")),
            "panelManifest": str(REPORT_DIR / "panel_manifest.json"),
            "statsReport": str(REPORT_DIR / "stats_report.md"),
            "metadata": str(REPORT_DIR / "metadata.json"),
            "renderQa": str(REPORT_DIR / "render_qa.json"),
            "renderContracts": str(RENDER_CONTRACT_PATH),
        },
    }
    (REPORT_DIR / "metadata.json").write_text(json.dumps(json_safe(metadata), indent=2), encoding="utf-8")

    stats_lines = [
        "# UCI household power telemetry statistics",
        "",
        "Generated with `scifig-generate` from the concrete semicolon-delimited file.",
        "",
        "## Data profile",
        f"- Rows after missing-value removal: {len(raw):,}",
        f"- Date range: {raw['datetime'].min():%Y-%m-%d %H:%M} to {raw['datetime'].max():%Y-%m-%d %H:%M}",
        f"- Mean active power: {raw['Global_active_power'].mean():.3f} kW",
        f"- 95th percentile active power: {raw['Global_active_power'].quantile(0.95):.3f} kW",
        f"- Mean voltage: {raw['Voltage'].mean():.2f} V",
        f"- 5th percentile voltage: {raw['Voltage'].quantile(0.05):.2f} V",
        f"- Mean global intensity: {raw['Global_intensity'].mean():.2f} A",
        f"- Mean metered share: {monthly['metered_share'].mean():.1f}%",
        "",
        "## Figure statistics",
        f"- Hero peak 14-day active power: {daily['active_14d_kw'].max():.3f} kW",
        f"- Hour-of-day peak active power: {int(hourly.loc[hourly['active_mean_kw'].idxmax(), 'hour']):02d}:00",
        f"- Month-hour maximum active power cell: {derived['heatmap'].to_numpy().max():.3f} kW",
        f"- Voltage-intensity correlation in sampled panel: {derived['sample'][['Voltage', 'Global_intensity']].corr().iloc[0, 1]:.3f}",
        f"- Total active energy represented: {monthly['active_kwh'].sum():.1f} kWh",
        "",
        "## Render QA",
        f"- hardFail: {str(render_qa['hardFail']).lower()}",
        f"- legendContractEnforced: {str(render_qa['requiredContracts']['legendContractEnforced']).lower()}",
        f"- layoutContractEnforced: {str(render_qa['requiredContracts']['layoutContractEnforced']).lower()}",
        f"- axisLegendRemainingCount: {render_qa['requiredContracts']['axisLegendRemainingCount']}",
        f"- colorbarPanelOverlapCount: {render_qa['requiredContracts']['colorbarPanelOverlapCount']}",
        f"- textDataOverlapCount: {render_qa['requiredContracts']['textDataOverlapCount']}",
        f"- metricTableDataOverlapCount: {render_qa['requiredContracts']['metricTableDataOverlapCount']}",
        f"- allPngNonblank: {str(render_qa['requiredContracts']['allPngNonblank']).lower()}",
    ]
    (REPORT_DIR / "stats_report.md").write_text("\n".join(stats_lines) + "\n", encoding="utf-8")

    requirements = "\n".join(
        [
            "matplotlib",
            "numpy",
            "pandas",
        ]
    )
    (OUTPUT_DIR / "requirements.txt").write_text(requirements + "\n", encoding="utf-8")


def main() -> None:
    configure_style()
    if RENDER_CONTRACT_PATH.exists():
        RENDER_CONTRACT_PATH.unlink()
    raw, derived = load_and_derive()
    qa_records: list[dict] = []
    figures: list[dict] = []
    figures.append(
        {
            "stem": "fig0_single_panel_energy_load_hero",
            "role": "single-panel hero",
            "exports": figure_single_panel_hero(derived, qa_records),
        }
    )
    figures.append(
        {
            "stem": "fig1_multi_panel_load_atlas",
            "role": "multi-panel load atlas",
            "exports": figure_load_atlas(derived, qa_records),
        }
    )
    write_reports(raw, derived, figures, qa_records)
    render_qa = json.loads((REPORT_DIR / "render_qa.json").read_text(encoding="utf-8"))
    if render_qa.get("hardFail"):
        raise RuntimeError(f"Render QA hardFail: {json.dumps(render_qa, indent=2)[:2000]}")


if __name__ == "__main__":
    main()
