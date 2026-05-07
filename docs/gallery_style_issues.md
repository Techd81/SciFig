# Gallery Style Issues — Skill Optimization Spec

21 张 Gallery 图经过人工审查发现的问题汇总，供 skill 优化参考。

---

## 通用规则

以下规则适用于 scifig-generate 生成的所有图表。

### 1. 标题居中

**规则**: 所有 `fig.suptitle()` 和 `ax.set_title()` 默认使用居中对齐。

**当前问题**: 部分图表使用 `loc="left"` 或 `x=0.02, ha="left"` 导致标题左对齐。

**修复方式**:
```python
# suptitle: 使用 x=0.5, ha="center"
fig.suptitle("Title", x=0.5, ha="center", fontsize=10, fontweight="bold")

# ax.set_title: 使用 loc="center" 或省略 loc（默认居中）
ax.set_title("Panel Title", loc="center", fontweight="bold", pad=5)
```

**受影响图表**: covid_national_burden_hero, covid_state_storyboard, covid_parallel_heatmaps, covid_wave_atlas, covid_marginal_coupling, power_load_hero, power_load_atlas, gtex_quality_hero, wine_class_hero

### 2. 底部图例距离与大小

**规则**: 底部共享图例应紧贴绘图区域，字体大小 7pt，带矩形边框。

**当前问题**:
- `fig.subplots_adjust(bottom=0.16~0.24)` 预留过多底部空间，导致图例与绘图区域间距过大
- `enforce_figure_legend_contract` 移动图例到底部后，间距由 `bottom` 值控制
- 图例字体太小（默认 6pt，应为 7pt）

**修复方式**:
```python
# 1. 减小 bottom 边距（单面板 ~0.06-0.08，多面板 ~0.08-0.10）
fig.subplots_adjust(bottom=0.08)  # 而非 0.16~0.24
# 或
fig.tight_layout(rect=[0, 0.06, 1, 0.93])

# 2. 图例参数
fig.legend(handles=handles, loc='lower center', ncol=N,
           bbox_to_anchor=(0.5, 0.01), fontsize=7,
           frameon=True, edgecolor='#cccccc', borderpad=0.4)
```

**受影响图表**: covid_national_burden_hero, covid_state_storyboard, covid_wave_atlas, covid_marginal_coupling, citibike_mobility_spine, gtex_qc_atlas, gtex_quality_hero, power_load_hero, power_load_atlas, wine_class_hero, wine_feature_atlas

### 3. 面板标签位置（A B C D）

**规则**: 面板标签必须位于绘图区域外部（左上方），不能进入数据区域造成重叠。

**当前问题**: 部分图表的 `add_panel_label` 使用 `x=0.08~0.10, y=0.96~1.04`，标签进入绘图区域与数据重叠。

**修复方式**:
```python
# 正确：标签在轴外左上方
ax.text(-0.06, 1.08, label, transform=ax.transAxes,
        fontsize=9, fontweight='bold', va='bottom')

# 错误：标签在轴内
ax.text(0.10, 1.04, label, transform=ax.transAxes, ...)  # x=0.10 在绘图区域内
ax.text(0.08, 0.96, label, transform=ax.transAxes, ...)   # x=0.08, y=0.96 完全在区域内
```

**受影响图表**: citibike_mobility_atlas, exoplanet_candidate_quality, exoplanet_discovery_bias

### 4. 图例统一归纳到底部

**规则**: 所有图例应统一使用一个 `fig.legend()` 放置在底部居中位置，禁止在单个 axes 内放置独立图例。

**当前问题**: 部分图表在 axes 内使用 `ax.legend(loc="upper right")` 或 `ax.legend(loc="upper center")`，未统一到底部。

