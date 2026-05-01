# Phase 4: Export, Source Data, And Statistical Report

Execute the generated code, export figure assets, generate source-data friendly tables, and package a submission-grade output bundle.

## Objective

- Run the generated Python script safely
- Export figures in all requested formats
- Export source-data friendly tables for quantitative panels
- Generate statistical and methods-ready reporting
- Package metadata, panel manifest, and reproducibility requirements
- Run rendered visual QA before declaring the output submission-ready

## Execution

### Step 4.1: Prepare Output Directories

```python
from pathlib import Path

Path("output").mkdir(exist_ok=True)
Path("output/source_data").mkdir(exist_ok=True)
Path("output/reports").mkdir(exist_ok=True)
```

### Step 4.2: Write and Execute Generated Code

First, write the generated Python code to disk:

```python
output_script = Path("output/generate_figure.py")
output_script.write_text(styledCode["pythonCode"], encoding="utf-8")
```

Smoke check -- verify the file was written and is valid Python:

```python
import ast

# 1. File must exist and be non-empty
assert output_script.exists(), f"Script not written: {output_script}"
assert output_script.stat().st_size > 0, "Script is empty"

# 2. Syntax must be valid Python
source = output_script.read_text(encoding="utf-8")
try:
    ast.parse(source)
except SyntaxError as exc:
    raise RuntimeError(f"Generated code has syntax error: {exc}") from exc

# 3. Must contain at least one savefig call (figure was requested)
assert "savefig" in source, "Generated code has no savefig call -- no figure will be produced"
assert "legend_contract_report = enforce_figure_legend_contract(" in source, (
    "Generated code saves figures without enforcing the final legend contract"
)
assert "record_render_contract_report(" in source and "render_contracts.json" in source, (
    "Generated code does not persist rendered legend/layout contract reports before savefig"
)
assert "audit_figure_layout_contract" in source and "layoutContractFailures" in source, (
    "Generated code missing rendered layout contract checks"
)
assert "exec(aaa, globals())" in source, "Generated code missing embedded skill helper execution"
assert source.count("def enforce_figure_legend_contract(") == 1, (
    "Generated code defines a custom or duplicate legend contract helper"
)
assert "bbox_to_anchor=(0.5, -" not in source and "bbox_to_anchor = (0.5, -" not in source, (
    "Generated code places the shared legend with a negative figure anchor"
)
assert "risk_table_y = -" not in source and "table_y = -" not in source, (
    "Generated code draws table text with negative axes coordinates instead of a reserved slot"
)

# 4. Must import matplotlib (core dependency)
assert "import matplotlib" in source, "Generated code missing matplotlib import"
```

Then execute:

```bash
cd "{{PROJECT_ROOT}}"
python output/generate_figure.py
```

If execution fails:

- Missing library -> regenerate `requirements.txt` and surface the missing import
- Font missing -> fall back to `DejaVu Sans` and note the substitution in metadata
- Data path mismatch -> stop and verify `dataProfile["filePath"]`
- Chart generator missing -> keep the emitted template and flag the chart in `generatorCoverage`

> **CHECKPOINT**: After Step 4.2:
> 1. `output/generate_figure.py` exists, is non-empty, and parses as valid Python
> 2. The script contains at least one `savefig` call, imports `matplotlib`, and calls `enforce_figure_legend_contract(...)` before export
> 3. Execution produced figure files in `output/`

### Step 4.3: Validate Required Outputs

```python
expected = []
normalized_formats = workflowPreferences.get("exportFormats", ["pdf", "svg"])

for fmt in normalized_formats:
    path = Path(f"output/figure1.{fmt}")
    expected.append({"path": str(path), "exists": path.exists()})

required_support_files = [
    Path("output/generate_figure.py"),
    Path("output/reports/stats_report.md"),
    Path("output/reports/panel_manifest.json"),
    Path("output/reports/metadata.json"),
    Path("output/requirements.txt")
]
```

### Step 4.4: Rendered Visual QA Gate

After execution and required-output checks, inspect the rendered artifacts before writing the final bundle. Prefer a read-only `rendered-qa` Agent for complex multi-panel outputs; otherwise run the same checks directly.

