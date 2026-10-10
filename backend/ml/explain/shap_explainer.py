"""SHAP explanations for the supported heart disease models."""

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.explain.features import aggregate_by_feature, build_contributions
from ml.explain.types import Explanation
from ml.pipelines.heart import FEATURES


class ShapExplainer:
    """Explains one patient at a time, aggregated onto the 13 input features.

    Random Forest contributions are in probability units; Logistic Regression
    contributions are in log-odds units (see Explanation.output_space).
    """

    def __init__(self, pipeline: Pipeline, background: pd.DataFrame) -> None:
        self._pipeline = pipeline
        self._preprocess = pipeline.named_steps["preprocess"]
        classifier = pipeline.named_steps["model"]
        self._columns = [str(name) for name in self._preprocess.get_feature_names_out()]

        if isinstance(classifier, RandomForestClassifier):
            self._explainer = shap.TreeExplainer(classifier)
            self.output_space = "probability"
        elif isinstance(classifier, LogisticRegression):
            data = self._preprocess.transform(background[FEATURES])
            # Use the whole background so the base value is exact and reproducible.
            masker = shap.maskers.Independent(data, max_samples=len(data))
            self._explainer = shap.LinearExplainer(classifier, masker)
            self.output_space = "log_odds"
        else:
            raise NotImplementedError(
                f"SHAP explanations are not implemented for {type(classifier).__name__}"
            )

    def column_contributions(self, patient: pd.DataFrame) -> dict[str, float]:
        """Contributions per transformed column (one-hot level), before aggregation."""
        transformed = self._preprocess.transform(patient[FEATURES].iloc[[0]])
        values = np.asarray(self._explainer.shap_values(transformed))
        if values.ndim == 3:  # tree explainers return one slice per class; class 1 = disease
            values = values[..., 1]
        return dict(zip(self._columns, values[0].tolist(), strict=True))

    def explain(self, patient: pd.DataFrame) -> Explanation:
        frame = patient[FEATURES].iloc[[0]]
        per_feature = aggregate_by_feature(self.column_contributions(frame))
        return Explanation(
            method="shap",
            probability=float(self._pipeline.predict_proba(frame)[0, 1]),
            output_space=self.output_space,
            contributions=build_contributions(per_feature, frame.iloc[0]),
            base_value=float(np.ravel(self._explainer.expected_value)[-1]),
        )
