---
name: scifig-generate
description: Upload experimental data (CSV/Excel/matrix), auto-detect structure, infer scientific domain, recommend publication-grade charts, generate Nature/Cell/Science-aligned figure code, optimize multi-panel composition and palette systems, and export vector graphics with statistical reports. Triggers on "generate figure", "plot data", "sci figure", "科研图", "画图", "多 panel".
allowed-tools: Agent, AskUserQuestion, TodoWrite, Read, Write, Edit, Bash, Glob, Grep
---
# SciFig Generate

End-to-end workflow for turning real experimental data into submission-ready scientific figures. The skill is journal-token driven, domain-aware, and narrative-first: it reads the data, infers the scientific context, picks chart families and statistics, builds a multi-panel story when needed, and exports reproducible code plus publication assets.

## Architecture Overview

```text
+-----------------------------------------------------------------------------------+
| scifig-generate (Orchestrator)                                                    |
| -> collect preferences -> load references -> dispatch phases -> iterate on demand |
+----------------------+----------------------+----------------------+---------------+
                       |                      |                      |
                       v                      v                      v
                +-------------+        +-------------+        +-------------+
                | Phase 1     |        | Phase 2     |        | Phase 3     |
                | Data Detect |        | Charts+Stat |        | Code+Style  |
                +------+------+        +------+------+        +------+------+
                       |                      |                      |
                       v                      v                      v
                  dataProfile           chartPlan +             styledCode +
                + domainHints         panelBlueprint           journalProfile
                + panelCandidates      + palettePlan           + colorSystem
                       \                      |                      /
                        \                     v                     /
                         \              +-------------+            /
                          ------------> | Phase 4     | <----------
                                        | Export      |
                                        +------+------+
                                               |
                                               v
                                          outputBundle
```

## Key Design Principles

1. **Journal-token driven**: Use explicit style profiles instead of ad-hoc plotting choices. Nature dimensions are grounded in the official Nature figure guide; Cell-like and Science-like presets maintain the same production-safe discipline.
2. **Domain-aware charting**: Infer likely domains such as genomics, single-cell, pharmacology, neuroscience, or clinical survival and bias chart recommendations toward the conventions of that field.
3. **Narrative multi-panel design**: Treat multi-panel figures as a story with hero, support, validation, and mechanism panels rather than a loose grid of unrelated plots.
4. **Palette governance**: Prefer restrained, colorblind-safe palettes; keep semantic mappings consistent across panels; avoid rainbow and uncontrolled red-green contrasts.
5. **Statistical honesty**: No inferential claims without replicate or cohort meaning. When data only support descriptive visualization, say so.
6. **Reproducibility-first**: Every figure should be exportable as code plus metadata, source-data manifests, and methods-ready statistical descriptions.

## Interactive Preference Collection

Collect workflow preferences before dispatching to phases, but treat data availability, file-path validation, and mode selection as separate gates.

- Never use Bash, Glob, Grep, or Read to scan the workspace for candidate CSV, TSV, XLSX, or XLS files.
- Never assume files under `tests/`, `output/`, fixtures, or nearby folders are the user's real data.
- Mirror the user's language in all AskUserQuestion cards. If the request is Chinese, use Chinese cards from the start.
- If the user did not explicitly provide `FILE:` or a concrete file path, first use AskUserQuestion to ask whether a data file already exists.
- If the user says a file exists, use a second AskUserQuestion card to ask where it is. Tell the user to choose Other and paste the exact path there so the answer still appears under `User answered Claude's questions`.
- If the path card comes back with the canned option label instead of a real path, ask one direct follow-up for the exact path and stop there.
- Only accept concrete file paths ending in `.csv`, `.tsv`, `.xlsx`, or `.xls`. If the reply is a directory, a folder-like path, or anything without one of those suffixes, ask again and stop there.
- Never run Bash, Read, Grep, or directory inspection on a provided path before both the file-path gate and the mode gate are complete.
- Mode selection is a separate gate after the data-status decision, and after the file path only when a real file already exists. Never infer `auto` from any answer that is not an exact mode-card selection, and never fall through to auto defaults after an invalid answer.
- If the user answers a card with a localization request such as `请用中文`, treat it as a language-switch request, re-issue the same card in Chinese, and do not consume it as a data or mode decision.
- If the user does not have data yet, branch explicitly: either help define a schema/template first, or generate a synthetic dataset only if the user explicitly asks for simulated data. Custom domains entered through Other must be preserved and must not collapse back to biomedical defaults.
- AskUserQuestion payloads must stay tool-compatible: every question needs `id`, `header`, `question`, and 2-3 options. Do not use `multiSelect`. Use 1-3 questions per card by default; the final visual preference card is the only permitted 4-question exception because journal style, color, resolution, and crowding must be answered together. The journal-style options in that card must be inferred from the selected or custom scientific domain before the card is shown.

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


