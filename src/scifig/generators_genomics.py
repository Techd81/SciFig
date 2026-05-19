"""Dedicated genomics-family generators for the chart registry.

volcano    — Volcano plot (log2FC vs -log10(p), significance thresholds)
ma_plot    — MA plot (mean expression vs log2FC)
manhattan  — Manhattan plot (cumulative chromosomal position vs -log10(p))
"""

from __future__ import annotations

import math
from typing import Any, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
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


def _categorical_columns(df: pd.DataFrame) -> list[str]:
    numeric = set(_numeric_columns(df))
    return [str(c) for c in df.columns if str(c) not in numeric]


def _first_valid(df: pd.DataFrame, *candidates: Optional[str]) -> Optional[str]:
    columns = {str(c) for c in df.columns}
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _first_numeric_valid(df: pd.DataFrame, *candidates: Optional[str]) -> Optional[str]:
    numeric = set(_numeric_columns(df))
    for candidate in candidates:
        if candidate in numeric:
            return candidate
    return None


def _unique_columns(*columns: Optional[str]) -> list[str]:
    result: list[str] = []
    for column in columns:
        if column and column not in result:
            result.append(column)
    return result


def _decorate_axes(ax: Any) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _fallback_empty(ax: Any, title: str, message: str) -> Any:
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


def _short_label(value: Any, width: int = 16) -> str:
    text = str(value)
    return text if len(text) <= width else text[: width - 1] + "..."


# -- Volcano ------------------------------------------------------------------

