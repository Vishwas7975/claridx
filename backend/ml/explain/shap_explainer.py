"""SHAP explanations for supported clinical risk models."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.explain.features import aggregate_by_feature, build_contributions
from ml.explain.types import Explanation
from ml.pipelines.heart import FEATURES as HEART_FEATURES


class ShapExplainer:
    """Explains one patient at a time, aggregated onto input features.

    Random Forest contributions are in probability units; Logistic Regression
    contributions are in log-odds units (see Explanation.output_space).
    """

    def __init__(
        self,
        pipeline: Pipeline,
        background: pd.DataFrame,
        features: Sequence[str] | None = None,
        zero_as_missing: Sequence[str] | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._preprocess = pipeline.named_steps["preprocess"]
        classifier = pipeline.named_steps["model"]

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

        self._zero_as_missing = zero_as_missing

        try:
            self._columns = [str(name) for name in self._preprocess.get_feature_names_out()]
        except (AttributeError, ValueError):
            transformed_cols = []
            if hasattr(self._preprocess, "transformers_"):
                for _, _, cols in self._preprocess.transformers_:
                    if cols != "drop":
                        transformed_cols.extend(cols)
            self._columns = [str(name) for name in (transformed_cols or self._features)]

        if isinstance(classifier, RandomForestClassifier):
            self._explainer = shap.TreeExplainer(classifier)
            self.output_space = "probability"
        elif isinstance(classifier, LogisticRegression):
            data = self._preprocess.transform(background[self._features])
            # Use the whole background so the base value is exact and reproducible.
            masker = shap.maskers.Independent(data, max_samples=len(data))
            self._explainer = shap.LinearExplainer(classifier, masker)
            self.output_space = "log_odds"
        else:
            raise NotImplementedError(
                f"SHAP explanations are not implemented for {type(classifier).__name__}"
            )

    def column_contributions(self, patient: pd.DataFrame) -> dict[str, float]:
        """Contributions per transformed column, before aggregation."""
        transformed = self._preprocess.transform(patient[self._features].iloc[[0]])
        raw_values = self._explainer.shap_values(transformed)
        if isinstance(raw_values, list):
            values = np.asarray(raw_values[1])
        else:
            values = np.asarray(raw_values)
            if values.ndim == 3:  # tree explainers return one slice per class; class 1 = disease
                values = values[..., 1]
        return dict(zip(self._columns, values[0].tolist(), strict=True))

    def explain(self, patient: pd.DataFrame) -> Explanation:
        frame = patient[self._features].iloc[[0]]
        per_feature = aggregate_by_feature(
            self.column_contributions(frame), features=self._features
        )
        expected_val = np.ravel(self._explainer.expected_value)[-1]
        return Explanation(
            method="shap",
            probability=float(self._pipeline.predict_proba(frame)[0, 1]),
            output_space=self.output_space,
            contributions=build_contributions(
                per_feature, frame.iloc[0], zero_as_missing=self._zero_as_missing
            ),
            base_value=float(expected_val),
        )
