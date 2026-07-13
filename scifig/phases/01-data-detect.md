# Phase 1: Data Input, Semantic Detection, And Domain Signals

Read the input file, determine the structural pattern, extract semantic roles, infer likely scientific domains, and build the `dataProfile` used by later phases.

## Objective

- Read CSV, TSV, Excel, or matrix-like input safely
- Detect structural pattern: `tidy`, `wide`, or `matrix`
- Map a richer set of semantic roles beyond `group` and `value`
- Infer domain hints such as genomics, clinical survival, pharmacology, or single-cell
- Pre-compute panel candidates and risk flags for later phase decisions
- Attach scale-policy and optional data-profile audit fields for complex datasets

## Execution

### Step 1.1: Read And Inspect File

```python
import pandas as pd
from pathlib import Path

LARGE_ROW_THRESHOLD = 100_000

file_path = "{{FILE_PATH}}"
if not file_path:
    raise ValueError("Missing FILE_PATH. Ask the user where the data file lives before Phase 1.")

path = Path(file_path)
if not path.exists() or not path.is_file():
    raise FileNotFoundError(f"Input file not found: {file_path}. Ask the user to confirm the exact path.")

ext = path.suffix.lower()

if ext in (".csv", ".txt", ".tsv"):
    # Encoding detection: try utf-8 first, fall back to latin-1, then chardet
    _encoding = "utf-8"
    try:
        with open(path, encoding="utf-8") as f:
            f.read(8192)
    except UnicodeDecodeError:
        try:
            with open(path, encoding="latin-1") as f:
                f.read(8192)
            _encoding = "latin-1"
        except UnicodeDecodeError:
            try:
                import chardet
                with open(path, "rb") as f:
                    _detected = chardet.detect(f.read(100000))
                _encoding = _detected.get("encoding", "latin-1") or "latin-1"
            except ImportError:
                _encoding = "latin-1"

    # Delimiter auto-detection for .csv/.txt
    sep = "\t" if ext == ".tsv" else ","
    if ext in (".csv", ".txt"):
        with open(path, encoding=_encoding, errors="replace") as f:
            _first_lines = [f.readline() for _ in range(5)]
        _tab_counts = [line.count("\t") for line in _first_lines]
        _comma_counts = [line.count(",") for line in _first_lines]
        if all(t > c for t, c in zip(_tab_counts, _comma_counts)) and max(_tab_counts) > 0:
            sep = "\t"

    # Probe row count for large-file handling
    _probe = pd.read_csv(path, sep=sep, nrows=10, encoding=_encoding, on_bad_lines="warn")
    _total_rows = sum(1 for _ in open(path, encoding="utf-8", errors="replace")) - 1
    if _total_rows > LARGE_ROW_THRESHOLD:
        # Chunked read: sample for structure detection, keep full for downstream
        _chunk_size = min(50_000, _total_rows // 5)
        df_full = pd.read_csv(path, sep=sep, encoding=_encoding, on_bad_lines="warn")
        df = df_full.head(LARGE_ROW_THRESHOLD)  # working sample for Phase 1
        _is_chunked = True
    else:
        df = pd.read_csv(path, sep=sep, encoding=_encoding, on_bad_lines="warn")
        df_full = df
        _is_chunked = False
elif ext in (".xlsx", ".xls"):
    df = pd.read_excel(path)
    df_full = df
    _is_chunked = False
else:
    raise ValueError(f"Unsupported file type: {ext}")

if df.empty:
    raise ValueError("Input file has no rows")

column_names = df.columns.tolist()
lower_cols = [c.lower() for c in column_names]
```

When `_is_chunked` is `True`:
- Use `df` (head sample) for structure detection, semantic role mapping, domain inference, and risk assessment.
- Store `df_full` reference in `dataProfile["fullDfPath"]` so downstream phases can load the complete dataset when needed.
- Add `dataProfile["isChunked"] = True` and `dataProfile["totalRows"] = _total_rows` so Phase 2+ can decide whether to subsample for plotting.
- Warn in `dataProfile["warnings"]`: `CHUNKED_READ: structure detection used {_total_rows} rows, analysis limited to first {len(df)} rows`.

