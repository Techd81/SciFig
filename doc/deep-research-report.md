# 基于真实实验数据的顶刊级科研实验图绘图 Skill 产品研究报告

## 执行摘要

本报告研究的产品形态是：面向科研人员与数据分析人员的“科研实验图绘图 skill”，输入真实实验数据（CSV/Excel/矩阵），自动完成数据结构识别、统计流程建议与执行、并生成符合顶刊风格与投稿规范的高质量图形（尤其是矢量图 PDF/SVG）及可复现代码。该方向的关键壁垒不在“能画出图”，而在“能画出可投稿的图”：顶刊对字体、尺寸、线宽、色彩可访问性、面板排版、文件格式、以及统计信息披露都有明确偏好与硬性规则，且强调图像完整性与可追溯性。以 Nature 体系为例，其图形指南明确提出：字体需可编辑、避免网格线/阴影等装饰、线条粗细范围、单/双栏尺寸与字体点数范围、颜色可访问性与避免红绿对比/彩虹色标、并强调导出时嵌入字体（含 Matplotlib 的 `pdf.fonttype=42` 建议）与使用矢量格式（PDF/EPS）等要求。citeturn12view0turn12view1turn13view1

竞品与替代方案方面，现有生态可分为三类：桌面 GUI 科研绘图统计软件（如 Prism、Origin、JMP）以低门槛与内置统计见长，但在可复现性、批量化、风格模板一致性与复杂多 panel 组图自动化方面存在明显缺口；代码绘图库（Python/R）具备精细控制与可复现优势，但对用户技能要求高，且“顶刊风格化”往往依赖多年经验沉淀；AI 编码助手（如对话式代码生成、IDE 内联助手、Notebook AI 扩展）能提升写代码效率，却缺少对期刊规范、统计合规与默认风格引擎的“科研语义理解”。citeturn6search0turn6search5turn6search6turn2search0turn4search3turn3search1turn3search2turn3search4

建议的 MVP 应聚焦“高频且最能体现顶刊质感”的图型与流程：分组比较图（箱线/小提琴/分组散点与显著性标注）、热力图/聚类热图、火山图、PCA/UMAP、ROC 与 KM 曲线、相关矩阵，以及基础的多 panel 拼图（A/B/C 标注与统一尺寸）。并将 Nature 体系公开规范抽象为可工程化的“样式与导出规则集”，以“上传→识别→建议→生成代码→一键导出→迭代修改”为核心交互闭环。citeturn9view0turn12view0turn12view1turn13view0turn2search0turn20search0turn20search1

## 目标用户与使用场景

目标用户可按“科研绘图链路角色”拆分：

研究生与博士后：手里有 Excel/CSV/分析结果表，希望快速得到“论文级主图/补图”，但缺乏 matplotlib/ggplot2 的风格控制经验，常见问题是线宽、字体、配色、留白、显著性标注与多 panel 布局不统一，导致图像像“分析截图”而非“期刊 figure”。Nature 指南对图形尺寸、字体点数、可编辑字体与导出格式提出明确要求，恰好对应这一群体最薄弱的环节。citeturn12view0turn12view1turn13view1

生信/计算生物/数据科学工程师：强调可复现、批量化与自动化（同一套管线产出多个项目/多个队列/多个阈值版本），更需要“从数据结构出发自动选图并固化样式模板”的系统能力。热力图、聚类热图与多注释排版是高频痛点；R 生态的 ComplexHeatmap之所以流行，核心在于它对复杂热图排版与注释的高灵活性。citeturn0search3turn0search15turn0search7

PI/通讯作者/论文润色与科研服务人员：更关注“是否符合期刊规范与审稿习惯”，例如要求在图中展示原始数据点、明确误差线含义、报告精确 n 值与重复类型（biological/technical replicates），并避免不当图像处理。Nature 的投稿与图像完整性页面对这些要点有直接要求。citeturn9view0turn13view0turn5search0

典型使用场景包括：

将实验重复数据从“柱状图+误差线”升级为“显示所有数据点（dot plot）+分布（violin/box）+清晰误差线含义与 n 标注”，以满足更强的数据透明度趋势；Nature Biomedical Engineering 明确呼吁在图中展示数据点，JBC 资源也建议尽可能用散点而非柱状图，并要求清晰说明误差线与 n 的含义。citeturn1search9turn1search18

基于差异分析输出（log2FC、p 值、校正 p 值）快速生成可投稿火山图，并支持标签避让、阈值可配置与多重比较校正（如 Benjamini–Hochberg FDR）。citeturn2search2turn2search10turn19search7

将模型评估结果表生成 ROC 曲线并输出矢量图；scikit-learn 提供 `roc_curve` 与 `roc_auc_score` 的标准实现。citeturn4search1turn4search5

将临床或动物实验随访数据生成 KM 曲线，并提供 log-rank 检验；lifelines 文档提供 KM 拟合与统计检验接口。citeturn4search0turn21search3

## 竞品与现有工具格局

