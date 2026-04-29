"""Template-mining extraction — runs once over 77 .md cases under template/articles.

Produces:
  - case-index.json      machine-readable per-case metadata for Phase 2/3 lookup
  - stats.md             aggregate frequency table consumed by 01/02/03 modules
  - palette-harvest.json grouped hex codes per case (feeds 03-palette-bank.md)

Zero external deps; pure stdlib. Run from repo root:
    python .claude/skills/scifig-generate/template-mining/_extraction/extract.py
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[5]
ARTICLES = ROOT / "template" / "articles"
OUT_DIR = Path(__file__).resolve().parent
SKILL_DIR = Path(__file__).resolve().parents[1]  # template-mining/

HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
RCPARAM_RE = re.compile(r"plt\.rcParams\s*(?:\[[^\]]+\]|\.update)\s*[=\(]")
RC_KEY_VAL = re.compile(r"['\"]([a-z]+\.[a-z.]+)['\"]\s*:\s*([^,}\n]+)")
RC_INDEX = re.compile(r"plt\.rcParams\[['\"]([a-z]+\.[a-z.]+)['\"]\]\s*=\s*([^\n]+)")
GRIDSPEC_RE = re.compile(r"GridSpec\s*\(\s*(\d+)\s*,\s*(\d+)")
SUBPLOTS_RE = re.compile(r"plt\.subplots\s*\(\s*(?:nrows\s*=\s*)?(\d+)?\s*,?\s*(?:ncols\s*=\s*)?(\d+)?")
FIGSIZE_RE = re.compile(r"figsize\s*=\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)")
ZORDER_RE = re.compile(r"zorder\s*=\s*(-?\d+)")
TWINX_RE = re.compile(r"\.twinx\(\)")
TWINY_RE = re.compile(r"\.twiny\(\)")
INSET_RE = re.compile(r"inset_axes")
AXVLINE_RE = re.compile(r"\.axvline\(")
AXHLINE_RE = re.compile(r"\.axhline\(")
TRANSAXES_RE = re.compile(r"transform\s*=\s*ax\w*\.transAxes")
DESPINE_RE = re.compile(r"spines\[['\"](top|right|left|bottom)['\"]\]\.set_visible\(False\)")
COLORBAR_RE = re.compile(r"colorbar\(|ColorbarBase\(")
ERRORBAR_RE = re.compile(r"\.errorbar\(")
FILL_BETWEEN_RE = re.compile(r"\.fill_between(?:x)?\(")
CONTOURF_RE = re.compile(r"\.contourf?\(")
SCATTER_RE = re.compile(r"\.scatter\(")
BAR_RE = re.compile(r"\.bar(?:h)?\(")
BOXPLOT_RE = re.compile(r"\.boxplot\(|sns\.boxplot|sns\.violinplot")
HIST_RE = re.compile(r"\.hist\(")
HEATMAP_RE = re.compile(r"sns\.heatmap|imshow\(|pcolormesh\(")
POLAR_RE = re.compile(r"projection\s*=\s*['\"]polar['\"]|polar=True|subplot_kw\s*=\s*\{[^}]*polar")
KDE_RE = re.compile(r"gaussian_kde\(|sns\.kdeplot\(")
ANNOT_TEXT_RE = re.compile(r"\.text\(")
LEGEND_RE = re.compile(r"\.legend\(")
SAVEFIG_DPI_RE = re.compile(r"savefig\.dpi['\"]\s*:\s*(\d+)|dpi\s*=\s*(\d+)")
CMAP_RE = re.compile(r"cmap\s*=\s*['\"]([\w_]+)['\"]")
ZORDER_GE_RE = re.compile(r"zorder\s*=\s*(\d+)")

JOURNAL_TOKENS = [
    ("Nature Comms", r"Nature\s*Comms?|Nat\.\s*Commun"),
    ("Nature Nano",  r"Nature\s*Nanotechnology"),
    ("Nature",       r"Nature(?!\s*(Comms|Nano|Methods|Materials))"),
    ("Cell",         r"\bCell\b(?!\s*Reports)"),
    ("Cell Reports", r"Cell\s*Reports"),
    ("Science",      r"\bScience\b"),
    ("Advanced Sci", r"Advanced\s*Science"),
    ("CEJ",          r"\bCEJ\b|Chemical\s*Engineering\s*Journal"),
    ("JECE",         r"\bJECE\b"),
    ("JBE",          r"\bJBE\b"),
    ("MGEA",         r"\bMGEA\b"),
    ("Materials Today", r"Materials\s*Today"),
]

CHART_FAMILIES = [
    ("radar",            ["radar", "雷达", "polar", "极坐标"]),
    ("forest",           ["forest", "森林"]),
    ("shap_composite",   ["SHAP", "shap"]),
    ("heatmap_pairwise", ["皮尔逊", "相关性矩阵", "spearman", "correlation matrix"]),
    ("heatmap",          ["热力图", "heatmap", "热图"]),
    ("scatter_regression", ["预测", "真实", "predicted", "actual", "回归预测散点", "拟合"]),
    ("dual_axis",        ["双Y轴", "双 Y 轴", "dual y", "双面板"]),
    ("marginal_joint",   ["边缘直方图", "边缘分布", "marginal", "joint"]),
    ("time_series_pi",   ["时序", "time series", "prediction interval", "预测区间"]),
    ("gradient_box",     ["渐变箱", "gradient box"]),
    ("lollipop",         ["棒棒糖", "lollipop"]),
    ("mirror_radial",    ["镜像玫瑰", "mirror radial"]),
    ("violin",           ["小提琴", "violin"]),
    ("raincloud",        ["雨云", "raincloud"]),
    ("box",              ["箱线", "boxplot"]),
    ("density_scatter",  ["密度散点", "density scatter", "二维核密度"]),
    ("pareto",           ["帕累托", "pareto"]),
    ("nmds_pca",         ["NMDS", "PCA", "PLS"]),
    ("ridgeline",        ["山脊", "ridgeline"]),
    ("treemap_pie",      ["饼图", "圆环", "pie", "donut"]),
    ("ale_pdp",          ["ALE", "PDP", "依赖图"]),
]


def detect_journal(text: str) -> list[str]:
    out = []
    for name, pat in JOURNAL_TOKENS:
        if re.search(pat, text, re.IGNORECASE):
            out.append(name)
    return out


def detect_chart_families(title: str, body: str) -> list[str]:
    text = title + " " + body
    out = []
    for family, kws in CHART_FAMILIES:
        if any(kw.lower() in text.lower() for kw in kws):
            out.append(family)
    return out


def parse_code_blocks(md: str) -> str:
    blocks = re.findall(r"```(?:python)?\s*(.*?)```", md, flags=re.DOTALL)
    return "\n".join(blocks)


def harvest_rcparams(code: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in RC_KEY_VAL.findall(code):
        out[k] = v.strip().rstrip(",")
    for k, v in RC_INDEX.findall(code):
        out[k] = v.strip().rstrip(",")
    return out


def harvest_palette(code: str) -> list[str]:
    seen, ordered = set(), []
    for m in HEX_RE.findall(code):
        m_norm = m.upper()
        if m_norm not in seen:
            seen.add(m_norm)
            ordered.append(m_norm)
    return ordered


def detect_grid(code: str) -> dict:
    info: dict = {"gridspec": None, "subplots": None, "figsize": None}
    g = GRIDSPEC_RE.search(code)
    if g:
        info["gridspec"] = (int(g.group(1)), int(g.group(2)))
    s = SUBPLOTS_RE.search(code)
    if s and (s.group(1) or s.group(2)):
        nrows = int(s.group(1)) if s.group(1) else 1
        ncols = int(s.group(2)) if s.group(2) else 1
        info["subplots"] = (nrows, ncols)
    f = FIGSIZE_RE.search(code)
    if f:
        info["figsize"] = (float(f.group(1)), float(f.group(2)))
    return info


def count_hits(pattern: re.Pattern, text: str) -> int:
    return len(pattern.findall(text))


def case_record(path: Path) -> dict:
    md = path.read_text(encoding="utf-8", errors="replace")
    code = parse_code_blocks(md)
    rcparams = harvest_rcparams(code)
    palette = harvest_palette(code)
    grid = detect_grid(code)
    zorders = [int(z) for z in ZORDER_RE.findall(code)]
    cmaps = list(set(CMAP_RE.findall(code)))
    title = path.stem.split("_")[0] if "_" in path.stem else path.stem
    journals = detect_journal(md[:3000])
    families = detect_chart_families(path.stem, md[:6000])
    return {
        "id": path.stem,
        "file": path.name,
        "title": title,
        "journals": journals,
        "chart_families": families,
        "rc": {
            "font.family":       rcparams.get("font.family"),
            "mathtext.fontset":  rcparams.get("mathtext.fontset"),
            "font.size":         rcparams.get("font.size"),
            "axes.linewidth":    rcparams.get("axes.linewidth"),
            "xtick.direction":   rcparams.get("xtick.direction"),
            "ytick.direction":   rcparams.get("ytick.direction"),
            "savefig.dpi":       rcparams.get("savefig.dpi"),
            "savefig.bbox":      rcparams.get("savefig.bbox"),
        },
        "palette_hex": palette,
        "cmaps": cmaps,
        "grid": grid,
        "counts": {
            "zorder_calls":   len(zorders),
            "zorder_max":     max(zorders) if zorders else None,
            "zorder_distinct_levels": len(set(zorders)),
            "twinx":          count_hits(TWINX_RE, code),
            "twiny":          count_hits(TWINY_RE, code),
            "inset_axes":     count_hits(INSET_RE, code),
            "axvline":        count_hits(AXVLINE_RE, code),
            "axhline":        count_hits(AXHLINE_RE, code),
            "transAxes":      count_hits(TRANSAXES_RE, code),
            "despine_calls":  count_hits(DESPINE_RE, code),
            "errorbar":       count_hits(ERRORBAR_RE, code),
            "fill_between":   count_hits(FILL_BETWEEN_RE, code),
            "scatter":        count_hits(SCATTER_RE, code),
            "bar":            count_hits(BAR_RE, code),
            "boxplot":        count_hits(BOXPLOT_RE, code),
            "hist":           count_hits(HIST_RE, code),
            "heatmap":        count_hits(HEATMAP_RE, code),
            "kde":            count_hits(KDE_RE, code),
            "polar":          count_hits(POLAR_RE, code),
            "contourf":       count_hits(CONTOURF_RE, code),
            "annotation_text": count_hits(ANNOT_TEXT_RE, code),
            "legend_calls":   count_hits(LEGEND_RE, code),
            "colorbar":       count_hits(COLORBAR_RE, code),
        },
        "code_lines": code.count("\n") + 1,
    }


def aggregate(records: list[dict]) -> dict:
    n = len(records)
    rc_keys = ("font.family", "mathtext.fontset", "font.size", "axes.linewidth",
               "xtick.direction", "ytick.direction", "savefig.dpi", "savefig.bbox")
    rc_freq = {k: sum(1 for r in records if r["rc"].get(k)) for k in rc_keys}
    feature_freq = {
        "uses_zorder":      sum(1 for r in records if r["counts"]["zorder_calls"] > 0),
        "uses_gridspec":    sum(1 for r in records if r["grid"]["gridspec"]),
        "uses_subplots":    sum(1 for r in records if r["grid"]["subplots"]),
        "uses_twinx":       sum(1 for r in records if r["counts"]["twinx"] > 0),
        "uses_inset":       sum(1 for r in records if r["counts"]["inset_axes"] > 0),
        "uses_axvline":     sum(1 for r in records if r["counts"]["axvline"] > 0),
        "uses_axhline":     sum(1 for r in records if r["counts"]["axhline"] > 0),
        "uses_transAxes":   sum(1 for r in records if r["counts"]["transAxes"] > 0),
        "uses_despine":     sum(1 for r in records if r["counts"]["despine_calls"] > 0),
        "uses_errorbar":    sum(1 for r in records if r["counts"]["errorbar"] > 0),
        "uses_fill_between": sum(1 for r in records if r["counts"]["fill_between"] > 0),
        "uses_polar":       sum(1 for r in records if r["counts"]["polar"] > 0),
        "uses_kde":         sum(1 for r in records if r["counts"]["kde"] > 0),
        "uses_colorbar":    sum(1 for r in records if r["counts"]["colorbar"] > 0),
    }
    family_freq = Counter()
    for r in records:
        for f in r["chart_families"]:
            family_freq[f] += 1
    journal_freq = Counter()
    for r in records:
        for j in r["journals"]:
            journal_freq[j] += 1
    cmap_freq = Counter()
    for r in records:
        cmap_freq.update(r["cmaps"])
    grid_shapes = Counter()
    for r in records:
        for k in ("gridspec", "subplots"):
            if r["grid"].get(k):
                grid_shapes[f"{k}:{r['grid'][k][0]}x{r['grid'][k][1]}"] += 1
    palette_freq = Counter()
    for r in records:
        palette_freq.update(r["palette_hex"])
    rc_value_freq = defaultdict(Counter)
    for r in records:
        for k in rc_keys:
            v = r["rc"].get(k)
            if v:
                rc_value_freq[k][v.strip().strip("'\"")] += 1
    return {
        "n_cases":        n,
        "rc_freq":        rc_freq,
        "rc_value_freq":  {k: dict(v.most_common(10)) for k, v in rc_value_freq.items()},
        "feature_freq":   feature_freq,
        "family_freq":    dict(family_freq.most_common()),
        "journal_freq":   dict(journal_freq.most_common()),
        "cmap_freq":      dict(cmap_freq.most_common(20)),
        "grid_shapes":    dict(grid_shapes.most_common(20)),
        "palette_top60":  dict(palette_freq.most_common(60)),
    }


def render_stats_md(agg: dict) -> str:
    n = agg["n_cases"]
    lines = [f"# Template Mining — Aggregated Stats (n={n})\n"]
    lines.append("Auto-generated by `_extraction/extract.py`. Do not edit; rerun the script.\n\n")

    lines.append("## rcParams declaration frequency\n")
    lines.append("| Key | Cases declaring | % |")
    lines.append("|---|---|---|")
    for k, v in agg["rc_freq"].items():
        lines.append(f"| `{k}` | {v}/{n} | {v/n*100:.0f}% |")

    lines.append("\n## rcParams top values (most common)\n")
    for k, vals in agg["rc_value_freq"].items():
        if not vals:
            continue
        items = ", ".join(f"`{val}` ({cnt})" for val, cnt in vals.items())
        lines.append(f"- **{k}** — {items}")

    lines.append("\n## Rendering feature frequency\n")
    lines.append("| Feature | Cases | % |")
    lines.append("|---|---|---|")
    for k, v in agg["feature_freq"].items():
        lines.append(f"| {k} | {v}/{n} | {v/n*100:.0f}% |")

    lines.append("\n## Chart family detection (heuristic, multi-label)\n")
    lines.append("| Family | Cases |")
    lines.append("|---|---|")
    for k, v in agg["family_freq"].items():
        lines.append(f"| {k} | {v} |")

    lines.append("\n## Journal/venue tags\n")
    lines.append("| Venue | Cases |")
    lines.append("|---|---|")
    for k, v in agg["journal_freq"].items():
        lines.append(f"| {k} | {v} |")

    lines.append("\n## Top colormaps\n")
    lines.append("| cmap | Cases |")
    lines.append("|---|---|")
    for k, v in agg["cmap_freq"].items():
        lines.append(f"| `{k}` | {v} |")

    lines.append("\n## Multi-panel grid shapes\n")
    lines.append("| Shape | Cases |")
    lines.append("|---|---|")
    for k, v in agg["grid_shapes"].items():
        lines.append(f"| {k} | {v} |")

    lines.append("\n## Top 60 palette hex codes (corpus-wide)\n")
    lines.append("| Hex | Cases |")
    lines.append("|---|---|")
    for k, v in agg["palette_top60"].items():
        lines.append(f"| `{k}` | {v} |")

    return "\n".join(lines) + "\n"


def main():
    md_files = sorted(ARTICLES.glob("*.md"))
    records = [case_record(p) for p in md_files]
    agg = aggregate(records)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    case_index = SKILL_DIR / "case-index.json"
    case_index.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    palette_harvest = OUT_DIR / "palette-harvest.json"
    palette_harvest.write_text(
        json.dumps({r["id"]: r["palette_hex"] for r in records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stats_md = OUT_DIR / "stats.md"
    stats_md.write_text(render_stats_md(agg), encoding="utf-8")

    agg_json = OUT_DIR / "stats.json"
    agg_json.write_text(json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {case_index}")
    print(f"Wrote {palette_harvest}")
    print(f"Wrote {stats_md}")
    print(f"Wrote {agg_json}")
    print(f"n_cases = {len(records)}")


if __name__ == "__main__":
    main()