### Step 1.2: Detect Structure And Special Patterns

Keep the top-level structure coarse (`tidy`, `wide`, `matrix`) and store domain-specific cues separately.

```python
def detect_structure(df):
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude="number").columns.tolist()

    if len(non_numeric_cols) <= 1 and len(numeric_cols) >= 3:
        return "matrix"

    if len(numeric_cols) >= 1 and len(non_numeric_cols) >= 1:
        return "tidy"

    if len(numeric_cols) >= 3:
        return "wide"

    return "tidy"


def detect_special_patterns(columns):
    cols = [c.lower() for c in columns]
    patterns = set()

    if any(c.startswith("umap") for c in cols) or any(c.startswith("tsne") for c in cols):
        patterns.add("embedding")
    if any(c.startswith("pc") for c in cols):
        patterns.add("pca")
    if any("log2fc" in c or "logfc" in c for c in cols) and any("pval" in c or "padj" in c for c in cols):
        patterns.add("differential")
    if any("chr" in c for c in cols) and any("pos" in c for c in cols):
        patterns.add("genomic_association")
    if any("event" in c or "status" in c for c in cols) and any(c == "time" or "survival" in c for c in cols):
        patterns.add("survival")
    if any("dose" in c or "concentration" in c for c in cols) and any("response" in c or "viability" in c for c in cols):
        patterns.add("dose_response")
    if any("ci_low" in c or "ci_lower" in c for c in cols) and any("ci_high" in c or "ci_upper" in c for c in cols):
        patterns.add("effect_interval")
    if any(token in c for c in cols for token in ("actual", "observed", "measured", "experimental", "y_true")) and any(
        token in c for c in cols for token in ("pred", "predict", "fitted", "estimated", "y_pred")
    ):
        patterns.add("prediction_diagnostic")
    if any("residual" in c for c in cols) or any("rmse" in c or "mae" in c or "percent_error" in c or "error_pct" in c for c in cols):
        patterns.add("model_error_diagnostic")
    if any("model" in c or "algorithm" in c or "estimator" in c or "method" in c for c in cols) and any(
        token in c for c in cols for token in (
            "train", "test", "testing", "validation", "cv", "r2", "r_2", "auc",
            "accuracy", "f1", "precision", "recall", "rmse", "mae"
        )
    ):
        patterns.add("model_performance_benchmark")
    if any(
        c in ("rf", "rfr") or any(token in c for token in ("random_forest", "randomforest", "xgboost", "lightgbm", "gbdt", "svm", "knn"))
        for c in cols
    ):
        patterns.add("ml_model_family")
    if any("shap" in c for c in cols) or any("ale" in c for c in cols) or any("pdp" in c for c in cols):
        patterns.add("ml_explainability")
    if any("importance" in c or "gain" in c or "permutation" in c for c in cols) and any("feature" in c for c in cols):
        patterns.add("feature_importance")
    if any("pareto" in c or "objective" in c or "optimal" in c for c in cols):
        patterns.add("optimization_tradeoff")
    if any("pi_low" in c or "pi_lower" in c or "prediction_interval_low" in c for c in cols) and any(
        "pi_high" in c or "pi_upper" in c or "prediction_interval_high" in c for c in cols
    ):
        patterns.add("prediction_interval")
    # Materials / engineering
    if any("stress" in c or "sigma" in c for c in cols) and any("strain" in c or "epsilon" in c for c in cols):
        patterns.add("stress_strain")
    if any("phase" in c for c in cols) and any("composition" in c or "temp" in c for c in cols):
        patterns.add("phase_diagram")
    if any("xrd" in c or "2theta" in c for c in cols):
        patterns.add("xrd")
    if any("ftir" in c or "wavenumber" in c for c in cols):
        patterns.add("ftir")
    if any("dsc" in c or "heat_flow" in c for c in cols):
        patterns.add("dsc")
    # Ecology / environmental
    if any("species" in c or "taxon" in c or "otu" in c for c in cols):
        patterns.add("species")
    if any("abundance" in c or "count" in c for c in cols) and any("species" in c or "taxon" in c for c in cols):
        patterns.add("abundance")
    if any("shannon" in c or "diversity" in c or "richness" in c for c in cols):
        patterns.add("diversity")
    if any("ordination" in c or "nmds" in c or "pcoa" in c for c in cols):
        patterns.add("ordination")
    # Agriculture / food science
    if any("yield" in c or "production" in c for c in cols):
        patterns.add("yield")
    if any("growth" in c or "biomass" in c for c in cols):
        patterns.add("growth")
    if any("sensory" in c or "panelist" in c for c in cols):
        patterns.add("sensory")
    # Psychology / social science
    if any("likert" in c or "scale" in c for c in cols):
        patterns.add("likert")
    if any("survey" in c or "questionnaire" in c for c in cols):
        patterns.add("survey")
    if any("mediation" in c or "mediator" in c for c in cols):
        patterns.add("mediation")
    if any("pre" in c and "post" in c for c in cols) or any("before" in c and "after" in c for c in cols):
        patterns.add("pre_post")

    return sorted(patterns)
```

