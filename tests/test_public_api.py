import pandas as pd

import scifig
from scifig.palette import get_palette
from scifig.style import get_journal_profile
from scifig.utils import sanitize_columns


def test_package_exposes_readme_modules():
    assert scifig.style.get_journal_profile("nature")["single_width_mm"] == 89
    assert scifig.palette.get_palette("wong", n=4) == [
        "#000000",
        "#E69F00",
        "#56B4E9",
        "#009E73",
    ]
    assert scifig.utils.detect_available_font()


def test_journal_profile_is_case_insensitive_copy():
    profile = get_journal_profile("Nature")
    profile["single_width_mm"] = 0

    assert get_journal_profile("nature")["single_width_mm"] == 89


def test_sanitize_columns_handles_duplicate_original_names():
    df = pd.DataFrame([[1, 2, 3, 4]], columns=["A B", "1value", "", "A B"])

    result = sanitize_columns(df)

    assert list(result.columns) == ["a_b", "col_1value", "col_2", "a_b_1"]
    assert result.columns.is_unique
    assert list(df.columns) == ["A B", "1value", "", "A B"]


def test_sanitize_columns_avoids_generated_name_collisions():
    df = pd.DataFrame([[1, 2, 3]], columns=["a", "a_1", "a"])

    result = sanitize_columns(df)

    assert list(result.columns) == ["a", "a_1", "a_2"]
    assert result.columns.is_unique


def test_sequential_palette_interpolates_without_adjacent_duplicates():
    colors = get_palette("seq:blues", 10)

    assert len(colors) == 10
    assert colors[0] == "#f7fbff"
    assert colors[-1] == "#084594"
    assert all(a != b for a, b in zip(colors, colors[1:]))


def test_categorical_palette_cycles_when_requested_length_exceeds_base():
    assert get_palette("wong", 10)[8:] == ["#000000", "#E69F00"]
