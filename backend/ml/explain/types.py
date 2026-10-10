"""Structured explanation results shared by all explainers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureContribution:
    feature: str
    value: float | None  # value as entered; None when the input was missing
    imputed: bool  # True when the model had to fill this input in
    contribution: float  # push toward (+) or away from (-) disease, in output_space units


@dataclass(frozen=True)
class Explanation:
    method: str  # "shap" or "lime"
    probability: float  # the model's predicted probability of disease
    output_space: str  # unit of the contributions: "probability" or "log_odds"
    contributions: tuple[FeatureContribution, ...]  # largest absolute contribution first
    base_value: float | None = None  # SHAP only: model output when no feature is known
    fidelity: float | None = None  # LIME only: R^2 of the local surrogate model
