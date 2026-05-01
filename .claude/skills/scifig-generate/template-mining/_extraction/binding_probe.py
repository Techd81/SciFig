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

BINDINGS = {
    "gen_radar": ["add_polygon_polar_grid"],
    "gen_biodiversity_radar": ["add_polygon_polar_grid"],
    "gen_forest": ["add_forest_panel"],
    "gen_heatmap_triangular": ["TwoSlopeNorm", "RdBu_r"],
    "gen_scatter_regression": ["apply_scatter_regression_floor"],
}


def main() -> int:
    text_blocks = []
    for path in SOURCE_FILES:
        if path.exists():
            text_blocks.append(path.read_text(encoding="utf-8"))
    text = "\n".join(text_blocks)

    fn_pattern_template = r"^def {name}\([\s\S]*?(?=^def [A-Za-z_]\w*\s*\(|\Z)"
    results = {}
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

    report = {
        "binding_results": results,
        "violations": violations,
        "passed": len(violations) == 0,
        "skill_root": str(SKILL_ROOT),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