```python
import json

render_contract_path = Path("output/reports/render_contracts.json")
render_contracts = []
if render_contract_path.exists():
    render_contracts = json.loads(render_contract_path.read_text(encoding="utf-8"))

runtime_crowding_records = [item.get("crowdingPlan", {}) for item in render_contracts]
runtime_visual_records = [item.get("visualContentPlan", {}) for item in render_contracts]
runtime_crowding = runtime_crowding_records[0] if runtime_crowding_records else {}
runtime_visual = runtime_visual_records[0] if runtime_visual_records else {}
planned_crowding = chartPlan.get("crowdingPlan", {})
planned_visual = chartPlan.get("visualContentPlan", {})

def _runtime_crowding(key, default=None):
    values = [record.get(key) for record in runtime_crowding_records if key in record]
    if not values:
        return planned_crowding.get(key, default)
    if key.endswith("Failures") or key.endswith("Issues"):
        merged = []
        for value in values:
            if isinstance(value, list):
                merged.extend(value)
            elif value:
                merged.append(value)
        return merged
    if key.endswith("Count"):
        numeric_values = [value for value in values if isinstance(value, (int, float))]
        return max(numeric_values) if numeric_values else default
    if key == "legendFrameApplied":
        legend_records = [
            record for record in runtime_crowding_records
            if record.get("figureLegendCount", 0) > 0 or record.get("legendModeUsed") not in (None, "none")
        ]
        return all(bool(record.get(key)) for record in legend_records) if legend_records else False
    if key in ("legendOutsidePlotArea", "legendContractEnforced", "layoutContractEnforced", "legendCenterPlacementOnly", "forbidOutsideRightLegend"):
        return all(bool(value) for value in values)
    if key == "legendModeUsed":
        bad_modes = [value for value in values if value not in ("bottom_center", "none")]
        if bad_modes:
            return bad_modes[0]
        return "bottom_center" if "bottom_center" in values else "none"
    return values[-1]

def _runtime_visual(key, default=None):
    values = [record.get(key) for record in runtime_visual_records if key in record]
    if not values:
        return planned_visual.get(key, default)
    if key in ("appliedEnhancements", "templateMotifsApplied", "visualGrammarMotifsApplied"):
        merged = []
        for value in values:
            if isinstance(value, list):
                merged.extend(item for item in value if item not in merged)
        return merged
    if key in ("templateMotifs", "visualGrammarMotifs"):
        return planned_visual.get(key, values[-1])
    if key.endswith("Count") or key.startswith("min"):
        numeric_values = [value for value in values if isinstance(value, (int, float))]
        return max(numeric_values) if numeric_values else default
    return values[-1]

render_qa = {
    "renderContractReportPath": str(render_contract_path),
    "renderContractReportLoaded": bool(render_contracts),
    "legendOutsidePlotArea": _runtime_crowding("legendOutsidePlotArea"),
    "legendContractEnforced": _runtime_crowding("legendContractEnforced", False),
    "legendContractFailures": _runtime_crowding("legendContractFailures", []),
    "layoutContractEnforced": _runtime_crowding("layoutContractEnforced", False),
    "layoutContractFailures": _runtime_crowding("layoutContractFailures", []),
    "crossPanelOverlapIssues": _runtime_crowding("crossPanelOverlapIssues", []),
    "colorbarReflowCount": _runtime_crowding("colorbarReflowCount", 0),
    "colorbarPanelOverlapIssues": _runtime_crowding("colorbarPanelOverlapIssues", []),
    "colorbarPanelOverlapCount": _runtime_crowding("colorbarPanelOverlapCount", 0),
    "metricTableDataOverlapIssues": _runtime_crowding("metricTableDataOverlapIssues", []),
    "metricTableDataOverlapCount": _runtime_crowding("metricTableDataOverlapCount", 0),
    "negativeAxesTextCount": _runtime_crowding("negativeAxesTextCount", 0),
    "oversizedTextCount": _runtime_crowding("oversizedTextCount", 0),
    "figureWhitespaceFraction": _runtime_crowding("figureWhitespaceFraction", 0),
    "axisLegendRemovedCount": _runtime_crowding("axisLegendRemovedCount", 0),
    "axisLegendRemainingCount": _runtime_crowding("axisLegendRemainingCount", None),
    "figureLegendCount": _runtime_crowding("figureLegendCount", None),
    "legendModeUsed": _runtime_crowding("legendModeUsed", None),
    "legendAllowedModes": _runtime_crowding("legendAllowedModes", ["bottom_center"]),
    "legendCenterPlacementOnly": _runtime_crowding("legendCenterPlacementOnly", True),
    "legendFrameApplied": _runtime_crowding("legendFrameApplied", False),
    "legendFrameStyle": _runtime_crowding("legendFrameStyle", {}),
    "forbidOutsideRightLegend": _runtime_crowding("forbidOutsideRightLegend", True),
    "sharedColorbarApplied": _runtime_crowding("sharedColorbarApplied", False),
    "visualEnhancementCount": len(_runtime_visual("appliedEnhancements", [])),
    "minVisualEnhancementCount": _runtime_visual("minTotalEnhancements", 0),
    "inPlotExplanatoryLabelCount": _runtime_visual("inPlotExplanatoryLabelCount", 0),
    "minInPlotExplanatoryLabels": _runtime_visual("minInPlotLabelsPerFigure", 0),
    "referenceMotifCount": _runtime_visual("referenceMotifCount", 0),
    "minReferenceMotifCount": _runtime_visual("minReferenceMotifsPerFigure", 0),
    "templateMotifCount": _runtime_visual("templateMotifCount", 0),
    "minTemplateMotifCount": _runtime_visual("minTemplateMotifsPerFigure", 0),
    "templateMotifs": _runtime_visual("templateMotifs", []),
    "templateMotifsApplied": _runtime_visual("templateMotifsApplied", []),
    "visualGrammarMotifs": _runtime_visual("visualGrammarMotifs", []),
    "visualGrammarMotifsApplied": _runtime_visual("visualGrammarMotifsApplied", []),
    "metricTableCount": _runtime_visual("metricTableCount", 0),
    "metricTableRelocatedCount": _runtime_visual("metricTableRelocatedCount", 0),
    "metricTableSuppressedCount": _runtime_visual("metricTableSuppressedCount", 0),
    "metricTableFallbackBoxCount": _runtime_visual("metricTableFallbackBoxCount", 0),
    "referenceLineCount": _runtime_visual("referenceLineCount", 0),
    "densityHaloCount": _runtime_visual("densityHaloCount", 0),
    "marginalAxesCount": _runtime_visual("marginalAxesCount", 0),
    "densityColorEncodingCount": _runtime_visual("densityColorEncodingCount", 0),
    "subAxesCount": _runtime_visual("subAxesCount", 0),
    "colorbarSlotCount": _runtime_visual("colorbarSlotCount", 0),
    "multiAxisEncodingCount": _runtime_visual("multiAxisEncodingCount", 0),
    "sampleEncodingCount": _runtime_visual("sampleEncodingCount", 0),
    "significanceStarLayerCount": _runtime_visual("significanceStarLayerCount", 0),
    "dualAxisEncodingCount": _runtime_visual("dualAxisEncodingCount", 0),
    "paletteContrastCheck": chartPlan.get("palettePlan", {}).get("contrastAuditRequired", True),
    "editableTextCheck": "required_for_svg_pdf",
    "overlapFailures": [],
    "contentDensityFailures": [],
    "blankOrTinyOutputs": [],
    "statProvenanceWarnings": [],
    "hardFail": False,
    "impactScore": None,
}

for item in expected:
    artifact = Path(item["path"])
    if not artifact.exists() or artifact.stat().st_size < 1024:
        render_qa["blankOrTinyOutputs"].append(str(artifact))

if not render_qa["renderContractReportLoaded"]:
    render_qa["overlapFailures"].append("missing_render_contract_report")

if not render_qa["legendOutsidePlotArea"]:
    render_qa["overlapFailures"].append("legend_overlaps_plot_area")

if not render_qa["legendContractEnforced"]:
    render_qa["overlapFailures"].append("legend_contract_not_enforced")

if render_qa["legendContractFailures"]:
    render_qa["overlapFailures"].append("legend_contract_failed")

if not render_qa["layoutContractEnforced"]:
    render_qa["overlapFailures"].append("layout_contract_not_enforced")

if render_qa["layoutContractFailures"]:
    render_qa["overlapFailures"].append("layout_contract_failed")

if render_qa["crossPanelOverlapIssues"]:
    render_qa["overlapFailures"].append("cross_panel_text_or_table_overlap")

if render_qa["colorbarPanelOverlapCount"] > 0:
    render_qa["overlapFailures"].append("colorbar_panel_overlap")

if render_qa["metricTableDataOverlapCount"] > 0:
    render_qa["overlapFailures"].append("metric_table_data_overlap")

if render_qa["negativeAxesTextCount"] > 0:
    render_qa["overlapFailures"].append("negative_axes_text_without_reserved_slot")

if render_qa["oversizedTextCount"] > 0:
    render_qa["overlapFailures"].append("poster_scale_fontsize")

if render_qa["axisLegendRemainingCount"] is None:
    render_qa["overlapFailures"].append("axis_legend_remaining_count_missing")
elif render_qa["axisLegendRemainingCount"] > 0:
    render_qa["overlapFailures"].append("axis_legend_remaining")

legend_count = render_qa["figureLegendCount"]
legend_mode = render_qa["legendModeUsed"]
legend_exists = legend_mode not in (None, "none") or (legend_count is not None and legend_count > 0)
if render_qa["figureLegendCount"] is None:
    render_qa["overlapFailures"].append("figure_legend_count_missing")
if legend_exists and render_qa["figureLegendCount"] != 1:
    render_qa["overlapFailures"].append("figure_legend_count_invalid")

if legend_exists and render_qa["legendModeUsed"] != "bottom_center":
    render_qa["overlapFailures"].append("legend_not_bottom_center")

if legend_exists and not render_qa["legendFrameApplied"]:
    render_qa["overlapFailures"].append("legend_frame_missing")

if render_qa["forbidOutsideRightLegend"] and render_qa["legendModeUsed"] == "outside_right":
    render_qa["overlapFailures"].append("outside_right_legend_forbidden")

if render_qa["visualEnhancementCount"] < render_qa["minVisualEnhancementCount"]:
    render_qa["contentDensityFailures"].append("visual_enhancement_count_below_minimum")

if render_qa["inPlotExplanatoryLabelCount"] < render_qa["minInPlotExplanatoryLabels"]:
    render_qa["contentDensityFailures"].append("inplot_explanatory_labels_below_minimum")

if chartPlan.get("visualContentPlan", {}).get("referenceMotifsRequired", True):
    if render_qa["referenceMotifCount"] < render_qa["minReferenceMotifCount"]:
        render_qa["contentDensityFailures"].append("reference_visual_motif_count_below_minimum")
    missing_reference_motifs = sorted(
        set(render_qa["visualGrammarMotifs"]) - set(render_qa["visualGrammarMotifsApplied"])
    )
    if missing_reference_motifs:
        render_qa["missingVisualGrammarMotifs"] = missing_reference_motifs
        render_qa["contentDensityFailures"].append("missing_required_visual_grammar_motifs")

if chartPlan.get("visualContentPlan", {}).get("templateMotifsRequired", False):
    if render_qa["templateMotifCount"] < render_qa["minTemplateMotifCount"]:
        render_qa["contentDensityFailures"].append("template_visual_motif_count_below_minimum")
    missing_template_motifs = sorted(
        set(render_qa["templateMotifs"]) - set(render_qa["templateMotifsApplied"])
    )
    if missing_template_motifs:
        render_qa["missingTemplateMotifs"] = missing_template_motifs
        render_qa["contentDensityFailures"].append("missing_required_template_motifs")

if chartPlan.get("visualContentPlan", {}).get("statProvenanceRequired", True):
    for enhancement in chartPlan.get("visualContentPlan", {}).get("appliedEnhancements", []):
        if any(token in enhancement for token in ("pvalue", "effect", "auc", "slope")):
            if enhancement not in chartPlan.get("visualContentPlan", {}).get("statProvenance", []):
                render_qa["statProvenanceWarnings"].append(enhancement)

render_qa["hardFail"] = bool(
    render_qa["blankOrTinyOutputs"] or
    render_qa["overlapFailures"] or
    render_qa["contentDensityFailures"] or
    render_qa["statProvenanceWarnings"]
)

if render_qa["hardFail"]:
    raise RuntimeError(
        "Rendered QA failed. Return to Phase 3 for layout/style/code fixes, "
        "or Phase 2 if the figure plan is overpacked."
    )
```

