"""Genomics-enrichment chart generators (volcano/manhattan/oncoprint/...).

Stage-2 refactor: function bodies are byte-identical to the pre-refactor
runtime generator_sources map. Consumed via _load_generator_source_map()
source-concatenation (not standalone import); shared role/color helpers
live in generators_distribution, classifier-board helpers in generators_ml.
"""


from math import pi as _pi
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colors import TwoSlopeNorm
from matplotlib.gridspec import GridSpecFromSubplotSpec
from matplotlib.patches import Ellipse
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.optimize import curve_fit
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from scipy.stats import gaussian_kde
from scipy.stats import norm
from sklearn.linear_model import LinearRegression
from sklearn.metrics import precision_recall_curve, average_precision_score
from sklearn.metrics import roc_curve, auc
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
from statsmodels.nonparametric.smoothers_lowess import lowess
import math as _math
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
import squarify
import textwrap
import warnings


def gen_chromosome_coverage(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Chromosome-wide coverage/depth plot: line along chromosome position.

    Expects columns: position (genomic coordinate) and coverage (read depth) in
    semanticRoles. Optionally chromosome label for multi-chrom figure.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pos_col = roles.get("position") or roles.get("x")
    cov_col = roles.get("coverage") or roles.get("depth") or roles.get("value")
    chrom_col = roles.get("chromosome") or roles.get("group")

    if pos_col is None or cov_col is None:
        raise ValueError("chromosome_coverage requires 'position' and 'coverage' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 40 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#1F4E79"])[0]

    if chrom_col and chrom_col in df.columns:
        for i, (name, grp) in enumerate(df.groupby(chrom_col)):
            c = palette.get("categorical", ["#1F4E79", "#C8553D"])[i % 2]
            ax.fill_between(grp[pos_col], grp[cov_col], alpha=0.5, color=c, linewidth=0)
            ax.plot(grp[pos_col], grp[cov_col], color=c, lw=0.4, label=str(name))
        ax.legend(frameon=False, fontsize=5, loc="upper right")
    else:
        ax.fill_between(df[pos_col], df[cov_col], alpha=0.4, color=color, linewidth=0)
        ax.plot(df[pos_col], df[cov_col], color=color, lw=0.5)

    ax.set_xlabel("Genomic position (bp)")
    ax.set_ylabel("Coverage depth")
    ax.set_xlim(df[pos_col].min(), df[pos_col].max())
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "chromosome_coverage")
    return ax


def gen_circos_karyotype(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Simplified circos-like karyotype plot (linear chromosomes with colored tracks).

    Expects columns: chromosome, start, end, and optionally track_value and
    track_color in semanticRoles.  Draws horizontal chromosome bands with
    colored overlay tracks simulating a circos layout in linear form.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    chr_col = roles.get("chromosome") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end")
    value_col = roles.get("track_value") or roles.get("value")
    color_col = roles.get("track_color")

    if chr_col is None or start_col is None or end_col is None:
        raise ValueError("circos_karyotype requires 'chromosome', 'start', 'end' in semanticRoles")

    chromosomes = df[chr_col].dropna().unique().tolist()
    n_chr = len(chromosomes)
    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), max(60, 12 * n_chr) * (1 / 25.4)),
                           constrained_layout=True)

    fallback = palette.get("categorical", ["#1F4E79", "#4C956C", "#F2A541",
                                            "#C8553D", "#7A6C8F", "#2B6F77"])
    chr_colors = {c: fallback[i % len(fallback)] for i, c in enumerate(chromosomes)}

    for yi, chrom in enumerate(chromosomes):
        sub = df[df[chr_col] == chrom].sort_values(start_col)
        x_max = sub[end_col].max()
        # Chromosome backbone
        ax.barh(yi, x_max, left=0, height=0.5, color="#E0E0E0",
                edgecolor="black", linewidth=0.4)
        # Colored segments
        for _, row in sub.iterrows():
            seg_color = row[color_col] if color_col and color_col in df.columns \
                else chr_colors[chrom]
            seg_alpha = 0.7
            if value_col and value_col in df.columns:
                seg_alpha = max(0, min(1, 0.3 + 0.7 * min(row[value_col], 1.0)))
            ax.barh(yi, row[end_col] - row[start_col], left=row[start_col],
                    height=0.5, color=seg_color, alpha=seg_alpha, linewidth=0)

    ax.set_yticks(range(n_chr))
    ax.set_yticklabels(chromosomes, fontsize=5)
    ax.set_xlabel("Genomic position")
    ax.set_ylim(-0.5, n_chr - 0.5)
    ax.invert_yaxis()
    ax.spines["left"].set_visible(False)
    if standalone:
        apply_chart_polish(ax, "circos_karyotype")
    return ax


