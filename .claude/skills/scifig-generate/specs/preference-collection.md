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
    if any(k in text for k in ("material", "polymer", "alloy", "engineering")):
        return "materials_engineering"
    if any(k in text for k in ("ecology", "environment", "biodiversity", "climate", "marine")):
        return "ecology_environmental"
    if any(k in text for k in ("agriculture", "crop", "yield", "food", "sensory")):
        return "agriculture_food_science"
    if any(k in text for k in ("psychology", "survey", "likert", "social", "education")):
        return "psychology_social_science"
    return "general_biomedical"
```

## Domain-to-Journal-Style Mapping

Each domain family maps to a ranked list of journal-style options. Language is handled by a single lookup; no duplicated branches.

```python
_JOURNAL_STYLE_BY_DOMAIN = {
    "clinical_diagnostics_survival": [
        {"en": ("Lancet-like (Clinical recommended)", "Clinical evidence, cohort, survival, and translational medical figures"),
         "zh": ("Lancet-like（临床推荐）", "适合临床证据、队列、生存和转化医学图表")},
        {"en": ("NEJM-like", "High-impact clinical trial, outcome, and medical research figures"),
         "zh": ("NEJM-like", "适合高影响临床试验、结局和医学研究")},
        {"en": ("JAMA-like", "Diagnostic accuracy, validation studies, and precise labeling"),
         "zh": ("JAMA-like", "适合诊断准确性、验证研究和清晰标签")},
    ],
    "genomics_transcriptomics": [
        {"en": ("Nature-like (Recommended)", "Submission-safe multi-panel figures for omics, mechanism, and discovery work"),
         "zh": ("Nature-like（推荐）", "适合组学、机制发现和投稿安全的多 panel 科研图")},
        {"en": ("Cell-like", "Mechanism narrative, cell states, and story-first multi-panel figures"),
         "zh": ("Cell-like", "适合机制叙事、细胞状态和故事驱动组图")},
        {"en": ("Science-like", "Compact, low-ink, fast-scanning high-impact figures"),
         "zh": ("Science-like", "适合紧凑、低墨量、快速阅读的高影响图表")},
    ],
    "materials_engineering": [
        {"en": ("Science-like (Recommended)", "Compact cross-disciplinary figures for engineering, ecology, or social science"),
         "zh": ("Science-like（推荐）", "适合跨学科、工程、生态或社会科学的紧凑表达")},
        {"en": ("Nature-like", "Submission-safe spacing and restrained general scientific figure style"),
         "zh": ("Nature-like", "适合投稿安全、克制留白和通用科研图")},
        {"en": ("Cell-like", "Story-led multi-panel results when narrative structure matters"),
         "zh": ("Cell-like", "适合需要更强故事线的多 panel 结果")},
    ],
    "_default": [
        {"en": ("Nature-like (Recommended)", "Submission-safe restrained defaults for most scientific figures"),
         "zh": ("Nature-like（推荐）", "投稿安全、留白克制、适合多数科研图")},
        {"en": ("Science-like", "Compact, low-ink, fast-scanning figures"),
         "zh": ("Science-like", "紧凑、低墨量、便于快速阅读")},
        {"en": ("Cell-like", "Story-first multi-panel organization"),
         "zh": ("Cell-like", "强调叙事和多 panel 组织")},
    ],
}

# Domains that share the genomics journal-style set
_GENOMICS_LIKE_DOMAINS = {"genomics_transcriptomics", "single_cell_spatial", "proteomics_metabolomics", "immunology_cell_biology"}
# Domains that share the materials journal-style set
_CROSS_DISCIPLINE_DOMAINS = {"materials_engineering", "ecology_environmental", "agriculture_food_science", "psychology_social_science", "neuroscience_behavior"}