#### Step 4.4b: Visual Impact Scoring

After `render_qa` passes its hard-fail checks, evaluate visual impact using a `visual-impact-scorer` Agent. The agent scores contrast depth, visual hierarchy, focal-point clarity, and information-density vs readability balance on a 0-100 scale.

```python
# After render_qa passes (no hardFail)
# Delegate to visual-impact-scorer agent
# Agent returns: { impactScore: 0-100, dimensions: { contrast, hierarchy, focalClarity, infoDensityVsReadability } }

render_qa["impactScore"] = impact_result.get("impactScore", 50)
if render_qa["impactScore"] < 20:
    raise RuntimeError(
        f"Visual impact score {render_qa['impactScore']}/100 is critically low. "
        "Review contrast, hierarchy, focal clarity, and information density."
    )
```

Hard failures:

- legend, colorbar, metric boxes, panel labels, or direct labels overlap plotted data
- generated code saves a figure without `enforce_figure_legend_contract(...)`
- `legendContractEnforced` is false or `legendContractFailures` is non-empty
- `layoutContractEnforced` is false or `layoutContractFailures` is non-empty
- `colorbarPanelOverlapCount > 0`
- `metricTableDataOverlapCount > 0` after helper relocation attempts
- risk tables, footnotes, or outside summaries are drawn with negative axes coordinates instead of a reserved GridSpec/subfigure slot
- generated typography is poster-scale (`font.size >= 12`, `fontsize >= 13`, or panel labels above 12 pt)
- any title, risk table, text box, or statistical bracket overlaps another panel's rendered layout box
- any axis-level legend remains after crowding management
- any final legend is outside `bottom_center`, missing its rounded frame, or placed outside-right
- visual content is under-dense: too few data-derived enhancements or no in-plot explanatory labels
- required reference visual grammar is missing: too few data-supported motif layers such as metric tables, perfect-fit/reference lines, density halos, matrix labels, p-value stars, sample-shape overlays, or dual-axis error bars
- required template visual grammar is missing: planned motif layers such as joint marginal axes, density-colored scatter, prediction diagnostic matrix, correlation evidence matrix, interval band, or dual-axis error sidecar were not applied
- output artifact is missing, blank, or implausibly small
- requested vector text is not editable in SVG/PDF
- `legendOutsidePlotArea` is false
- `figureLegendCount` is not exactly 1 when a legend exists
- inline statistical callouts have no provenance in `statPlan`, input columns, or `visualContentPlan.statProvenance`

