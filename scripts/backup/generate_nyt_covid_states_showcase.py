from __future__ import annotations

import json
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker
from matplotlib.colors import LinearSegmentedColormap


ROOT = Path(r"D:\test_scifig")
SKILL_ROOT = ROOT / ".codex" / "skills" / "scifig-generate"
INPUT_FILE = Path(r"D:\SciFig\.workflow\.scratchpad\test-data\raw\nyt_covid_states.csv")
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
    "style": "epidemiology_public_health_showcase",
    "journalName": "Public-health journal showcase",
    "font_family": ["DejaVu Sans"],
    "font_size_pt": 7,
    "font_size_axis_pt": 7,
    "font_size_panel_label_pt": 9,
    "max_text_font_size_pt": 12,
    "max_panel_label_font_size_pt": 10,
    "axes_linewidth": 0.9,
    "savefig_dpi": 1200,
}

CROWDING_PLAN = {
    "crowdingPolicy": "preserve_information",
    "overlapPriority": "information_first",
    "legendMode": "bottom_center",
    "legendAllowedModes": ["bottom_center"],
    "legendFrame": True,
    "legendFontSizePt": 7,
    "legendBottomAnchorY": 0.015,
    "legendBottomMarginNoLegend": 0.09,
    "legendBottomMarginMin": 0.06,
    "legendBottomMarginMax": 0.16,
    "maxTextFontSizePt": 12,
    "maxPanelLabelFontSizePt": 10,
}

PALETTE = {
    "cases": "#2166AC",
    "cases_light": "#92C5DE",
    "deaths": "#B2182B",
    "deaths_light": "#F4A582",
    "neutral": "#4D4D4D",
    "grid": "#D9D9D9",
    "accent": "#1B9E77",
    "gold": "#D8A03D",
}


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


def load_and_derive() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    raw = pd.read_csv(INPUT_FILE, parse_dates=["date"])
    raw["cases"] = pd.to_numeric(raw["cases"], errors="coerce")
    raw["deaths"] = pd.to_numeric(raw["deaths"], errors="coerce")
    raw = raw.dropna(subset=["date", "state", "cases", "deaths"]).copy()
    raw = raw.sort_values(["state", "date"]).reset_index(drop=True)

    for cumulative, daily in (("cases", "new_cases"), ("deaths", "new_deaths")):
        raw[daily] = raw.groupby("state")[cumulative].diff().fillna(raw[cumulative])
        raw[daily] = raw[daily].clip(lower=0)
        raw[f"{daily}_7d"] = (
            raw.groupby("state", group_keys=False)[daily]
            .rolling(7, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )

    raw["case_fatality_pct"] = np.where(
        raw["cases"] > 0, raw["deaths"] / raw["cases"] * 100.0, np.nan
    )
    raw["week"] = raw["date"].dt.to_period("W-SUN").dt.start_time
    raw["month"] = raw["date"].dt.to_period("M").dt.to_timestamp()

    national = (
        raw.groupby("date", as_index=False)
        .agg(
            cases=("cases", "sum"),
            deaths=("deaths", "sum"),
            new_cases=("new_cases", "sum"),
            new_deaths=("new_deaths", "sum"),
        )
        .sort_values("date")
    )
    national["new_cases_7d"] = national["new_cases"].rolling(7, min_periods=1).mean()
    national["new_deaths_7d"] = national["new_deaths"].rolling(7, min_periods=1).mean()

    latest = raw.groupby("state", as_index=False).tail(1).copy()
    latest = latest.sort_values("cases", ascending=False).reset_index(drop=True)
    top_states = latest.head(24)["state"].tolist()

    weekly = (
        raw[raw["state"].isin(top_states)]
        .groupby(["state", "week"], as_index=False)
        .agg(
            new_cases_7d=("new_cases_7d", "mean"),
            new_deaths_7d=("new_deaths_7d", "mean"),
            cases=("cases", "max"),
            deaths=("deaths", "max"),
        )
    )

    monthly = (
        raw.groupby(["state", "month"], as_index=False)
        .agg(
            new_cases=("new_cases", "sum"),
            new_deaths=("new_deaths", "sum"),
            cases=("cases", "max"),
            deaths=("deaths", "max"),
        )
    )

    derived = {
        "national": national,
        "latest": latest,
        "weekly": weekly,
        "monthly": monthly,
        "top_states": pd.DataFrame({"state": top_states}),
    }
    return raw, derived


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


def build_matrix(
    weekly: pd.DataFrame,
    states: list[str],
    metric: str,
) -> pd.DataFrame:
    matrix = weekly.pivot(index="state", columns="week", values=metric)
    matrix = matrix.reindex(states).fillna(0)
    matrix = matrix.reindex(sorted(matrix.columns), axis=1)
    return matrix


def fmt_large(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}k"
    return f"{value:.0f}"


def format_date_axis(ax) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    for label in ax.get_xticklabels():
        label.set_rotation(30)
        label.set_ha("right")


def style_cartesian(ax, grid_axis: str = "y") -> None:
    ax.grid(axis=grid_axis, color=PALETTE["grid"], linewidth=0.45, linestyle="--", alpha=0.7, zorder=0)
    apply_chart_polish(ax, "line")


def add_letter(ax, label: str) -> None:
    add_panel_label(ax, label, x=-0.045, y=1.025, fontsize=9)


def draw_heatmap(ax, matrix: pd.DataFrame, title: str, cmap, cbar_label: str, panel_label: str):
    data = np.log10(matrix.to_numpy(dtype=float) + 1.0)
    vmax = max(1.0, np.nanpercentile(data, 99.5))
    im = ax.imshow(data, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0, vmax=vmax, zorder=2)
    ax.set_title(title, loc="center", fontweight="bold", pad=4)
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_yticklabels(matrix.index, fontsize=5.3)

    ticks = np.arange(0, matrix.shape[1], 13)
    tick_labels = [pd.Timestamp(matrix.columns[i]).strftime("%Y-%m") for i in ticks]
    ax.set_xticks(ticks)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=5.3)
    ax.set_xlabel("Reporting week")
    ax.set_ylabel("State ordered by cumulative case burden")
    for spine in ax.spines.values():
        spine.set_linewidth(0.6)
    add_letter(ax, panel_label)
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.028, pad=0.015)
    cbar.set_label(cbar_label, fontsize=6)
    cbar.ax.tick_params(labelsize=5.5)
    return im


