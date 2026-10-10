"""Loads the trained heart disease models and their explainers once, for serving."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from ml.explain import LimeExplainer, ShapExplainer
from ml.pipelines.heart import FEATURES, NUMERIC_FEATURES, ORDINAL_FEATURES

SERVED_MODELS = ("random_forest", "logistic_regression")
PRIMARY_MODEL = "random_forest"
MODEL_DESCRIPTIONS = {
    "random_forest": "Random Forest: the main model, explained with exact tree SHAP.",
    "logistic_regression": (
        "Logistic Regression: interpretable reference whose coefficients validate the explainers."
    ),
}


@dataclass(frozen=True)
class LoadedModel:
    name: str
    pipeline: Pipeline
    shap: ShapExplainer
    lime: LimeExplainer


class ModelRegistry:
    def __init__(
        self,
        version: str,
        models: dict[str, LoadedModel],
        training_ranges: dict[str, tuple[float, float]],
    ) -> None:
        self.version = version
        self.models = models
        self.training_ranges = training_ranges

    def get(self, name: str) -> LoadedModel:
        return self.models[name]

    @classmethod
    def from_models(
        cls,
        pipelines: dict[str, Pipeline],
        background: pd.DataFrame,
        version: str,
        lime_samples: int = 3000,
    ) -> Self:
        background = background[FEATURES]
        models = {
            name: LoadedModel(
                name=name,
                pipeline=pipeline,
                shap=ShapExplainer(pipeline, background),
                lime=LimeExplainer(pipeline, background, num_samples=lime_samples),
            )
            for name, pipeline in pipelines.items()
        }
        ranges = {
            feature: (float(background[feature].min()), float(background[feature].max()))
            for feature in NUMERIC_FEATURES + ORDINAL_FEATURES
        }
        return cls(version, models, ranges)

    @classmethod
    def load(cls, directory: Path, lime_samples: int = 3000) -> Self:
        """Load artifacts written by ml.scripts.train_heart.

        The .joblib files are pickles: only ever load artifacts we produced ourselves.
        """
        required = [directory / "metrics.json", directory / "background.csv"]
        required += [directory / f"{name}.joblib" for name in SERVED_MODELS]
        for path in required:
            if not path.exists():
                raise FileNotFoundError(path)

        metadata = json.loads((directory / "metrics.json").read_text())["metadata"]
        created = datetime.fromisoformat(metadata["created_at"])
        version = f"heart-{created.strftime('%Y%m%dT%H%M%SZ')}"

        background = pd.read_csv(directory / "background.csv")
        pipelines = {name: joblib.load(directory / f"{name}.joblib") for name in SERVED_MODELS}
        return cls.from_models(pipelines, background, version, lime_samples)
