"""Synthetic-but-realistic data fixtures for the v0.1.7 30-case validation suite.

Each domain ships one CSV that resembles the shape, units, and edge cases of
the real-world data scientists upload to ``scifig`` so the integration tests
catch issues that pure unit tests miss (extreme range, missing values,
multi-class group columns, etc.).

Domains: genomics, clinical, ml, distribution, time_series, composition.

Run this module to (re)generate the fixture CSVs::

    python -m tests.fixtures.generate_fixtures
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

FIXTURE_DIR = Path(__file__).resolve().parent
SEED = 20260507


# -- Genomics: differential expression (volcano / MA plot) ---------------------

def make_genomics_de() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n = 320
    log2fc = np.concatenate([
        rng.normal(0, 0.5, n - 30),
        rng.normal(2.5, 0.4, 15),
        rng.normal(-2.5, 0.4, 15),
    ])
    base_p = rng.uniform(0.001, 1.0, n)
    base_p[log2fc.argsort()[:15]] = rng.uniform(1e-8, 1e-3, 15)
    base_p[log2fc.argsort()[-15:]] = rng.uniform(1e-8, 1e-3, 15)
    nlogp = -np.log10(np.clip(base_p, 1e-12, 1.0))
    significance = np.where(np.abs(log2fc) > 1.5, np.where(log2fc > 0, "up", "down"), "ns")
    base_mean = np.exp(rng.normal(5.5, 1.5, n))
    return pd.DataFrame({
        "gene": [f"GENE_{i:04d}" for i in range(n)],
        "log2fc": log2fc,
        "padj": base_p,
        "nlogp": nlogp,
        "category": significance,
        "baseMean": base_mean,
    })


def make_clinical_survival() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 1)
    n_per = 80
    arms = ["Control", "Treatment_A", "Treatment_B"]
    rows = []
    for arm_idx, arm in enumerate(arms):
        rate = 0.06 - 0.018 * arm_idx
        for _ in range(n_per):
            time = rng.exponential(1 / rate)
            event = int(rng.random() < (1 - np.exp(-rate * 36)))
            time = float(np.clip(time, 0.5, 60))
            age = float(rng.normal(60 + arm_idx * 1.5, 10))
            sex = str(rng.choice(["F", "M"]))
            rows.append({"arm": arm, "time_months": time, "event": event, "age": age, "sex": sex})
    return pd.DataFrame(rows)


def make_ml_metrics() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 2)
    rows = []
    for model_idx, model in enumerate(["LogReg", "RandomForest", "XGBoost", "MLP"]):
        skill = 0.7 + 0.05 * model_idx
        for fold in range(5):
            for _ in range(50):
                y_true = int(rng.random() < 0.4)
                noise = rng.normal(0, 0.15)
                y_score = float(np.clip(skill * y_true + (1 - skill) * 0.5 + noise, 0.01, 0.99))
                rows.append({
                    "model": model,
                    "fold": fold,
                    "y_true": y_true,
                    "y_score": y_score,
                })
    return pd.DataFrame(rows)


def make_distribution_groups() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 3)
    rows = []
    for group, mu, sd in [("WT", 5.0, 1.2), ("HET", 5.5, 1.4), ("KO", 7.5, 1.8), ("Rescue", 5.8, 1.3)]:
        for _ in range(60):
            value = float(rng.normal(mu, sd))
            timepoint = str(rng.choice(["0h", "6h", "24h"], p=[0.4, 0.35, 0.25]))
            rows.append({"group": group, "value": value, "timepoint": timepoint})
    return pd.DataFrame(rows)


def make_time_series() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 4)
    rows = []
    for subject in range(20):
        baseline = float(rng.normal(100, 10))
        slope = float(rng.normal(-1.2, 0.6))
        cohort = "Treatment" if subject % 2 == 0 else "Control"
        if cohort == "Treatment":
            slope += 0.6
        for week in range(0, 13):
            value = baseline + slope * week + float(rng.normal(0, 2.5))
            rows.append({"subject": subject, "cohort": cohort, "week": week, "value": value})
    return pd.DataFrame(rows)


def make_composition() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 5)
    sites = [f"Site_{i:02d}" for i in range(8)]
    species = ["Acer", "Quercus", "Pinus", "Betula", "Fagus", "Other"]
    rows = []
    for site in sites:
        weights = rng.dirichlet(np.array([1.5, 2.0, 1.0, 0.8, 1.2, 0.5]))
        total = int(rng.integers(150, 400))
        counts = rng.multinomial(total, weights)
        richness = int(np.count_nonzero(counts))
        for sp, count in zip(species, counts):
            rows.append({"site": site, "species": sp, "count": int(count), "richness": richness})
    return pd.DataFrame(rows)


DOMAINS: dict[str, Callable[[], pd.DataFrame]] = {
    "genomics_de": make_genomics_de,
    "clinical_survival": make_clinical_survival,
    "ml_metrics": make_ml_metrics,
    "distribution_groups": make_distribution_groups,
    "time_series": make_time_series,
    "composition": make_composition,
}


def write_all(target_dir: Path = FIXTURE_DIR) -> dict[str, Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for name, factory in DOMAINS.items():
        df = factory()
        path = target_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        out[name] = path
    return out


def load_fixture(name: str) -> pd.DataFrame:
    path = FIXTURE_DIR / f"{name}.csv"
    if not path.is_file():
        write_all(FIXTURE_DIR)
    return pd.read_csv(path)


if __name__ == "__main__":
    paths = write_all(FIXTURE_DIR)
    for name, p in paths.items():
        print(f"{name:>22s}: {p}")