本节对比的“工具面”覆盖：桌面 GUI 软件（Prism、Origin、JMP）、代码绘图库（Python/R）、在线热图服务与 AI 编码辅助。涉及的主要机构包括 entity["company","GraphPad","scientific software company"]、entity["company","OriginLab","data analysis software"]、entity["company","SAS","analytics software company"]、entity["organization","Broad Institute","biomedical research institute"]、entity["company","BioRender","scientific illustration platform"]、entity["company","OpenAI","ai research company"]、entity["company","GitHub","software hosting company"] 与 entity["company","Microsoft","technology company"]。citeturn6search0turn6search5turn6search6turn19search2turn19search0turn3search1turn3search4

对比符号说明：✅ 强/原生支持；△ 可实现但需要额外搭建或学习；— 不适合或不支持。

| 工具/库 | 类别 | 数据导入（CSV/Excel） | 统计分析（t/ANOVA/非参/多重校正等） | 顶刊风格落地（尺寸/字体/线宽/导出规则可固化） | 热图/聚类热图 | KM/ROC | 多 panel 拼图 | 可复现/可批量 | 导出（SVG/PDF/EPS/TIFF） | 依据 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GraphPad Prism | 桌面 GUI | ✅ | ✅ | △ | △ | ✅ | △ | △ | ✅ | citeturn6search0turn6search4 |
| Origin/OriginPro | 桌面 GUI | ✅ | △ | △ | △ | △ | △ | △ | ✅ | citeturn6search5turn6search1 |
| JMP | 桌面 GUI | ✅ | ✅ | △ | △ | △ | △ | △ | △ | citeturn6search6turn6search21 |
| Matplotlib（Python） | 代码库 | ✅ | —（依赖 SciPy/statsmodels） | ✅（rcParams/样式表/严格尺寸导出） | △ | △ | ✅（GridSpec 等） | ✅ | ✅ | citeturn2search0turn4search3turn20search0turn20search1 |
| seaborn（Python） | 代码库 | ✅ | —（偏可视化） | △（仍需底层 matplotlib 精修） | ✅（含 clustermap） | — | △ | ✅ | ✅ | citeturn4search2turn4search6turn2search5 |
| ggplot2 + patchwork（R） | 代码库 | ✅ | △（配合 stats 生态） | ✅（主题系统+组图） | △ | △ | ✅ | ✅ | ✅ | citeturn7search3turn7search2turn7search14 |
| ComplexHeatmap（R/Bioconductor） | 代码库 | ✅ | —（偏可视化） | ✅（复杂热图与注释排版强） | ✅ | — | ✅（热图+注释组合） | ✅ | ✅ | citeturn0search3turn0search15 |
| Plotly（Python） | 代码库/在线生态 | ✅ | — | △（交互强，期刊风格需额外主题化） | ✅ | ✅ | ✅（subplots） | ✅ | ✅（可导出 SVG/PDF） | citeturn7search4turn7search8 |
| Altair/Vega-Lite（Python） | 代码库 | ✅ | — | △（声明式美观，但科研特定规则需封装） | △ | △ | △ | ✅ | ✅（可导出 SVG/PDF） | citeturn7search1turn7search5 |
| Morpheus | 在线服务 | ✅（矩阵导入） | △（探索型） | △ | ✅ | △ | — | — | △ | citeturn19search2turn19search10turn19search22 |
| BioRender | 在线服务 | △（偏示意/排版） | — | △ | — | — | ✅ | — | △ | citeturn19search0turn19search24 |
| ChatGPT / GitHub Copilot / Jupyter AI | AI 辅助 | △（靠用户描述/提示） | △（能写统计代码，但需校验） | △（容易“能跑但不顶刊”） | △ | △ | △ | △ | △ | citeturn3search4turn3search1turn3search2 |

对“基于真实实验数据、输出顶刊级论文图”的产品来说，机会点集中在两个缝隙：其一，把顶刊图形规范（尺寸、字体点数、线宽范围、可访问性色彩、导出格式、嵌入字体、避免装饰元素等）固化为可机器执行的风格引擎；其二，把统计合规与数据结构识别前置为默认流程，否则“看起来好看”也可能因误差线/重复定义/多重比较处理不当而被审稿意见否定。citeturn9view0turn12view0turn13view1turn1search18

## 顶刊风格的审美与合规要求

以 entity["company","Springer Nature","academic publisher"] 的 Nature 体系为代表，顶刊风格可以被拆成“可工程化的版式与可读性规则”与“不可替代的人类叙事与科学判断”两部分。本节聚焦前者：能被产品化的硬规则与强偏好。citeturn12view0turn12view1turn13view1turn9view0

### 版式尺寸与字体规则

尺寸：Nature figure guide 明确给出单栏宽 89 mm、双栏宽 183 mm，最大高度 170 mm（给图注留空间），并提醒生产流程可能缩放，建议按最小合适尺寸提交。citeturn12view1

