"""Public API for the scifig package."""

from ._version import __version__
from .api import plot
from .figure import Figure
from .registry import CHART_GENERATORS, get_chart_info, list_charts, register_chart
from . import styles

__all__ = [
    "CHART_GENERATORS",
    "Figure",
    "__version__",
    "get_chart_info",
    "list_charts",
    "plot",
    "register_chart",
    "styles",
]