def infer_journal_style_options(domain_family, custom_domain_text, language):
    effective_domain = infer_domain_family_from_text(domain_family, custom_domain_text)
    if language == "zh":
        if effective_domain == "clinical_diagnostics_survival":
            return [
                {"label": "Lancet-like（临床推荐）", "description": "适合临床证据、队列、生存和转化医学图表"},
                {"label": "NEJM-like", "description": "适合高影响临床试验、结局和医学研究"},
                {"label": "JAMA-like", "description": "适合诊断准确性、验证研究和清晰标签"}
            ]
        if effective_domain in ("genomics_transcriptomics", "single_cell_spatial", "proteomics_metabolomics", "immunology_cell_biology"):
            return [
                {"label": "Nature-like（推荐）", "description": "适合组学、机制发现和投稿安全的多 panel 科研图"},
                {"label": "Cell-like", "description": "适合机制叙事、细胞状态和故事驱动组图"},
                {"label": "Science-like", "description": "适合紧凑、低墨量、快速阅读的高影响图表"}
            ]
        if effective_domain in ("materials_engineering", "ecology_environmental", "agriculture_food_science", "psychology_social_science", "neuroscience_behavior"):
            return [
                {"label": "Science-like（推荐）", "description": "适合跨学科、工程、生态或社会科学的紧凑表达"},
                {"label": "Nature-like", "description": "适合投稿安全、克制留白和通用科研图"},
                {"label": "Cell-like", "description": "适合需要更强故事线的多 panel 结果"}
            ]
        return [
            {"label": "Nature-like（推荐）", "description": "投稿安全、留白克制、适合多数科研图"},
            {"label": "Science-like", "description": "紧凑、低墨量、便于快速阅读"},
            {"label": "Cell-like", "description": "强调叙事和多 panel 组织"}
        ]

    if effective_domain == "clinical_diagnostics_survival":
        return [
            {"label": "Lancet-like (Clinical recommended)", "description": "Clinical evidence, cohort, survival, and translational medical figures"},
            {"label": "NEJM-like", "description": "High-impact clinical trial, outcome, and medical research figures"},
            {"label": "JAMA-like", "description": "Diagnostic accuracy, validation studies, and precise labeling"}
        ]
    if effective_domain in ("genomics_transcriptomics", "single_cell_spatial", "proteomics_metabolomics", "immunology_cell_biology"):
        return [
            {"label": "Nature-like (Recommended)", "description": "Submission-safe multi-panel figures for omics, mechanism, and discovery work"},
            {"label": "Cell-like", "description": "Mechanism narrative, cell states, and story-first multi-panel figures"},
            {"label": "Science-like", "description": "Compact, low-ink, fast-scanning high-impact figures"}
        ]
    if effective_domain in ("materials_engineering", "ecology_environmental", "agriculture_food_science", "psychology_social_science", "neuroscience_behavior"):
        return [
            {"label": "Science-like (Recommended)", "description": "Compact cross-disciplinary figures for engineering, ecology, or social science"},
            {"label": "Nature-like", "description": "Submission-safe spacing and restrained general scientific figure style"},
            {"label": "Cell-like", "description": "Story-led multi-panel results when narrative structure matters"}
        ]
    return [
        {"label": "Nature-like (Recommended)", "description": "Submission-safe restrained defaults for most scientific figures"},
        {"label": "Science-like", "description": "Compact, low-ink, fast-scanning figures"},
        {"label": "Cell-like", "description": "Story-first multi-panel organization"}
    ]


def infer_synthetic_bundle_options(domain_family, custom_domain_text, language):
    if language == "zh":
        if domain_family == "genomics_transcriptomics":
            return [
                {"label": "组学发现图表集（推荐）", "description": "差异分析、热图、富集、PCA/UMAP"},
                {"label": "单细胞/空间图表集", "description": "embedding、组成、表达、空间或细胞类型面板"},
                {"label": "机制验证图表集", "description": "表达、通路和验证实验组合"}
            ]
        if domain_family == "clinical_diagnostics_survival":
            return [
                {"label": "转化医学图表集（推荐）", "description": "生存、ROC、分层、疗效和队列概览"},
                {"label": "机制验证图表集", "description": "机制、标志物和验证实验组合"},
                {"label": "综合科研图表集", "description": "覆盖发现、验证和背景说明"}
            ]
        return [
            {"label": "领域通用图表集（推荐）", "description": "适配用户输入或选定领域的核心图表"},
            {"label": "机制/过程图表集", "description": "强调过程、机制、时间或实验条件变化"},
            {"label": "对比/趋势图表集", "description": "强调组间比较、趋势、分布和相关性"}
        ]

    if domain_family == "genomics_transcriptomics":
        return [
            {"label": "Omics discovery set (Recommended)", "description": "Differential analysis, heatmap, enrichment, PCA/UMAP"},
            {"label": "Single-cell / spatial set", "description": "Embedding, composition, expression, spatial or cell-type panels"},
            {"label": "Mechanism-focused set", "description": "Expression, pathway, and validation-heavy figures"}
        ]
    if domain_family == "clinical_diagnostics_survival":
        return [
            {"label": "Clinical translational set (Recommended)", "description": "Survival, ROC, stratification, efficacy, and cohort overview"},
            {"label": "Mechanism-focused set", "description": "Mechanism, biomarker, and validation-heavy figures"},
            {"label": "Integrated figure set", "description": "Discovery, validation, and context in one publication-ready bundle"}
        ]
    return [
        {"label": "Domain-general figure set (Recommended)", "description": "Core figures adapted to the user-selected or custom domain"},
        {"label": "Process / mechanism set", "description": "Process, mechanism, time, or experimental-condition changes"},
        {"label": "Comparison / trend set", "description": "Group comparisons, trends, distributions, and correlations"}
    ]


