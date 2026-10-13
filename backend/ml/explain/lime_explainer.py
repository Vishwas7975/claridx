"""LIME explanations for supported clinical risk models."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from lime.lime_tabular import LimeTabularExplainer
from sklearn.pipeline import Pipeline

from ml.config import RANDOM_SEED
from ml.explain.features import build_contributions, fill_values
from ml.explain.types import Explanation
from ml.pipelines.heart import (
    BINARY_FEATURES as HEART_BINARY_FEATURES,
)
from ml.pipelines.heart import (
    FEATURES as HEART_FEATURES,
)
from ml.pipelines.heart import (
    NOMINAL_FEATURES as HEART_NOMINAL_FEATURES,
)

DISEASE_CLASS = 1


class LimeExplainer:
    """Local surrogate explanations. Contributions are in probability units.

    LIME needs complete rows, so missing inputs are filled the same way the
    model's own imputers fill them. Such features are still flagged as imputed.
    """

    def __init__(
        self,
        pipeline: Pipeline,
        background: pd.DataFrame,
        num_samples: int = 3000,
        seed: int = RANDOM_SEED,
        features: Sequence[str] | None = None,
        categorical_features: Sequence[int] | None = None,
        class_names: Sequence[str] | None = None,
        zero_as_missing: Sequence[str] | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._num_samples = num_samples
        self._seed = seed
        self._zero_as_missing = zero_as_missing

        if features is not None:
            self._features = list(features)
        elif isinstance(background, pd.DataFrame) and list(background.columns) == list(
            HEART_FEATURES
        ):
            self._features = list(HEART_FEATURES)
        elif isinstance(background, pd.DataFrame):
            self._features = list(background.columns)
        else:
            self._features = list(HEART_FEATURES)

        missing = [f for f in self._features if f not in background.columns]
        if missing:
            raise ValueError(f"Background missing features: {missing}")

        self._fill = fill_values(
            background, features=self._features, zero_as_missing=zero_as_missing
        )
        self._background = background[self._features].fillna(self._fill).to_numpy(dtype=float)

        if categorical_features is not None:
            self._categorical = list(categorical_features)
        elif self._features == list(HEART_FEATURES):
            self._categorical = [
                self._features.index(name)
                for name in HEART_NOMINAL_FEATURES + HEART_BINARY_FEATURES
            ]
        else:
            self._categorical = []

        if class_names is not None:
            self._class_names = list(class_names)
        elif self._features == list(HEART_FEATURES):
            self._class_names = ["absent", "present"]
        else:
            self._class_names = ["tested_negative", "tested_positive"]

    def _predict(self, rows: np.ndarray) -> np.ndarray:
        return self._pipeline.predict_proba(pd.DataFrame(rows, columns=self._features))

    def explain(self, patient: pd.DataFrame) -> Explanation:
        frame = patient[self._features].iloc[[0]]
        row = frame.iloc[0]
        filled = row.fillna(self._fill).to_numpy(dtype=float)

        # A fresh, identically seeded explainer per call makes every explanation reproducible.
        explainer = LimeTabularExplainer(
            self._background,
            feature_names=self._features,
            class_names=self._class_names,
            categorical_features=self._categorical,
            mode="classification",
            discretize_continuous=True,
            random_state=self._seed,
        )
        result = explainer.explain_instance(
            filled,
            self._predict,
            labels=(DISEASE_CLASS,),
            num_features=len(self._features),
            num_samples=self._num_samples,
        )

        weights = dict.fromkeys(self._features, 0.0)
        for index, weight in result.local_exp[DISEASE_CLASS]:
            weights[self._features[index]] = float(weight)

        score = result.score
        fidelity = score[DISEASE_CLASS] if isinstance(score, dict) else score
        return Explanation(
            method="lime",
            probability=float(self._pipeline.predict_proba(frame)[0, DISEASE_CLASS]),
            output_space="probability",
            contributions=build_contributions(weights, row, zero_as_missing=self._zero_as_missing),
            fidelity=None if fidelity is None else float(fidelity),
        )