def finalizer_chart_plan(name: str, axes_count: int, families: list[str], narrative_arc: str) -> dict:
    return {
        "name": name,
        "primaryChart": families[0],
        "secondaryCharts": families[1:],
        "panelBlueprint": {
            "panelCount": axes_count,
            "layout": "publication_multi_panel",
            "narrativeArc": narrative_arc,
        },
        "crowdingPlan": dict(CROWDING_PLAN),
        "visualContentPlan": {
            "mode": "nature_cell_dense",
            "density": "high",
            "impactLevel": "editorial_science",
            "minTotalEnhancements": 8,
            "minInPlotLabelsPerFigure": 2,
            "appliedEnhancements": [
                "weekly_state_heatmap",
                "rolling_average",
                "peak_callouts",
                "metric_boxes",
                "ranked_lollipop",
                "density_scatter",
            ],
            "visualGrammarMotifsApplied": [
                "panel_labels",
                "reference_lines",
                "metric_text_box",
                "layered_zorder",
                "shared_legend_bottom",
            ],
            "templateMotifsApplied": [
                "multipanel_grid",
                "time_series_band",
                "marginal_joint_density",
            ],
        },
    }


def record_render_contract_report(
    stem: str,
    chart_plan: dict,
    legend_contract_report: dict,
    layout_report: dict,
    saved: list[dict] | None = None,
    hard_fail: bool | None = None,
    png_validation: dict | None = None,
) -> None:
    crowding_plan = dict(chart_plan.get("crowdingPlan", {}))
    crowding_plan.update(
        {
            key: value
            for report in (legend_contract_report, layout_report)
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
        "chartPlanName": chart_plan.get("name"),
        "primaryChart": chart_plan.get("primaryChart"),
        "secondaryCharts": chart_plan.get("secondaryCharts", []),
        "panelBlueprint": chart_plan.get("panelBlueprint", {}),
        "crowdingPlan": crowding_plan,
        "visualContentPlan": chart_plan.get("visualContentPlan", {}),
        "legendContractReport": legend_contract_report,
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


def save_figure(fig, axes, stem: str, chart_plan: dict, qa_records: list[dict]) -> list[dict]:
    axis_map = {chr(ord("A") + i): ax for i, ax in enumerate(axes)}
    legend_contract_report = enforce_figure_legend_contract(
        fig,
        axes=axis_map,
        chartPlan=chart_plan,
        journalProfile=JOURNAL_PROFILE,
        crowdingPlan=CROWDING_PLAN,
        strict=False,
    )
    layout_report = audit_figure_layout_contract(
        fig,
        axes=axis_map,
        chartPlan=chart_plan,
        journalProfile=JOURNAL_PROFILE,
        strict=False,
    )
    contract_hard_fail = bool(
        (not legend_contract_report.get("legendContractEnforced"))
        or (not layout_report.get("layoutContractEnforced"))
        or int(legend_contract_report.get("axisLegendRemainingCount", 0)) > 0
        or legend_contract_report.get("legendContractFailures", [])
        or layout_report.get("layoutContractFailures", [])
    )
    record_render_contract_report(
        stem,
        chart_plan,
        legend_contract_report,
        layout_report,
        saved=[],
        hard_fail=contract_hard_fail,
    )

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
        "legendContractEnforced": bool(legend_contract_report.get("legendContractEnforced")),
        "layoutContractEnforced": bool(layout_report.get("layoutContractEnforced")),
        "legendOutsidePlotArea": bool(legend_contract_report.get("legendOutsidePlotArea", True)),
        "axisLegendRemovedCount": int(legend_contract_report.get("axisLegendRemovedCount", 0)),
        "axisLegendRemainingCount": int(legend_contract_report.get("axisLegendRemainingCount", 0)),
        "figureLegendCount": int(legend_contract_report.get("figureLegendCount", 0)),
        "legendFrameApplied": bool(legend_contract_report.get("legendFrameApplied", False)),
        "legendModeUsed": legend_contract_report.get("legendModeUsed", "none"),
        "legendContractFailures": legend_contract_report.get("legendContractFailures", []),
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
        chart_plan,
        legend_contract_report,
        layout_report,
        saved=saved,
        hard_fail=record["hardFail"],
        png_validation={"nonblankPng": nonblank, "pngShape": list(img.shape)},
    )
    qa_records.append(record)
    plt.close(fig)
    return saved


def figure_national_wave_hero(df: pd.DataFrame, derived: dict[str, pd.DataFrame], qa_records: list[dict]):
    national = derived["national"].copy()
    latest = derived["latest"]
    cases_peak = float(national["new_cases_7d"].max())
    deaths_peak = float(national["new_deaths_7d"].max())
    national["case_burden_index"] = np.where(cases_peak > 0, national["new_cases_7d"] / cases_peak * 100.0, 0.0)
    national["death_burden_index"] = np.where(deaths_peak > 0, national["new_deaths_7d"] / deaths_peak * 100.0, 0.0)
    peak_cases = national.loc[national["case_burden_index"].idxmax()]
    peak_deaths = national.loc[national["death_burden_index"].idxmax()]

    fig, ax = plt.subplots(figsize=(9.2, 5.8), constrained_layout=False)
    ax.fill_between(
        national["date"],
        national["case_burden_index"],
        color=PALETTE["cases_light"],
        alpha=0.42,
        linewidth=0,
        label="Cases, 7-day burden index",
        zorder=1,
    )
    ax.plot(
        national["date"],
        national["case_burden_index"],
        color=PALETTE["cases"],
        lw=1.8,
        label="Cases, 7-day burden index",
        zorder=4,
    )
    ax.plot(
        national["date"],
        national["death_burden_index"],
        color=PALETTE["deaths"],
        lw=1.55,
        label="Deaths, 7-day burden index",
        zorder=5,
    )
    for peak, color, label, ypos in (
        (peak_cases, PALETTE["cases"], "case peak", 93),
        (peak_deaths, PALETTE["deaths"], "death peak", 76),
    ):
        ax.axvline(peak["date"], color=color, lw=0.8, ls="--", alpha=0.75, zorder=6)
        ax.text(
            peak["date"],
            ypos,
            f"{label}\n{pd.Timestamp(peak['date']).strftime('%Y-%m-%d')}",
            ha="center",
            va="top",
            fontsize=6.2,
            color="#222222",
            bbox=dict(boxstyle="round,pad=0.24", fc="white", ec=color, lw=0.55, alpha=0.92),
            zorder=20,
        )
    ax.set_ylim(0, 108)
    ax.set_ylabel("Peak-normalized national burden index")
    ax.set_xlabel("Report date")
    ax.set_title("Single-panel national COVID burden hero", loc="center", fontweight="bold", pad=5)
    format_date_axis(ax)
    style_cartesian(ax, "y")
    add_metric_box(
        ax,
        {
            "State groups": f"{df['state'].nunique()}",
            "Final cases": fmt_large(float(latest["cases"].sum())),
            "Final deaths": fmt_large(float(latest["deaths"].sum())),
            "Daily rates": "within-state diff + 7d mean",
        },
        loc="bottom_left",
        fontsize=6,
    )
    ax.legend(loc="upper right", frameon=False)
    add_letter(ax, "A")
    fig.suptitle("United States state-reported COVID-19 burden waves", x=0.5, y=0.985, ha="center", fontsize=10, fontweight="bold")
    fig.text(0.5, 0.945, "A single-panel hero normalizes case and death waves to their national 7-day peaks, preserving date structure without per-capita claims.", fontsize=6.5, ha="center")
    saved = save_figure(
        fig,
        [ax],
        "fig0_single_panel_national_burden_hero",
        finalizer_chart_plan("single-panel national burden hero", 1, ["time_series_pi", "dual_metric_line"], "hero"),
        qa_records,
    )
    national.to_csv(SOURCE_DIR / "fig0_single_panel_national_burden_hero.csv", index=False)
    return saved


def figure_state_burden_story(df: pd.DataFrame, derived: dict[str, pd.DataFrame], qa_records: list[dict]):
    national = derived["national"]
    latest = derived["latest"]
    weekly = derived["weekly"]
    states = derived["top_states"]["state"].tolist()
    case_matrix = build_matrix(weekly, states, "new_cases_7d")

    fig, axes = build_grid(
        "R2_two_by_two_storyboard",
        figsize=(14.0, 10.7),
        wspace=0.48,
        hspace=0.50,
    )
    ax_a, ax_b, ax_c, ax_d = axes

    ax_a.fill_between(
        national["date"],
        national["new_cases_7d"],
        color=PALETTE["cases_light"],
        alpha=0.35,
        linewidth=0,
        label="Cases, 7-day mean",
        zorder=1,
    )
    ax_a.plot(national["date"], national["new_cases_7d"], color=PALETTE["cases"], lw=1.55, zorder=3)
    ax_a2 = ax_a.twinx()
    ax_a2.plot(
        national["date"],
        national["new_deaths_7d"],
        color=PALETTE["deaths"],
        lw=1.25,
        label="Deaths, 7-day mean",
        zorder=4,
    )
    peak_cases = national.loc[national["new_cases_7d"].idxmax()]
    peak_deaths = national.loc[national["new_deaths_7d"].idxmax()]
    ax_a.axvline(peak_cases["date"], color=PALETTE["cases"], lw=0.8, ls="--", alpha=0.6, zorder=5)
    ax_a2.axvline(peak_deaths["date"], color=PALETTE["deaths"], lw=0.8, ls="--", alpha=0.6, zorder=5)
    ax_a.set_title("National epidemic waves", loc="center", fontweight="bold", pad=4)
    ax_a.set_ylabel("New cases, 7-day mean")
    ax_a2.set_ylabel("New deaths, 7-day mean", labelpad=2)
    ax_a.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: fmt_large(x)))
    ax_a2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: fmt_large(x)))
    format_date_axis(ax_a)
    style_cartesian(ax_a, "y")
    ax_a2.tick_params(axis="y", colors=PALETTE["deaths"])
    ax_a2.spines["right"].set_color(PALETTE["deaths"])
    ax_a.plot([], [], color=PALETTE["deaths"], lw=1.25, label="Deaths, 7-day mean")
    ax_a.legend(loc="upper left", frameon=False)
    add_metric_box(
        ax_a,
        {
            "Peak cases": pd.Timestamp(peak_cases["date"]).strftime("%Y-%m-%d"),
            "7d cases": fmt_large(float(peak_cases["new_cases_7d"])),
            "Peak deaths": pd.Timestamp(peak_deaths["date"]).strftime("%Y-%m-%d"),
        },
        loc="top_left",
        fontsize=6,
    )
    add_letter(ax_a, "A")

    case_cmap = LinearSegmentedColormap.from_list(
        "cases_semantic",
        ["#F7FBFF", "#C6DBEF", "#6BAED6", PALETTE["cases"], "#08306B"],
    )
    draw_heatmap(
        ax_b,
        case_matrix,
        "State-week case burden matrix",
        case_cmap,
        "log10(new cases + 1), 7-day mean",
        "B",
    )

    top20 = latest.head(20).copy().iloc[::-1]
    y = np.arange(len(top20))
    ax_c.hlines(y, 0, top20["cases"], color=PALETTE["cases_light"], lw=4.8, zorder=1)
    ax_c.scatter(top20["cases"], y, s=34, color=PALETTE["cases"], edgecolor="white", linewidth=0.7, zorder=4, label="Cumulative cases")
    death_scaled = top20["deaths"] / top20["deaths"].max() * top20["cases"].max()
    ax_c.scatter(death_scaled, y, s=28, color=PALETTE["deaths"], edgecolor="white", linewidth=0.7, zorder=5, label="Deaths, scaled")
    for idx, (_, row) in enumerate(top20.iterrows()):
        if idx % 3 == 0 or idx >= len(top20) - 4:
            ax_c.text(
                row["cases"] * 0.985,
                idx,
                fmt_large(row["cases"]),
                ha="right",
                va="center",
                fontsize=5.4,
                color="white",
                fontweight="bold",
                clip_on=True,
                zorder=20,
            )
    ax_c.set_yticks(y)
    ax_c.set_yticklabels(top20["state"], fontsize=5.5)
    ax_c.set_xlabel("Cumulative cases")
    ax_c.set_title("Cumulative state burden ranking", loc="center", fontweight="bold", pad=4)
    ax_c.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: fmt_large(x)))
    style_cartesian(ax_c, "x")
    ax_c.legend(loc="lower right", frameon=False)
    add_metric_box(
        ax_c,
        {
            "States": f"{latest['state'].nunique()}",
            "Final cases": fmt_large(float(latest["cases"].sum())),
            "Final deaths": fmt_large(float(latest["deaths"].sum())),
        },
        loc="bottom_right",
        fontsize=6,
    )
    add_letter(ax_c, "C")

    scatter = df.loc[(df["new_cases_7d"] > 0) & (df["new_deaths_7d"] > 0)].copy()
    scatter = scatter.sample(min(14000, len(scatter)), random_state=17)
    x = np.log10(scatter["new_cases_7d"].to_numpy() + 1)
    yy = np.log10(scatter["new_deaths_7d"].to_numpy() + 1)
    density_color_scatter(ax_d, x, yy, cmap="mako_r" if "mako_r" in plt.colormaps() else "GnBu_r", s=8, linewidth=0.12, colorbar_label="Local density")
    coeff = np.polyfit(x, yy, deg=1)
    xs = np.linspace(x.min(), x.max(), 160)
    ax_d.plot(xs, coeff[0] * xs + coeff[1], color="black", lw=1.0, ls="--", zorder=6)
    r = float(np.corrcoef(x, yy)[0, 1])
    ax_d.set_title("State-day case-death coupling", loc="center", fontweight="bold", pad=4)
    ax_d.set_xlabel("log10(new cases + 1), 7-day mean")
    ax_d.set_ylabel("log10(new deaths + 1), 7-day mean")
    style_cartesian(ax_d, "both")
    add_metric_box(ax_d, {"State-days": f"{len(scatter):,}", "Pearson r": f"{r:.2f}"}, loc="top_left", fontsize=6)
    add_letter(ax_d, "D")

    fig.suptitle("United States COVID-19 state burden matrix", x=0.5, y=0.975, ha="center", fontsize=10, fontweight="bold")
    fig.text(0.5, 0.943, "NYT state-level cumulative reports; daily increments derived by within-state differencing.", fontsize=6.5, ha="center")
    saved = save_figure(
        fig,
        axes,
        "fig1_state_burden_storyboard",
        finalizer_chart_plan("state burden storyboard", 4, ["heatmap_annotated", "line", "lollipop_horizontal", "scatter_regression"], "multipanel_grid"),
        qa_records,
    )

    national.to_csv(SOURCE_DIR / "fig1_panel_a_national_trend.csv", index=False)
    case_matrix.to_csv(SOURCE_DIR / "fig1_panel_b_state_week_case_matrix.csv")
    top20.iloc[::-1].to_csv(SOURCE_DIR / "fig1_panel_c_top20_burden.csv", index=False)
    scatter.to_csv(SOURCE_DIR / "fig1_panel_d_case_death_coupling_sample.csv", index=False)
    return saved