**修复方式**:
```python
# 错误：在 axes 内放置图例
ax.legend(loc="upper right", frameon=False)

# 正确：收集所有 handles，统一放底部
handles = [...]  # 收集所有图例项
fig.legend(handles=handles, loc='lower center', ncol=N,
           bbox_to_anchor=(0.5, 0.01), fontsize=7,
           frameon=True, edgecolor='#cccccc', borderpad=0.4)
```

**受影响图表**: iris_radar_hero, power_streamgraph_hero

### 5. 图例边框

**规则**: 底部共享图例必须使用矩形边框（`frameon=True`）。

**当前问题**: 部分图表使用 `frameon=False` 或未设置边框。

**修复方式**:
```python
fig.legend(..., frameon=True, edgecolor='#cccccc', borderpad=0.4)
```

**受影响图表**: iris_feature_atlas

### 6. 字体特殊字符渲染

**规则**: 禁止使用 Unicode 特殊字符（如 `⊕`, `₁₀`, `—` em dash），使用 ASCII 替代。字体回退链以 DejaVu Sans 为首选。

**当前问题**: `R⊕`, `M⊕`, `log₁₀`, `—` (em dash) 在部分系统上渲染为方框。

**修复方式**:
```python
# 错误
ax.set_xlabel('Planet Radius (R⊕)')
ax.set_ylabel('Planet Mass (M⊕)')
cb.set_label('log₁₀(cases + 1)')
ax.set_title('... — ...')

# 正确
ax.set_xlabel('Planet Radius (Earth radii)')
ax.set_ylabel('Planet Mass (Earth masses)')
cb.set_label('log10(cases + 1)')
ax.set_title('... - ...')

# rcParams 字体优先
'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
```

**受影响图表**: covid_states_heatmap_hero, exoplanet_bubble_hero

---

## 逐图问题清单

### Single-Panel Hero 图

| 图 | 问题 | 根因 | 修复 |
|---|---|---|---|
| citibike_dotplot_hero | 标题未居中 | `set_title` 缺少 `loc='center'` | 添加 `loc='center'` |
| citibike_mobility_spine | 底部图例距离太大 | `bottom=0.18` 过大 | 改为 `bottom=0.08` |
| covid_national_burden_hero | 标题未居中 + 图例距离太大/太小 | `suptitle ha="left"` + `bottom` 过大 | `x=0.5, ha="center"` + `tight_layout` |
| covid_states_heatmap_hero | 字体方框 | `log₁₀` Unicode 字符 | 改为 `log10` |
| exoplanet_bubble_hero | 字体方框 | `R⊕`, `M⊕` Unicode + `—` em dash | 改为 Earth radii/masses |
| gtex_quality_hero | 图例距离太大/太小 + 标题未居中 | `bottom=0.125` + 标题无 `loc` | `loc='center'` + `bottom=0.06` |
| iris_radar_hero | 图例未归纳到底部 | `ax.legend(loc='upper right')` | 改为 `fig.legend(loc='lower center')` |
| power_load_hero | 标题未居中 + 图例距离太大 | `loc='left'` + `bottom=0.24` | `loc='center'` + `bottom=0.08` |
| power_streamgraph_hero | 图例未归纳到底部 | `ax.legend(loc='upper right')` | 改为 `fig.legend(loc='lower center')` |
| wine_class_hero | 图例距离太大/太小 + 标题未居中 | `bottom=0.20` + 标题无 `loc` | `loc='center'` + `bottom=0.10` |

### Multi-Panel 图

