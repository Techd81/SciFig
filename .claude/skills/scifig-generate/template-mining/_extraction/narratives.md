# Template Mining — Per-Case Narrative & Trick Digest

Source: 77 cases.  Re-run `enrich.py` after `extract.py` to refresh.

## Narrative arc distribution

| Arc | Cases | % |
|---|---|---|
| `multipanel_grid` | 26 | 34% |
| `single_focus` | 18 | 23% |
| `global_local` | 5 | 6% |
| `n×n_pairwise` | 5 | 6% |
| `marginal_joint` | 4 | 5% |
| `train_test_diagnostic` | 4 | 5% |
| `composite_two_lane` | 4 | 5% |
| `mirror_compare` | 4 | 5% |
| `hero` | 4 | 5% |
| `inset_overlay` | 3 | 4% |

## Signature-trick frequency (regex over code)

| Trick | Cases |
|---|---|
| `alpha_layered_scatter` | 24 |
| `group_divider_axvline` | 14 |
| `density_color_scatter` | 14 |
| `raincloud_combo` | 13 |
| `metric_text_box` | 9 |
| `axes_inset_overlay` | 8 |
| `dotted_zero_axhline` | 8 |
| `pvalue_stars_overlay` | 7 |
| `colored_marker_edge` | 7 |
| `twin_axes_color_spines` | 6 |
| `error_band_fill_between` | 5 |
| `marginal_axes_grid` | 5 |
| `category_split_dashed` | 4 |
| `dual_y_bar_line` | 4 |
| `imshow_gradient_box` | 4 |
| `ridgeline_offset_kde` | 2 |
| `upper_triangle_split` | 2 |
| `perfect_fit_diagonal` | 2 |
| `polygon_polar_grid` | 2 |
| `regression_band_fillbtw` | 1 |
| `bezier_smooth_line` | 1 |
| `shaded_zone_axvspan` | 1 |
| `diverging_cell_label` | 1 |
| `polar_value_marker` | 1 |

## Per-case digest (grouped by narrative arc)


### Narrative arc: `multipanel_grid` (26 cases)

- **1777452771** `Python复现顶刊CEJ `
  - family: scatter_regression | grid: [2, 3] | palette: #00CED1,#FF0000,#1E90FF
  - tricks: —
- **1777453520** `Python科研绘图复现`
  - family: forest,scatter_regression | grid: [1, 4] | palette: #8DA0CB,#FC8D62,#66C2A5
  - tricks: group_divider_axvline,ridgeline_offset_kde,category_split_dashed
- **1777461729** `基于PSO多目标优化与SHAP可解释分析的回归预测模型框架`
  - family: radar,shap_composite,heatmap_pairwise | grid: — | palette: —
  - tricks: —
- **1777451702** `如何用Python绘制教科书级的双Y轴组合图`
  - family: dual_axis,ale_pdp | grid: — | palette: #CFE2F3,#9BC2E6,#F48E66
  - tricks: twin_axes_color_spines,group_divider_axvline,bezier_smooth_line,dual_y_bar_line,category_split_dashed
- **1777451272** `拒绝默认配色：Python 绘制多模型性能对比图的进阶实战`
  - family: forest,shap_composite,scatter_regression | grid: — | palette: #E64B35,#4DBBD5,#00A087,#3C5488
  - tricks: group_divider_axvline,category_split_dashed
- **1777454691** `期刊图表复现：多面板SHAP依赖图展示分子特征对自由基反应速率的非线性影响`
  - family: shap_composite,scatter_regression,ale_pdp | grid: [2, 3] | palette: #FFCCCC,#CCE5FF
  - tricks: shaded_zone_axvspan,dotted_zero_axhline,alpha_layered_scatter
- **1777454475** `期刊图表复现：多面板SHAP依赖图解析特征主效应与交互作用`
  - family: shap_composite,scatter_regression,density_scatter | grid: — | palette: —
  - tricks: pvalue_stars_overlay,dotted_zero_axhline,alpha_layered_scatter
- **1777454431** `期刊图表：双Y轴直方图与累积频率曲线展示HPC数据集多变量分布特征`
  - family: scatter_regression,dual_axis,nmds_pca | grid: [3, 3] | palette: —
  - tricks: twin_axes_color_spines
- **1777450693** `期刊复现：Nature Comms 双Y轴组合图`
  - family: dual_axis | grid: — | palette: #E6553A
  - tricks: twin_axes_color_spines,dual_y_bar_line
