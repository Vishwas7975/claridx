"""Helpers mapping between the model's input features and its transformed columns."""

import pandas as pd

from ml.explain.types import FeatureContribution
from ml.pipelines.heart import FEATURES, NUMERIC_FEATURES, ORDINAL_FEATURES


def fill_values(background: pd.DataFrame) -> pd.Series:
    """Per-feature value used for a missing input; mirrors the pipeline's imputers."""
    continuous = set(NUMERIC_FEATURES + ORDINAL_FEATURES)
    filled: dict[str, float] = {}
    for feature in FEATURES:
        column = background[feature].dropna()
        value = column.median() if feature in continuous else column.mode().iloc[0]
        filled[feature] = float(value)
    return pd.Series(filled)


def original_feature(column: str) -> str:
    """Name of the input feature a transformed (for example one-hot) column came from."""
    for feature in FEATURES:
        if column == feature or column.startswith(f"{feature}_"):
            return feature
    raise ValueError(f"Cannot map transformed column {column!r} to an input feature")


def aggregate_by_feature(column_values: dict[str, float]) -> dict[str, float]:
    """Sum per-column contributions back onto the original input features."""
    totals = dict.fromkeys(FEATURES, 0.0)
    for column, value in column_values.items():
        totals[original_feature(column)] += value
    return totals


def build_contributions(
    per_feature: dict[str, float], patient: pd.Series
) -> tuple[FeatureContribution, ...]:
    """Attach the patient's entered values and sort by absolute contribution."""
    items = []
    for feature, contribution in per_feature.items():
        raw = patient[feature]
        missing = bool(pd.isna(raw))
        items.append(
            FeatureContribution(
                feature=feature,
                value=None if missing else float(raw),
                imputed=missing,
                contribution=contribution,
            )
        )
    items.sort(key=lambda item: abs(item.contribution), reverse=True)
    return tuple(items)
