"""Template-mining helpers for the knowledge base under `knowledge/`.

Phase 3 imports from this module to apply article-derived visual grammar
distilled from the current template corpus.

Module status (n/n implemented):
  - apply_journal_kernel        ok
  - resolve_palette             ok
  - role_color                  ok
  - add_metric_box              ok
  - add_perfect_fit_diagonal    ok
  - add_zero_reference          ok
  - add_group_dividers          ok
  - add_panel_label             ok
  - density_sort                ok
  - density_color_scatter       ok
  - add_polygon_polar_grid      ok
  - add_polar_spoke_tick_labels ok (case 001 hollow-center radar)
  - add_hollow_polar_center     ok (case 001 hollow-center radar)
  - scatter_glass_markers       ok (case 001 pseudo-3D marker highlight)
  - draw_mirror_radial_bar_board ok (case 023 mirror radial rose)
  - draw_gradient_box           ok
  - add_forest_panel            ok
  - build_grid                  ok (R0 / R1 / R2 / R3 / R4 / R5 / R6 / R7 / R8 / R9 / R10 / R11 implemented)
  - select_narrative_arc        ok
  - arc_required_motifs         ok
  - arc_default_grid            ok
  - apply_zorder_recipe         ok (scatter_regression / forest / dual_axis / radar / shap_composite / marginal_joint)
  - add_heatmap_pairwise_panel  ok (cycle 21; n*n correlation matrix discipline)
  - draw_bubble_correlation_matrix ok (case 011 red-blue bubble matrix)
  - draw_textbook_dual_axis_bar_line ok (case 012 Materials Today dual Y-axis)
  - draw_dual_axis_hist_cumfreq_grid ok (case 020 HPC distribution matrix)
  - draw_bipolar_lollipop_ale_board ok (case 022 PFI + ALE lollipop pair)
  - draw_hump_threshold_regression ok (case 024 Advanced Science threshold hump)
  - draw_bayesian_ridge_heatmap_board ok (case 025 ridge + heat strip board)
  - draw_inset_heatmap_bar_rank ok (case 027 ranked bar + inset heatmap)
  - draw_inset_raincloud       ok (case 009 main+inset residual raincloud)
  - draw_shap_bar_beeswarm_inset_pie ok (case 010 SHAP composite)
  - draw_lollipop_shap_beeswarm_board ok (case 021 XGBoost lollipop + SHAP)
  - draw_shap_bar_pie_summary_board ok (case 019 SHAP bar + standalone pie + summary)
  - draw_pls_pm_path_model     ok (case 014 PLS-PM/SEM path model)
  - draw_density_parity_matrix ok (case 015 2D-KDE parity matrix)
  - draw_time_series_prediction_interval ok (case 016 train/test PI time series)
  - draw_shap_dependence_background_grid ok (case 017 red/blue SHAP dependence grid)
  - draw_shap_interaction_dependence_grid ok (case 018 SHAP interaction dependence grid)

Reference docs:
  - 01-rcparams-kernel.md       kernel definitions
  - 02-zorder-recipes.md        per-family zorder layering
  - 03-palette-bank.md          named palettes + role mapping
  - 04-grid-recipes.md          GridSpec / subplots recipes
  - 05-annotation-idioms.md     in-axes annotation idioms
  - 06-narrative-arcs.md        story shapes
  - knowledge/techniques/<family>.md   deep-dive per chart family
"""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib as mpl
import matplotlib.colors as mc
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec


# ============================================================================
# 0. BUNDLED FONT REGISTRATION  (assets/fonts/)
# ============================================================================
#
# Templates anchor `font.family` to commercial typefaces (Arial, Helvetica,
# Times New Roman, SimHei) that the skill cannot legally redistribute. Linux
# servers / Docker containers / clean macOS installs typically lack these
# fonts, so matplotlib silently falls back to DejaVu Sans and emits a
# `findfont` warning that some environments treat as an error.
#
# Resolution: an opt-in `assets/fonts/` directory at the skill root holds
# user-supplied TTF/OTF/TTC files. `_register_bundled_fonts()` scans the
# directory at the top of `apply_journal_kernel()` and registers every font
# with matplotlib's font_manager. Idempotent across calls; safe under
# `exec()` embedding (Phase 3 sets SCIFIG_FONTS_DIR before exec'ing this
# source).

_FONT_REGISTRATION_DONE: bool = False
_FONT_REGISTRATION_RESULT: dict | None = None


def _resolve_fonts_dir() -> Path | None:
    """Resolve the assets/fonts directory across import / exec / cwd contexts.

    Strategy order (first existing directory wins):
      1. ``SCIFIG_FONTS_DIR`` env var �?explicit override; Phase 3 sets this.
      2. ``__SCIFIG_SKILL_ROOT__`` global �?injected into namespace before
         ``exec(template_mining_helpers_source)`` in generated scripts.
      3. ``__file__``-relative �?three levels up from this module:
         ``runtime/template_mining_helpers.py`` ->
         ``<skill_root>/assets/fonts``. Works for direct imports.
      4. ``Path.cwd() / "assets/fonts"`` �?last-resort for ad-hoc scripts.

    Returns ``None`` when no candidate directory exists; callers must treat
    this as a no-op rather than an error (font registration is opt-in).
    """
    env_dir = os.environ.get("SCIFIG_FONTS_DIR")
    if env_dir:
        candidate = Path(env_dir).expanduser()
        if candidate.is_dir():
            return candidate.resolve()

    injected_root = globals().get("__SCIFIG_SKILL_ROOT__")
    if injected_root:
        candidate = Path(str(injected_root)).expanduser() / "assets" / "fonts"
        if candidate.is_dir():
            return candidate.resolve()

    try:
        here = Path(__file__).resolve()
        candidate = here.parent.parent.parent / "assets" / "fonts"
        if candidate.is_dir():
            return candidate.resolve()
    except NameError:
        # __file__ is undefined when this source is exec'd into a foreign
        # namespace (Phase 3 runtime path); fall through to the cwd probe.
        pass

    candidate = Path.cwd() / "assets" / "fonts"
    if candidate.is_dir():
        return candidate.resolve()

    return None


def _register_bundled_fonts(force: bool = False) -> dict:
    """Register every TTF/OTF/TTC under ``assets/fonts/`` with matplotlib.

    Behavior:
      * Idempotent �?repeated calls return the cached result unchanged
        unless ``force=True``.
      * Safe �?every error is caught and recorded; never propagates into
        ``apply_journal_kernel()``.
      * Resilient �?if no fonts directory exists or it is empty, returns a
        no-op result and the caller proceeds normally (matplotlib's
        DejaVu Sans fallback still works).

    Returns a diagnostic dict::

        {
            "fonts_dir":  "<absolute path or None>",
            "registered": [<filenames added to fontManager>],
            "errors":     [<"<filename>: <ExcType>: <msg>">],
            "cached":     bool,  # True if this call returned a cached result
        }
    """
    global _FONT_REGISTRATION_DONE, _FONT_REGISTRATION_RESULT

    if _FONT_REGISTRATION_DONE and not force and _FONT_REGISTRATION_RESULT is not None:
        cached = dict(_FONT_REGISTRATION_RESULT)
        cached["cached"] = True
        return cached

    fonts_dir = _resolve_fonts_dir()
    result: dict = {
        "fonts_dir":  str(fonts_dir) if fonts_dir else None,
        "registered": [],
        "errors":     [],
        "cached":     False,
    }

    if fonts_dir is None:
        _FONT_REGISTRATION_DONE = True
        _FONT_REGISTRATION_RESULT = result
        return result

    seen: set[Path] = set()
    for pattern in ("*.ttf", "*.otf", "*.ttc", "*.TTF", "*.OTF", "*.TTC"):
        for path in fonts_dir.glob(pattern):
            if path.is_file():
                seen.add(path.resolve())

    for path in sorted(seen):
        try:
            font_manager.fontManager.addfont(str(path))
            result["registered"].append(path.name)
        except Exception as exc:  # noqa: BLE001 �?catalog errors, never raise
            result["errors"].append(f"{path.name}: {type(exc).__name__}: {exc}")

    _FONT_REGISTRATION_DONE = True
    _FONT_REGISTRATION_RESULT = result
    return result


# ============================================================================
# 1. RCPARAMS KERNEL  (01-rcparams-kernel.md)
# ============================================================================

_KERNEL_BASE = {
    # Font fallback chain (V0.1.1):
    #   [DejaVu Sans, Arial, Helvetica, Times New Roman] (Latin / scientific)
    #   [Microsoft YaHei, SimHei, Noto Sans CJK SC, Noto Sans CJK JP, Hiragino Sans]
    #   (CJK glyph coverage �?first family available wins per glyph).
    # matplotlib walks the list and picks the first family that has each
    # glyph; this means English text has DejaVu coverage first while
    # Chinese / Japanese / Korean characters can fall through to YaHei / Noto
    # without raising "Glyph N missing from font" warnings on Windows /
    # macOS / Linux respectively. DejaVu Sans ships with matplotlib and
    # prevents fragile scientific labels from rendering as boxes.
    "font.family":       ["DejaVu Sans", "Arial", "Helvetica",
                           "Times New Roman", "Microsoft YaHei", "SimHei",
                           "Noto Sans CJK SC", "Noto Sans CJK JP",
                           "Hiragino Sans"],
    "font.sans-serif":   ["DejaVu Sans", "Arial", "Helvetica",
                           "Microsoft YaHei", "SimHei",
                           "Noto Sans CJK SC", "Noto Sans CJK JP",
                           "Hiragino Sans"],
    "axes.unicode_minus": False,  # CJK fonts often miss U+2212; use ASCII '-' for axis ticks
    "mathtext.fontset":  "stix",
    "font.size":         6.5,
    "axes.linewidth":    0.65,
    "xtick.direction":   "in",
    "ytick.direction":   "in",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "lines.linewidth":   0.9,
    "lines.markersize":  3.5,
    "legend.fontsize":   7,
    "legend.frameon":    True,
    "legend.edgecolor":  "#cccccc",
    "legend.borderpad":  0.4,
    "savefig.bbox":      "tight",
    "savefig.dpi":       600,
}

_VARIANTS = {
    "default": {},
    "hero":    {"font.size": 7.5, "axes.linewidth": 0.75, "lines.linewidth": 1.2},
    "compact": {"font.family": ["DejaVu Sans", "Arial", "Helvetica",
                                  "Times New Roman", "Microsoft YaHei", "SimHei",
                                  "Noto Sans CJK SC", "Noto Sans CJK JP",
                                  "Hiragino Sans"],
                "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica",
                                      "Microsoft YaHei", "SimHei",
                                      "Noto Sans CJK SC", "Noto Sans CJK JP",
                                      "Hiragino Sans"],
                "font.size": 6.5, "axes.linewidth": 0.65,
                "lines.linewidth": 0.9, "lines.markersize": 3.5},
    "polar":   {"font.size": 7.0, "axes.linewidth": 0.75,
                "grid.linestyle": "--", "grid.alpha": 0.5},
}


def _filter_available_fonts(font_chain: list) -> list:
    """Drop font families that are not installed on this system.

    matplotlib walks the ``font.family`` list and emits a `findfont` warning
    for every missing entry before falling through to one that exists. On a
    Windows host the CJK chain ``[Microsoft YaHei, SimHei, Noto Sans CJK SC,
    Noto Sans CJK JP, Hiragino Sans, DejaVu Sans]`` produces three warnings
    per render even though YaHei + SimHei already cover Chinese glyphs.

    This filter keeps a family iff ``font_manager`` can find it. Callers
    must guarantee at least one fallback always survives �?`_KERNEL_BASE`
    ends in `DejaVu Sans` which ships with matplotlib, so the filtered list
    is never empty in practice. If somehow it is, return the original
    chain unchanged so matplotlib raises its own clear error rather than
    a silent empty-list KeyError downstream.
    """
    try:
        installed = {f.name for f in font_manager.fontManager.ttflist}
    except Exception:
        return list(font_chain)
    available = [name for name in font_chain if name in installed]
    return available if available else list(font_chain)


def _prefer_dejavu_first(font_chain: list) -> list:
    """Keep DejaVu Sans first so ASCII-safe labels render on clean systems."""
    out = ["DejaVu Sans"]
    for name in font_chain:
        if name and name not in out:
            out.append(name)
    return out


def apply_journal_kernel(variant: str = "default",
                          journalProfile: dict | None = None) -> None:
    """Apply the kernel rcParams for one of the four variants and let
    journal-specific overrides win. Variants: 'default' | 'hero' | 'compact' | 'polar'.

    Behavioral rules (from 01-rcparams-kernel.md):
      1. Variant is required; no silent fallback to matplotlib defaults.
      2. journalProfile fields take precedence for font_family, font_size_body_pt,
         axis_linewidth_pt.
      3. Always keep tick.direction='in'.
      4. Bundled fonts under ``assets/fonts/`` are registered once at the top
         of the first call (idempotent); registration failures never block
         kernel application.
      5. (cycle-23) ``font.family`` fallback chain is filtered against the
         installed font set so matplotlib does not emit a `findfont` warning
         for every cross-platform CJK fallback (Noto Sans CJK on Linux,
         Hiragino Sans on macOS, Microsoft YaHei / SimHei on Windows).
    """
    # Register bundled fonts BEFORE rcParams.update so that user-supplied
    # Arial/Helvetica/Times TTFs are present when matplotlib resolves the
    # font.family fallback chain. Idempotent and exception-safe.
    try:
        _register_bundled_fonts()
    except Exception as _font_err:  # noqa: BLE001 �?never block kernel apply
        warnings.warn(
            f"_register_bundled_fonts failed: "
            f"{type(_font_err).__name__}: {_font_err}; "
            f"continuing with system fonts only.",
            stacklevel=2,
        )

    if variant not in _VARIANTS:
        raise KeyError(f"unknown kernel variant {variant!r}; "
                       f"choices: {sorted(_VARIANTS)}")
    rc = dict(_KERNEL_BASE)
    rc.update(_VARIANTS[variant])

    if journalProfile:
        if journalProfile.get("font_family"):
            rc["font.family"] = _prefer_dejavu_first(list(journalProfile["font_family"]))
            rc["font.sans-serif"] = _prefer_dejavu_first(list(journalProfile["font_family"]))
        if journalProfile.get("font_size_body_pt"):
            rc["font.size"] = float(journalProfile["font_size_body_pt"])
        if journalProfile.get("axis_linewidth_pt"):
            rc["axes.linewidth"] = float(journalProfile["axis_linewidth_pt"])
        rc["legend.fontsize"] = float(journalProfile.get("legend_font_size_pt", 7))

    # Filter font.family to only installed families (suppresses findfont
    # warnings for cross-platform CJK fallbacks). MUST happen after the
    # journalProfile override so user-specified fonts are still honored.
    if isinstance(rc.get("font.family"), list):
        rc["font.family"] = _filter_available_fonts(rc["font.family"])
    if isinstance(rc.get("font.sans-serif"), list):
        rc["font.sans-serif"] = _filter_available_fonts(rc["font.sans-serif"])

    rc["xtick.direction"] = "in"
    rc["ytick.direction"] = "in"
    plt.rcParams.update(rc)


# ============================================================================
# 2. PALETTE BANK  (03-palette-bank.md)
# ============================================================================

FALLBACK_PALETTE = ["#1F3A5F", "#C8553D", "#4C956C"]
FALLBACK_SEMANTIC_ROLES = {
    "control": "#1F4E79",
    "treatment": "#C8553D",
    "actual": "#1F4E79",
    "observed": "#1F4E79",
    "predicted": "#C8553D",
    "positive_correlation": "#C0504D",
    "negative_correlation": "#4F81BD",
    "shap_positive": "#C0504D",
    "shap_negative": "#4F81BD",
}
_PALETTE_CACHE: dict | None = None


def _resolve_skill_root() -> Path:
    injected_root = globals().get("__SCIFIG_SKILL_ROOT__")
    if injected_root:
        return Path(str(injected_root)).expanduser().resolve()
    try:
        candidate = Path(__file__).resolve().parents[1]
        # Validate: must contain resources/template-palette-registry.json
        if (candidate / "resources" / "template-palette-registry.json").exists():
            return candidate
    except (NameError, IndexError):
        pass
    # Fallback: search cwd for scifig
    for base in [Path.cwd(), *Path.cwd().parents]:
        candidate = base / "scifig"
        if (candidate / "resources" / "template-palette-registry.json").exists():
            return candidate.resolve()
    return Path.cwd().resolve()


def _load_palette_registry() -> dict:
    global _PALETTE_CACHE
    if _PALETTE_CACHE is None:
        skill_root = _resolve_skill_root()
        try:
            with open(skill_root / "resources" / "template-palette-registry.json", encoding="utf-8") as f:
                _PALETTE_CACHE = json.load(f)
        except Exception:
            _PALETTE_CACHE = {
                "categorical": {
                    "nature_radar_dual": {
                        "anchors": list(FALLBACK_PALETTE),
                    },
                    "template_case_hex": {
                        "anchors": list(FALLBACK_PALETTE),
                    },
                },
                "sequential": {},
                "diverging": {},
                "semantic_roles": dict(FALLBACK_SEMANTIC_ROLES),
            }
    return _PALETTE_CACHE


def _registry_palette_choices(registry: dict) -> dict[str, list[str]]:
    choices = {}
    for section in ("categorical", "sequential", "diverging"):
        for name, meta in registry.get(section, {}).items():
            if isinstance(meta, dict):
                choices[name] = list(meta.get("anchors", []))
    return choices


def resolve_palette(name: str, n: int | None = None,
                    journalProfile: dict | None = None) -> list[str]:
    """Return the hex list for a named palette. Truncates or cycles to n if given.
    journalProfile.palette_overrides[name] takes precedence."""
    if journalProfile and "palette_overrides" in journalProfile:
        overrides = journalProfile["palette_overrides"]
        if name in overrides:
            return list(overrides[name])
    registry = _load_palette_registry()
    choices = _registry_palette_choices(registry)
    if name not in choices:
        raise KeyError(f"palette {name!r} not in template-palette-registry.json; "
                       f"choices: {sorted(choices)}")
    palette = list(choices[name])
    if n is None:
        return palette
    if n <= len(palette):
        return palette[:n]
    return [palette[i % len(palette)] for i in range(n)]


def role_color(role: str, palette: list[str] | None = None) -> str:
    """Lookup a semantic role from template-palette-registry.json."""
    registry = _load_palette_registry()
    role_map = {**FALLBACK_SEMANTIC_ROLES, **registry.get("semantic_roles", {})}
    # Legacy aliases: "train" �?"TRAIN_BLUE", "test" �?"TEST_RED"
    _LEGACY_ROLE_ALIASES = {"train": "TRAIN_BLUE", "test": "TEST_RED"}
    key = _LEGACY_ROLE_ALIASES.get(role, role if role in role_map else role.upper())
    if key not in role_map:
        raise KeyError(f"role {role!r} not in template-palette-registry.json semantic_roles")
    value = role_map[key]
    if isinstance(value, str) and value.startswith("palette[") and palette:
        if value == "palette[0]":
            return palette[0]
        if value == "palette[-1]":
            return palette[-1]
    return value


def resolve_method_style_map(methods: Sequence[str] | None = None,
                             *,
                             variant: str = "cej_adsorption") -> dict[str, dict]:
    """Return template-derived line/marker semantics for method comparison panels.

    Anchor case 002 (CEJ adsorption isotherms) uses a semantic style map rather
    than arbitrary categorical colors: OR is cyan support, IL is the red focal
    model, experimental observations are blue hollow markers, and GCMC
    simulation is black hollow markers. Unknown methods fall back to a muted
    multi-model palette while preserving the same zorder hierarchy.
    """
    base = {
        "or": {
            "color": "#00CED1", "marker": "^", "linestyle": "-",
            "markerfacecolor": "#00CED1", "markeredgecolor": "#00CED1",
            "zorder": 3, "draw": "line_marker",
        },
        "il": {
            "color": "#FF0000", "marker": "o", "linestyle": "-",
            "markerfacecolor": "#FF0000", "markeredgecolor": "#FF0000",
            "zorder": 4, "draw": "line_marker",
        },
        "experiment": {
            "color": "#1E90FF", "marker": "o", "linestyle": "None",
            "markerfacecolor": "white", "markeredgecolor": "#1E90FF",
            "zorder": 7, "draw": "hollow_marker",
        },
        "observed": {
            "color": "#1E90FF", "marker": "o", "linestyle": "None",
            "markerfacecolor": "white", "markeredgecolor": "#1E90FF",
            "zorder": 7, "draw": "hollow_marker",
        },
        "measured": {
            "color": "#1E90FF", "marker": "o", "linestyle": "None",
            "markerfacecolor": "white", "markeredgecolor": "#1E90FF",
            "zorder": 7, "draw": "hollow_marker",
        },
        "gcmc": {
            "color": "#111111", "marker": "o", "linestyle": "None",
            "markerfacecolor": "white", "markeredgecolor": "#111111",
            "zorder": 6, "draw": "hollow_marker",
        },
        "simulation": {
            "color": "#111111", "marker": "o", "linestyle": "None",
            "markerfacecolor": "white", "markeredgecolor": "#111111",
            "zorder": 6, "draw": "hollow_marker",
        },
    }
    fallback = ["#4A6B8A", "#5FA896", "#D9A75A", "#B85B5B", "#7A6C8F"]
    styles: dict[str, dict] = {}
    for idx, method in enumerate(methods or []):
        label = str(method)
        key = label.lower()
        chosen = None
        for token, style in base.items():
            if token in key:
                chosen = dict(style)
                break
        if chosen is None:
            color = fallback[idx % len(fallback)]
            chosen = {
                "color": color, "marker": "o", "linestyle": "-",
                "markerfacecolor": color, "markeredgecolor": color,
                "zorder": 3, "draw": "line_marker",
            }
        styles[label] = chosen
    return styles


def resolve_forest_model_style_map(models: Sequence[str] | None = None,
                                   *,
                                   variant: str = "nature_hr_adjustment") -> dict[str, dict]:
    """Return template-derived model semantics for faceted HR forest plots.

    Anchor case 003 (Nature Communications HR forest) uses stable adjustment-tier
    colors instead of cycling arbitrary categories: Model 1 is muted blue,
    Model 2 is orange-red, and Model 3 is green. Unknown model labels keep the
    same marker/whisker grammar while cycling through the source palette.
    """
    palette = ["#8DA0CB", "#FC8D62", "#66C2A5", "#FBC15E"]
    model_order = {
        "model 1": 0, "model1": 0, "m1": 0, "base": 0, "basic": 0,
        "model 2": 1, "model2": 1, "m2": 1, "adjusted": 1,
        "model 3": 2, "model3": 2, "m3": 2, "fully adjusted": 2,
    }
    styles: dict[str, dict] = {}
    for idx, model in enumerate(models or []):
        label = str(model)
        key = label.lower().strip()
        palette_idx = model_order.get(key, idx) % len(palette)
        color = palette[palette_idx]
        styles[label] = {
            "color": color,
            "marker": "o",
            "markerfacecolor": color,
            "markeredgecolor": "white",
            "markeredgewidth": 0.6,
            "elinewidth": 2.0,
            "capsize": 4,
            "markersize": 8,
            "zorder": 10,
        }
    return styles