def infer_journal_style_options(domain_family, custom_domain_text, language):
    """Return list of {label, description} dicts for the journal-style card."""
    effective_domain = infer_domain_family_from_text(domain_family, custom_domain_text)
    lang = language if language in ("zh", "en") else "en"

    if effective_domain == "clinical_diagnostics_survival":
        entries = _JOURNAL_STYLE_BY_DOMAIN["clinical_diagnostics_survival"]
    elif effective_domain in _GENOMICS_LIKE_DOMAINS:
        entries = _JOURNAL_STYLE_BY_DOMAIN["genomics_transcriptomics"]
    elif effective_domain in _CROSS_DISCIPLINE_DOMAINS:
        entries = _JOURNAL_STYLE_BY_DOMAIN["materials_engineering"]
    else:
        entries = _JOURNAL_STYLE_BY_DOMAIN["_default"]

    return [{"label": e[lang][0], "description": e[lang][1]} for e in entries]
```

## Synthetic Bundle Options

```python
_BUNDLE_BY_DOMAIN = {
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

    if effective == "genomics_transcriptomics":
        entries = _BUNDLE_BY_DOMAIN["genomics_transcriptomics"]
    elif effective == "clinical_diagnostics_survival":
        entries = _BUNDLE_BY_DOMAIN["clinical_diagnostics_survival"]
    else:
        entries = _BUNDLE_BY_DOMAIN["_default"]

    return [{"label": e[lang][0], "description": e[lang][1]} for e in entries]
```

## AI Option Generator

```python
def generate_options_with_ai(context, question_type, fallback_options):
    """Generate AskUserQuestion options dynamically using AI.

    context: dict with dataProfile, domainHints, journalProfile, IMPLEMENTED_CHARTS registry
    question_type: one of "domain", "chart_bundle", "layout", "palette", "synthetic_bundle"
    fallback_options: hardcoded list to use if AI generation fails

    Returns: list of {label, description} dicts (2-5 items)
    """
    prompt = _build_option_prompt(context, question_type)
    try:
        ai_result = _call_option_generator(prompt, question_type)
        if ai_result and len(ai_result) >= 2:
            return ai_result[:5]
    except Exception:
        pass
    return fallback_options


def _build_option_prompt(context, question_type):
    domain = context.get("domainHints", {})
    profile = context.get("dataProfile", {})
    charts = context.get("IMPLEMENTED_CHARTS", [])
    journal = context.get("journalProfile", {})

    if question_type == "domain":
        return f"Given columns {profile.get('columns', [])} and sample data patterns, suggest 3-5 specific scientific domains. Return JSON array of {{label, description}}."
    if question_type == "chart_bundle":
        return f"For domain {domain}, data with {profile.get('nObservations', 0)} rows and {profile.get('nGroups', 0)} groups, suggest 2-3 chart bundles. Each bundle: primaryChart + 1-3 secondaryCharts. Available charts: {charts}. Return JSON array of {{label, description}}."
    if question_type == "layout":
        n_panels = context.get("panelCount", 2)
        return f"For {n_panels} panels in a {journal.get('style', 'nature')}-style figure, suggest 2-3 layout options. Return JSON array of {{label, description}}."
    if question_type == "palette":
        n_categories = profile.get("nGroups", 1)
        return f"For {n_categories} categories in {domain} domain, suggest 2-3 color palettes. Return JSON array of {{label, description}}."
    if question_type == "synthetic_bundle":
        return f"For {domain} domain, suggest 2-3 synthetic figure bundle types. Return JSON array of {{label, description}}."
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

All card option strings use a bilingual map so the same normalized answer works regardless of language. The flow is:

1. Data-status card (file exists / synthetic / template)
2. Data-path card (only if file exists)
3. Mode card (free / interactive)
4. Synthetic-domain card (only if synthetic chosen)
5. Synthetic-bundle card (only if synthetic chosen)
6. Visual-preference card (4 questions: journal, color, resolution, crowding)

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
    "组学/单细胞": "genomics_transcriptomics",
    "Omics / single-cell": "genomics_transcriptomics",
    "工程/生态/其他科学": "materials_engineering",
    "Engineering / ecology / other sciences": "materials_engineering",
}

DOMAIN_MAP = {
    "通用生物医学（推荐）": "general_biomedical",
    "General biomedical (Recommended)": "general_biomedical",
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
}

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
    "journalStyle": JOURNAL_STYLE_RESOLVE.get(preferences.journal, "custom"),
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