def gen_enrichment_dotplot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Enrichment dotplot: pathway terms vs enrichment score with dot size = gene count."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 78 * (1 / 25.4)), constrained_layout=True)

    roles = dataProfile.get("semanticRoles", {})
    term_col = roles.get("term") or roles.get("pathway") or roles.get("label")
    score_col = roles.get("score") or roles.get("effect") or roles.get("fold_change")
    pval_col = roles.get("p_value")
    size_col = roles.get("size")

    if not term_col or not score_col:
        raise ValueError("enrichment_dotplot requires 'term' and 'score' in semanticRoles")

    # Sort by score
    plot_df = df.sort_values(score_col, ascending=True).head(20)

    y_pos = range(len(plot_df))
    scores = plot_df[score_col].values

    # Dot sizes
    if size_col and size_col in plot_df.columns:
        sizes = plot_df[size_col].values
        sizes = 10 + (sizes - sizes.min()) / (sizes.max() - sizes.min() + 1e-9) * 80
    else:
        sizes = np.full(len(plot_df), 30)

    # Colors from p-value or score
    if pval_col and pval_col in plot_df.columns:
        colors = -np.log10(plot_df[pval_col].values.clip(1e-300))
        sc = ax.scatter(scores, y_pos, s=sizes, c=colors, cmap="YlOrRd", edgecolor="white", lw=0.3, zorder=3)
        plt.colorbar(sc, ax=ax, label="-log10(p)", shrink=0.6, pad=0.02)
    else:
        color = palette.get("categorical", ["#1F4E79"])[0]
        ax.scatter(scores, y_pos, s=sizes, color=color, edgecolor="white", lw=0.3, zorder=3)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([display_label(t, col_map) for t in plot_df[term_col]], fontsize=4.5)
    ax.set_xlabel("Enrichment Score")
    ax.axvline(x=0, color="#999999", lw=0.4, ls="--")
    ax.invert_yaxis()
    if standalone:
        apply_chart_polish(ax, "enrichment_dotplot")
    return ax