def resolve_parity_split_style_map(splits: Sequence[str] | None = None,
                                   *,
                                   variant: str = "spt_train_test") -> dict[str, dict]:
    """Return template-derived train/test styling for parity CI matrices.

    Anchor case 004 (Separation and Purification Technology parity matrix)
    uses a dark blue / dark red pair with hollow markers. The line and CI band
    inherit the split color so the regression evidence stays connected to the
    point cloud.
    """
    if variant in {"nested_marginal_joint", "marginal_joint_matrix"}:
        base = {
            "train": "#d62728",
            "training": "#d62728",
            "training data": "#d62728",
            "test": "#1f77b4",
            "testing": "#1f77b4",
            "testing data": "#1f77b4",
        }
        fallback = ["#d62728", "#1f77b4", "#9467bd", "#2ca02c"]
    else:
        base = {
            "train": "#313695",
            "training": "#313695",
            "training data": "#313695",
            "test": "#A50026",
            "testing": "#A50026",
            "testing data": "#A50026",
        }
        fallback = ["#313695", "#A50026", "#4477AA", "#CC6677"]
    styles: dict[str, dict] = {}
    for idx, split in enumerate(splits or []):
        label = str(split)
        key = label.lower().strip()
        color = base.get(key, fallback[idx % len(fallback)])
        styles[label] = {
            "color": color,
            "marker": "o",
            "markerfacecolor": "none",
            "markeredgecolor": color,
            "linewidth": 2.0,
            "ci_alpha": 0.15,
            "scatter_alpha": 0.72,
            "scatter_size": 54,
            "zorder_scatter": 5,
            "zorder_line": 4,
            "zorder_band": 3,
        }
    return styles


def resolve_gam_residual_style_map(groups: Sequence[str] | None = None) -> dict[str, dict]:
    """Return Nature GAM relationship/residual category styling.

    Anchor case 008 uses three semantic layers: ordinary background pairs are
    neutral gray, adjacent/expected links are muted green, and hidden/high
    residual transmission links are warm yellow. The same colors must be reused
    in the residual panel so the anomaly class stays visually connected.
    """
    base = {
        "non": "#B0B0B0", "none": "#B0B0B0", "background": "#B0B0B0",
        "ordinary": "#B0B0B0", "normal": "#B0B0B0",
        "adj": "#5FA896", "adjacent": "#5FA896", "expected": "#5FA896",
        "in": "#FBC15E", "hidden": "#FBC15E", "outlier": "#FBC15E",
        "prison": "#FBC15E", "high residual": "#FBC15E",
    }
    fallback = ["#B0B0B0", "#5FA896", "#FBC15E", "#4C78A8"]
    styles: dict[str, dict] = {}
    for idx, group in enumerate(groups or []):
        label = str(group)
        key = label.lower().strip()
        color = base.get(key, fallback[idx % len(fallback)])
        is_background = color.lower() == "#b0b0b0"
        styles[label] = {
            "color": color,
            "alpha": 0.30 if is_background else 0.66,
            "size": 20 if is_background else 35,
            "zorder": 1 if is_background else 4,
            "linewidth": 0.0,
        }
    return styles


def draw_inset_raincloud(ax: Axes,
                         residuals: Sequence[float],
                         *,
                         color: str = "#008000",
                         rect: Sequence[float] = (0.55, 0.35, 0.40, 0.35),
                         title: str = "Residual",
                         seed: int = 42,
                         max_width: float = 0.38) -> Axes | None:
    """Draw the Case-009 residual raincloud inside a main axes.

    The inset is a micro-chart: white floating axes, half-KDE density, compact
    box, jittered residual points, and a zero residual reference. It returns
    the inset axes for QA counting; ``None`` means the input was too sparse.
    """
    vals = np.asarray(residuals, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size < 3:
        return None

    inset = ax.inset_axes(list(rect), zorder=10)
    inset.set_gid("scifig_inset_raincloud")
    inset.set_facecolor("white")
    inset.patch.set_alpha(0.96)
    for spine in inset.spines.values():
        spine.set_linewidth(0.8)
        spine.set_color("#222222")

    y_min = float(np.nanmin(vals))
    y_max = float(np.nanmax(vals))
    span = max(y_max - y_min, 1e-9)
    pad = span * 0.15
    grid = np.linspace(y_min - pad, y_max + pad, 160)
    density = None
    if vals.size >= 5 and float(np.nanstd(vals)) > 1e-12:
        try:
            from scipy.stats import gaussian_kde
            density = gaussian_kde(vals)(grid)
        except Exception:
            hist, edges = np.histogram(vals, bins=min(12, max(5, int(np.sqrt(vals.size)))), density=True)
            grid = (edges[:-1] + edges[1:]) / 2
            density = hist
    if density is not None and np.nanmax(density) > 0:
        density = density / np.nanmax(density) * max_width
        inset.fill_betweenx(grid, 0, density, color=color, alpha=0.40, linewidth=0, zorder=1)
        inset.plot(density, grid, color=color, linewidth=1.15, zorder=2)

    q1, med, q3 = np.percentile(vals, [25, 50, 75])
    iqr = q3 - q1
    whisker_lo = max(float(np.nanmin(vals)), float(q1 - 1.5 * iqr))
    whisker_hi = min(float(np.nanmax(vals)), float(q3 + 1.5 * iqr))
    box_x = 0.50
    inset.add_patch(plt.Rectangle(
        (box_x - 0.045, q1), 0.09, max(q3 - q1, span * 0.015),
        facecolor="white", edgecolor=color, linewidth=1.0, zorder=3,
    ))
    inset.plot([box_x - 0.045, box_x + 0.045], [med, med],
               color=color, linewidth=1.45, zorder=4)
    inset.plot([box_x, box_x], [whisker_lo, q1], color=color, linewidth=0.85, zorder=3)
    inset.plot([box_x, box_x], [q3, whisker_hi], color=color, linewidth=0.85, zorder=3)
    inset.plot([box_x - 0.035, box_x + 0.035], [whisker_lo, whisker_lo],
               color=color, linewidth=0.85, zorder=3)
    inset.plot([box_x - 0.035, box_x + 0.035], [whisker_hi, whisker_hi],
               color=color, linewidth=0.85, zorder=3)

    rng = np.random.default_rng(seed)
    jitter_x = box_x + 0.13 + rng.random(vals.size) * 0.15
    inset.scatter(jitter_x, vals, s=10, color=color, alpha=0.55,
                  edgecolor="white", linewidth=0.25, zorder=5)
    inset.axhline(0, color="black", linestyle="--", linewidth=0.65, alpha=0.70, zorder=4)
    inset.set_xlim(0, 0.84)
    inset.set_ylim(y_min - pad, y_max + pad)
    inset.set_xticks([])
    inset.tick_params(axis="y", labelsize=5.0, length=2, width=0.45, direction="in")
    inset.set_ylabel("Residual", fontsize=5.2)
    inset.set_title(title, fontsize=5.4, pad=1.5)
    return inset


def draw_shap_bar_beeswarm_inset_pie(df,
                                     feature_col: str,
                                     shap_value_col: str,
                                     *,
                                     feature_value_col: str | None = None,
                                     category_col: str | None = None,
                                     top_n: int = 15,
                                     category_colors: dict[str, str] | None = None,
                                     cmap: str = "RdBu_r",
                                     width_ratios: Sequence[float] = (1.15, 0.05, 1.20, 0.05),
                                     pie_bbox: Sequence[float] = (0.50, 0.20, 0.45, 0.45),
                                     figsize: tuple[float, float] = (15, 6),
                                     seed: int = 42,
                                     col_map: dict | None = None,
                                     zero_reference_fn=None) -> dict:
    """Draw Case-010 SHAP importance bar + density beeswarm + inset pie.

    Input is a long SHAP table: one row per sample-feature pair with feature
    name, SHAP value, optional raw feature value, and optional feature category.
    The helper creates the whole article-specific layout because the bar, swarm,
    inset pie, and colorbar must share one feature order.
    """
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover - pandas is required upstream too
        raise RuntimeError("draw_shap_bar_beeswarm_inset_pie requires pandas") from exc

    if feature_col not in df or shap_value_col not in df:
        raise ValueError("SHAP composite requires feature and shap value columns")
    work = pd.DataFrame({
        "feature": df[feature_col].astype(str),
        "shap": pd.to_numeric(df[shap_value_col], errors="coerce"),
    })
    if feature_value_col and feature_value_col in df:
        work["feature_value"] = pd.to_numeric(df[feature_value_col], errors="coerce")
    else:
        work["feature_value"] = 0.5
    if category_col and category_col in df:
        work["category"] = df[category_col].fillna("Feature").astype(str)
    else:
        work["category"] = "Feature"
    work = work.dropna(subset=["feature", "shap"])
    if work.empty:
        raise ValueError("SHAP composite requires non-empty SHAP rows")

    ranked = (
        work.assign(_abs=work["shap"].abs())
            .groupby("feature")["_abs"].mean()
            .sort_values(ascending=False)
            .head(max(1, int(top_n)))
    )
    order = ranked.index.tolist()
    work = work[work["feature"].isin(order)].copy()
    y_lookup = {feature: i for i, feature in enumerate(order)}

    category_lookup = (
        work.drop_duplicates("feature")
            .set_index("feature")["category"]
            .to_dict()
    )
    default_colors = ["#4DBBD5", "#E64B35", "#00A087", "#7E6148", "#8491B4", "#F39B7F"]
    categories = list(dict.fromkeys(category_lookup.get(feature, "Feature") for feature in order))
    color_map = {}
    for idx, category in enumerate(categories):
        if category_colors and category in category_colors:
            color_map[category] = category_colors[category]
        else:
            color_map[category] = default_colors[idx % len(default_colors)]

    fig = plt.figure(figsize=figsize)
    gs = GridSpec(1, 4, figure=fig, width_ratios=list(width_ratios), wspace=0.10)
    ax_bar = fig.add_subplot(gs[0, 0])
    ax_bee = fig.add_subplot(gs[0, 2], sharey=ax_bar)
    ax_cbar = fig.add_subplot(gs[0, 3])
    ax_bar.set_gid("scifig_shap_importance_bar")
    ax_bee.set_gid("scifig_shap_beeswarm")
    ax_cbar.set_gid("scifig_feature_value_colorbar")

    y_pos = np.arange(len(order))
    bar_colors = [color_map.get(category_lookup.get(feature, "Feature"), "#4DBBD5") for feature in order]
    ax_bar.barh(y_pos, ranked.loc[order].to_numpy(dtype=float),
                color=bar_colors, edgecolor="white", linewidth=0.8,
                height=0.66, zorder=3)
    labels = [str(col_map.get(feature, feature)) if isinstance(col_map, dict) else str(feature)
              for feature in order]
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(labels, fontsize=8, fontweight="bold")
    ax_bar.invert_yaxis()
    ax_bar.set_xlabel("Mean |SHAP|", fontsize=8.5)
    ax_bar.set_facecolor("#FAFAFA")
    ax_bar.grid(axis="x", color="#E0E0E0", linestyle="--", linewidth=0.55, alpha=0.65, zorder=0)
    for spine_name in ("top", "right"):
        ax_bar.spines[spine_name].set_visible(False)
    if len(categories) > 1:
        handles = [mpl.patches.Patch(facecolor=color_map[c], label=c) for c in categories]
        ax_bar.legend(handles=handles, loc="upper right", frameon=False,
                      fontsize=6.5, handlelength=1.0)

    pie_sizes = []
    for category in categories:
        feats = [feature for feature in order if category_lookup.get(feature, "Feature") == category]
        pie_sizes.append(float(ranked.loc[feats].sum()) if feats else 0.0)
    if not any(size > 0 for size in pie_sizes):
        pie_sizes = [1.0]
        pie_colors = ["#BDBDBD"]
    else:
        pie_colors = [color_map[c] for c in categories]
    ax_pie = ax_bar.inset_axes(list(pie_bbox), transform=ax_bar.transAxes, zorder=10)
    ax_pie.set_gid("scifig_shap_inset_pie")
    ax_pie.pie(
        pie_sizes,
        colors=pie_colors,
        autopct="%1.1f%%",
        startangle=90,
        explode=tuple([0.02] * len(pie_sizes)),
        textprops={"fontsize": 5.2, "color": "#222222"},
        wedgeprops={"linewidth": 0.45, "edgecolor": "white"},
    )
    ax_pie.set_aspect("equal")

    rng = np.random.default_rng(seed)
    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    for feature in order:
        sub = work[work["feature"] == feature]
        s_vals = sub["shap"].to_numpy(dtype=float)
        raw_vals = sub["feature_value"].to_numpy(dtype=float)
        raw_min = float(np.nanmin(raw_vals)) if len(raw_vals) else 0.0
        raw_max = float(np.nanmax(raw_vals)) if len(raw_vals) else 1.0
        raw_norm = (raw_vals - raw_min) / max(raw_max - raw_min, 1e-12)
        density = np.ones_like(s_vals, dtype=float)
        if len(s_vals) >= 5 and float(np.nanstd(s_vals)) > 1e-12:
            try:
                from scipy.stats import gaussian_kde
                density = gaussian_kde(s_vals)(s_vals)
            except Exception:
                hist, edges = np.histogram(s_vals, bins=min(20, max(6, int(np.sqrt(len(s_vals))))), density=True)
                bucket = np.clip(np.searchsorted(edges, s_vals, side="right") - 1, 0, len(hist) - 1)
                density = hist[bucket]
        density = density / max(float(np.nanmax(density)), 1e-12)
        jitter = (rng.random(len(s_vals)) - 0.5) * 2 * (density * 0.38)
        y = y_lookup[feature] + jitter
        ax_bee.scatter(s_vals, y, s=15, c=raw_norm, cmap=cmap, norm=norm,
                       alpha=0.72, edgecolors="gray", linewidth=0.20, zorder=3)

    if zero_reference_fn is not None:
        try:
            zero_reference_fn(ax_bee, axis="x", color="black", lw=1.0, ls="-", zorder=2)
        except Exception:
            ax_bee.axvline(0, color="black", linewidth=1.0, zorder=2)
    else:
        ax_bee.axvline(0, color="black", linewidth=1.0, zorder=2)
    ax_bee.set_yticks(y_pos)
    ax_bee.set_yticklabels([])
    ax_bee.set_xlabel("SHAP value (impact on prediction)", fontsize=8.5)
    ax_bee.grid(axis="y", linestyle="--", color="#BDBDBD", alpha=0.30, linewidth=0.65, zorder=0)
    ax_bee.tick_params(axis="y", length=0)
    for spine_name in ("top", "right", "left"):
        ax_bee.spines[spine_name].set_visible(False)

    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=ax_cbar)
    cbar.set_label("Feature value", fontsize=8, rotation=270, labelpad=13)
    cbar.set_ticks([0, 1])
    cbar.set_ticklabels(["Low", "High"])
    cbar.ax.tick_params(labelsize=7, length=3, direction="in")
    return {
        "fig": fig,
        "ax_bar": ax_bar,
        "ax_bee": ax_bee,
        "ax_cbar": ax_cbar,
        "ax_pie": ax_pie,
        "order": order,
        "top_n": len(order),
        "categories": categories,
    }


def draw_lollipop_shap_beeswarm_board(df,
                                      feature_col: str,
                                      shap_value_col: str,
                                      *,
                                      importance_col: str | None = None,
                                      feature_value_col: str | None = None,
                                      top_n: int = 15,
                                      width_ratios: Sequence[float] = (1.0, 2.5),
                                      figsize: tuple[float, float] = (12, 6),
                                      wspace: float = 0.05,
                                      adjust: dict | None = None,
                                      stem_color: str = "grey",
                                      point_color: str = "teal",
                                      cmap: str = "coolwarm",
                                      seed: int = 42,
                                      col_map: dict | None = None,
                                      zero_reference_fn=None) -> dict:
    """Draw Case-021 XGBoost importance lollipop + SHAP beeswarm board."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_lollipop_shap_beeswarm_board requires pandas") from exc

    if feature_col not in df or shap_value_col not in df:
        raise ValueError("lollipop SHAP board requires feature and shap value columns")

    work = pd.DataFrame({
        "feature": df[feature_col].astype(str),
        "shap": pd.to_numeric(df[shap_value_col], errors="coerce"),
    })
    if importance_col and importance_col in df:
        work["importance"] = pd.to_numeric(df[importance_col], errors="coerce")
    else:
        work["importance"] = np.nan
    if feature_value_col and feature_value_col in df:
        work["feature_value"] = pd.to_numeric(df[feature_value_col], errors="coerce")
    else:
        work["feature_value"] = 0.5
    work = work.dropna(subset=["feature", "shap"])
    if work.empty:
        raise ValueError("lollipop SHAP board requires non-empty SHAP rows")

    importance = work.groupby("feature")["importance"].mean()
    if importance.notna().sum() == 0:
        importance = work.assign(_abs=work["shap"].abs()).groupby("feature")["_abs"].mean()
    else:
        fallback = work.assign(_abs=work["shap"].abs()).groupby("feature")["_abs"].mean()
        importance = importance.fillna(fallback)
    importance = importance.sort_values(ascending=False).head(max(1, int(top_n)))
    order = importance.index.tolist()
    work = work[work["feature"].isin(order)].copy()
    y_lookup = {feature: i for i, feature in enumerate(order)}

    fig, (ax_imp, ax_bee) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=figsize,
        sharey=True,
        gridspec_kw={"width_ratios": list(width_ratios), "wspace": float(wspace)},
    )
    if adjust is None:
        adjust = {"left": 0.15, "right": 0.90, "top": 0.90, "bottom": 0.15}
    fig.subplots_adjust(**adjust)
    ax_imp.set_gid("scifig_lollipop_shap_importance")
    ax_bee.set_gid("scifig_lollipop_shap_beeswarm")

    y_pos = np.arange(len(order))
    labels = [str(col_map.get(feature, feature)) if isinstance(col_map, dict) else str(feature)
              for feature in order]
    stems = ax_imp.hlines(
        y=y_pos,
        xmin=0,
        xmax=importance.loc[order].to_numpy(dtype=float),
        color=stem_color,
        linewidth=1.5,
        zorder=1,
    )
    stems.set_gid("scifig_lollipop_importance_stems")
    points = ax_imp.scatter(
        importance.loc[order].to_numpy(dtype=float),
        y_pos,
        color=point_color,
        s=40,
        zorder=2,
    )
    points.set_gid("scifig_lollipop_importance_points")
    ax_imp.set_yticks(y_pos)
    ax_imp.set_yticklabels(labels, fontsize=8.0, fontweight="bold")
    ax_imp.invert_yaxis()
    ax_imp.set_xlabel("Feature Importance", fontsize=8.5)
    ax_imp.grid(axis="x", color="#D9D9D9", linestyle="--", linewidth=0.55, alpha=0.70, zorder=0)
    ax_imp.spines["top"].set_visible(False)
    ax_imp.spines["right"].set_visible(False)

    rng = np.random.default_rng(seed)
    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    cmap_obj = plt.get_cmap(cmap)
    scatters = []
    for feature in order:
        sub = work[work["feature"] == feature]
        s_vals = sub["shap"].to_numpy(dtype=float)
        raw_vals = sub["feature_value"].to_numpy(dtype=float)
        raw_min = float(np.nanmin(raw_vals)) if len(raw_vals) else 0.0
        raw_max = float(np.nanmax(raw_vals)) if len(raw_vals) else 1.0
        raw_norm = (raw_vals - raw_min) / max(raw_max - raw_min, 1e-12)
        density = np.ones_like(s_vals, dtype=float)
        if len(s_vals) >= 5 and float(np.nanstd(s_vals)) > 1e-12:
            try:
                from scipy.stats import gaussian_kde
                density = gaussian_kde(s_vals)(s_vals)
            except Exception:
                hist, edges = np.histogram(s_vals, bins=min(20, max(6, int(np.sqrt(len(s_vals))))), density=True)
                bucket = np.clip(np.searchsorted(edges, s_vals, side="right") - 1, 0, len(hist) - 1)
                density = hist[bucket]
        density = density / max(float(np.nanmax(density)), 1e-12)
        jitter = (rng.random(len(s_vals)) - 0.5) * 2 * (density * 0.36)
        scatter = ax_bee.scatter(
            s_vals,
            y_lookup[feature] + jitter,
            c=raw_norm,
            cmap=cmap_obj,
            norm=norm,
            s=14,
            alpha=0.78,
            edgecolors="white",
            linewidth=0.20,
            zorder=3,
        )
        scatter.set_gid("scifig_lollipop_shap_points")
        scatters.append(scatter)

    if zero_reference_fn is not None:
        before = len(ax_bee.lines)
        zero_line = zero_reference_fn(ax_bee, axis="x", color="gray", lw=1.0, ls="--", zorder=2)
        if zero_line is None and len(ax_bee.lines) > before:
            zero_line = ax_bee.lines[-1]
    else:
        zero_line = ax_bee.axvline(0, color="gray", linestyle="--", linewidth=1.0, zorder=2)
    if zero_line is not None:
        zero_line.set_gid("scifig_lollipop_shap_zero_reference")
    ax_bee.set_xlabel("SHAP value (impact on model output)", fontsize=8.5)
    ax_bee.tick_params(axis="y", left=False, labelleft=False)
    ax_bee.grid(axis="y", linestyle="--", color="#BDBDBD", alpha=0.30, linewidth=0.7, zorder=0)
    ax_bee.spines["top"].set_visible(False)
    ax_bee.spines["right"].set_visible(False)
    ax_bee.spines["left"].set_visible(False)

    return {
        "fig": fig,
        "ax_importance": ax_imp,
        "ax_beeswarm": ax_bee,
        "stems": stems,
        "importance_points": points,
        "shap_points": scatters,
        "zero_line": zero_line,
        "order": order,
        "top_n": len(order),
        "width_ratios": list(width_ratios),
        "shared_feature_order": True,
    }


def draw_bipolar_lollipop_ale_board(df,
                                    feature_col: str,
                                    importance_col: str,
                                    ale_col: str,
                                    *,
                                    top_n: int = 15,
                                    figsize: tuple[float, float] = (10, 6),
                                    wspace: float = 0.15,
                                    importance_color: str = "#4A6B8A",
                                    positive_color: str = "#C0504D",
                                    negative_color: str = "#4F81BD",
                                    stem_width: float = 2.5,
                                    marker_size: float = 80,
                                    col_map: dict | None = None,
                                    zero_reference_fn=None) -> dict:
    """Draw Case-022 paired PFI importance + signed ALE lollipop board."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_bipolar_lollipop_ale_board requires pandas") from exc

    missing = [col for col in (feature_col, importance_col, ale_col) if col not in df]
    if missing:
        raise ValueError(f"bipolar lollipop ALE board missing required columns: {missing}")

    work = pd.DataFrame({
        "feature": df[feature_col].astype(str),
        "importance": pd.to_numeric(df[importance_col], errors="coerce"),
        "ale": pd.to_numeric(df[ale_col], errors="coerce"),
    }).replace([np.inf, -np.inf], np.nan).dropna(subset=["feature", "importance", "ale"])
    if work.empty:
        raise ValueError("bipolar lollipop ALE board requires finite rows")
    work = (
        work.groupby("feature", as_index=False)
            .agg({"importance": "mean", "ale": "mean"})
            .assign(_order=lambda d: d["importance"].abs())
            .sort_values("_order", ascending=False)
            .head(max(1, int(top_n)))
            .reset_index(drop=True)
    )

    y_pos = np.arange(len(work))
    labels = [str(col_map.get(feature, feature)) if isinstance(col_map, dict) else str(feature)
              for feature in work["feature"].tolist()]
    fig, (ax_imp, ax_ale) = plt.subplots(
        1,
        2,
        figsize=figsize,
        sharey=True,
        gridspec_kw={"wspace": float(wspace)},
    )
    ax_imp.set_gid("scifig_bipolar_lollipop_importance")
    ax_ale.set_gid("scifig_bipolar_lollipop_ale")

    imp_vals = work["importance"].to_numpy(dtype=float)
    imp_stems = ax_imp.hlines(
        y=y_pos,
        xmin=0,
        xmax=imp_vals,
        color=importance_color,
        linewidth=float(stem_width),
        zorder=1,
    )
    imp_stems.set_gid("scifig_bipolar_lollipop_importance_stems")
    imp_points = ax_imp.scatter(imp_vals, y_pos, color=importance_color,
                                s=float(marker_size), zorder=2)
    imp_points.set_gid("scifig_bipolar_lollipop_importance_points")
    ax_imp.set_yticks(y_pos)
    ax_imp.set_yticklabels(labels, fontsize=8.0, fontweight="bold")
    ax_imp.invert_yaxis()
    ax_imp.set_xlabel("Feature Importance", fontweight="bold")
    ax_imp.spines["top"].set_visible(False)
    ax_imp.spines["right"].set_visible(False)
    ax_imp.grid(axis="x", color="#E0E0E0", linestyle="--", linewidth=0.6, zorder=0)

    ale_vals = work["ale"].to_numpy(dtype=float)
    colors = [positive_color if val > 0 else negative_color for val in ale_vals]
    if zero_reference_fn is not None:
        before = len(ax_ale.lines)
        zero_line = zero_reference_fn(ax_ale, axis="x", color="gray", lw=1.2, ls="--", zorder=0)
        if zero_line is None and len(ax_ale.lines) > before:
            zero_line = ax_ale.lines[-1]
    else:
        zero_line = ax_ale.axvline(0, color="gray", linestyle="--", linewidth=1.2, zorder=0)
    if zero_line is not None:
        zero_line.set_gid("scifig_bipolar_lollipop_zero_reference")
    ale_stems = ax_ale.hlines(
        y=y_pos,
        xmin=0,
        xmax=ale_vals,
        color=colors,
        linewidth=float(stem_width),
        zorder=1,
    )
    ale_stems.set_gid("scifig_bipolar_lollipop_ale_stems")
    ale_points = ax_ale.scatter(ale_vals, y_pos, color=colors,
                                s=float(marker_size), zorder=2)
    ale_points.set_gid("scifig_bipolar_lollipop_ale_points")
    ax_ale.set_yticks(y_pos)
    ax_ale.set_yticklabels([])
    ax_ale.set_xlabel("ALE of Features", fontweight="bold")
    ax_ale.spines["left"].set_visible(False)
    ax_ale.spines["top"].set_visible(False)
    ax_ale.spines["right"].set_visible(False)
    ax_ale.tick_params(axis="y", left=False)
    ax_ale.grid(axis="x", color="#E0E0E0", linestyle="--", linewidth=0.6, zorder=0)

    return {
        "fig": fig,
        "ax_importance": ax_imp,
        "ax_ale": ax_ale,
        "importance_stems": imp_stems,
        "importance_points": imp_points,
        "ale_stems": ale_stems,
        "ale_points": ale_points,
        "zero_line": zero_line,
        "order": work["feature"].tolist(),
        "top_n": len(work),
        "positive_count": int(np.sum(ale_vals > 0)),
        "negative_count": int(np.sum(ale_vals <= 0)),
        "shared_feature_order": True,
    }


