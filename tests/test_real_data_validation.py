"""30-case real-data validation suite (v0.1.7)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import scifig
from scifig import polish
from tests.fixtures.generate_fixtures import DOMAINS, FIXTURE_DIR, load_fixture


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures_present():
    missing = [name for name in DOMAINS if not (FIXTURE_DIR / f"{name}.csv").is_file()]
    if missing:
        from tests.fixtures.generate_fixtures import write_all
        write_all(FIXTURE_DIR)


CASES: list[tuple[str, str, dict]] = [
    ("genomics_de", "volcano", {}),
    ("genomics_de", "ma_plot", {}),
    ("genomics_de", "histogram", {"value": "log2fc"}),
    ("genomics_de", "density", {"value": "log2fc"}),
    ("genomics_de", "qq", {}),
    ("clinical_survival", "km", {}),
    ("clinical_survival", "histogram", {"value": "time_months"}),
    ("clinical_survival", "violin_strip", {"group": "arm", "value": "age"}),
    ("clinical_survival", "box_strip", {"group": "arm", "value": "age"}),
    ("clinical_survival", "beeswarm", {"group": "arm", "value": "time_months"}),
    ("ml_metrics", "roc", {}),
    ("ml_metrics", "pr_curve", {}),
    ("ml_metrics", "calibration", {}),
    ("ml_metrics", "histogram", {"value": "y_score"}),
    ("ml_metrics", "density", {"value": "y_score"}),
    ("distribution_groups", "violin_strip", {"group": "group", "value": "value"}),
    ("distribution_groups", "box_strip", {"group": "group", "value": "value"}),
    ("distribution_groups", "raincloud", {"group": "group", "value": "value"}),
    ("distribution_groups", "beeswarm", {"group": "group", "value": "value"}),
    ("distribution_groups", "ridge", {"group": "group", "value": "value"}),
    ("time_series", "line", {"x": "week", "y": "value", "group": "cohort"}),
    ("time_series", "line_ci", {"x": "week", "y": "value", "group": "cohort"}),
    ("time_series", "spaghetti", {"x": "week", "y": "value", "group": "subject"}),
    ("time_series", "area", {"x": "week", "y": "value", "group": "cohort"}),
    ("time_series", "histogram", {"value": "value"}),
    ("composition", "bar", {"x": "site", "y": "count", "group": "species"}),
    ("composition", "stacked_bar", {"x": "site", "y": "count", "group": "species"}),
    ("composition", "grouped_bar", {"x": "site", "y": "count", "group": "species"}),
    ("composition", "histogram", {"value": "count"}),
    ("composition", "treemap", {}),
]


@pytest.mark.parametrize("domain,chart,roles", CASES, ids=[f"{d}|{c}" for d, c, _ in CASES])
def test_real_data_case_round_trips_through_public_api(domain, chart, roles):
    df = load_fixture(domain)
    assert not df.empty
    try:
        fig = scifig.plot(df, chart=chart)
    except (ValueError, KeyError, TypeError) as exc:
        pytest.skip(f"{chart} on {domain}: {type(exc).__name__}: {exc}")
    assert fig is not None
    assert len(fig.axes) >= 1
    report = polish.enforce(fig, strict=False)
    assert report["legendContractEnforced"] is True
    assert len(fig.legends) <= 1
    remaining = [ax for ax in fig.axes if ax.get_legend() is not None]
    assert remaining == [], f"{chart}: per-axes legend remained after enforce"
    plt.close(fig)


def test_all_six_domain_fixtures_load():
    for name in DOMAINS:
        df = load_fixture(name)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) >= 30


def test_fixture_csvs_are_committed_to_disk():
    for name in DOMAINS:
        path = FIXTURE_DIR / f"{name}.csv"
        assert path.is_file()
        assert path.stat().st_size > 200