inputFilePath = extracted_file_path if user_input already includes FILE: or a concrete local data path else None
syntheticDataRequested = False
syntheticPreferences = {}
modeChoice = None

if inputFilePath is None:
    dataStatus = AskUserQuestion(questions=[
        {
            "id": "data_status",
            "header": "数据" if preferredQuestionLanguage == "zh" else "Data",
            "question": "您是否已有数据文件用于生成科研图表？" if preferredQuestionLanguage == "zh" else "Do you already have a data file for generating the scientific figure?",
            "options": [
                {"label": "我已有数据文件（推荐）" if preferredQuestionLanguage == "zh" else "I have a data file (Recommended)", "description": "已有 CSV、TSV、XLSX 或 XLS 文件，SciFig 可以读取" if preferredQuestionLanguage == "zh" else "A CSV, TSV, XLSX, or XLS file already exists and SciFig can read it"},
                {"label": "没有数据，请先生成合成数据" if preferredQuestionLanguage == "zh" else "No data, generate synthetic data first", "description": "先创建合成数据集，再基于它生成图表" if preferredQuestionLanguage == "zh" else "Create a synthetic dataset first, then generate figures from it"},
                {"label": "我需要先定义模板" if preferredQuestionLanguage == "zh" else "I need a template first", "description": "先定义字段结构或示例表格，不立即绘图" if preferredQuestionLanguage == "zh" else "Define the expected schema or example table before plotting"}
            ]
        }
    ])

    statusChoice = normalize_card_answer(dataStatus.data_status, {
        "我已有数据文件（推荐）": "file_exists",
        "I have a data file (Recommended)": "file_exists",
        "没有数据，请先生成合成数据": "synthetic_data",
        "No data, generate synthetic data first": "synthetic_data",
        "我需要先定义模板": "template",
        "I need a template first": "template",
    })
    if statusChoice == "__language_switch__" and preferredQuestionLanguage != "zh":
        preferredQuestionLanguage = "zh"
        re-ask the same data_status card in Chinese and stop there
    elif statusChoice == "template":
        stop before Phase 1 and switch to schema/template guidance
    elif statusChoice == "synthetic_data":
        syntheticDataRequested = True
    elif statusChoice == "file_exists":
        dataPathResponse = AskUserQuestion(questions=[
            {
                "id": "data_path_capture",
                "header": "文件路径" if preferredQuestionLanguage == "zh" else "File path",
                "question": "数据文件在哪里？请选择 Other 并粘贴完整路径。" if preferredQuestionLanguage == "zh" else "Where is the data file? Choose Other and paste the exact file path.",
                "options": [
                    {"label": "用 Other 粘贴路径（推荐）" if preferredQuestionLanguage == "zh" else "Use Other to paste path (Recommended)", "description": "选择 Other 后输入完整的 CSV、TSV、XLSX 或 XLS 本地路径" if preferredQuestionLanguage == "zh" else "Select Other and enter the full local CSV, TSV, XLSX, or XLS path"},
                    {"label": "我需要先定义模板" if preferredQuestionLanguage == "zh" else "I need a template first", "description": "还没有真实文件路径，切换到结构模板指导" if preferredQuestionLanguage == "zh" else "No real file path yet; switch to schema/template guidance"}
                ]
            }
        ])

        pathChoice = normalize_card_answer(dataPathResponse.data_path_capture, {
            "用 Other 粘贴路径（推荐）": "path_expected",
            "Use Other to paste path (Recommended)": "path_expected",
            "我需要先定义模板": "template",
            "I need a template first": "template",
        })
        if pathChoice == "__language_switch__" and preferredQuestionLanguage != "zh":
            preferredQuestionLanguage = "zh"
            re-ask the same data_path_capture card in Chinese and stop there
        elif pathChoice == "template":
            stop before Phase 1 and switch to schema/template guidance
        elif pathChoice == "path_expected":
            ask one direct follow-up for the exact file path because the UI returned the canned option label, then stop there
        else:
            pathCandidate = dataPathResponse.data_path_capture
            if not is_concrete_data_file_path(pathCandidate):
                ask one direct follow-up for the exact CSV, TSV, XLSX, or XLS file path and stop there
            inputFilePath = pathCandidate
    else:
        re-ask the same data_status card once and stop there

if not syntheticDataRequested and not inputFilePath:
    stop before Phase 1 and switch to schema/template guidance

modeResponse = AskUserQuestion(questions=[
    {
        "id": "mode",
        "header": "模式" if preferredQuestionLanguage == "zh" else "Mode",
        "question": "您希望 SciFig 以什么模式工作？" if preferredQuestionLanguage == "zh" else "How should SciFig work?",
        "options": [
            {"label": "自由模式（推荐）" if preferredQuestionLanguage == "zh" else "Free mode (Recommended)", "description": "根据数据和目标自动规划，尽量少追问" if preferredQuestionLanguage == "zh" else "Plan automatically from the data and goal, with minimal follow-up questions"},
            {"label": "互动模式" if preferredQuestionLanguage == "zh" else "Interactive", "description": "先确认关键偏好，再进入图表或合成数据规划" if preferredQuestionLanguage == "zh" else "Confirm preferences first, then continue into figure or synthetic-data planning"}
        ]
    }
])