def gen_gene_structure(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Gene structure diagram (exons as boxes, introns as lines, UTRs colored).

    Expects columns: feature_type (exon/intron/5utr/3utr/cds), start, end,
    and optionally strand in semanticRoles.  Draws a horizontal gene model
    with exon boxes, intron lines, and colored UTR regions.
    """
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    type_col = roles.get("feature_type") or roles.get("group")
    start_col = roles.get("start") or roles.get("x")
    end_col = roles.get("end")
    strand = roles.get("strand", "+")

    if type_col is None or start_col is None or end_col is None:
        raise ValueError("gene_structure requires 'feature_type', 'start', 'end' in semanticRoles")

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 40 * (1 / 25.4)),
                           constrained_layout=True)

    feature_colors = {
        "exon": "#3B5998", "cds": "#1F4E79",
        "5utr": "#F2A541", "3utr": "#F2A541",
        "intron": "#999999",
    }

    gene_start = df[start_col].min()
    gene_end = df[end_col].max()
    # Intron line at y=0
    ax.plot([gene_start, gene_end], [0, 0], color="#666666", linewidth=0.8,
            solid_capstyle="round", zorder=1)

    for _, row in df.iterrows():
        ftype = str(row[type_col]).lower().strip()
        s, e = row[start_col], row[end_col]
        color = feature_colors.get(ftype, "#999999")
        height = 0.6 if ftype in ("exon", "cds") else 0.4
        box = plt.Rectangle((s, -height / 2), e - s, height,
                             facecolor=color, edgecolor="black",
                             linewidth=0.4, zorder=2)
        ax.add_patch(box)

    # Arrow indicating strand direction
    arrow_y = -0.8
    if strand == "+":
        ax.annotate("", xy=(gene_end, arrow_y), xytext=(gene_start, arrow_y),
                    arrowprops=dict(arrowstyle="->", lw=0.6, color="black"))
    else:
        ax.annotate("", xy=(gene_start, arrow_y), xytext=(gene_end, arrow_y),
                    arrowprops=dict(arrowstyle="->", lw=0.6, color="black"))

    ax.set_xlim(gene_start - (gene_end - gene_start) * 0.05,
                gene_end + (gene_end - gene_start) * 0.05)
    ax.set_ylim(-1.2, 0.8)
    ax.set_xlabel("Genomic position (bp)")
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)

    # Legend for feature types
    present_types = df[type_col].dropna().unique()
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=feature_colors.get(t, "#999999"),
                              edgecolor="black", linewidth=0.4, label=t)
               for t in present_types]
    ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=5, ncol=len(handles))

    if standalone:
        apply_chart_polish(ax, "gene_structure")
    return ax


def gen_lollipop_mutation(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Mutation lollipop plot: protein/genomic position versus mutation frequency."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    pos_col = roles.get("position") or roles.get("aa_position") or roles.get("x")
    count_col = roles.get("count") or roles.get("frequency") or roles.get("value") or roles.get("y")
    label_col = roles.get("label") or roles.get("mutation") or roles.get("feature_id")

    if pos_col is None or count_col is None:
        raise ValueError("lollipop_mutation requires 'position' and 'count'/'frequency' columns")

    plot_df = df[[c for c in [pos_col, count_col, label_col] if c and c in df.columns]].dropna().sort_values(pos_col)
    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 55 * (1 / 25.4)),
                           constrained_layout=True)

    color = palette.get("categorical", ["#C8553D"])[0]
    ax.hlines(0, plot_df[pos_col].min(), plot_df[pos_col].max(), color="#333333", lw=1.0)
    ax.vlines(plot_df[pos_col], 0, plot_df[count_col], color=color, lw=0.8, alpha=0.75)
    sizes = 25 + 40 * (plot_df[count_col] / plot_df[count_col].max())
    ax.scatter(plot_df[pos_col], plot_df[count_col], s=sizes, color=color,
               edgecolor="white", linewidth=0.35, zorder=3)
    if label_col:
        for _, row in plot_df.nlargest(min(8, len(plot_df)), count_col).iterrows():
            ax.annotate(str(row[label_col])[:16], (row[pos_col], row[count_col]),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=4.5,
                        arrowprops=dict(arrowstyle="-", lw=0.25, color="#555555"))
    ax.set_xlabel("Position")
    ax.set_ylabel("Mutation frequency")
    ax.set_ylim(bottom=0)
    if standalone:
        apply_chart_polish(ax, "lollipop_mutation")
    return ax


def gen_ma_plot(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """MA plot: average abundance/intensity versus log2 fold change."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    mean_col = roles.get("mean") or roles.get("baseMean") or roles.get("abundance") or roles.get("x")
    fc_col = roles.get("log2fc") or roles.get("fold_change") or roles.get("effect") or roles.get("y")
    p_col = roles.get("padj") or roles.get("p_value") or roles.get("pvalue")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if mean_col is None and numeric_cols:
        mean_col = numeric_cols[0]
    if fc_col is None and len(numeric_cols) > 1:
        fc_col = numeric_cols[1]
    if mean_col is None or fc_col is None:
        raise ValueError("ma_plot requires mean abundance and log2 fold-change columns")

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 65 * (1 / 25.4)),
                           constrained_layout=True)

    mean_vals = df[mean_col].astype(float).clip(lower=1e-12)
    fc_vals = df[fc_col].astype(float)
    sig = np.zeros(len(df), dtype=bool)
    if p_col and p_col in df.columns:
        sig = df[p_col].astype(float) < 0.05
    sig = sig & (np.abs(fc_vals) >= 1)

    ax.scatter(np.log10(mean_vals[~sig]), fc_vals[~sig], s=9, c="#B8B8B8",
               alpha=0.55, linewidth=0, label=f"NS ({int((~sig).sum())})")
    ax.scatter(np.log10(mean_vals[sig]), fc_vals[sig], s=13, c="#C8553D",
               alpha=0.8, edgecolors="white", linewidth=0.25,
               label=f"Changed ({int(sig.sum())})")
    # Zero baseline (logFC=0) — delegate to template_mining_helpers when reachable
    canonical_zero_ref = globals().get("add_zero_reference")
    if canonical_zero_ref is not None:
        try:
            canonical_zero_ref(ax, axis="y", color="black", lw=0.55, ls="-", zorder=1)
        except Exception:
            ax.axhline(0, color="black", lw=0.55)
    else:
        ax.axhline(0, color="black", lw=0.55)
    ax.axhline(1, color="#777777", lw=0.45, ls="--")
    ax.axhline(-1, color="#777777", lw=0.45, ls="--")
    ax.set_xlabel(f"log10({_display_col(mean_col, col_map)})")
    ax.set_ylabel(_display_col(fc_col, col_map))
    ax.legend(loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "ma_plot")
    return ax


