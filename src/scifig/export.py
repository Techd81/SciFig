"""Figure export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union


def export_figure(fig: Any, output: Union[str, Path], *, chart: str, style: str, dpi: int = 300) -> Path:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fmt = out.suffix.lower().lstrip(".")
    if fmt == "tif":
        fmt = "tiff"
    if fmt not in {"pdf", "svg", "tiff", "png"}:
        raise ValueError("Output extension must be one of .pdf, .svg, .tiff, .tif, or .png")
    fig.savefig(out, format=fmt, dpi=dpi, facecolor="white", edgecolor="none", bbox_inches="tight")
    metadata = {
        "chart": chart,
        "style": style,
        "output": str(out),
        "dpi": dpi,
        "generator": "scifig",
    }
    (out.parent / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (out.parent / "requirements.txt").write_text(
        "\n".join([
            "scifig==0.1.3",
            "numpy>=1.24",
            "pandas>=2.0",
            "matplotlib>=3.7",
            "scipy>=1.11",
        ]) + "\n",
        encoding="utf-8",
    )
    return out