字体与点数：要求使用标准无衬线字体（Arial/Helvetica），所有文字可编辑且清晰，正文标注常见范围 5–7 pt；多面板标签建议使用 8 pt 加粗、小写 a/b/c。citeturn12view0turn12view1turn9view0

文字可编辑与嵌入字体：Nature figure guide 明确反对“outlined text（文字转轮廓）”，并要求嵌入字体（TrueType 2 或 42）。其中特别点名：若使用 Python/Matplotlib，可通过 `Matplotlib.rcParams['pdf.fonttype']=42` 避免文字被转为不可编辑轮廓。citeturn12view0turn4search3

image_group{"layout":"carousel","aspect_ratio":"1:1","query":["Nature research figure guide panel arrangement schematic 89 mm 183 mm","Nature research figure guide font sizes 5pt 7pt figure labels example"],"num_per_query":1}

### 配色与可访问性

避免红绿对比与彩虹色标：Nature 初投指南要求使用可区分且可访问的颜色，避免红绿对比，并明确“避免彩虹色标”；对荧光图像鼓励使用更易辨识的组合（如绿/品红）。citeturn9view0turn12view0

可访问性标准：Nature figure guide 提到 Nature.com 尽可能遵循 WCAG 2.1 AA 级别，并要求作者考虑色盲等可访问性。citeturn12view0turn12view1 作为行业通用参照，entity["organization","W3C","web standards body"] 的 WCAG 2.1 规范定义了对比度等要求，可用作“颜色/标注可读性”自动检查的理论依据。citeturn22search0turn22search13

色盲友好调色板：Nature figure guide 直接引用 Bang Wong 在 Nature Methods 的“Color blindness”文章作为可访问性颜色的参考。citeturn22search4turn22search8 这意味着你的产品可以把“色盲友好配色”设计为默认策略，并提供自动校验与一键替换功能。

### 线条、坐标轴、网格线与装饰元素

坐标轴与刻度：Nature figure guide 对图形（graphs）明确要求保留轴线与刻度，并确保轴标签带单位（括号）。citeturn12view0

避免背景网格线与装饰：明确列出应避免的元素，包括背景网格线、装饰性图标、阴影（drop shadows）、图案填充、彩色文字、拥挤重叠文字等。citeturn12view0

线宽范围：Extended Data 指南给出线条/描边的推荐范围 0.25–1 pt。这个数字对“顶刊质感”非常关键，因为很多“丑图”的根源来自默认线宽与字体不匹配。citeturn13view1

### 导出格式与分辨率

矢量优先：Nature figure guide 建议以矢量形式导出 panel，优先 PDF/EPS，并保持文字/线条/比例尺为可编辑矢量元素。citeturn12view0turn12view1

分辨率：对摄影类图像最低 300 dpi，且提到在线校样最大 450 dpi，建议提供 450 dpi 或更高以获得最佳分辨率（同时强调“人为提高 dpi 不会提升质量”）。citeturn12view0 作为跨出版社通用参照，Elsevier 的快速指南也区分了不同图像类型的最小 dpi：照片 300 dpi、线稿 1000 dpi、混合图 500 dpi，并强调矢量图用 EPS/PDF 且嵌入字体。citeturn18view1turn17search17

### 统计信息披露与图注规范

误差线必须定义：Nature 初投指南要求“确保图中误差线被定义”，并要求在统计部分说明检验方法、单/双尾、以及在图中给出用于计算统计量的精确 n。citeturn9view0turn9view1

精确 n 与重复定义：Nature 要求明确 replicates（重复类型）并对“代表性实验”说明重复次数；其 Reporting Checklist 类资源也强调技术重复与生物重复的区别，避免误导。citeturn9view0turn1search13

“展示数据点”的趋势：Nature Biomedical Engineering 的政策性文章鼓励在图中展示个体数据点；JBC 作者资源也建议尽可能用散点图而非柱状图，并要求清晰说明误差线代表什么以及 n（包括技术/生物重复）。citeturn1search9turn1search18

### 图像完整性与 AI 图像风险

图像完整性：Nature figure guide 的 image integrity 页面要求图像应真实反映原始数据，必要时对拼接边界进行清晰标示，并避免使用“克隆/修复/内容感知移动”等会遮蔽数据的工具。citeturn13view0 Nature Portfolio 的 image integrity 政策同样强调最小化处理与编辑筛查。citeturn5search0

生成式 AI：Nature figure guide 明确指出“任何形式的生成式 AI 用于 figures 不被允许”，并将 Photoshop 的 Generative Fill 等列为禁用工具。对你的产品而言，这意味着必须把“基于真实数据的代码绘图”与“生成式图像/内容感知修补”严格隔离，至少在 Nature 风格模式下提供显性风险提示与合规声明。citeturn13view0

## 图类型最佳实践与实现建议

本节将用户列出的高频图型，拆为“表达目标→最佳实践→推荐实现路径（Python 为主，R 为辅）”。其中的实现建议优先使用官方文档可追溯的库接口（pandas、matplotlib、seaborn、SciPy、statsmodels、scikit-learn、umap-learn、lifelines 等）。citeturn8search0turn2search0turn4search3turn4search2turn8search2turn2search2turn2search3turn3search7turn4search0

