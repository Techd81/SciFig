# Technique: Heatmap Pairwise (n×n)

8/77 corpus cases. The exhaustive correlation matrix layout — Pearson, Spearman, mutual information, scatter matrix.

**Anchor cases:**
- `期刊复现：Nature同款皮尔逊热力图_1777451326`
- `期刊复现：基于上三角局部填充饼图的相关性矩阵_1777455707`
- `期刊配图：基于机器学习的Spearman相关性热力图与模型预测效果组合分析_1777456565`
- `期刊配图：基于高斯核密度的3x3多面板散点图评估混合水文模型模拟性能_1777453582`

## Hallmark elements

1. **n × n grid** with `hspace=wspace=0.05` (tight)
2. **Diagonal panels**: histogram + KDE
3. **Upper triangle**: correlation number on tinted-by-magnitude background, spines hidden
4. **Lower triangle**: hollow-marker scatter with linear fit
5. **Outer-only labels** (left column + bottom row only)
6. **Significance encoding** when p-values supplied (stars or asterisks)
7. **Diverging cmap** for tinted background: `RdBu_r`

## Reference: Nature-style 5×5 Pearson matrix

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, pearsonr
from matplotlib.gridspec import GridSpec
from matplotlib.colors import TwoSlopeNorm
import matplotlib.cm as cm

# Apply compact kernel
plt.rcParams.update({
    'font.family':      ['Arial', 'Times New Roman', 'DejaVu Sans'],
    'mathtext.fontset': 'stix',
    'font.size':        12,
    'axes.linewidth':   1.2,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})

features = ['F1', 'F2', 'F3', 'F4', 'F5']
n = len(features)
df = pd.DataFrame(np.random.randn(200, n), columns=features)

fig = plt.figure(figsize=(2.4 * n, 2.4 * n))
gs  = GridSpec(n, n, hspace=0.05, wspace=0.05)
PRIMARY = '#3C5488'
norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
cmap = cm.RdBu_r

for i in range(n):
    for j in range(n):
        ax = fig.add_subplot(gs[i, j])
        x  = df[features[j]].values
        y  = df[features[i]].values

        if i == j:
            # Diagonal: hist + KDE
            ax.hist(x, bins=15, density=True, color='white',
                    edgecolor='black', linewidth=0.8, zorder=1)
            kde = gaussian_kde(x)
            xx  = np.linspace(x.min(), x.max(), 200)
            ax.plot(xx, kde(xx), color=PRIMARY, linewidth=1.8, zorder=3)
            ax.set_yticks([])

        elif i < j:
            # Upper triangle: correlation number on tinted bg
            r, p = pearsonr(x, y)
            ax.set_facecolor(cmap(norm(r)))
            stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
            ax.text(0.5, 0.5, f'{r:.2f}{stars}',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, fontweight='bold',
                    color='white' if abs(r) > 0.5 else 'black',
                    zorder=10)
            for s in ax.spines.values():
                s.set_visible(False)
            ax.set_xticks([]); ax.set_yticks([])

        else:
            # Lower triangle: hollow scatter + linear fit
            ax.scatter(x, y, s=12, facecolor='none',
                       edgecolor=PRIMARY, alpha=0.5, linewidth=0.6, zorder=2)
            slope, intercept = np.polyfit(x, y, 1)
            xx = np.linspace(x.min(), x.max(), 100)
            ax.plot(xx, slope * xx + intercept, color='black',
                    linewidth=1.0, zorder=4)

        # Outer-only labels
        if j == 0:
            ax.set_ylabel(features[i], fontsize=12)
        else:
            ax.set_yticklabels([])
        if i == n - 1:
            ax.set_xlabel(features[j], fontsize=12)
        else:
            ax.set_xticklabels([])

# Shared colorbar (outside the matrix)
sm = cm.ScalarMappable(cmap=cmap, norm=norm); sm.set_array([])
cax = fig.add_axes([0.92, 0.30, 0.012, 0.40])
cbar = fig.colorbar(sm, cax=cax)
cbar.set_label('Pearson r', fontsize=11)

plt.savefig('pairwise.pdf', dpi=600, bbox_inches='tight')
```

## Variant: Upper-triangle pie correlation

Replace upper-triangle text with a pie wedge whose angle encodes |r| and color encodes sign.

```python
elif i < j:
    r = pearsonr(x, y)[0]
    angle = abs(r) * 360
    color = cmap(norm(r))
    wedge = plt.matplotlib.patches.Wedge(
        center=(0.5, 0.5), r=0.40,
        theta1=90, theta2=90 + angle,
        facecolor=color, edgecolor='black', linewidth=0.5,
        transform=ax.transAxes, zorder=10)
    ax.add_patch(wedge)
    ax.text(0.5, 0.5, f'{r:.2f}', ha='center', va='center',
            transform=ax.transAxes, fontsize=10, zorder=11)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
```

Anchor: `期刊复现：基于上三角局部填充饼图的相关性矩阵`.

## Discipline rules

- `hspace=wspace=0.05` — must be tight
- Outer-only labels (else clutter)
- Tinted background uses `TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)` — center at 0
- Text color flips to white when |r| > 0.5 (contrast)
- Significance stars only when p-values supplied; never invent
- Lower-triangle markers are **hollow** (`facecolor='none'`) so cells with many points stay readable

## QA contract

- `tightSpacing`: `hspace ≤ 0.10` and `wspace ≤ 0.10`
- `outerOnlyLabels`: True
- `divergingNormCentered`: cmap norm has `vcenter=0`
- `significanceStarsOnlyIfP`: stars present iff p-value column in dataProfile
