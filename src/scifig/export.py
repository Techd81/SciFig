"""Figure export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union

from ._version import __version__


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
        "scifig_version": __version__,
    }
    (out.parent / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    # BUG-CR-001 fix: pin scifig to actual installed version (was hardcoded 0.1.3 → 4 versions stale on v0.2.0)
    # BUG-CR-002 fix: include lifelines/seaborn/openpyxl so KM/forest/Excel-input figures are reproducible from bundle
    (out.parent / "requirements.txt").write_text(
        "\n".join([
            f"scifig=={__version__}",
            "numpy>=1.24",
            "pandas>=2.0",
            "matplotlib>=3.7",
            "scipy>=1.11",
            "seaborn>=0.13",
            "lifelines>=0.27",
            "openpyxl>=3.1",
        ]) + "\n",
        encoding="utf-8",
    )
    return out
