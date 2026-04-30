# Technique: SHAP Composite

26/77 corpus cases — the largest family. SHAP composites usually combine **3 sub-views**: importance ranking (top), beeswarm (middle), and dependence/local force (bottom or beside).

**Anchor cases:**
- `期刊配图复现 _ Python绘制多面板SHAP蜂群图_1777452005`
- `复现顶刊 _ 拒绝千篇一律的SHAP图，用Matplotlib手绘一张"蜂群+条形"组合图_1777452577`
- `期刊配图复现 _ 手把手教你用 Python 绘制 SHAP 全局与局部解释组合图_1777452973`
- `期刊复现：组合重要性条形图与SHAP蜂群图解析特征的全局预测贡献_1777454956`
- `期刊复现：基于SHAP复合图揭示高能分子特征对性能的全局与局部影响_1777454774`

## Hallmark elements

1. **Mean |SHAP| importance** as horizontal bars or lollipops (left or top)
2. **Beeswarm**: per-sample SHAP value with points jittered vertically per feature
3. **Color = feature value low→high** via `viridis` (or `RdBu_r` for sign emphasis)
4. **Shared y-feature ordering** across all sub-panels (sorted by mean |SHAP|)
5. **Zero reference line** (vertical) to separate positive/negative contribution
6. **Top-N filter** (typically top 10-15 features)

## Full reference: Bar + Beeswarm composite

```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

# Pre-computed: shap_values (n_samples, n_features), feature_values (same shape),
# feature_names (n_features,). Sort features by mean |SHAP| desc.
mean_abs = np.abs(shap_values).mean(axis=0)
order    = np.argsort(mean_abs)[::-1][:15]   # top 15
feat_top = [feature_names[i] for i in order]
ypos     = np.arange(len(order))             # 0 = top of chart

# === Layout: 1×2 with 30/70 width ===
fig = plt.figure(figsize=(13, 7))
gs  = GridSpec(1, 2, width_ratios=[0.30, 0.70], wspace=0.05)
ax_bar = fig.add_subplot(gs[0, 0])
ax_bee = fig.add_subplot(gs[0, 1], sharey=ax_bar)

# === Left: importance bars ===
ax_bar.barh(ypos, mean_abs[order],
            color='#7E6148', alpha=0.6,
            edgecolor='black', linewidth=0.6, zorder=2)
ax_bar.set_yticks(ypos)
ax_bar.set_yticklabels(feat_top, fontsize=11)
ax_bar.invert_yaxis()                        # top feature at top
ax_bar.set_xlabel('Mean |SHAP|', fontsize=12)
ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)
ax_bar.set_facecolor('#FAFAFA')

# === Right: beeswarm with feature-value coloring ===
ax_bee.axvline(0, color='black', linewidth=1.0, zorder=4)

def jitter(values, width=0.35):
    """Vertical jitter density-aware: more samples → wider spread."""
    rng = np.random.default_rng(42)
    return (rng.random(len(values)) - 0.5) * width

for i, idx in enumerate(order):
    sv = shap_values[:, idx]
    fv = feature_values[:, idx]
    # Normalize feature value to [0, 1] for cmap
    fv_n = (fv - fv.min()) / (fv.max() - fv.min() + 1e-12)
    ax_bee.scatter(sv, np.full(len(sv), i) + jitter(sv),
                   c=fv_n, cmap='RdYlBu_r', s=10, alpha=0.7,
                   edgecolor='white', linewidth=0.2, zorder=5)

ax_bee.set_xlabel('SHAP value (impact on prediction)', fontsize=12)
ax_bee.tick_params(labelleft=False)
ax_bee.spines['top'].set_visible(False)
ax_bee.spines['right'].set_visible(False)

# === Shared color bar for feature value ===
sm = plt.cm.ScalarMappable(cmap='RdYlBu_r',
                           norm=plt.Normalize(vmin=0, vmax=1))
sm.set_array([])
cax = fig.add_axes([0.93, 0.20, 0.012, 0.60])
cbar = fig.colorbar(sm, cax=cax)
cbar.set_label('Feature value', fontsize=11, rotation=270, labelpad=15)
cbar.set_ticks([0, 1]); cbar.set_ticklabels(['Low', 'High'])

plt.tight_layout(rect=[0, 0, 0.92, 1])
plt.savefig('shap_composite.pdf', dpi=600, bbox_inches='tight')
```