### Step 1.3: Map Semantic Roles

Use a broader keyword system so downstream charting is domain-aware.

```python
ROLE_KEYWORDS = {
    "sample_id": ["sample", "sample_id", "specimen", "id"],
    "subject_id": ["subject", "patient", "mouse", "animal", "donor", "participant"],
    "pair_id": ["pair_id", "pair", "matched_id"],
    "group": ["group", "condition", "treatment", "arm", "class", "variety"],
    "cohort": ["cohort", "batch", "center", "site"],
    "value": ["value", "measurement", "signal", "abundance", "expression"],
    "time": ["time", "day", "week", "month", "visit"],
    "bio_rep": ["bio_rep", "biorep", "replicate", "n_bio"],
    "tech_rep": ["tech_rep", "techrep", "technical"],
    "dose": ["dose", "concentration", "conc", "drug_dose"],
    "response": ["response", "viability", "effect", "auc"],
    "event": ["event", "status", "censor", "progression", "death"],
    "duration": ["duration", "survival_time", "follow_up", "os", "pfs"],
    "score": ["score", "probability", "risk", "prediction", "pred", "nes"],
    "label": ["label", "target", "truth", "outcome"],
    "actual": ["actual", "observed", "measured", "experimental", "truth", "y_true"],
    "predicted": ["predicted", "prediction", "pred", "fitted", "estimated", "estimate", "y_pred"],
    "residual": ["residual", "error", "prediction_error"],
    "sample": ["sample", "sample_id", "source", "reference", "ref"],
    "model": ["model", "algorithm", "estimator", "method"],
    "metric": ["metric", "measure", "score_name", "r2", "r_2", "auc", "roc_auc", "accuracy", "f1", "precision", "recall"],
    "effect": ["effect", "estimate", "beta", "hazard_ratio", "odds_ratio"],
    "se": ["se", "std_error", "stderr"],
    "ci_low": ["ci_low", "ci_lower", "lower", "lcl"],
    "ci_high": ["ci_high", "ci_upper", "upper", "ucl"],
    "pi_low": ["pi_low", "pi_lower", "prediction_interval_low", "lower_pi"],
    "pi_high": ["pi_high", "pi_upper", "prediction_interval_high", "upper_pi"],
    "rmse": ["rmse", "root_mean_square_error"],
    "mae": ["mae", "mean_absolute_error"],
    "error_pct": ["percent_error", "percentage_error", "error_pct", "mape"],
    "fold_change": ["log2fc", "logfc", "fold_change"],
    "p_value": ["p", "pval", "p_value", "padj", "qvalue"],
    "feature_id": ["gene", "protein", "metabolite", "feature", "marker", "pathway"],
    "importance": ["importance", "feature_importance", "gain", "permutation_importance"],
    "shap_value": ["shap", "shap_value", "mean_shap"],
    "feature_value": ["feature_value", "input_value", "covariate_value"],
    "ale_effect": ["ale", "ale_effect", "accumulated_local_effect"],
    "pdp_value": ["pdp", "partial_dependence", "pdp_value"],
    "h_statistic": ["h_statistic", "interaction_strength", "interaction_score"],
    "objective": ["objective", "loss", "cost", "utility", "score_objective"],
    "pareto_flag": ["pareto", "non_dominated", "nondominated"],
    "optimal_flag": ["optimal", "best", "selected"],
    "pathway": ["pathway", "term", "hallmark", "geneset"],
    "term": ["term", "pathway", "go_term", "kegg_term"],
    "size": ["size", "count", "set_size", "n_genes"],
    "chromosome": ["chr", "chromosome"],
    "position": ["pos", "position", "bp", "amino_acid_position"],
    "x": ["x", "x_coord", "coord_x", "spatial_x", "umap_1", "pc1"],
    "y": ["y", "y_coord", "coord_y", "spatial_y", "umap_2", "pc2"],
    "umap_1": ["umap_1", "umap1", "tsne_1", "pc1"],
    "umap_2": ["umap_2", "umap2", "tsne_2", "pc2"],
    "cell_type": ["cell_type", "cluster", "annotation", "cellstate"],
    "before": ["before", "pre", "baseline", "value_pre"],
    "after": ["after", "post", "followup", "value_post"],
    "facet": ["facet", "panel", "marker", "endpoint"],
    "label_col": ["label", "gene", "protein", "term_name"],
    "estimate": ["estimate", "effect", "beta", "log2fc", "hazard_ratio"],
    # Materials / engineering
    "stress": ["stress", "sigma", "tensile_stress"],
    "strain": ["strain", "epsilon", "deformation"],
    "temperature": ["temperature", "temp", "celsius", "kelvin"],
    "composition": ["composition", "fraction", "mol_percent", "wt_percent"],
    # Ecology
    "species": ["species", "taxon", "otu", "asv"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng"],
    # Agriculture
    "yield": ["yield", "production", "output", "harvest"],
    # Psychology
    "score_pre": ["score_pre", "pre_score", "baseline_score"],
    "score_post": ["score_post", "post_score", "followup_score"],
}


def map_semantic_roles(df):
    roles = {}
    for role, keywords in ROLE_KEYWORDS.items():
        for col in df.columns:
            low = col.lower()
            if low in keywords or any(k in low for k in keywords):
                roles[role] = col
                break
    return roles
```