def draw_shap_bar_pie_summary_board(df,
                                    feature_col: str,
                                    shap_value_col: str,
                                    *,
                                    feature_value_col: str | None = None,
                                    category_col: str | None = None,
                                    top_n: int = 15,
                                    category_colors: dict[str, str] | None = None,
                                    cmap: str = "coolwarm",
                                    width_ratios: Sequence[float] = (1.2, 0.8, 1.5),
                                    height_ratios: Sequence[float] = (1.0, 1.0),
                                    figsize: tuple[float, float] = (16, 6),
                                    seed: int = 42,
                                    col_map: dict | None = None,
                                    zero_reference_fn=None) -> dict:
    """Draw Case-019 SHAP importance bar + standalone category pie + summary.

    Input is a long SHAP table. The layout follows the article's asymmetric
    `GridSpec(2, 3)`: panel (a) spans the first column, panel (b) is a
    standalone pie in the upper middle cell, and panel (c) spans the right
    column with a SHAP summary beeswarm and feature-value colorbar.
    """
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover - pandas is required upstream too
        raise RuntimeError("draw_shap_bar_pie_summary_board requires pandas") from exc

    if feature_col not in df or shap_value_col not in df:
        raise ValueError("SHAP bar-pie-summary board requires feature and shap value columns")
    work = pd.DataFrame({
        "feature": df[feature_col].astype(str),
        "shap": pd.to_numeric(df[shap_value_col], errors="coerce"),
    })
    if feature_value_col and feature_value_col in df:
        work["feature_value"] = pd.to_numeric(df[feature_value_col], errors="coerce")
    else:
        work["feature_value"] = 0.5
    if category_col and category_col in df:
        work["category"] = df[category_col].fillna("Descriptor").astype(str)
    else:
        work["category"] = "Descriptor"
    work = work.dropna(subset=["feature", "shap"])
    if work.empty:
        raise ValueError("SHAP bar-pie-summary board requires non-empty SHAP rows")

    ranked = (
        work.assign(_abs=work["shap"].abs())
            .groupby("feature")["_abs"].mean()
            .sort_values(ascending=False)
            .head(max(1, int(top_n)))
    )
    order = ranked.index.tolist()
    work = work[work["feature"].isin(order)].copy()
    y_lookup = {feature: i for i, feature in enumerate(order)}

    category_lookup = (
        work.drop_duplicates("feature")
            .set_index("feature")["category"]
            .to_dict()
    )
    default_colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B3", "#CCB974", "#64B5CD"]
    categories = list(dict.fromkeys(category_lookup.get(feature, "Descriptor") for feature in order))
    color_map = {}
    for idx, category in enumerate(categories):
        if category_colors and category in category_colors:
            color_map[category] = category_colors[category]
        else:
            color_map[category] = default_colors[idx % len(default_colors)]

    fig = plt.figure(figsize=figsize)
    gs = GridSpec(
        2,
        3,
        figure=fig,
        width_ratios=list(width_ratios),
        height_ratios=list(height_ratios),
        wspace=0.35,
        hspace=0.30,
    )
    ax_bar = fig.add_subplot(gs[:, 0])
    ax_pie = fig.add_subplot(gs[0, 1])
    ax_bee = fig.add_subplot(gs[:, 2], sharey=ax_bar)
    ax_bar.set_gid("scifig_shap_importance_bar")
    ax_pie.set_gid("scifig_shap_standalone_pie")
    ax_bee.set_gid("scifig_shap_summary_beeswarm")

    y_pos = np.arange(len(order))
    labels = [str(col_map.get(feature, feature)) if isinstance(col_map, dict) else str(feature)
              for feature in order]
    ax_bar.barh(
        y_pos,
        ranked.loc[order].to_numpy(dtype=float),
        height=0.60,
        color="#4C72B0",
        edgecolor="black",
        linewidth=1.0,
        zorder=3,
    )
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(labels, fontsize=8, fontweight="bold")
    ax_bar.invert_yaxis()
    ax_bar.set_xlabel("Mean |SHAP|", fontsize=8.5)
    ax_bar.grid(axis="x", color="#D9D9D9", linestyle="--", linewidth=0.55, alpha=0.70, zorder=0)
    for spine_name in ("top", "right"):
        ax_bar.spines[spine_name].set_visible(False)

    pie_sizes = [sum(1 for feature in order if category_lookup.get(feature, "Descriptor") == category)
                 for category in categories]
    if not any(size > 0 for size in pie_sizes):
        pie_sizes = [1]
        pie_labels = ["Descriptor"]
        pie_colors = ["#BDBDBD"]
    else:
        pie_labels = categories
        pie_colors = [color_map[category] for category in categories]
    ax_pie.pie(
        pie_sizes,
        labels=pie_labels,
        colors=pie_colors,
        autopct="%1.1f%%",
        startangle=90,
        textprops={"fontsize": 6.0, "color": "#222222"},
        wedgeprops={"edgecolor": "black", "linewidth": 0.8},
    )
    ax_pie.set_aspect("equal")

    rng = np.random.default_rng(seed)
    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    for feature in order:
        sub = work[work["feature"] == feature]
        s_vals = sub["shap"].to_numpy(dtype=float)
        raw_vals = sub["feature_value"].to_numpy(dtype=float)
        raw_min = float(np.nanmin(raw_vals)) if len(raw_vals) else 0.0
        raw_max = float(np.nanmax(raw_vals)) if len(raw_vals) else 1.0
        raw_norm = (raw_vals - raw_min) / max(raw_max - raw_min, 1e-12)
        density = np.ones_like(s_vals, dtype=float)
        if len(s_vals) >= 5 and float(np.nanstd(s_vals)) > 1e-12:
            try:
                from scipy.stats import gaussian_kde
                density = gaussian_kde(s_vals)(s_vals)
            except Exception:
                hist, edges = np.histogram(s_vals, bins=min(20, max(6, int(np.sqrt(len(s_vals))))), density=True)
                bucket = np.clip(np.searchsorted(edges, s_vals, side="right") - 1, 0, len(hist) - 1)
                density = hist[bucket]
        density = density / max(float(np.nanmax(density)), 1e-12)
        jitter = (rng.random(len(s_vals)) - 0.5) * 2 * (density * 0.36)
        y = y_lookup[feature] + jitter
        scatter = ax_bee.scatter(
            s_vals,
            y,
            s=15,
            c=raw_norm,
            cmap=cmap,
            norm=norm,
            alpha=0.78,
            edgecolors="white",
            linewidth=0.20,
            zorder=3,
        )
        scatter.set_gid("scifig_shap_summary_points")

    line_count_before = len(ax_bee.lines)
    if zero_reference_fn is not None:
        try:
            zero_line = zero_reference_fn(ax_bee, axis="x", color="black", lw=1.0, ls="-", zorder=2)
        except Exception:
            zero_line = ax_bee.axvline(0, color="black", linewidth=1.0, zorder=2)
    else:
        zero_line = ax_bee.axvline(0, color="black", linewidth=1.0, zorder=2)
    if zero_line is None and len(ax_bee.lines) > line_count_before:
        zero_line = ax_bee.lines[-1]
    if zero_line is not None:
        try:
            zero_line.set_gid("scifig_shap_summary_zero_reference")
        except Exception:
            pass
    ax_bee.set_yticks(y_pos)
    ax_bee.set_yticklabels([])
    ax_bee.set_xlabel("SHAP value (impact on prediction)", fontsize=8.5)
    ax_bee.grid(axis="y", linestyle="--", color="#BDBDBD", alpha=0.30, linewidth=0.65, zorder=0)
    ax_bee.tick_params(axis="y", length=0)
    for spine_name in ("top", "right", "left"):
        ax_bee.spines[spine_name].set_visible(False)

    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_bee, fraction=0.046, pad=0.04)
    cbar.ax.set_gid("scifig_feature_value_colorbar")
    cbar.set_label("Feature Value", fontsize=8, labelpad=10)
    cbar.set_ticks([0, 1])
    cbar.set_ticklabels(["Low", "High"])
    cbar.ax.tick_params(labelsize=7, length=3, direction="in")

    for label, axis in zip(("(a)", "(b)", "(c)"), (ax_bar, ax_pie, ax_bee)):
        text = axis.text(
            -0.10,
            1.04,
            label,
            transform=axis.transAxes,
            fontsize=9,
            fontweight="bold",
            va="bottom",
            ha="left",
        )
        text.set_gid("scifig_shap_bar_pie_panel_label")

    return {
        "fig": fig,
        "ax_bar": ax_bar,
        "ax_pie": ax_pie,
        "ax_bee": ax_bee,
        "ax_cbar": cbar.ax,
        "order": order,
        "top_n": len(order),
        "categories": categories,
    }


# ============================================================================
# 3. ANNOTATION IDIOMS  (05-annotation-idioms.md)
# ============================================================================

def add_metric_box(ax: Axes, metrics: dict[str, str | float], *,
                   loc: str = "top_left", fontsize: int = 6,
                   pad: float = 0.28, lw: float = 0.45) -> None:
    """Place a metric text box with white fill + thin black border (idiom I1).

    metrics: dict mapping label �?value. Values formatted with default precision.
             Keys may use $...$ for math.
    loc: 'top_left' (default), 'top_right', 'bottom_left', 'bottom_right'.
    """
    positions = {
        "top_left":     (0.05, 0.95, "top",    "left"),
        "top_right":    (0.95, 0.95, "top",    "right"),
        "bottom_left":  (0.05, 0.05, "bottom", "left"),
        "bottom_right": (0.95, 0.05, "bottom", "right"),
    }
    if loc not in positions:
        raise KeyError(f"loc {loc!r} invalid; choices: {sorted(positions)}")
    x, y, va, ha = positions[loc]

    lines = []
    for k, v in metrics.items():
        if isinstance(v, float):
            lines.append(f"{k} = {v:.3f}")
        else:
            lines.append(f"{k} = {v}")
    text = "\n".join(lines)

    ax.text(x, y, text, transform=ax.transAxes, va=va, ha=ha,
            fontsize=fontsize, fontweight="bold",
            bbox=dict(boxstyle=f"square,pad={pad}", fc="white",
                      ec="black", lw=lw),
            zorder=20)


def add_perfect_fit_diagonal(ax: Axes,
                              x: np.ndarray, y: np.ndarray, *,
                              color: str = "black",
                              lw: float = 1.0,
                              alpha: float = 0.6,
                              percentile: float | None = None) -> None:
    """Add y=x dashed diagonal for predicted-vs-actual scatter (idiom I2).
    Sets equal aspect ratio.

    percentile: when given (e.g. 99.5), clip the diagonal range to the [p, 100-p]
                joint percentile of x and y. Use this for noisy density scatter
                where a few outliers would otherwise stretch the diagonal far
                beyond the data bulk. None (default) uses the full min/max range.

    Degenerate-input guard: when the joint x/y range is zero or non-finite (single
    point, all NaN), the diagonal is drawn over a small symbolic range around the
    midpoint so matplotlib does not emit the "singular transformation" warning.
    """
    if percentile is not None:
        p_lo = (100.0 - percentile)
        p_hi = percentile
        lo = float(min(np.percentile(x, p_lo), np.percentile(y, p_lo)))
        hi = float(max(np.percentile(x, p_hi), np.percentile(y, p_hi)))
    else:
        lo = float(min(np.min(x), np.min(y)))
        hi = float(max(np.max(x), np.max(y)))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        # Degenerate range �?fall back to a sensible symbolic interval centered
        # on the midpoint (or 0 if midpoint also degenerate).
        mid = (lo + hi) / 2.0 if np.isfinite(lo) and np.isfinite(hi) else 0.0
        half = max(abs(mid) * 0.10, 0.5)
        lo, hi = mid - half, mid + half
    pad = max((hi - lo) * 0.05, 1e-6)
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad],
            color=color, linestyle="--", linewidth=lw, alpha=alpha, zorder=6)
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_aspect("equal")


def add_zero_reference(ax: Axes, *, axis: str = "y",
                        color: str = "#222222",
                        lw: float = 1.0, ls: str = "--",
                        zorder: int = 5) -> None:
    """Add a dashed zero reference line (idiom I4). axis='y' �?axhline; 'x' �?axvline."""
    if axis == "y":
        ax.axhline(0, color=color, linestyle=ls, linewidth=lw, zorder=zorder)
    elif axis == "x":
        ax.axvline(0, color=color, linestyle=ls, linewidth=lw, zorder=zorder)
    else:
        raise ValueError("axis must be 'x' or 'y'")


def add_group_dividers(ax: Axes,
                        split_indices: Sequence[float], *,
                        group_labels: Sequence[str] | None = None,
                        group_centers: Sequence[float] | None = None,
                        color: str = "gray", lw: float = 0.7,
                        alpha: float = 0.6,
                        label_position: str = "above",
                        label_y_frac: float | None = None,
                        label_color: str = "#444",
                        label_fontsize: int = 6) -> None:
    """Draw dashed vertical group dividers and optional group labels (idiom I3).

    label_position: 'above' (default, outside chart at y=1.02 axes coords) |
                    'inside_top' (at y=0.96 axes coords, safer with figure title) |
                    'inside_bottom' (at y=0.04 axes coords).
    label_y_frac:  override fraction (axes coords) explicitly. Wins over label_position.
    """
    for x_split in split_indices:
        ax.axvline(x_split, color=color, linestyle="--",
                   linewidth=lw, alpha=alpha, zorder=1)
    if not (group_labels and group_centers):
        return
    pos_map = {"above": 1.02, "inside_top": 0.96, "inside_bottom": 0.04}
    yfrac = label_y_frac if label_y_frac is not None else pos_map.get(label_position, 0.96)
    va = "bottom" if yfrac >= 1.0 else "top"
    for cx, name in zip(group_centers, group_labels):
        ax.text(cx, yfrac, name,
                ha="center", va=va,
                fontsize=label_fontsize, fontweight="bold",
                color=label_color, transform=ax.get_xaxis_transform())


def add_panel_label(ax: Axes, label: str, *,
                     x: float = -0.06, y: float = 1.08,
                     fontsize: int = 9) -> None:
    """Bold panel label (a/b/c) outside the data rectangle (idiom I13)."""
    ax.text(x, y, label, transform=ax.transAxes,
            fontweight="bold", fontsize=fontsize, va="bottom", ha="right",
            gid="scifig_panel_label", clip_on=False)


def apply_scatter_regression_floor(ax: Axes, *,
                                    grid_color: str = "#E0E0E0",
                                    grid_lw: float = 0.6,
                                    despine: bool = True,
                                    grid_axis: str = "both") -> None:
    """Apply the L0 floor for scatter-regression panels: light dashed grid + despine.
    Anchor cases: GAM scatter+residual (Nature), R�?scatter, distance-decay scatter.
    Always call this BEFORE drawing scatter so the grid sits at zorder=0.

    grid_axis: 'both' (default, scatter), 'x' (horizontal bars / dot-plot), 'y' (vertical bars).

    Polar-safe: matplotlib polar Axes only own a 'polar' spine, not 'top'/'right'.
    The despine step is skipped silently when called on polar axes so radar /
    polar variants can call this generically without KeyError.
    """
    if grid_axis == "both":
        ax.grid(True, linestyle="--", color=grid_color, linewidth=grid_lw,
                alpha=0.6, zorder=0)
    elif grid_axis == "x":
        ax.xaxis.grid(True, linestyle="--", color=grid_color, linewidth=grid_lw,
                       alpha=0.6, zorder=0)
        ax.yaxis.grid(False)
    elif grid_axis == "y":
        ax.yaxis.grid(True, linestyle="--", color=grid_color, linewidth=grid_lw,
                       alpha=0.6, zorder=0)
        ax.xaxis.grid(False)
    else:
        raise ValueError(f"grid_axis must be 'both'|'x'|'y', got {grid_axis!r}")
    ax.set_axisbelow(True)
    if despine:
        spines = getattr(ax, "spines", None)
        is_polar = getattr(ax, "name", "") == "polar" or (
            spines is not None and "polar" in spines and "top" not in spines
        )
        if not is_polar and spines is not None:
            if "top" in spines:
                ax.spines["top"].set_visible(False)
            if "right" in spines:
                ax.spines["right"].set_visible(False)


def resolve_split_palette(dataProfile: dict, *,
                           default_palette: str = "morandi_sci_4",
                           journalProfile: dict | None = None) -> dict[str, str]:
    """One-stop palette resolver that auto-detects split semantics.

    Returns a dict mapping role/category �?hex.

    Discipline (per 03-palette-bank.md):
      - dataProfile.has_train_test_split �?role_color('train'/'test')
      - dataProfile.has_actual_predicted �?role_color('actual'/'predicted')
      - dataProfile.has_shap_signed       �?role_color('shap_positive'/'shap_negative')
      - dataProfile.has_correlation_signed�?role_color('positive_correlation'/'negative_correlation')
      - Otherwise return categorical palette by `default_palette` name
        (categorical roles cat_0, cat_1, ...).
    """
    out: dict[str, str] = {}
    if dataProfile.get("has_train_test_split"):
        out["train"] = role_color("train")
        out["test"]  = role_color("test")
    if dataProfile.get("has_actual_predicted"):
        out["actual"]    = role_color("actual")
        out["predicted"] = role_color("predicted")
    if dataProfile.get("has_shap_signed"):
        out["shap_positive"] = role_color("shap_positive")
        out["shap_negative"] = role_color("shap_negative")
    if dataProfile.get("has_correlation_signed"):
        out["positive_correlation"] = role_color("positive_correlation")
        out["negative_correlation"] = role_color("negative_correlation")
    if not out:
        palette = resolve_palette(default_palette, journalProfile=journalProfile)
        for i, hex_ in enumerate(palette):
            out[f"cat_{i}"] = hex_
    return out


