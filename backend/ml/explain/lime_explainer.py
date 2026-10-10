"""LIME explanations for the supported heart disease models."""

import numpy as np
import pandas as pd
from lime.lime_tabular import LimeTabularExplainer
from sklearn.pipeline import Pipeline

from ml.config import RANDOM_SEED
from ml.explain.features import build_contributions, fill_values
from ml.explain.types import Explanation
from ml.pipelines.heart import BINARY_FEATURES, FEATURES, NOMINAL_FEATURES

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
    ) -> None:
        self._pipeline = pipeline
        self._num_samples = num_samples
        self._seed = seed
        self._fill = fill_values(background)
        self._background = background[FEATURES].fillna(self._fill).to_numpy(dtype=float)
        self._categorical = [FEATURES.index(name) for name in NOMINAL_FEATURES + BINARY_FEATURES]

    def _predict(self, rows: np.ndarray) -> np.ndarray:
        return self._pipeline.predict_proba(pd.DataFrame(rows, columns=FEATURES))

    def explain(self, patient: pd.DataFrame) -> Explanation:
        frame = patient[FEATURES].iloc[[0]]
        row = frame.iloc[0]
        filled = row.fillna(self._fill).to_numpy(dtype=float)

        # A fresh, identically seeded explainer per call makes every explanation reproducible.
        explainer = LimeTabularExplainer(
            self._background,
            feature_names=FEATURES,
            class_names=["absent", "present"],
            categorical_features=self._categorical,
            mode="classification",
            discretize_continuous=True,
            random_state=self._seed,
        )
        result = explainer.explain_instance(
            filled,
            self._predict,
            labels=(DISEASE_CLASS,),
            num_features=len(FEATURES),
            num_samples=self._num_samples,
        )

        weights = dict.fromkeys(FEATURES, 0.0)
        for index, weight in result.local_exp[DISEASE_CLASS]:
            weights[FEATURES[index]] = float(weight)

        score = result.score
        fidelity = score[DISEASE_CLASS] if isinstance(score, dict) else score
        return Explanation(
            method="lime",
            probability=float(self._pipeline.predict_proba(frame)[0, DISEASE_CLASS]),
            output_space="probability",
            contributions=build_contributions(weights, row),
            fidelity=None if fidelity is None else float(fidelity),
        )
