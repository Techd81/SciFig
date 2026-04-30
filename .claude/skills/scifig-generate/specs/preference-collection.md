# Preference Collection Protocol

This file contains the implementation details for interactive preference collection. The orchestrator (`SKILL.md`) references this file; it does not inline the code.

## Helper Functions

```python
preferredQuestionLanguage = "zh" if user_input contains Chinese text or asks for Chinese, else "en"


def normalize_card_answer(raw_answer, mapping):
    if raw_answer in mapping:
        return mapping[raw_answer]
    if any(token in str(raw_answer) for token in ["中文", "请用中文", "Chinese"]):
        return "__language_switch__"
    return "__invalid__"


def is_concrete_data_file_path(path_candidate):
    if not path_candidate:
        return False
    normalized = str(path_candidate).strip().strip('"').strip("'")
    if normalized.endswith("\\") or normalized.endswith("/"):
        return False
    lowered = normalized.lower()
    return lowered.endswith((".csv", ".tsv", ".xlsx", ".xls"))


def resolve_domain_answer(raw_answer, mapping):
    raw = str(raw_answer).strip() if raw_answer is not None else ""
    if raw in mapping:
        return mapping[raw], None
    if not raw or raw == "Other":
        return "general_biomedical", None
    return "custom_user_domain", raw


def infer_domain_family_from_text(domain_family, custom_domain_text):
    text = (custom_domain_text or "").lower()
    if domain_family != "custom_user_domain":
        return domain_family
    if any(k in text for k in ("clinical", "patient", "trial", "survival", "diagnostic", "tumor", "cancer")):
        return "clinical_diagnostics_survival"
    if any(k in text for k in ("genomic", "transcript", "single-cell", "scrna", "spatial", "omics", "gene")):
        return "genomics_transcriptomics"
    if any(k in text for k in ("immune", "cell biology", "cytokine", "flow cytometry")):
        return "immunology_cell_biology"
    if any(k in text for k in ("neuro", "behavior", "behaviour", "brain")):
        return "neuroscience_behavior"
    if any(k in text for k in (
        "computer", "machine learning", "deep learning", "artificial intelligence", "ai", "ml",
        "random forest", "randomforest", "rf", "rfr", "xgboost", "lightgbm", "gbdt",
        "model benchmark", "model performance", "classifier", "regressor", "algorithm"
    )):
        return "computer_ai_ml"
    if any(k in text for k in ("material", "polymer", "alloy", "engineering")):
        return "materials_engineering"
    if any(k in text for k in ("ecology", "environment", "biodiversity", "climate", "marine")):
        return "ecology_environmental"
    if any(k in text for k in ("agriculture", "crop", "yield", "food", "sensory")):
        return "agriculture_food_science"
    if any(k in text for k in ("psychology", "survey", "likert", "social", "education")):
        return "psychology_social_science"
    if any(k in text for k in (
        "audio", "acoustic", "sound", "speech", "signal", "wave", "spectrogram", "sonar", "ultrasound",
        "音频", "声学", "声音", "语音", "信号", "波形", "声波", "频谱", "超声",
    )):
        return "signal_processing_acoustics"
    return "general_biomedical"
```

## AI Journal-Style Options with Fallback

Journal-style options are AI-generated after the user selects a domain. The user-facing labels must be top journals, conferences, or venue families from that selected field, not the generic Nature/Science/Cell trio. The fallback map below is only a domain-specific seed list for runtimes where `_call_option_generator` is not intercepted; it must not replace the AI reasoning step.

