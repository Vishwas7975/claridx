"""Turns a validated patient into a prediction with explanations."""

import pandas as pd

from app.domain.heart_features import LABELS
from app.schemas.heart import (
    AgreementOut,
    ContributionOut,
    ExplanationOut,
    PatientInput,
    PredictionRequest,
    PredictionResponse,
)
from app.services.model_registry import ModelRegistry
from ml.explain import Explanation, compare
from ml.pipelines.heart import FEATURES

DECISION_THRESHOLD = 0.5
LOW_FIDELITY_THRESHOLD = 0.5
DISCLAIMER = (
    "Decision support only, not a diagnosis. Trained on a small public research dataset "
    "(UCI Cleveland, 303 patients) and not validated for clinical use. Probabilities are "
    "raw model outputs and have not been calibrated."
)


def patient_frame(patient: PatientInput) -> pd.DataFrame:
    """One-row frame in model feature order; missing measurements become NaN."""
    return pd.DataFrame([patient.model_dump()], columns=FEATURES).astype(float)


def _explanation_out(explanation: Explanation) -> ExplanationOut:
    fidelity = explanation.fidelity
    return ExplanationOut(
        method=explanation.method,
        output_space=explanation.output_space,
        base_value=explanation.base_value,
        fidelity=fidelity,
        low_confidence=fidelity is not None and fidelity < LOW_FIDELITY_THRESHOLD,
        contributions=[
            ContributionOut(
                feature=item.feature,
                label=LABELS[item.feature],
                value=item.value,
                imputed=item.imputed,
                contribution=item.contribution,
            )
            for item in explanation.contributions
        ],
    )


def _range_warnings(frame: pd.DataFrame, ranges: dict[str, tuple[float, float]]) -> list[str]:
    warnings = []
    for feature, (low, high) in ranges.items():
        value = frame.iloc[0][feature]
        if pd.notna(value) and not low <= value <= high:
            warnings.append(
                f"{LABELS[feature]} = {value:g} is outside the range seen in training data "
                f"({low:g} to {high:g}); the prediction may be unreliable."
            )
    return warnings


class HeartPredictionService:
    def __init__(self, registry: ModelRegistry) -> None:
        self._registry = registry

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        loaded = self._registry.get(request.model_name)
        frame = patient_frame(request.patient)

        shap_result = loaded.shap.explain(frame)
        lime_result = loaded.lime.explain(frame)
        agreement = compare(shap_result, lime_result)
        probability = shap_result.probability

        return PredictionResponse(
            model_name=request.model_name,
            model_version=self._registry.version,
            probability=probability,
            threshold=DECISION_THRESHOLD,
            predicted_positive=probability >= DECISION_THRESHOLD,
            calibrated=False,
            imputed_features=[f for f in FEATURES if pd.isna(frame.iloc[0][f])],
            warnings=_range_warnings(frame, self._registry.training_ranges),
            shap=_explanation_out(shap_result),
            lime=_explanation_out(lime_result),
            agreement=AgreementOut(
                rank_correlation=agreement.rank_correlation,
                top_k_overlap=agreement.top_k_overlap,
                sign_agreement=agreement.sign_agreement,
                k=agreement.k,
            ),
            disclaimer=DISCLAIMER,
        )