### 热力图与聚类热图

最佳实践要点：热图不是“把矩阵染色”，而是“在高密度信息下维持可读性”。关键包括：对行/列做一致的标准化策略（如按行 z-score）、明确色条范围与中心点（尤其是表达 up/down 的发散色标）、控制标签密度（只显示关键行/列或分层标签）、统一线宽与字体点数、避免彩虹色标、并在需要时添加样本/分组注释条。Nature 明确要求色彩可访问并避免彩虹色标、且要求字体 5–7 pt、线宽范围等硬约束。citeturn9view0turn12view0turn13view1

Python 路线：seaborn 提供 `heatmap` 与 `clustermap`（后者依赖 SciPy 并支持层次聚类）。优点是生态成熟；缺点是深度定制有时需要回到 matplotlib。citeturn4search6turn4search2

R 路线：ComplexHeatmap 以“可组合热图+注释+布局”为核心，适合做顶刊常见的复杂热图 figure；并有 InteractiveComplexHeatmap 扩展支持交互查看。citeturn0search3turn0search7

### 箱线图、小提琴图与分组散点

最佳实践要点：在样本量不大或分布重要时，优先展示个体点（strip/swarm）叠加分布摘要（box/violin），并明确误差线与统计量含义。Nature Biomedical Engineering 与 JBC 资源均强调展示数据点与清晰的 n/误差线说明。citeturn1search9turn1search18

Python 实现建议：seaborn 的 `boxplot`、`violinplot` 可搭配 `stripplot` 或 `swarmplot` 做“分布+个体点”的组合；其中 swarm/strip 的适用与参数在官方文档中明确。citeturn2search5turn2search13turn2search9turn2search1

统计标注：显著性标注应基于“独立重复”的统计结果，并避免把技术重复当成 n；对“n 的定义”存在大量误用与伪重复风险，Lazic 的文章系统讨论了 cell culture/animal experiments 中 N 的含义与伪重复问题，可作为默认策略的理论依据之一。citeturn1search6turn1search21

### 柱状图 + 误差线 + 显著性标注

最佳实践要点：柱状图在科研中常被批评为掩盖分布信息，因此若使用柱状图，建议至少同时显示原始点或采用更透明的替代（如“均值线+散点+CI”）。JBC 明确建议尽可能用散点而非柱状图。citeturn1search18

误差线：必须在图注中解释误差线（SD/SEM/CI），并提供精确 n 与重复定义；Nature 初投指南要求“定义误差线并给出精确 n”。citeturn9view0turn9view1

### 折线图与时间序列

最佳实践要点：时间序列常需要同时表达趋势与变异度。建议区分“技术重复曲线”（可用淡色细线）与“生物学重复汇总”（用均值线+置信区间带），并在图注中说明误差带含义与 n 定义。Nature 对误差线定义与重复定义的要求决定了产品必须把这些信息结构化写进图注/元数据。citeturn9view0

实现建议：matplotlib 负责主控尺寸、线宽、字体点数与导出；必要时用 `constrained_layout` 自动避免标签、图例与色条重叠。citeturn20search1turn2search0

### PCA 与 UMAP

PCA：scikit-learn 的 PCA 接口提供 `explained_variance_` 与 `explained_variance_ratio_`，方便将解释方差写入坐标轴标题（例如 PC1 (35%)）。citeturn2search3turn2search15

UMAP：umap-learn 文档给出核心参数（如 `n_neighbors`、`min_dist`、`random_state` 等）。在论文级出图时，必须固定随机种子以确保复现。citeturn3search7turn3search3

可视化：点图同样应使用可访问调色板并避免红绿对比；Nature 明确强调色盲友好与避免红绿/彩虹。citeturn9view0turn12view0turn22search8

### 火山图

数据结构标准：火山图通常来自差异分析结果表，至少需要基因/特征名、log2 fold change、p 值与（最好）校正 p 值（FDR）。Scanpy 的 `rank_genes_groups` 输出就包含 `logfoldchanges`、`pvals`、`pvals_adj` 等字段，可作为“输入 schema”参考。citeturn20search3

多重比较：默认应提供 BH-FDR（`fdr_bh`）并允许更严格方法；statsmodels 的 `multipletests` 明确列出了 `fdr_bh`、`fdr_by` 等方法。citeturn2search2turn2search10

R 生态参考：EnhancedVolcano 在 Bioconductor 中以“publication-ready volcano plots”为目标，体现了用户对“可投稿火山图”的成熟需求。citeturn19search7turn19search11

### ROC 曲线

计算：scikit-learn 提供 `roc_curve` 与 `roc_auc_score` 的标准实现，并支持减少绘制点数量的 `drop_intermediate` 等参数。citeturn4search1turn4search5