- **1777455934** `期刊复现：双Y轴分组柱状与折线组合图评估多模型预测性能`
  - family: scatter_regression,dual_axis | grid: — | palette: #4B74B2,#F08A5D,#2CA02C
  - tricks: twin_axes_color_spines,dual_y_bar_line
- **1777456015** `期刊复现：双面板组合图展示特征重要性权重与模型性能演变`
  - family: scatter_regression,dual_axis | grid: [2, 1] | palette: #D62728,#1F77B4
  - tricks: —
- **1777455596** `期刊复现：基于多面板组合的SHAP依赖图解析特征对模型预测的非线性影响`
  - family: shap_composite,scatter_regression,ale_pdp | grid: [3, 2] | palette: —
  - tricks: marginal_axes_grid,dotted_zero_axhline,alpha_layered_scatter
- **1777455863** `期刊复现：多面板回归预测散点图对比不同模型真实与预测偏差`
  - family: forest,scatter_regression | grid: [2, 3] | palette: —
  - tricks: metric_text_box,alpha_layered_scatter
- **1777455897** `期刊复现：多面板回归预测散点图对比不同模型真实与预测偏差`
  - family: scatter_regression,time_series_pi | grid: [2, 1] | palette: —
  - tricks: dotted_zero_axhline,alpha_layered_scatter
- **1777455635** `期刊复现：多面板箱线图对比多模型不同评估指标的误差分布`
  - family: scatter_regression,box,ale_pdp | grid: [1, 3] | palette: #4A90E2,#F5A623
  - tricks: —
- **1777454251** `期刊复现：通过多子图布局对比城市化梯度对气体排放量的非线性影响`
  - family: scatter_regression,box,ale_pdp | grid: [1, 2] | palette: #4C72B0,#DD8452
  - tricks: —
- **1777454562** `期刊复现：通过多面板SHAP依赖图解析特征对转化率的主效应与交互作用`
  - family: shap_composite,scatter_regression,ale_pdp | grid: [2, 2] | palette: —
  - tricks: dotted_zero_axhline
- **1777451488** `期刊配图复现 `
  - family: dual_axis | grid: [2, 6] | palette: #D3D3D3,#E67E22,#27AE60
  - tricks: twin_axes_color_spines,colored_marker_edge,dual_y_bar_line
- **1777452639** `期刊配图复现 `
  - family: heatmap | grid: — | palette: —
  - tricks: diverging_cell_label
- **1777452005** `期刊配图复现 `
  - family: shap_composite,ale_pdp | grid: [2, 6] | palette: —
  - tricks: density_color_scatter,twin_axes_color_spines,pvalue_stars_overlay,marginal_axes_grid,raincloud_combo,colored_marker_edge
- **1777454521** `期刊配图：利用多面板2D-PDP揭示机器学习模型的双变量交互与控制边界`
  - family: forest,shap_composite,scatter_regression | grid: [2, 2] | palette: —
  - tricks: density_color_scatter
- **1777455972** `期刊配图：基于NSGA-II的三维帕累托前沿散点图可视化多目标权衡解`
  - family: pareto | grid: — | palette: —
  - tricks: density_color_scatter
- **1777454388** `期刊配图：基于极坐标系的多面板雷达图对比多维环境变量与模型表现`
  - family: radar | grid: — | palette: #1F77B4,#FF7F0E
  - tricks: —
- **1777453942** `期刊配图：基于组合多面板条形图对比多条件下的机器学习特征重要性`
  - family: scatter_regression | grid: [2, 2] | palette: #FFB74D,#2B0E68,#D26E17,#466B6C
  - tricks: —
- **1777456052** `期刊配图：多面板预测散点与SHAP局部依赖特征解释组合图`
  - family: forest,shap_composite,scatter_regression | grid: [2, 2] | palette: —
  - tricks: perfect_fit_diagonal,metric_text_box,alpha_layered_scatter
- **1777458801** `机器学习：集PSO多目标优化与SHAP的回归预测模型`
  - family: radar,forest,shap_composite | grid: — | palette: —
  - tricks: —

### Narrative arc: `single_focus` (18 cases)

- **1777452458** `Python 科研绘图：如何优雅地展示“模型精度+稳定性”？顶刊可视化复盘`
  - family: forest,scatter_regression,marginal_joint | grid: [2, 3] | palette: #EE6677,#4477AA
  - tricks: group_divider_axvline,alpha_layered_scatter
