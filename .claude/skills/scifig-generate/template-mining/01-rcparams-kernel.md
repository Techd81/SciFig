# 顶刊审美内核 (rcParams Kernel)

The single biggest "顶刊感" multiplier. **64/77** of the reference cases declare a near-identical `rcParams` block before any plotting. This file is the canonical version of that block plus its variants.

## The Kernel (canonical)

```python
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

plt.rcParams.update({
    # --- Typography ---
    'font.family':      ['Times New Roman', 'Arial', 'DejaVu Sans'],
    'mathtext.fontset': 'stix',          # LaTeX-like math
    'font.size':        14,              # body baseline; bump to 16 for sparse panels

    # --- Axes ---
    'axes.linewidth':   1.2,             # 1.2 for n×n compact, 1.5 for hero panels

    # --- Ticks ---
    'xtick.direction':  'in',            # universal — 77/77
    'ytick.direction':  'in',            # universal — 77/77
    'xtick.major.width': 1.0,
    'ytick.major.width': 1.0,

    # --- Lines ---
    'lines.linewidth':  1.5,
    'lines.markersize': 6,

    # --- Save ---
    'savefig.bbox':     'tight',         # auto-trim margins
    'savefig.dpi':      600,             # journal print
})
```

This kernel is the **default starting point** for every Phase 3 code generation. Variations below override only what's necessary.

## Variant A — Hero / single-panel (font 16, axes 1.5)

Use when: 1 panel, ample whitespace, headline figure (e.g. radar, single scatter).
Source cases: case Nature radar, GAM scatter+residual, forest plot, mirror radial, dual-axis combo.

```python
plt.rcParams.update({
    'font.family':      ['Times New Roman', 'Arial', 'SimHei'],
    'mathtext.fontset': 'stix',
    'font.size':        16,
    'axes.linewidth':   1.5,
    'lines.linewidth':  2.0,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})
```

## Variant B — Compact / n×n grid (font 14, axes 1.2)

Use when: 2×2 / 3×3 / pairwise grid; visual budget is tight.
Source cases: Nature Pearson n×n, SHAP 上三下二, gradient box 2×2, density scatter 4-panel.

```python
plt.rcParams.update({
    'font.family':      ['Arial', 'Times New Roman', 'DejaVu Sans'],
    'mathtext.fontset': 'stix',
    'font.size':        14,
    'axes.linewidth':   1.2,
    'lines.linewidth':  1.5,
    'lines.markersize': 6,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})
```

## Variant C — Polar / radar (no Times New Roman fallback shrink)

Use when: Polar coordinate plots (radar, mirror radial, biodiversity radar).
Polar plots already have heavy spine logic; keep typography clean.

```python
plt.rcParams.update({
    'font.family':       ['Times New Roman', 'Arial', 'DejaVu Sans'],
    'mathtext.fontset':  'stix',
    'font.size':         16,
    'axes.linewidth':    1.5,
    'xtick.direction':   'in',
    'ytick.direction':   'in',
    'grid.linestyle':    '--',
    'grid.alpha':        0.5,            # softer grid for polar
    'savefig.bbox':      'tight',
    'savefig.dpi':       600,
})
```

## Helpers Contract

`phases/code-gen/helpers.py` exposes the kernel as a single function. Phase 3 code generators MUST call it before constructing any figure.

```python
def apply_journal_kernel(variant: str = "default", journalProfile: dict | None = None) -> None:
    """Apply the kernel rcParams. Variants: 'default' | 'hero' | 'compact' | 'polar'.
    If journalProfile is provided, font_family / font_size / axes_linewidth from the
    profile override the variant defaults so journal-specific tokens win.
    """
```

Behavioural rules:

1. **Variant is always required**. No silent fallback to matplotlib defaults.
2. **journalProfile fields take precedence** for `font_family`, `font_size_body_pt`, `axis_linewidth_pt` — this is what binds the kernel to the chosen Nature/Cell/Lancet/etc profile.
3. **Never call `plt.rcParams.update` directly** in chart generators after this — they should rely on the kernel.
4. **Always keep `tick.direction='in'`**. Even if the user requests "presentation style", keep it; this single token is what makes a figure read as journal-grade.

## Anti-patterns from non-顶刊 figures

These patterns appear in tutorial/blog code but are **absent** from all 77 reference cases. Phase 3 code review should flag them.

| Anti-pattern | Why bad | Replace with |
|--------------|---------|--------------|
| `plt.style.use('seaborn-v0_8-darkgrid')` | dark grid is presentation-style, not journal | the kernel above |
| `tick.direction='out'` (matplotlib default) | reads as "Excel chart" | `tick.direction='in'` |
| Default sans-serif font | fails review at editorial typesetting | `Times New Roman / Arial` stack |
| `dpi=300` for raster export | borderline for double-column print | `dpi=600` |
| Unset `savefig.bbox` | wastes whitespace, breaks layout in PDFs | `savefig.bbox='tight'` |
| `lines.linewidth=1.0` (default) | spaghetti at print scale | 1.5 default, 2.0 hero |

## Source Anchors

The variants and rule frequencies are derived from frequency analysis of the 77 cases under `template/articles/`. Specific anchor cases:

- Variant A (hero): `绝美！Nature 这张雷达图`, `复现 Nature _ Python 绘制广义相加模型`, `Python科研绘图复现_绘制多面板分组森林图`.
- Variant B (compact): `期刊复现：Nature同款皮尔逊热力图`, `期刊配图复现 _ Python绘制多面板SHAP蜂群图`, `顶刊审美 _ 用 Python 绘制带"垂直渐变特效"的组合箱线图`.
- Variant C (polar): `期刊复现 _ Python绘制"镜像玫瑰"组合图`, `绝美！Nature 这张雷达图`.

Frequency counts are from `grep` over the corpus on 2026-04-30. Re-run `_extraction/build_case_index.py` to refresh.
