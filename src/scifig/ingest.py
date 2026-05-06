"""Data loading and semantic-role inference."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .types import DataInput, DataProfile


ROLE_ALIASES: Dict[str, Tuple[str, ...]] = {
    "group": ("group", "condition", "class", "category", "species", "cohort", "arm", "treatment"),
    "value": ("value", "measurement", "expression", "intensity", "abundance", "score", "response"),
    "x": ("x", "x_value", "feature_x", "pc1", "umap1", "tsne1", "radius", "dose"),
    "y": ("y", "y_value", "feature_y", "pc2", "umap2", "tsne2", "mass", "response"),
    "time": ("time", "date", "day", "year", "month", "timestamp", "survival_time"),
    "identifier": ("id", "sample", "sample_id", "subject", "patient", "gene", "feature"),
    "survival_time": ("survival_time", "time_to_event", "os_time", "pfs_time"),
    "survival_event": ("event", "status", "death", "censored"),
    "dose": ("dose", "concentration", "log_dose", "drug_dose"),
    "response": ("response", "viability", "effect", "inhibition"),
    "fold_change": ("log2fc", "log2_fold_change", "fold_change", "logfc"),
    "p_value": ("p", "pvalue", "p_value", "padj", "qvalue", "fdr"),
    "estimate": ("estimate", "effect", "hazard_ratio", "odds_ratio", "risk_ratio"),
    "ci_low": ("ci_low", "lower", "lower_ci", "lcl"),
    "ci_high": ("ci_high", "upper", "upper_ci", "ucl"),
    "label": ("label", "name", "term", "pathway", "feature_name"),
    "score": ("score", "probability", "prediction", "predicted", "risk"),
    "actual": ("actual", "observed", "truth", "label_true"),
    "predicted": ("predicted", "prediction", "fitted", "estimate_y"),
    "residual": ("residual", "error", "delta"),
    "chromosome": ("chromosome", "chr"),
    "position": ("position", "pos", "bp"),
    "start": ("start", "begin"),
    "end": ("end", "stop"),
    "source": ("source", "from"),
    "target": ("target", "to"),
    "weight": ("weight", "count", "flow"),
    "feature_id": ("feature_id", "feature", "variable"),
    "importance": ("importance", "gain", "shap", "shap_value"),
    "metric": ("metric", "measure"),
    "model": ("model", "algorithm"),
    "epoch": ("epoch", "step", "iteration"),
    "loss": ("loss", "train_loss"),
    "accuracy": ("accuracy", "auc", "r2"),
    "category": ("category", "type", "kind"),
    "frequency": ("frequency", "freq", "n"),
    "proportion": ("proportion", "fraction", "percent"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon", "lng"),
    "component": ("component", "module", "layer"),
    "rank": ("rank", "order"),
    "low": ("low", "min"),
    "high": ("high", "max"),
}


def load_data(data: DataInput) -> tuple[pd.DataFrame, str]:
    if isinstance(data, pd.DataFrame):
        return data.copy(), "dataframe"
    path = Path(data)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}. Provide a readable CSV, TSV, XLSX, or XLS file.")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path), "csv"
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t"), "tsv"
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path), "excel"
    raise ValueError(f"Unsupported data format '{suffix}'. Use CSV, TSV, XLSX, or XLS.")


def infer_structure(df: pd.DataFrame) -> str:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == len(df.columns) and len(df.columns) >= 3:
        return "matrix"
    if len(numeric_cols) >= 3 and len(df.columns) <= len(numeric_cols) + 2:
        return "wide"
    return "tidy"


def map_semantic_roles(df: pd.DataFrame) -> Dict[str, str]:
    lowered = {str(col).lower().replace(" ", "_").replace("-", "_"): str(col) for col in df.columns}
    roles: Dict[str, str] = {}
    for role, aliases in ROLE_ALIASES.items():
        for alias in aliases:
            if alias in lowered:
                roles[role] = lowered[alias]
                break
    numeric = [str(col) for col in df.select_dtypes(include=[np.number]).columns]
    categorical = [str(col) for col in df.columns if str(col) not in numeric]
    if "x" not in roles and len(numeric) >= 2:
        roles["x"] = numeric[0]
    if "y" not in roles and len(numeric) >= 2:
        roles["y"] = numeric[1]
    if "value" not in roles and numeric:
        # Pick a numeric column not already bound to x/y/time to avoid role overlap.
        used = {roles.get(r) for r in ("x", "y", "time")}
        available = [col for col in numeric if col not in used]
        if available:
            roles["value"] = available[-1]
        elif "y" not in roles:
            roles["value"] = numeric[-1]
    if "group" not in roles and categorical:
        roles["group"] = categorical[0]
    return roles


def infer_domain_hints(df: pd.DataFrame, roles: Dict[str, str]) -> list[str]:
    cols = " ".join(str(c).lower() for c in df.columns)
    hints: list[str] = []
    if {"fold_change", "p_value"} <= roles.keys() or any(token in cols for token in ("gene", "padj", "log2fc")):
        hints.append("genomics_transcriptomics")
    if {"survival_time", "survival_event"} <= roles.keys():
        hints.append("clinical_survival")
    if any(token in cols for token in ("model", "auc", "rmse", "shap")):
        hints.append("computer_ai_ml")
    if not hints:
        hints.append("general_science")
    return hints


def profile_data(data: DataInput) -> tuple[pd.DataFrame, DataProfile]:
    df, fmt = load_data(data)
    roles = map_semantic_roles(df)
    group_col = roles.get("group")
    n_groups = int(df[group_col].nunique()) if group_col in df.columns else 0
    warnings: list[str] = []
    if df.empty:
        warnings.append("input_data_empty")
    missing_rate = float(df.isna().mean().mean()) if len(df.columns) else 0.0
    risk_flags = ["high_missingness"] if missing_rate > 0.25 else []
    profile = DataProfile(
        format=fmt,
        structure=infer_structure(df),
        columns=[str(c) for c in df.columns],
        semantic_roles=roles,
        n_groups=n_groups,
        n_observations=int(len(df)),
        domain_hints=infer_domain_hints(df, roles),
        risk_flags=risk_flags,
        warnings=warnings,
    )
    return df, profile