### Step 4.5: Generate `requirements.txt`

```python
def gen_requirements(chartPlan):
    requirements = [
        "numpy>=1.24",
        "pandas>=2.0",
        "matplotlib>=3.7",
        "seaborn>=0.13",
        "scipy>=1.11",
        "openpyxl>=3.1"
    ]

    primary = chartPlan["primaryChart"]
    secondary = chartPlan["secondaryCharts"]
    charts = [primary] + secondary

    if any(c in charts for c in ("pca", "rf_classifier_report_board", "classifier_validation_board", "roc", "pr_curve", "calibration")):
        requirements.append("scikit-learn>=1.3")
    if any(c in charts for c in ("km", "forest")):
        requirements.append("lifelines>=0.27")
    if any(c in charts for c in ("volcano", "ma_plot", "enrichment_dotplot")):
        requirements.append("statsmodels>=0.14")
    if any(c in charts for c in ("umap",)):
        requirements.append("umap-learn>=0.5")

    return "\n".join(sorted(set(requirements)))
```

### Step 4.6: Build Metadata And Panel Manifest

```python
import hashlib
import json
from datetime import datetime

input_hash = hashlib.md5(Path(dataProfile["filePath"]).read_bytes()).hexdigest()

metadata = {
    "inputFile": dataProfile["filePath"],
    "inputHash": input_hash,
    "timestamp": datetime.now().isoformat(),
    "interactionMode": workflowPreferences.get("interactionMode", "interactive"),
    "preferenceSource": workflowPreferences.get("preferenceSource", "user_selected"),
    "crowdingPolicy": workflowPreferences.get("crowdingPolicy", "auto_simplify"),
    "overlapPriority": workflowPreferences.get("overlapPriority", "clarity_first"),
    "journalProfile": styledCode["journalProfile"]["name"],
    "primaryChart": chartPlan["primaryChart"],
    "secondaryCharts": chartPlan["secondaryCharts"],
    "statsMethod": chartPlan["statMethod"],
    "exportFormats": normalized_formats,
    "rasterDpi": workflowPreferences.get("rasterDpi", 300),
    "requestedLayout": chartPlan["panelBlueprint"].get("requestedLayout", chartPlan["panelBlueprint"]["layout"]["recipe"]),
    "finalLayout": chartPlan["panelBlueprint"].get("finalLayout", chartPlan["panelBlueprint"]["layout"]["recipe"]),
    "simplificationsApplied": chartPlan.get("crowdingPlan", {}).get("simplificationsApplied", []),
    "droppedDirectLabelCount": chartPlan.get("crowdingPlan", {}).get("droppedDirectLabelCount", 0),
    "renderContractReportPath": render_qa["renderContractReportPath"],
    "legendModeUsed": render_qa["legendModeUsed"],
    "legendAllowedModes": render_qa["legendAllowedModes"],
    "legendFrameApplied": render_qa["legendFrameApplied"],
    "legendContractEnforced": render_qa["legendContractEnforced"],
    "legendContractFailures": render_qa["legendContractFailures"],
    "layoutContractEnforced": render_qa["layoutContractEnforced"],
    "layoutContractFailures": render_qa["layoutContractFailures"],
    "negativeAxesTextCount": render_qa["negativeAxesTextCount"],
    "oversizedTextCount": render_qa["oversizedTextCount"],
    "axisLegendRemovedCount": render_qa["axisLegendRemovedCount"],
    "figureLegendCount": render_qa["figureLegendCount"],
    "legendOutsidePlotArea": render_qa["legendOutsidePlotArea"],
    "sharedColorbarApplied": render_qa["sharedColorbarApplied"],
    "visualContentPlan": runtime_visual or chartPlan.get("visualContentPlan", {}),
    "delegationReports": chartPlan.get("delegationReports", {}),
    "renderQa": render_qa,
    "seed": styledCode["seed"],
    "scifigVersion": "0.2.0"
}

panel_manifest = {
    "layout": chartPlan["panelBlueprint"]["layout"],
    "requestedLayout": chartPlan["panelBlueprint"].get("requestedLayout", chartPlan["panelBlueprint"]["layout"]["recipe"]),
    "finalLayout": chartPlan["panelBlueprint"].get("finalLayout", chartPlan["panelBlueprint"]["layout"]["recipe"]),
    "panels": chartPlan["panelBlueprint"]["panels"],
    "sharedLegend": chartPlan["panelBlueprint"]["sharedLegend"],
    "sharedColorbar": chartPlan["panelBlueprint"]["sharedColorbar"],
    "palettePlan": chartPlan["palettePlan"],
    "crowdingPlan": runtime_crowding or chartPlan.get("crowdingPlan", {}),
    "visualContentPlan": runtime_visual or chartPlan.get("visualContentPlan", {}),
    "delegationReports": chartPlan.get("delegationReports", {}),
    "renderQa": render_qa
}
```