```python
_DOMAIN_TOP_JOURNAL_SEEDS = {
    "computer_ai_ml": [
        {"en": ("NeurIPS / ICML / ICLR-style (Recommended)", "Machine-learning benchmark, ablation, feature-importance, and model-diagnostic figures with compact technical density", "field_compact"),
         "zh": ("NeurIPS / ICML / ICLR 风格（推荐）", "适合机器学习 benchmark、消融、特征重要性和模型诊断图；强调紧凑技术密度", "field_compact")},
        {"en": ("IEEE TPAMI / TNNLS-style", "Algorithm comparison, classifier/regressor validation, and quantitative model-performance figures", "field_methods"),
         "zh": ("IEEE TPAMI / TNNLS 风格", "适合算法对比、分类/回归验证和定量模型性能图", "field_methods")},
        {"en": ("Nature Machine Intelligence-style", "AI-for-science stories that combine prediction accuracy, stability, and interpretability", "field_dense"),
         "zh": ("Nature Machine Intelligence 风格", "适合 AI for Science；组合预测精度、稳定性和可解释性", "field_dense")},
    ],
    "signal_processing_acoustics": [
        {"en": ("IEEE/ACM TASLP-style (Recommended)", "Audio, speech, and acoustic signal-processing figures with compact spectra, waveform, and model-comparison panels", "field_compact"),
         "zh": ("IEEE/ACM TASLP 风格（推荐）", "适合音频、语音和声学信号处理；强调频谱、波形、模型对比和紧凑多 panel", "field_compact")},
        {"en": ("JASA-style", "Acoustics-first presentation for wave, psychoacoustic, room/speech, and measurement-heavy studies", "field_methods"),
         "zh": ("JASA 风格", "适合声学、波形、心理声学、房间/语音和测量型研究；强调方法与可解释标注", "field_methods")},
        {"en": ("IEEE TSP / Signal Processing-style", "Signal-processing theory, filtering, time-frequency analysis, and algorithm-performance figures", "field_compact"),
         "zh": ("IEEE TSP / Signal Processing 风格", "适合信号处理理论、滤波、时频分析和算法性能图；强调清晰坐标与算法比较", "field_compact")},
    ],
    "clinical_diagnostics_survival": [
        {"en": ("Lancet-style (Clinical recommended)", "Clinical evidence, cohort, survival, and translational medical figures", "lancet"),
         "zh": ("Lancet 风格（临床推荐）", "适合临床证据、队列、生存和转化医学图表", "lancet")},
        {"en": ("NEJM-style", "High-impact clinical trial, outcome, and medical research figures", "nejm"),
         "zh": ("NEJM 风格", "适合高影响临床试验、结局和医学研究", "nejm")},
        {"en": ("JAMA-style", "Diagnostic accuracy, validation studies, and precise labeling", "jama"),
         "zh": ("JAMA 风格", "适合诊断准确性、验证研究和清晰标签", "jama")},
    ],
    "genomics_transcriptomics": [
        {"en": ("Nature Genetics / Nature Methods-style (Recommended)", "Omics discovery, methods, clustering, enrichment, and validation-heavy multi-panel figures", "nature"),
         "zh": ("Nature Genetics / Nature Methods 风格（推荐）", "适合组学发现、方法、聚类、富集和验证型多 panel 图", "nature")},
        {"en": ("Genome Biology-style", "Genomics workflows, benchmarking, differential analysis, and data-resource figures", "field_methods"),
         "zh": ("Genome Biology 风格", "适合组学流程、benchmark、差异分析和数据资源型图表", "field_methods")},
        {"en": ("Cell Genomics-style", "Mechanistic omics and cell-state stories with denser multi-panel organization", "cell"),
         "zh": ("Cell Genomics 风格", "适合机制组学和细胞状态叙事；强调较密集的多 panel 组织", "cell")},
    ],
    "materials_engineering": [
        {"en": ("Advanced Materials-style (Recommended)", "Materials mechanism, performance, microscopy/spectra, and application-oriented multi-panel figures", "field_dense"),
         "zh": ("Advanced Materials 风格（推荐）", "适合材料机制、性能、显微/谱图和应用导向多 panel", "field_dense")},
        {"en": ("ACS Nano / Nano Letters-style", "Nanomaterials, device metrics, compact spectra, and structure-performance figures", "field_compact"),
         "zh": ("ACS Nano / Nano Letters 风格", "适合纳米材料、器件指标、紧凑谱图和结构-性能图", "field_compact")},
        {"en": ("Materials Today-style", "Cross-disciplinary materials story with clear mechanism-to-performance flow", "science"),
         "zh": ("Materials Today 风格", "适合跨学科材料叙事；强调机制到性能的清晰链路", "science")},
    ],
    "_default": [
        {"en": ("Field-leading journal style (Recommended)", "Ask the AI runtime to name the top venue for the selected field and adapt figure density to that venue", "field_top_journal"),
         "zh": ("本领域顶刊风格（推荐）", "由 AI 根据所选领域命名顶级期刊/会议，并按该领域图表习惯调整密度与标注", "field_top_journal")},
        {"en": ("Methods-focused journal style", "For method, benchmark, pipeline, and validation-heavy studies in the selected field", "field_methods"),
         "zh": ("方法型顶刊风格", "适合该领域的方法、benchmark、流程和验证型研究", "field_methods")},
        {"en": ("Compact communication style", "For concise, fast-scanning figures when the selected field values compact technical communication", "field_compact"),
         "zh": ("紧凑传播型风格", "适合该领域偏好快速阅读、低墨量和技术比较的图表", "field_compact")},
    ],
}

# Domains that share the genomics journal-style set
_GENOMICS_LIKE_DOMAINS = {"genomics_transcriptomics", "single_cell_spatial", "proteomics_metabolomics", "immunology_cell_biology"}
# Domains that share the materials journal-style set
_CROSS_DISCIPLINE_DOMAINS = {"materials_engineering", "ecology_environmental", "agriculture_food_science", "psychology_social_science", "neuroscience_behavior"}


def infer_journal_style_fallback_options(domain_family, custom_domain_text, language):
    """Return domain-specific top-journal fallback options for the journal-style card."""
    effective_domain = infer_domain_family_from_text(domain_family, custom_domain_text)
    lang = language if language in ("zh", "en") else "en"

    if effective_domain == "computer_ai_ml":
        entries = _DOMAIN_TOP_JOURNAL_SEEDS["computer_ai_ml"]
    elif effective_domain == "signal_processing_acoustics":
        entries = _DOMAIN_TOP_JOURNAL_SEEDS["signal_processing_acoustics"]
    elif effective_domain == "clinical_diagnostics_survival":
        entries = _DOMAIN_TOP_JOURNAL_SEEDS["clinical_diagnostics_survival"]
    elif effective_domain in _GENOMICS_LIKE_DOMAINS:
        entries = _DOMAIN_TOP_JOURNAL_SEEDS["genomics_transcriptomics"]
    elif effective_domain in _CROSS_DISCIPLINE_DOMAINS:
        entries = _DOMAIN_TOP_JOURNAL_SEEDS["materials_engineering"]
    else:
        entries = _DOMAIN_TOP_JOURNAL_SEEDS["_default"]

    return [{"label": e[lang][0], "description": e[lang][1], "styleKey": e[lang][2]} for e in entries]


def _normalize_journal_options(options, fallback_options):
    """Accept field-specific AI journal labels and attach a styleKey for rendering."""
    valid = []
    for option in options or []:
        if not isinstance(option, dict):
            continue
        label = option.get("label")
        description = option.get("description")
        if label and description:
            valid.append({
                "label": label,
                "description": description,
                "styleKey": option.get("styleKey") or option.get("visualStyleKey") or "field_top_journal",
                "journalName": option.get("journalName") or label,
            })
    return valid[:5] if len(valid) >= 2 else fallback_options


def infer_journal_style_options(domain_family, custom_domain_text, language, context=None):
    """Return AI-generated field-top-journal options with deterministic domain fallback."""
    fallback_options = infer_journal_style_fallback_options(domain_family, custom_domain_text, language)
    effective_domain = infer_domain_family_from_text(domain_family, custom_domain_text)
    context = dict(context or {})
    domain_hints = context.get("domainHints", {})
    if not isinstance(domain_hints, dict):
        domain_hints = {"selected": domain_hints}

    journal_context = {
        **context,
        "language": language if language in ("zh", "en") else "en",
        "selectedDomainFamily": domain_family,
        "customDomainText": custom_domain_text,
        "effectiveDomainFamily": effective_domain,
        "fallbackJournalSeeds": fallback_options,
        "domainHints": {
            **domain_hints,
            "selected": custom_domain_text or domain_family,
            "primary": effective_domain,
        },
    }
    ai_options = generate_options_with_ai(journal_context, "journal_style", fallback_options)
    return _normalize_journal_options(ai_options, fallback_options)
```

## Synthetic Bundle Options

