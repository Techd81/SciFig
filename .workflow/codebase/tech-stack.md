# Tech Stack

## Current Repository Reality

The repository is not yet a runnable Python package. The current stack is a mix of design-time and artifact assets:

- Markdown research and workflow specs under `doc/` and `.claude/skills/`
- CSV sample datasets under `data/`
- JSON workflow metadata under `.workflow/` and `.ace-tool/`
- Rendered PDF/PNG outputs under `output/all14/`

## Dependency Signals

The only committed dependency manifest is [output/requirements.txt](/D:/SciFig/output/requirements.txt:1), which points to the example figure generation environment:

- `numpy>=1.24`
- `pandas>=2.0`
- `matplotlib>=3.7`
- `seaborn>=0.13`
- `scipy>=1.11`

## Planned Runtime Stack

Based on [doc/deep-research-report.md](/D:/SciFig/doc/deep-research-report.md:1) and `.workflow/project-tech.json`, the intended Python runtime stack is:

- Data: pandas, NumPy
- Statistics: SciPy, statsmodels
- Visualization: Matplotlib, seaborn
- Algorithms: scikit-learn, umap-learn, lifelines
- Export: Matplotlib PDF backend, CairoSVG

## Operational Entry Point Today

The closest thing to a runtime contract is [.claude/skills/scifig-generate/SKILL.md](/D:/SciFig/.claude/skills/scifig-generate/SKILL.md:1), which defines a four-phase flow:

1. Data input and structure detection
2. Chart recommendation and statistics
3. Code generation and style application
4. Export and reporting

## Gaps

- No `pyproject.toml`, package directory, or importable modules
- No root dependency manifest
- No test framework wired into the repo
- No CI or lint configuration committed
