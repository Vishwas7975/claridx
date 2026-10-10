"""Missing-data sensitivity: how far could the prediction move if the unknown inputs
took values that real patients actually have?

Scenarios are built from training patients: each one supplies its own values for all the
missing features at once, so combinations that occur together in practice stay together.
Scenarios do not take the entered measurements into account, so they describe the
training population, not patients "like this one".
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
import pandas as pd

from ml.config import (
    DECISION_THRESHOLD,
    TYPICAL_PERCENTILES,
    UNCERTAIN_SHARE_HIGH,
    UNCERTAIN_SHARE_LOW,
)
from ml.pipelines.heart import FEATURES


class ProbabilityModel(Protocol):
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return an (n, 2) array of class probabilities."""


@dataclass(frozen=True)
class FeatureImpact:
    feature: str
    probability_min: float  # extremes while only this feature varies
    probability_max: float
    typical_low: float  # 10th and 90th percentile while only this feature varies
    typical_high: float
    can_flip: bool  # the typical range straddles the decision threshold

    @property
    def spread(self) -> float:
        return self.typical_high - self.typical_low


@dataclass(frozen=True)
class SensitivityResult:
    baseline_probability: float  # missing inputs filled by the model's own imputers
    probability_min: float  # lowest and highest over all training patterns
    probability_max: float
    typical_low: float  # 10th and 90th percentile over training patterns
    typical_high: float
    positive_share: float  # share of plausible cases at or above the decision threshold
    verdict_uncertain: bool  # plausible cases disagree about the verdict
    patterns_used: int  # number of training patients that supplied values
    impacts: tuple[FeatureImpact, ...]  # missing features, most influential first


class SensitivityAnalyzer:
    def __init__(
        self,
        model: ProbabilityModel,
        background: pd.DataFrame,
        threshold: float = DECISION_THRESHOLD,
    ) -> None:
        self._model = model
        self._threshold = threshold
        self._background = background[FEATURES].astype(float).reset_index(drop=True)

    def analyze(self, patient: pd.DataFrame) -> SensitivityResult | None:
        """Return None when nothing is missing, or when no training patient has values for
        all the missing features (an honest range cannot be computed then)."""
        row = patient[FEATURES].iloc[[0]].astype(float)
        missing = [feature for feature in FEATURES if bool(row[feature].isna().iloc[0])]
        if not missing:
            return None

        patterns = self._background.dropna(subset=missing)
        if patterns.empty:
            return None

        baseline = float(self._model.predict_proba(row)[0, 1])

        joint = self._repeat(row, len(patterns))
        for feature in missing:
            joint[feature] = patterns[feature].to_numpy()
        singles, owners = self._single_scenarios(row, missing)

        scenarios = pd.concat([joint, singles], ignore_index=True)
        probabilities = self._model.predict_proba(scenarios)[:, 1]
        joint_probabilities = probabilities[: len(joint)]
        single_probabilities = probabilities[len(joint) :]

        low_percentile, high_percentile = TYPICAL_PERCENTILES
        typical_low, typical_high = (
            float(value)
            for value in np.percentile(joint_probabilities, [low_percentile, high_percentile])
        )
        positive_share = float(np.mean(joint_probabilities >= self._threshold))

        impacts = []
        for feature in missing:
            values = single_probabilities[owners == feature]
            feature_low, feature_high = (
                float(value) for value in np.percentile(values, [low_percentile, high_percentile])
            )
            impacts.append(
                FeatureImpact(
                    feature=feature,
                    probability_min=float(min(baseline, values.min())),
                    probability_max=float(max(baseline, values.max())),
                    typical_low=feature_low,
                    typical_high=feature_high,
                    can_flip=feature_low < self._threshold <= feature_high,
                )
            )
        impacts.sort(key=lambda item: (-item.spread, item.feature))

        return SensitivityResult(
            baseline_probability=baseline,
            probability_min=float(min(baseline, probabilities.min())),
            probability_max=float(max(baseline, probabilities.max())),
            typical_low=typical_low,
            typical_high=typical_high,
            positive_share=positive_share,
            verdict_uncertain=UNCERTAIN_SHARE_LOW <= positive_share <= UNCERTAIN_SHARE_HIGH,
            patterns_used=len(patterns),
            impacts=tuple(impacts),
        )

    @staticmethod
    def _repeat(row: pd.DataFrame, count: int) -> pd.DataFrame:
        return pd.concat([row] * count, ignore_index=True)

    def _single_scenarios(
        self, row: pd.DataFrame, missing: list[str]
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """Vary one missing feature at a time over training values; others stay at default."""
        frames = []
        owners: list[str] = []
        for feature in missing:
            values = self._background[feature].dropna().to_numpy()
            frame = self._repeat(row, len(values))
            frame[feature] = values
            frames.append(frame)
            owners.extend([feature] * len(values))
        return pd.concat(frames, ignore_index=True), np.array(owners)