```python
_BUNDLE_BY_DOMAIN = {
    "computer_ai_ml": [
        {"en": ("ML model-performance set (Recommended)", "Model benchmark, train/test metrics, predicted-vs-actual, residual, and feature-importance panels"),
         "zh": ("机器学习模型性能图表集（推荐）", "模型 benchmark、训练/测试指标、预测-真实、残差和特征重要性面板")},
        {"en": ("Explainability / SHAP set", "Feature importance, SHAP-style contribution, dependence, and interaction panels"),
         "zh": ("可解释性 / SHAP 图表集", "特征重要性、SHAP 风格贡献、依赖和交互作用面板")},
        {"en": ("Classifier validation set", "ROC, PR, calibration, threshold, and confusion-oriented validation panels"),
         "zh": ("分类器验证图表集", "ROC、PR、校准、阈值和混淆矩阵导向验证面板")},
    ],
    "genomics_transcriptomics": [
        {"en": ("Omics discovery set (Recommended)", "Differential analysis, heatmap, enrichment, PCA/UMAP"),
         "zh": ("组学发现图表集（推荐）", "差异分析、热图、富集、PCA/UMAP")},
        {"en": ("Single-cell / spatial set", "Embedding, composition, expression, spatial or cell-type panels"),
         "zh": ("单细胞/空间图表集", "embedding、组成、表达、空间或细胞类型面板")},
        {"en": ("Mechanism-focused set", "Expression, pathway, and validation-heavy figures"),
         "zh": ("机制验证图表集", "表达、通路和验证实验组合")},
    ],
    "clinical_diagnostics_survival": [
        {"en": ("Clinical translational set (Recommended)", "Survival, ROC, stratification, efficacy, and cohort overview"),
         "zh": ("转化医学图表集（推荐）", "生存、ROC、分层、疗效和队列概览")},
        {"en": ("Mechanism-focused set", "Mechanism, biomarker, and validation-heavy figures"),
         "zh": ("机制验证图表集", "机制、标志物和验证实验组合")},
        {"en": ("Integrated figure set", "Discovery, validation, and context in one publication-ready bundle"),
         "zh": ("综合科研图表集", "覆盖发现、验证和背景说明")},
    ],
    "_default": [
        {"en": ("Domain-general figure set (Recommended)", "Core figures adapted to the user-selected or custom domain"),
         "zh": ("领域通用图表集（推荐）", "适配用户输入或选定领域的核心图表")},
        {"en": ("Process / mechanism set", "Process, mechanism, time, or experimental-condition changes"),
         "zh": ("机制/过程图表集", "强调过程、机制、时间或实验条件变化")},
        {"en": ("Comparison / trend set", "Group comparisons, trends, distributions, and correlations"),
         "zh": ("对比/趋势图表集", "强调组间比较、趋势、分布和相关性")},
    ],
}


def infer_synthetic_bundle_options(domain_family, custom_domain_text, language):
    """Return list of {label, description} dicts for the synthetic-bundle card."""
    effective = infer_domain_family_from_text(domain_family, custom_domain_text)
    lang = language if language in ("zh", "en") else "en"

    if effective == "computer_ai_ml":
        entries = _BUNDLE_BY_DOMAIN["computer_ai_ml"]
    elif effective == "genomics_transcriptomics":
        entries = _BUNDLE_BY_DOMAIN["genomics_transcriptomics"]
    elif effective == "clinical_diagnostics_survival":
        entries = _BUNDLE_BY_DOMAIN["clinical_diagnostics_survival"]
    else:
        entries = _BUNDLE_BY_DOMAIN["_default"]

    return [{"label": e[lang][0], "description": e[lang][1]} for e in entries]
```

## Template-backed Chart Bundle Options

The chart-bundle question must be grounded in `template-mining/case-index.json` and the dedicated technique notes under `template-mining/07-techniques/`. Ask this card as:

> 你希望生成哪类图表套餐？

For real-file interactive runs, ask it after Phase 1 has inferred the domain and before Phase 2 locks `chartPlan`. For synthetic-data runs, ask it after the synthetic-domain and synthetic-bundle cards. In auto mode, use the first compatible template-backed bundle as the default without adding another question.