modeChoice = normalize_card_answer(modeResponse.mode, {
    "自由模式（推荐）": "auto",
    "Free mode (Recommended)": "auto",
    "互动模式": "interactive",
    "Interactive": "interactive",
})
if modeChoice == "__language_switch__" and preferredQuestionLanguage != "zh":
    preferredQuestionLanguage = "zh"
    re-ask the same mode card in Chinese and stop there
elif modeChoice == "__invalid__":
    re-ask the same mode card once and stop there

if syntheticDataRequested:
    syntheticDomainResponse = AskUserQuestion(questions=[
        {
            "id": "synthetic_domain",
            "header": "领域" if preferredQuestionLanguage == "zh" else "Domain",
            "question": "合成数据应代表哪个科学领域？" if preferredQuestionLanguage == "zh" else "Which scientific domain should the synthetic data represent?",
            "options": [
                {"label": "肿瘤/癌症研究（推荐）" if preferredQuestionLanguage == "zh" else "Tumor / cancer research (Recommended)", "description": "支持差异分析、生存、疗效和队列类图表" if preferredQuestionLanguage == "zh" else "Supports differential analysis, survival, response, and cohort-style figures"},
                {"label": "组学/单细胞" if preferredQuestionLanguage == "zh" else "Omics / single-cell", "description": "表达矩阵、embedding、丰度和通路背景" if preferredQuestionLanguage == "zh" else "Expression matrices, embeddings, abundance, pathway context"},
                {"label": "工程/生态/其他科学" if preferredQuestionLanguage == "zh" else "Engineering / ecology / other sciences", "description": "材料、环境、农业、心理、行为或其他非医学领域；精确领域请用 Other" if preferredQuestionLanguage == "zh" else "Materials, environment, agriculture, psychology, behavior, or any other non-medical domain; use Other for a precise field"}
            ]
        }
    ])

    syntheticDomainFamily, syntheticDomainText = resolve_domain_answer(syntheticDomainResponse.synthetic_domain, {
        "肿瘤/癌症研究（推荐）": "clinical_diagnostics_survival",
        "Tumor / cancer research (Recommended)": "clinical_diagnostics_survival",
        "组学/单细胞": "genomics_transcriptomics",
        "Omics / single-cell": "genomics_transcriptomics",
        "工程/生态/其他科学": "materials_engineering",
        "Engineering / ecology / other sciences": "materials_engineering",
    })

    journalStyleOptions = infer_journal_style_options(
        domain_family=syntheticDomainFamily,
        custom_domain_text=syntheticDomainText,
        language=preferredQuestionLanguage,
    )

    syntheticBundleOptions = infer_synthetic_bundle_options(
        domain_family=syntheticDomainFamily,
        custom_domain_text=syntheticDomainText,
        language=preferredQuestionLanguage,
    )

    syntheticBundleResponse = AskUserQuestion(questions=[
        {
            "id": "synthetic_bundle",
            "header": "图表集" if preferredQuestionLanguage == "zh" else "Bundle",
            "question": "合成数据应支持哪类图表集？" if preferredQuestionLanguage == "zh" else "Which figure bundle should the synthetic data support?",
            "options": syntheticBundleOptions
        }
    ])

    syntheticPreferences = {
        "synthetic_domain_raw": syntheticDomainResponse.synthetic_domain,
        "synthetic_domain_family": syntheticDomainFamily,
        "synthetic_domain_text": syntheticDomainText,
        "synthetic_bundle": syntheticBundleResponse.synthetic_bundle,
    }

else:
    journalStyleOptions = infer_journal_style_options(
        domain_family="general_biomedical",
        custom_domain_text=None,
        language=preferredQuestionLanguage,
    )

visualPreferencesRequired = syntheticDataRequested or modeChoice == "interactive"