@register_chart("volcano")
def gen_volcano(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Volcano plot — log2 fold-change vs -log10(p), with significance
    thresholds (|FC|>1, p<0.05) and red/blue colouring."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    fc_col = roles.get("fc") or roles.get("x") or (numeric[0] if numeric else None)
    p_col = roles.get("p") or roles.get("pvalue") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if fc_col not in df.columns or p_col not in df.columns:
        ax.text(0.5, 0.5, "Need fold-change + p-value columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Volcano", loc="center", fontweight="bold", pad=5)
        return ax

    x = pd.to_numeric(df[fc_col], errors="coerce")
    y = -np.log10(pd.to_numeric(df[p_col], errors="coerce").clip(lower=1e-300))
    sig = (y > -math.log10(0.05)) & (x.abs() >= 1)
    ax.scatter(x[~sig], y[~sig], s=12, color="#999999", alpha=0.55, linewidths=0)
    ax.scatter(x[sig & (x > 0)], y[sig & (x > 0)], s=14, color=colors[4 % len(colors)],
               alpha=0.8, linewidths=0)
    ax.scatter(x[sig & (x < 0)], y[sig & (x < 0)], s=14, color=colors[5 % len(colors)],
               alpha=0.8, linewidths=0)
    ax.axvline(1, color="#555555", lw=0.6, ls="--")
    ax.axvline(-1, color="#555555", lw=0.6, ls="--")
    ax.axhline(-math.log10(0.05), color="#555555", lw=0.6, ls=":")
    ax.set_xlabel("log2 fold-change")
    ax.set_ylabel("-log10(p)")
    ax.set_title("Volcano", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


# -- MA plot ------------------------------------------------------------------

@register_chart("ma_plot")
def gen_ma_plot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                rc_params: dict[str, Any], palette: dict[str, Any],
                col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """MA plot — mean expression (A) vs log2 fold-change (M), with zero line."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    a_col = roles.get("mean") or roles.get("x") or (numeric[0] if numeric else None)
    m_col = roles.get("fc") or roles.get("value") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if a_col not in df.columns or m_col not in df.columns:
        ax.text(0.5, 0.5, "Need mean + fold-change columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("MA plot", loc="center", fontweight="bold", pad=5)
        return ax

    a = pd.to_numeric(df[a_col], errors="coerce")
    m = pd.to_numeric(df[m_col], errors="coerce")
    ax.scatter(a, m, s=12, color=colors[1 % len(colors)], alpha=0.65, linewidths=0)
    ax.axhline(0, color="#555555", lw=0.6, ls="--")
    ax.set_xlabel("Mean expression (A)")
    ax.set_ylabel("log2 fold-change (M)")
    ax.set_title("MA plot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


# -- Manhattan ----------------------------------------------------------------

@register_chart("manhattan")
def gen_manhattan(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Manhattan plot — cumulative chromosomal position vs -log10(p),
    alternating chrom colours + genome-wide significance line."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(profile=data_profile)
    numeric = _numeric_columns(df)
    chr_col = roles.get("chr") or roles.get("chromosome") or roles.get("group")
    pos_col = roles.get("position") or roles.get("pos") or roles.get("x") or (numeric[0] if numeric else None)
    p_col = roles.get("p") or roles.get("pvalue") or roles.get("y") or (numeric[1] if len(numeric) > 1 else None)
    if chr_col not in df.columns or pos_col not in df.columns or p_col not in df.columns:
        ax.text(0.5, 0.5, "Need chr + position + p-value columns",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_title("Manhattan", loc="center", fontweight="bold", pad=5)
        return ax

    p_raw = pd.to_numeric(df[p_col], errors="coerce")
    y = -np.log10(p_raw.clip(lower=1e-300))
    pos = pd.to_numeric(df[pos_col], errors="coerce")
    chr_groups = df[chr_col].astype(str)
    chroms = list(dict.fromkeys(chr_groups.tolist()))
    cum_pos = np.zeros(len(df))
    cum_offsets: list[float] = []
    offset = 0.0
    for chrom in chroms:
        mask = chr_groups == chrom
        chr_pos = pos[mask]
        cum_pos[mask.values] = chr_pos.values + offset
        cum_offsets.append(offset + (chr_pos.max() if not chr_pos.empty else 0))
        offset = cum_offsets[-1]

    for i, chrom in enumerate(chroms):
        mask = chr_groups == chrom
        ax.scatter(cum_pos[mask.values], y[mask.values], s=9,
                   color=colors[i % len(colors)], alpha=0.7, linewidths=0)

    sig = -math.log10(5e-8)
    ax.axhline(sig, color="#CC0000", lw=0.6, ls="--")
    ax.set_xlabel("Chromosomal position (cumulative)")
    ax.set_ylabel("-log10(p)")
    ax.set_title("Manhattan", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("chromosome_coverage")
def gen_chromosome_coverage(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                            rc_params: dict[str, Any], palette: dict[str, Any],
                            col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Coverage/depth track along genomic position, optionally faceted by chromosome."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    pos_col = _first_numeric_valid(df, roles.get("position"), roles.get("x"), numeric[0] if numeric else None)
    cov_col = _first_numeric_valid(
        df,
        roles.get("coverage"),
        roles.get("value"),
        roles.get("y"),
        numeric[1] if len(numeric) > 1 else None,
    )
    chrom_col = _first_valid(df, roles.get("chromosome"), roles.get("group"))
    if pos_col is None or cov_col is None:
        return _fallback_empty(ax, "Chromosome coverage", "Need position + coverage columns")

    work = df[[col for col in (chrom_col, pos_col, cov_col) if col]].copy()
    work[pos_col] = pd.to_numeric(work[pos_col], errors="coerce")
    work[cov_col] = pd.to_numeric(work[cov_col], errors="coerce")
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[pos_col, cov_col])
    if work.empty:
        return _fallback_empty(ax, "Chromosome coverage", "Need finite coverage values")

    if chrom_col and chrom_col in work.columns:
        for i, (name, grp) in enumerate(work.groupby(chrom_col, sort=False)):
            grp = grp.sort_values(pos_col)
            x = grp[pos_col].to_numpy(dtype=float)
            y = grp[cov_col].to_numpy(dtype=float)
            color = colors[i % len(colors)]
            ax.fill_between(x, y, color=color, alpha=0.28, linewidth=0)
            ax.plot(x, y, color=color, lw=0.65, label=str(name))
    else:
        work = work.sort_values(pos_col)
        ax.fill_between(work[pos_col], work[cov_col], color=colors[1 % len(colors)], alpha=0.30, linewidth=0)
        ax.plot(work[pos_col], work[cov_col], color=colors[1 % len(colors)], lw=0.7)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Genomic position")
    ax.set_ylabel("Coverage")
    ax.set_title("Chromosome coverage", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("circos_karyotype")
def gen_circos_karyotype(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                         rc_params: dict[str, Any], palette: dict[str, Any],
                         col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Linear circos-like karyotype tracks for chromosome intervals."""
    ax = _get_ax(ax)
    colors = _categorical_palette(palette)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    chrom_col = _first_valid(df, roles.get("chromosome"), roles.get("group"))
    start_col = _first_numeric_valid(df, roles.get("start"), roles.get("position"), roles.get("x"), numeric[0] if numeric else None)
    end_col = _first_numeric_valid(df, roles.get("end"), numeric[1] if len(numeric) > 1 else None)
    if end_col == start_col:
        end_col = next((col for col in numeric if col != start_col), None)
    value_col = _first_numeric_valid(df, roles.get("value"), roles.get("coverage"), numeric[2] if len(numeric) > 2 else None)
    if value_col in {start_col, end_col}:
        value_col = next((col for col in numeric if col not in {start_col, end_col}), None)
    if chrom_col is None or start_col is None or end_col is None:
        return _fallback_empty(ax, "Circos karyotype", "Need chromosome + start + end columns")

    work = df[_unique_columns(chrom_col, start_col, end_col, value_col)].copy()
    work[start_col] = pd.to_numeric(work[start_col], errors="coerce")
    work[end_col] = pd.to_numeric(work[end_col], errors="coerce")
    if value_col:
        work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[chrom_col, start_col, end_col])
    if work.empty:
        return _fallback_empty(ax, "Circos karyotype", "Need finite interval values")

    chroms = list(dict.fromkeys(work[chrom_col].astype(str).tolist()))[:12]
    vmax = float(work[value_col].abs().max()) if value_col else 1.0
    vmax = vmax if vmax > 0 else 1.0
    for y, chrom in enumerate(chroms):
        grp = work[work[chrom_col].astype(str) == chrom]
        start = float(grp[start_col].min())
        end = float(grp[end_col].max())
        ax.plot([start, end], [y, y], color="#666666", lw=5.0, alpha=0.20, solid_capstyle="round")
        for i, row in grp.iterrows():
            value = float(row[value_col]) if value_col else i + 1
            color = colors[int(abs(value)) % len(colors)] if not value_col else plt.cm.viridis(abs(value) / vmax)
            ax.add_patch(Rectangle((float(row[start_col]), y - 0.22),
                                   max(float(row[end_col]) - float(row[start_col]), 1e-9),
                                   0.44, facecolor=color, edgecolor="white", linewidth=0.25))
    ax.set_yticks(np.arange(len(chroms)), [_short_label(chrom, 10) for chrom in chroms])
    ax.set_xlabel("Genomic position")
    ax.set_title("Circos karyotype", loc="center", fontweight="bold", pad=5)
    ax.invert_yaxis()
    _decorate_axes(ax)
    return ax


@register_chart("gene_structure")
def gen_gene_structure(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                       rc_params: dict[str, Any], palette: dict[str, Any],
                       col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Gene model: exon/CDS/UTR blocks on a genomic backbone with strand arrow."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    categorical = _categorical_columns(df)
    numeric = _numeric_columns(df)
    type_col = _first_valid(df, roles.get("feature_type"), roles.get("group"), categorical[0] if categorical else None)
    start_col = _first_numeric_valid(df, roles.get("start"), roles.get("x"), numeric[0] if numeric else None)
    end_col = _first_numeric_valid(df, roles.get("end"), numeric[1] if len(numeric) > 1 else None)
    if end_col == start_col:
        end_col = next((col for col in numeric if col != start_col), None)
    strand_col = _first_valid(df, roles.get("strand"))
    if type_col is None or start_col is None or end_col is None:
        return _fallback_empty(ax, "Gene structure", "Need feature type + start + end columns")

    work = df[_unique_columns(type_col, start_col, end_col, strand_col)].copy()
    work[start_col] = pd.to_numeric(work[start_col], errors="coerce")
    work[end_col] = pd.to_numeric(work[end_col], errors="coerce")
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[type_col, start_col, end_col])
    if work.empty:
        return _fallback_empty(ax, "Gene structure", "Need finite gene intervals")

    gene_start = float(work[start_col].min())
    gene_end = float(work[end_col].max())
    span = max(gene_end - gene_start, 1.0)
    feature_colors = {
        "exon": "#3B5998",
        "cds": "#1F4E79",
        "5utr": "#F2A541",
        "5'utr": "#F2A541",
        "3utr": "#F2A541",
        "3'utr": "#F2A541",
        "utr": "#F2A541",
        "intron": "#999999",
    }
    ax.plot([gene_start, gene_end], [0, 0], color="#666666", lw=0.8, solid_capstyle="round", zorder=1)
    for _, row in work.iterrows():
        ftype = str(row[type_col]).lower().replace("_", "").strip()
        height = 0.58 if ftype in {"exon", "cds"} else 0.34
        ax.add_patch(Rectangle((float(row[start_col]), -height / 2),
                               max(float(row[end_col]) - float(row[start_col]), span * 0.002),
                               height, facecolor=feature_colors.get(ftype, "#999999"),
                               edgecolor="black", linewidth=0.35, zorder=2))
    strand = "+" if strand_col is None or str(work[strand_col].dropna().iloc[0] if not work[strand_col].dropna().empty else "+") == "+" else "-"
    if strand == "+":
        ax.annotate("", xy=(gene_end, -0.82), xytext=(gene_start, -0.82),
                    arrowprops={"arrowstyle": "->", "lw": 0.65, "color": "#333333"})
    else:
        ax.annotate("", xy=(gene_start, -0.82), xytext=(gene_end, -0.82),
                    arrowprops={"arrowstyle": "->", "lw": 0.65, "color": "#333333"})
    ax.set_xlim(gene_start - span * 0.05, gene_end + span * 0.05)
    ax.set_ylim(-1.12, 0.82)
    ax.set_yticks([])
    ax.set_xlabel("Genomic position")
    ax.set_title("Gene structure", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("enrichment_dotplot")
def gen_enrichment_dotplot(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                           rc_params: dict[str, Any], palette: dict[str, Any],
                           col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Enrichment dotplot: term on y, enrichment score on x, count by bubble size."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    term_col = _first_valid(df, roles.get("label"), roles.get("category"), roles.get("group"), roles.get("gene"), _categorical_columns(df)[0] if _categorical_columns(df) else None)
    score_col = _first_numeric_valid(
        df,
        roles.get("enrichment_score"),
        roles.get("score"),
        roles.get("value"),
        roles.get("fold_change"),
        numeric[0] if numeric else None,
    )
    size_col = _first_numeric_valid(df, roles.get("gene_count"), roles.get("size"), roles.get("weight"), numeric[1] if len(numeric) > 1 else None)
    p_col = _first_numeric_valid(df, roles.get("p_value"), numeric[2] if len(numeric) > 2 else None)
    if term_col is None or score_col is None:
        return _fallback_empty(ax, "Enrichment dotplot", "Need term + enrichment score columns")

    keep = _unique_columns(term_col, score_col, size_col, p_col)
    work = df[keep].copy()
    work[score_col] = pd.to_numeric(work[score_col], errors="coerce")
    if size_col:
        work[size_col] = pd.to_numeric(work[size_col], errors="coerce")
    if p_col:
        work[p_col] = pd.to_numeric(work[p_col], errors="coerce")
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[term_col, score_col])
    if work.empty:
        return _fallback_empty(ax, "Enrichment dotplot", "Need finite enrichment values")
    work = work.sort_values(score_col, ascending=True).tail(20)
    y = np.arange(len(work))
    if size_col:
        raw_sizes = work[size_col].fillna(0).to_numpy(dtype=float)
        span = raw_sizes.max() - raw_sizes.min()
        sizes = 24 + 160 * (raw_sizes - raw_sizes.min()) / (span if span > 0 else 1.0)
    else:
        sizes = np.full(len(work), 54.0)
    if p_col:
        color_values = -np.log10(work[p_col].clip(lower=1e-300).to_numpy(dtype=float))
        scatter = ax.scatter(work[score_col], y, s=sizes, c=color_values, cmap="YlOrRd",
                             edgecolor="white", linewidth=0.35, zorder=3)
        ax.figure.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04, label="-log10(p)")
    else:
        ax.scatter(work[score_col], y, s=sizes, color=_categorical_palette(palette)[1],
                   edgecolor="white", linewidth=0.35, zorder=3)
    ax.axvline(0, color="#777777", lw=0.6, ls="--", zorder=1)
    ax.set_yticks(y, [_short_label(label, 18) for label in work[term_col]])
    ax.set_xlabel("Enrichment score")
    ax.set_title("Enrichment dotplot", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax


@register_chart("oncoprint")
def gen_oncoprint(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                  rc_params: dict[str, Any], palette: dict[str, Any],
                  col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Oncoprint-style gene-by-sample alteration matrix."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    categorical = _categorical_columns(df)
    gene_col = _first_valid(df, roles.get("gene"), roles.get("feature_id"), roles.get("row"), categorical[0] if categorical else None)
    sample_col = _first_valid(df, roles.get("sample"), roles.get("column"), roles.get("identifier"), categorical[1] if len(categorical) > 1 else None)
    alteration_col = _first_valid(df, roles.get("alteration"), roles.get("value"), roles.get("category"), categorical[2] if len(categorical) > 2 else None)
    if gene_col is None or sample_col is None or alteration_col is None:
        return _fallback_empty(ax, "Oncoprint", "Need gene + sample + alteration columns")

    mat = df.pivot_table(index=gene_col, columns=sample_col, values=alteration_col,
                         aggfunc=lambda values: ";".join(sorted(set(map(str, values)))))
    mat = mat.fillna("")
    if mat.empty:
        return _fallback_empty(ax, "Oncoprint", "Need alteration calls")
    gene_order = (mat != "").sum(axis=1).sort_values(ascending=False).index[:30]
    sample_order = (mat.loc[gene_order] != "").sum(axis=0).sort_values(ascending=False).index[:60]
    mat = mat.loc[gene_order, sample_order]
    alteration_types = sorted({token for value in mat.to_numpy().ravel() for token in str(value).split(";")
                               if token not in {"", "0", "nan", "False", "None"}})
    if not alteration_types:
        alteration_types = ["altered"]
    code_map = {alt: i + 1 for i, alt in enumerate(alteration_types)}
    codes = np.zeros(mat.shape, dtype=float)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            tokens = [token for token in str(mat.iat[i, j]).split(";") if token in code_map]
            codes[i, j] = code_map[tokens[0]] if tokens else 0.0
    from matplotlib.colors import BoundaryNorm, ListedColormap
    cmap_colors = ["#F2F2F2"] + _categorical_palette(palette)
    cmap = ListedColormap(cmap_colors[: len(alteration_types) + 1])
    norm = BoundaryNorm(np.arange(-0.5, len(alteration_types) + 1.5), cmap.N)
    ax.imshow(codes, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
    ax.set_yticks(range(mat.shape[0]), [_short_label(label, 14) for label in mat.index])
    ax.set_xticks([])
    ax.set_xlabel(f"Samples (n={mat.shape[1]})")
    ax.set_ylabel("Genes")
    ax.set_title("Oncoprint", loc="center", fontweight="bold", pad=5)
    return ax


@register_chart("lollipop_mutation")
def gen_lollipop_mutation(df: pd.DataFrame, data_profile: Any, chart_plan: Any,
                          rc_params: dict[str, Any], palette: dict[str, Any],
                          col_map: Optional[dict[str, str]] = None, ax: Any = None) -> Any:
    """Mutation lollipop plot: genomic/protein position versus frequency."""
    ax = _get_ax(ax)
    roles = _roles(data_profile)
    numeric = _numeric_columns(df)
    pos_col = _first_numeric_valid(df, roles.get("position"), roles.get("x"), numeric[0] if numeric else None)
    count_col = _first_numeric_valid(df, roles.get("frequency"), roles.get("weight"), roles.get("value"), roles.get("y"), numeric[1] if len(numeric) > 1 else None)
    label_col = _first_valid(df, roles.get("alteration"), roles.get("label"), roles.get("gene"), roles.get("feature_id"))
    if pos_col is None or count_col is None:
        return _fallback_empty(ax, "Lollipop mutation", "Need position + mutation count columns")
    if count_col == pos_col:
        count_col = next((col for col in numeric if col != pos_col), None)
    if count_col is None:
        return _fallback_empty(ax, "Lollipop mutation", "Need position + mutation count columns")
    keep = _unique_columns(pos_col, count_col, label_col)
    work = df[keep].copy()
    work[pos_col] = pd.to_numeric(work[pos_col], errors="coerce")
    work[count_col] = pd.to_numeric(work[count_col], errors="coerce")
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=[pos_col, count_col]).sort_values(pos_col)
    if work.empty:
        return _fallback_empty(ax, "Lollipop mutation", "Need finite mutation positions")
    color = _categorical_palette(palette)[6 % len(_categorical_palette(palette))]
    ax.plot([float(work[pos_col].min()), float(work[pos_col].max())], [0.0, 0.0],
            color="#333333", lw=1.0)
    ax.vlines(work[pos_col], 0, work[count_col], color=color, lw=0.8, alpha=0.75)
    max_count = float(work[count_col].max()) if float(work[count_col].max()) > 0 else 1.0
    ax.scatter(work[pos_col], work[count_col], s=28 + 70 * work[count_col] / max_count,
               color=color, edgecolor="white", linewidth=0.35, zorder=3)
    if label_col:
        for _, row in work.nlargest(min(6, len(work)), count_col).iterrows():
            ax.annotate(_short_label(row[label_col], 12), (row[pos_col], row[count_col]),
                        xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                        fontsize=5, arrowprops={"arrowstyle": "-", "lw": 0.25, "color": "#555555"})
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Position")
    ax.set_ylabel("Mutation frequency")
    ax.set_title("Lollipop mutation", loc="center", fontweight="bold", pad=5)
    _decorate_axes(ax)
    return ax
