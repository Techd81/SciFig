# SciFig

Publication-ready scientific figure generation from experimental data.

SciFig is an open-source (MIT) system that takes real experimental data
(CSV / Excel / matrix) and produces high-quality, journal-compliant figures
with reproducible code.

## Install

```bash
pip install scifig            # core
pip install scifig[full]      # + scikit-learn, lifelines, umap-learn, openpyxl
```

## Quick start

```python
import pandas as pd
import scifig

# Load data
df = pd.read_csv("experiment.csv")

# Get a journal style profile
style = scifig.style.get_journal_profile("nature")
print(style["single_width_mm"])  # 89

# Pick a colorblind-safe palette
colors = scifig.palette.get_palette("wong", n=4)
print(colors)  # ['#000000', '#E69F00', '#56B4E9', '#009E73']

# Sanitise column names for safe code generation
clean_df = scifig.utils.sanitize_columns(df)

# Detect the best available font
font = scifig.utils.detect_available_font()
print(font)
```

## Journal profiles

Built-in profiles for: **Nature**, **Cell**, **Science**, **The Lancet**,
**NEJM**, **JAMA**. Each profile encodes single/double column widths, font
sizes, line widths, and spine visibility matching the target journal's
guidelines.

## Color palettes

- **Wong (2011)** colorblind-safe palette (8 colors)
- Okabe-Ito, tab10, bold4, muted6
- Sequential: blues, viridis, inferno, greens
- Diverging: rdbu, brbg, coolwarm

## Skills

Reusable workflow skills live under `skills/`, not under tool-specific
directories such as `.claude/` or `.codex/`. To use the SciFig generation
workflow with a compatible agent runner, copy `skills/scifig-generate` into
that runner's local skills directory. See [skills/README.md](skills/README.md)
for install commands.

## Documentation

See the [deep research report](doc/deep-research-report.md) for full product
specification, user personas, statistical strategies, and roadmap.

## License

MIT