def figure_dual_heatmap(derived: dict[str, pd.DataFrame], qa_records: list[dict]):
    weekly = derived["weekly"]
    states = derived["top_states"]["state"].tolist()
    cases = build_matrix(weekly, states, "new_cases_7d")
    deaths = build_matrix(weekly, states, "new_deaths_7d")

    fig, axes = build_grid("R1_two_panel_horizontal", figsize=(13.5, 6.4), wspace=0.22)
    ax_a, ax_b = axes
    case_cmap = LinearSegmentedColormap.from_list("case_cmap", ["#F7FBFF", "#9ECAE1", PALETTE["cases"], "#08306B"])
    death_cmap = LinearSegmentedColormap.from_list("death_cmap", ["#FFF5F0", "#FCAE91", PALETTE["deaths"], "#67000D"])
    draw_heatmap(ax_a, cases, "Weekly case intensity by state", case_cmap, "log10(new cases + 1)", "A")
    draw_heatmap(ax_b, deaths, "Weekly death intensity by state", death_cmap, "log10(new deaths + 1)", "B")
    fig.suptitle("Parallel state burden matrices", x=0.5, y=0.985, ha="center", fontsize=10, fontweight="bold")
    fig.text(0.5, 0.947, "Rows are ordered identically by final cumulative cases, revealing asynchronous case and death burden waves.", fontsize=6.5, ha="center")
    saved = save_figure(
        fig,
        axes,
        "fig2_parallel_state_matrices",
        finalizer_chart_plan("parallel state matrices", 2, ["heatmap_annotated", "heatmap_pure"], "composite_two_lane"),
        qa_records,
    )
    cases.to_csv(SOURCE_DIR / "fig2_panel_a_weekly_case_matrix.csv")
    deaths.to_csv(SOURCE_DIR / "fig2_panel_b_weekly_death_matrix.csv")
    return saved