```python
_TEMPLATE_CHART_BUNDLE_SEEDS = {
    "computer_ai_ml": [
        {
            "key": "rf_model_performance_report",
            "charts": ["grouped_bar", "scatter_regression", "residual_vs_fitted"],
            "families": ["ml_model_diagnostics", "forest", "scatter_regression", "marginal_joint"],
            "techniqueRefs": ["template-mining/07-techniques/ml-model-diagnostics.md", "template-mining/07-techniques/marginal-joint.md"],
            "anchors": ["期刊复现：基于随机森林(RF)的多维模型性能评估与预测残差可视化图谱_1777456409.md"],
            "en": ("Random-forest model report (Recommended)", "Clone the RF case when model/algorithm, train-test metrics, predicted-vs-actual, or residual columns are present: benchmark bar, parity scatter, residual panel."),
            "zh": ("随机森林模型报告套餐（推荐）", "当数据含 model/algorithm、训练测试指标、预测-真实值或残差字段时，直接复刻 RF 案例：指标横向柱、1:1 预测散点、残差面板。"),
        },
        {
            "key": "incremental_feature_selection_curve",
            "charts": ["line", "lollipop_horizontal", "scatter_regression"],
            "families": ["ml_model_diagnostics", "time_series_pi", "shap_composite"],
            "techniqueRefs": ["template-mining/07-techniques/ml-model-diagnostics.md", "template-mining/07-techniques/time-series-pi.md", "template-mining/07-techniques/shap-composite.md"],
            "anchors": ["拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272.md"],
            "en": ("Incremental feature-selection benchmark", "Use for feature-count, top-k, ablation, AUC/F1/accuracy, or multi-algorithm curves; preserve the RF-highlighted decision-point style."),
            "zh": ("增量特征选择 benchmark 套餐", "适合 feature-count、top-k、消融、AUC/F1/accuracy 或多算法曲线；保留 RF 高亮和决策拐点风格。"),
        },
        {
            "key": "rf_feature_importance_shap",
            "charts": ["lollipop_horizontal", "dotplot", "nested_donut", "heatmap_annotated"],
            "families": ["ml_model_diagnostics", "shap_composite"],
            "techniqueRefs": ["template-mining/07-techniques/ml-model-diagnostics.md", "template-mining/07-techniques/shap-composite.md"],
            "anchors": ["期刊复现：随机森林(RF)模型驱动的EFI特征重要度条形图与SHAP圆环图可视化_1777456510.md"],
            "en": ("RF feature importance + SHAP package", "Clone the EFI bar plus SHAP donut/composite layout when feature importance, SHAP, permutation, gain, or model interpretability fields appear."),
            "zh": ("RF 特征重要性 + SHAP 套餐", "当数据含特征重要性、SHAP、permutation、gain 或模型解释字段时，复刻 EFI 条形图 + SHAP 圆环/复合布局。"),
        },
        {
            "key": "pso_shap_optimization_framework",
            "charts": ["radar", "lollipop_horizontal", "heatmap_triangular", "pareto_chart"],
            "families": ["radar", "shap_composite", "heatmap_pairwise", "pareto"],
            "techniqueRefs": ["template-mining/07-techniques/radar.md", "template-mining/07-techniques/shap-composite.md", "template-mining/07-techniques/heatmap-pairwise.md", "template-mining/07-techniques/ml-model-diagnostics.md"],
            "anchors": ["基于PSO多目标优化与SHAP可解释分析的回归预测模型框架_1777461729.md"],
            "en": ("Optimization + explainability framework", "Use for PSO/NSGA/Pareto/multi-objective workflows that need model metrics, SHAP-style importance, correlation heatmaps, and Pareto panels."),
            "zh": ("优化 + 可解释框架套餐", "适合 PSO/NSGA/Pareto/多目标流程：模型指标、SHAP 重要性、相关性热图和 Pareto 面板。"),
        },
        {
            "key": "classifier_validation_board",
            "charts": ["roc", "pr_curve", "calibration", "forest"],
            "families": ["ml_model_diagnostics", "forest"],
            "techniqueRefs": ["template-mining/07-techniques/ml-model-diagnostics.md"],
            "anchors": ["拒绝默认配色：Python 绘制多模型性能对比图的进阶实战_1777451272.md"],
            "en": ("Classifier validation board", "Use for classifier probability, label, ROC-AUC, F1, precision/recall, calibration, or threshold tuning datasets."),
            "zh": ("分类器验证板套餐", "适合分类概率、标签、ROC-AUC、F1、precision/recall、校准或阈值调优数据。"),
        },
    ],
    "clinical_diagnostics_survival": [
        {
            "key": "clinical_survival_validation",
            "charts": ["km", "forest", "roc", "calibration"],
            "families": ["forest"],
            "techniqueRefs": ["template-mining/07-techniques/dual-axis.md"],
            "anchors": ["Python科研绘图复现_绘制多面板分组森林图展示生存分析风险比(HR)_1777453520.md"],
            "en": ("Clinical survival + validation package (Recommended)", "Template-backed KM/forest/ROC/calibration panels for cohort, survival, and diagnostic evidence."),
            "zh": ("临床生存+验证套餐（推荐）", "来自模板案例的 KM/森林图/ROC/校准曲线组合，适合队列、生存和诊断证据。"),
        },
        {
            "key": "clinical_prediction_diagnostic",
            "charts": ["scatter_regression", "residual_vs_fitted", "bland_altman", "histogram"],
            "families": ["marginal_joint", "density_scatter"],
            "techniqueRefs": ["template-mining/07-techniques/marginal-joint.md", "template-mining/07-techniques/inset-distribution.md"],
            "anchors": ["Python 科研绘图：如何优雅地展示“模型精度+稳定性”？顶刊可视化复盘_1777452458.md"],
            "en": ("Prediction diagnostic matrix", "Predicted-vs-actual hero panel with marginal densities, residual diagnostics, and metric boxes."),
            "zh": ("预测诊断矩阵套餐", "预测值-真实值主图配边缘密度、残差诊断和指标框，尽量复刻模板案例结构。"),
        },
        {
            "key": "clinical_effect_board",
            "charts": ["forest", "risk_ratio_plot", "decision_curve", "waterfall"],
            "families": ["forest"],
            "techniqueRefs": ["template-mining/07-techniques/dual-axis.md"],
            "anchors": ["Python科研绘图复现_绘制多面板分组森林图展示生存分析风险比(HR)_1777453520.md"],
            "en": ("Effect-size evidence board", "Forest/effect-size panels with clinical decision support charts when estimates are available."),
            "zh": ("效应量证据板套餐", "森林图/风险比/决策曲线组合，适合已有效应量、CI 或风险分层结果。"),
        },
    ],
    "genomics_transcriptomics": [
        {
            "key": "omics_discovery_story",
            "charts": ["volcano", "heatmap+cluster", "enrichment_dotplot", "pca"],
            "families": ["heatmap_pairwise", "heatmap"],
            "techniqueRefs": ["template-mining/07-techniques/heatmap-pairwise.md"],
            "anchors": ["期刊复现：Nature同款皮尔逊热力图_1777451326.md"],
            "en": ("Omics discovery package (Recommended)", "Volcano, clustered heatmap, enrichment, and PCA/embedding panels for discovery-to-validation stories."),
            "zh": ("组学发现套餐（推荐）", "火山图、聚类热图、富集点图和 PCA/embedding，适合发现到验证的多 panel 叙事。"),
        },
        {
            "key": "shap_explainability_composite",
            "charts": ["lollipop_horizontal", "dotplot", "heatmap_annotated", "correlation"],
            "families": ["shap_composite", "heatmap_pairwise"],
            "techniqueRefs": ["template-mining/07-techniques/shap-composite.md", "template-mining/07-techniques/heatmap-pairwise.md"],
            "anchors": ["复现顶刊 _ 拒绝千篇一律的SHAP图，用Matplotlib手绘一张“蜂群+条形”组合图_1777452577.md"],
            "en": ("SHAP explainability composite", "Bar/lollipop importance, beeswarm-like feature effects, annotated heatmap, and correlation context."),
            "zh": ("SHAP 解释复合套餐", "重要性条形/棒棒糖、蜂群式特征贡献、注释热图和相关性背景，优先按模板案例复刻。"),
        },
        {
            "key": "pairwise_correlation_matrix",
            "charts": ["heatmap_triangular", "correlation", "scatter_regression", "bubble_matrix"],
            "families": ["heatmap_pairwise", "marginal_joint"],
            "techniqueRefs": ["template-mining/07-techniques/heatmap-pairwise.md", "template-mining/07-techniques/marginal-joint.md"],
            "anchors": ["如何用 Python 完美复刻一张“红蓝气泡”相关性分析图_1777451587.md"],
            "en": ("Pairwise evidence matrix", "Triangular heatmap/correlation matrix with significance stars and lower-lane scatter diagnostics."),
            "zh": ("成对证据矩阵套餐", "三角热图/相关矩阵配显著性星标和散点诊断，适合多变量关联分析。"),
        },
    ],
    "materials_engineering": [
        {
            "key": "materials_prediction_stability",
            "charts": ["scatter_regression", "residual_vs_fitted", "histogram", "correlation"],
            "families": ["marginal_joint", "density_scatter"],
            "techniqueRefs": ["template-mining/07-techniques/marginal-joint.md", "template-mining/07-techniques/inset-distribution.md"],
            "anchors": ["复现 CEJ 顶刊神图 _ Python 绘制“密度散点+边缘直方图”多面板组合图_1777452838.md"],
            "en": ("CEJ-style prediction stability package (Recommended)", "Density-colored predicted-vs-actual panels with marginal distributions and residual/stability support panels."),
            "zh": ("CEJ 风格预测稳定性套餐（推荐）", "密度着色预测散点+边缘分布+残差/稳定性支持面板，尽量贴近 CEJ 模板案例。"),
        },
        {
            "key": "materials_model_explain_optimize",
            "charts": ["radar", "lollipop_horizontal", "heatmap_triangular", "pareto_chart"],
            "families": ["radar", "shap_composite", "heatmap_pairwise", "pareto"],
            "techniqueRefs": ["template-mining/07-techniques/radar.md", "template-mining/07-techniques/shap-composite.md", "template-mining/07-techniques/heatmap-pairwise.md", "template-mining/07-techniques/ml-model-diagnostics.md"],
            "anchors": ["基于PSO多目标优化与SHAP可解释分析的回归预测模型框架_1777461729.md"],
            "en": ("Model explainability + optimization package", "Radar metrics, SHAP-style importance, triangular heatmap, and Pareto optimization panels."),
            "zh": ("模型解释+优化套餐", "雷达指标、SHAP 风格重要性、三角热图和 Pareto 优化面板，适合材料/工程建模。"),
        },
        {
            "key": "materials_characterization_panel",
            "charts": ["xrd_pattern", "ftir_spectrum", "dsc_thermogram", "stress_strain"],
            "families": ["dual_axis", "time_series_pi"],
            "techniqueRefs": ["template-mining/07-techniques/dual-axis.md", "template-mining/07-techniques/time-series-pi.md"],
            "anchors": ["如何用Python绘制教科书级的双Y轴组合图_1777451702.md"],
            "en": ("Characterization + performance package", "XRD/FTIR/DSC/stress-strain panels for materials characterization and performance evidence."),
            "zh": ("表征+性能套餐", "XRD/FTIR/DSC/应力-应变多 panel，适合材料表征与性能证据链。"),
        },
    ],
    "_default": [
        {
            "key": "template_prediction_diagnostic",
            "charts": ["scatter_regression", "residual_vs_fitted", "bland_altman", "histogram"],
            "families": ["marginal_joint", "density_scatter"],
            "techniqueRefs": ["template-mining/07-techniques/marginal-joint.md"],
            "anchors": ["复现 CEJ 顶刊神图 _ Python 绘制“密度散点+边缘直方图”多面板组合图_1777452838.md"],
            "en": ("Template prediction diagnostic package (Recommended)", "A safe top-journal template for any numeric prediction or model-validation dataset."),
            "zh": ("模板预测诊断套餐（推荐）", "适合多数数值预测/模型验证数据的顶刊模板：密度散点、边缘分布、残差和指标框。"),
        },
        {
            "key": "template_shap_explainability",
            "charts": ["lollipop_horizontal", "dotplot", "heatmap_annotated", "correlation"],
            "families": ["shap_composite", "heatmap_pairwise"],
            "techniqueRefs": ["template-mining/07-techniques/shap-composite.md"],
            "anchors": ["复现顶刊 _ 拒绝千篇一律的SHAP图，用Matplotlib手绘一张“蜂群+条形”组合图_1777452577.md"],
            "en": ("Template SHAP/explainability package", "Use when columns imply feature importance, SHAP values, or model interpretability."),
            "zh": ("模板 SHAP/解释性套餐", "当数据包含特征重要性、SHAP 或模型解释字段时使用。"),
        },
        {
            "key": "template_pairwise_matrix",
            "charts": ["heatmap_triangular", "correlation", "scatter_regression", "bubble_matrix"],
            "families": ["heatmap_pairwise"],
            "techniqueRefs": ["template-mining/07-techniques/heatmap-pairwise.md"],
            "anchors": ["期刊复现：Nature同款皮尔逊热力图_1777451326.md"],
            "en": ("Template pairwise matrix package", "Use for multi-feature matrices, correlations, and association-heavy datasets."),
            "zh": ("模板成对矩阵套餐", "适合多变量矩阵、相关性和关联分析。"),
        },
    ],
}

_GENOMICS_BUNDLE_DOMAINS = {"genomics_transcriptomics", "single_cell_spatial", "proteomics_metabolomics", "immunology_cell_biology"}
_MATERIALS_BUNDLE_DOMAINS = {"materials_engineering", "ecology_environmental", "agriculture_food_science", "neuroscience_behavior", "psychology_social_science", "signal_processing_acoustics"}


def _template_bundle_domain_key(domain_family, custom_domain_text):
    effective = infer_domain_family_from_text(domain_family, custom_domain_text)
    if effective == "computer_ai_ml":
        return "computer_ai_ml"
    if effective == "clinical_diagnostics_survival":
        return "clinical_diagnostics_survival"
    if effective in _GENOMICS_BUNDLE_DOMAINS:
        return "genomics_transcriptomics"
    if effective in _MATERIALS_BUNDLE_DOMAINS:
        return "materials_engineering"
    return "_default"


def _normalize_template_bundle_entry(entry, language):
    lang = language if language in ("zh", "en") else "en"
    label, description = entry[lang]
    charts = list(entry["charts"])
    return {
        "label": label,
        "description": description,
        "bundleKey": entry["key"],
        "primaryChart": charts[0],
        "secondaryCharts": charts[1:],
        "templateFamilies": list(entry.get("families", [])),
        "templateAnchors": list(entry.get("anchors", [])),
        "techniqueRefs": list(entry.get("techniqueRefs", [])),
        "templateMatchMode": "clone_when_known",
    }


def _template_bundle_profile_tokens(context):
    profile = (context or {}).get("dataProfile") or {}
    roles = profile.get("semanticRoles") or {}
    columns = profile.get("columnNames") or profile.get("columns") or []
    patterns = profile.get("specialPatterns") or []
    selected_bundle = (context or {}).get("selectedChartBundle") or {}
    domain_hints = (context or {}).get("domainHints") or profile.get("domainHints") or {}
    tokens = [str(profile.get("structure", "")).lower()]
    tokens.extend(str(c).lower() for c in columns)
    tokens.extend(str(k).lower() for k in roles.keys())
    tokens.extend(str(v).lower() for v in roles.values())
    tokens.extend(str(p).lower() for p in patterns)
    tokens.extend(str((context or {}).get(k, "")).lower() for k in ("customDomainText", "syntheticDomainText", "selectedDomainFamily"))
    if isinstance(domain_hints, dict):
        tokens.extend(str(v).lower() for v in domain_hints.values())
    else:
        tokens.append(str(domain_hints).lower())
    if isinstance(selected_bundle, dict):
        tokens.extend(str(selected_bundle.get(k, "")).lower() for k in ("bundleKey", "label", "description"))
    df = profile.get("df")
    for role in ("model", "algorithm", "estimator", "method"):
        col = roles.get(role)
        if df is not None and col in getattr(df, "columns", []):
            try:
                tokens.extend(str(v).lower() for v in df[col].dropna().astype(str).unique()[:12])
            except Exception:
                pass
    return " ".join(tokens)


def _score_template_bundle_entry(entry, context):
    """Prefer the template package whose chart grammar is most compatible with the data profile."""
    text = _template_bundle_profile_tokens(context)
    key = entry.get("key", "")
    score = 0

    if any(t in text for t in ("actual", "predicted", "prediction", "residual", "rmse", "mae", "r2", "r_2")):
        if any(t in key for t in ("prediction", "diagnostic", "stability")):
            score += 30
    if any(t in text for t in ("rf", "rfr", "random forest", "randomforest", "xgboost", "lightgbm", "gbdt", "knn", "svm", "algorithm", "estimator")):
        if any(t in key for t in ("rf_", "model_performance", "classifier", "feature_selection")):
            score += 42
    if any(t in text for t in ("training", "testing", "train", "test", "validation", "cross_validation", "cv", "auc", "roc_auc", "accuracy", "f1", "precision", "recall")):
        if any(t in key for t in ("rf_model", "classifier", "feature_selection", "performance")):
            score += 32
    if any(t in text for t in ("shap", "importance", "feature_importance", "permutation", "explain")):
        if any(t in key for t in ("shap", "explain")):
            score += 35
        if any(t in key for t in ("rf_feature", "feature_selection")):
            score += 25
    if any(t in text for t in ("correlation", "corr", "matrix", "pvalue", "p_value", "padj", "fdr", "qvalue")):
        if any(t in key for t in ("pairwise", "matrix", "discovery")):
            score += 28
    if any(t in text for t in ("log2fc", "logfc", "fold_change", "gene", "pathway", "enrichment", "omics")):
        if "omics" in key or "discovery" in key:
            score += 30
    if any(t in text for t in ("survival", "event", "hazard", "hr", "ci_low", "ci_high", "roc", "auc")):
        if any(t in key for t in ("survival", "clinical", "effect")):
            score += 32
    if any(t in text for t in ("xrd", "ftir", "dsc", "stress", "strain", "spectrum", "spectra")):
        if "characterization" in key:
            score += 35
    if any(t in text for t in ("pareto", "objective", "multiobjective", "optimization", "radar")):
        if any(t in key for t in ("optimize", "optimization", "explain")):
            score += 25

    return score


def _rank_template_bundle_entries(entries, context):
    scored = []
    for index, entry in enumerate(entries):
        scored.append((_score_template_bundle_entry(entry, context), -index, entry))
    scored.sort(reverse=True)
    return [entry for _, _, entry in scored]


def _normalize_template_chart_bundle_options(options, fallback_options):
    """Preserve chart metadata from AI output; fall back if metadata is missing."""
    valid = []
    for option in options or []:
        if not isinstance(option, dict):
            continue
        label = option.get("label")
        description = option.get("description")
        primary = option.get("primaryChart")
        secondary = option.get("secondaryCharts") or option.get("charts", [])[1:]
        if label and description and primary:
            valid.append({
                "label": label,
                "description": description,
                "bundleKey": option.get("bundleKey") or option.get("key") or label,
                "primaryChart": primary,
                "secondaryCharts": list(secondary or []),
                "templateFamilies": list(option.get("templateFamilies") or option.get("families") or []),
                "templateAnchors": list(option.get("templateAnchors") or option.get("anchors") or []),
                "techniqueRefs": list(option.get("techniqueRefs") or []),
                "templateMatchMode": option.get("templateMatchMode") or "clone_when_known",
            })
    return valid[:3] if len(valid) >= 2 else fallback_options


def infer_template_chart_bundle_options(domain_family, custom_domain_text, language, context=None):
    """Return domain-matched chart-package options grounded in template-mining cases."""
    key = _template_bundle_domain_key(domain_family, custom_domain_text)
    entries = _TEMPLATE_CHART_BUNDLE_SEEDS.get(key, _TEMPLATE_CHART_BUNDLE_SEEDS["_default"])
    entries = _rank_template_bundle_entries(entries, context)
    fallback_options = [_normalize_template_bundle_entry(entry, language) for entry in entries]
    bundle_context = dict(context or {})
    bundle_context.update({
        "selectedDomainFamily": domain_family,
        "customDomainText": custom_domain_text,
        "effectiveBundleDomain": key,
        "fallbackTemplateBundles": fallback_options,
    })
    ai_options = generate_options_with_ai(bundle_context, "chart_bundle", fallback_options)
    return _normalize_template_chart_bundle_options(ai_options, fallback_options)


def resolve_chart_bundle_choice(selected_label, chart_bundle_options):
    """Resolve AskUserQuestion label back to the full template-backed bundle contract."""
    for option in chart_bundle_options or []:
        if option.get("label") == selected_label:
            return option
    return (chart_bundle_options or [None])[0]
```