- **1777452391** `Python科研绘图：一行代码实现 R² + 95% 置信区间的高级散点图`
  - family: scatter_regression | grid: — | palette: #313695,#A50026
  - tricks: metric_text_box,alpha_layered_scatter
- **1777451587** `如何用 Python 完美复刻一张“红蓝气泡”相关性分析图`
  - family: heatmap_pairwise,heatmap | grid: — | palette: #8ECFC9,#FFFFFF,#FA7F6F,#F0F0F0
  - tricks: —
- **1777455232** `期刊图表复现：偏最小二乘路径模型揭示变量间因果与总效应`
  - family: scatter_regression,nmds_pca,ale_pdp | grid: — | palette: —
  - tricks: axes_inset_overlay,metric_text_box,group_divider_axvline,category_split_dashed
- **1777455816** `期刊图表复现：叠加二维核密度的渗透汽化膜性能预测对比图`
  - family: scatter_regression,density_scatter | grid: [1, 2] | palette: —
  - tricks: density_color_scatter,metric_text_box,alpha_layered_scatter
- **1777454034** `期刊复现：SHAP依赖图解析环境因子对目标变量的影响方向与程度`
  - family: shap_composite,scatter_regression,ale_pdp | grid: — | palette: #808080
  - tricks: group_divider_axvline,raincloud_combo
- **1777455105** `期刊复现：SHAP蜂群图解析环境因子对目标变量的影响方向与程度`
  - family: shap_composite,scatter_regression,ale_pdp | grid: — | palette: #808080
  - tricks: group_divider_axvline,raincloud_combo
- **1777456122** `期刊复现：利用组合式箱线折线图与气泡热力图可视化模型超参数稳定性`
  - family: heatmap,scatter_regression,box | grid: [2, 2] | palette: —
  - tricks: density_color_scatter,alpha_layered_scatter
- **1777453986** `期刊复现：双面板NMDS散点图通过颜色分组评估水质期群落差异`
  - family: scatter_regression,dual_axis,nmds_pca | grid: [1, 2] | palette: —
  - tricks: —
- **1777455674** `期刊复现：基于H-statistic的特征交互重要性与二维等高线依赖图解析`
  - family: heatmap,scatter_regression,ale_pdp | grid: [3, 2] | palette: #4A708B
  - tricks: density_color_scatter,alpha_layered_scatter
- **1777454077** `期刊复现：基于RF-XGB的SHAP部分依赖图解析关键参数阈值`
  - family: shap_composite,scatter_regression,ale_pdp | grid: [1, 3] | palette: #1F77B4
  - tricks: density_color_scatter,dotted_zero_axhline,alpha_layered_scatter
- **1777451762** `期刊配图优化：Python绘制“双面板PCA得分图”，优雅展示多配方综合评价`
  - family: dual_axis,nmds_pca | grid: — | palette: —
  - tricks: —
- **1777451814** `期刊配图复现 `
  - family: scatter_regression,time_series_pi,box | grid: [2, 4] | palette: —
  - tricks: error_band_fill_between
- **1777452713** `期刊配图复现 `
  - family: scatter_regression | grid: — | palette: #D62728,#1F77B4
  - tricks: —
- **1777454339** `期刊配图：云雨图结合半小提琴与抖动散点展示不同城市化水平的通量差异`
  - family: scatter_regression,violin,raincloud | grid: [1, 2] | palette: —
  - tricks: raincloud_combo,colored_marker_edge
- **1777454120** `期刊配图：基于线性拟合与误差带的距离衰减散点图解析群落空间演变`
  - family: scatter_regression,density_scatter | grid: — | palette: #D62728,#1F77B4
  - tricks: error_band_fill_between
- **1777451428** `顶刊审美 `
  - family: scatter_regression,gradient_box,box | grid: — | palette: #E0E0E0,#F06292,#C2185B
  - tricks: imshow_gradient_box,raincloud_combo,alpha_layered_scatter
- **1777451193** `高级感！Python复刻Cell顶刊散点柱状图`
  - family: — | grid: — | palette: —
  - tricks: raincloud_combo

### Narrative arc: `global_local` (5 cases)

- **1777454644** `期刊图表复现：组合SHAP摘要图与饼图解析分子特征对自由基反应预测的全局影响`
  - family: shap_composite,scatter_regression,treemap_pie | grid: [2, 3] | palette: #4C72B0
  - tricks: —