## Variant: SHAP + Pie / SHAP + Donut (global contribution share)

When the user wants total-contribution share alongside beeswarm:

```python
# Top-3 importance share + 'other' aggregated
top3 = mean_abs[order[:3]]
other = mean_abs[order[3:]].sum()
share = np.append(top3, other)
labels = feat_top[:3] + ['Others']

ax_pie.pie(share, labels=labels, colors=['#E64B35', '#4DBBD5', '#00A087', '#7F7F7F'],
           wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2),
           startangle=90, textprops={'fontsize': 10})
```

Anchor: `期刊复现：组合SHAP摘要图与饼图解析分子特征对自由基反应预测的全局影响`, `期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化`.

## Variant: 上三下二 (top-wide + 2 below) — SHAP global+local hero

```python
fig = plt.figure(figsize=(11, 9))
gs  = GridSpec(2, 2, height_ratios=[1, 1], hspace=0.35, wspace=0.25)
ax_top = fig.add_subplot(gs[0, :])   # full-width: global importance bars
ax_bl  = fig.add_subplot(gs[1, 0])   # bottom-left: beeswarm (top 10 features)
ax_br  = fig.add_subplot(gs[1, 1])   # bottom-right: dependence plot for #1 feature
```

Anchor: `期刊复现：基于SHAP复合图揭示高能分子特征对性能的全局与局部影响`.

## Variant: 6-panel SHAP dependence grid (ALE-style)

For each top-6 feature: SHAP value vs feature value, colored by interaction feature:

```python
fig = plt.figure(figsize=(15, 9))
gs  = GridSpec(2, 3, hspace=0.35, wspace=0.25)

for k, feat_idx in enumerate(order[:6]):
    ax = fig.add_subplot(gs[k // 3, k % 3])
    fv = feature_values[:, feat_idx]
    sv = shap_values[:, feat_idx]
    # color by the strongest interaction feature
    interact_idx = strongest_interaction[feat_idx]
    iv = feature_values[:, interact_idx]
    iv_n = (iv - iv.min()) / (iv.max() - iv.min() + 1e-12)
    ax.scatter(fv, sv, c=iv_n, cmap='viridis', s=15, alpha=0.7,
               edgecolor='white', linewidth=0.2, zorder=4)
    ax.axhline(0, color='black', linewidth=1.0, zorder=3)
    ax.set_title(feature_names[feat_idx], fontsize=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
```

Anchor: `期刊图表复现：多面板SHAP依赖图展示分子特征对自由基反应速率的非线性影响`.

Executable mapping: `scatter_regression` switches into SHAP dependence mode when the data carries `feature_value` + `shap_value` plus optional `interaction_value`. It must draw the zero contribution line, feature-value color encoding, a compact effect summary, and an outside colorbar only for standalone figures so composite panels stay render-QA safe.

## Discipline rules (universal across the 26 cases)

| Rule | Why |
|---|---|
| Sort features by mean |SHAP| descending; ALL sub-panels share that order | Reader's eye tracks one ranking |
| `cmap='RdYlBu_r'` or `'viridis'` for feature value | Cool-low to warm-high is universal |
| `axvline(0)` at SHAP=0 with `linewidth=1.0` | Sign separator |
| Marker `edgecolor='white', linewidth=0.2` | Crispness on dense beeswarm |
| Top-N filter typically 10-15 | Anything more is unreadable |
| Alpha 0.7 on scatter | Density visible, individual points still legible |
| Color bar labeled "Feature value" with Low / High ticks only | Not 0-1 numbers |

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Different feature order across panels | Sort once, share via `sharey=ax_bar` |
| Showing all 100 features | Top-15 max; rest collapsed to "Others" in pie variant |
| Using rainbow cmap for feature value | Use `RdYlBu_r` (diverging) or `viridis` (sequential) |
| Forgetting zero line | Sign of contribution becomes ambiguous |
| Color bar inside data area | Always outside the data rectangle, dedicated `add_axes` |

## QA contract

Phase 4 render-qa requires for SHAP composite:
- `sharedFeatureOrdering`: y-axis order identical across all sub-panels
- `zeroReferenceCount`: ≥1 (the `axvline(0)`)
- `colorbarLabelPresent`: 'Feature value' or equivalent
- `topFeatureLimit`: ≤15 (else readability fails)
- `featureValueColorEncoded`: scatter has `c=` parameter