| 图 | 问题 | 根因 | 修复 |
|---|---|---|---|
| citibike_mobility_atlas | ABCD 标签进入绘图区 | `add_panel_label(x=0.08, y=0.96)` | 改为 `x=-0.06, y=1.08` |
| covid_marginal_coupling | 标题未居中 + 图例距离太大 | `suptitle ha="left"` | `x=0.5, ha="center"` + `tight_layout` |
| covid_parallel_heatmaps | 标题未居中 | `suptitle ha="left"` | `x=0.5, ha="center"` |
| covid_state_storyboard | 标题未居中 + 图例距离太大/太小 | `suptitle ha="left"` + `bottom` 过大 | `x=0.5, ha="center"` + `tight_layout` |
| covid_wave_atlas | 标题未居中 + 图例距离太大/太小 | `suptitle ha="left"` | `x=0.5, ha="center"` + `tight_layout` |
| exoplanet_candidate_quality | ABCD 标签进入绘图区 | `add_panel_label(x=0.10, y=1.04)` | 改为 `x=-0.06, y=1.08` |
| exoplanet_discovery_bias | ABCD 标签进入绘图区 | `add_panel_label(x=0.10, y=1.04)` | 改为 `x=-0.06, y=1.08` |
| gtex_qc_atlas | 图例距离太大/太小 | `bottom=0.18` | 改为 `bottom=0.08` |
| iris_feature_atlas | 图例未使用矩形框 | `fig.legend` 缺少 `frameon=True` | 添加 `frameon=True, edgecolor='#cccccc'` |
| power_load_atlas | 标题未居中 + 图例距离太大/太小 | 4 面板 `loc='left'` + `bottom=0.16` | `loc='center'` + `bottom=0.08` |
| wine_feature_atlas | 图例距离太大/太小 | `bottom=0.17` | 改为 `bottom=0.08` |

---

## Skill 需要修改的关键位置

### 1. `helpers.py` — `enforce_figure_legend_contract`

图例移到底部后，应同时：
- 设置 `fontsize=7`（非默认 6）
- 设置 `frameon=True, edgecolor='#cccccc', borderpad=0.4`
- 使用 `bbox_to_anchor=(0.5, 0.01)` 而非更大的 y 值
- 调用后调整 `fig.subplots_adjust(bottom=0.08)` 以消除多余间距

### 2. `template_mining_helpers.py` — `add_panel_label`

面板标签默认位置应改为轴外：
```python
def add_panel_label(ax, label, x=-0.06, y=1.08, fontsize=9):
    ax.text(x, y, label, transform=ax.transAxes,
            fontsize=fontsize, fontweight='bold', va='bottom')
```

### 3. `template_mining_helpers.py` — `apply_journal_kernel`

`fig.suptitle` 的默认位置应改为居中：
```python
# 生成代码中 suptitle 的默认参数
x=0.5, ha="center"  # 而非 x=0.02, ha="left"
```

### 4. 生成代码模板中的 `set_title`

所有 `ax.set_title()` 调用应使用 `loc="center"`：
```python
ax.set_title("...", loc="center", fontweight="bold", pad=5)
```

### 5. 字体回退与特殊字符

- `font.sans-serif` 首选 `DejaVu Sans`
- 禁止生成包含 Unicode 特殊字符的标签（`⊕`, `₁₀`, `—` 等）
- 使用 ASCII 替代：`R⊕` → `Earth radii`, `log₁₀` → `log10`, `—` → `-`

### 6. `save_figure` 中的 `subplots_adjust`

底部边距应根据是否有底部图例动态调整：
- 有底部图例: `bottom=0.06~0.10`
- 无底部图例: `bottom=0.04~0.06`
- 当前值 `bottom=0.16~0.24` 一律过大

---

## rcParams 推荐值

```python
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 6,
    'axes.linewidth': 0.6,
    'axes.labelsize': 7,
    'axes.titlesize': 7.5,
    'axes.titleweight': 'bold',
    'xtick.labelsize': 5.5,
    'ytick.labelsize': 5.5,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.major.size': 3,
    'ytick.major.size': 3,
    'legend.fontsize': 7,          # 关键：7pt 而非 6pt
    'legend.frameon': True,         # 关键：默认带边框
    'legend.edgecolor': '#cccccc',  # 关键：边框颜色
    'legend.borderpad': 0.4,        # 关键：边距
    'axes.grid': False,
    'axes.spines.top': False,
    'axes.spines.right': False,
})
```
