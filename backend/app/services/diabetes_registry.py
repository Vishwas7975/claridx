"""Loads the trained diabetes models and their explainers once, for serving."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Self

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

ALL_SUPPORTED_MODELS = ("logistic_regression", "random_forest", "gradient_boosting", "mlp")
SERVED_MODELS = ("logistic_regression", "random_forest")
PRIMARY_MODEL = "logistic_regression"
MODEL_DESCRIPTIONS = {
    "logistic_regression": (
        "Logistic Regression: primary model selected by cross-validation ROC-AUC."
    ),
    "random_forest": "Random Forest: non-linear tree-based alternative reference model.",
    "gradient_boosting": "Gradient Boosting: boosted tree ensemble candidate classifier.",
    "mlp": "Multi-Layer Perceptron: feed-forward neural network candidate classifier.",
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
        candidate_pipelines: dict[str, Pipeline] | None = None,
    ) -> None:
        self.version = version
        self.models = models
        self.training_ranges = training_ranges
        self.candidate_pipelines = candidate_pipelines or {
            name: m.pipeline for name, m in models.items()
        }

    def get(self, name: str) -> DiabetesLoadedModel:
        return self.models[name]

    def predict_all(
        self,
        frame: pd.DataFrame,
        threshold: float = DECISION_THRESHOLD,
    ) -> tuple[bool, int, int, list[dict[str, Any]], str]:
        """Execute all four candidate models and compute majority-voting consensus.

        Returns (consensus_positive, votes_pos, votes_neg, model_results, summary).
        """
        results: list[dict[str, Any]] = []
        for name in ALL_SUPPORTED_MODELS:
            pipe = self.candidate_pipelines.get(name)
            if pipe is None:
                results.append(
                    {
                        "model_name": name,
                        "probability": None,
                        "predicted_positive": None,
                        "threshold": threshold,
                        "status": "failed",
                        "error_message": f"Pipeline '{name}' not found",
                    }
                )
                continue
            try:
                proba_arr = pipe.predict_proba(frame)
                val = proba_arr[0][1] if hasattr(proba_arr[0], "__getitem__") else proba_arr[0, 1]
                proba = float(val)
                is_pos = proba >= threshold
                results.append(
                    {
                        "model_name": name,
                        "probability": proba,
                        "predicted_positive": is_pos,
                        "threshold": threshold,
                        "status": "success",
                        "error_message": None,
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "model_name": name,
                        "probability": None,
                        "predicted_positive": None,
                        "threshold": threshold,
                        "status": "failed",
                        "error_message": str(exc),
                    }
                )

        successful = [
            r for r in results if r["status"] == "success" and r["predicted_positive"] is not None
        ]
        total_candidates = len(self.candidate_pipelines)
        min_required = 3 if total_candidates >= 3 else max(1, total_candidates)
        if len(successful) < min_required:
            raise RuntimeError(
                f"Too few models succeeded ({len(successful)} of {len(ALL_SUPPORTED_MODELS)}) "
                "to form a defensible consensus prediction."
            )

        votes_pos = sum(1 for r in successful if r["predicted_positive"] is True)
        votes_neg = sum(1 for r in successful if r["predicted_positive"] is False)

        if votes_pos > votes_neg:
            consensus_positive = True
        elif votes_neg > votes_pos:
            consensus_positive = False
        else:
            primary_r = next((r for r in successful if r["model_name"] == PRIMARY_MODEL), None)
            consensus_positive = primary_r["predicted_positive"] if primary_r is not None else False

        summary = (
            f"Experimental majority voting: {votes_pos} elevated risk vote(s), "
            f"{votes_neg} lower risk vote(s) across {len(successful)} models."
        )
        return consensus_positive, votes_pos, votes_neg, results, summary

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
            if name in SERVED_MODELS
        }
        ranges: dict[str, tuple[float, float]] = {}
        for feature in DIABETES_FEATURES:
            col = background[feature].dropna()
            if feature in SUSPICIOUS_ZERO_FEATURES:
                col = col[col != 0]
            ranges[feature] = (float(col.min()), float(col.max()))
        return cls(version, models, ranges, candidate_pipelines=pipelines)

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
        pipelines = {}
        for name in ALL_SUPPORTED_MODELS:
            path = directory / f"{name}.joblib"
            if path.exists():
                pipelines[name] = joblib.load(path)
        return cls.from_models(pipelines, background, version, lime_samples)