### Step 1.4: Infer Domain Hints

Combine user preference and column cues into ranked domain hints.

```python
def infer_domain_hints(df, roles, special_patterns, workflowPreferences):
    scores = {
        "general_biomedical": 1,
        "genomics_transcriptomics": 0,
        "single_cell_spatial": 0,
        "proteomics_metabolomics": 0,
        "pharmacology_toxicology": 0,
        "immunology_cell_biology": 0,
        "neuroscience_behavior": 0,
        "clinical_diagnostics_survival": 0,
        "epidemiology_public_health": 0,
        "materials_engineering": 0,
        "ecology_environmental": 0,
        "agriculture_food_science": 0,
        "psychology_social_science": 0,
        "computer_ai_ml": 0,
    }

    custom_domain = (
        workflowPreferences.get("customDomainText")
        or workflowPreferences.get("syntheticDomainText")
        or ""
    ).lower()

    if "differential" in special_patterns or "genomic_association" in special_patterns:
        scores["genomics_transcriptomics"] += 4
    if "embedding" in special_patterns or "x" in roles or "umap_1" in roles or "cell_type" in roles:
        scores["single_cell_spatial"] += 4
    if "dose_response" in special_patterns or "dose" in roles:
        scores["pharmacology_toxicology"] += 4
    if "survival" in special_patterns or "event" in roles:
        scores["clinical_diagnostics_survival"] += 4
    if "feature_id" in roles:
        scores["proteomics_metabolomics"] += 2
    if "subject_id" in roles and "score" in roles:
        scores["clinical_diagnostics_survival"] += 2
    if "time" in roles and "subject_id" in roles:
        scores["neuroscience_behavior"] += 1
        scores["immunology_cell_biology"] += 1
    # Materials / engineering
    if any(k in special_patterns for k in ("stress_strain", "phase_diagram", "xrd", "ftir", "dsc")):
        scores["materials_engineering"] += 4
    if any(roles.get(r) for r in ("stress", "strain", "temperature", "composition")):
        scores["materials_engineering"] += 2
    # Ecology / environmental
    if any(k in special_patterns for k in ("species", "abundance", "diversity", "shannon", "ordination")):
        scores["ecology_environmental"] += 4
    if any(roles.get(r) for r in ("species", "cohort", "latitude", "longitude")):
        scores["ecology_environmental"] += 2
    # Agriculture / food science
    if any(k in special_patterns for k in ("yield", "growth", "sensory")):
        scores["agriculture_food_science"] += 4
    if any(roles.get(r) for r in ("yield", "group", "bio_rep")):
        scores["agriculture_food_science"] += 2
    # Psychology / social science
    if any(k in special_patterns for k in ("likert", "survey", "mediation", "pre_post")):
        scores["psychology_social_science"] += 4
    if any(roles.get(r) for r in ("subject_id", "group", "score_pre", "score_post")):
        scores["psychology_social_science"] += 2
    # Computer science / AI / machine learning
    if any(k in special_patterns for k in ("prediction_diagnostic", "model_error_diagnostic", "model_performance_benchmark", "ml_model_family", "ml_explainability", "feature_importance", "optimization_tradeoff")):
        scores["computer_ai_ml"] += 5
    if any(roles.get(r) for r in ("model", "metric", "actual", "predicted", "residual", "rmse", "mae", "importance", "shap_value", "objective")):
        scores["computer_ai_ml"] += 3

    user_domain = workflowPreferences.get("domainFamily")
    if user_domain in scores:
        scores[user_domain] += 3

    custom_keyword_map = {
        "genomics_transcriptomics": ["genomics", "transcriptomics", "rna", "dna", "epigen", "mutation"],
        "single_cell_spatial": ["single-cell", "single cell", "spatial", "cell atlas", "cell state"],
        "proteomics_metabolomics": ["proteomics", "metabolomics", "lipidomics", "mass spec"],
        "pharmacology_toxicology": ["drug", "compound", "toxicology", "pharmacology", "screening"],
        "immunology_cell_biology": ["immunology", "immune", "cell biology", "signaling", "pathway"],
        "neuroscience_behavior": ["neuroscience", "behavior", "behaviour", "brain", "neural"],
        "clinical_diagnostics_survival": ["clinical", "diagnostic", "survival", "oncology", "tumor", "tumour", "cancer"],
        "epidemiology_public_health": ["epidemiology", "public health", "population", "cohort", "incidence"],
        "materials_engineering": ["materials", "material", "engineering", "battery", "electrochem", "corrosion", "mechanical", "semiconductor"],
        "ecology_environmental": ["ecology", "environment", "environmental", "marine", "biodiversity", "climate", "soil"],
        "agriculture_food_science": ["agriculture", "crop", "plant", "food", "yield", "agronomy"],
        "psychology_social_science": ["psychology", "social science", "education", "survey", "consumer", "behavioral"],
        "computer_ai_ml": ["computer", "machine learning", "deep learning", "artificial intelligence", "ai", "ml", "random forest", "randomforest", "xgboost", "lightgbm", "gbdt", "classifier", "regressor", "benchmark", "algorithm"],
    }
    for domain_name, keywords in custom_keyword_map.items():
        if any(keyword in custom_domain for keyword in keywords):
            scores[domain_name] += 6

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "primary": ranked[0][0],
        "alternatives": [k for k, _ in ranked[1:4]],
        "scores": scores
    }
```