def gen_manhattan(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Manhattan plot for chromosome-position association scans."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    chrom_col = roles.get("chromosome") or roles.get("chr") or roles.get("group")
    pos_col = roles.get("position") or roles.get("x")
    p_col = roles.get("pvalue") or roles.get("p_value") or roles.get("padj") or roles.get("y")

    if chrom_col is None or pos_col is None or p_col is None:
        raise ValueError("manhattan requires chromosome, position, and p-value columns")

    plot_df = df[[chrom_col, pos_col, p_col]].dropna().copy()
    plot_df[p_col] = plot_df[p_col].astype(float).clip(lower=1e-300, upper=1.0)
    chroms = sorted(plot_df[chrom_col].unique(), key=lambda x: str(x))
    offset = 0
    ticks, ticklabels = [], []
    xs = np.zeros(len(plot_df))
    for chrom in chroms:
        idx = plot_df[chrom_col] == chrom
        sub_pos = plot_df.loc[idx, pos_col].astype(float)
        xs[idx.to_numpy()] = sub_pos + offset
        ticks.append(offset + (sub_pos.min() + sub_pos.max()) / 2)
        ticklabels.append(str(chrom))
        offset += sub_pos.max() + max(sub_pos.max() * 0.04, 1)
    plot_df["_x"] = xs
    plot_df["_nlogp"] = -np.log10(plot_df[p_col])

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), 60 * (1 / 25.4)),
                           constrained_layout=True)

    colors = palette.get("categorical", ["#1F4E79", "#C8553D"])
    for i, chrom in enumerate(chroms):
        sub = plot_df[plot_df[chrom_col] == chrom]
        ax.scatter(sub["_x"], sub["_nlogp"], s=6, color=colors[i % len(colors)],
                   alpha=0.72, linewidth=0)
    ax.axhline(-np.log10(5e-8), color="#333333", lw=0.5, ls="--")
    ax.axhline(-np.log10(1e-5), color="#999999", lw=0.45, ls=":")
    ax.set_xticks(ticks)
    ax.set_xticklabels(ticklabels, fontsize=5)
    ax.set_xlabel("Chromosome")
    ax.set_ylabel("-log10(p-value)")
    if standalone:
        apply_chart_polish(ax, "manhattan")
    return ax


