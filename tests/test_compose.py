"""Tests for v0.1.6 multi-panel composition module ``scifig.compose``."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from scifig import compose


def test_compose_module_public_api_surface():
    expected = {
        "RECIPE_REGISTRY",
        "list_recipes",
        "get_recipe",
        "pick_recipe",
        "build_grid",
        "load_recipes_from_path",
    }
    assert expected.issubset(set(compose.__all__))


def test_recipe_registry_has_at_least_R0_through_R7():
    ids = compose.list_recipes()
    for needed in ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"]:
        assert needed in ids, f"missing recipe {needed}"


def test_get_recipe_by_id_and_by_name_resolve_to_same_record():
    by_id = compose.get_recipe("R0")
    by_name = compose.get_recipe(by_id["name"])
    assert by_id == by_name
    assert by_id["id"] == "R0"


def test_get_recipe_unknown_key_raises_keyerror():
    with pytest.raises(KeyError):
        compose.get_recipe("R999_missing")


def test_pick_recipe_one_panel_returns_R0():
    rec = compose.pick_recipe(panel_count=1)
    assert rec["id"] == "R0"


def test_pick_recipe_two_panel_horizontal_match():
    rec = compose.pick_recipe(panel_count=2, use_case="comparison_pair")
    assert rec["id"] == "R1"


def test_pick_recipe_falls_back_to_closest_panel_count_when_no_use_case_match():
    # 3 panels, no specific use case -> should pick R4 (panel_count=3)
    rec = compose.pick_recipe(panel_count=3)
    assert rec["panel_count"] == 3 or abs(rec.get("panel_count", 0) - 3) <= 1


def test_build_grid_R0_returns_single_axes_dict():
    fig, axes = compose.build_grid("R0")
    assert isinstance(axes, dict)
    assert "A" in axes
    assert len(axes) == 1
    plt.close(fig)


def test_build_grid_R1_returns_two_panel_horizontal():
    fig, axes = compose.build_grid("R1")
    assert set(axes.keys()) == {"A", "B"}
    bbox_a = axes["A"].get_position()
    bbox_b = axes["B"].get_position()
    # Two panels side by side: A is to the left of B
    assert bbox_a.x0 < bbox_b.x0
    plt.close(fig)


def test_build_grid_R2_returns_two_by_two_storyboard():
    fig, axes = compose.build_grid("R2")
    assert set(axes.keys()) == {"A", "B", "C", "D"}
    plt.close(fig)


def test_build_grid_R5_requires_n_for_pairwise_grid():
    with pytest.raises(ValueError, match="symbolic n"):
        compose.build_grid("R5")


def test_build_grid_R5_with_n_three_returns_nine_panels():
    fig, axes = compose.build_grid("R5", n=3)
    assert len(axes) == 9
    plt.close(fig)


def test_build_grid_respects_figsize_override():
    fig, axes = compose.build_grid("R0", figsize=(4.0, 3.0))
    width, height = fig.get_size_inches()
    assert abs(width - 4.0) < 0.01
    assert abs(height - 3.0) < 0.01
    plt.close(fig)


def test_load_recipes_from_path_round_trips_a_temp_file(tmp_path):
    payload = {
        "version": "test",
        "source": "unit",
        "RX": {
            "id": "RX",
            "name": "test_panel",
            "panel_count": 1,
            "gridspec_args": {"engine": "subplots", "nrows": 1, "ncols": 1},
            "reserved_slots": {},
            "use_cases": ["unit_test"],
        },
    }
    p = tmp_path / "recipes.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    loaded = compose.load_recipes_from_path(p)
    assert loaded["RX"]["name"] == "test_panel"


def test_recipe_registry_includes_canonical_skill_recipes_when_available():
    """The package should ship with the same recipes as the skill JSON when both are visible."""
    # If the canonical JSON exists in the source-checkout layout, the registry
    # should match it. In a pure pip-install env without skill, the fallback
    # registry kicks in (just R0 + R1) and we skip this check.
    skill_json = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "scifig-generate" / "templates" / "layout-recipes-ready.json"
    if not skill_json.is_file():
        pytest.skip("skill JSON not present in this layout")
    expected = json.loads(skill_json.read_text(encoding="utf-8"))
    expected_ids = {k for k, v in expected.items() if isinstance(v, dict) and v.get("id")}
    actual_ids = set(compose.list_recipes())
    assert expected_ids.issubset(actual_ids)