if visualPreferencesRequired:
    pref_visual = AskUserQuestion(questions=[
        {
            "id": "journal",
            "header": "期刊" if preferredQuestionLanguage == "zh" else "Journal",
            "question": "您希望图表最接近哪种期刊风格？" if preferredQuestionLanguage == "zh" else "Which journal style family is closest to what you want?",
            "options": journalStyleOptions
        },
        {
            "id": "color",
            "header": "颜色" if preferredQuestionLanguage == "zh" else "Color",
            "question": "颜色方案偏好是什么？" if preferredQuestionLanguage == "zh" else "Which color system should SciFig favor?",
            "options": [
                {"label": "期刊安全柔和配色（推荐）" if preferredQuestionLanguage == "zh" else "Journal-safe muted (Recommended)", "description": "色盲友好，灰度打印也稳健" if preferredQuestionLanguage == "zh" else "Muted categorical colors with grayscale resilience"},
                {"label": "领域语义配色" if preferredQuestionLanguage == "zh" else "Domain semantic", "description": "按风险、治疗、通路或状态映射颜色" if preferredQuestionLanguage == "zh" else "Use risk, treatment, pathway, or state-driven mappings where helpful"},
                {"label": "严格灰度安全" if preferredQuestionLanguage == "zh" else "Strict grayscale-safe", "description": "优先满足黑白审稿和打印可读性" if preferredQuestionLanguage == "zh" else "Maximize contrast for grayscale review and printing"}
            ]
        },
        {
            "id": "resolution",
            "header": "分辨率" if preferredQuestionLanguage == "zh" else "Resolution",
            "question": "导出分辨率希望是多少？" if preferredQuestionLanguage == "zh" else "Which raster export resolution should SciFig target?",
            "options": [
                {"label": "300 dpi（推荐）" if preferredQuestionLanguage == "zh" else "300 dpi (Recommended)", "description": "适合 PNG/TIFF 预览和多数投稿资产" if preferredQuestionLanguage == "zh" else "Good default for PNG and TIFF preview or submission assets"},
                {"label": "600 dpi", "description": "适合注释较密或生产级输出" if preferredQuestionLanguage == "zh" else "Sharper raster output for dense annotations or production requests"},
                {"label": "1200 dpi", "description": "最高栅格清晰度，但文件更大" if preferredQuestionLanguage == "zh" else "Maximum raster sharpness with larger file sizes"}
            ]
        },
        {
            "id": "crowding",
            "header": "拥挤" if preferredQuestionLanguage == "zh" else "Crowding",
            "question": "标签、图例或 panel 发生拥挤时，SciFig 应如何处理？" if preferredQuestionLanguage == "zh" else "When labels, legends, or panels start colliding, how should SciFig respond?",
            "options": [
                {"label": "自动简化（推荐）" if preferredQuestionLanguage == "zh" else "Auto simplify (Recommended)", "description": "优先清晰度，自动限制标签、共享图例并调整布局" if preferredQuestionLanguage == "zh" else "Prefer clarity by capping labels, sharing legends, and shrinking overloaded layouts automatically"},
                {"label": "保留信息量" if preferredQuestionLanguage == "zh" else "Preserve information", "description": "尽量保留更多标签和细节，即使图更密" if preferredQuestionLanguage == "zh" else "Keep more labels and detail even if the figure becomes denser"},
                {"label": "简化前先询问" if preferredQuestionLanguage == "zh" else "Ask before simplify", "description": "重大简化前先提示拥挤风险" if preferredQuestionLanguage == "zh" else "Flag crowding risks before major simplification"}
            ]
        }
    ])

    preferences = {
        "journal": pref_visual.journal,
        "domain": syntheticPreferences.get("synthetic_domain_raw") or ("通用生物医学（推荐）" if preferredQuestionLanguage == "zh" else "General biomedical (Recommended)"),
        "story": "多 panel 故事板" if syntheticDataRequested and preferredQuestionLanguage == "zh" else ("Story board" if syntheticDataRequested else ("对比双 panel（推荐）" if preferredQuestionLanguage == "zh" else "Comparison pair (Recommended)")),
        "color": pref_visual.color,
        "resolution": pref_visual.resolution,
        "crowding": pref_visual.crowding,
        "export_bundle": "矢量包（推荐）" if preferredQuestionLanguage == "zh" else "Vector package (Recommended)",
        "stats": "严格（推荐）" if preferredQuestionLanguage == "zh" else "Strict (Recommended)",
        "missing": "删除缺失值（推荐）" if preferredQuestionLanguage == "zh" else "Drop missing (Recommended)",
    }
else:
    preferences = {
        "journal": "Nature-like（推荐）" if preferredQuestionLanguage == "zh" else "Nature-like (Recommended)",
        "domain": syntheticPreferences.get("synthetic_domain_raw") or ("通用生物医学（推荐）" if preferredQuestionLanguage == "zh" else "General biomedical (Recommended)"),
        "story": "对比双 panel（推荐）" if preferredQuestionLanguage == "zh" else "Comparison pair (Recommended)",
        "color": "期刊安全柔和配色（推荐）" if preferredQuestionLanguage == "zh" else "Journal-safe muted (Recommended)",
        "resolution": "300 dpi（推荐）" if preferredQuestionLanguage == "zh" else "300 dpi (Recommended)",
        "crowding": "自动简化（推荐）" if preferredQuestionLanguage == "zh" else "Auto simplify (Recommended)",
        "export_bundle": "矢量包（推荐）" if preferredQuestionLanguage == "zh" else "Vector package (Recommended)",
        "stats": "严格（推荐）" if preferredQuestionLanguage == "zh" else "Strict (Recommended)",
        "missing": "删除缺失值（推荐）" if preferredQuestionLanguage == "zh" else "Drop missing (Recommended)"
    }

resolvedDomainFamily, customDomainText = resolve_domain_answer(preferences.domain, {
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
})

