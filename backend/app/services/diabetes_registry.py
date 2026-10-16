"""Loads the trained diabetes models and their explainers once, for serving."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from ml.config import DECISION_THRESHOLD
from ml.explain import LimeExplainer, ShapExplainer
from ml.pipelines.diabetes import (
    FEATURES as DIABETES_FEATURES,
)
from ml.pipelines.diabetes import (
    SUSPICIOUS_ZERO_FEATURES,
)
from ml.sensitivity import SensitivityAnalyzer

SERVED_MODELS = ("logistic_regression", "random_forest")
PRIMARY_MODEL = "logistic_regression"
MODEL_DESCRIPTIONS = {
    "logistic_regression": (
        "Logistic Regression: primary model selected by cross-validation ROC-AUC."
    ),
    "random_forest": "Random Forest: non-linear tree-based alternative reference model.",
}


@dataclass(frozen=True)
class DiabetesLoadedModel:
    name: str
    pipeline: Pipeline
    shap: ShapExplainer
    lime: LimeExplainer
    sensitivity: SensitivityAnalyzer


class DiabetesModelRegistry:
    def __init__(
        self,
        version: str,
        models: dict[str, DiabetesLoadedModel],
        training_ranges: dict[str, tuple[float, float]],
    ) -> None:
        self.version = version
        self.models = models
        self.training_ranges = training_ranges

    def get(self, name: str) -> DiabetesLoadedModel:
        return self.models[name]

    @classmethod
    def from_models(
        cls,
        pipelines: dict[str, Pipeline],
        background: pd.DataFrame,
        version: str,
        lime_samples: int = 3000,
    ) -> Self:
        background = background[DIABETES_FEATURES]
        models = {
            name: DiabetesLoadedModel(
                name=name,
                pipeline=pipeline,
                shap=ShapExplainer(
                    pipeline,
                    background,
                    features=DIABETES_FEATURES,
                    zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
                ),
                lime=LimeExplainer(
                    pipeline,
                    background,
                    features=DIABETES_FEATURES,
                    zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
                    class_names=["tested_negative", "tested_positive"],
                    num_samples=lime_samples,
                ),
                sensitivity=SensitivityAnalyzer(
                    pipeline,
                    background,
                    features=DIABETES_FEATURES,
                    zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
                    threshold=DECISION_THRESHOLD,
                ),
            )
            for name, pipeline in pipelines.items()
        }
        ranges: dict[str, tuple[float, float]] = {}
        for feature in DIABETES_FEATURES:
            col = background[feature].dropna()
            if feature in SUSPICIOUS_ZERO_FEATURES:
                col = col[col != 0]
            ranges[feature] = (float(col.min()), float(col.max()))
        return cls(version, models, ranges)

    @classmethod
    def load(cls, directory: Path, lime_samples: int = 3000) -> Self:
        """Load artifacts written by ml.scripts.train_diabetes."""
        required = [directory / "metrics.json", directory / "background.csv"]
        required += [directory / f"{name}.joblib" for name in SERVED_MODELS]
        for path in required:
            if not path.exists():
                raise FileNotFoundError(f"Missing required artifact: {path}")

        try:
            metadata = json.loads((directory / "metrics.json").read_text())["metadata"]
            created = datetime.fromisoformat(metadata["created_at"])
            version = f"diabetes-{created.strftime('%Y%m%dT%H%M%SZ')}"
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"Malformed metrics.json in {directory}: {exc}") from exc

        background = pd.read_csv(directory / "background.csv")
        pipelines = {name: joblib.load(directory / f"{name}.joblib") for name in SERVED_MODELS}
        return cls.from_models(pipelines, background, version, lime_samples)