- **1777454774** `期刊复现：基于SHAP复合图揭示高能分子特征对性能的全局与局部影响`
  - family: shap_composite,scatter_regression | grid: [2, 2] | palette: #4B74B2
  - tricks: axes_inset_overlay,group_divider_axvline,raincloud_combo
- **1777454297** `期刊复现：子图平铺展示比表面积与孔容的全局SHAP值与关键特征排行`
  - family: shap_composite,scatter_regression | grid: [1, 3] | palette: —
  - tricks: —
- **1777454956** `期刊复现：组合重要性条形图与SHAP蜂群图解析特征的全局预测贡献`
  - family: shap_composite,scatter_regression,dual_axis | grid: [1, 2] | palette: —
  - tricks: pvalue_stars_overlay,marginal_axes_grid
- **1777452973** `期刊配图复现 `
  - family: shap_composite,scatter_regression,dual_axis | grid: [1, 3] | palette: #1F77B4
  - tricks: group_divider_axvline,raincloud_combo,alpha_layered_scatter

### Narrative arc: `n×n_pairwise` (5 cases)

- **1777451326** `期刊复现：Nature同款皮尔逊热力图`
  - family: heatmap_pairwise,heatmap | grid: — | palette: —
  - tricks: density_color_scatter,upper_triangle_split
- **1777454813** `期刊复现：多变量散点图矩阵解析特征与比冲的相关性`
  - family: — | grid: [2, 3] | palette: #1F77B4
  - tricks: colored_marker_edge,alpha_layered_scatter
- **1777452095** `期刊配图复现：如何用Python绘制多模型评估密度散点图矩阵`
  - family: scatter_regression,density_scatter | grid: [3, 6] | palette: #D62728,#1F77B4
  - tricks: density_color_scatter,alpha_layered_scatter
- **1777456565** `期刊配图：基于机器学习的Spearman相关性热力图与模型预测效果组合分析`
  - family: forest,shap_composite,heatmap_pairwise | grid: — | palette: —
  - tricks: axes_inset_overlay,pvalue_stars_overlay
- **1777453582** `期刊配图：基于高斯核密度的3x3多面板散点图评估混合水文模型模拟性能`
  - family: scatter_regression,density_scatter | grid: [3, 3] | palette: #D62728
  - tricks: density_color_scatter,marginal_axes_grid

### Narrative arc: `marginal_joint` (4 cases)

- **1777453032** `Python绘图实战：基于GridSpec构建多面板回归预测与边缘分布组合图`
  - family: scatter_regression,marginal_joint | grid: — | palette: #D62728,#1F77B4
  - tricks: metric_text_box
- **1777452838** `复现 CEJ 顶刊神图 `
  - family: scatter_regression,marginal_joint,density_scatter | grid: — | palette: #69B3A2
  - tricks: density_color_scatter,metric_text_box
- **1777454914** `期刊复现：联合等高线热图与边缘分布图验证模型预测精度与参数寻优`
  - family: heatmap,scatter_regression,dual_axis | grid: [4, 8] | palette: —
  - tricks: density_color_scatter,metric_text_box
- **1777454731** `期刊复现：通过带边缘密度的联合残差图全面评估预测模型性能`
  - family: scatter_regression,marginal_joint | grid: [3, 2] | palette: #1F77B4,#FF7F0E
  - tricks: perfect_fit_diagonal,metric_text_box,dotted_zero_axhline,alpha_layered_scatter

### Narrative arc: `train_test_diagnostic` (4 cases)

- **1777452515** `复现 Nature `
  - family: shap_composite,scatter_regression,dual_axis | grid: [1, 2] | palette: #B0B0B0,#5FA896,#FBC15E
  - tricks: error_band_fill_between,alpha_layered_scatter,regression_band_fillbtw
- **1777454854** `期刊图表复现：基于预测区间与训练`
  - family: scatter_regression,time_series_pi | grid: — | palette: —
  - tricks: group_divider_axvline,error_band_fill_between,alpha_layered_scatter
- **1777456338** `期刊复现：基于梯度提升树(GBDT)的多面板预测误差评估图`
  - family: scatter_regression,dual_axis,box | grid: — | palette: #0072B2
  - tricks: raincloud_combo