## AI Option Generator

```python
def generate_options_with_ai(context, question_type, fallback_options):
    """Generate AskUserQuestion options dynamically using AI.

    context: dict with dataProfile, domainHints, journalProfile, IMPLEMENTED_CHARTS registry
    question_type: one of "domain", "chart_bundle", "layout", "palette", "synthetic_bundle", "journal_style"
    fallback_options: hardcoded list to use if AI generation fails

    Returns: list of option dicts. For most cards this is {label, description}; for
    chart_bundle and journal_style it must preserve metadata fields such as
    primaryChart, secondaryCharts, templateAnchors, techniqueRefs, journalName, and styleKey.
    """
    prompt = _build_option_prompt(context, question_type)
    try:
        ai_result = _call_option_generator(prompt, question_type, fallback_options)
        if ai_result and len(ai_result) >= 2:
            return ai_result[:5]
    except Exception:
        pass
    return fallback_options


def _build_option_prompt(context, question_type):
    context = context or {}
    domain = context.get("domainHints", {})
    if not isinstance(domain, dict):
        domain = {"selected": domain}
    profile = context.get("dataProfile", {})
    charts = context.get("IMPLEMENTED_CHARTS", [])
    journal = context.get("journalProfile", {})

    if question_type == "domain":
        return f"Given columns {profile.get('columns', [])} and sample data patterns, suggest 3-5 specific scientific domains. Return JSON array of {{label, description}}."
    if question_type == "chart_bundle":
        template_bundles = context.get("fallbackTemplateBundles", [])
        return (
            f"For domain {domain}, data with {profile.get('nObservations', 0)} rows and "
            f"{profile.get('nGroups', 0)} groups, suggest 2-3 chart bundles grounded in the "
            f"template-mining article cases. Prefer these template-backed seeds when compatible: {template_bundles}. "
            f"Available implemented charts: {charts}. If a known template family matches the data, keep its "
            f"chart composition and visual structure as close to the template case as possible. "
            f"Each option must include label, description, bundleKey, primaryChart, secondaryCharts, "
            f"templateFamilies, templateAnchors, techniqueRefs, and templateMatchMode='clone_when_known'. "
            f"Return JSON array."
        )
    if question_type == "layout":
        n_panels = context.get("panelCount", 2)
        return f"For {n_panels} panels in a {journal.get('style', 'nature')}-style figure, suggest 2-3 layout options. Return JSON array of {{label, description}}."
    if question_type == "palette":
        n_categories = profile.get("nGroups", 1)
        return f"For {n_categories} categories in {domain} domain, suggest 2-3 color palettes. Return JSON array of {{label, description}}."
    if question_type == "synthetic_bundle":
        return f"For {domain} domain, suggest 2-3 synthetic figure bundle types. Return JSON array of {{label, description}}."
    if question_type == "journal_style":
        selected_domain = (
            context.get("customDomainText")
            or context.get("selectedDomainFamily")
            or domain.get("selected")
            or domain.get("primary")
            or domain
        )
        effective_domain = context.get("effectiveDomainFamily") or domain.get("primary") or selected_domain
        fallback_seeds = context.get("fallbackJournalSeeds", [])
        language = context.get("language", "en")
        return (
            f"The user selected scientific domain: {selected_domain}. "
            f"Effective domain family: {effective_domain}. "
            f"Data profile: columns={profile.get('columns', [])}, "
            f"rows={profile.get('nObservations', 0)}, groups={profile.get('nGroups', 0)}. "
            f"Think like a domain-aware publication advisor. Suggest 2-3 top journals, conferences, "
            f"or venue families from this exact field for the final visual preference card. "
            f"Do not show generic Nature-like, Science-like, or Cell-like options unless the selected field itself "
            f"would reasonably target those broad journals. For audio/acoustic/signal domains, prefer venues such as "
            f"IEEE/ACM TASLP, JASA, IEEE TSP, Signal Processing, ICASSP, or Interspeech when appropriate. "
            f"Fallback seeds if the field is ambiguous: {fallback_seeds}. "
            f"Each option must include label, description, journalName, and styleKey. "
            f"styleKey must be one of field_top_journal, field_methods, field_compact, field_dense, nature, science, cell, lancet, nejm, jama. "
            f"Descriptions must explain why the venue matches the selected field and expected figure story. "
            f"Return JSON array of {{label, description, journalName, styleKey}} in {language}."
        )
    return ""


def _call_option_generator(prompt, question_type, fallback_options=None):
    """Generate options via AI with proper fallback chain.

    The coordinator may intercept this call and generate options inline via LLM.
    If not intercepted, returns fallback_options (or None if no fallback provided).
    """
    # Coordinator runtime protocol (when intercepted):
    # 1. Read _build_option_prompt output
    # 2. Construct inline prompt: "Generate 2-5 options as JSON array of {label, description}.\n{prompt}"
    # 3. Parse LLM response as JSON array
    # 4. If parsing fails or result has <2 items, fall through to fallback_options
    return fallback_options
```

