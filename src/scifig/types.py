"""Typed contracts for the scifig package."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, TypedDict, Union


class JournalProfile(TypedDict):
    name: str
    single_width_mm: float
    double_width_mm: float
    max_height_mm: float
    body_pt: float
    panel_label_pt: float
    axis_lw_pt: float
    tick_w_pt: float
    panel_gap_rel: float
    font_family: str
    grid: bool
    legend_frame: bool


@dataclass(frozen=True)
class DataProfile:
    format: str
    structure: str
    columns: List[str]
    semantic_roles: Dict[str, str]
    n_groups: int
    n_observations: int
    domain_hints: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def as_skill_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "structure": self.structure,
            "columns": self.columns,
            "columnNames": self.columns,
            "semanticRoles": self.semantic_roles,
            "nGroups": self.n_groups,
            "nObservations": self.n_observations,
            "domainHints": self.domain_hints,
            "riskFlags": self.risk_flags,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class ChartPlan:
    primary_chart: str
    secondary_charts: List[str] = field(default_factory=list)
    stat_method: str = "auto"
    panel_blueprint: Dict[str, Any] = field(default_factory=dict)
    palette_plan: Dict[str, Any] = field(default_factory=dict)

    def as_skill_dict(self) -> Dict[str, Any]:
        return {
            "primaryChart": self.primary_chart,
            "secondaryCharts": self.secondary_charts,
            "statMethod": self.stat_method,
            "panelBlueprint": self.panel_blueprint,
            "palettePlan": self.palette_plan,
        }


@dataclass(frozen=True)
class OutputBundle:
    figure: Any
    output_path: Optional[Path]
    metadata_path: Optional[Path]
    requirements_path: Optional[Path]


PanelPosition = Tuple[int, int]
DataInput = Union[str, Path, Any]
RoleMap = Mapping[str, str]
PaletteInput = Optional[Union[str, List[str]]]
