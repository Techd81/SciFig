# Phase 4: Export, Source Data, And Statistical Report

Execute the generated code, export figure assets, generate source-data friendly tables, and package a submission-grade output bundle.

## Objective

- Run the generated Python script safely
- Export figures in all requested formats
- Export source-data friendly tables for quantitative panels
- Generate statistical and methods-ready reporting
- Package metadata, panel manifest, and reproducibility requirements

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
> 2. The script contains at least one `savefig` call and imports `matplotlib`
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

### Step 4.4: Generate `requirements.txt`

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

    if any(c in charts for c in ("pca", "roc", "pr_curve", "calibration")):
        requirements.append("scikit-learn>=1.3")
    if any(c in charts for c in ("km", "forest")):
        requirements.append("lifelines>=0.27")
    if any(c in charts for c in ("volcano", "ma_plot", "enrichment_dotplot")):
        requirements.append("statsmodels>=0.14")
    if any(c in charts for c in ("umap",)):
        requirements.append("umap-learn>=0.5")

    return "\n".join(sorted(set(requirements)))
```

### Step 4.5: Build Metadata And Panel Manifest

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
    "crowdingPlan": chartPlan.get("crowdingPlan", {})
}
```

### Step 4.6: Export Source Data Tables

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

### Step 4.7: Write Statistical Report

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

### Step 4.8: Package `outputBundle`

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
    "metadata": "output/reports/metadata.json"
}
```

Write files:

```python
Path("output/reports/stats_report.md").write_text(stats_report_content, encoding="utf-8")
Path("output/reports/panel_manifest.json").write_text(json.dumps(panel_manifest, indent=2), encoding="utf-8")
Path("output/reports/metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
Path("output/requirements.txt").write_text(gen_requirements(chartPlan), encoding="utf-8")
```

### Step 4.9: Iteration Rules

If the user requests changes:

- chart family or domain framing -> return to Phase 2
- style, palette, typography, layout, shared legends -> return to Phase 3
- export format or report packaging -> stay in Phase 4
- data interpretation or pairing assumptions -> return to Phase 1 or Phase 2 depending on whether schema meaning changed

The `dataProfile` from Phase 1 should be reused unless the input file or semantic interpretation changes.

## Output

- **Variable**: `outputBundle`
- **Files**: `output/figure1.*`, `output/source_data/*`, `output/reports/*`, `output/requirements.txt`
- **TodoWrite**: Mark Phase 4 completed, workflow complete

## Next Phase

Workflow complete. If revisions are requested, jump back to the appropriate prior phase instead of restarting from scratch.
