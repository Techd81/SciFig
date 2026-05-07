"""Public API for the scifig package."""

from ._version import __version__
from .api import plot
from .figure import Figure
from .registry import CHART_GENERATORS, get_chart_info, list_charts, register_chart
from . import polish, styles

# Differentiated generator modules — import to trigger @register_chart decorators.
# Each module overrides its chart keys in CHART_GENERATORS, replacing the
# generic_chart fallback registered by charts.py.
from . import generators_distribution as _generators_distribution  # noqa: F401
from . import generators_time_series as _generators_time_series  # noqa: F401
from . import generators_matrix as _generators_matrix  # noqa: F401
from . import generators_scatter as _generators_scatter  # noqa: F401
from . import generators_clinical as _generators_clinical  # noqa: F401
from . import generators_genomics as _generators_genomics  # noqa: F401
from . import generators_ml as _generators_ml  # noqa: F401

__all__ = [
    "CHART_GENERATORS",
    "Figure",
    "__version__",
    "get_chart_info",
    "list_charts",
    "plot",
    "polish",
    "register_chart",
    "styles",
]
