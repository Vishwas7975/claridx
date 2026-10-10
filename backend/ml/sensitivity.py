"""Missing-data sensitivity: how far could the prediction move if the unknown inputs
took plausible values?

Plausible values come only from the training data: every observed code for categorical
features, and five quantiles (5th to 95th percentile) for numeric ones. No clinical
values are invented here.
"""

from dataclasses import dataclass
from itertools import product
from typing import Protocol

import numpy as np
import pandas as pd

from ml.config import DECISION_THRESHOLD, MAX_SENSITIVITY_SCENARIOS, RANDOM_SEED
from ml.pipelines.heart import FEATURES, NUMERIC_FEATURES

QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)


class ProbabilityModel(Protocol):
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return an (n, 2) array of class probabilities."""


@dataclass(frozen=True)
class FeatureImpact:
    feature: str
    probability_min: float
    probability_max: float
    can_flip: bool  # plausible values of this feature alone can change the verdict

    @property
    def spread(self) -> float:
        return self.probability_max - self.probability_min


@dataclass(frozen=True)
class SensitivityResult:
    baseline_probability: float  # missing inputs filled by the model's own imputers
    probability_min: float
    probability_max: float
    can_flip: bool  # the range crosses the decision threshold
    exhaustive: bool  # False when joint scenarios were sampled, so the range is approximate
    scenarios_evaluated: int
    impacts: tuple[FeatureImpact, ...]  # missing features, most influential first


def _candidate_values(column: pd.Series, feature: str) -> np.ndarray:
    values = column.dropna()
    if feature in NUMERIC_FEATURES:
        return np.unique(values.quantile(QUANTILES).to_numpy(dtype=float))
    return np.unique(values.to_numpy(dtype=float))


class SensitivityAnalyzer:
    def __init__(
        self,
        model: ProbabilityModel,
        background: pd.DataFrame,
        threshold: float = DECISION_THRESHOLD,
        max_scenarios: int = MAX_SENSITIVITY_SCENARIOS,
        seed: int = RANDOM_SEED,
    ) -> None:
        self._model = model
        self._threshold = threshold
        self._max_scenarios = max_scenarios
        self._seed = seed
        self._candidates = {
            feature: _candidate_values(background[feature], feature) for feature in FEATURES
        }

    def analyze(self, patient: pd.DataFrame) -> SensitivityResult | None:
        """Return None when nothing is missing (there is nothing to be sensitive to)."""
        row = patient[FEATURES].iloc[[0]].astype(float)
        missing = [feature for feature in FEATURES if bool(row[feature].isna().iloc[0])]
        if not missing:
            return None

        baseline = float(self._model.predict_proba(row)[0, 1])
        joint, exhaustive = self._joint_scenarios(row, missing)
        singles, owners = self._single_scenarios(row, missing)

        scenarios = pd.concat([joint, singles], ignore_index=True)
        probabilities = self._model.predict_proba(scenarios)[:, 1]
        single_probabilities = probabilities[len(joint) :]

        low = float(min(baseline, probabilities.min()))
        high = float(max(baseline, probabilities.max()))

        impacts = []
        for feature in missing:
            values = single_probabilities[owners == feature]
            feature_low = float(min(baseline, values.min()))
            feature_high = float(max(baseline, values.max()))
            impacts.append(
                FeatureImpact(
                    feature=feature,
                    probability_min=feature_low,
                    probability_max=feature_high,
                    can_flip=feature_low < self._threshold <= feature_high,
                )
            )
        impacts.sort(key=lambda item: (-item.spread, item.feature))

        return SensitivityResult(
            baseline_probability=baseline,
            probability_min=low,
            probability_max=high,
            can_flip=low < self._threshold <= high,
            exhaustive=exhaustive,
            scenarios_evaluated=len(scenarios),
            impacts=tuple(impacts),
        )

    def _joint_scenarios(self, row: pd.DataFrame, missing: list[str]) -> tuple[pd.DataFrame, bool]:
        """Every combination of candidate values, or a seeded random sample if too many."""
        value_lists = [self._candidates[feature] for feature in missing]
        total = int(np.prod([len(values) for values in value_lists]))
        if total <= self._max_scenarios:
            combos = np.array(list(product(*value_lists)), dtype=float)
            exhaustive = True
        else:
            rng = np.random.default_rng(self._seed)
            combos = np.column_stack(
                [rng.choice(values, size=self._max_scenarios) for values in value_lists]
            )
            exhaustive = False

        frame = pd.concat([row] * len(combos), ignore_index=True)
        for index, feature in enumerate(missing):
            frame[feature] = combos[:, index]
        return frame, exhaustive

    def _single_scenarios(
        self, row: pd.DataFrame, missing: list[str]
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """Vary one missing feature at a time; the other unknowns stay at the model's default."""
        frames = []
        owners: list[str] = []
        for feature in missing:
            values = self._candidates[feature]
            frame = pd.concat([row] * len(values), ignore_index=True)
            frame[feature] = values
            frames.append(frame)
            owners.extend([feature] * len(values))
        return pd.concat(frames, ignore_index=True), np.array(owners)