### Step 1.5: Pre-compute Panel Candidates

Panel candidates are lightweight story hints, not final blueprint decisions.

```python
def build_panel_candidates(df, roles, special_patterns, domain_hints):
    candidates = []
    domain = domain_hints["primary"]

    if "differential" in special_patterns:
        candidates.append({"role": "hero", "chart": "volcano"})
        candidates.append({"role": "support", "chart": "enrichment_dotplot"})
    if "survival" in special_patterns:
        candidates.append({"role": "hero", "chart": "km"})
        candidates.append({"role": "support", "chart": "forest"})
    if "embedding" in special_patterns:
        candidates.append({"role": "hero", "chart": "umap"})
        candidates.append({"role": "support", "chart": "composition_dotplot"})
    if "dose_response" in special_patterns:
        candidates.append({"role": "hero", "chart": "dose_response"})
        candidates.append({"role": "support", "chart": "waterfall"})
    if "prediction_diagnostic" in special_patterns:
        candidates.append({"role": "hero", "chart": "scatter_regression"})
        candidates.append({"role": "validation", "chart": "residual_vs_fitted"})
        candidates.append({"role": "support", "chart": "bland_altman"})
    if "ml_explainability" in special_patterns or "feature_importance" in special_patterns:
        candidates.append({"role": "hero", "chart": "lollipop_horizontal"})
        candidates.append({"role": "support", "chart": "heatmap_annotated"})
        candidates.append({"role": "context", "chart": "dotplot"})
    if "optimization_tradeoff" in special_patterns:
        candidates.append({"role": "hero", "chart": "pareto_chart"})
        candidates.append({"role": "support", "chart": "scatter_regression"})

    if not candidates and "group" in roles and "value" in roles:
        candidates.append({"role": "hero", "chart": "raincloud"})
        candidates.append({"role": "support", "chart": "paired_lines" if "subject_id" in roles else "beeswarm"})

    return candidates
```

