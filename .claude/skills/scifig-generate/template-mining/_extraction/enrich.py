"""Semantic enrichment pass — adds narrative-arc, signature-trick clues
and preamble prose to the case-index. Reads each source_path recorded by
extract.py but only keeps ~600 chars of prose (the visual-analysis paragraph).
Run after extract.py.

Output (Stage-4 split):
  - case-index.json (slim runtime routing index — RUNTIME_KEEP_FIELDS only)
  - case-evidence.json (bulk images/code_blocks/visual_signals/... — gitignored)
  - narratives.md (human-readable per-case digest)
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TEMPLATE_ROOT = ROOT / "template"
SKILL_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent

CASE_INDEX = SKILL_DIR / "case-index.json"
CASE_EVIDENCE = SKILL_DIR / "case-evidence.json"

# Runtime routing (phases/02-recommend-stats.md rank_template_cases_for_family)
# reads only these fields. Everything else is bulk evidence (images, code_blocks,
# visual_signals, image_evidence, rc, ...) split into case-evidence.json —
# regenerable from template/, kept out of git.
RUNTIME_KEEP_FIELDS = {
    "id", "file", "source_path", "title", "narrative_arc", "preamble",
    "chart_families", "signature_tricks", "palette_hex", "cmaps",
    "grid", "counts", "template_motifs", "bundle_key", "learning_status",
}

# -------------- narrative arc classifier (title-driven) --------------
# Order matters; first match wins.
ARC_RULES: list[tuple[str, list[str]]] = [
    ("inset_overlay",        ["主图+嵌入", "画中画", "中心挖空", "立体高光", "嵌入"]),
    ("mirror_compare",       ["镜像玫瑰", "镜像", "双侧棒棒糖", "三角热图", "上三角"]),
    ("marginal_joint",       ["边缘直方图", "边缘分布", "边缘密度", "边缘核密度", "联合等高线", "联合残差"]),
    ("global_local",         ["全局与局部", "全局+局部", "全局SHAP", "全局影响", "全局预测"]),
    ("train_test_diagnostic",["训练_测试", "训练/测试", "预测区间", "残差诊断", "预测残差", "预测误差"]),
    ("n×n_pairwise",         ["皮尔逊", "Spearman", "相关性矩阵", "散点图矩阵", "n×n", "3x3", "3X3", "三角热图"]),
    ("composite_two_lane",   ["条形图与SHAP", "棒棒糖图与SHAP", "饼图与", "条形图与", "组合重要性",
                              "蜂群+条形", "条形+蜂群", "组合SHAP", "依赖图与"]),
    ("multipanel_grid",      ["多面板", "多子图", "多模型", "多维", "多变量", "多目标", "组合多面板",
                              "子图平铺", "组合图"]),
    ("hero",                 ["雷达图", "森林图", "堆叠小提琴", "渐变箱", "驼峰", "山脊图",
                              "教科书级", "像素级", "顶刊神图", "Nature 这张", "Cell 顶刊", "顶刊同款"]),
]

DEFAULT_ARC = "single_focus"

# -------------- signature-trick detection (regex over code) --------------
TRICK_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("polygon_polar_grid",       re.compile(r"polar.*spines\[.polar.\]\.set_visible\(False\)|spines\[.polar.\]", re.S)),
    ("imshow_gradient_box",      re.compile(r"imshow\([^)]*aspect=.auto.|gradient.*box|np\.linspace.*for.*imshow", re.S)),
    ("density_color_scatter",    re.compile(r"gaussian_kde|kde\(np\.vstack|c\s*=\s*z[^_a-z]|cmap=.viridis|cmap=.GnBu_r")),
    ("perfect_fit_diagonal",     re.compile(r"plot\(\[\s*0?\s*,?\s*lim\s*\]\s*,\s*\[|y\s*=\s*x|perfect\s*fit", re.I)),
    ("axes_inset_overlay",       re.compile(r"inset_axes\(|ax\.inset_axes")),
    ("twin_axes_color_spines",   re.compile(r"twinx|twiny|spines\[.right.\]\.set_color")),
    ("metric_text_box",          re.compile(r"transform\s*=\s*ax\w*\.transAxes[^\n]*\n[^\n]*bbox|bbox=dict\([^)]*boxstyle")),
    ("polygon_dashed_grid",      re.compile(r"for\s+\w+\s+in\s+\[[\d.,\s]+\][^\n]*plot\(.*linestyle=.--", re.S)),
    ("pvalue_stars_overlay",     re.compile(r"\*{1,3}.*p\s*<|significance|p_values|asterisk", re.I)),
    ("upper_triangle_split",     re.compile(r"i\s*<\s*j|i\s*>\s*j|tril|triu|np\.triu|np\.tril")),
    ("marginal_axes_grid",       re.compile(r"add_axes\(|append_axes|axes_divider|make_axes_locatable")),
    ("group_divider_axvline",    re.compile(r"axvline.*linestyle=.--|axvline.*color=.gray")),
    ("error_band_fill_between",  re.compile(r"fill_between[^)]*alpha")),
    ("ridgeline_offset_kde",     re.compile(r"kdeplot.*y_offset|ridge|offset\s*=\s*\d|np\.arange.*-\s*\d")),
    ("colored_bar_by_sign",      re.compile(r"color\s*=\s*\[\s*['\"]#[0-9A-Fa-f]+['\"]\s+if\s+\w+\s*[><]\s*0", re.I)),
    ("split_violin",             re.compile(r"violinplot\([^)]*split=True|sns\.violinplot.*split")),
    ("raincloud_combo",          re.compile(r"raincloud|half_violin|jitter.*scatter|stripplot.*+.*boxplot", re.S)),
    ("bezier_smooth_line",       re.compile(r"make_interp_spline|UnivariateSpline|interp1d.*cubic")),
    ("annotate_arrow",           re.compile(r"annotate\([^)]*arrowprops")),
    ("shaded_zone_axvspan",      re.compile(r"axvspan|axhspan")),
    ("hatch_fill",               re.compile(r"hatch\s*=\s*['\"]")),
    ("diverging_cell_label",     re.compile(r"sns\.heatmap\([^)]*annot=True|imshow.*text\(\s*j\s*,\s*i", re.S)),
    ("colored_marker_edge",      re.compile(r"edgecolor=.white|edgecolors=.white")),
    ("dotted_zero_axhline",      re.compile(r"axhline\(\s*0\s*,|axhline\(\s*y?\s*=?\s*0\s*,")),
    ("dual_y_bar_line",          re.compile(r"twinx.*\.bar\(|\.bar\(.*twinx", re.S)),
    ("colorbar_ticks_styled",    re.compile(r"colorbar.*set_ticks|cbar\.ax\.tick_params")),
    ("category_split_dashed",    re.compile(r"axvline.*linewidth.*alpha|axvline.*\.\d.*linestyle")),
    ("alpha_layered_scatter",    re.compile(r"scatter\([^)]*alpha=0\.\d[^)]*zorder=")),
    ("regression_band_fillbtw",  re.compile(r"fill_between\([^)]*color=.k.|fill_between.*black.*alpha")),
    ("polar_value_marker",       re.compile(r"errorbar\(\s*angles", re.S)),
]

# -------------- preamble extractor --------------
def pull_preamble(md: str) -> str:
    """Grab the first 800 chars after title that's prose (not code)."""
    # remove markdown code blocks
    no_code = re.sub(r"```.*?```", "", md, flags=re.DOTALL)
    no_imgs = re.sub(
        r"!\[([^\]]*)\]\([^)]+\)",
        lambda match: f" [image: {match.group(1).strip() or 'reference'}] ",
        no_code,
    )
    # take from first '原图' or '前言' to next 'Step ' / 'step '
    m = re.search(r"(原图解析|前言|视觉语言|视觉拆解)(.*?)(?=Step\s*1|步骤\s*1|核心代码|代码|\n#{1,3}\s*\d{2}\s)",
                  no_imgs, re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(0)
    else:
        text = no_imgs[:1500]
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:900]


