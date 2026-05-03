"""Static binding probe for the template-mining helper contract.

Verifies that each registered generator function calls the canonical
template_mining_helpers API mandated by `specs/template-distillation-contract.md`
§ "Generator Binding Contract".

Usage (autonomous distillation cycles):
    python .claude/skills/scifig-generate/template-mining/_extraction/binding_probe.py

Exit code 0 = all bindings honored. Exit code 1 = at least one violation.
The cycle report must include `templateMiningHelperBindings` populated from
the JSON output written to stdout.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = [
    SKILL_ROOT / "phases" / "code-gen" / "generators-distribution.md",
    SKILL_ROOT / "phases" / "code-gen" / "generators-distribution.py",
    SKILL_ROOT / "phases" / "code-gen" / "generators-clinical.md",
    SKILL_ROOT / "phases" / "code-gen" / "generators-psychology.md",
]
SMOKE_SOURCE_FILES = SOURCE_FILES + [
    SKILL_ROOT / "phases" / "03-code-gen-style.md",
    SKILL_ROOT / "phases" / "04-export-report.md",
    SKILL_ROOT / "phases" / "code-gen" / "helpers.py",
    SKILL_ROOT / "phases" / "code-gen" / "template_mining_helpers.py",
    SKILL_ROOT / "templates" / "finalizer-safe-template-contract.md",
    SKILL_ROOT / "templates" / "layout-recipes-ready.json",
    SKILL_ROOT / "templates" / "zorder-recipes-ready.json",
]

# Generator → required template_mining_helpers API calls.
# Grouped by chart family; each generator must contain the named helper(s)
# anywhere in its body (canonical call OR guarded fallback both qualify).
BINDINGS = {
    # ── POLAR / RADAR FAMILY ──
    # add_polygon_polar_grid replaces the default circular polar grid with the
    # corpus-anchored polygon dashed grid (Nature Vol 626 Fig 3c discipline).
    "gen_radar":              ["add_polygon_polar_grid"],
    "gen_biodiversity_radar": ["add_polygon_polar_grid"],

    # ── FOREST / CI FAMILY ──
    # add_forest_panel encodes one-call forest discipline: dashed reference
    # line + asymmetric CI whiskers + per-row HR(CI) annotation column.
    "gen_forest":             ["add_forest_panel"],
    "gen_caterpillar_plot":   ["add_forest_panel"],
    "gen_risk_ratio_plot":    ["add_forest_panel"],
    "gen_ci_plot":            ["add_forest_panel"],

    # ── CORRELATION HEATMAP FAMILY ──
    # TwoSlopeNorm + RdBu_r enforce the corpus-anchored diverging palette
    # centered at 0 (red_blue_correlation discipline) for symmetric matrices.
    "gen_heatmap_triangular": ["TwoSlopeNorm", "RdBu_r"],
    "gen_correlation":        ["TwoSlopeNorm", "RdBu_r"],
    "gen_heatmap_symmetric":  ["TwoSlopeNorm", "RdBu_r"],

    # ── PERFECT-FIT DIAGONAL FAMILY (y = x reference) ──
    # add_perfect_fit_diagonal owns the dashed y=x line for predicted-vs-actual
    # / probability-probability / quantile-quantile / ROC chance-line panels.
    "gen_calibration":        ["add_perfect_fit_diagonal"],
    "gen_pp_plot":            ["add_perfect_fit_diagonal"],
    "gen_qq":                 ["add_perfect_fit_diagonal"],
    "gen_roc":                ["add_perfect_fit_diagonal"],

    # ── ZERO REFERENCE FAMILY ──
    # add_zero_reference owns the dashed/solid y=0 (or x=0) anchor line for
    # residual / fold-change / waterfall / diverging / SHAP-divider panels.
    "gen_residual_vs_fitted": ["add_zero_reference", "apply_scatter_regression_floor"],
    "gen_ma_plot":            ["add_zero_reference"],
    "gen_waterfall":          ["add_zero_reference"],
    "gen_diverging_bar":      ["add_zero_reference"],
    "gen_likert_divergent":   ["add_zero_reference"],
    "gen_decision_curve":     ["add_zero_reference"],
    "gen_lollipop_horizontal": ["add_zero_reference"],
    "gen_dotplot":            ["add_zero_reference"],

    # ── SCATTER REGRESSION FLOOR FAMILY ──
    # apply_scatter_regression_floor owns the L0 floor: light dashed grid +
    # despine, applied BEFORE drawing scatter so the grid sits at zorder=0.
    "gen_scatter_regression": ["apply_scatter_regression_floor", "add_zero_reference"],
    "gen_dose_response":      ["apply_scatter_regression_floor"],
    "gen_scale_location":     ["apply_scatter_regression_floor"],
}


HIGH_FREQUENCY_FAMILIES = [
    "scatter_regression",
    "ale_pdp",
    "shap_composite",
    "dual_axis",
    "heatmap",
    "multipanel_grid",
    "single_focus",
    "global_local",
    "n_by_n_pairwise",
    "marginal_joint",
]

FAMILY_CHECK_PATTERNS = {
    "legend_compliance": r"enforce_figure_legend_contract|legend_contract_report|source-lint.py",
    "zorder_declared": r"apply_zorder_recipe|zorder-recipes-ready.json|family_overrides",
    "colorbar_slot_reserved": r"colorbar|colorbarPanelOverlapCount|reserved_slots",
    "inset_audit_inclusion": r"normalize_axes_map|audited_axes_count|inset",
    "text_safe_bbox": r"_promote_inaxes_text_safety|textTextOverlapCount|bboxDataCoverageOverflowCount",
}

FAMILY_SMOKE_MATRIX_IDS = [
    "scatter_regression.legend_compliance",
    "scatter_regression.zorder_declared",
    "scatter_regression.colorbar_slot_reserved",
    "scatter_regression.inset_audit_inclusion",
    "scatter_regression.text_safe_bbox",
    "ale_pdp.legend_compliance",
    "ale_pdp.zorder_declared",
    "ale_pdp.colorbar_slot_reserved",
    "ale_pdp.inset_audit_inclusion",
    "ale_pdp.text_safe_bbox",
    "shap_composite.legend_compliance",
    "shap_composite.zorder_declared",
    "shap_composite.colorbar_slot_reserved",
    "shap_composite.inset_audit_inclusion",
    "shap_composite.text_safe_bbox",
    "dual_axis.legend_compliance",
    "dual_axis.zorder_declared",
    "dual_axis.colorbar_slot_reserved",
    "dual_axis.inset_audit_inclusion",
    "dual_axis.text_safe_bbox",
    "heatmap.legend_compliance",
    "heatmap.zorder_declared",
    "heatmap.colorbar_slot_reserved",
    "heatmap.inset_audit_inclusion",
    "heatmap.text_safe_bbox",
    "multipanel_grid.legend_compliance",
    "multipanel_grid.zorder_declared",
    "multipanel_grid.colorbar_slot_reserved",
    "multipanel_grid.inset_audit_inclusion",
    "multipanel_grid.text_safe_bbox",
    "single_focus.legend_compliance",
    "single_focus.zorder_declared",
    "single_focus.colorbar_slot_reserved",
    "single_focus.inset_audit_inclusion",
    "single_focus.text_safe_bbox",
    "global_local.legend_compliance",
    "global_local.zorder_declared",
    "global_local.colorbar_slot_reserved",
    "global_local.inset_audit_inclusion",
    "global_local.text_safe_bbox",
    "n_by_n_pairwise.legend_compliance",
    "n_by_n_pairwise.zorder_declared",
    "n_by_n_pairwise.colorbar_slot_reserved",
    "n_by_n_pairwise.inset_audit_inclusion",
    "n_by_n_pairwise.text_safe_bbox",
    "marginal_joint.legend_compliance",
    "marginal_joint.zorder_declared",
    "marginal_joint.colorbar_slot_reserved",
    "marginal_joint.inset_audit_inclusion",
    "marginal_joint.text_safe_bbox",
]

FAMILY_SMOKE_BINDINGS = [
    {
        "id": matrix_id,
        "family": matrix_id.split(".", 1)[0],
        "check": matrix_id.split(".", 1)[1],
        "pattern": FAMILY_CHECK_PATTERNS[matrix_id.split(".", 1)[1]],
    }
    for matrix_id in FAMILY_SMOKE_MATRIX_IDS
]


def main() -> int:
    text_blocks = []
    for path in SOURCE_FILES:
        if path.exists():
            text_blocks.append(path.read_text(encoding="utf-8"))
    text = "\n".join(text_blocks)
    smoke_text_blocks = []
    smoke_file_map: dict[str, str] = {}
    for path in SMOKE_SOURCE_FILES:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            smoke_text_blocks.append(content)
            smoke_file_map[path.name] = content
    smoke_text = "\n".join(smoke_text_blocks)

    fn_pattern_template = r"^def {name}\([\s\S]*?(?=^def [A-Za-z_]\w*\s*\(|\Z)"
    results = {}
    family_smoke_results = {}
    violations = []

    for fn_name, required_calls in BINDINGS.items():
        m = re.search(fn_pattern_template.format(name=re.escape(fn_name)),
                      text, flags=re.M)
        if not m:
            results[fn_name] = {"present": False, "missing_calls": list(required_calls)}
            violations.append(f"missing_generator:{fn_name}")
            continue
        body = m.group(0)
        missing = [r for r in required_calls if r not in body]
        results[fn_name] = {
            "present": True,
            "required_calls": list(required_calls),
            "missing_calls": missing,
        }
        for missing_call in missing:
            violations.append(f"unbound:{fn_name}:{missing_call}")

    # Coverage assertion — every chart family must have at least one binding
    families_covered = {
        "polar":               any(k in BINDINGS for k in ("gen_radar", "gen_biodiversity_radar")),
        "forest":              any(k in BINDINGS for k in ("gen_forest", "gen_caterpillar_plot", "gen_risk_ratio_plot", "gen_ci_plot")),
        "correlation_heatmap": any(k in BINDINGS for k in ("gen_heatmap_triangular", "gen_correlation", "gen_heatmap_symmetric")),
        "perfect_fit":         any(k in BINDINGS for k in ("gen_calibration", "gen_pp_plot", "gen_qq", "gen_roc")),
        "zero_reference":      any(k in BINDINGS for k in ("gen_residual_vs_fitted", "gen_ma_plot", "gen_waterfall", "gen_diverging_bar", "gen_likert_divergent", "gen_decision_curve", "gen_lollipop_horizontal", "gen_dotplot")),
        "scatter_floor":       any(k in BINDINGS for k in ("gen_scatter_regression", "gen_dose_response", "gen_scale_location")),
    }
    for family, covered in families_covered.items():
        if not covered:
            violations.append(f"family_uncovered:{family}")

    for item in FAMILY_SMOKE_BINDINGS:
        # Search globally but record which file(s) contain the match
        matching_files = []
        for fname, fcontent in smoke_file_map.items():
            if re.search(item["pattern"], fcontent, flags=re.M):
                matching_files.append(fname)
        matched = len(matching_files) > 0
        family_smoke_results[item["id"]] = {
            "family": item["family"],
            "check": item["check"],
            "pattern": item["pattern"],
            "present": matched,
            "found_in": matching_files,
        }
        if not matched:
            violations.append(f"family_smoke_missing:{item['id']}")

    total_bindings = len(BINDINGS) + len(FAMILY_SMOKE_BINDINGS)
    report = {
        "binding_results": results,
        "family_smoke_results": family_smoke_results,
        "families_covered": families_covered,
        "total_bindings": total_bindings,
        "violations": violations,
        "passed": len(violations) == 0,
        "skill_root": str(SKILL_ROOT),
    }
    print(f"Binding count: {total_bindings}")
    print(f"Pass: {total_bindings - len(violations)}/{total_bindings}")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