出图：论文中常同时展示 ROC 曲线、AUC 数值、以及置信区间（可作为后续增强）。基础版本至少要输出矢量 PDF/SVG，并确保线宽、字体点数符合图形规范。citeturn2search0turn13view1

### KM 生存曲线

拟合与绘图：lifelines 的 `KaplanMeierFitter` 支持 KM 拟合并提供绘图接口。citeturn4search0turn4search8

统计检验：lifelines 文档指出 logrank 在比例风险假设成立时更有力，并提示曲线交叉时解读风险；这类统计注意事项适合由产品内置成“自动警告/解释”。citeturn21search3turn21search7

### 相关矩阵与相关性热图

实现：相关矩阵可用 pandas/NumPy 计算后用 seaborn `heatmap` 展示，必要时加层次聚类用 `clustermap`。citeturn4search6turn4search2

风格：应避免背景网格线与装饰，保留必要轴刻度与单位/标签；与 Nature 的“避免网格线、强调可编辑文字与清晰轴标签”一致。citeturn12view0

### 多 panel 拼图

关键难点：顶刊 figure 的“高级感”很大部分来自 panel 一致性与排版。Nature figure guide 明确要求 panel 排列紧凑、尽量减少白边、按字母顺序排列，并控制整体尺寸与字体点数。citeturn12view1turn13view1

Python 实现：matplotlib 的 `GridSpec` 提供精确子图网格控制；`constrained_layout` 可减少图例/色条/标签重叠。citeturn20search0turn20search1

R 实现：patchwork 提供组合 ggplot 的“算子式”排版接口，是 R 生态常用组图方案。citeturn7search2turn7search14

## 数据输入与自动识别、统计流程默认策略

### 数据输入与结构识别需求

产品应支持两种主流数据形态并自动分流：

Tidy（长表）：一行一条观测值，例如 `sample_id / group / time / value / bio_rep / tech_rep`。适用于箱线/小提琴/折线/ROC/KM 等。

Matrix（矩阵）：行是特征（基因/蛋白/代谢物），列是样本，单元格是数值。适用于热图/聚类热图/相关矩阵。

读取层：pandas 的 `read_excel` 与 `read_csv` 是最通用入口，并支持多 sheet、日期解析等；因此产品侧应将“读取参数”显式记录到可复现代码中。citeturn8search0turn8search1

自动识别至少应覆盖：

分组变量识别：基于 dtype（object/category）、唯一值数量占比、是否为用户指定列名（如 group/condition/treatment）等启发式，并输出可编辑的“识别解释”。

重复（replicate）识别：优先识别显式列（bio_rep、technical_rep、batch、donor、animal_id）；若缺失则提示用户补充。Nature 要求“明确定义 replicates 并给出精确 n”，因此缺失 replicate 信息时应阻止自动生成显著性结论，只允许“描述性可视化”。citeturn9view0turn1search13

避免伪重复：当同一 biological unit 下存在多个技术重复时，显著性检验的 n 不应直接等于技术重复次数；Lazic 文章对伪重复风险给出系统阐述，可转化为自动检测规则（例如：同一 subject 下多条记录但未聚合）。citeturn1search6

### 统计流程与默认策略

默认策略必须“保守且可解释”，并把关键选择写入图注/代码注释。Nature 的统计信息要求（定义误差线、给出精确 n、说明检验与单双尾、报告 t/F 与自由度、给出精确 p 值）意味着产品需要把“统计报告”当作一等输出，而不是附属文本。citeturn9view0

建议的默认决策树（概念层）：

误差线默认：优先 SD（体现数据变异度），但必须强制用户选择并在图注中声明；JBC 明确要求说明误差线含义，并倾向 SD 作为变异度表达。citeturn1search18

两组独立比较：默认 Welch t-test（`equal_var=False`）或在明显偏态/小样本时切换 Mann–Whitney U，并允许用户强制指定；SciPy 的 `ttest_ind` 与 `mannwhitneyu` 都是标准实现。citeturn8search2turn21search0

多组比较：正态/方差齐性前提下走 ANOVA（statsmodels `anova_lm`）；否则走 Kruskal–Wallis，并提示需要事后检验（post hoc）定位差异组。citeturn8search3turn21search1

重复测量：优先识别 within-subject 结构并用 `AnovaRM` 或混合效应模型（可作为增强）；statsmodels 提供 `AnovaRM` 接口。citeturn21search2

多重比较校正：默认提供 BH-FDR（`fdr_bh`），并显示校正后 p；statsmodels `multipletests` 提供多种校正方法。citeturn2search2turn2search10

p 值显示策略：默认显示精确 p（至少在图注/补充信息中），并可选星号；Nature 初投指南要求在适用时提供精确 p 值（包括显著与不显著）。citeturn9view0

样本量标注：默认在图中或图注中标注精确 n，且区分 biological/technical。Nature/JBC 均强调 n 与重复类型披露。citeturn9view0turn1search18

## 产品方案与实现建议

### MVP 功能清单与优先级