def figure_wave_atlas(df: pd.DataFrame, derived: dict[str, pd.DataFrame], qa_records: list[dict]):
    latest = derived["latest"]
    states = latest.head(6)["state"].tolist()
    fig, axes = build_grid("R3_two_by_three_grid", figsize=(15.8, 9.0), wspace=0.44, hspace=0.50)
    for ax, state, label in zip(axes, states, list("ABCDEF")):
        sub = df[df["state"] == state].sort_values("date")
        ax.fill_between(sub["date"], sub["new_cases_7d"], color=PALETTE["cases_light"], alpha=0.38, linewidth=0, zorder=1)
        ax.plot(sub["date"], sub["new_cases_7d"], color=PALETTE["cases"], lw=1.15, zorder=3, label="Cases")
        ax2 = ax.twinx()
        ax2.plot(sub["date"], sub["new_deaths_7d"], color=PALETTE["deaths"], lw=0.95, alpha=0.92, zorder=4, label="Deaths")
        peak = sub.loc[sub["new_cases_7d"].idxmax()]
        ax.axvline(peak["date"], color=PALETTE["neutral"], lw=0.7, ls=":", alpha=0.7, zorder=5)
        ax.text(
            0.03,
            0.82,
            f"{state}\npeak {fmt_large(float(peak['new_cases_7d']))}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=6.1,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#333333", lw=0.45, alpha=0.9),
            zorder=20,
        )
        ax.set_ylabel("New cases")
        is_right_col = label in ("C", "F")
        if is_right_col:
            ax2.set_ylabel("New deaths", labelpad=2)
        else:
            ax2.set_ylabel("")
            ax2.tick_params(axis="y", right=False, labelright=False)
            ax2.spines["right"].set_visible(False)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: fmt_large(x)))
        ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: fmt_large(x)))
        format_date_axis(ax)
        style_cartesian(ax, "y")
        ax2.tick_params(axis="y", labelsize=5.5, colors=PALETTE["deaths"])
        ax2.spines["right"].set_color(PALETTE["deaths"])
        if label == "A":
            ax.plot([], [], color=PALETTE["deaths"], lw=0.95, label="Deaths")
            ax.legend(loc="upper right", frameon=False)
        add_letter(ax, label)

    fig.suptitle("Top-state epidemic wave atlas", x=0.5, y=0.985, ha="center", fontsize=10, fontweight="bold")
    fig.text(0.5, 0.947, "Small multiples preserve within-state trajectories while keeping case/death semantics fixed across panels.", fontsize=6.5, ha="center")
    saved = save_figure(
        fig,
        axes,
        "fig3_top_state_wave_atlas",
        finalizer_chart_plan("top state wave atlas", 6, ["line", "line_ci"], "multipanel_grid"),
        qa_records,
    )
    df[df["state"].isin(states)].to_csv(SOURCE_DIR / "fig3_top_state_wave_atlas.csv", index=False)
    return saved


