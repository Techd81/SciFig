"""Color palette resolution."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

WONG = ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]
VIRIDIS = ["#440154", "#31688E", "#35B779", "#FDE725"]
RDBU = ["#2166AC", "#F7F7F7", "#B2182B"]


def resolve_palette(palette: Optional[Union[str, Sequence[str]]] = None) -> Dict[str, Any]:
    if palette is None or palette in ("colorblind", "wong"):
        colors = WONG
    elif palette == "okabe-ito":
        colors = OKABE_ITO
    elif palette in ("viridis", "sequential"):
        colors = VIRIDIS
    elif palette in ("rdbu", "diverging"):
        colors = RDBU
    elif isinstance(palette, (list, tuple)):
        colors = list(palette)
    else:
        raise ValueError("Unknown palette. Use colorblind, wong, okabe-ito, viridis, rdbu, or a list of hex colors.")
    return {"categorical": list(colors), "categoryMap": {}, "sequential": VIRIDIS, "diverging": RDBU}