### Step 4.7: Export Source Data Tables

For every quantitative panel, write a tidy CSV to `output/source_data/`.

```python
def export_source_data(chartPlan, dataProfile):
    source_files = []
    base_df = dataProfile["df"].copy()
    roles = dataProfile["semanticRoles"]

    keep_cols = [roles[k] for k in roles if roles[k] in base_df.columns]
    keep_cols = list(dict.fromkeys(keep_cols))

    primary_path = Path(f"output/source_data/{chartPlan['primaryChart']}_source.csv")
    base_df[keep_cols].to_csv(primary_path, index=False)
    source_files.append(str(primary_path))

    for chart in chartPlan["secondaryCharts"]:
        path = Path(f"output/source_data/{chart}_source.csv")
        base_df[keep_cols].to_csv(path, index=False)
        source_files.append(str(path))

    return source_files
```

### Step 4.8: Write Statistical Report

Build the report content from the template:

```python
stats_report_content = f"""# Statistical Report

## Figure Overview
- Primary chart: {chartPlan['primaryChart']}
- Secondary charts: {', '.join(chartPlan['secondaryCharts'])}
- Domain: {dataProfile['domainHints']['primary']}
- Story recipe: {chartPlan['panelBlueprint']['layout']['recipe']}

## Data Summary
- Structure: {dataProfile['structure']}
- Special patterns: {', '.join(dataProfile.get('specialPatterns', []))}
- N observations: {dataProfile['nObservations']}
- N groups: {dataProfile['nGroups']}

## Statistical Plan
- Method: {chartPlan['statMethod']}
- Multiple comparison: {chartPlan.get('multipleComparison') or 'None'}
- Notes: {chartPlan.get('statNotes', '')}

## Methods Sentence
> {styledCode.get('statsReport', {}).get('methods_sentence', 'See figure caption for statistical details.')}

## Reproducibility
- Seed: {styledCode['seed']}
- Input hash: {dataProfile.get('inputHash', 'N/A')}
- Journal profile: {styledCode['journalProfile']['name']}
- Requirements: see `output/requirements.txt`
- Source data: see `output/source_data/`
"""
```