def figure_marginal_coupling(df: pd.DataFrame, qa_records: list[dict]):
    scatter = df.loc[(df["new_cases_7d"] > 0) & (df["new_deaths_7d"] > 0)].copy()
    scatter = scatter.sample(min(20000, len(scatter)), random_state=41)
    x = np.log10(scatter["new_cases_7d"].to_numpy() + 1)
    y = np.log10(scatter["new_deaths_7d"].to_numpy() + 1)

    fig, axes = build_grid("R8_main_with_marginal", figsize=(8.0, 8.0), hspace=0.05, wspace=0.05)
    ax_main, ax_top, ax_right, ax_corner = axes
    density_color_scatter(ax_main, x, y, cmap="GnBu_r", s=7, linewidth=0.10, with_colorbar=False)
    coeff = np.polyfit(x, y, deg=1)
    xs = np.linspace(x.min(), x.max(), 180)
    ax_main.plot(xs, coeff[0] * xs + coeff[1], color="black", lw=1.1, ls="--", zorder=6, label="Linear fit")
    ax_main.axhline(0, color=PALETTE["grid"], lw=0.7, zorder=0)
    ax_main.axvline(0, color=PALETTE["grid"], lw=0.7, zorder=0)
    ax_top.hist(x, bins=50, color=PALETTE["cases"], alpha=0.72, density=True, zorder=2)
    ax_right.hist(y, bins=50, color=PALETTE["deaths"], alpha=0.72, density=True, orientation="horizontal", zorder=2)
    ax_top.axis("off")
    ax_right.axis("off")
    ax_corner.axis("off")
    ax_main.set_xlabel("log10(new cases + 1), 7-day mean")
    ax_main.set_ylabel("log10(new deaths + 1), 7-day mean")
    ax_main.set_title("Coupled state-day morbidity and mortality burden", loc="center", fontweight="bold", pad=5)
    style_cartesian(ax_main, "both")
    r = float(np.corrcoef(x, y)[0, 1])
    add_metric_box(
        ax_main,
        {"State-days": f"{len(scatter):,}", "Pearson r": f"{r:.2f}", "Fit slope": f"{coeff[0]:.2f}"},
        loc="top_left",
        fontsize=6,
    )
    add_letter(ax_main, "A")
    ax_main.legend(loc="lower right", frameon=False)
    fig.suptitle("Case-death burden coupling with marginal distributions", x=0.5, y=0.985, ha="center", fontsize=10, fontweight="bold")
    saved = save_figure(
        fig,
        [ax_main],
        "fig4_case_death_marginal_coupling",
        finalizer_chart_plan("case death marginal coupling", 1, ["scatter_regression", "marginal_joint"], "marginal_joint"),
        qa_records,
    )
    scatter.to_csv(SOURCE_DIR / "fig4_case_death_marginal_coupling_sample.csv", index=False)
    return saved