def density_sort(x: np.ndarray, y: np.ndarray, bw_method=None
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (x, y, density) sorted ascending by local 2D KDE density."""
    from scipy.stats import gaussian_kde
    xy = np.vstack([x, y])
    z = gaussian_kde(xy, bw_method=bw_method)(xy)
    idx = z.argsort()
    return x[idx], y[idx], z[idx]


def density_color_scatter(ax: Axes, x: np.ndarray, y: np.ndarray, *,
                           cmap: str = "GnBu_r", s: int = 18,
                           with_colorbar: bool = True,
                           colorbar_label: str = "Density",
                           rasterized: bool = True,
                           edgecolor: str = "white",
                           linewidth: float = 0.4,
                           zorder: int = 4) -> Axes:
    """Density-colored scatter with white-edged markers (idiom I6 + I7)."""
    x_s, y_s, z_s = density_sort(x, y)
    sc = ax.scatter(x_s, y_s, c=z_s, cmap=cmap, s=s,
                    edgecolor=edgecolor, linewidth=linewidth,
                    rasterized=rasterized, zorder=zorder)
    if with_colorbar:
        cbar = ax.figure.colorbar(sc, ax=ax, shrink=0.6, pad=0.04)
        cbar.set_label(colorbar_label, fontsize=6)
    return sc


def add_polygon_polar_grid(ax: Axes, angles: Sequence[float],
                            levels: Sequence[float] = (0.25, 0.5, 0.75, 1.0),
                            *,
                            color: str = "black",
                            grid_lw: float = 0.8,
                            spoke_lw: float = 0.6,
                            alpha_grid: float = 0.6,
                            alpha_spoke: float = 0.4) -> None:
    """Replace default circular polar grid with explicit polygon dashed grid (idiom I11).
    angles must already be closed (first angle appended to end)."""
    ax.spines["polar"].set_visible(False)
    ax.grid(False)
    for level in levels:
        ax.plot(angles, [level] * len(angles), color=color,
                linestyle="--", linewidth=grid_lw, alpha=alpha_grid, zorder=0)
    for ang in angles[:-1]:
        ax.plot([ang, ang], [0, max(levels)], color=color,
                linewidth=spoke_lw, alpha=alpha_spoke, zorder=0)


def add_polar_spoke_tick_labels(ax: Axes,
                                tick_values: Sequence[float],
                                *,
                                center: float = 0.0,
                                angle: float = 0.0,
                                fmt: str = "{:g}",
                                fontsize: float = 6.5,
                                fontweight: str = "bold",
                                color: str = "#222222",
                                bbox: dict | None = None,
                                zorder: int = 4) -> list:
    """Place radial tick labels on one spoke for hollow-center radar panels.

    Anchor case: `顶刊复刻 _ 中心挖空 + 立体高光 radar`.
    `tick_values` are physical tick values; `center` is subtracted so the labels
    align with the translated radii used by the hollow-center radar.
    """
    artists = []
    label_box = bbox if bbox is not None else {
        "boxstyle": "round,pad=0.05",
        "fc": "white",
        "ec": "none",
        "alpha": 0.72,
    }
    for value in tick_values:
        radius = float(value) - float(center)
        if radius <= 0:
            continue
        artists.append(
            ax.text(angle, radius, fmt.format(value),
                    ha="center", va="center", fontsize=fontsize,
                    fontweight=fontweight, color=color, bbox=label_box,
                    zorder=zorder)
        )
    return artists


def add_hollow_polar_center(ax: Axes, *,
                            size: float = 135,
                            facecolor: str = "white",
                            edgecolor: str = "black",
                            linewidth: float = 0.9,
                            zorder: int = 15):
    """Add the visual center cutout used by non-zero-origin radar panels."""
    return ax.scatter([0], [0], s=size, c=facecolor, edgecolors=edgecolor,
                      linewidths=linewidth, zorder=zorder)


def scatter_glass_markers(ax: Axes,
                          angles: Sequence[float],
                          radii: Sequence[float],
                          *,
                          color: str,
                          base_s: float = 72,
                          edgecolor: str = "white",
                          edge_lw: float = 1.4,
                          highlight_angle_shift: float = -0.035,
                          highlight_radius_shift: float | None = None,
                          soft_s: float = 24,
                          hard_s: float = 8,
                          zorder: int = 12) -> list:
    """Draw three-layer pseudo-3D glass markers for radar vertices.

    Layer order follows the article: colored base marker + soft white reflection
    + hard white specular dot. Returns artists for render-QA counting.
    """
    angles_arr = np.asarray(angles, dtype=float)
    radii_arr = np.asarray(radii, dtype=float)
    radius_shift = (
        float(highlight_radius_shift)
        if highlight_radius_shift is not None
        else max(float(np.nanmax(radii_arr)) * 0.018, 0.01)
    )
    base = ax.scatter(angles_arr, radii_arr, s=base_s, c=color,
                      edgecolors=edgecolor, linewidths=edge_lw, zorder=zorder)
    soft = ax.scatter(angles_arr + highlight_angle_shift,
                      radii_arr + radius_shift,
                      s=soft_s, c="white", alpha=0.55, linewidths=0,
                      zorder=zorder + 1)
    hard = ax.scatter(angles_arr + highlight_angle_shift * 1.3,
                      radii_arr + radius_shift * 1.55,
                      s=hard_s, c="white", alpha=0.95, linewidths=0,
                      zorder=zorder + 2)
    return [base, soft, hard]


def set_polar_title(ax: Axes, title: str, *,
                     fontsize: int = 8,
                     fontweight: str = "bold",
                     y: float = 1.18) -> None:
    """Place title above polar axis without colliding with the topmost angle label.
    Default y=1.18 keeps clearance for tick labels (max=...) AND axis names.

    Use this instead of `ax.set_title(title)` on polar axes �?matplotlib's default
    title position overlaps the angle-0 label on radar/polygon plots.
    """
    ax.text(0.5, y, title, transform=ax.transAxes,
            ha="center", va="bottom",
            fontsize=fontsize, fontweight=fontweight)


def draw_mirror_radial_bar_board(df,
                                 *,
                                 model_col: str,
                                 original_col: str,
                                 simplified_col: str,
                                 condition_col: str | None = None,
                                 condition_order: Sequence[str] | None = None,
                                 condition_labels: Sequence[str] | None = None,
                                 max_val: float | None = None,
                                 top_angles_deg: Sequence[float] = (20, 55, 90, 125, 160),
                                 bottom_angles_deg: Sequence[float] = (200, 235, 270, 305, 340),
                                 original_color: str = "#33CCFF",
                                 simplified_color: str = "#FFFF99",
                                 bar_width: float = 0.45,
                                 scale_rect: Sequence[float] = (0.05, 0.40, 0.02, 0.40),
                                 figsize: tuple[float, float] = (7.0, 7.0),
                                 col_map: dict | None = None) -> dict:
    """Draw the Case-023 mirror radial rose: two conditions on opposite hemispheres.

    Rows should contain model names, an optional condition column, and paired
    original/simplified feature model metrics.  The first condition is placed on
    the upper hemisphere; the second condition is mirrored on the lower half.
    """
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_mirror_radial_bar_board requires pandas") from exc

    missing = [col for col in (model_col, original_col, simplified_col) if col not in df]
    if missing:
        raise ValueError(f"mirror radial bar board missing required columns: {missing}")

    work_cols = [model_col, original_col, simplified_col]
    if condition_col and condition_col in df:
        work_cols.append(condition_col)
    work = df[work_cols].copy()
    work[model_col] = work[model_col].astype(str)
    work[original_col] = pd.to_numeric(work[original_col], errors="coerce")
    work[simplified_col] = pd.to_numeric(work[simplified_col], errors="coerce")
    work = work.dropna(subset=[model_col, original_col, simplified_col])
    if work.empty:
        raise ValueError("mirror radial bar board requires finite paired metric rows")

    models = list(dict.fromkeys(work[model_col].tolist()))
    if len(models) < 3:
        raise ValueError("mirror radial bar board requires at least 3 models")
    models = models[:min(len(models), len(top_angles_deg), len(bottom_angles_deg))]

    if condition_col and condition_col in work:
        available = list(dict.fromkeys(work[condition_col].astype(str).tolist()))
        if condition_order:
            conditions = [str(c) for c in condition_order if str(c) in available]
            conditions += [c for c in available if c not in conditions]
        else:
            conditions = available
        conditions = conditions[:2]
        if len(conditions) < 2:
            conditions = conditions + [conditions[0]]
    else:
        conditions = ["upper", "lower"]
        work[condition_col or "_condition"] = np.where(
            np.arange(len(work)) % 2 == 0, conditions[0], conditions[1]
        )
        condition_col = condition_col or "_condition"

    def _row_values(condition):
        sub = work[work[condition_col].astype(str) == str(condition)]
        if sub.empty:
            sub = work
        sub = sub.drop_duplicates(model_col, keep="first").set_index(model_col)
        orig, simp = [], []
        for model in models:
            if model in sub.index:
                orig.append(float(sub.loc[model, original_col]))
                simp.append(float(sub.loc[model, simplified_col]))
            else:
                orig.append(0.0)
                simp.append(0.0)
        return np.asarray(orig, dtype=float), np.asarray(simp, dtype=float)

    orig_top, simp_top = _row_values(conditions[0])
    orig_bot, simp_bot = _row_values(conditions[1])
    finite_max = float(np.nanmax(np.concatenate([orig_top, simp_top, orig_bot, simp_bot])))
    max_radius = float(max_val) if max_val is not None else max(finite_max * 1.10, 1.0)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="polar")
    ax.set_gid("scifig_mirror_radial_bar_board")
    ax.set_ylim(0, max_radius * 1.25)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    try:
        ax.spines["polar"].set_visible(False)
    except Exception:
        pass

    angles_top = np.deg2rad(np.asarray(top_angles_deg[:len(models)], dtype=float))
    angles_bottom = np.deg2rad(np.asarray(bottom_angles_deg[:len(models)], dtype=float))
    bars_orig_top = ax.bar(angles_top, orig_top, width=bar_width,
                           color=original_color, edgecolor="black",
                           linewidth=0.8, zorder=5)
    bars_simp_top = ax.bar(angles_top, simp_top, width=bar_width * 0.70,
                           color=simplified_color, edgecolor="black",
                           linewidth=0.6, zorder=10)
    bars_orig_bot = ax.bar(angles_bottom, orig_bot, width=bar_width,
                           color=original_color, edgecolor="black",
                           linewidth=0.8, zorder=5)
    bars_simp_bot = ax.bar(angles_bottom, simp_bot, width=bar_width * 0.70,
                           color=simplified_color, edgecolor="black",
                           linewidth=0.6, zorder=10)
    for patch in list(bars_orig_top) + list(bars_orig_bot):
        patch.set_gid("scifig_mirror_radial_original_bar")
    for patch in list(bars_simp_top) + list(bars_simp_bot):
        patch.set_gid("scifig_mirror_radial_simplified_bar")

    label_radius = max_radius * 1.13
    for angle, label in zip(np.concatenate([angles_top, angles_bottom]), models * 2):
        rotation = float(np.rad2deg(angle))
        if 90 < rotation < 270:
            rotation += 180
        display = str(col_map.get(label, label)) if isinstance(col_map, dict) else str(label)
        ax.text(angle, label_radius, display, rotation=rotation,
                ha="center", va="center", fontsize=9, fontweight="bold", zorder=12)

    labels = list(condition_labels) if condition_labels else [str(c) for c in conditions]
    if len(labels) < 2:
        labels = labels + labels[:1]
    condition_text = [
        ax.text(np.deg2rad(90), max_radius * 1.05, labels[0],
                ha="center", va="center", fontsize=10, fontweight="bold", zorder=12),
        ax.text(np.deg2rad(270), max_radius * 1.05, labels[1],
                ha="center", va="center", fontsize=10, fontweight="bold",
                rotation=180, zorder=12),
    ]

    ax_scale = fig.add_axes(list(scale_rect))
    ax_scale.set_gid("scifig_mirror_radial_external_scale")
    ax_scale.axis("off")
    ax_scale.set_ylim(0, max_radius)
    ax_scale.plot([0, 0], [0, max_radius], "k-", linewidth=1.2, zorder=2)
    tick_step = max_radius / 7.0
    tick_values = np.arange(tick_step, max_radius + tick_step * 0.5, tick_step)
    scale_labels = []
    for value in tick_values:
        ax_scale.plot([-0.08, 0.08], [value, value], "k-", linewidth=0.9, zorder=2)
        scale_labels.append(
            ax_scale.text(-0.18, value, f"{value:.1f}",
                          va="center", ha="right", fontsize=7)
        )
    ax_scale.set_xlim(-0.35, 0.20)

    legend_handles = [
        mpl.patches.Patch(facecolor=original_color, edgecolor="black", label="Original features"),
        mpl.patches.Patch(facecolor=simplified_color, edgecolor="black", label="Simplified features"),
    ]
    ax.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, -0.08),
              ncol=2, frameon=False, fontsize=8)

    return {
        "fig": fig,
        "ax": ax,
        "scale_ax": ax_scale,
        "models": models,
        "conditions": conditions,
        "bar_groups": [bars_orig_top, bars_simp_top, bars_orig_bot, bars_simp_bot],
        "original_bar_count": len(bars_orig_top) + len(bars_orig_bot),
        "simplified_bar_count": len(bars_simp_top) + len(bars_simp_bot),
        "radial_bar_layer_count": 4,
        "condition_label_count": len(condition_text),
        "external_scale_label_count": len(scale_labels),
        "max_radius": max_radius,
        "palette": [original_color, simplified_color],
    }


def draw_gradient_box(ax: Axes, x: float, q1: float, width: float,
                       height: float, color: str, *,
                       alpha_lo: float = 0.15, alpha_hi: float = 0.95,
                       zorder: int = 2) -> None:
    """Vertical-gradient fill inside a box rectangle via imshow (idiom I12)."""
    rgba = mc.to_rgba(color)
    alphas = np.linspace(alpha_lo, alpha_hi, 256)
    cmap = mc.LinearSegmentedColormap.from_list(
        "grad", [(rgba[0], rgba[1], rgba[2], a) for a in alphas])
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    ax.imshow(grad, extent=(x, x + width, q1, q1 + height),
              aspect="auto", origin="lower", cmap=cmap, zorder=zorder)
    rect = plt.Rectangle((x, q1), width, height, fill=False,
                         edgecolor=color, linewidth=1.2, zorder=zorder + 1)
    ax.add_patch(rect)


# ============================================================================
# 4. GRID RECIPES  (04-grid-recipes.md)
# ============================================================================

def build_grid(recipe: str, *, fig: Figure | None = None,
                figsize: tuple[float, float] | None = None,
                n: int = 5,
                width_ratios: Sequence[float] | None = None,
                height_ratios: Sequence[float] | None = None,
                wspace: float | None = None,
                hspace: float | None = None,
                polar: bool = False,
                ) -> tuple[Figure, list[Axes]]:
    """Build a multi-panel figure from a recipe key. Returns (fig, axes-flat).

    Implemented recipes: R0 R1 R2 R3 R4 R4b R5 R6 R7 R8 R9 R10 R11.
    """
    if recipe == "R0_single_panel":
        fig = fig or plt.figure(figsize=figsize or (6.5, 6.0))
        ax = fig.add_subplot(111, polar=polar)
        return fig, [ax]

    if recipe == "R1_two_panel_horizontal":
        fig = fig or plt.figure(figsize=figsize or (12, 5))
        wr = list(width_ratios) if width_ratios else [1, 1]
        gs = GridSpec(1, 2, width_ratios=wr,
                      wspace=wspace if wspace is not None else 0.25)
        ax_l = fig.add_subplot(gs[0, 0]); ax_r = fig.add_subplot(gs[0, 1])
        return fig, [ax_l, ax_r]

    if recipe == "R2_two_by_two_storyboard":
        fig = fig or plt.figure(figsize=figsize or (11, 9))
        gs = GridSpec(2, 2,
                      hspace=hspace if hspace is not None else 0.30,
                      wspace=wspace if wspace is not None else 0.30)
        axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(2)]
        return fig, axes

    if recipe == "R3_two_by_three_grid":
        fig = fig or plt.figure(figsize=figsize or (15, 9))
        gs = GridSpec(2, 3,
                      hspace=hspace if hspace is not None else 0.35,
                      wspace=wspace if wspace is not None else 0.25)
        axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]
        return fig, axes

    if recipe == "R4_three_panel_horizontal":
        fig = fig or plt.figure(figsize=figsize or (15, 5))
        axs = fig.subplots(1, 3, sharey=True)
        return fig, list(axs)

    if recipe in ("R4b_rf_ml_diagnostic_triptych", "ml_model_performance_triptych", "architecture_metric_storyboard", "rf_classifier_report_board", "classifier_validation_board"):
        fig = fig or plt.figure(figsize=figsize or (14, 10.6))
        gs = GridSpec(
            2,
            2,
            height_ratios=list(height_ratios) if height_ratios else [0.92, 1.00],
            hspace=hspace if hspace is not None else 0.23,
            wspace=wspace if wspace is not None else 0.22,
        )
        ax_benchmark = fig.add_subplot(gs[0, :])
        ax_parity = fig.add_subplot(gs[1, 0])
        ax_residual = fig.add_subplot(gs[1, 1])
        return fig, [ax_benchmark, ax_parity, ax_residual]

    if recipe == "R5_n_by_n_pairwise":
        fig = fig or plt.figure(figsize=figsize or (2.4 * n, 2.4 * n))
        gs = GridSpec(n, n,
                      hspace=hspace if hspace is not None else 0.05,
                      wspace=wspace if wspace is not None else 0.05)
        axes = [fig.add_subplot(gs[i, j]) for i in range(n) for j in range(n)]
        return fig, axes

    if recipe == "R6_four_panel_band":
        fig = fig or plt.figure(figsize=figsize or (16, 4))
        axs = fig.subplots(1, 4, sharey=True)
        return fig, list(axs)

    if recipe == "R8_main_with_marginal":
        fig = fig or plt.figure(figsize=figsize or (8, 8))
        gs = GridSpec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4],
                      hspace=hspace if hspace is not None else 0.05,
                      wspace=wspace if wspace is not None else 0.05)
        ax_top    = fig.add_subplot(gs[0, 0])
        ax_main   = fig.add_subplot(gs[1, 0])
        ax_right  = fig.add_subplot(gs[1, 1])
        ax_corner = fig.add_subplot(gs[0, 1]); ax_corner.axis("off")
        return fig, [ax_main, ax_top, ax_right, ax_corner]

    if recipe == "R9_inset_overlay":
        fig = fig or plt.figure(figsize=figsize or (8, 5.5))
        ax = fig.add_subplot(111)
        rect = [0.55, 0.35, 0.40, 0.35]
        ax_ins = ax.inset_axes(rect, zorder=10)
        # Fully opaque so main artists never bleed through (corpus discipline)
        ax_ins.set_facecolor("white")
        ax_ins.patch.set_alpha(1.0)
        # Cover anything behind via a backing white rectangle on the parent axis
        # (inset_axes alone doesn't always block lower-zorder artists)
        from matplotlib.patches import Rectangle
        backing = Rectangle((rect[0], rect[1]), rect[2], rect[3],
                            transform=ax.transAxes,
                            facecolor="white", edgecolor="none", zorder=9)
        ax.add_patch(backing)
        for s in ax_ins.spines.values():
            s.set_linewidth(0.8); s.set_color("#222")
        return fig, [ax, ax_ins]

    if recipe == "R7_dense_2x6_lineup":
        fig = fig or plt.figure(figsize=figsize or (20, 7))
        gs = GridSpec(2, 6,
                      hspace=hspace if hspace is not None else 0.40,
                      wspace=wspace if wspace is not None else 0.30)
        axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(6)]
        return fig, axes

    if recipe == "R10_asymmetric_top_wide":
        # 1 wide top + 2 narrow below (SHAP composite, global_local arc default)
        fig = fig or plt.figure(figsize=figsize or (11, 9))
        gs = GridSpec(2, 2,
                      height_ratios=list(height_ratios) if height_ratios else [1, 1],
                      hspace=hspace if hspace is not None else 0.35,
                      wspace=wspace if wspace is not None else 0.25)
        ax_top = fig.add_subplot(gs[0, :])
        ax_bl  = fig.add_subplot(gs[1, 0])
        ax_br  = fig.add_subplot(gs[1, 1])
        return fig, [ax_top, ax_bl, ax_br]

    if recipe == "R11_triple_y_axis":
        fig = fig or plt.figure(figsize=figsize or (10, 5.5))
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        ax3 = ax1.twinx()
        ax3.spines["right"].set_position(("outward", 60))
        return fig, [ax1, ax2, ax3]

    raise KeyError(f"unknown recipe {recipe!r}; see 04-grid-recipes.md")


# ============================================================================
# 5. NARRATIVE ARCS  (06-narrative-arcs.md)
# ============================================================================

ARCS = ("hero", "single_focus", "multipanel_grid", "global_local",
        "n×n_pairwise", "marginal_joint", "train_test_diagnostic",
        "composite_two_lane", "mirror_compare", "inset_overlay")


def select_narrative_arc(dataProfile: dict, chartPlan: dict | None = None) -> str:
    """Heuristic arc selector matching `modules/06-narrative-arcs.md` decision matrix."""
    cp = chartPlan or {}
    if dataProfile.get("has_train_test_split"):
        return "train_test_diagnostic"
    if cp.get("requested_inset"):
        return "inset_overlay"
    if cp.get("has_marginal_distribution"):
        return "marginal_joint"
    if cp.get("has_correlation_matrix"):
        return "n×n_pairwise"
    if cp.get("has_shap_global") and cp.get("has_shap_local"):
        return "global_local"
    if cp.get("bipolar_or_mirror"):
        return "mirror_compare"
    panels = cp.get("panels") or []
    if len(panels) >= 4 and len({p.get("family") for p in panels}) == 1:
        return "multipanel_grid"
    if len(panels) == 2 and len({p.get("family") for p in panels}) > 1:
        return "composite_two_lane"
    if cp.get("is_headline"):
        return "hero"
    return "single_focus"


_ARC_REQUIRED_MOTIFS = {
    # 'hero' is single-panel headline. Sub-types differentiate polar vs cartesian.
    "hero":                  ["colored_marker_edge"],                  # universal hero requirement
    "hero.polar":            ["polygon_polar_grid", "colored_marker_edge"],
    "hero.cartesian":        ["colored_marker_edge"],
    "hero.dual_axis":        ["twin_axes_color_spines", "colored_marker_edge"],
    "single_focus":          ["alpha_layered_scatter"],
    "multipanel_grid":       ["panel_label", "colored_marker_edge", "dotted_zero_axhline"],
    "global_local":          ["shared_feature_ordering", "colored_marker_edge", "dotted_zero_axhline"],
    "n×n_pairwise":          ["upper_triangle_split", "outer_only_labels"],
    "marginal_joint":        ["density_color_scatter", "perfect_fit_diagonal", "marginal_axes_off"],
    "train_test_diagnostic":              ["metric_text_box"],
    "train_test_diagnostic.scatter":      ["metric_text_box", "perfect_fit_diagonal", "colored_marker_edge"],
    "train_test_diagnostic.time_series":  ["metric_text_box", "error_band_fill_between", "group_divider_axvline"],
    "composite_two_lane":    ["shared_feature_ordering", "dotted_zero_axhline"],
    "mirror_compare":        ["dotted_zero_axhline", "bipolar_palette"],
    "inset_overlay":         ["axes_inset_overlay", "colored_marker_edge"],
}


def arc_required_motifs(arc: str, *, chart_family: str | None = None) -> list[str]:
    """Return mandatory motif keys for the chosen narrative arc.

    For arcs with sub-types, pass `chart_family` to disambiguate:
      - hero + 'radar' / 'mirror_radial' �?polar sub-type
      - hero + 'dual_axis'                �?dual_axis sub-type
      - hero + 'scatter_regression' / 'forest' / 'box' / 'violin' �?cartesian sub-type
      - train_test_diagnostic + 'scatter_regression' �?scatter sub-type
      - train_test_diagnostic + 'time_series_pi'      �?time-series sub-type
    Default (no chart_family): return the arc's universal motifs.
    """
    if arc == "hero" and chart_family:
        if chart_family in {"radar", "mirror_radial", "polar"}:
            return list(_ARC_REQUIRED_MOTIFS["hero.polar"])
        if chart_family in {"dual_axis"}:
            return list(_ARC_REQUIRED_MOTIFS["hero.dual_axis"])
        return list(_ARC_REQUIRED_MOTIFS["hero.cartesian"])
    if arc == "train_test_diagnostic" and chart_family:
        if chart_family in {"scatter_regression", "predicted_actual"}:
            return list(_ARC_REQUIRED_MOTIFS["train_test_diagnostic.scatter"])
        if chart_family in {"time_series_pi", "time_series"}:
            return list(_ARC_REQUIRED_MOTIFS["train_test_diagnostic.time_series"])
    if arc not in _ARC_REQUIRED_MOTIFS:
        raise KeyError(f"unknown arc {arc!r}; choices: {sorted(_ARC_REQUIRED_MOTIFS)}")
    return list(_ARC_REQUIRED_MOTIFS[arc])


_ARC_DEFAULT_GRID = {
    "hero":                  "R0_single_panel",
    "single_focus":          "R0_single_panel",
    "multipanel_grid":       "R3_two_by_three_grid",
    "global_local":          "R10_asymmetric_top_wide",
    "n×n_pairwise":          "R5_n_by_n_pairwise",
    "marginal_joint":        "R8_main_with_marginal",
    "train_test_diagnostic": "R0_single_panel",
    "composite_two_lane":    "R1_two_panel_horizontal",
    "mirror_compare":        "R0_single_panel",
    "inset_overlay":         "R9_inset_overlay",
}


def arc_default_grid(arc: str, panel_count: int = 1) -> str:
    """Return the default grid recipe key for the arc.

    Overrides:
      multipanel_grid + panel_count <= 4 �?R2 (2x2)
      multipanel_grid + panel_count >= 9 �?R5 (3x3 / n×n)
    """
    if arc == "multipanel_grid":
        if panel_count <= 4:
            return "R2_two_by_two_storyboard"
        if panel_count >= 9:
            return "R5_n_by_n_pairwise"
    return _ARC_DEFAULT_GRID[arc]


# ============================================================================
# 6. ZORDER RECIPES  (02-zorder-recipes.md)
# ============================================================================

_ZORDER_TIER = {
    "grid":        0,
    "background":  1,
    "fill":        2,
    "primary":     4,
    "reference":   6,
    "error":       8,
    "highlight":  10,
}


def apply_zorder_recipe(family: str, ax: Axes, layers: dict[str, list]) -> None:
    """Re-tag artist `zorder` attributes by semantic role.

    family: 'scatter_regression' | 'forest' | 'dual_axis' | 'radar'
            | 'shap_composite' | 'marginal_joint' (plus stubs for
            'time_series_pi' | 'lollipop' | 'gradient_box' | 'inset_distribution').
    layers: dict mapping role-key �?list of artist objects (or single artist).
            Roles: 'grid', 'background', 'fill', 'primary', 'reference',
                    'error', 'highlight'.
    """
    if family in {"scatter_regression", "forest", "dual_axis", "radar",
                  "shap_composite", "marginal_joint", "time_series_pi",
                  "lollipop", "gradient_box", "inset_distribution"}:
        for role, artists in layers.items():
            if role not in _ZORDER_TIER:
                raise KeyError(f"role {role!r} unknown; "
                               f"choices: {sorted(_ZORDER_TIER)}")
            zord = _ZORDER_TIER[role]
            seq = artists if isinstance(artists, (list, tuple)) else [artists]
            for art in seq:
                try:
                    art.set_zorder(zord)
                except AttributeError:
                    # Some collection-like objects may need set_zorder_(?)
                    pass
    else:
        raise KeyError(f"family {family!r} has no zorder recipe; "
                       f"see 02-zorder-recipes.md")


# ============================================================================
# 7. CONVENIENCE: ONE-CALL CHART BOOTSTRAP
# ============================================================================

def bootstrap_chart(arc: str, *,
                     panel_count: int = 1,
                     variant: str = "default",
                     palette: str = "morandi_sci_4",
                     journalProfile: dict | None = None,
                     figsize: tuple[float, float] | None = None,
                     ) -> tuple[Figure, list[Axes], list[str]]:
    """Bootstrap a figure from a narrative arc �?applies kernel + grid + palette.

    Returns (fig, axes_flat, palette_hex_list).

    Equivalent to:
        apply_journal_kernel(variant, journalProfile)
        recipe = arc_default_grid(arc, panel_count)
        fig, axes = build_grid(recipe, figsize=figsize)
        palette = resolve_palette(palette, journalProfile=journalProfile)
    """
    apply_journal_kernel(variant, journalProfile)
    recipe = arc_default_grid(arc, panel_count)
    fig, axes = build_grid(recipe, figsize=figsize)
    pal = resolve_palette(palette, journalProfile=journalProfile)
    return fig, axes, pal


# ============================================================================
# 8. FOREST PLOT (cycle 2 addition)
# ============================================================================

def add_forest_panel(ax, hrs, lower, upper, labels, *,
                      color="#3C5488",
                      reference_line=1.0,
                      log_scale=True,
                      show_yticklabels=True,
                      annotation_format="{hr:.2f} ({lo:.2f}-{hi:.2f})",
                      title=None):
    """One-call forest panel: dashed reference line + HR markers with asymmetric
    CI whiskers + per-row HR(CI) annotation column at right edge.

    Anchor cases: HR multi-cohort forest (Nature Comms), risk-ratio caterpillar.
    Annotation is positioned via axes-fraction (x=0.99) so it never collides
    with the marker positions on log scale.
    """
    n = len(hrs)
    y_pos = np.arange(n)
    hrs = np.asarray(hrs, dtype=float)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)

    ax.xaxis.grid(True, linestyle=':', color='#E0E0E0',
                  linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.axvline(reference_line, color='#888888', linestyle='--',
               linewidth=1.0, zorder=1)

    xerr = [hrs - lower, upper - hrs]
    ax.errorbar(hrs, y_pos, xerr=xerr, fmt='o',
                color=color, ecolor=color, elinewidth=2, capsize=4,
                markersize=9, markeredgecolor='white', markeredgewidth=0.6,
                zorder=10)

    for i, (hr, lo, hi) in enumerate(zip(hrs, lower, upper)):
        ax.text(0.99, y_pos[i],
                annotation_format.format(hr=hr, lo=lo, hi=hi),
                transform=ax.get_yaxis_transform(),
                ha='right', va='center',
                fontsize=6, color='#222',
                family='monospace', zorder=15,
                bbox=dict(boxstyle='round,pad=0.15',
                          fc='white', ec='none', alpha=0.85))

    if log_scale:
        ax.set_xscale('log')
        from matplotlib.ticker import LogLocator, ScalarFormatter
        ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=(1.0,), numticks=5))
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        ax.xaxis.set_major_formatter(formatter)

    ax.set_yticks(y_pos)
    if show_yticklabels:
        ax.set_yticklabels(labels, fontsize=6)
    else:
        ax.set_yticklabels([])
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if title:
        ax.set_title(title, color=color, fontsize=8, fontweight='bold')


# ============================================================================
# 9. HEATMAP PAIRWISE PANEL (cycle 21 addition)
# ============================================================================

def add_heatmap_pairwise_panel(fig, features_df, *,
                                 gs=None,
                                 cmap_name="RdBu_r",
                                 primary_color="#3C5488",
                                 spacing=0.05,
                                 show_colorbar=True,
                                 colorbar_label="Pearson r",
                                 colorbar_rect=(0.92, 0.30, 0.012, 0.40),
                                 max_features=8) -> dict:
    """One-call pairwise correlation matrix panel �?encodes the corpus-anchored
    `heatmap_pairwise` discipline (11/94 cases) from `knowledge/techniques/heatmap-pairwise.md`.

    Layout discipline (Nature 5x5 Pearson matrix anchor):
      - n*n GridSpec with hspace=wspace=0.05 (tight)
      - Diagonal: histogram + KDE in primary color
      - Upper triangle: correlation r-value (with significance stars when p<0.05)
        on TwoSlopeNorm-tinted background, spines hidden
      - Lower triangle: hollow-marker scatter + linear fit (corpus pattern)
      - Outer-only labels (left column + bottom row)
      - Diverging cmap RdBu_r centered at 0
      - Text color flips to white when |r| > 0.5 (contrast rule)

    Args:
      fig: matplotlib Figure to populate.
      features_df: pandas DataFrame whose columns are the features to compare.
                   Each column must be numeric and have >=2 valid observations.
      gs: optional pre-built GridSpec (n*n). If None, one is built from features_df.
      cmap_name: diverging colormap name (default "RdBu_r").
      primary_color: KDE + scatter edge color (default "#3C5488", NPG navy).
      spacing: hspace/wspace for the GridSpec (default 0.05, corpus tight value).
      show_colorbar: whether to add the shared diverging colorbar.
      colorbar_label: label for the colorbar.
      colorbar_rect: [left, bottom, width, height] in fig fraction for colorbar.
      max_features: hard cap to avoid 20x20 matrices (default 8). Raises if exceeded.

    Returns:
      dict with keys:
        axes:        list[Axes] in row-major order (length n*n)
        norm:        TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
        cmap:        the colormap object
        gridspec:    the GridSpec used
        n_features:  number of features (n)
        correlation_matrix: dict mapping (i,j) -> {'r': float, 'p': float}

    Anchor cases:
      - Nature Pearson 5x5 matrix
      - Spearman ML model performance
      - Gaussian-kernel 3x3 multipanel scatter
    """
    from matplotlib.gridspec import GridSpec
    from matplotlib.colors import TwoSlopeNorm
    import matplotlib.cm as cm
    try:
        from scipy.stats import gaussian_kde, pearsonr
        _has_scipy = True
    except ImportError:
        _has_scipy = False

    features = list(features_df.columns)
    n = len(features)
    if n < 2:
        raise ValueError(f"heatmap_pairwise requires >=2 features, got {n}")
    if n > max_features:
        raise ValueError(
            f"heatmap_pairwise capped at {max_features} features to keep panels readable; "
            f"got {n}. Pre-select top variables before calling."
        )

    if gs is None:
        gs = GridSpec(n, n, figure=fig, hspace=spacing, wspace=spacing)

    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    # Use modern matplotlib.colormaps API when available (>=3.7); fall back to
    # cm.get_cmap for older matplotlib versions
    try:
        cmap = mpl.colormaps[cmap_name]
    except (AttributeError, KeyError):
        cmap = cm.get_cmap(cmap_name)
    axes = []
    correlation_matrix = {}

    for i in range(n):
        for j in range(n):
            ax = fig.add_subplot(gs[i, j])
            axes.append(ax)
            x_raw = features_df[features[j]].dropna().values
            y_raw = features_df[features[i]].dropna().values
            n_pts = min(len(x_raw), len(y_raw))
            x = np.asarray(x_raw[:n_pts], dtype=float)
            y = np.asarray(y_raw[:n_pts], dtype=float)

            if i == j:
                # Diagonal: histogram + KDE
                ax.hist(x, bins=15, density=True, color="white",
                        edgecolor="black", linewidth=0.8, zorder=1)
                if _has_scipy and n_pts > 1 and float(np.std(x)) > 0:
                    try:
                        kde = gaussian_kde(x)
                        xx = np.linspace(float(x.min()), float(x.max()), 200)
                        ax.plot(xx, kde(xx), color=primary_color, linewidth=1.8, zorder=3)
                    except Exception:
                        pass
                ax.set_yticks([])
            elif i < j:
                # Upper triangle: correlation r-value on tinted background
                # Guard against zero-variance columns (constant features) which
                # would produce NaN + RuntimeWarning from pearsonr / corrcoef.
                std_x = float(np.std(x)) if n_pts >= 2 else 0.0
                std_y = float(np.std(y)) if n_pts >= 2 else 0.0
                if _has_scipy and n_pts >= 2 and std_x > 0 and std_y > 0:
                    r, p = pearsonr(x, y)
                    r = float(r); p = float(p)
                elif n_pts >= 2 and std_x > 0 and std_y > 0:
                    # Manual fallback when scipy unavailable
                    with np.errstate(all="ignore"):
                        r = float(np.corrcoef(x, y)[0, 1])
                    if not np.isfinite(r):
                        r = 0.0
                    p = 1.0
                else:
                    # Degenerate: at least one column is constant, correlation is undefined
                    r, p = 0.0, 1.0
                correlation_matrix[(i, j)] = {"r": r, "p": p}
                ax.set_facecolor(cmap(norm(r)))
                stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
                ax.text(0.5, 0.5, f"{r:.2f}{stars}",
                        ha="center", va="center", transform=ax.transAxes,
                        fontsize=8, fontweight="bold",
                        color="white" if abs(r) > 0.5 else "black",
                        zorder=10)
                for s in ax.spines.values():
                    s.set_visible(False)
                ax.set_xticks([]); ax.set_yticks([])
            else:
                # Lower triangle: hollow scatter + linear fit
                ax.scatter(x, y, s=12, facecolor="none",
                           edgecolor=primary_color, alpha=0.5,
                           linewidth=0.6, zorder=2)
                if n_pts >= 2 and float(np.std(x)) > 0:
                    try:
                        slope, intercept = np.polyfit(x, y, 1)
                        xx = np.linspace(float(x.min()), float(x.max()), 100)
                        ax.plot(xx, slope * xx + intercept, color="black",
                                linewidth=1.0, zorder=4)
                    except Exception:
                        pass

            # Outer-only labels (corpus discipline)
            if j == 0:
                ax.set_ylabel(features[i], fontsize=8)
            else:
                ax.set_yticklabels([])
            if i == n - 1:
                ax.set_xlabel(features[j], fontsize=8)
            else:
                ax.set_xticklabels([])

    if show_colorbar:
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cax = fig.add_axes(list(colorbar_rect))
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label(colorbar_label, fontsize=8)

    return {
        "axes": axes,
        "norm": norm,
        "cmap": cmap,
        "gridspec": gs,
        "n_features": n,
        "correlation_matrix": correlation_matrix,
    }


def draw_bubble_correlation_matrix(ax: Axes,
                                   matrix_or_df,
                                   *,
                                   row_col: str | None = None,
                                   col_col: str | None = None,
                                   value_col: str | None = None,
                                   labels: Sequence[str] | None = None,
                                   palette: Sequence[str] = ("#8ECFC9", "#FFFFFF", "#FA7F6F"),
                                   size_scale: float = 2000,
                                   annotate: bool = True,
                                   colorbar_label: str = "Pearson r",
                                   col_map: dict | None = None) -> dict:
    """Draw the Case-011 red-blue bubble correlation matrix.

    Accepts either a square correlation matrix (DataFrame/array) or a long
    ``row_col`` / ``col_col`` / ``value_col`` table. Color encodes signed r via
    TwoSlopeNorm centered at 0; area encodes ``abs(r)``.
    """
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_bubble_correlation_matrix requires pandas") from exc
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    try:
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        _has_divider = True
    except Exception:
        _has_divider = False

    if row_col and col_col and value_col:
        work = pd.DataFrame({
            "row": matrix_or_df[row_col].astype(str),
            "col": matrix_or_df[col_col].astype(str),
            "value": pd.to_numeric(matrix_or_df[value_col], errors="coerce"),
        }).dropna(subset=["row", "col", "value"])
        if labels is None:
            labels = list(dict.fromkeys(list(work["row"]) + list(work["col"])))
        matrix = work.pivot_table(index="row", columns="col", values="value", aggfunc="mean")
        matrix = matrix.reindex(index=list(labels), columns=list(labels))
    else:
        if hasattr(matrix_or_df, "values") and hasattr(matrix_or_df, "index"):
            matrix = matrix_or_df.copy()
            if labels is None:
                labels = [str(x) for x in matrix.index]
        else:
            arr = np.asarray(matrix_or_df, dtype=float)
            if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
                raise ValueError("bubble correlation matrix requires a square matrix")
            labels = list(labels or [f"V{i + 1}" for i in range(arr.shape[0])])
            matrix = pd.DataFrame(arr, index=labels, columns=labels)
    labels = [str(label) for label in labels]
    matrix = matrix.reindex(index=labels, columns=labels)
    values = matrix.to_numpy(dtype=float)
    n = len(labels)
    if n < 2:
        raise ValueError("bubble correlation matrix requires at least two variables")

    xs, ys = np.meshgrid(np.arange(n), np.arange(n))
    flat = values.ravel()
    cmap = LinearSegmentedColormap.from_list("TealRed", list(palette))
    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    scatter = ax.scatter(
        xs.ravel(),
        ys.ravel(),
        s=np.nan_to_num(np.abs(flat), nan=0.0) * size_scale,
        c=flat,
        cmap=cmap,
        norm=norm,
        alpha=0.96,
        edgecolors="#333333",
        linewidth=0.35,
        zorder=2,
    )
    text_count = 0
    if annotate:
        for i in range(n):
            for j in range(n):
                val = values[i, j]
                if not np.isfinite(val):
                    continue
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=6.0 if n <= 13 else 5.0, color="black", zorder=3)
                text_count += 1

    display_labels = [str(col_map.get(label, label)) if isinstance(col_map, dict) else label
                      for label in labels]
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(display_labels, rotation=45, ha="right", fontsize=6.5)
    ax.set_yticklabels(display_labels, fontsize=6.5)
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_xticks(np.arange(n + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(n + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="#f0f0f0", linewidth=1.1, zorder=0)
    ax.tick_params(which="minor", length=0)
    ax.tick_params(which="major", length=3, direction="in")
    ax.set_gid("scifig_bubble_correlation_matrix")
    if _has_divider:
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3.5%", pad=0.12)
        cbar = ax.figure.colorbar(scatter, cax=cax)
    else:
        cbar = ax.figure.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(colorbar_label, fontsize=7.5)
    cbar.ax.tick_params(labelsize=6.5, length=3, direction="in")
    return {
        "ax": ax,
        "scatter": scatter,
        "colorbar": cbar,
        "norm": norm,
        "cmap": cmap,
        "n": n,
        "text_count": text_count,
        "matrix": matrix,
    }


def draw_textbook_dual_axis_bar_line(ax: Axes,
                                     df,
                                     *,
                                     x_col: str,
                                     bar_col: str,
                                     line_col: str,
                                     bar_err_col: str | None = None,
                                     line_err_col: str | None = None,
                                     group_col: str | None = None,
                                     group_splits: Sequence[float] | None = None,
                                     left_ylim: Sequence[float] | None = None,
                                     right_ylim: Sequence[float] | None = None,
                                     palette: Sequence[str] = ("#CFE2F3", "#9BC2E6", "#F48E66"),
                                     spline_points: int = 300,
                                     xtick_rotation: float = 90,
                                     line_smoothing: bool = True,
                                     show_mean_line: bool = False,
                                     mean_line_label: str = "Mean",
                                     bar_width: float = 0.6,
                                     line_width: float = 3.0,
                                     marker_size: float = 8.0,
                                     bar_edge_color: str | None = None,
                                     col_map: dict | None = None) -> dict:
    """Draw a template-mined dual-Y bar+line chart.

    Defaults preserve the Case-012 Materials Today bar+spline behavior.  The
    optional unsmoothed mean-line mode covers Case-026 Nature Comms
    count/proportion compositions.
    """
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_textbook_dual_axis_bar_line requires pandas") from exc
    try:
        from scipy.interpolate import make_interp_spline
    except Exception:  # pragma: no cover
        make_interp_spline = None

    missing = [col for col in (x_col, bar_col, line_col) if col not in df]
    if missing:
        raise ValueError(f"dual-axis bar-line missing required columns: {missing}")

    work = pd.DataFrame({
        "x_label": df[x_col].astype(str),
        "bar": pd.to_numeric(df[bar_col], errors="coerce"),
        "line": pd.to_numeric(df[line_col], errors="coerce"),
    })
    if bar_err_col and bar_err_col in df:
        work["bar_err"] = pd.to_numeric(df[bar_err_col], errors="coerce")
    if line_err_col and line_err_col in df:
        work["line_err"] = pd.to_numeric(df[line_err_col], errors="coerce")
    if group_col and group_col in df:
        work["group"] = df[group_col].astype(str)
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=["x_label", "bar", "line"])
    if len(work) < 2:
        raise ValueError("dual-axis bar-line requires at least two finite rows")

    bar_face, bar_edge, line_color = list(palette)[:3]
    if bar_edge_color is not None:
        bar_edge = str(bar_edge_color)
    x = np.arange(len(work), dtype=float)
    ax2 = ax.twinx()
    ax.set_gid("scifig_textbook_dual_axis_left")
    ax2.set_gid("scifig_textbook_dual_axis_right")

    bars = ax.bar(
        x,
        work["bar"].to_numpy(dtype=float),
        width=float(bar_width),
        yerr=work["bar_err"].to_numpy(dtype=float) if "bar_err" in work else None,
        capsize=5 if "bar_err" in work else 0,
        color=bar_face,
        edgecolor=bar_edge,
        linewidth=1.5,
        error_kw={"linewidth": 1.0, "ecolor": "#666666"},
        zorder=2,
        label=str(col_map.get(bar_col, bar_col)) if isinstance(col_map, dict) else str(bar_col),
    )

    y_line = work["line"].to_numpy(dtype=float)
    if line_smoothing and len(x) >= 4 and make_interp_spline is not None:
        x_smooth = np.linspace(x.min(), x.max(), int(max(spline_points, len(x))))
        try:
            spline = make_interp_spline(x, y_line, k=min(3, len(x) - 1))
            y_smooth = spline(x_smooth)
        except Exception:
            y_smooth = np.interp(x_smooth, x, y_line)
    elif line_smoothing:
        x_smooth = np.linspace(x.min(), x.max(), int(max(spline_points, len(x))))
        y_smooth = np.interp(x_smooth, x, y_line)
    else:
        x_smooth = x
        y_smooth = y_line
    line, = ax2.plot(
        x_smooth,
        y_smooth,
        color=line_color,
        linewidth=float(line_width),
        zorder=3,
        label=str(col_map.get(line_col, line_col)) if isinstance(col_map, dict) else str(line_col),
    )
    ax2.errorbar(
        x,
        y_line,
        yerr=work["line_err"].to_numpy(dtype=float) if "line_err" in work else None,
        fmt="o",
        color=line_color,
        markersize=float(marker_size),
        capsize=5 if "line_err" in work else 0,
        elinewidth=1.6,
        markeredgecolor="white",
        markeredgewidth=0.8,
        zorder=4,
    )
    mean_line = None
    if show_mean_line:
        mean_line = ax2.axhline(
            float(np.nanmean(y_line)),
            color=line_color,
            linestyle="--",
            linewidth=max(float(line_width) * 0.55, 1.0),
            alpha=0.65,
            zorder=3.5,
            label=mean_line_label,
        )

    divider_lines = []
    if group_splits:
        split_positions = [float(v) for v in group_splits]
    elif "group" in work:
        split_positions = []
        group_values = work["group"].tolist()
        for idx in range(1, len(group_values)):
            if group_values[idx] != group_values[idx - 1]:
                split_positions.append(idx - 0.5)
    else:
        split_positions = []
    for split in split_positions:
        divider_lines.append(ax.axvline(split, color="gray", linestyle="--",
                                        linewidth=1.5, alpha=0.6, zorder=1))

    if left_ylim is not None and len(left_ylim) == 2:
        ax.set_ylim(float(left_ylim[0]), float(left_ylim[1]))
    if right_ylim is not None and len(right_ylim) == 2:
        ax2.set_ylim(float(right_ylim[0]), float(right_ylim[1]))

    ax.spines["left"].set_color(bar_edge)
    ax.spines["left"].set_linewidth(2)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax2.spines["right"].set_color(line_color)
    ax2.spines["right"].set_linewidth(2)
    ax2.spines["left"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax.tick_params(axis="y", colors=bar_edge)
    ax2.tick_params(axis="y", colors=line_color)
    ax.set_ylabel(str(col_map.get(bar_col, bar_col)) if isinstance(col_map, dict) else str(bar_col),
                  color=bar_edge)
    ax2.set_ylabel(str(col_map.get(line_col, line_col)) if isinstance(col_map, dict) else str(line_col),
                   color=line_color)
    display_labels = [str(col_map.get(label, label)) if isinstance(col_map, dict) else label
                      for label in work["x_label"].tolist()]
    ax.set_xticks(x)
    ax.set_xticklabels(display_labels, rotation=xtick_rotation,
                       ha="center" if abs(xtick_rotation) >= 75 else "right",
                       fontweight="bold")
    ax.set_xlim(-0.7, len(work) - 0.3)
    ax.grid(axis="y", color="#EDEDED", linewidth=0.8, zorder=0)
    ax2.grid(False)
    legend_handles = [bars, line]
    legend_labels = [bars.get_label(), line.get_label()]
    if mean_line is not None:
        legend_handles.append(mean_line)
        legend_labels.append(mean_line.get_label())
    ax.legend(legend_handles, legend_labels, loc="upper left", frameon=False, fontsize=8)
    return {
        "ax_left": ax,
        "ax_right": ax2,
        "bars": bars,
        "line": line,
        "mean_line": mean_line,
        "divider_lines": divider_lines,
        "x_smooth": x_smooth,
        "left_color": bar_edge,
        "right_color": line_color,
        "n": len(work),
        "has_bar_error": "bar_err" in work,
        "has_line_error": "line_err" in work,
        "has_mean_line": mean_line is not None,
        "line_smoothing": bool(line_smoothing),
    }


def draw_dual_axis_hist_cumfreq_grid(df,
                                     *,
                                     value_cols: Sequence[str] | None = None,
                                     nrows: int = 3,
                                     ncols: int = 3,
                                     bins: int = 15,
                                     figsize: tuple[float, float] = (12, 10),
                                     wspace: float = 0.40,
                                     hspace: float = 0.35,
                                     hist_color: str = "gray",
                                     hist_edgecolor: str = "black",
                                     hist_alpha: float = 0.70,
                                     line_color: str = "blue",
                                     marker: str = "o",
                                     marker_size: float = 4.0,
                                     line_width: float = 1.5,
                                     col_map: dict | None = None) -> dict:
    """Draw the Case-020 3x3 histogram + cumulative-frequency twin-axis grid."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_dual_axis_hist_cumfreq_grid requires pandas") from exc

    def _as_column_list(raw) -> list[str]:
        if raw is None:
            return []
        if isinstance(raw, str):
            pieces = [part.strip() for part in raw.replace(";", ",").split(",")]
            return [part for part in pieces if part]
        if isinstance(raw, (list, tuple)):
            return [str(part) for part in raw if str(part) in df.columns]
        return []

    requested = _as_column_list(value_cols)
    selected: list[str] = []
    candidates = requested if requested else list(df.columns)
    for col in candidates:
        if col not in df.columns:
            continue
        vals = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if vals.size >= 2 and float(vals.max()) > float(vals.min()):
            selected.append(str(col))
        if len(selected) >= int(nrows) * int(ncols):
            break
    if not selected:
        raise ValueError("histogram cumulative-frequency grid requires at least one finite numeric column")

    fig, axes = plt.subplots(nrows=int(nrows), ncols=int(ncols), figsize=figsize)
    axes_flat = np.ravel(axes)
    fig.subplots_adjust(wspace=float(wspace), hspace=float(hspace))

    left_axes = []
    right_axes = []
    hist_patches = []
    lines = []
    counts_by_column = {}
    bins_by_column = {}

    for idx, ax1 in enumerate(axes_flat):
        if idx >= len(selected):
            ax1.set_visible(False)
            continue
        col = selected[idx]
        values = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy(dtype=float)
        counts, edges, patches = ax1.hist(
            values,
            bins=int(bins),
            color=hist_color,
            edgecolor=hist_edgecolor,
            alpha=float(hist_alpha),
            zorder=1,
        )
        for patch in patches:
            patch.set_gid("scifig_dual_axis_histogram_bar")
        ax1.set_gid("scifig_dual_axis_hist_cumfreq_left")
        ax2 = ax1.twinx()
        ax2.set_gid("scifig_dual_axis_hist_cumfreq_right")

        total = float(np.sum(counts))
        cumulative = np.cumsum(counts) / max(total, 1e-12) * 100.0
        centers = 0.5 * (edges[:-1] + edges[1:])
        line, = ax2.plot(
            centers,
            cumulative,
            color=line_color,
            marker=marker,
            markersize=float(marker_size),
            linewidth=float(line_width),
            zorder=3,
        )
        line.set_gid("scifig_dual_axis_cumulative_frequency_line")

        display = str(col_map.get(col, col)) if isinstance(col_map, dict) else str(col)
        ax1.set_xlabel(display, fontsize=8.0)
        ax1.set_ylabel("Frequency", fontsize=7.5)
        ax2.set_ylabel("Cumulative Frequency (%)", fontsize=7.5, color=line_color)
        ax2.set_ylim(0, 105)
        ax1.set_ylim(0, max(float(np.max(counts)) * 1.2, 1.0))
        ax1.tick_params(labelsize=7.0, direction="in")
        ax2.tick_params(labelsize=7.0, direction="in", colors=line_color)
        ax1.spines["top"].set_visible(False)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_color(line_color)
        ax2.grid(False)

        left_axes.append(ax1)
        right_axes.append(ax2)
        hist_patches.extend(list(patches))
        lines.append(line)
        counts_by_column[col] = counts.tolist()
        bins_by_column[col] = edges.tolist()

    return {
        "fig": fig,
        "axes_left": left_axes,
        "axes_right": right_axes,
        "hist_patches": hist_patches,
        "lines": lines,
        "columns": selected,
        "panel_count": len(left_axes),
        "twin_axis_count": len(right_axes),
        "histogram_count": len(left_axes),
        "cumulative_curve_count": len(lines),
        "grid_shape": [int(nrows), int(ncols)],
        "bins": int(bins),
        "right_ylim": [0, 105],
        "counts_by_column": counts_by_column,
        "bins_by_column": bins_by_column,
    }