workflowPreferences = {
    "interactionMode": modeChoice,
    "preferenceSource": "user_selected" if visualPreferencesRequired else "automatic_defaults",
    "allowFollowupPreferenceQuestions": visualPreferencesRequired,
    "syntheticDataRequested": syntheticDataRequested,
    "syntheticDomainFamily": syntheticPreferences.get("synthetic_domain_family"),
    "syntheticDomainText": syntheticPreferences.get("synthetic_domain_text"),
    "syntheticFigureBundle": syntheticPreferences.get("synthetic_bundle"),
    "journalStyle": {
        "Nature-like（推荐）": "nature",
        "Nature-like (Recommended)": "nature",
        "Nature-like": "nature",
        "Cell-like": "cell",
        "Science-like（推荐）": "science",
        "Science-like (Recommended)": "science",
        "Science-like": "science",
        "Lancet-like（临床推荐）": "lancet",
        "Lancet-like (Clinical recommended)": "lancet",
        "NEJM-like": "nejm",
        "JAMA-like": "jama"
    }.get(preferences.journal, "custom"),
    "domainFamily": resolvedDomainFamily,
    "customDomainText": customDomainText,
    "storyMode": {
        "单 panel": "single",
        "Single panel": "single",
        "对比双 panel（推荐）": "comparison_pair",
        "Comparison pair (Recommended)": "comparison_pair",
        "多 panel 故事板": "story_board_2x2",
        "Story board": "story_board_2x2"
    }.get(preferences.story, "hero_plus_stacked_support"),
    "missingHandling": {
        "删除缺失值（推荐）": "drop",
        "Drop missing (Recommended)": "drop",
        "警告但保留": "warn",
        "Warn but keep": "warn",
        "插补": "impute",
        "Impute": "impute"
    }.get(preferences.missing, "drop"),
    "colorMode": {
        "期刊安全柔和配色（推荐）": "journal_safe_muted",
        "Journal-safe muted (Recommended)": "journal_safe_muted",
        "领域语义配色": "domain_semantic",
        "Domain semantic": "domain_semantic",
        "严格灰度安全": "strict_grayscale_safe",
        "Strict grayscale-safe": "strict_grayscale_safe"
    }.get(preferences.color, "journal_safe_muted"),
    "rasterDpi": {
        "300 dpi（推荐）": 300,
        "300 dpi (Recommended)": 300,
        "600 dpi": 600,
        "1200 dpi": 1200
    }.get(preferences.resolution, 300),
    "crowdingPolicy": {
        "自动简化（推荐）": "auto_simplify",
        "Auto simplify (Recommended)": "auto_simplify",
        "保留信息量": "preserve_information",
        "Preserve information": "preserve_information",
        "简化前先询问": "ask_before_simplify",
        "Ask before simplify": "ask_before_simplify"
    }.get(preferences.crowding, "auto_simplify"),
    "overlapPriority": "clarity_first",
    "exportFormats": {
        "矢量包（推荐）": ["pdf", "svg"],
        "Vector package (Recommended)": ["pdf", "svg"],
        "审阅包": ["pdf", "svg", "png"],
        "Review package": ["pdf", "svg", "png"],
        "栅格包": ["pdf", "png", "tiff"],
        "Raster package": ["pdf", "png", "tiff"]
    }.get(preferences.export_bundle, ["pdf", "svg"]),
    "statsRigor": {
        "严格（推荐）": "strict",
        "Strict (Recommended)": "strict",
        "标准": "standard",
        "Standard": "standard",
        "仅描述": "descriptive",
        "Descriptive only": "descriptive"
    }.get(preferences.stats, "strict"),
    "panelLayout": {
        "单 panel": "single",
        "Single panel": "single",
        "对比双 panel（推荐）": "1x2",
        "Comparison pair (Recommended)": "1x2",
        "多 panel 故事板": "2x2",
        "Story board": "2x2"
    }.get(preferences.story, "2x2-hero-span")
}
```

## Auto Mode Defaults

When `workflowPreferences["interactionMode"] == "auto"`:

- Ask the data-status card first, then always ask the explicit mode card before any plotting or synthetic-data generation branch. Ask the data-path card only when the user already has a file.
- If the user chooses synthetic data, ask the synthetic-domain card after mode selection, infer suitable journal-style and bundle options from that answer, then ask the synthetic-bundle card as a separate follow-up.
- Ask journal style, color, raster DPI, and crowding together in the final visual preference card for every synthetic-data run. The journal-style options in that card must come from `infer_journal_style_options(...)`, so clinical domains see clinical journal families, omics/cell biology domains see Nature/Cell/Science-like families, and engineering/ecology/social-science domains see more compact cross-disciplinary options. For real-file auto mode, fill these with submission-safe defaults unless the user selected interactive mode.
- Use `crowdingPolicy=auto_simplify` and `overlapPriority=clarity_first`.
- Continue directly into Phase 1 only after either a concrete user-confirmed file path exists or a user-approved synthetic-data plan exists, and only after the user explicitly selected free mode.
- Let the data and detected domain cues drive the recommendation unless the user already supplied explicit `DOMAIN_OVERRIDE` or `MUST_HAVE` constraints.

## Execution Flow

> **COMPACT DIRECTIVE**: The phase currently marked `in_progress` in TodoWrite is the active execution phase and must remain uncompressed. If a sentinel survives but the detailed protocol does not, re-read that phase file before continuing.

```text
Phase 1: Data Input, Structure Detection, Domain Signals
   -> Ref: phases/01-data-detect.md
      Input: file path + workflowPreferences
      Output: dataProfile (schema, semantic roles, domainHints, risks, panelCandidates)