### Step 4.9: Package `outputBundle`

```python
sourceDataFiles = export_source_data(chartPlan, dataProfile)

outputBundle = {
    "figures": {
        "pdf": "output/figure1.pdf" if "pdf" in normalized_formats else None,
        "svg": "output/figure1.svg" if "svg" in normalized_formats else None,
        "png": "output/figure1.png" if "png" in normalized_formats else None,
        "tiff": "output/figure1.tiff" if "tiff" in normalized_formats else None
    },
    "code": "output/generate_figure.py",
    "statsReport": "output/reports/stats_report.md",
    "sourceData": sourceDataFiles,
    "panelManifest": "output/reports/panel_manifest.json",
    "requirements": "output/requirements.txt",
    "metadata": "output/reports/metadata.json",
    "renderQa": "output/reports/render_qa.json"
}
```

Write files:

```python
Path("output/reports/stats_report.md").write_text(stats_report_content, encoding="utf-8")
Path("output/reports/panel_manifest.json").write_text(json.dumps(panel_manifest, indent=2), encoding="utf-8")
Path("output/reports/metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
Path("output/reports/render_qa.json").write_text(json.dumps(render_qa, indent=2), encoding="utf-8")
Path("output/requirements.txt").write_text(gen_requirements(chartPlan), encoding="utf-8")
```

### Step 4.10: Iteration Rules

If the user requests changes:

- chart family or domain framing -> return to Phase 2
- style, palette, typography, layout, shared legends -> return to Phase 3
- rendered QA failure -> return to Phase 3 unless the plan is overpacked, then return to Phase 2
- export format or report packaging -> stay in Phase 4
- data interpretation or pairing assumptions -> return to Phase 1 or Phase 2 depending on whether schema meaning changed

The `dataProfile` from Phase 1 should be reused unless the input file or semantic interpretation changes.

## Output

- **Variable**: `outputBundle`
- **Files**: `output/figure1.*`, `output/source_data/*`, `output/reports/*`, `output/requirements.txt`
- **TodoWrite**: Mark Phase 4 completed, workflow complete

## Next Phase

Workflow complete. If revisions are requested, jump back to the appropriate prior phase instead of restarting from scratch.