### Step 1.6: Risk Assessment

```python
DATA_SCALE_POLICY = {
    "high_missing_rate_pct": 10,
    "overplotting_rows": 400,
    "large_matrix_rows": 2000,
}


def assess_risks(df, roles, structure, special_patterns):
    warnings = []
    risk_flags = []

    # Missing value detection
    missing = df.isna().sum()
    total_missing = missing.sum()
    if total_missing > 0:
        cols_with_missing = [c for c in df.columns if missing[c] > 0]
        pct = total_missing / (len(df) * len(df.columns)) * 100
        warnings.append(f"MISSING_VALUES: {total_missing} cells ({pct:.1f}%) in columns: {', '.join(cols_with_missing[:5])}")
        if pct > DATA_SCALE_POLICY["high_missing_rate_pct"]:
            risk_flags.append("high_missing_rate")
        # Warn specifically about missing group/value columns
        group_col = roles.get("group")
        value_col = roles.get("value")
        if group_col and missing.get(group_col, 0) > 0:
            warnings.append(f"MISSING_IN_GROUP_COLUMN: {missing[group_col]} rows will be dropped")
        if value_col and missing.get(value_col, 0) > 0:
            warnings.append(f"MISSING_IN_VALUE_COLUMN: {missing[value_col]} rows will be dropped from analysis")

    if "bio_rep" not in roles and "subject_id" not in roles and "event" not in roles:
        warnings.append("NO_REPLICATE_DEFINITION")
        risk_flags.append("weak_inferential_support")

    if "group" in roles and "value" in roles and len(df) > DATA_SCALE_POLICY["overplotting_rows"]:
        warnings.append("OVERPLOTTING_RISK")
        risk_flags.append("consider_summary_or_alpha_control")

    if "survival" in special_patterns and "event" not in roles:
        warnings.append("SURVIVAL_WITHOUT_EVENT_FLAG")
        risk_flags.append("survival_incomplete")

    if "dose_response" in special_patterns and "dose" not in roles:
        warnings.append("DOSE_RESPONSE_WITHOUT_EXPLICIT_DOSE_COLUMN")

    if structure == "matrix" and df.shape[0] > DATA_SCALE_POLICY["large_matrix_rows"]:
        warnings.append("LARGE_MATRIX_CLUSTERING_RISK")

    return risk_flags, warnings
```