def draw_pls_pm_path_model(ax: Axes,
                           edges_df,
                           *,
                           source_col: str,
                           target_col: str,
                           coef_col: str,
                           significance_col: str | None = None,
                           p_col: str | None = None,
                           curvature_col: str | None = None,
                           node_positions: dict | None = None,
                           total_effects: dict | None = None,
                           total_effect_col: str | None = None,
                           target_node: str | None = None,
                           gof_text: str | None = None,
                           positive_color: str = "#D73027",
                           negative_color: str = "#2B6CB0",
                           inset_rect: Sequence[float] = (0.70, 0.65, 0.25, 0.30),
                           linewidth_base: float = 1.0,
                           linewidth_scale: float = 8.0,
                           col_map: dict | None = None) -> dict:
    """Draw a Case-014 PLS-PM/SEM path model with a total-effect inset.

    Edges are a long table with source, target, signed coefficient, and optional
    significance. Color encodes sign and linewidth encodes abs(coefficient).
    """
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_pls_pm_path_model requires pandas") from exc
    import textwrap
    from collections import Counter
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    missing = [col for col in (source_col, target_col, coef_col) if col not in edges_df]
    if missing:
        raise ValueError(f"PLS-PM path model missing required columns: {missing}")

    def _p_to_stars(value) -> str:
        try:
            p = float(value)
        except Exception:
            return ""
        if p < 0.001:
            return "***"
        if p < 0.01:
            return "**"
        if p < 0.05:
            return "*"
        return ""

    work = pd.DataFrame({
        "source": edges_df[source_col].astype(str),
        "target": edges_df[target_col].astype(str),
        "coef": pd.to_numeric(edges_df[coef_col], errors="coerce"),
    })
    if significance_col and significance_col in edges_df:
        work["sig"] = edges_df[significance_col].fillna("").astype(str)
    elif p_col and p_col in edges_df:
        work["sig"] = edges_df[p_col].map(_p_to_stars)
    else:
        work["sig"] = ""
    if curvature_col and curvature_col in edges_df:
        work["curvature"] = pd.to_numeric(edges_df[curvature_col], errors="coerce")
    work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=["source", "target", "coef"])
    if work.empty:
        raise ValueError("PLS-PM path model requires at least one finite edge")

    node_order = list(dict.fromkeys(work["source"].tolist() + work["target"].tolist()))
    if target_node is None:
        target_counts = Counter(work["target"].tolist())
        target_node = target_counts.most_common(1)[0][0]
    target_node = str(target_node)

    if node_positions:
        positions = {
            str(label): (float(pos[0]), float(pos[1]))
            for label, pos in node_positions.items()
            if isinstance(pos, (list, tuple)) and len(pos) >= 2
        }
    else:
        positions = {}
    missing_nodes = [node for node in node_order if node not in positions]
    if missing_nodes:
        non_target = [node for node in node_order if node != target_node]
        roots = [
            node for node in non_target
            if node not in set(work["target"]) or node in set(work["source"]) - set(work["target"])
        ]
        mids = [node for node in non_target if node not in roots]
        y_roots = np.linspace(0.82, 0.18, max(1, len(roots)))
        y_mids = np.linspace(0.72, 0.28, max(1, len(mids)))
        for node, y in zip(roots, y_roots):
            positions.setdefault(node, (0.18, float(y)))
        for node, y in zip(mids, y_mids):
            positions.setdefault(node, (0.50, float(y)))
        positions.setdefault(target_node, (0.84, 0.50))
        fallback_y = np.linspace(0.80, 0.20, max(1, len(missing_nodes)))
        for node, y in zip(missing_nodes, fallback_y):
            positions.setdefault(node, (0.30, float(y)))

    xs = np.array([pos[0] for pos in positions.values()], dtype=float)
    ys = np.array([pos[1] for pos in positions.values()], dtype=float)
    x_span = max(float(xs.max() - xs.min()), 1.0)
    y_span = max(float(ys.max() - ys.min()), 1.0)
    ax.set_xlim(float(xs.min() - x_span * 0.34), float(xs.max() + x_span * 0.34))
    ax.set_ylim(float(ys.min() - y_span * 0.28), float(ys.max() + y_span * 0.28))
    ax.axis("off")
    ax.set_gid("scifig_pls_pm_path_model")

    box_w = min(max(x_span * 0.28, 0.18), x_span * 0.40)
    box_h = min(max(y_span * 0.08, 0.08), y_span * 0.13)
    if x_span > 2.5:
        box_w = min(max(box_w, 1.35), 1.90)
        box_h = min(max(box_h, 0.48), 0.72)

    node_patches = []
    for label in node_order:
        cx, cy = positions[label]
        is_target = label == target_node
        face = "#FFF4E6" if is_target else "#F7F7F7"
        edge = "#B85B2E" if is_target else "#444444"
        patch = FancyBboxPatch(
            (cx - box_w / 2, cy - box_h / 2),
            box_w,
            box_h,
            boxstyle="round,pad=0.08,rounding_size=0.08",
            facecolor=face,
            edgecolor=edge,
            linewidth=1.35,
            zorder=3,
        )
        ax.add_patch(patch)
        node_patches.append(patch)
        display = str(col_map.get(label, label)) if isinstance(col_map, dict) else label
        wrapped = "\n".join(textwrap.wrap(display, width=18)) or display
        ax.text(cx, cy, wrapped, ha="center", va="center", fontsize=8.0,
                fontweight="bold", zorder=4)

    edge_patches = []
    label_artists = []
    fallback_curvatures = np.linspace(0.16, -0.16, max(2, len(work)))
    for idx, row in enumerate(work.itertuples(index=False)):
        sx, sy = positions[row.source]
        tx, ty = positions[row.target]
        coef = float(row.coef)
        color = positive_color if coef >= 0 else negative_color
        lw = linewidth_base + abs(coef) * linewidth_scale
        if hasattr(row, "curvature") and np.isfinite(row.curvature):
            rad = float(row.curvature)
        else:
            rad = float(fallback_curvatures[idx % len(fallback_curvatures)])
        arrow = FancyArrowPatch(
            (sx, sy),
            (tx, ty),
            connectionstyle=f"arc3,rad={rad}",
            color=color,
            linewidth=lw,
            arrowstyle="-|>",
            mutation_scale=14.0 + abs(coef) * 10.0,
            shrinkA=22,
            shrinkB=24,
            alpha=0.84,
            zorder=1,
        )
        ax.add_patch(arrow)
        edge_patches.append(arrow)
        mid_x = (sx + tx) / 2
        mid_y = (sy + ty) / 2 + rad * y_span * 0.36
        label = f"{coef:+.3f}{row.sig}"
        label_artists.append(ax.text(
            mid_x,
            mid_y,
            label,
            ha="center",
            va="center",
            fontsize=7.0,
            color=color,
            fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.86, pad=1.4),
            zorder=5,
        ))

    if gof_text:
        center_x = float(np.mean(xs))
        center_y = float(np.mean(ys))
        ax.text(center_x, center_y, str(gof_text), fontsize=8.5, weight="bold",
                ha="center", va="center",
                bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.45"),
                zorder=6)

    if not total_effects:
        if total_effect_col and total_effect_col in edges_df:
            effect_work = pd.DataFrame({
                "node": edges_df[source_col].astype(str),
                "effect": pd.to_numeric(edges_df[total_effect_col], errors="coerce"),
            }).dropna(subset=["node", "effect"])
            total_effects = dict(zip(effect_work["node"], effect_work["effect"]))
        else:
            target_edges = work[work["target"] == target_node]
            total_effects = target_edges.groupby("source")["coef"].sum().to_dict()

    inset = None
    bars = []
    if total_effects:
        labels = [str(label) for label in total_effects.keys()]
        values = np.asarray([float(total_effects[label]) for label in labels], dtype=float)
        finite = np.isfinite(values)
        labels = [label for label, ok in zip(labels, finite) if ok]
        values = values[finite]
        if values.size:
            inset = ax.inset_axes(list(inset_rect), zorder=8)
            inset.set_gid("scifig_pls_total_effects_inset")
            y_pos = np.arange(len(labels))
            bar_colors = [positive_color if value >= 0 else negative_color for value in values]
            bars = inset.barh(y_pos, values, color=bar_colors, alpha=0.84, height=0.60)
            inset.axvline(0, color="black", linewidth=0.8, linestyle="--", zorder=1)
            inset.set_yticks(y_pos)
            inset.set_yticklabels(
                [str(col_map.get(label, label)) if isinstance(col_map, dict) else label for label in labels],
                fontsize=5.4,
            )
            inset.set_xlabel("effect", fontsize=6.0)
            inset.set_title(f"Total effects on\n{target_node}", fontsize=6.2, weight="bold")
            inset.tick_params(axis="x", labelsize=5.2, direction="in", length=2)
            inset.tick_params(axis="y", length=0)
            inset.spines["top"].set_visible(False)
            inset.spines["right"].set_visible(False)

    positive_edges = int((work["coef"] > 0).sum())
    negative_edges = int((work["coef"] < 0).sum())
    return {
        "ax": ax,
        "inset": inset,
        "nodes": node_patches,
        "edges": edge_patches,
        "labels": label_artists,
        "node_count": len(node_order),
        "edge_count": len(edge_patches),
        "positive_edge_count": positive_edges,
        "negative_edge_count": negative_edges,
        "significance_label_count": int(sum(bool(str(sig).strip()) for sig in work["sig"])),
        "total_effect_bar_count": len(bars),
        "has_zero_reference": inset is not None and bool(bars),
        "target_node": target_node,
    }


