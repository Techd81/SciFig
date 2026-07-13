"""Template-mining extraction over every Markdown case under template/.

Produces:
  - case-index.json      machine-readable per-case metadata for Phase 2/3 lookup
  - stats.md             aggregate frequency table consumed by 01/02/03 modules
  - palette-harvest.json grouped hex codes per case (feeds 03-palette-bank.md)

Zero external deps; pure stdlib. Run from repo root:
    python scifig/knowledge/scripts/extract.py
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_ROOT = ROOT / "template"
OUT_DIR = Path(__file__).resolve().parent
SKILL_DIR = Path(__file__).resolve().parents[1]  # knowledge/

HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
CODE_BLOCK_RE = re.compile(r"```([A-Za-z0-9_+.-]*)[^\n]*\n(.*?)```", re.DOTALL)
INLINE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+['\"]([^'\"]+)['\"])?\)")
REF_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\[([^\]]+)\]")
REF_DEF_RE = re.compile(r"^\[([^\]]+)\]:\s*(\S+)(?:\s+['\"]([^'\"]+)['\"])?\s*$", re.MULTILINE)
HTML_IMAGE_RE = re.compile(r"<img\b[^>]*\bsrc=['\"]([^'\"]+)['\"][^>]*>", re.IGNORECASE)
ALT_RE = re.compile(r"\balt=['\"]([^'\"]*)['\"]", re.IGNORECASE)
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
LEGEND_LOC_RE = re.compile(r"\.legend\([^)]*loc\s*=\s*['\"]([^'\"]+)['\"]", re.DOTALL)
LEGEND_BBOX_RE = re.compile(r"\.legend\([^)]*bbox_to_anchor\s*=\s*\(([^)]+)\)", re.DOTALL)
LEGEND_NCOL_RE = re.compile(r"\.legend\([^)]*ncol\s*=\s*(\d+)", re.DOTALL)
BBOX_RE = re.compile(r"bbox\s*=\s*dict\(|bbox=dict\(")
ARROW_RE = re.compile(r"arrowprops\s*=\s*dict\(|arrowprops=dict\(")
FONT_SIZE_RE = re.compile(r"(?:fontsize|font_size|size)\s*=\s*([\d.]+)")
LINEWIDTH_RE = re.compile(r"(?:linewidth|lw)\s*=\s*([\d.]+)")
ALPHA_RE = re.compile(r"alpha\s*=\s*([\d.]+)")
SAVEFIG_DPI_RE = re.compile(r"savefig\.dpi['\"]\s*:\s*(\d+)|dpi\s*=\s*(\d+)")
SAVEFIG_RE = re.compile(r"\.savefig\(")
SAVEFIG_FORMAT_RE = re.compile(r"\.savefig\([^)]*['\"]([^'\"]+\.(?:png|pdf|svg|tif|tiff|eps))['\"]", re.IGNORECASE | re.DOTALL)
BBOX_TIGHT_RE = re.compile(r"bbox_inches\s*=\s*['\"]tight['\"]")
TIGHT_LAYOUT_RE = re.compile(r"\.tight_layout\(")
CONSTRAINED_LAYOUT_RE = re.compile(r"constrained_layout\s*=\s*True")
SUBPLOTS_ADJUST_RE = re.compile(r"\.subplots_adjust\(")
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
    ("radar",            ["radar", "雷达", "polar", "极坐�?]),
    ("forest",           ["forest", "森林"]),
    ("shap_composite",   ["SHAP", "shap"]),
    ("heatmap_pairwise", ["皮尔�?, "相关性矩�?, "spearman", "correlation matrix"]),
    ("heatmap",          ["热力�?, "heatmap", "热图"]),
    ("scatter_regression", ["预测", "真实", "predicted", "actual", "回归预测散点", "拟合"]),
    ("dual_axis",        ["双Y�?, "�?Y �?, "dual y", "双面�?]),
    ("marginal_joint",   ["边缘直方�?, "边缘分布", "marginal", "joint"]),
    ("time_series_pi",   ["时序", "time series", "prediction interval", "预测区间"]),
    ("gradient_box",     ["渐变�?, "gradient box"]),
    ("lollipop",         ["棒棒�?, "lollipop"]),
    ("mirror_radial",    ["镜像玫瑰", "mirror radial"]),
    ("violin",           ["小提�?, "violin"]),
    ("raincloud",        ["雨云", "raincloud"]),
    ("box",              ["箱线", "boxplot"]),
    ("density_scatter",  ["密度散点", "density scatter", "二维核密�?]),
    ("pareto",           ["帕累�?, "pareto"]),
    ("nmds_pca",         ["NMDS", "PCA", "PLS"]),
    ("ridgeline",        ["山脊", "ridgeline"]),
    ("treemap_pie",      ["饼图", "圆环", "pie", "donut"]),
    ("ale_pdp",          ["ALE", "PDP", "依赖�?]),
]


def iter_template_markdown() -> list[Path]:
    """Return every template Markdown case, including newer article batches."""
    return sorted(
        p for p in TEMPLATE_ROOT.rglob("*")
        if p.is_file() and p.suffix.lower() in {".md", ".markdown"}
    )


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


def parse_code_block_records(md: str) -> list[dict]:
    records: list[dict] = []
    for idx, match in enumerate(CODE_BLOCK_RE.finditer(md), start=1):
        lang = (match.group(1) or "").strip().lower() or "plain"
        code = match.group(2).strip("\n")
        records.append({
            "index": idx,
            "lang": lang,
            "line_count": code.count("\n") + (1 if code else 0),
            "char_count": len(code),
            "starts_with": code.splitlines()[0][:120] if code.splitlines() else "",
        })
    return records


def parse_code_blocks(md: str) -> str:
    blocks = [match.group(2) for match in CODE_BLOCK_RE.finditer(md)]
    return "\n".join(blocks)


def _line_number(text: str, start: int) -> int:
    return text.count("\n", 0, start) + 1


def _image_ext(url: str) -> str:
    wx_fmt = re.search(r"wx_fmt(?:%3D|=)([A-Za-z0-9]+)", url, re.IGNORECASE)
    if wx_fmt:
        return wx_fmt.group(1).lower()
    mmbiz_fmt = re.search(r"mmbiz_([A-Za-z0-9]+)", url, re.IGNORECASE)
    if mmbiz_fmt:
        return mmbiz_fmt.group(1).lower()
    clean = url.split("?", 1)[0].split("#", 1)[0]
    suffix = Path(clean).suffix.lower().lstrip(".")
    return suffix if suffix in {"png", "jpg", "jpeg", "gif", "webp", "svg", "tif", "tiff"} else "unknown"


def parse_markdown_images(md: str) -> list[dict]:
    """Extract inline, reference-style, and HTML image references."""
    without_code = CODE_BLOCK_RE.sub("", md)
    ref_defs = {
        key.strip().lower(): {"url": url, "title": title or ""}
        for key, url, title in REF_DEF_RE.findall(without_code)
    }
    images: list[dict] = []

    for match in INLINE_IMAGE_RE.finditer(without_code):
        alt, url, title = match.group(1), match.group(2), match.group(3) or ""
        images.append({
            "kind": "markdown_inline",
            "alt": alt.strip(),
            "url": url.strip(),
            "title": title.strip(),
            "line": _line_number(without_code, match.start()),
            "is_remote": bool(re.match(r"https?://", url.strip(), re.I)),
            "extension": _image_ext(url.strip()),
        })

    for match in REF_IMAGE_RE.finditer(without_code):
        alt, ref = match.group(1), match.group(2)
        target = ref_defs.get(ref.strip().lower(), {})
        if not target:
            continue
        url = target["url"]
        images.append({
            "kind": "markdown_reference",
            "alt": alt.strip(),
            "url": url.strip(),
            "title": target.get("title", "").strip(),
            "line": _line_number(without_code, match.start()),
            "is_remote": bool(re.match(r"https?://", url.strip(), re.I)),
            "extension": _image_ext(url.strip()),
        })

    for match in HTML_IMAGE_RE.finditer(without_code):
        tag = match.group(0)
        url = match.group(1)
        alt_match = ALT_RE.search(tag)
        images.append({
            "kind": "html",
            "alt": alt_match.group(1).strip() if alt_match else "",
            "url": url.strip(),
            "title": "",
            "line": _line_number(without_code, match.start()),
            "is_remote": bool(re.match(r"https?://", url.strip(), re.I)),
            "extension": _image_ext(url.strip()),
        })

    seen: set[tuple[str, int]] = set()
    unique: list[dict] = []
    for image in images:
        key = (image["url"], image["line"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(image)
    return unique


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


def visual_signal_record(md: str, code: str) -> dict:
    legend_locs = sorted(set(LEGEND_LOC_RE.findall(code)))
    legend_bbox = sorted(set(m.strip() for m in LEGEND_BBOX_RE.findall(code)))
    font_sizes = [float(v) for v in FONT_SIZE_RE.findall(code)]
    linewidths = [float(v) for v in LINEWIDTH_RE.findall(code)]
    alphas = [float(v) for v in ALPHA_RE.findall(code)]
    savefig_targets = sorted(set(SAVEFIG_FORMAT_RE.findall(code)))
    lower_md = md.lower()
    return {
        "layout": {
            "uses_gridspec": bool(GRIDSPEC_RE.search(code)),
            "uses_inset": bool(INSET_RE.search(code)),
            "uses_twin_axes": bool(TWINX_RE.search(code) or TWINY_RE.search(code)),
            "uses_tight_layout": bool(TIGHT_LAYOUT_RE.search(code)),
            "uses_constrained_layout": bool(CONSTRAINED_LAYOUT_RE.search(code)),
            "uses_subplots_adjust": bool(SUBPLOTS_ADJUST_RE.search(code)),
        },
        "legend": {
            "calls": count_hits(LEGEND_RE, code),
            "loc_values": legend_locs,
            "bbox_to_anchor": legend_bbox,
            "ncol_values": [int(v) for v in LEGEND_NCOL_RE.findall(code)],
            "mentions_outside": any(token in lower_md for token in ("legend", "图例", "外置", "outside")),
        },
        "annotation": {
            "text_calls": count_hits(ANNOT_TEXT_RE, code),
            "uses_bbox": bool(BBOX_RE.search(code)),
            "uses_arrowprops": bool(ARROW_RE.search(code)),
            "uses_trans_axes": bool(TRANSAXES_RE.search(code)),
            "mentions_significance": any(token in md for token in ("显著�?, "星号", "p <", "P <", "***", "**")),
        },
        "typography": {
            "font_sizes": sorted(set(font_sizes)),
            "font_size_min": min(font_sizes) if font_sizes else None,
            "font_size_max": max(font_sizes) if font_sizes else None,
            "linewidths": sorted(set(linewidths)),
            "linewidth_min": min(linewidths) if linewidths else None,
            "linewidth_max": max(linewidths) if linewidths else None,
            "alpha_values": sorted(set(alphas)),
        },
        "export": {
            "savefig_calls": count_hits(SAVEFIG_RE, code),
            "dpi_mentions": [int(a or b) for a, b in SAVEFIG_DPI_RE.findall(code)],
            "bbox_tight": bool(BBOX_TIGHT_RE.search(code)),
            "targets": savefig_targets,
            "mentions_publication": any(token in md for token in ("300 dpi", "600 dpi", "1200 dpi", "论文", "期刊", "顶刊")),
        },
    }


def count_hits(pattern: re.Pattern, text: str) -> int:
    return len(pattern.findall(text))


def case_record(path: Path) -> dict:
    md = path.read_text(encoding="utf-8", errors="replace")
    code_blocks = parse_code_block_records(md)
    images = parse_markdown_images(md)
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
        "source_path": path.relative_to(ROOT).as_posix(),
        "source_dir": path.parent.relative_to(ROOT).as_posix(),
        "title": title,
        "journals": journals,
        "chart_families": families,
        "images": images,
        "image_count": len(images),
        "remote_image_count": sum(1 for image in images if image["is_remote"]),
        "code_blocks": code_blocks,
        "code_block_count": len(code_blocks),
        "code_block_langs": sorted(set(block["lang"] for block in code_blocks)),
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
        "visual_signals": visual_signal_record(md, code),
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
        "code_lines": code.count("\n") + (1 if code else 0),
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
    image_ext_freq = Counter()
    image_host_freq = Counter()
    code_lang_freq = Counter()
    legend_loc_freq = Counter()
    for r in records:
        for image in r.get("images", []):
            image_ext_freq[image.get("extension") or "unknown"] += 1
            host_match = re.match(r"https?://([^/]+)", image.get("url", ""), re.I)
            if host_match:
                image_host_freq[host_match.group(1).lower()] += 1
        code_lang_freq.update(r.get("code_block_langs", []))
        legend_loc_freq.update(r.get("visual_signals", {}).get("legend", {}).get("loc_values", []))
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
        "image_stats": {
            "cases_with_images": sum(1 for r in records if r.get("image_count", 0) > 0),
            "image_refs_total": sum(r.get("image_count", 0) for r in records),
            "remote_image_refs_total": sum(r.get("remote_image_count", 0) for r in records),
            "unique_image_urls": len({image["url"] for r in records for image in r.get("images", [])}),
            "extensions": dict(image_ext_freq.most_common()),
            "remote_hosts": dict(image_host_freq.most_common(20)),
        },
        "code_block_stats": {
            "cases_with_code_blocks": sum(1 for r in records if r.get("code_block_count", 0) > 0),
            "code_blocks_total": sum(r.get("code_block_count", 0) for r in records),
            "languages": dict(code_lang_freq.most_common()),
        },
        "legend_loc_freq": dict(legend_loc_freq.most_common()),
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
    lines = [f"# Template Mining �?Aggregated Stats (n={n})\n"]
    lines.append("Auto-generated by `knowledge/scripts/extract.py`. Do not edit; rerun the script.\n\n")

    image_stats = agg["image_stats"]
    code_stats = agg["code_block_stats"]
    lines.append("## Markdown evidence coverage\n")
    lines.append("| Evidence | Count |")
    lines.append("|---|---:|")
    lines.append(f"| Cases with image refs | {image_stats['cases_with_images']}/{n} |")
    lines.append(f"| Image refs total | {image_stats['image_refs_total']} |")
    lines.append(f"| Remote image refs | {image_stats['remote_image_refs_total']} |")
    lines.append(f"| Unique image URLs | {image_stats['unique_image_urls']} |")
    lines.append(f"| Cases with code blocks | {code_stats['cases_with_code_blocks']}/{n} |")
    lines.append(f"| Code blocks total | {code_stats['code_blocks_total']} |")

    lines.append("\n## Image extensions\n")
    lines.append("| Extension | Refs |")
    lines.append("|---|---:|")
    for ext, count in image_stats["extensions"].items():
        lines.append(f"| `{ext}` | {count} |")

    lines.append("\n## Code block languages\n")
    lines.append("| Language | Cases |")
    lines.append("|---|---:|")
    for lang, count in code_stats["languages"].items():
        lines.append(f"| `{lang}` | {count} |")

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
        lines.append(f"- **{k}** �?{items}")

    lines.append("\n## Rendering feature frequency\n")
    lines.append("| Feature | Cases | % |")
    lines.append("|---|---|---|")
    for k, v in agg["feature_freq"].items():
        lines.append(f"| {k} | {v}/{n} | {v/n*100:.0f}% |")

    lines.append("\n## Legend placement values\n")
    lines.append("| loc | Cases |")
    lines.append("|---|---:|")
    for loc, count in agg["legend_loc_freq"].items():
        lines.append(f"| `{loc}` | {count} |")

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
    md_files = iter_template_markdown()
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