### Step 1.7: Optional Data Profile Audit

After semantic roles and risks are computed, use a read-only `data-profile-auditor` Agent when the dataset is complex:

- `structure == "matrix"` or `LARGE_MATRIX_CLUSTERING_RISK`
- `high_missing_rate`
- `weak_inferential_support`
- no clear `group`, `value`, `x`, or `y` role for a requested quantitative chart
- ambiguous or custom domain routing
- survival or dose-response cues with missing required roles
- many groups, many columns, or very long category labels

The agent returns JSON into `dataProfile["audit"]`:

```json
{
  "schemaConfidence": "high|medium|low",
  "roleConflicts": [],
  "requiredClarifications": [],
  "recommendedScalePolicy": {},
  "blocking": false
}
```

If `blocking=true`, stop before Phase 2 and ask the minimum clarification needed. Do not invent roles or inferential design to proceed.

### Step 1.8: Build `dataProfile`

```python
structure = detect_structure(df)
special_patterns = detect_special_patterns(df.columns)
semantic_roles = map_semantic_roles(df)
domain_hints = infer_domain_hints(df, semantic_roles, special_patterns, workflowPreferences)
panel_candidates = build_panel_candidates(df, semantic_roles, special_patterns, domain_hints)
risk_flags, warnings = assess_risks(df, semantic_roles, structure, special_patterns)

group_col = semantic_roles.get("group")

dataProfile = {
    "format": ext.lstrip("."),
    "structure": structure,
    "specialPatterns": special_patterns,
    "columns": semantic_roles,
    "semanticRoles": semantic_roles,
    "domainHints": domain_hints,
    "panelCandidates": panel_candidates,
    "nGroups": df[group_col].nunique() if group_col and group_col in df.columns else None,
    "nObservations": len(df),
    "columnNames": df.columns.tolist(),
    "dtypes": {c: str(d) for c, d in df.dtypes.items()},
    "replicateInfo": {
        "has_bio_rep": "bio_rep" in semantic_roles,
        "has_tech_rep": "tech_rep" in semantic_roles,
        "paired_design": "subject_id" in semantic_roles,
        "pseudo_rep_risk": "weak_inferential_support" in risk_flags
    },
    "riskFlags": risk_flags,
    "warnings": warnings,
    "scalePolicy": DATA_SCALE_POLICY,
    "audit": dataProfileAudit if "dataProfileAudit" in globals() else {
        "schemaConfidence": "high" if not risk_flags else "medium",
        "roleConflicts": [],
        "requiredClarifications": [],
        "blocking": False
    },
    "filePath": file_path,
    "isChunked": _is_chunked if "_is_chunked" in dir() else False,
    "totalRows": _total_rows if "_total_rows" in dir() else len(df),
    "fullDfPath": file_path if "_is_chunked" in dir() and _is_chunked else None,
    "df": df
}
```

## Output

- **Variable**: `dataProfile`
- **TodoWrite**: Mark Phase 1 completed, Phase 2 in_progress

## Next Phase

Return to orchestrator, then continue to [Phase 2: Chart Recommendation, Stats, And Panel Blueprint](02-recommend-stats.md).