## Card Definitions and Flow

All card option strings use a bilingual map so the same normalized answer works regardless of language. The base flow is:

1. Data-status card (file exists / synthetic / template)
2. Data-path card (only if file exists)
3. Mode card (free / interactive)
4. Synthetic-domain card (only if synthetic chosen)
5. Synthetic-bundle card (only if synthetic chosen)
6. Template chart-bundle card: ask "你希望生成哪类图表套餐？" with `infer_template_chart_bundle_options(...)`. For real-file interactive runs, ask this after Phase 1 domain inference and before Phase 2 locks `chartPlan`; for synthetic runs, ask it after synthetic-bundle selection; for auto mode, use the first compatible returned bundle without another user card.
7. Visual-preference card (4 questions: journal, color, resolution, crowding)

Before step 6, compute `chartBundleOptions = infer_template_chart_bundle_options(resolvedDomainFamily, customDomainText, lang, context={...})`. Include `dataProfile` in `context` whenever available so `_rank_template_bundle_entries()` can put the most compatible template case first. Pass only `{label, description}` into AskUserQuestion, but preserve the full option list in coordinator state so `primaryChart`, `secondaryCharts`, `templateAnchors`, and `techniqueRefs` survive into `workflowPreferences`.

Before step 7, compute `journalOptions = infer_journal_style_options(resolvedDomainFamily, customDomainText, lang, context={...})` and pass `{label, description}` from those exact options into the journal-style question. Preserve the full `journalOptions` list in coordinator state so `styleKey` is available when building `workflowPreferences`. Do not replace them with a static Nature/Science/Cell list.

