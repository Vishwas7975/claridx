import pytest

from ml.explain import Explanation, FeatureContribution, compare

BASE = {"a": 5.0, "b": 4.0, "c": 3.0, "d": 2.0, "e": 1.0}


def _explanation(values: dict[str, float]) -> Explanation:
    contributions = tuple(
        FeatureContribution(feature=name, value=0.0, imputed=False, contribution=value)
        for name, value in values.items()
    )
    return Explanation(
        method="test",
        probability=0.5,
        output_space="probability",
        contributions=contributions,
    )


def test_identical_explanations_agree_fully() -> None:
    result = compare(_explanation(BASE), _explanation(BASE))
    assert result.rank_correlation == pytest.approx(1.0)
    assert result.top_k_overlap == 1.0
    assert result.sign_agreement == 1.0


def test_opposite_directions_keep_ranking_but_lose_sign_agreement() -> None:
    flipped = {name: -value for name, value in BASE.items()}
    result = compare(_explanation(BASE), _explanation(flipped))
    assert result.rank_correlation == pytest.approx(1.0)
    assert result.sign_agreement == 0.0


def test_reversed_ranking_is_detected() -> None:
    reversed_values = dict(zip(BASE, reversed(list(BASE.values())), strict=True))
    result = compare(_explanation(BASE), _explanation(reversed_values))
    assert result.rank_correlation == pytest.approx(-1.0)
    assert result.top_k_overlap == pytest.approx(1 / 3)


def test_constant_contributions_give_undefined_correlation() -> None:
    flat = {name: 1.0 for name in BASE}
    assert compare(_explanation(BASE), _explanation(flat)).rank_correlation is None


def test_mismatched_features_are_rejected() -> None:
    with pytest.raises(ValueError):
        compare(_explanation(BASE), _explanation({"a": 1.0, "z": 2.0}))