MVP 的第一目标不是“覆盖所有图”，而是把最常见且最能体现期刊质感的图做到“默认就正确”。

高优先级（首版必须）：

数据上传与解析：支持 CSV/XLSX；自动识别 tidy vs matrix；输出识别报告与可编辑映射。citeturn8search0turn8search1

顶刊风格模板：至少内置一套“Nature-like”规则集（尺寸 89/183 mm、字体 5–7 pt、线宽 0.25–1 pt、禁用网格线与阴影、避免红绿/彩虹、矢量导出与嵌入字体）。citeturn12view1turn13view1turn12view0turn9view0

首批图型：分组比较（箱线/小提琴/分组散点）、热图/聚类热图、火山图、PCA、ROC、相关矩阵。citeturn4search6turn4search2turn2search3turn4search1turn19search7

一键导出：至少输出 SVG+PDF；并可选 TIFF（照片/线稿 dpi 规则可引用 Elsevier/通用指南）。citeturn2search0turn18view1

中优先级（第二阶段）：

UMAP、KM 曲线、折线/时间序列与置信区间带；多 panel 拼图（A/B/C 自动布局、统一边距、统一字号）。citeturn3search7turn4search0turn20search0

统计引擎增强：多组事后检验、自动生成 Methods/legend 的统计句子模板（含 test、tail、df、t/F 值等）与可追溯报告。citeturn9view0turn8search3

低优先级（扩展生态）：

交互式探索与分享（Plotly/Altair 导出）；R 后端（ggplot2/ComplexHeatmap）双栈；在线结果报告。citeturn7search4turn7search1turn0search3

### 技术实现建议

首选技术栈（Python 为主）：

数据层：pandas（读入 CSV/Excel）、NumPy。citeturn8search0turn8search1

统计层：SciPy（t-test、Mann–Whitney、Kruskal）、statsmodels（ANOVA、重复测量 ANOVA、多重比较校正）。citeturn8search2turn21search0turn21search1turn8search3turn21search2turn2search2

可视化层：matplotlib 作为“风格与导出控制面”，seaborn 提供统计图与热图基础；多 panel 用 GridSpec，布局用 constrained_layout。citeturn2search0turn4search3turn4search2turn20search0turn20search1

算法层：scikit-learn（PCA、ROC），umap-learn（UMAP），lifelines（KM 与 logrank）。citeturn2search3turn4search1turn3search7turn4search0turn21search3

关键参数与“顶刊风格落地”示例（面向产品模板化）：

尺寸换算：以 89 mm/183 mm 为基准，转换为英寸设置 `figsize`（Matplotlib 以英寸为单位）；最大高度 170 mm。citeturn12view1

线宽：将 `axes.linewidth`、`lines.linewidth`、`xtick.major.width` 等统一到 0.25–1 pt 区间；并把误差线 capsize 与线宽同步。citeturn13view1turn4search3

字体与可编辑性：默认 sans-serif（Arial/Helvetica），并设置 `pdf.fonttype=42` 以避免文字轮廓化；避免彩色文字。citeturn12view0turn9view0

禁用装饰：默认关闭背景网格线（或极弱化），禁止阴影/渐变/图案填充。citeturn12view0

导出：统一 `savefig(..., format='pdf/svg', bbox_inches='tight')`；Matplotlib 的 `savefig` 支持直接输出矢量格式。citeturn2search0

代码生成策略：

模板驱动而非“自由生成”：将每类图型的代码拆为（a）数据整理块（b）统计块（c）绘图块（d）导出块，并由 schema 与风格引擎填充参数。这样可以保证输出长期稳定、便于测试与回归。

可复现性元数据：输出时同时生成 `requirements.txt`/`environment.yml`、随机种子、输入文件 hash、统计选择记录与图形规格（宽高、字体、线宽、色标）。Nature 对统计与图形描述的要求使这类“可追溯记录”直接对应审稿与返修效率。citeturn9view0turn12view0

### UX/交互设计要点

交互目标是把“画图”从一次性生成变成可控迭代，避免用户反复手改代码。

```mermaid
flowchart LR
U[上传 CSV/Excel/矩阵] --> S[结构识别: tidy vs matrix]
S --> M[变量映射: 分组/数值/时间/重复/批次]
M --> R[风险检查: 缺失n/重复定义/伪重复/异常值]
R --> P[推荐图型与默认统计方案]
P --> C[生成可运行代码 + 样式模板]
C --> V[预览: SVG/PDF]
V --> I[迭代: 改图型/阈值/配色/版式/统计]
I --> E[导出: SVG/PDF/TIFF + 统计报告 + 代码包]
```

在“迭代”环节建议提供的最小控制面：目标期刊风格（至少 Nature-like）、单/双栏尺寸、字体点数范围、是否显示原始点、误差线含义（SD/SEM/CI）、显著性展示（精确 p/星号）、以及多 panel 布局规则（A/B/C 标签、间距、对齐）。这些控制项直接对应 Nature figure guide 的硬性与强偏好。citeturn12view0turn12view1turn13view1turn9view0