def gen_oncoprint(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Oncoprint-style alteration matrix for gene-by-sample mutation calls."""
    standalone = ax is None
    plt.rcParams.update(rcParams)
    roles = dataProfile.get("semanticRoles", {})
    gene_col = roles.get("gene") or roles.get("feature_id") or roles.get("row")
    sample_col = roles.get("sample") or roles.get("subject_id") or roles.get("column")
    alteration_col = roles.get("alteration") or roles.get("mutation") or roles.get("value")

    if gene_col and sample_col and alteration_col:
        mat = df.pivot_table(index=gene_col, columns=sample_col, values=alteration_col,
                             aggfunc=lambda x: ";".join(sorted(set(map(str, x)))))
    else:
        mat = df.copy()
        if gene_col and gene_col in mat.columns:
            mat = mat.set_index(gene_col)

    mat = mat.fillna("")
    genes = list(mat.index)[:40]
    samples = list(mat.columns)[:80]
    mat = mat.loc[genes, samples]
    alteration_types = sorted({str(v) for v in mat.to_numpy().ravel() if str(v) not in ("", "0", "nan", "False")})
    if not alteration_types:
        alteration_types = ["altered"]
    code_map = {alt: i + 1 for i, alt in enumerate(alteration_types)}
    codes = np.zeros(mat.shape, dtype=float)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            value = str(mat.iat[i, j])
            if value in code_map:
                codes[i, j] = code_map[value]
            elif value not in ("", "0", "nan", "False"):
                codes[i, j] = 1

    if standalone:
        fig, ax = plt.subplots(figsize=(183 * (1 / 25.4), max(55, 3 * len(genes)) * (1 / 25.4)),
                           constrained_layout=True)

    cmap_colors = ["#F2F2F2"] + palette.get("categorical", ["#1F4E79", "#C8553D", "#4C956C", "#F2A541"])
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(cmap_colors[:len(alteration_types) + 1])
    norm = BoundaryNorm(np.arange(-0.5, len(alteration_types) + 1.5), cmap.N)
    ax.imshow(codes, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
    ax.set_yticks(range(len(genes)))
    ax.set_yticklabels(genes, fontsize=5)
    ax.set_xticks([])
    ax.set_xlabel(f"Samples (n={len(samples)})")
    ax.set_ylabel("Genes")
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=cmap_colors[i + 1]) for i in range(len(alteration_types))]
    ax.legend(handles, alteration_types, loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "oncoprint")
    return ax


def gen_volcano(df, dataProfile, chartPlan, rcParams, palette, col_map=None, ax=None):
    """Volcano plot: fold-change vs significance with threshold lines."""
    standalone = ax is None
    roles = dataProfile.get("semanticRoles", {})
    fc_col = roles.get("fold_change") or roles.get("x")
    pval_col = roles.get("p_value")
    label_col = roles.get("label_col") or roles.get("feature_id")

    if fc_col is None or pval_col is None:
        raise ValueError("volcano requires 'fold_change' and 'p_value' in semanticRoles")

    df = df.copy()
    df["nlogp"] = -np.log10(df[pval_col].clip(lower=1e-20))
    fc_thresh = 1
    pval_thresh = 0.05

    def _cat(row):
        if row[pval_col] < pval_thresh and row[fc_col] > fc_thresh:
            return "Up"
        elif row[pval_col] < pval_thresh and row[fc_col] < -fc_thresh:
            return "Down"
        return "NS"

    df["cat"] = df.apply(_cat, axis=1)

    if standalone:
        fig, ax = plt.subplots(figsize=(89 * (1 / 25.4), 70 * (1 / 25.4)),
                           constrained_layout=True)

    colors = {"Up": "#D55E00", "Down": "#0072B2", "NS": "#999999"}
    for cat, col in colors.items():
        s = df[df.cat == cat]
        ax.scatter(s[fc_col], s["nlogp"], c=col, s=12, alpha=0.7,
                   linewidth=0.3, edgecolors="white", label=f"{cat} ({len(s)})")

    ax.axhline(-np.log10(pval_thresh), color="black", lw=0.5, ls="--", alpha=0.5)
    ax.axvline(fc_thresh, color="black", lw=0.5, ls="--", alpha=0.5)
    ax.axvline(-fc_thresh, color="black", lw=0.5, ls="--", alpha=0.5)

    if label_col:
        top = df[df.cat != "NS"].nlargest(5, "nlogp")
        for idx, (_, row) in enumerate(top.iterrows()):
            y_off = (idx % 3) * df["nlogp"].max() * 0.04
            ax.annotate(row[label_col], (row[fc_col], row["nlogp"] + y_off),
                        fontsize=4, ha="center", va="bottom",
                        arrowprops=dict(arrowstyle="-", lw=0.3, color="black"))

    ax.set_xlabel("log2(Fold Change)")
    ax.set_ylabel("-log10(adj. p-value)")
    ax.legend(loc="upper right", frameon=False, fontsize=5)
    if standalone:
        apply_chart_polish(ax, "volcano")
    return ax
