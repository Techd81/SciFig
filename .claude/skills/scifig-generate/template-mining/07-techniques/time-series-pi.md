# Technique: Time Series with Prediction Interval

3/77 corpus cases. Time-series with PI band, train/test split, and observed vs predicted overlay.

**Anchor cases:**
- `期刊图表复现：基于预测区间与训练_测试划分的时序拟合效果对比_1777454854`
- `期刊配图复现 _ Python绘制"趋势+分布"时序混合图_1777451814`

## Hallmark elements

1. **PI band**: `fill_between` translucent (alpha 0.40), sky-blue
2. **Observed dots**: small black, alpha 0.7
3. **Predicted line**: red, thin (lw 1.5), `zorder=3`
4. **Train/test divider**: dashed gray vertical line at split index
5. **Train/test palette**: `#4C78A8` (train) / `#E45756` (test)
6. **In-plot metric box** with R² + RMSE per fold
7. **Optional inset** with residual distribution

## Reference

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    'font.family':      ['Times New Roman', 'Arial'],
    'mathtext.fontset': 'stix',
    'font.size':        6.5,
    'axes.linewidth':   1.5,
    'xtick.direction':  'in',
    'ytick.direction':  'in',
    'savefig.bbox':     'tight',
    'savefig.dpi':      600,
})

# Data
np.random.seed(0)
n = 200
x = np.arange(n)
y_true = 50 + 0.3 * x + 5 * np.sin(x / 10) + np.random.normal(0, 1.5, n)
y_pred = y_true + np.random.normal(0, 1.0, n)
pi_lo  = y_pred - 1.645 * 2.5
pi_hi  = y_pred + 1.645 * 2.5
split = 150  # train/test split

fig, ax = plt.subplots(figsize=(11, 5))

# === L1: 90% PI band ===
ax.fill_between(x, pi_lo, pi_hi, color='skyblue', alpha=0.40,
                linewidth=0, label='90% Prediction Interval', zorder=1)

# === L2: observed dots ===
ax.scatter(x, y_true, color='black', s=12, alpha=0.7,
           label='Actual Observations', zorder=2)

# === L3: predicted line ===
ax.plot(x, y_pred, color='#E45756', linewidth=1.5,
        label='Model Prediction', zorder=3)

# === Train/test divider ===
ax.axvline(x=split, color='gray', linestyle='--', linewidth=1.5,
           alpha=0.7, zorder=4)
ax.text(split / 2, ax.get_ylim()[1] * 0.95, 'Training', ha='center',
        va='top', fontsize=11, color='#4C78A8', fontweight='bold')
ax.text((split + n) / 2, ax.get_ylim()[1] * 0.95, 'Testing', ha='center',
        va='top', fontsize=11, color='#E45756', fontweight='bold')

# === Per-fold metrics ===
def metrics(y, p):
    r2  = 1 - np.sum((y - p)**2) / np.sum((y - y.mean())**2)
    rmse = np.sqrt(np.mean((y - p)**2))
    return r2, rmse

r2_tr, rmse_tr = metrics(y_true[:split], y_pred[:split])
r2_te, rmse_te = metrics(y_true[split:], y_pred[split:])

ax.text(0.02, 0.98, f"Train: $R^2$={r2_tr:.3f}  RMSE={rmse_tr:.2f}\n"
                    f"Test:  $R^2$={r2_te:.3f}  RMSE={rmse_te:.2f}",
        transform=ax.transAxes, va='top', ha='left', fontsize=11,
        family='monospace',
        bbox=dict(boxstyle='square,pad=0.4', fc='white', ec='black', lw=0.8),
        zorder=20)

ax.set_xlabel('Time index')
ax.set_ylabel('Value')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.legend(loc='lower right', frameon=False, fontsize=11)

plt.savefig('time_series_pi.pdf', dpi=600, bbox_inches='tight')
```

## Discipline rules

- PI band alpha 0.40 (more visible than CI band 0.15)
- Observed dots alpha 0.7 with `s=12-15` (small, restraint)
- Predicted line `linewidth=1.5` (thin so band shows through)
- Train/test text at top of panel; never inside the band
- Use **monospace** font in metric box so the numbers align

## Variant: PI band only (no observed dots)

When the user wants pure trend + uncertainty:

```python
ax.fill_between(x, pi_lo, pi_hi, color='skyblue', alpha=0.4, zorder=1)
ax.plot(x, y_pred, color='#E45756', linewidth=2.0, zorder=3)
```

## QA contract

- `intervalBandCount`: ≥1 (`fill_between` with alpha 0.30–0.50)
- `trainTestDividerPresent`: True if train/test split detected in data
- `metricBoxPerFold`: ≥2 metric rows (train + test)
- `referenceLineCount`: ≥1 (the divider)