def build_panel_manifest(qa_records: list[dict], figure_records: list[dict], render_qa: dict) -> dict:
    panels = [
        {
            "figure": "fig0_single_panel_national_burden_hero",
            "panel": "A",
            "title": "Single-panel national COVID burden hero",
            "chartType": "single_panel_peak_normalized_time_series",
            "sourceData": str(SOURCE_DIR / "fig0_single_panel_national_burden_hero.csv"),
            "statScope": "descriptive national 7-day burden indices derived from state daily rates",
        },
        {
            "figure": "fig1_state_burden_storyboard",
            "panel": "A",
            "title": "National epidemic waves",
            "chartType": "dual_axis_time_series",
            "sourceData": str(SOURCE_DIR / "fig1_panel_a_national_trend.csv"),
            "statScope": "descriptive 7-day rolling trend",
        },
        {
            "figure": "fig1_state_burden_storyboard",
            "panel": "B",
            "title": "State-week case burden matrix",
            "chartType": "weekly_heatmap",
            "sourceData": str(SOURCE_DIR / "fig1_panel_b_state_week_case_matrix.csv"),
            "statScope": "log10 transformed 7-day mean cases",
        },
        {
            "figure": "fig1_state_burden_storyboard",
            "panel": "C",
            "title": "Cumulative state burden ranking",
            "chartType": "ranked_lollipop",
            "sourceData": str(SOURCE_DIR / "fig1_panel_c_top20_burden.csv"),
            "statScope": "absolute cumulative counts",
        },
        {
            "figure": "fig1_state_burden_storyboard",
            "panel": "D",
            "title": "State-day case-death coupling",
            "chartType": "density_scatter_regression",
            "sourceData": str(SOURCE_DIR / "fig1_panel_d_case_death_coupling_sample.csv"),
            "statScope": "Pearson correlation on log-transformed sampled state-days",
        },
        {
            "figure": "fig2_parallel_state_matrices",
            "panel": "A",
            "title": "Weekly case intensity by state",
            "chartType": "weekly_heatmap",
            "sourceData": str(SOURCE_DIR / "fig2_panel_a_weekly_case_matrix.csv"),
            "statScope": "log10 transformed 7-day mean cases",
        },
        {
            "figure": "fig2_parallel_state_matrices",
            "panel": "B",
            "title": "Weekly death intensity by state",
            "chartType": "weekly_heatmap",
            "sourceData": str(SOURCE_DIR / "fig2_panel_b_weekly_death_matrix.csv"),
            "statScope": "log10 transformed 7-day mean deaths",
        },
        {
            "figure": "fig3_top_state_wave_atlas",
            "panel": "A-F",
            "title": "Top-state epidemic wave atlas",
            "chartType": "small_multiple_dual_axis_time_series",
            "sourceData": str(SOURCE_DIR / "fig3_top_state_wave_atlas.csv"),
            "statScope": "within-state 7-day rolling trends",
        },
        {
            "figure": "fig4_case_death_marginal_coupling",
            "panel": "A",
            "title": "Coupled state-day morbidity and mortality burden",
            "chartType": "marginal_joint_density_scatter",
            "sourceData": str(SOURCE_DIR / "fig4_case_death_marginal_coupling_sample.csv"),
            "statScope": "Pearson correlation and linear fit on log-transformed sampled state-days",
        },
    ]
    return {
        "layout": "five figure bundle; includes one explicit single-panel hero and multiple state-level atlas/storyboard figures",
        "figures": figure_records,
        "panels": panels,
        "sharedLegend": {
            "mode": "bottom_center",
            "figuresWithSharedLegend": [
                record["figure"] for record in qa_records if record.get("legendModeUsed") == "bottom_center"
            ],
        },
        "sharedColorbar": {
            "mode": "per-panel colorbar for heatmaps and density encodings where present",
            "colorbarPanelOverlapCount": sum(record.get("colorbarPanelOverlapCount", 0) for record in qa_records),
        },
        "renderQa": render_qa,
    }