### 风险与挑战

学科差异：不同领域对图型偏好差异显著，例如生物医学强调重复定义与点图透明度，机器学习更强调 ROC、置信区间与多折交叉验证呈现方式。产品需以“领域模板”管理，而不是试图用单一规则覆盖全部。

统计合规与可解释性：错误的 n 定义（把技术重复当独立样本）与不当误差线会直接导致审稿质疑；Nature 与多份检查表强调必须定义误差线与 replicates，且要求精确 n。citeturn9view0turn1search13turn1search6

图像完整性与版权/期刊要求：Nature 明确禁止生成式 AI 内容进入 figures，并列出禁止的图像修补工具；同时要求避免不当拼接与不当对比度调整，并可能筛查图像。产品必须在生成与导出链路中强化“仅基于数据绘图”“不做图像修补”的合规边界。citeturn13view0turn5search0turn5search2

工具链依赖：不同机构/用户环境字体、后端、导出链路差异导致“同样代码不同观感”。Nature figure guide 对字体嵌入与可编辑性有明确要求（TrueType 2/42），因此产品最好提供“字体打包/检测”能力。citeturn12view0turn20search2

### 商业化与产品化建议

差异化定位：不是“AI 画图”，而是“投稿级科研实验图自动化系统”。核心卖点可以落在：默认合规（期刊规范内置）、默认好看（风格引擎）、默认可复现（代码与环境）、默认可迭代（交互闭环）。其价值对标 GUI 工具的易用性与代码工具的可复现性，同时补齐两者的短板。citeturn6search0turn2search0turn12view0

定价模型建议：采用“按席位订阅 + 机构授权 + 高级功能分层”。基础版覆盖高频图型与导出；专业版加入多 panel 自动排版、统计报告自动生成、团队模板与审稿返修模式；机构版加入合规模板（如 Nature-like）锁定、审计日志与私有部署（对应科研数据合规）。

渠道与合作：优先切入研究组/平台（生信平台、核心实验平台）与科研写作/润色服务链路；此外，与 Notebook/IDE 生态联动（如在 JupyterLab 内集成），可利用 Jupyter AI 等扩展思路形成“可复现工作台”，但需强调你的产品提供的是“科研规范与风格引擎”，而不仅是代码生成。citeturn3search2turn12view0

## 示例工作流与可运行 Python 示例

以下示例以“可运行、≤30 行、输出 SVG 与 PDF”为约束；真实产品中应把“读入文件、结构识别、统计选择、风格模板”拆成独立模块，并记录元数据以可复现。Matplotlib 的 `savefig` 支持直接输出矢量格式。citeturn2search0turn12view0

### 示例一：两组比较的分组散点 + 箱线 + Welch t-test

输入数据结构示意（tidy 长表）：

| sample_id | group | value |
|---|---|---|
| S1 | Control | 1.2 |
| S2 | Control | 0.9 |
| S3 | Treat | 1.8 |
| … | … | … |

推荐图型：箱线图叠加散点（展示所有点），避免单纯柱状图掩盖分布；符合“展示数据点”的期刊趋势。citeturn1search9turn1search18  
统计方法：Welch t-test（对方差不齐更稳健），SciPy `ttest_ind(equal_var=False)`。citeturn8search2  
期刊级样式要点：单栏宽（89 mm）思路、线宽控制、字体点数、禁用网格线、导出矢量且嵌入字体。citeturn12view1turn13view1turn12view0  
输出格式：SVG + PDF。

```python
import numpy as np, pandas as pd, seaborn as sns, matplotlib.pyplot as plt
from scipy.stats import ttest_ind
np.random.seed(7)
df = pd.DataFrame({"group": np.repeat(["Control","Treat"], 20),
                   "value": np.r_[np.random.normal(1.0,0.25,20),
                                 np.random.normal(1.3,0.30,20)]})
t, p = ttest_ind(df[df.group=="Control"].value, df[df.group=="Treat"].value, equal_var=False)
mm = 1/25.4
plt.rcParams.update({"pdf.fonttype":42,"font.size":6,"axes.linewidth":0.6})
fig, ax = plt.subplots(figsize=(89*mm, 60*mm), constrained_layout=True)
sns.boxplot(data=df, x="group", y="value", width=0.45, fliersize=0, ax=ax)
sns.stripplot(data=df, x="group", y="value", size=2.2, jitter=0.18, ax=ax)
ax.set_xlabel(""); ax.set_ylabel("Signal (a.u.)"); ax.grid(False)
y = df.value.max()*1.08; ax.plot([0,0,1,1],[y,y*1.02,y*1.02,y], lw=0.6, c="black")
ax.text(0.5, y*1.03, f"Welch t-test p={p:.3g}", ha="center", va="bottom", fontsize=6)
fig.savefig("example1.pdf"); fig.savefig("example1.svg")
```

### 示例二：聚类热图（clustermap）用于表达矩阵数据模式

输入数据结构示意（矩阵）：

