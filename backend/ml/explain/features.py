"""Helpers mapping between the model's input features and its transformed columns."""

from collections.abc import Sequence

import pandas as pd

from ml.explain.types import FeatureContribution
from ml.pipelines.heart import FEATURES, NUMERIC_FEATURES, ORDINAL_FEATURES


def fill_values(
    background: pd.DataFrame,
    features: Sequence[str] | None = None,
    continuous: Sequence[str] | None = None,
    zero_as_missing: Sequence[str] | None = None,
) -> pd.Series:
    """Per-feature value used for a missing input; mirrors the pipeline's imputers."""
    feats = list(features) if features is not None else list(FEATURES)
    if continuous is not None:
        cont_set = set(continuous)
    elif features is not None:
        cont_set = set(feats)
    else:
        cont_set = set(NUMERIC_FEATURES + ORDINAL_FEATURES)

    zero_missing_set = set(zero_as_missing) if zero_as_missing is not None else set()

    filled: dict[str, float] = {}
    for feature in feats:
        column = background[feature].dropna()
        if feature in zero_missing_set:
            column = column[column != 0]
        value = column.median() if feature in cont_set else column.mode().iloc[0]
        filled[feature] = float(value)
    return pd.Series(filled)


def original_feature(column: str, features: Sequence[str] | None = None) -> str:
    """Name of the input feature a transformed (for example one-hot) column came from."""
    feats = list(features) if features is not None else list(FEATURES)
    for feature in feats:
        if column == feature or column.startswith(f"{feature}_"):
            return feature
    raise ValueError(f"Cannot map transformed column {column!r} to an input feature")


def aggregate_by_feature(
    column_values: dict[str, float], features: Sequence[str] | None = None
) -> dict[str, float]:
    """Sum per-column contributions back onto the original input features."""
    feats = list(features) if features is not None else list(FEATURES)
    totals = dict.fromkeys(feats, 0.0)
    for column, value in column_values.items():
        orig = original_feature(column, features=feats)
        totals[orig] += value
    return totals


def build_contributions(
    per_feature: dict[str, float],
    patient: pd.Series,
    zero_as_missing: Sequence[str] | None = None,
) -> tuple[FeatureContribution, ...]:
    """Attach the patient's entered values and sort by absolute contribution."""
    zero_missing_set = set(zero_as_missing) if zero_as_missing is not None else set()
    items = []
    for feature, contribution in per_feature.items():
        raw = patient[feature]
        is_na = bool(pd.isna(raw))
        is_zero_missing = (not is_na) and (feature in zero_missing_set) and (float(raw) == 0.0)
        imputed = is_na or is_zero_missing
        items.append(
            FeatureContribution(
                feature=feature,
                value=None if is_na else float(raw),
                imputed=imputed,
                contribution=contribution,
            )
        )
    items.sort(key=lambda item: abs(item.contribution), reverse=True)
    return tuple(items)