def draw_density_parity_matrix(df,
                               *,
                               actual_col: str,
                               predicted_col: str,
                               panel_col: str | None = None,
                               max_panels: int = 2,
                               cmap: str = "jet",
                               scatter_size: float = 20,
                               scatter_alpha: float = 0.90,
                               reference_color: str = "#D62728",
                               colorbar_label: str = "Density",
                               metric_box: bool = True,
                               figsize: tuple[float, float] = (12.0, 5.0),
                               wspace: float = 0.30,
                               col_map: dict | None = None) -> dict:
    """Draw Case-015 density-sorted KDE parity panels with per-panel colorbars."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_density_parity_matrix requires pandas") from exc

    missing = [col for col in (actual_col, predicted_col) if col not in df]
    if missing:
        raise ValueError(f"density parity matrix missing required columns: {missing}")

    plot_cols = [actual_col, predicted_col]
    if panel_col and panel_col in df and panel_col not in plot_cols:
        plot_cols.append(panel_col)
    work = df[plot_cols].copy()
    work[actual_col] = pd.to_numeric(work[actual_col], errors="coerce")
    work[predicted_col] = pd.to_numeric(work[predicted_col], errors="coerce")
    work = work.dropna(subset=[actual_col, predicted_col])
    if work.empty:
        raise ValueError("density parity matrix requires finite actual/predicted rows")

    if panel_col and panel_col in work:
        panels = work[panel_col].dropna().astype(str).unique().tolist()[:max_panels]
        if not panels:
            panels = ["Panel"]
    else:
        panels = ["Panel"]

    fig, axes_arr = plt.subplots(1, len(panels), figsize=figsize, squeeze=False)
    fig.subplots_adjust(wspace=wspace)
    axes = list(axes_arr[0])
    scatters = []
    colorbars = []
    metrics = []

    for idx, (sub_ax, panel_value) in enumerate(zip(axes, panels)):
        if panel_col and panel_col in work:
            panel_df = work[work[panel_col].astype(str) == str(panel_value)]
        else:
            panel_df = work
        x = panel_df[actual_col].to_numpy(dtype=float)
        y = panel_df[predicted_col].to_numpy(dtype=float)
        if len(x) < 3:
            continue

        sc = density_color_scatter(
            sub_ax,
            x,
            y,
            cmap=cmap,
            s=int(scatter_size),
            with_colorbar=False,
            edgecolor="none",
            linewidth=0.0,
            zorder=2,
        )
        sc.set_alpha(scatter_alpha)
        sc.set_gid("scifig_density_parity_points")
        scatters.append(sc)

        lo = float(np.nanmin([np.nanmin(x), np.nanmin(y)]))
        hi = float(np.nanmax([np.nanmax(x), np.nanmax(y)]))
        pad = max((hi - lo) * 0.04, 1e-9)
        sub_ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad],
                    color=reference_color, linewidth=2.0, zorder=3)
        sub_ax.set_xlim(lo - pad, hi + pad)
        sub_ax.set_ylim(lo - pad, hi + pad)
        sub_ax.set_aspect("equal", adjustable="box")
        sub_ax.set_gid("scifig_density_parity_panel")

        residuals = y - x
        ss_res = float(np.nansum(residuals ** 2))
        ss_tot = float(np.nansum((x - np.nanmean(x)) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        rmse = float(np.sqrt(np.nanmean(residuals ** 2))) if len(residuals) else np.nan
        metrics.append({"panel": str(panel_value), "r2": r2, "rmse": rmse, "n": int(len(x))})
        if metric_box:
            sub_ax.text(
                0.05,
                0.95,
                f"$R^2$ = {r2:.4f}\nRMSE = {rmse:.4f}",
                transform=sub_ax.transAxes,
                fontsize=8.5,
                va="top",
                ha="left",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.82, edgecolor="none"),
                zorder=10,
            )

        if len(panels) > 1:
            title = str(col_map.get(panel_value, panel_value)) if isinstance(col_map, dict) else str(panel_value)
            sub_ax.set_title(title, fontsize=9.0, fontweight="bold", pad=6)
        x_label = f"Experimental {panel_value}" if panel_value != "Panel" else str(actual_col)
        y_label = f"Predicted {panel_value}" if panel_value != "Panel" else str(predicted_col)
        if isinstance(col_map, dict):
            x_label = str(col_map.get(actual_col, x_label))
            y_label = str(col_map.get(predicted_col, y_label))
        sub_ax.set_xlabel(x_label, fontsize=8.2)
        sub_ax.set_ylabel(y_label if idx == 0 else "", fontsize=8.2)
        sub_ax.tick_params(labelsize=7, direction="in")
        sub_ax.spines["top"].set_visible(False)
        sub_ax.spines["right"].set_visible(False)

        cbar = fig.colorbar(sc, ax=sub_ax, fraction=0.046, pad=0.035)
        cbar.set_label(colorbar_label, rotation=270, labelpad=12, fontsize=7.4)
        cbar.ax.tick_params(labelsize=6.2, length=2)
        cbar.ax.set_gid("scifig_density_parity_colorbar")
        colorbars.append(cbar)

    return {
        "fig": fig,
        "axes": axes,
        "scatters": scatters,
        "colorbars": colorbars,
        "metrics": metrics,
        "panel_count": len(axes),
        "density_scatter_count": len(scatters),
        "colorbar_count": len(colorbars),
        "reference_line_count": len(scatters),
        "metric_box_count": len(metrics) if metric_box else 0,
        "cmap": cmap,
    }


def draw_hump_threshold_regression(df,
                                   *,
                                   x_col: str,
                                   y_col: str,
                                   threshold: float | None = None,
                                   degree: int = 3,
                                   n_bootstraps: int = 200,
                                   figsize: tuple[float, float] = (7.0, 5.0),
                                   ci_color: str = "#D9D9D9",
                                   ci_alpha: float = 0.60,
                                   scatter_color: str = "#E87A6E",
                                   global_line_color: str = "#404040",
                                   threshold_color: str = "#E63946",
                                   low_segment_color: str = "#2AB7CA",
                                   high_segment_color: str = "#1E847F",
                                   scatter_size: float = 60,
                                   scatter_alpha: float = 0.80,
                                   random_state: int = 42,
                                   col_map: dict | None = None) -> dict:
    """Draw Case-024 Advanced Science hump-shaped threshold regression."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_hump_threshold_regression requires pandas") from exc

    missing = [col for col in (x_col, y_col) if col not in df]
    if missing:
        raise ValueError(f"hump threshold regression missing required columns: {missing}")

    work = df[[x_col, y_col]].copy()
    work[x_col] = pd.to_numeric(work[x_col], errors="coerce")
    work[y_col] = pd.to_numeric(work[y_col], errors="coerce")
    work = work.dropna(subset=[x_col, y_col]).sort_values(x_col)
    if len(work) < 8:
        raise ValueError("hump threshold regression requires at least 8 finite rows")

    x = work[x_col].to_numpy(dtype=float)
    y = work[y_col].to_numpy(dtype=float)
    if threshold is None:
        threshold = float(x[int(np.nanargmax(y))])
    threshold = float(threshold)

    x_grid = np.linspace(float(np.nanmin(x)), float(np.nanmax(x)), 240)
    fit_degree = max(1, min(int(degree), len(x) - 1))

    def _poly_predict(x_train, y_train, x_eval):
        deg = max(1, min(fit_degree, len(x_train) - 1))
        coeff = np.polyfit(x_train, y_train, deg=deg)
        return np.polyval(coeff, x_eval)

    y_fit = _poly_predict(x, y, x_grid)
    rng = np.random.default_rng(random_state)
    boot_preds = []
    if int(n_bootstraps) > 0:
        for _ in range(int(n_bootstraps)):
            idx = rng.integers(0, len(x), len(x))
            x_s = x[idx]
            y_s = y[idx]
            if len(np.unique(x_s)) <= fit_degree:
                continue
            try:
                boot_preds.append(_poly_predict(x_s, y_s, x_grid))
            except Exception:
                continue
    if boot_preds:
        boot_arr = np.vstack(boot_preds)
        ci_lower = np.nanpercentile(boot_arr, 2.5, axis=0)
        ci_upper = np.nanpercentile(boot_arr, 97.5, axis=0)
    else:
        residual = y - np.interp(x, x_grid, y_fit)
        sigma = float(np.nanstd(residual)) or max(float(np.nanstd(y)) * 0.08, 1e-3)
        ci_lower = y_fit - 1.96 * sigma
        ci_upper = y_fit + 1.96 * sigma

    y_hat_at_x = np.interp(x, x_grid, y_fit)
    ss_res = float(np.nansum((y - y_hat_at_x) ** 2))
    ss_tot = float(np.nansum((y - np.nanmean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_gid("scifig_hump_threshold_regression")
    band = ax.fill_between(x_grid, ci_lower, ci_upper, color=ci_color,
                           alpha=ci_alpha, linewidth=0, zorder=1,
                           label="95% CI")
    band.set_gid("scifig_hump_threshold_ci_band")
    global_line = ax.plot(x_grid, y_fit, color=global_line_color,
                          linewidth=2.5, zorder=2,
                          label="Cubic fit")[0]
    global_line.set_gid("scifig_hump_threshold_global_fit")
    scatter = ax.scatter(x, y, color=scatter_color, s=scatter_size,
                         alpha=scatter_alpha, zorder=3,
                         edgecolor="white", linewidth=0.5,
                         label="Samples")
    scatter.set_gid("scifig_hump_threshold_points")

    segment_lines = []
    for mask, color, label in (
        (x <= threshold, low_segment_color, "Low regime"),
        (x >= threshold, high_segment_color, "High regime"),
    ):
        if int(np.sum(mask)) >= 2:
            xs = x[mask]
            ys = y[mask]
            coeff = np.polyfit(xs, ys, deg=1)
            x_seg = np.linspace(float(np.nanmin(xs)), float(np.nanmax(xs)), 80)
            line = ax.plot(x_seg, np.polyval(coeff, x_seg), color=color,
                           linewidth=3.5, linestyle="--", dashes=(4, 2),
                           zorder=4, label=label)[0]
            line.set_gid("scifig_hump_threshold_segment_fit")
            segment_lines.append(line)

    y_min, y_max = ax.get_ylim()
    threshold_line = ax.axvline(x=threshold, ymin=0.0, ymax=0.55,
                                color=threshold_color, linestyle="--",
                                linewidth=2.0, zorder=5, label="Threshold")
    threshold_line.set_gid("scifig_hump_threshold_line")
    ax.text(0.70, 0.90, f"$R^2={r2:.2f}^{{***}}$",
            transform=ax.transAxes, fontsize=14, zorder=8)
    ax.text(threshold + (x_grid.max() - x_grid.min()) * 0.015,
            y_min + (y_max - y_min) * 0.08,
            f"Threshold = {threshold:g}", color=threshold_color,
            fontsize=12, fontweight="bold", zorder=8)

    x_label = str(col_map.get(x_col, x_col)) if isinstance(col_map, dict) else str(x_col)
    y_label = str(col_map.get(y_col, y_col)) if isinstance(col_map, dict) else str(y_col)
    ax.set_xlabel(x_label, fontsize=11, fontweight="bold")
    ax.set_ylabel(y_label, fontsize=11, fontweight="bold")
    ax.grid(True, color="white", linestyle="--", linewidth=1.0, zorder=0)
    ax.set_facecolor("#F2F2F2")
    ax.tick_params(direction="in", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    legend = ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5),
                       frameon=False, fontsize=8)
    fig.subplots_adjust(right=0.76)

    return {
        "fig": fig,
        "axis": ax,
        "band": band,
        "scatter": scatter,
        "global_line": global_line,
        "segment_lines": segment_lines,
        "threshold_line": threshold_line,
        "legend": legend,
        "threshold": threshold,
        "r2": r2,
        "confidence_band_count": 1,
        "scatter_count": 1,
        "global_fit_count": 1,
        "segment_fit_count": len(segment_lines),
        "threshold_line_count": 1,
        "external_legend_count": 1,
        "annotation_count": 2,
    }


def draw_bayesian_ridge_heatmap_board(df,
                                      *,
                                      condition_col: str,
                                      factor_col: str,
                                      draw_col: str,
                                      correlation_col: str,
                                      probability_col: str | None = None,
                                      condition_order: Sequence[str] | None = None,
                                      figsize: tuple[float, float] = (16.0, 10.0),
                                      width_ratios: Sequence[float] = (4.2, 0.35, 0.6, 4.2, 0.35),
                                      positive_color: str = "#D95F5F",
                                      negative_color: str = "#4C78A8",
                                      heatmap_cmap: str = "RdBu_r",
                                      heatmap_vlim: float = 0.6,
                                      col_map: dict | None = None) -> dict:
    """Draw Case-025 Bayesian posterior ridges plus narrow correlation heat strips."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_bayesian_ridge_heatmap_board requires pandas") from exc

    missing = [col for col in (condition_col, factor_col, draw_col, correlation_col) if col not in df]
    if missing:
        raise ValueError(f"Bayesian ridge heatmap board missing required columns: {missing}")

    work_cols = [condition_col, factor_col, draw_col, correlation_col]
    if probability_col and probability_col in df:
        work_cols.append(probability_col)
    work = df[work_cols].copy()
    work[condition_col] = work[condition_col].astype(str)
    work[factor_col] = work[factor_col].astype(str)
    work[draw_col] = pd.to_numeric(work[draw_col], errors="coerce")
    work[correlation_col] = pd.to_numeric(work[correlation_col], errors="coerce")
    if probability_col and probability_col in work:
        work[probability_col] = pd.to_numeric(work[probability_col], errors="coerce")
    work = work.dropna(subset=[condition_col, factor_col, draw_col, correlation_col])
    if work.empty:
        raise ValueError("Bayesian ridge heatmap board requires finite posterior/correlation rows")

    available = list(dict.fromkeys(work[condition_col].tolist()))
    if condition_order:
        conditions = [str(c) for c in condition_order if str(c) in available]
        conditions += [c for c in available if c not in conditions]
    else:
        conditions = available
    conditions = conditions[:2]
    if len(conditions) < 2:
        raise ValueError("Bayesian ridge heatmap board requires two conditions")

    factors = list(dict.fromkeys(work[factor_col].tolist()))
    med = work.groupby(factor_col)[draw_col].median().reindex(factors)
    factors = sorted(factors, key=lambda f: float(med.get(f, 0.0)))
    x_vals = work[draw_col].dropna().to_numpy(dtype=float)
    x_min, x_max = float(np.nanmin(x_vals)), float(np.nanmax(x_vals))
    pad = max((x_max - x_min) * 0.12, 0.1)
    x_grid = np.linspace(x_min - pad, x_max + pad, 320)

    fig = plt.figure(figsize=figsize)
    gs = GridSpec(1, 5, figure=fig, width_ratios=list(width_ratios), wspace=0.15)
    ax_low_ridge = fig.add_subplot(gs[0])
    ax_low_heat = fig.add_subplot(gs[1])
    ax_gap = fig.add_subplot(gs[2])
    ax_high_ridge = fig.add_subplot(gs[3])
    ax_high_heat = fig.add_subplot(gs[4])
    ax_gap.axis("off")
    ax_gap.set_gid("scifig_bayesian_ridge_heatmap_gap")

    ridge_axes = [ax_low_ridge, ax_high_ridge]
    heat_axes = [ax_low_heat, ax_high_heat]
    ridge_patches = []
    ridge_outlines = []
    probability_texts = []
    heat_images = []
    significance_texts = []
    colorbars = []

    def _display(value):
        return str(col_map.get(value, value)) if isinstance(col_map, dict) else str(value)

    def _density(vals):
        vals = np.asarray(vals, dtype=float)
        vals = vals[np.isfinite(vals)]
        if len(vals) < 2:
            return np.zeros_like(x_grid)
        sigma = float(np.nanstd(vals)) * len(vals) ** (-1 / 5)
        if not np.isfinite(sigma) or sigma <= 1e-9:
            sigma = 0.1
        dens = np.zeros_like(x_grid)
        for val in vals:
            dens += np.exp(-0.5 * ((x_grid - val) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
        dens = dens / max(float(np.nanmax(dens)), 1e-12) * 0.82
        return dens

    for cond, ax_ridge, ax_heat in zip(conditions, ridge_axes, heat_axes):
        subset = work[work[condition_col] == cond]
        ax_ridge.set_gid("scifig_bayesian_ridge_panel")
        ax_ridge.axvline(0, linestyle="--", color="black", alpha=0.5, zorder=1)
        for i, factor in enumerate(factors):
            vals = subset[subset[factor_col] == factor][draw_col].to_numpy(dtype=float)
            if len(vals) == 0:
                continue
            dens = _density(vals)
            mean_val = float(np.nanmean(vals))
            color = positive_color if mean_val >= 0 else negative_color
            patch = ax_ridge.fill_between(x_grid, i, i + dens, color=color,
                                          alpha=0.85, linewidth=0, zorder=3)
            patch.set_gid("scifig_bayesian_ridge_fill")
            ridge_patches.append(patch)
            line = ax_ridge.plot(x_grid, i + dens, color="white",
                                 linewidth=1.2, zorder=4)[0]
            line.set_gid("scifig_bayesian_ridge_white_outline")
            ridge_outlines.append(line)
            prob = None
            if probability_col and probability_col in subset:
                pvals = subset[subset[factor_col] == factor][probability_col].dropna()
                if len(pvals):
                    prob = float(pvals.iloc[0])
            if prob is None:
                prob = float(np.mean(vals > 0) * 100.0)
            txt = ax_ridge.text(x_grid[-1], i + 0.20, f"{prob:.0f}%",
                                color=color, fontweight="bold", fontsize=8,
                                ha="right", va="center", zorder=5)
            txt.set_gid("scifig_bayesian_ridge_probability_text")
            probability_texts.append(txt)
        ax_ridge.set_ylim(-0.8, len(factors) + 0.5)
        ax_ridge.set_yticks(np.arange(len(factors)))
        ax_ridge.set_yticklabels([_display(f) for f in factors], fontsize=8)
        ax_ridge.set_xlabel("Posterior effect")
        ax_ridge.set_title(_display(cond), fontsize=10, fontweight="bold")
        ax_ridge.spines["top"].set_visible(False)
        ax_ridge.spines["right"].set_visible(False)

        corr_vals = []
        for factor in factors:
            cvals = subset[subset[factor_col] == factor][correlation_col].dropna()
            corr_vals.append(float(cvals.iloc[0]) if len(cvals) else np.nan)
        corr_arr = np.asarray(corr_vals, dtype=float).reshape(-1, 1)
        im = ax_heat.imshow(corr_arr, cmap=heatmap_cmap, aspect="auto",
                            vmin=-abs(float(heatmap_vlim)), vmax=abs(float(heatmap_vlim)),
                            origin="lower")
        ax_heat.set_gid("scifig_bayesian_heat_strip")
        heat_images.append(im)
        ax_heat.set_xticks([])
        ax_heat.set_yticks(np.arange(len(factors)))
        ax_heat.set_yticklabels([_display(f) for f in factors], fontsize=7)
        ax_heat.yaxis.tick_right()
        for i, value in enumerate(corr_vals):
            if np.isfinite(value) and abs(value) > 0.3:
                star = ax_heat.text(0, i, "*", ha="center", va="center",
                                    fontsize=18, fontweight="bold", zorder=5)
                star.set_gid("scifig_bayesian_heatmap_significance")
                significance_texts.append(star)
        cax = ax_heat.inset_axes([0.0, -0.15, 1.0, 0.05])
        cax.set_gid("scifig_bayesian_heatmap_inset_colorbar")
        cbar = fig.colorbar(im, cax=cax, orientation="horizontal")
        cbar.set_ticks([-0.5, 0.5])
        colorbars.append(cbar)

    return {
        "fig": fig,
        "axes": [ax_low_ridge, ax_low_heat, ax_gap, ax_high_ridge, ax_high_heat],
        "ridge_axes": ridge_axes,
        "heat_axes": heat_axes,
        "ridge_patches": ridge_patches,
        "ridge_outlines": ridge_outlines,
        "probability_texts": probability_texts,
        "heat_images": heat_images,
        "significance_texts": significance_texts,
        "colorbars": colorbars,
        "conditions": conditions,
        "factors": factors,
        "grid_width_ratios": list(width_ratios),
        "ridge_panel_count": len(ridge_axes),
        "heat_strip_count": len(heat_axes),
        "ridge_fill_count": len(ridge_patches),
        "ridge_outline_count": len(ridge_outlines),
        "probability_text_count": len(probability_texts),
        "significance_text_count": len(significance_texts),
        "inset_colorbar_count": len(colorbars),
    }


def draw_inset_heatmap_bar_rank(df,
                                *,
                                category_col: str,
                                value_col: str,
                                error_col: str | None = None,
                                heatmap_cols: Sequence[str] | None = None,
                                sort_descending: bool = True,
                                figsize: tuple[float, float] = (8.0, 6.0),
                                bar_color: str = "#ED9F78",
                                jitter_seed: int = 2027,
                                inset_rect: Sequence[float] = (0.45, 0.44, 0.44, 0.50),
                                heatmap_cmap: str = "RdBu",
                                heatmap_vmin: float = -1.0,
                                heatmap_vmax: float = 1.0,
                                col_map: dict | None = None) -> dict:
    """Draw Case-027 ranked bars with raw jitter points and a heatmap inset.

    The template preserves the article's single-axis discipline: the ranking is
    the main evidence layer, while a compact inset heatmap occupies deliberate
    top-right whitespace instead of becoming a loose second panel.
    """
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_inset_heatmap_bar_rank requires pandas") from exc

    missing = [col for col in (category_col, value_col) if col not in df]
    if missing:
        raise ValueError(f"inset heatmap bar rank missing required columns: {missing}")

    work = df.copy()
    work[category_col] = work[category_col].astype(str)
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    if error_col and error_col in work:
        work[error_col] = pd.to_numeric(work[error_col], errors="coerce")
    work = work.dropna(subset=[category_col, value_col])
    if work.empty:
        raise ValueError("inset heatmap bar rank requires finite category/value rows")

    stats = work.groupby(category_col, sort=False)[value_col].agg(["mean", "std", "count"])
    if error_col and error_col in work:
        err = work.groupby(category_col, sort=False)[error_col].mean()
        stats["err"] = err.reindex(stats.index).fillna(0.0).to_numpy(dtype=float)
    else:
        stats["err"] = stats["std"].fillna(0.0).to_numpy(dtype=float)
    stats = stats.sort_values("mean", ascending=not bool(sort_descending))
    categories = stats.index.tolist()
    if len(categories) < 2:
        raise ValueError("inset heatmap bar rank requires at least two categories")

    numeric_cols = [col for col in work.select_dtypes(include=[np.number]).columns if col != value_col]
    if heatmap_cols:
        heat_cols = [col for col in heatmap_cols if col in work and col != value_col]
    else:
        heat_cols = numeric_cols[:6]
    if len(heat_cols) >= 2:
        heat_data = work[heat_cols].apply(pd.to_numeric, errors="coerce").corr().fillna(0.0)
        heat_labels = [str(col_map.get(col, col)) if isinstance(col_map, dict) else str(col) for col in heat_cols]
    else:
        rank_values = stats["mean"].to_numpy(dtype=float)
        spread = max(float(np.ptp(rank_values)), 1e-9)
        scaled = (rank_values - float(np.nanmin(rank_values))) / spread
        matrix = 1.0 - np.abs(scaled[:, None] - scaled[None, :]) * 2.0
        heat_data = pd.DataFrame(np.clip(matrix, -1.0, 1.0), index=categories, columns=categories)
        heat_labels = [str(label) for label in categories]

    display_categories = [
        str(col_map.get(cat, cat)) if isinstance(col_map, dict) else str(cat)
        for cat in categories
    ]
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_gid("scifig_inset_heatmap_bar_rank_main")
    x = np.arange(len(categories), dtype=float)
    means = stats["mean"].to_numpy(dtype=float)
    errs = stats["err"].to_numpy(dtype=float)
    bars = ax.bar(
        x,
        means,
        yerr=errs,
        color=bar_color,
        edgecolor="none",
        width=0.74,
        ecolor="black",
        capsize=3.0,
        error_kw={"elinewidth": 1.0, "zorder": 5},
        zorder=2,
    )
    for patch in bars:
        patch.set_gid("scifig_inset_heatmap_rank_bar")

    rng = np.random.default_rng(jitter_seed)
    jitter_artists = []
    for idx, category in enumerate(categories):
        vals = work.loc[work[category_col] == category, value_col].to_numpy(dtype=float)
        if len(vals) == 0:
            continue
        jitter_x = idx + rng.uniform(-0.10, 0.10, size=len(vals))
        scatter = ax.scatter(
            jitter_x,
            vals,
            s=24,
            facecolors="none",
            edgecolors="black",
            linewidths=0.75,
            alpha=0.78,
            zorder=6,
        )
        scatter.set_gid("scifig_inset_heatmap_rank_jitter")
        jitter_artists.append(scatter)

    upper = float(np.nanmax(means + errs)) if len(means) else 1.0
    lower = min(0.0, float(np.nanmin(work[value_col].to_numpy(dtype=float))))
    ax.set_ylim(lower, upper * 1.42 if upper > 0 else upper + abs(upper) * 0.42 + 1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(display_categories, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(str(col_map.get(value_col, value_col)) if isinstance(col_map, dict) else str(value_col),
                  fontsize=10, fontweight="bold")
    ax.tick_params(direction="in")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax_inset = ax.inset_axes(list(inset_rect), zorder=9)
    ax_inset.set_gid("scifig_inset_heatmap_bar_rank_heatmap")
    im = ax_inset.imshow(
        heat_data.to_numpy(dtype=float),
        cmap=heatmap_cmap,
        vmin=heatmap_vmin,
        vmax=heatmap_vmax,
        aspect="auto",
        zorder=2,
    )
    n_heat = len(heat_labels)
    ax_inset.set_xticks(np.arange(n_heat))
    ax_inset.set_yticks(np.arange(n_heat))
    ax_inset.set_xticklabels(heat_labels, rotation=45, ha="right", fontsize=6)
    ax_inset.set_yticklabels(heat_labels, fontsize=6)
    ax_inset.tick_params(length=0)
    for spine in ax_inset.spines.values():
        spine.set_visible(False)

    cax = ax_inset.inset_axes([1.04, 0.15, 0.045, 0.70])
    cax.set_gid("scifig_inset_heatmap_bar_rank_colorbar")
    colorbar = fig.colorbar(im, cax=cax)
    colorbar.set_label("Pearson r", fontsize=7)
    colorbar.ax.tick_params(labelsize=6, length=2, direction="in")

    return {
        "fig": fig,
        "axis": ax,
        "inset_axis": ax_inset,
        "colorbar_axis": cax,
        "bars": bars,
        "jitter_artists": jitter_artists,
        "heatmap_image": im,
        "colorbar": colorbar,
        "categories": categories,
        "heatmap_labels": heat_labels,
        "bar_count": len(bars),
        "jitter_layer_count": len(jitter_artists),
        "sample_point_count": int(len(work)),
        "inset_heatmap_count": 1,
        "inset_colorbar_count": 1,
    }


def draw_time_series_prediction_interval(df,
                                         *,
                                         time_col: str,
                                         actual_col: str,
                                         predicted_col: str,
                                         lower_col: str | None = None,
                                         upper_col: str | None = None,
                                         split_col: str | None = None,
                                         split_index: float | int | None = None,
                                         figsize: tuple[float, float] = (10.0, 5.0),
                                         interval_color: str = "skyblue",
                                         interval_alpha: float = 0.40,
                                         observed_color: str = "black",
                                         predicted_color: str = "red",
                                         divider_color: str = "gray",
                                         observed_size: float = 15,
                                         observed_alpha: float = 0.70,
                                         predicted_lw: float = 1.5,
                                         interval_label: str = "90% Prediction Interval",
                                         observed_label: str = "Actual Observations",
                                         predicted_label: str = "Model Prediction",
                                         train_label: str = "Training data set",
                                         test_label: str = "Testing data set",
                                         top_legend: bool = True,
                                         region_labels: bool = True,
                                         col_map: dict | None = None) -> dict:
    """Draw Case-016 time-series prediction interval with train/test split."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_time_series_prediction_interval requires pandas") from exc

    missing = [col for col in (time_col, actual_col, predicted_col) if col not in df]
    if missing:
        raise ValueError(f"time-series prediction interval missing required columns: {missing}")

    plot_cols = [time_col, actual_col, predicted_col]
    for col in (lower_col, upper_col, split_col):
        if col and col in df and col not in plot_cols:
            plot_cols.append(col)
    work = df[plot_cols].copy()
    work["_x"] = pd.to_numeric(work[time_col], errors="coerce")
    if work["_x"].isna().all():
        work["_x"] = np.arange(len(work), dtype=float)
        x_label = "Sample index"
    else:
        x_label = str(col_map.get(time_col, time_col)) if isinstance(col_map, dict) else str(time_col)
    work["_actual"] = pd.to_numeric(work[actual_col], errors="coerce")
    work["_predicted"] = pd.to_numeric(work[predicted_col], errors="coerce")

    has_interval_cols = lower_col and upper_col and lower_col in work and upper_col in work
    if has_interval_cols:
        work["_lower"] = pd.to_numeric(work[lower_col], errors="coerce")
        work["_upper"] = pd.to_numeric(work[upper_col], errors="coerce")
    else:
        residuals = work["_actual"] - work["_predicted"]
        sigma = float(np.nanstd(residuals))
        if not np.isfinite(sigma) or sigma <= 1e-12:
            sigma = max(float(np.nanstd(work["_actual"])), 1.0) * 0.08
        half_width = 1.645 * sigma
        work["_lower"] = work["_predicted"] - half_width
        work["_upper"] = work["_predicted"] + half_width

    work = work.dropna(subset=["_x", "_actual", "_predicted", "_lower", "_upper"]).sort_values("_x")
    if work.empty:
        raise ValueError("time-series prediction interval requires finite time/actual/predicted/interval rows")

    x = work["_x"].to_numpy(dtype=float)
    actual = work["_actual"].to_numpy(dtype=float)
    predicted = work["_predicted"].to_numpy(dtype=float)
    lower = work["_lower"].to_numpy(dtype=float)
    upper = work["_upper"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(left=0.10, right=0.95, top=0.85 if top_legend else 0.92, bottom=0.15)
    ax.set_gid("scifig_time_series_pi")
    band = ax.fill_between(
        x,
        lower,
        upper,
        color=interval_color,
        alpha=interval_alpha,
        linewidth=0,
        label=interval_label,
        zorder=1,
    )
    band.set_gid("scifig_time_series_pi_band")
    observed = ax.scatter(
        x,
        actual,
        color=observed_color,
        s=observed_size,
        alpha=observed_alpha,
        label=observed_label,
        zorder=2,
    )
    observed.set_gid("scifig_time_series_pi_observed")
    predicted_line = ax.plot(
        x,
        predicted,
        color=predicted_color,
        linewidth=predicted_lw,
        label=predicted_label,
        zorder=3,
    )[0]
    predicted_line.set_gid("scifig_time_series_pi_prediction")

    divider = None
    split_value = split_index
    if split_value is None and split_col and split_col in work:
        labels = work[split_col].astype(str).str.lower().to_numpy()
        is_test = np.array([
            any(token in label for token in ("test", "testing", "validation", "holdout", "unknown"))
            for label in labels
        ], dtype=bool)
        if is_test.any() and (~is_test).any():
            split_value = float(x[int(np.flatnonzero(is_test)[0])])
        else:
            changes = np.flatnonzero(labels[1:] != labels[:-1])
            if len(changes):
                pos = int(changes[0])
                split_value = float((x[pos] + x[pos + 1]) / 2)

    region_texts = []
    if split_value is not None and np.isfinite(float(split_value)):
        split_value = float(split_value)
        divider = ax.axvline(
            x=split_value,
            color=divider_color,
            linestyle="--",
            linewidth=1.5,
            alpha=0.85,
            zorder=4,
        )
        divider.set_gid("scifig_time_series_pi_split")
        if region_labels:
            y_min, y_max = ax.get_ylim()
            y_text = y_min + (y_max - y_min) * 0.95
            x_min, x_max = float(np.nanmin(x)), float(np.nanmax(x))
            train_x = (x_min + split_value) / 2
            test_x = (split_value + x_max) / 2
            region_texts.append(ax.text(
                train_x,
                y_text,
                train_label,
                ha="center",
                va="top",
                fontweight="bold",
                fontsize=9.0,
                color="#4C78A8",
                zorder=10,
            ))
            region_texts.append(ax.text(
                test_x,
                y_text,
                test_label,
                ha="center",
                va="top",
                fontweight="bold",
                fontsize=9.0,
                color="#E45756",
                zorder=10,
            ))
            for text in region_texts:
                text.set_gid("scifig_time_series_pi_region_label")

    legend = None
    if top_legend:
        legend = ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15),
                           ncol=3, frameon=False, fontsize=8.5)
    ax.set_xlabel(x_label, fontsize=9.0)
    y_label = str(col_map.get(actual_col, actual_col)) if isinstance(col_map, dict) else str(actual_col)
    ax.set_ylabel(y_label, fontsize=9.0)
    ax.tick_params(direction="in", labelsize=8.0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#E6E6E6", linestyle="--", linewidth=0.55, alpha=0.65, zorder=0)

    return {
        "fig": fig,
        "axis": ax,
        "band": band,
        "observed": observed,
        "predicted_line": predicted_line,
        "divider": divider,
        "region_texts": region_texts,
        "legend": legend,
        "interval_band_count": 1,
        "observed_scatter_count": 1,
        "predicted_line_count": 1,
        "train_test_divider_count": 1 if divider is not None else 0,
        "train_test_region_label_count": len(region_texts),
        "legend_count": 1 if legend is not None else 0,
        "split_index": split_value,
        "uses_supplied_interval": bool(has_interval_cols),
    }


def draw_shap_dependence_background_grid(df,
                                         *,
                                         feature_col: str,
                                         feature_value_col: str,
                                         shap_value_col: str,
                                         max_features: int = 6,
                                         ncols: int = 3,
                                         figsize: tuple[float, float] = (12.0, 7.0),
                                         y_limits: tuple[float, float] = (-2.5, 2.5),
                                         positive_color: str = "#ffcccc",
                                         negative_color: str = "#cce5ff",
                                         background_alpha: float = 0.40,
                                         scatter_color: str = "black",
                                         scatter_size: float = 15,
                                         scatter_alpha: float = 0.70,
                                         zero_color: str = "gray",
                                         col_map: dict | None = None) -> dict:
    """Draw Case-017 2x3 SHAP dependence panels with signed background zones."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_shap_dependence_background_grid requires pandas") from exc

    missing = [col for col in (feature_col, feature_value_col, shap_value_col) if col not in df]
    if missing:
        raise ValueError(f"SHAP dependence grid missing required columns: {missing}")

    work = df[[feature_col, feature_value_col, shap_value_col]].copy()
    work[feature_col] = work[feature_col].astype(str)
    work[feature_value_col] = pd.to_numeric(work[feature_value_col], errors="coerce")
    work[shap_value_col] = pd.to_numeric(work[shap_value_col], errors="coerce")
    work = work.dropna(subset=[feature_col, feature_value_col, shap_value_col])
    if work.empty:
        raise ValueError("SHAP dependence grid requires finite feature/value/SHAP rows")

    features = work[feature_col].dropna().astype(str).unique().tolist()[:max(1, int(max_features))]
    ncols = max(1, int(ncols))
    nrows = int(np.ceil(len(features) / ncols))
    fig, axes_arr = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, squeeze=False)
    fig.subplots_adjust(wspace=0.30, hspace=0.40, left=0.08, right=0.95, bottom=0.10, top=0.92)
    axes = list(axes_arr.ravel())
    active_axes = []
    scatters = []
    zero_lines = []
    background_patches = []

    y_min, y_max = y_limits
    for idx, (ax, feature) in enumerate(zip(axes, features)):
        sub = work[work[feature_col] == feature]
        pos_patch = ax.axhspan(ymin=0, ymax=y_max, color=positive_color,
                               alpha=background_alpha, zorder=0)
        neg_patch = ax.axhspan(ymin=y_min, ymax=0, color=negative_color,
                               alpha=background_alpha, zorder=0)
        pos_patch.set_gid("scifig_shap_positive_background")
        neg_patch.set_gid("scifig_shap_negative_background")
        background_patches.extend([pos_patch, neg_patch])
        zero_line = ax.axhline(y=0, color=zero_color, linestyle="--",
                               linewidth=1.5, zorder=1)
        zero_line.set_gid("scifig_shap_zero_reference")
        zero_lines.append(zero_line)
        sc = ax.scatter(
            sub[feature_value_col],
            sub[shap_value_col],
            color=scatter_color,
            s=scatter_size,
            alpha=scatter_alpha,
            linewidth=0,
            zorder=2,
        )
        sc.set_gid("scifig_shap_dependence_points")
        scatters.append(sc)
        ax.set_gid("scifig_shap_dependence_background_panel")
        label = str(col_map.get(feature, feature)) if isinstance(col_map, dict) else str(feature)
        ax.set_xlabel(label, fontsize=9.0, fontweight="bold")
        ax.set_ylabel("SHAP value" if idx % ncols == 0 else "", fontsize=9.0)
        ax.set_ylim(y_min, y_max)
        ax.tick_params(labelsize=7.5, direction="in")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        active_axes.append(ax)

    for ax in axes[len(features):]:
        ax.set_visible(False)

    return {
        "fig": fig,
        "axes": active_axes,
        "scatters": scatters,
        "zero_lines": zero_lines,
        "background_patches": background_patches,
        "panel_count": len(active_axes),
        "scatter_count": len(scatters),
        "zero_line_count": len(zero_lines),
        "background_zone_count": len(background_patches),
        "positive_background_count": len(active_axes),
        "negative_background_count": len(active_axes),
        "y_limits": [float(y_min), float(y_max)],
    }


def draw_shap_interaction_dependence_grid(df,
                                          *,
                                          feature_col: str,
                                          feature_value_col: str,
                                          shap_value_col: str,
                                          interaction_col: str,
                                          max_features: int = 6,
                                          ncols: int = 3,
                                          figsize: tuple[float, float] = (14.0, 8.0),
                                          cmap: str = "coolwarm",
                                          scatter_size: float = 15,
                                          scatter_alpha: float = 0.80,
                                          zero_color: str = "gray",
                                          colorbar_label: str = "Interaction Feature",
                                          col_map: dict | None = None) -> dict:
    """Draw Case-018 2x3 SHAP dependence grid with interaction colorbars."""
    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("draw_shap_interaction_dependence_grid requires pandas") from exc

    missing = [col for col in (feature_col, feature_value_col, shap_value_col, interaction_col) if col not in df]
    if missing:
        raise ValueError(f"SHAP interaction dependence grid missing required columns: {missing}")

    work = df[[feature_col, feature_value_col, shap_value_col, interaction_col]].copy()
    work[feature_col] = work[feature_col].astype(str)
    work[feature_value_col] = pd.to_numeric(work[feature_value_col], errors="coerce")
    work[shap_value_col] = pd.to_numeric(work[shap_value_col], errors="coerce")
    work[interaction_col] = pd.to_numeric(work[interaction_col], errors="coerce")
    work = work.dropna(subset=[feature_col, feature_value_col, shap_value_col, interaction_col])
    if work.empty:
        raise ValueError("SHAP interaction grid requires finite feature/value/SHAP/interaction rows")

    features = work[feature_col].dropna().astype(str).unique().tolist()[:max(1, int(max_features))]
    ncols = max(1, int(ncols))
    nrows = int(np.ceil(len(features) / ncols))
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(nrows, ncols, wspace=0.40, hspace=0.30)
    axes = []
    scatters = []
    colorbars = []
    zero_lines = []
    panel_texts = []
    labels = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)", "(g)", "(h)", "(i)"]

    for idx, feature in enumerate(features):
        ax = fig.add_subplot(gs[idx // ncols, idx % ncols])
        sub = work[work[feature_col] == feature]
        sc = ax.scatter(
            sub[feature_value_col],
            sub[shap_value_col],
            c=sub[interaction_col],
            cmap=cmap,
            s=scatter_size,
            alpha=scatter_alpha,
            edgecolors="none",
            zorder=2,
        )
        sc.set_gid("scifig_shap_interaction_points")
        zero_line = ax.axhline(0, color=zero_color, linestyle="--",
                               linewidth=0.8, zorder=1)
        zero_line.set_gid("scifig_shap_interaction_zero_reference")
        zero_lines.append(zero_line)
        ax.set_gid("scifig_shap_interaction_dependence_panel")
        label = str(col_map.get(feature, feature)) if isinstance(col_map, dict) else str(feature)
        ax.set_xlabel(label, fontsize=8.8, fontweight="bold")
        ax.set_ylabel("SHAP value for CH$_4$ conversion", fontsize=8.2)
        ax.tick_params(labelsize=7.0, direction="in")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        panel_text = ax.text(-0.15, 1.05, labels[idx], transform=ax.transAxes,
                             fontsize=9.0, fontweight="bold", va="bottom", zorder=6)
        panel_text.set_gid("scifig_shap_interaction_panel_label")
        cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(colorbar_label, size=7.0)
        cbar.ax.tick_params(labelsize=6.0, length=2)
        cbar.ax.set_gid("scifig_shap_interaction_colorbar")
        axes.append(ax)
        scatters.append(sc)
        colorbars.append(cbar)
        panel_texts.append(panel_text)

    return {
        "fig": fig,
        "axes": axes,
        "scatters": scatters,
        "colorbars": colorbars,
        "zero_lines": zero_lines,
        "panel_texts": panel_texts,
        "panel_count": len(axes),
        "scatter_count": len(scatters),
        "colorbar_count": len(colorbars),
        "zero_line_count": len(zero_lines),
        "panel_label_count": len(panel_texts),
        "cmap": cmap,
    }


# ============================================================================
# 10. OCCLUSION GUARDS  (cycle 22: anti-overlap discipline)
# ============================================================================
#
# Three helpers that protect generated figures from the three dominant
# occlusion modes observed in cycle-22 audit:
#
#   1. safe_annotate            Replaces ax.text/ax.annotate; forces zorder>=20
#                               and an opaque rounded white bbox so the text
#                               reads on any data background.
#   2. choose_heatmap_fmt       Picks "{:.Nf}" format string adaptively from
#                               cell physical size, font size, and value range
#                               so heatmap cell labels never overflow.
#   3. auto_relocate_annotations
#                               Post-render collision avoidance: probes text
#                               artists' display bbox against data artists,
#                               picks the least-occluded candidate offset.
#
# The constants below were calibrated against the template corpus.

_SAFE_ANNOT_ZORDER = 20
_SAFE_ANNOT_BBOX_ALPHA = 0.85
_SAFE_ANNOT_BBOX_PAD = 0.25
_HEATMAP_CELL_SAFETY = 0.85       # use 85% of cell width before rejecting fmt
_HEATMAP_CHAR_WIDTH_PT = 0.55     # digit width / font size for sans-serif
_RELOCATE_OFFSET_POINTS = [
    (0, 8), (0, -8), (8, 0), (-8, 0),
    (8, 8), (-8, 8), (8, -8), (-8, -8),
    (0, 14), (0, -14), (14, 0), (-14, 0),
]


def safe_annotate(
    ax: Axes,
    text: str,
    xy: tuple[float, float],
    *,
    xytext: tuple[float, float] | None = None,
    xycoords: str = "data",
    textcoords: str | None = None,
    ha: str = "center",
    va: str = "center",
    fontsize: float | None = None,
    color: str = "black",
    zorder: float | None = None,
    bbox: dict | bool | None = True,
    arrowprops: dict | None = None,
    **kwargs,
):
    """Drop-in replacement for ax.annotate / ax.text with anti-occlusion guards.

    Differences from raw ax.annotate:
      * zorder is forced to >= 20 so labels sit above every data layer
        (default zorder for ax.plot=2, ax.scatter=1, ax.fill=1; this
        ensures annotations are not silently buried by curves drawn later).
      * bbox defaults to an opaque rounded white box (alpha 0.85) so the
        text remains readable when a data line passes underneath.
      * va/ha default to "center" to keep annotations flush with their
        anchor point rather than baseline-left (matplotlib default).

    Pass ``bbox=False`` to disable the white box (e.g., for heatmap cell
    labels where the cell colour already provides contrast).
    Pass an explicit dict to override individual bbox properties.
    """
    if zorder is None or zorder < _SAFE_ANNOT_ZORDER:
        zorder = _SAFE_ANNOT_ZORDER

    if bbox is True:
        bbox_props: dict | None = dict(
            boxstyle=f"round,pad={_SAFE_ANNOT_BBOX_PAD}",
            facecolor="white",
            alpha=_SAFE_ANNOT_BBOX_ALPHA,
            edgecolor="none",
            linewidth=0,
        )
    elif bbox is False or bbox is None:
        bbox_props = None
    else:
        bbox_props = dict(bbox)

    annotation_kwargs: dict = dict(
        xy=xy,
        xycoords=xycoords,
        ha=ha,
        va=va,
        zorder=zorder,
        color=color,
    )
    if fontsize is not None:
        annotation_kwargs["fontsize"] = fontsize
    if xytext is not None:
        annotation_kwargs["xytext"] = xytext
        annotation_kwargs["textcoords"] = textcoords or "offset points"
    if bbox_props is not None:
        annotation_kwargs["bbox"] = bbox_props
    if arrowprops is not None:
        annotation_kwargs["arrowprops"] = arrowprops
    annotation_kwargs.update(kwargs)

    return ax.annotate(text, **annotation_kwargs)


def choose_heatmap_fmt(
    cell_width_in: float,
    *,
    font_size_pt: float = 5.0,
    value_range: tuple[float, float] = (-1.0, 1.0),
    safety: float = _HEATMAP_CELL_SAFETY,
    char_width_factor: float = _HEATMAP_CHAR_WIDTH_PT,
) -> str:
    """Pick the longest fmt string that fits without overflowing the cell.

    Parameters
    ----------
    cell_width_in
        Physical width of one heatmap cell in inches.
        e.g. ``panel_width_mm / n_cols / 25.4``.
    font_size_pt
        Font size used by ``annot_kws["size"]`` (typically 4.5-6.0 pt).
    value_range
        ``(vmin, vmax)`` of the matrix values being annotated. Used to
        compute the worst-case formatted text length (sign + integer
        digits + decimal separator + fractional digits).
    safety
        Fraction of cell width allowed for text. Default 0.85 leaves
        15% inter-cell padding so neighbouring labels never visually
        merge across the cell border.
    char_width_factor
        Character width as a fraction of font size (�?.55 for sans-serif
        digits in the corpus).

    Returns
    -------
    str
        One of ``".3f"``, ``".2f"``, ``".1f"``, ``".0f"``, or ``""``.
        Empty string means "do not annotate"; the caller should switch
        to a colorbar-only display, or apply graceful degradation
        (e.g., annotate only diagonal cells / only ``|r| > 0.5``).

    Examples
    --------
    >>> choose_heatmap_fmt(0.18, font_size_pt=5.0, value_range=(-1, 1))
    '.2f'
    >>> choose_heatmap_fmt(0.10, font_size_pt=5.0, value_range=(-1, 1))
    '.1f'
    >>> choose_heatmap_fmt(0.06, font_size_pt=5.0, value_range=(-1, 1))
    ''
    """
    vmin, vmax = float(value_range[0]), float(value_range[1])
    int_digits = max(
        len(str(int(abs(vmin)))) + (1 if vmin < 0 else 0),
        len(str(int(abs(vmax)))) + (1 if vmax < 0 else 0),
        1,
    )

    char_width_in = (font_size_pt * char_width_factor) / 72.0
    available_in = cell_width_in * safety

    for decimals in (3, 2, 1, 0):
        if decimals == 0:
            text_chars = int_digits
        else:
            # int part + '.' + fractional digits
            text_chars = int_digits + 1 + decimals
        text_width_in = text_chars * char_width_in
        if text_width_in <= available_in:
            return f".{decimals}f"
    return ""


def auto_relocate_annotations(
    ax: Axes,
    *,
    text_artists: list | None = None,
    fig: Figure | None = None,
    overlap_threshold: float = 0.30,
    max_relocate: int | None = None,
) -> dict:
    """Post-placement collision avoidance for text artists on an Axes.

    **Available but NOT auto-invoked** by ``enforce_figure_legend_contract``.
    The default zero-touch retrofit (zorder>=20 + white bbox via
    ``_promote_inaxes_text_safety``) already resolves the dominant
    occlusion modes; this relocator is a heavier escape hatch generators
    can call manually when they expect heavy collision (e.g., dense
    network labels, scatterplot point annotations on top of a fitted
    curve where bbox alone is not enough).

    Algorithm (cycle-22):
      1. Force one canvas redraw to populate every artist's display bbox.
      2. For each text artist, compute its display-coord bbox once and
         cache it. Compute the same for every data artist on this Axes
         (lines, collections, patches) �?also cached, so we do not redraw
         per candidate offset.
      3. If the original overlap ratio (overlap area / text bbox area)
         exceeds ``overlap_threshold``, probe 12 candidate offsets in
         points: the 4 cardinals, 4 intercardinals, and 4 long-cardinals
         (14 pt). For each candidate the new bbox is just the cached
         original bbox shifted in display coords �?no redraw needed.
      4. Pick the offset minimising overlap, apply via ``set_position``
         in data coordinates, then redraw once at the end.

    Parameters
    ----------
    ax
        Target axes. ``ax.figure`` is used if ``fig`` is None.
    text_artists
        List of ``Text`` artists to consider. Defaults to ``ax.texts``.
    overlap_threshold
        Fraction of the text bbox area that may overlap with data
        artists before relocation triggers (default 0.30).
    max_relocate
        Optional cap on the number of relocations performed. Useful when
        annotation density is so high that every text overlaps with
        something �?set this to ``len(text_artists) // 2`` to relocate
        only the worst half.

    Returns
    -------
    dict
        ``{"checked": int, "relocated": int, "skipped": int,
           "max_overlap_before": float, "max_overlap_after": float}``
    """
    fig = fig or ax.figure
    if text_artists is None:
        text_artists = list(ax.texts)

    if not text_artists:
        return {"checked": 0, "relocated": 0, "skipped": 0,
                "max_overlap_before": 0.0, "max_overlap_after": 0.0}

    try:
        fig.canvas.draw()
    except Exception:
        return {"checked": len(text_artists), "relocated": 0,
                "skipped": len(text_artists),
                "max_overlap_before": 0.0, "max_overlap_after": 0.0,
                "error": "initial_draw_failed"}

    try:
        renderer = fig.canvas.get_renderer()
    except Exception:
        return {"checked": len(text_artists), "relocated": 0,
                "skipped": len(text_artists),
                "max_overlap_before": 0.0, "max_overlap_after": 0.0,
                "error": "no_renderer"}

    def _bbox(artist):
        try:
            b = artist.get_window_extent(renderer=renderer)
            if b is None or b.width <= 0 or b.height <= 0:
                return None
            return b
        except Exception:
            return None

    def _overlap_area(b1, b2):
        if b1 is None or b2 is None:
            return 0.0
        x0 = max(b1.x0, b2.x0); x1 = min(b1.x1, b2.x1)
        y0 = max(b1.y0, b2.y0); y1 = min(b1.y1, b2.y1)
        if x1 <= x0 or y1 <= y0:
            return 0.0
        return (x1 - x0) * (y1 - y0)

    def _bbox_area(b):
        if b is None:
            return 1.0
        return max((b.x1 - b.x0) * (b.y1 - b.y0), 1.0)

    data_artists = list(ax.lines) + list(ax.collections) + list(ax.patches)
    data_bboxes = [_bbox(a) for a in data_artists]
    data_bboxes = [b for b in data_bboxes if b is not None]

    dpi = fig.dpi
    relocated = 0
    skipped = 0
    max_overlap_before = 0.0
    max_overlap_after = 0.0

    relocation_budget = max_relocate if max_relocate is not None else len(text_artists)

    # First pass: rank text artists by overlap ratio (worst first)
    candidates = []
    for txt in text_artists:
        text_bbox = _bbox(txt)
        if text_bbox is None:
            skipped += 1
            continue
        original_overlap = sum(_overlap_area(text_bbox, db) for db in data_bboxes)
        ratio = original_overlap / _bbox_area(text_bbox)
        max_overlap_before = max(max_overlap_before, ratio)
        if ratio <= overlap_threshold:
            max_overlap_after = max(max_overlap_after, ratio)
            continue
        candidates.append((ratio, original_overlap, txt, text_bbox))

    candidates.sort(reverse=True)
    candidates = candidates[:relocation_budget]

    for ratio, original_overlap, txt, text_bbox in candidates:
        best_overlap = original_overlap
        best_offset = None

        for dx_pt, dy_pt in _RELOCATE_OFFSET_POINTS:
            shift_x = dx_pt * dpi / 72.0
            shift_y = dy_pt * dpi / 72.0
            from matplotlib.transforms import Bbox
            shifted = Bbox.from_bounds(
                text_bbox.x0 + shift_x,
                text_bbox.y0 + shift_y,
                text_bbox.width,
                text_bbox.height,
            )
            shifted_overlap = sum(_overlap_area(shifted, db) for db in data_bboxes)
            if shifted_overlap < best_overlap:
                best_overlap = shifted_overlap
                best_offset = (dx_pt, dy_pt)

        if best_offset is None:
            skipped += 1
            max_overlap_after = max(max_overlap_after,
                                    original_overlap / _bbox_area(text_bbox))
            continue

        try:
            trans = ax.transData
            trans_inv = trans.inverted()
            old_data_xy = txt.get_position()
            old_display_xy = trans.transform(old_data_xy)
            new_display_xy = (
                old_display_xy[0] + best_offset[0] * dpi / 72.0,
                old_display_xy[1] + best_offset[1] * dpi / 72.0,
            )
            new_data_xy = trans_inv.transform(new_display_xy)
            txt.set_position(tuple(new_data_xy))
            relocated += 1
            max_overlap_after = max(max_overlap_after,
                                    best_overlap / _bbox_area(text_bbox))
        except Exception:
            skipped += 1

    try:
        fig.canvas.draw()
    except Exception:
        pass

    return {
        "checked": len(text_artists),
        "relocated": relocated,
        "skipped": skipped,
        "max_overlap_before": round(max_overlap_before, 3),
        "max_overlap_after": round(max_overlap_after, 3),
    }