Phase 2: Chart Recommendation, Stats, Panel Blueprint
   -> Ref: phases/02-recommend-stats.md
      Input: dataProfile + workflowPreferences
      Output: chartPlan (primary/secondary charts, stats, panelBlueprint, crowdingPlan, palettePlan)

Phase 3: Code Generation, Journal Styling, Multi-panel Composition
   -> Ref: phases/03-code-gen-style.md
      Input: chartPlan + dataProfile + workflowPreferences
      Output: styledCode (pythonCode, journalProfile, colorSystem, figureSpec, panelGeometry)

Phase 4: Export, Source Data, Statistical Report
   -> Ref: phases/04-export-report.md
      Input: styledCode + chartPlan + dataProfile + workflowPreferences
      Output: outputBundle (figures, code, source data, reports, metadata)
```

**Phase Reference Documents** (read on-demand):

| Phase | Document                                                  | Purpose                                                        | Compact                     |
| ----- | --------------------------------------------------------- | -------------------------------------------------------------- | --------------------------- |
| 1     | [phases/01-data-detect.md](phases/01-data-detect.md)         | Data ingestion, semantic role mapping, domain inference        | TodoWrite driven            |
| 2     | [phases/02-recommend-stats.md](phases/02-recommend-stats.md) | Chart taxonomy selection, stats, panel blueprint               | TodoWrite driven + sentinel |
| 3     | [phases/03-code-gen-style.md](phases/03-code-gen-style.md)   | Journal profiles, palette system, code generation, composition | TodoWrite driven + sentinel |
| 4     | [phases/04-export-report.md](phases/04-export-report.md)     | Export bundle, source data, metadata, reporting                | TodoWrite driven            |

**Reference Specs** (read on-demand when needed):

| Kind     | Document                                                            | Purpose                                                   |
| -------- | ------------------------------------------------------------------- | --------------------------------------------------------- |
| Journal  | [specs/journal-profiles.md](specs/journal-profiles.md)                 | Nature/Cell/Science-aligned style tokens                  |
| Charts   | [specs/chart-catalog.md](specs/chart-catalog.md)                       | Expanded chart family taxonomy and triggers               |
| Domains  | [specs/domain-playbooks.md](specs/domain-playbooks.md)                 | Domain-specific plotting, stats, and panel guidance       |
| Layouts  | [templates/panel-layout-recipes.md](templates/panel-layout-recipes.md) | Reusable multi-panel story recipes                        |
| Palettes | [templates/palette-presets.md](templates/palette-presets.md)           | Reusable categorical/sequential/diverging palette presets |

**Compact Rules**:

1. `TodoWrite in_progress` -> preserve full content
2. `TodoWrite completed` -> safe to compress to summary
3. If a sentinel remains without the full step protocol -> `Read("phases/0N-xxx.md")` before continuing

## Core Rules

1. Do not claim a Nature- or Cell-like figure solely from a palette; typography, spacing, line weight, and panel discipline must also match.
2. Do not use bar charts to hide distributions when individual-level or cohort-level data can be shown.
3. Do not mix unrelated semantic color mappings across panels of the same figure.
4. Do not use rainbow colormaps unless the variable is cyclic and the legend explicitly justifies it.
5. Keep all figure text editable, sans serif, and legible at final print size.
6. Treat multi-panel legends as figure-level layout elements, not as axes annotations. When panels share group, color, marker, or line semantics, keep one shared `fig.legend` outside every plotting area; prefer bottom-center, then top-center, then outside-right. Never use `loc="best"` for publication output.
7. If legend space is tight, adjust columns, shorten labels, reduce spacing, increase margins, or reflow panels before allowing any legend to overlap curves, bars, points, error bars, confidence bands, grids, or heatmap cells.
8. Use shared legends or shared colorbars when panels encode the same semantics.
9. Multi-panel figures must have an explicit panel blueprint before code generation.
10. For implemented single-panel charts, increase Nature/Cell-style information density through data-derived summaries, reference lines, callouts, insets, sample-size labels, and effect-size context before adding new chart types.
11. Do not invent statistics for visual impact. Every p-value, AUC, effect size, threshold count, or fitted parameter must come from the supplied data or a documented upstream result.
12. Prefer vector export and generate source-data friendly artifacts for quantitative panels.
13. If domain inference is weak, fall back to general biomedical rules instead of overfitting to a guessed specialty.
14. If statistical assumptions are uncertain, downgrade to a conservative or descriptive choice and explain why.

## Input Processing

User input is normalized into:

```text
FILE: /path/to/data.csv
EXTRAS: optional figure request or hypothesis
DOMAIN_OVERRIDE: optional explicit domain hint
MUST_HAVE: optional chart or panel requirements
```

If `FILE:` is missing, first use an AskUserQuestion data-status card. If a file exists, ask a data-path card, then ask the separate mode card. If the user chooses synthetic data, skip the file-path card, ask the mode card, then ask the synthetic-domain card. After the synthetic-domain answer, infer the best journal-style options and bundle options from the selected or custom scientific field; ask the synthetic-bundle card separately, then use the inferred journal-style options in the final visual preference card. The final visual preference card asks `journal`, `color`, `resolution`, and `crowding` together before Phase 1. All cards should mirror the user's language. The data-path card should instruct the user to choose Other and paste the exact path there so the reply still shows under `User answered Claude's questions`. Do not use Bash, Glob, Grep, or Read to scan the workspace for candidate datasets. Normalize a confirmed real-file reply into `FILE:` and carry that exact path into Phase 1 as `{{FILE_PATH}}`. Only accept concrete file paths ending in `.csv`, `.tsv`, `.xlsx`, or `.xls`. If the path card only returns the canned option label, ask one direct follow-up for the exact path and stop there. If the reply is a directory or a folder-like path, ask again and stop there. Never run Bash, Read, Grep, or directory inspection before both the file-path gate and the mode gate are complete. Never infer `auto` from any answer that is not an exact mode-card choice, and never fall through to auto defaults after an invalid answer. If the user answers with a localization request like `请用中文`, treat it as a language-switch request and re-ask the same card in Chinese. If the user does not have data and does not choose synthetic data, stop before Phase 1 and help define the expected schema or template instead. If `DOMAIN_OVERRIDE` conflicts with detected cues, keep the user override but warn in Phase 2.
Preference collection happens after the data or synthetic-data target is known and before Phase 1. Use 1-3 questions per AskUserQuestion card by default; the final visual preference card is the only 4-question exception and must keep journal style, color, resolution, and crowding together. The journal-style options must be derived from `syntheticDomainFamily` and `syntheticDomainText` when synthetic data is requested. Do not use `multiSelect`, then freeze `workflowPreferences` before phase dispatch. If the user fills Other for any domain card, preserve that exact text in `customDomainText` or `syntheticDomainText` instead of silently mapping back to biomedical defaults.

