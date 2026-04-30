# Technique: Lollipop / Bipolar (ALE & SHAP signed effect)

ALE main-effect lollipops (29/77 cases under `ale_pdp` family) and bipolar SHAP importance (`composite_two_lane`).

**Anchor cases:**
- `期刊复刻：通过双侧棒棒糖图解析特征重要性与ALE主效应方向_1777455283`
- `期刊复刻：多面板结合XGBoost特征重要性棒棒糖图与SHAP蜂群图_1777454599`
- `期刊配图：基于组合多面板条形图对比多条件下的机器学习特征重要性_1777453942`

## Hallmark elements

1. **Stem (line)** from 0 to value; bipolar coloring by sign
2. **Endpoint marker** (filled circle, `s=80`)
3. **Zero reference axvline** (gray dashed)
4. **Bipolar palette**: `#C0504D` positive / `#4F81BD` negative
5. **Sorted by magnitude** descending
6. **Optional bilateral layout**: importance bars on left, ALE direction on right (mirror)

## Reference: Bipolar lollipop

```python
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.family':      ['Arial', 'Times New Roman'],
    'mathtext.fontset': 'stix',
    'font.size':        6.5,
    'axes.linewidth':   1.2,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})

features = ['F1', 'F3', 'F7', 'F2', 'F5', 'F8', 'F4', 'F6']
ale_main = np.array([+0.42, -0.31, +0.28, -0.22, +0.18, +0.12, -0.09, +0.05])

# Sort by magnitude descending
idx = np.argsort(-np.abs(ale_main))
features = [features[i] for i in idx]
ale_main = ale_main[idx]
y_pos = np.arange(len(features))

POS = '#C0504D'
NEG = '#4F81BD'
colors = [POS if v > 0 else NEG for v in ale_main]

fig, ax = plt.subplots(figsize=(7, 5))

# === L0: zero reference ===
ax.axvline(0, color='#888888', linestyle='--', linewidth=1.0, zorder=0)

# === L1: stems ===
ax.hlines(y=y_pos, xmin=0, xmax=ale_main, color=colors,
          linewidth=2.5, zorder=1)

# === L2: endpoint markers ===
ax.scatter(ale_main, y_pos, color=colors, s=90,
           edgecolor='white', linewidth=1.0, zorder=2)

# === Y labels ===
ax.set_yticks(y_pos)
ax.set_yticklabels(features, fontsize=12)
ax.invert_yaxis()                # most important at top
ax.set_xlabel('ALE main effect', fontsize=12)

# === Annotated values ===
for y, v in zip(y_pos, ale_main):
    offset = 0.02 if v > 0 else -0.02
    ha = 'left' if v > 0 else 'right'
    ax.text(v + offset, y, f'{v:+.2f}',
            va='center', ha=ha, fontsize=10,
            color='#222', fontweight='bold')

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.savefig('lollipop_bipolar.pdf', dpi=600, bbox_inches='tight')
```

## Variant: Bilateral (importance + direction)

Left subplot = importance bars (positive only), right subplot = ALE direction lollipop.

```python
fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
ax_imp, ax_dir = axes

# Left: importance bars (gray, sorted)
ax_imp.barh(y_pos, importance, color='#666', alpha=0.7,
            edgecolor='black', linewidth=0.6, zorder=2)
ax_imp.invert_yaxis()
ax_imp.set_xlabel('Importance')
ax_imp.spines['top'].set_visible(False)
ax_imp.spines['right'].set_visible(False)

# Right: ALE bipolar lollipop (same y-order)
ax_dir.axvline(0, color='#888', linestyle='--', linewidth=1.0, zorder=0)
ax_dir.hlines(y=y_pos, xmin=0, xmax=ale_main, color=colors, linewidth=2.5, zorder=1)
ax_dir.scatter(ale_main, y_pos, color=colors, s=80, edgecolor='white',
               linewidth=0.8, zorder=2)
ax_dir.set_xlabel('ALE main effect')
ax_dir.spines['top'].set_visible(False)
ax_dir.spines['right'].set_visible(False)
```

Anchor: `期刊复刻：通过双侧棒棒糖图解析特征重要性与ALE主效应方向`.

## QA contract

- `zeroReferenceCount`: ≥1
- `bipolarPaletteApplied`: True (per-segment color array, not single color)
- `sortedByMagnitudeDesc`: True
- `referenceLineCount`: ≥1 (the zero axvline)
