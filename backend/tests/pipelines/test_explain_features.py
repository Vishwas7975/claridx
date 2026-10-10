import pytest

from ml.explain.features import original_feature


def test_transformed_columns_map_back_to_their_input_feature() -> None:
    expected = {
        "cp_4.0": "cp",
        "thal_7.0": "thal",
        "thalach": "thalach",  # starts with "thal" but is a different feature
        "restecg_2.0": "restecg",
        "sex": "sex",
        "ca": "ca",
    }
    for column, feature in expected.items():
        assert original_feature(column) == feature


def test_unmappable_column_is_rejected() -> None:
    with pytest.raises(ValueError):
        original_feature("mystery_column")
