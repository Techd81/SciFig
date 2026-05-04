"""Revalidate a hand-edited SciFig SVG and rebuild derived outputs.

Example:
    python scripts/scifig_revalidate_edited_svg.py output/figure1.edited.svg --output-dir output --figure-id figure1 --formats svg,png,pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")


ROOT = Path(__file__).resolve().parents[1]
HELPERS_PATH = ROOT / ".claude" / "skills" / "scifig-generate" / "phases" / "code-gen" / "helpers.py"


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```python"):
        text = text[len("```python"):].lstrip("\r\n")
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text


def _load_helpers() -> dict:
    namespace: dict = {}
    exec(_strip_code_fence(HELPERS_PATH.read_text(encoding="utf-8")), namespace)
    return namespace


def _parse_formats(value: str) -> list[str]:
    return [item.strip().lstrip(".").lower() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edited_svg", type=Path, help="Path to the SVG after manual editing.")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="SciFig output directory.")
    parser.add_argument("--figure-id", default="figure1", help="Figure stem, for example figure1.")
    parser.add_argument("--dpi", type=int, default=300, help="Raster DPI for PNG/TIFF derivatives.")
    parser.add_argument("--formats", default="svg,png,pdf", help="Comma-separated outputs to regenerate.")
    parser.add_argument("--no-strict", action="store_true", help="Write QA even if SVG conversion fails.")
    args = parser.parse_args()

    helpers = _load_helpers()
    result = helpers["revalidate_edited_svg_bundle"](
        args.edited_svg,
        figure_id=args.figure_id,
        output_dir=args.output_dir,
        raster_dpi=args.dpi,
        normalized_formats=_parse_formats(args.formats),
        strict=not args.no_strict,
    )
    qa = result["svgRenderQa"]
    print(f"svgRenderQa: {args.output_dir / 'reports' / 'svg_render_qa.json'}")
    print(f"hardFail: {qa.get('hardFail')}")
    if qa.get("failures"):
        print("failures: " + ", ".join(qa["failures"]))
    return 1 if qa.get("hardFail") else 0


if __name__ == "__main__":
    raise SystemExit(main())