def classify_arc(title: str) -> str:
    for arc, kws in ARC_RULES:
        if any(kw in title for kw in kws):
            return arc
    return DEFAULT_ARC


def detect_tricks(code: str) -> list[str]:
    out = []
    for name, pat in TRICK_PATTERNS:
        if pat.search(code):
            out.append(name)
    return out


def resolve_case_path(case: dict) -> Path:
    """Resolve both new source_path records and legacy file-only records."""
    if case.get("source_path"):
        return ROOT / case["source_path"]
    matches = sorted(TEMPLATE_ROOT.rglob(case["file"]))
    if not matches:
        raise FileNotFoundError(case["file"])
    return matches[0]


def main():
    cases = json.loads(CASE_INDEX.read_text(encoding="utf-8"))
    enriched = []
    arc_counter: Counter = Counter()
    trick_counter: Counter = Counter()

    for case in cases:
        path = resolve_case_path(case)
        md = path.read_text(encoding="utf-8", errors="replace")
        preamble = pull_preamble(md)
        # extract code blocks again (re-use pattern)
        code = "\n".join(re.findall(r"```(?:python)?\s*(.*?)```", md, flags=re.DOTALL))
        arc = classify_arc(case["id"])
        tricks = detect_tricks(code)
        case["narrative_arc"] = arc
        case["signature_tricks"] = tricks
        case["preamble"] = preamble
        case["image_evidence"] = {
            "image_count": case.get("image_count", 0),
            "remote_image_count": case.get("remote_image_count", 0),
            "first_images": [
                {
                    "alt": image.get("alt", ""),
                    "url": image.get("url", ""),
                    "line": image.get("line"),
                }
                for image in case.get("images", [])[:3]
            ],
        }
        enriched.append(case)
        arc_counter[arc] += 1
        for t in tricks:
            trick_counter[t] += 1

    slim = [{k: v for k, v in case.items() if k in RUNTIME_KEEP_FIELDS} for case in enriched]
    evidence = [dict({k: v for k, v in case.items() if k not in RUNTIME_KEEP_FIELDS},
                     id=case.get("id"), file=case.get("file")) for case in enriched]
    CASE_INDEX.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
    CASE_EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")

    # write a human-readable digest grouped by narrative arc
    out = ["# Template Mining — Per-Case Narrative & Trick Digest", "",
           f"Source: {len(cases)} cases.  Re-run `enrich.py` after `extract.py` to refresh.", ""]

    out.append("## Narrative arc distribution\n")
    out.append("| Arc | Cases | % |")
    out.append("|---|---|---|")
    for arc, n in arc_counter.most_common():
        out.append(f"| `{arc}` | {n} | {n/len(cases)*100:.0f}% |")

    out.append("\n## Signature-trick frequency (regex over code)\n")
    out.append("| Trick | Cases |")
    out.append("|---|---|")
    for t, n in trick_counter.most_common():
        out.append(f"| `{t}` | {n} |")

    out.append("\n## Per-case digest (grouped by narrative arc)\n")
    by_arc: dict[str, list[dict]] = {}
    for c in enriched:
        by_arc.setdefault(c["narrative_arc"], []).append(c)

    for arc, lst in sorted(by_arc.items(), key=lambda kv: -len(kv[1])):
        out.append(f"\n### Narrative arc: `{arc}` ({len(lst)} cases)\n")
        for c in lst:
            short_id = c["id"].split("_")[-1] if "_" in c["id"] else c["id"]
            fams = ",".join(c.get("chart_families", [])[:3]) or "—"
            grid = c["grid"]["gridspec"] or c["grid"]["subplots"] or "—"
            tricks = ",".join(c["signature_tricks"][:6]) or "—"
            palette = ",".join(c.get("palette_hex", [])[:4]) or "—"
            image_count = c.get("image_count", 0)
            code_blocks = c.get("code_block_count", 0)
            title = c["title"][:60]
            out.append(f"- **{short_id}** `{title}`")
            out.append(f"  - family: {fams} | grid: {grid} | palette: {palette} | images: {image_count} | code blocks: {code_blocks}")
            out.append(f"  - tricks: {tricks}")
            first_images = c.get("image_evidence", {}).get("first_images", [])
            if first_images:
                urls = "; ".join(image["url"] for image in first_images)
                out.append(f"  - image refs: {urls}")

    (OUT_DIR / "narratives.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Updated {CASE_INDEX} (added narrative_arc, signature_tricks, preamble)")
    print(f"Wrote {OUT_DIR/'narratives.md'}")
    print(f"Arc distribution: {dict(arc_counter.most_common())}")


if __name__ == "__main__":
    main()