def write_reports(df: pd.DataFrame, derived: dict[str, pd.DataFrame], qa_records: list[dict], figure_records: list[dict]) -> None:
    latest = derived["latest"]
    national = derived["national"]
    peak_cases = national.loc[national["new_cases"].idxmax()]
    peak_deaths = national.loc[national["new_deaths"].idxmax()]
    input_hash = file_sha256(INPUT_FILE)
    data_profile = {
        "filePath": str(INPUT_FILE),
        "inputSha256": input_hash,
        "format": "csv",
        "structure": "tidy longitudinal",
        "columns": list(df.columns),
        "semanticRoles": {
            "time": "date",
            "group": "state",
            "identifier": "fips",
            "cumulative_cases": "cases",
            "cumulative_deaths": "deaths",
            "derived_daily_cases": "new_cases",
            "derived_daily_deaths": "new_deaths",
        },
        "domainHints": {
            "primary": "epidemiology_public_health",
            "confidence": "high",
            "rationale": "State-stratified date series with cumulative cases and deaths.",
        },
        "nObservations": int(len(df)),
        "nGroups": int(df["state"].nunique()),
        "dateRange": [str(df["date"].min().date()), str(df["date"].max().date())],
        "missing": {k: int(v) for k, v in df[["date", "state", "fips", "cases", "deaths"]].isna().sum().items()},
        "riskFlags": [
            "cumulative counts converted to daily increments by differencing",
            "no population denominator supplied; figures do not claim incidence per capita",
            "reporting artifacts can create bursty increments; rolling 7-day means shown where trends are emphasized",
        ],
    }
    chart_plan = {
        "selectedChartBundle": "State burden matrix",
        "primaryChart": "heatmap_annotated",
        "secondaryCharts": ["line", "lollipop_horizontal", "scatter_regression", "marginal_joint"],
        "statMethod": "descriptive trend analysis; Pearson correlation for log daily case/death coupling",
        "narrativeArc": "multipanel_grid plus marginal_joint support figure",
        "journalProfile": JOURNAL_PROFILE,
        "colorMode": "domain_semantic",
        "dpi": 1200,
        "crowdingPolicy": "preserve_information",
    }
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
            "allPngNonblank": all(record["nonblankPng"] for record in qa_records),
            "renderContractReportLoaded": render_contract_loaded,
        },
    }
    panel_manifest = build_panel_manifest(qa_records, figure_records, render_qa)
    source_data_files = [str(path) for path in sorted(SOURCE_DIR.glob("*.csv"))]
    output_bundle = {
        "figures": figure_records,
        "code": str(OUTPUT_DIR / "generate_nyt_covid_states_showcase.py"),
        "statsReport": str(REPORT_DIR / "stats_report.md"),
        "sourceData": source_data_files,
        "panelManifest": str(REPORT_DIR / "panel_manifest.json"),
        "requirements": str(OUTPUT_DIR / "requirements.txt"),
        "metadata": str(REPORT_DIR / "metadata.json"),
        "renderQa": str(REPORT_DIR / "render_qa.json"),
        "renderContracts": str(RENDER_CONTRACT_PATH),
    }

    metadata = {
        "generatedBy": "scifig-generate",
        "bundle": "nyt_covid_states_public_health_showcase",
        "sourceData": str(INPUT_FILE),
        "inputSha256": input_hash,
        "workflowPreferences": {
            "interactionMode": "auto",
            "domainFamily": "epidemiology_public_health",
            "selectedChartBundle": "State burden matrix",
            "journalStyle": "epidemiology_public_health_showcase",
            "colorMode": "domain_semantic",
            "rasterDpi": 1200,
            "crowdingPolicy": "preserve_information",
        },
        "figures": figure_records,
        "dataProfile": data_profile,
        "chartPlan": chart_plan,
        "outputBundle": output_bundle,
    }

    (REPORT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (REPORT_DIR / "data_profile.json").write_text(json.dumps(data_profile, indent=2), encoding="utf-8")
    (REPORT_DIR / "chart_plan.json").write_text(json.dumps(chart_plan, indent=2), encoding="utf-8")
    (REPORT_DIR / "panel_manifest.json").write_text(json.dumps(panel_manifest, indent=2), encoding="utf-8")
    (REPORT_DIR / "output_bundle.json").write_text(json.dumps(output_bundle, indent=2), encoding="utf-8")
    (REPORT_DIR / "render_qa.json").write_text(json.dumps(render_qa, indent=2), encoding="utf-8")

    methods = f"""# Statistical and Methods Report

## Data

Input file: `{INPUT_FILE}`

Rows: {len(df):,}; states / territories: {df['state'].nunique()}; date range: {df['date'].min().date()} to {df['date'].max().date()}.

## Derivations

- Daily new cases and deaths were computed by within-state first differences of cumulative NYT reports and clipped at zero to avoid plotting negative reporting corrections as biological events.
- Seven-day rolling means were used in trend panels and state-week matrices to reduce reporting-cycle artifacts.
- No population denominator was supplied, so all burden panels show absolute reported counts rather than incidence per capita.

## Descriptive Results

- Final cumulative cases: {fmt_large(float(latest['cases'].sum()))}; final cumulative deaths: {fmt_large(float(latest['deaths'].sum()))}.
- Highest cumulative case burden: {latest.iloc[0]['state']} with {fmt_large(float(latest.iloc[0]['cases']))} cases.
- National maximum daily new cases occurred on {pd.Timestamp(peak_cases['date']).date()} with {fmt_large(float(peak_cases['new_cases']))} reported new cases.
- National maximum daily new deaths occurred on {pd.Timestamp(peak_deaths['date']).date()} with {fmt_large(float(peak_deaths['new_deaths']))} reported new deaths.

## Statistical Scope

The figures are descriptive epidemiological visualizations. They do not estimate causal effects, p-values, treatment effects, or population-standardized incidence because those quantities are not present in the supplied dataset.

## Reproducibility

- Input SHA-256: `{input_hash}`
- Generator: `{OUTPUT_DIR / "generate_nyt_covid_states_showcase.py"}`
- Render contract report: `{RENDER_CONTRACT_PATH}`
"""
    (REPORT_DIR / "stats_report.md").write_text(methods, encoding="utf-8")
    (OUTPUT_DIR / "requirements.txt").write_text(
        "\n".join(
            [
                "numpy>=1.24",
                "pandas>=2.0",
                "matplotlib>=3.7",
                "seaborn>=0.13",
                "scipy>=1.11",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    configure_style()
    if RENDER_CONTRACT_PATH.exists():
        RENDER_CONTRACT_PATH.unlink()
    df, derived = load_and_derive()
    figure_records: list[dict] = []
    qa_records: list[dict] = []

    for builder in (
        figure_national_wave_hero,
        figure_state_burden_story,
        figure_dual_heatmap,
        figure_wave_atlas,
        figure_marginal_coupling,
    ):
        before = len(qa_records)
        if builder is figure_marginal_coupling:
            saved = builder(df, qa_records)
        elif builder is figure_dual_heatmap:
            saved = builder(derived, qa_records)
        else:
            saved = builder(df, derived, qa_records)
        figure_records.append(
            {
                "name": qa_records[before]["figure"],
                "assets": saved,
                "hardFail": qa_records[before]["hardFail"],
            }
        )

    write_reports(df, derived, qa_records, figure_records)
    if any(record["hardFail"] for record in qa_records):
        raise SystemExit("Render QA reported hard failures. See reports/render_qa.json.")
    print(json.dumps({"output": str(OUTPUT_DIR), "figures": figure_records}, indent=2))


if __name__ == "__main__":
    main()