### Bilingual Answer Maps

```python
DATA_STATUS_MAP = {
    "我已有数据文件（推荐）": "file_exists",
    "I have a data file (Recommended)": "file_exists",
    "没有数据，请先生成合成数据": "synthetic_data",
    "No data, generate synthetic data first": "synthetic_data",
    "我需要先定义模板": "template",
    "I need a template first": "template",
}

DATA_PATH_MAP = {
    "用 Other 粘贴路径（推荐）": "path_expected",
    "Use Other to paste path (Recommended)": "path_expected",
    "我需要先定义模板": "template",
    "I need a template first": "template",
}

MODE_MAP = {
    "自由模式（推荐）": "auto",
    "Free mode (Recommended)": "auto",
    "互动模式": "interactive",
    "Interactive": "interactive",
}

SYNTHETIC_DOMAIN_MAP = {
    "肿瘤/癌症研究（推荐）": "clinical_diagnostics_survival",
    "Tumor / cancer research (Recommended)": "clinical_diagnostics_survival",
    "计算机 / AI / 机器学习": "computer_ai_ml",
    "Computer / AI / machine learning": "computer_ai_ml",
    "组学/单细胞": "genomics_transcriptomics",
    "Omics / single-cell": "genomics_transcriptomics",
    "工程/生态/其他科学": "materials_engineering",
    "Engineering / ecology / other sciences": "materials_engineering",
}

DOMAIN_MAP = {
    "通用生物医学（推荐）": "general_biomedical",
    "General biomedical (Recommended)": "general_biomedical",
    "计算机 / AI / 机器学习": "computer_ai_ml",
    "Computer / AI / machine learning": "computer_ai_ml",
    "组学/单细胞": "genomics_transcriptomics",
    "Omics / single-cell": "genomics_transcriptomics",
    "工程/生态/其他科学": "materials_engineering",
    "Engineering / ecology / other sciences": "materials_engineering",
    "肿瘤/癌症研究（推荐）": "clinical_diagnostics_survival",
    "Tumor / cancer research (Recommended)": "clinical_diagnostics_survival",
    "临床/诊断": "clinical_diagnostics_survival",
    "Clinical / diagnostics": "clinical_diagnostics_survival",
}
```

### Card Option Templates

Each card's options are generated with language-aware labels. Use `preferredQuestionLanguage` to select the `"zh"` or `"en"` branch from each template.

```python
# Domain fallback options (for synthetic data flow)
DOMAIN_OPTIONS_TEMPLATE = [
    {"en": ("Tumor / cancer research (Recommended)", "Supports differential analysis, survival, response, and cohort-style figures"),
     "zh": ("肿瘤/癌症研究（推荐）", "支持差异分析、生存、疗效和队列类图表")},
    {"en": ("Computer / AI / machine learning", "Model performance, benchmark, SHAP, feature importance, algorithm comparison, and classifier/regressor validation"),
     "zh": ("计算机 / AI / 机器学习", "模型性能、benchmark、SHAP、特征重要性、算法对比和分类/回归验证")},
    {"en": ("Omics / single-cell", "Expression matrices, embeddings, abundance, pathway context"),
     "zh": ("组学/单细胞", "表达矩阵、embedding、丰度和通路背景")},
    {"en": ("Engineering / ecology / other sciences", "Materials, environment, agriculture, psychology, behavior, or any other non-medical domain; use Other for a precise field"),
     "zh": ("工程/生态/其他科学", "材料、环境、农业、心理、行为或其他非医学领域；精确领域请用 Other")},
]


def _localize_options(template, lang):
    """Convert a bilingual option template to {label, description} list."""
    language = lang if lang in ("zh", "en") else "en"
    return [{"label": t[language][0], "description": t[language][1]} for t in template]


# Visual preference card: palette options
PALETTE_OPTIONS_TEMPLATE = [
    {"en": ("Journal-safe muted (Recommended)", "Muted categorical colors with grayscale resilience"),
     "zh": ("期刊安全柔和配色（推荐）", "色盲友好，灰度打印也稳健")},
    {"en": ("Domain semantic", "Use risk, treatment, pathway, or state-driven mappings where helpful"),
     "zh": ("领域语义配色", "按风险、治疗、通路或状态映射颜色")},
    {"en": ("Strict grayscale-safe", "Maximize contrast for grayscale review and printing"),
     "zh": ("严格灰度安全", "优先满足黑白审稿和打印可读性")},
]

# Visual preference card: resolution options
RESOLUTION_OPTIONS_TEMPLATE = [
    {"en": ("300 dpi (Recommended)", "Good default for PNG and TIFF preview or submission assets"),
     "zh": ("300 dpi（推荐）", "适合 PNG/TIFF 预览和多数投稿资产")},
    {"en": ("600 dpi", "Sharper raster output for dense annotations or production requests"),
     "zh": ("600 dpi", "适合注释较密或生产级输出")},
    {"en": ("1200 dpi", "Maximum raster sharpness with larger file sizes"),
     "zh": ("1200 dpi", "最高栅格清晰度，但文件更大")},
]

# Visual preference card: crowding options
CROWDING_OPTIONS_TEMPLATE = [
    {"en": ("Auto simplify (Recommended)", "Prefer clarity by capping labels, sharing legends, and shrinking overloaded layouts automatically"),
     "zh": ("自动简化（推荐）", "优先清晰度，自动限制标签、共享图例并调整布局")},
    {"en": ("Preserve information", "Keep more labels and detail even if the figure becomes denser"),
     "zh": ("保留信息量", "尽量保留更多标签和细节，即使图更密")},
    {"en": ("Ask before simplify", "Flag crowding risks before major simplification"),
     "zh": ("简化前先询问", "重大简化前先提示拥挤风险")},
]
```

