"""Data loading and semantic-role inference."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .types import DataInput, DataProfile


ROLE_ALIASES: Dict[str, Tuple[str, ...]] = {
    "group": ("group", "condition", "class", "category", "species", "cohort", "arm", "treatment"),
    "value": ("value", "measurement", "expression", "intensity", "abundance", "score", "response"),
    "x": ("x", "x_value", "feature_x", "pc1", "umap1", "tsne1", "radius", "dose"),
    "y": ("y", "y_value", "feature_y", "pc2", "umap2", "tsne2", "mass", "response"),
    "time": ("time", "time_months", "date", "day", "year", "month", "timestamp", "survival_time"),
    "identifier": ("id", "sample", "sample_id", "subject", "patient", "gene", "feature"),
    "survival_time": ("survival_time", "time_to_event", "time_months", "os_time", "pfs_time", "os_months", "pfs_months"),
    "survival_event": ("event", "status", "death", "censored", "event_observed", "event_status"),
    "dose": ("dose", "dose_um", "dose_nm", "dose_mg", "concentration", "concentration_um", "concentration_nm", "log_dose", "drug_dose"),
    "response": ("response", "viability", "effect", "inhibition", "readout", "outcome"),
    "fold_change": ("log2fc", "log2_fold_change", "fold_change", "logfc"),
    "p_value": ("p", "pvalue", "p_value", "padj", "qvalue", "fdr"),
    "estimate": ("estimate", "effect", "hazard_ratio", "odds_ratio", "risk_ratio"),
    "ci_low": ("ci_low", "ci_lo", "lower", "lower_ci", "lower_ci_95", "lcl"),
    "ci_high": ("ci_high", "ci_hi", "upper", "upper_ci", "upper_ci_95", "ucl"),
    "label": ("label", "name", "term", "pathway", "feature_name"),
    "score": (
        "score", "probability", "prob", "proba", "y_score", "prediction_score",
        "pred_score", "prediction", "predicted", "risk",
    ),
    "actual": ("actual", "observed", "truth", "label_true", "y_true", "true_label", "target"),
    "predicted": ("predicted", "prediction", "fitted", "estimate_y"),
    "residual": ("residual", "error", "delta"),
    "before": ("before", "pre", "baseline", "value_pre", "pre_value", "control"),
    "after": ("after", "post", "followup", "follow_up", "value_post", "post_value", "treatment"),
    "pair_id": ("pair_id", "subject_id", "patient_id", "sample_id", "subject", "id"),
    "chromosome": ("chromosome", "chr"),
    "position": ("position", "pos", "bp"),
    "start": ("start", "begin", "start_time", "onset"),
    "end": ("end", "stop", "finish", "end_time", "duration"),
    "gene": ("gene", "gene_id", "symbol"),
    "sample": ("sample", "sample_id", "subject", "patient"),
    "alteration": ("alteration", "mutation", "variant", "event"),
    "coverage": ("coverage", "depth", "read_depth"),
    "feature_type": ("feature_type", "feature_class", "element_type"),
    "strand": ("strand",),
    "gene_count": ("gene_count", "gene_n", "n_genes"),
    "enrichment_score": ("enrichment_score", "enrichment", "nes"),
    "source": ("source", "from"),
    "target": ("target", "to"),
    "weight": ("weight", "count", "flow"),
    "row": ("row", "row_id", "row_label"),
    "column": ("column", "col", "column_id", "column_label"),
    "feature_id": ("feature_id", "feature", "variable"),
    "importance": ("importance", "gain", "shap", "shap_value", "mean_abs_shap", "permutation", "permutation_importance"),
    "metric": ("metric", "measure"),
    "model": ("model", "algorithm"),
    "epoch": ("epoch", "step", "iteration"),
    "loss": ("loss", "train_loss"),
    "accuracy": ("accuracy", "auc", "r2"),
    "category": ("category", "type", "kind", "site", "segment"),
    "parent": ("parent", "level1", "level_1", "outer_category"),
    "child": ("child", "level2", "level_2", "inner_category", "subgroup", "subcategory"),
    "frequency": ("frequency", "freq", "n"),
    "proportion": ("proportion", "fraction", "percent"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon", "lng"),
    "component": ("component", "module", "layer"),
    "layer": ("layer", "module", "component", "node"),
    "rank": ("rank", "order"),
    "order": ("order", "step", "depth"),
    "mediator": ("mediator", "mediation", "middle"),
    "spatial_x": ("spatial_x", "spot_x", "pixel_x"),
    "spatial_y": ("spatial_y", "spot_y", "pixel_y"),
    "low": ("low", "min"),
    "high": ("high", "max"),
    "base": ("base", "baseline", "reference"),
    "size": ("size", "bubble_size", "magnitude"),
    "std_error": ("se", "stderr", "std_error", "standard_error"),
    "leverage": ("leverage", "hat_value", "hat"),
    "cook_distance": ("cook_distance", "cooks_distance", "cooks_d", "cook_d"),
    "strain": ("strain", "epsilon", "extension"),
    "stress": ("stress", "sigma", "load"),
    "temperature": ("temperature", "temp"),
    "heat_flow": ("heat_flow", "heatflow", "dsc"),
    "two_theta": ("two_theta", "2theta", "theta", "angle"),
    "intensity": ("intensity", "counts", "absorbance", "transmittance"),
    "wavenumber": ("wavenumber", "wave_number"),
    "z_real": ("z_real", "zprime", "real", "re_z"),
    "z_imag": ("z_imag", "zimag", "imag", "im_z"),
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
    # v0.1.7 fix: coerce non-string column names (e.g. integer indices when a
    # CSV is loaded with header=None or a user passes a numeric-keyed dict)
    # to strings up front so semantic-role lookups in downstream generators
    # never miss because of dtype mismatch.
    if any(not isinstance(c, str) for c in df.columns):
        df.columns = [str(c) for c in df.columns]
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
