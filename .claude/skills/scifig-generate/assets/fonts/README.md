# Bundled Fonts Directory

This directory stores user-provided TrueType / OpenType font files that the
`scifig-generate` skill registers with matplotlib at runtime. Drop any
`.ttf`, `.otf`, or `.ttc` files here and they will be auto-loaded the first
time `apply_journal_kernel(...)` is called (idempotent — re-calls do not
re-scan).

## Why this directory exists

Templates anchor `font.family` to **commercial** typefaces — Arial,
Helvetica, Times New Roman, SimHei — that the skill itself **cannot
legally redistribute**. On Linux servers, Docker containers, and clean
macOS installs these fonts are typically absent, so matplotlib falls back
to DejaVu Sans, prints a `findfont` warning, and produces a figure whose
metrics no longer match the journal profile.

To fix this without shipping commercial fonts, the skill provides this
opt-in directory: **drop your own legally-obtained TTFs here** and they
will be picked up on the next render.

## What to put here

Any of these (filenames are freeform, matplotlib reads the family name
from the font file's internal name table):

- `Arial.ttf`, `Arial-Bold.ttf`, `Arial-Italic.ttf`
- `Helvetica.ttf`, `Helvetica-Bold.ttf`
- `Times-New-Roman.ttf`, `Times-New-Roman-Bold.ttf`, `Times-New-Roman-Italic.ttf`
- `SimHei.ttf` (or any CJK font: Noto Sans SC, Source Han Sans SC, ...)
- Any other typeface you want available globally to generated figures

If you do not have access to the commercial originals, drop in the
**metric-compatible** open replacements instead:

- **Liberation Sans** (Apache 2.0) → drop-in for Arial/Helvetica
- **Liberation Serif** (Apache 2.0) → drop-in for Times New Roman
- **Liberation Mono** (Apache 2.0) → drop-in for Courier
- **Noto Sans SC** (SIL OFL, Google) → CJK / SimHei replacement
- **Source Han Sans SC** (SIL OFL, Adobe) → CJK / SimHei replacement
- **Carlito** (SIL OFL, Google) → metric-compatible Calibri

## Loading mechanism

`phases/code-gen/template_mining_helpers.py::_register_bundled_fonts()` is
called once at the top of `apply_journal_kernel()`:

1. Resolves the fonts directory via four strategies (env var
   `SCIFIG_FONTS_DIR`, injected `__SCIFIG_SKILL_ROOT__` global, the
   helper module's `__file__`, current working dir).
2. Iterates every `*.ttf` / `*.otf` / `*.ttc` in the directory.
3. Calls `matplotlib.font_manager.fontManager.addfont(path)` for each.
4. Sets a module-level flag so subsequent calls skip the scan.

This means generated scripts load the fonts automatically (Phase 3 sets
`SCIFIG_FONTS_DIR` to this directory's absolute path before exec'ing
`template_mining_helpers.py`).

## Verifying registration

```python
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from template_mining_helpers import apply_journal_kernel

apply_journal_kernel("default")            # triggers _register_bundled_fonts
print([f.name for f in fm.fontManager.ttflist if "Arial" in f.name])
print([f.name for f in fm.fontManager.ttflist if "Times" in f.name])
```

## Troubleshooting

- **Font present but matplotlib still warns** — clear matplotlib's font
  cache: `import matplotlib; print(matplotlib.get_cachedir())`, then
  delete the `fontlist-*.json` file in that directory and re-run.
- **CJK glyphs render as squares** — confirm a CJK font is registered
  *and* appears somewhere in the active `font.family` list. Adding the
  font to this directory does not automatically prepend it to the
  fallback chain; you may need to extend `_KERNEL_BASE["font.family"]`
  in `template_mining_helpers.py` or pass a `journalProfile` with the
  CJK family at the head of `font_family`.
- **Path not found in generated script** — ensure Phase 3 emitted the
  `os.environ.setdefault("SCIFIG_FONTS_DIR", ...)` line at the top of
  the script. Without it, `_resolve_fonts_dir()` falls back to
  `__file__`-relative resolution, which fails when the helper source is
  embedded via `exec()`.

## Licensing reminder

This directory is `.gitkeep`-tracked but its `*.ttf` / `*.otf` /
`*.ttc` payload is `.gitignore`d (see `.gitignore` at the skill root if
applicable). **Do not commit** font files you do not have the right to
redistribute. The skill ships zero font files by default precisely so
that the repository remains license-clean.