## Resolution Maps

```python
JOURNAL_STYLE_RESOLVE = {
    "Nature-like（推荐）": "nature", "Nature-like (Recommended)": "nature", "Nature-like": "nature",
    "Cell-like": "cell",
    "Science-like（推荐）": "science", "Science-like (Recommended)": "science", "Science-like": "science",
    "Lancet-like（临床推荐）": "lancet", "Lancet-like (Clinical recommended)": "lancet",
    "NEJM-like": "nejm", "JAMA-like": "jama",
    "Lancet-style (Clinical recommended)": "lancet", "NEJM-style": "nejm", "JAMA-style": "jama",
    "IEEE/ACM TASLP-style (Recommended)": "field_compact",
    "JASA-style": "field_methods",
    "IEEE TSP / Signal Processing-style": "field_compact",
    "Advanced Materials-style (Recommended)": "field_dense",
    "ACS Nano / Nano Letters-style": "field_compact",
    "Materials Today-style": "science",
    "Nature Genetics / Nature Methods-style (Recommended)": "nature",
    "Genome Biology-style": "field_methods",
    "Cell Genomics-style": "cell",
}


def resolve_journal_style_choice(selected_label, journal_options):
    """Resolve dynamic field-journal labels to a rendering style key."""
    for option in journal_options or []:
        if option.get("label") == selected_label:
            return option.get("styleKey", "field_top_journal")
    return JOURNAL_STYLE_RESOLVE.get(selected_label, "field_top_journal")

STORY_MODE_RESOLVE = {
    "单 panel": "single", "Single panel": "single",
    "对比双 panel（推荐）": "comparison_pair", "Comparison pair (Recommended)": "comparison_pair",
    "多 panel 故事板": "story_board_2x2", "Story board": "story_board_2x2",
}

MISSING_RESOLVE = {
    "删除缺失值（推荐）": "drop", "Drop missing (Recommended)": "drop",
    "警告但保留": "warn", "Warn but keep": "warn",
    "插补": "impute", "Impute": "impute",
}

COLOR_MODE_RESOLVE = {
    "期刊安全柔和配色（推荐）": "journal_safe_muted", "Journal-safe muted (Recommended)": "journal_safe_muted",
    "领域语义配色": "domain_semantic", "Domain semantic": "domain_semantic",
    "严格灰度安全": "strict_grayscale_safe", "Strict grayscale-safe": "strict_grayscale_safe",
}

DPI_RESOLVE = {
    "300 dpi（推荐）": 300, "300 dpi (Recommended)": 300,
    "600 dpi": 600, "1200 dpi": 1200,
}

CROWDING_RESOLVE = {
    "自动简化（推荐）": "auto_simplify", "Auto simplify (Recommended)": "auto_simplify",
    "保留信息量": "preserve_information", "Preserve information": "preserve_information",
    "简化前先询问": "ask_before_simplify", "Ask before simplify": "ask_before_simplify",
}

EXPORT_FORMATS_RESOLVE = {
    "矢量包（推荐）": ["pdf", "svg"], "Vector package (Recommended)": ["pdf", "svg"],
    "审阅包": ["pdf", "svg", "png"], "Review package": ["pdf", "svg", "png"],
    "栅格包": ["pdf", "png", "tiff"], "Raster package": ["pdf", "png", "tiff"],
}

STATS_RIGOR_RESOLVE = {
    "严格（推荐）": "strict", "Strict (Recommended)": "strict",
    "标准": "standard", "Standard": "standard",
    "仅描述": "descriptive", "Descriptive only": "descriptive",
}

PANEL_LAYOUT_RESOLVE = {
    "单 panel": "single", "Single panel": "single",
    "对比双 panel（推荐）": "1x2", "Comparison pair (Recommended)": "1x2",
    "多 panel 故事板": "2x2", "Story board": "2x2",
}
```

## Building `workflowPreferences`

After all cards are answered, assemble the final dict:

```python
workflowPreferences = {
    "interactionMode": modeChoice,
    "preferenceSource": "user_selected" if visualPreferencesRequired else "automatic_defaults",
    "allowFollowupPreferenceQuestions": visualPreferencesRequired,
    "syntheticDataRequested": syntheticDataRequested,
    "syntheticDomainFamily": syntheticPreferences.get("synthetic_domain_family"),
    "syntheticDomainText": syntheticPreferences.get("synthetic_domain_text"),
    "syntheticFigureBundle": syntheticPreferences.get("synthetic_bundle"),
    "selectedChartBundle": resolve_chart_bundle_choice(preferences.chart_bundle, chartBundleOptions),
    "chartBundleLabel": preferences.chart_bundle,
    "chartBundleOptions": chartBundleOptions,
    "journalStyle": resolve_journal_style_choice(preferences.journal, journalOptions),
    "journalStyleLabel": preferences.journal,
    "journalStyleOptions": journalOptions,
    "domainFamily": resolvedDomainFamily,
    "customDomainText": customDomainText,
    "storyMode": STORY_MODE_RESOLVE.get(preferences.story, "hero_plus_stacked_support"),
    "missingHandling": MISSING_RESOLVE.get(preferences.missing, "drop"),
    "colorMode": COLOR_MODE_RESOLVE.get(preferences.color, "journal_safe_muted"),
    "rasterDpi": DPI_RESOLVE.get(preferences.resolution, 300),
    "crowdingPolicy": CROWDING_RESOLVE.get(preferences.crowding, "auto_simplify"),
    "overlapPriority": "clarity_first",
    "exportFormats": EXPORT_FORMATS_RESOLVE.get(preferences.export_bundle, ["pdf", "svg"]),
    "statsRigor": STATS_RIGOR_RESOLVE.get(preferences.stats, "strict"),
    "panelLayout": PANEL_LAYOUT_RESOLVE.get(preferences.story, "2x2-hero-span"),
}
```