## Data Flow

```text
input
  ->
Phase 1 -> dataProfile = {
  format,
  structure,
  columns,
  semanticRoles,
  domainHints,
  nGroups,
  nObservations,
  replicateInfo,
  riskFlags,
  panelCandidates,
  warnings
}
  ->
Phase 2 -> chartPlan = {
  primaryChart,
  secondaryCharts,
  statMethod,
  multipleComparison,
  annotations,
  panelBlueprint,
  crowdingPlan,
  palettePlan,
  journalOverrides,
  rationale
}
  ->
Phase 3 -> styledCode = {
  pythonCode,
  journalProfile,
  figureSpec,
  colorSystem,
  panelGeometry,
  statsReport,
  seed
}
  ->
Phase 4 -> outputBundle = {
  figures,
  code,
  statsReport,
  sourceData,
  panelManifest,
  requirements,
  metadata
}
```

## TodoWrite Pattern

```text
Phase 1 starts:
  -> [in_progress] Phase 1: data detect and domain inference
     -> [pending] Read and parse file
     -> [pending] Detect structure and semantic roles
     -> [pending] Infer domain hints and panel candidates
     -> [pending] Assess risks and build dataProfile

Phase 1 ends:
  -> [completed] Phase 1: dataProfile ready

Phase 2 starts:
  -> [in_progress] Phase 2: chart, stats, panel blueprint
     -> [pending] Resolve domain playbook
     -> [pending] Recommend chart family and stats
     -> [pending] Build panel blueprint and palette plan

Phase 2 ends:
  -> [completed] Phase 2: chartPlan locked
```

Collapse completed sub-tasks back to phase-level summaries before the next phase starts.

## Post-Phase Updates

- After Phase 1: If domain inference is high confidence, note the selected domain playbook and any field-specific warnings.
- After Phase 2: Freeze the chart vocabulary, panel blueprint, and palette plan unless the user requests revision.
- After Phase 3: Validate syntax, imports, and layout consistency before export.
- After Phase 4: Summarize how the user can iterate without re-running Phase 1.

## Error Handling

- Ambiguous domain -> fall back to `General biomedical`, present the top alternatives in rationale.
- Unsupported chart request -> map to the closest supported family and explain the substitution.
- Overcrowded multi-panel plan -> reduce to fewer panels or use a hero-plus-support recipe.
- Palette collision -> fall back to journal-safe muted palette with grayscale-safe accents.
- Weak statistical support -> switch to descriptive mode or a more conservative test.

## Coordinator Checklist

- Confirm a readable input file exists. If the path is missing, use a data-status card, a data-path card, validate the file suffix, and then use a separate mode card before Phase 1.
- Never scan the workspace for candidate data files unless the user explicitly asked for that behavior.
- If the confirmed path is a directory or lacks a supported file suffix, ask again and stop there.
- Never run Bash, Read, Grep, or directory inspection before the file-path gate and mode gate are both complete.
- If any card answer is a language-switch request or otherwise invalid, re-ask the same card and do not consume it as a decision.
- Collect `workflowPreferences` with tool-compatible AskUserQuestion rounds before any phase dispatch, preserving the final 4-question visual preference card when synthetic data or interactive mode requires it.
- In auto mode, do not stop for extra style questions after defaults are set unless the user explicitly asks to switch to interactive refinement.
- Read chart/domain/journal references only when needed.
- Keep the active phase marked `in_progress`.
- Before Phase 3, ensure the panel blueprint and palette plan are explicit.
- Before Phase 4, ensure code generation includes source-data and metadata hooks.

## Related Commands

- `/spec-add learning ...` to record new plotting or domain edge cases.
- `/spec-add arch ...` when the eventual runtime package introduces permanent APIs.