- 行：基因/特征  
- 列：样本  
- 值：表达量/信号强度  
并可选一个样本注释表（样本分组、批次等）用于顶端色条。

推荐图型：聚类热图（行列聚类），并按行 z-score 标准化以突出相对模式（具体策略需产品可配置）。seaborn `clustermap` 是快速方案，但重度定制时通常需要回到 matplotlib；其文档说明 clustermap 需要 SciPy。citeturn4search2turn4search6  
统计方法：此类图通常是探索性可视化，并不默认做显著性检验；若叠加统计（例如差异基因筛选），需配合多重比较校正。citeturn2search2turn2search10  
期刊级样式要点：避免彩虹色标、字体与线宽控制、必要时减少标签密度；Nature 强调可访问性与避免装饰网格线。citeturn9view0turn12view0  
输出格式：SVG + PDF。

```python
import numpy as np, pandas as pd, seaborn as sns, matplotlib.pyplot as plt
np.random.seed(1)
X = pd.DataFrame(np.random.randn(30, 12), index=[f"G{i}" for i in range(30)],
                 columns=[f"S{i}" for i in range(12)])
Z = X.sub(X.mean(1), axis=0).div(X.std(1).replace(0,1), axis=0)  # row z-score
plt.rcParams.update({"pdf.fonttype":42,"font.size":5,"axes.linewidth":0.4})
g = sns.clustermap(Z, cmap="vlag", center=0, linewidths=0, xticklabels=True, yticklabels=False,
                   figsize=(89/25.4, 75/25.4))
g.ax_heatmap.set_xlabel(""); g.ax_heatmap.set_ylabel("")
g.figure.savefig("example2.pdf"); g.figure.savefig("example2.svg")
```

### 示例三：KM 生存曲线 + log-rank 检验

输入数据结构示意（tidy 长表）：

| time | event | group |
|---|---|---|
| 12 | 1 | A |
| 8 | 0 | A |
| 15 | 1 | B |
| … | … | … |

推荐图型：KM 曲线（含删失标记可作为增强）。citeturn4search0  
统计方法：log-rank 检验；lifelines 文档强调当曲线交叉时 log-rank 的解读需谨慎，可作为产品自动提示。citeturn21search3turn21search7  
期刊级样式要点：线宽、字体点数与单栏尺寸；矢量导出与字体嵌入。citeturn12view1turn12view0  
输出格式：SVG + PDF。

```python
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test
np.random.seed(3)
df = pd.DataFrame({"group": np.repeat(["A","B"], 60)})
df["time"] = np.where(df.group=="A", np.random.exponential(10,60), np.random.exponential(7,60))
df["event"] = (np.random.rand(120) > 0.25).astype(int)
plt.rcParams.update({"pdf.fonttype":42,"font.size":6,"axes.linewidth":0.6})
fig, ax = plt.subplots(figsize=(89/25.4, 60/25.4), constrained_layout=True)
km = KaplanMeierFitter()
for g in ["A","B"]:
    sub = df[df.group==g]; km.fit(sub.time, sub.event, label=g); km.plot(ax=ax, ci_show=False, lw=1)
p = logrank_test(df[df.group=="A"].time, df[df.group=="B"].time,
                 df[df.group=="A"].event, df[df.group=="B"].event).p_value
ax.set_xlabel("Time"); ax.set_ylabel("Survival"); ax.grid(False)
ax.text(0.02, 0.02, f"log-rank p={p:.3g}", transform=ax.transAxes, fontsize=6)
fig.savefig("example3.pdf"); fig.savefig("example3.svg")
```

### 下一步行动项

- 最高优先级：将 Nature research figure guide 的硬规则编码为“风格规范对象”（尺寸 89/183/170mm、字体 5–7pt、线宽 0.25–1pt、禁用网格线/阴影、颜色可访问性、矢量导出、嵌入字体与禁止 outlined text），并为 matplotlib/seaborn 输出一套可自动测试的 rcParams 模板。citeturn12view0turn12view1turn13view1  
- 高优先级：实现数据结构识别（tidy vs matrix）与变量映射 UI，并把“replicates/n/误差线含义”结构化为必填或强提示项，避免伪重复与统计误用。citeturn9view0turn1search6turn1search18  
- 高优先级：落地首批高频图型代码生成器（分组散点+箱线/小提琴、热图/聚类热图、火山图、PCA、ROC、相关矩阵），并确保一键导出 SVG+PDF（可选 TIFF）。citeturn2search0turn4search2turn2search3turn4search1turn19search7  
- 中优先级：加入“多 panel 拼图”与“统一图组风格锁定”（A/B/C 标签、间距、对齐、统一字体/线宽），以实现顶刊 figure 的核心竞争力。citeturn12view1turn20search0turn20search1  
- 中优先级：建立合规与风险防线：在 Nature-like 模式下显性提示“禁止生成式 AI 图像内容进入 figures”，并对图像类输入加入“完整性与拼接标识”检查清单与导出声明模板。citeturn13view0turn5search0