- **1777456409** `期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱`
  - family: forest,scatter_regression | grid: — | palette: #9BCBEB,#F6CFA3,#9BD28C,#FA9875
  - tricks: dotted_zero_axhline

### Narrative arc: `composite_two_lane` (4 cases)

- **1777452577** `复现顶刊 `
  - family: shap_composite,dual_axis,treemap_pie | grid: [1, 4] | palette: —
  - tricks: density_color_scatter,axes_inset_overlay,pvalue_stars_overlay,raincloud_combo,alpha_layered_scatter
- **1777454599** `期刊复刻：多面板结合XGBoost特征重要性棒棒糖图与SHAP蜂群图`
  - family: shap_composite,scatter_regression,dual_axis | grid: [1, 2] | palette: —
  - tricks: group_divider_axvline
- **1777456510** `期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化`
  - family: forest,shap_composite,scatter_regression | grid: — | palette: #D6EAF8,#5A9BBF
  - tricks: imshow_gradient_box,pvalue_stars_overlay,colored_marker_edge
- **1777456159** `期刊配图：基于GS-XGBoost与SHAP特征重要性的条形图与蜂群图组合可视化`
  - family: shap_composite,scatter_regression,dual_axis | grid: — | palette: #4A90E2,#E94B3C
  - tricks: axes_inset_overlay,pvalue_stars_overlay,raincloud_combo,alpha_layered_scatter

### Narrative arc: `mirror_compare` (4 cases)

- **1777455283** `期刊复刻：通过双侧棒棒糖图解析特征重要性与ALE主效应方向`
  - family: dual_axis,lollipop,ale_pdp | grid: [1, 2] | palette: #4A6B8A,#C0504D,#4F81BD
  - tricks: group_divider_axvline
- **1777452890** `期刊复现 `
  - family: radar,shap_composite,mirror_radial | grid: — | palette: #33CCFF,#FFFF99
  - tricks: marginal_axes_grid
- **1777455707** `期刊复现：基于上三角局部填充饼图的相关性矩阵解析合金成分与性能关系`
  - family: heatmap_pairwise,treemap_pie | grid: — | palette: —
  - tricks: —
- **1777452320** `进阶绘图：解决“多变量拥挤”痛点——Python 绘制带显著性星号与斜向色条的三角热图`
  - family: heatmap_pairwise,heatmap,scatter_regression | grid: — | palette: #A50026,#F46D43,#FFFFBF,#74ADD1
  - tricks: upper_triangle_split

### Narrative arc: `hero` (4 cases)

- **1777450933** `期刊复现：Advanced Science “驼峰”阈值回归图解剖与复刻（附Python源码）`
  - family: shap_composite,scatter_regression | grid: — | palette: #D9D9D9,#404040,#E87A6E,#E63946
  - tricks: group_divider_axvline,alpha_layered_scatter
- **1777451123** `期刊复现：Advanced Science 贝叶斯山脊图 + 热图组合策略（附代码）`
  - family: heatmap_pairwise,heatmap,ridgeline | grid: [1, 5] | palette: —
  - tricks: imshow_gradient_box,axes_inset_overlay,group_divider_axvline,error_band_fill_between,ridgeline_offset_kde
- **1777449664** `绝美！Nature 这张雷达图，被我用 Python 像素级扒下来了！`
  - family: radar,ale_pdp | grid: — | palette: —
  - tricks: polygon_polar_grid,polar_value_marker
- **1777452180** `顶刊同款！Python绘制堆叠小提琴图`
  - family: scatter_regression,violin,box | grid: [3, 1] | palette: #F79698,#6CA6F0,#98E6B6,#FBC285
  - tricks: colored_marker_edge

### Narrative arc: `inset_overlay` (3 cases)

- **1777452243** `复现顶刊 `
  - family: scatter_regression,raincloud,box | grid: — | palette: #FFA500,#008000
  - tricks: density_color_scatter,axes_inset_overlay,raincloud_combo
- **1777450514** `期刊复现：Nature Nanotechnology 经典“画中画”组合图（附 Python 完整代`
  - family: heatmap,scatter_regression | grid: — | palette: #ED9F78
  - tricks: imshow_gradient_box,axes_inset_overlay,raincloud_combo,alpha_layered_scatter
- **1777451060** `顶刊复刻 `
  - family: radar,scatter_regression | grid: — | palette: —
  - tricks: polygon_polar_grid,colored_marker_edge,alpha_layered_scatter
