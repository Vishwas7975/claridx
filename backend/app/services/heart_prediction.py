"""Turns a validated patient into a prediction with explanations."""

import pandas as pd

from app.domain.heart_features import LABELS
from app.schemas.heart import (
    AgreementOut,
    ContributionOut,
    EnsembleOut,
    ExplanationOut,
    FeatureImpactOut,
    ModelExecutionOut,
    PatientInput,
    PredictionRequest,
    PredictionResponse,
    SensitivityOut,
)
from app.services.model_registry import ModelRegistry
from ml.config import DECISION_THRESHOLD
from ml.explain import Explanation, compare
from ml.pipelines.heart import FEATURES
from ml.sensitivity import SensitivityResult

LOW_FIDELITY_THRESHOLD = 0.5
DISCLAIMER = (
    "Decision support only, not a diagnosis. Trained on a small public research dataset "
    "(UCI Cleveland, 303 patients) and not validated for clinical use. Probabilities are "
    "raw model outputs and have not been calibrated."
)
SENSITIVITY_NOTE = (
    "Missing inputs are unknown, not normal. Contributions marked imputed are assumptions, "
    "not evidence. Ranges come from the values that real training patients have for the "
    "missing measurements; they describe the training population and do not take the "
    "entered measurements into account."
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


def _sensitivity_out(result: SensitivityResult) -> SensitivityOut:
    return SensitivityOut(
        baseline_probability=result.baseline_probability,
        probability_min=result.probability_min,
        probability_max=result.probability_max,
        typical_low=result.typical_low,
        typical_high=result.typical_high,
        positive_share=result.positive_share,
        verdict_uncertain=result.verdict_uncertain,
        patterns_used=result.patterns_used,
        impacts=[
            FeatureImpactOut(
                feature=item.feature,
                label=LABELS[item.feature],
                probability_min=item.probability_min,
                probability_max=item.probability_max,
                typical_low=item.typical_low,
                typical_high=item.typical_high,
                can_flip=item.can_flip,
            )
            for item in result.impacts
        ],
        note=SENSITIVITY_NOTE,
    )


def sensitivity_warning(result: SensitivityResult) -> str | None:
    """A warning naming the most influential missing input, only when plausible cases
    disagree about the verdict."""
    if not result.verdict_uncertain or not result.impacts:
        return None
    lead = result.impacts[0]
    return (
        "The result is uncertain because of missing measurements: about "
        f"{result.positive_share:.0%} of plausible cases are positive. The most influential "
        f"is {LABELS[lead.feature]}, typically ranging from {lead.typical_low:.2f} "
        f"to {lead.typical_high:.2f}."
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

        sensitivity = loaded.sensitivity.analyze(frame)
        warnings = _range_warnings(frame, self._registry.training_ranges)
        if sensitivity is not None:
            uncertainty_warning = sensitivity_warning(sensitivity)
            if uncertainty_warning is not None:
                warnings.append(uncertainty_warning)

        # Multi-model consensus execution
        (
            consensus_pos,
            votes_pos,
            votes_neg,
            model_results_raw,
            summary,
        ) = self._registry.predict_all(frame)
        ensemble = EnsembleOut(
            aggregation_method="majority_voting",
            is_experimental=True,
            predicted_positive=consensus_pos,
            votes_positive=votes_pos,
            votes_negative=votes_neg,
            total_models_evaluated=len(model_results_raw),
            summary=summary,
            model_results=[ModelExecutionOut(**m) for m in model_results_raw],
        )

        return PredictionResponse(
            model_name=request.model_name,
            model_version=self._registry.version,
            probability=probability,
            threshold=DECISION_THRESHOLD,
            predicted_positive=probability >= DECISION_THRESHOLD,
            calibrated=False,
            imputed_features=[f for f in FEATURES if pd.isna(frame.iloc[0][f])],
            warnings=warnings,
            shap=_explanation_out(shap_result),
            lime=_explanation_out(lime_result),
            agreement=AgreementOut(
                rank_correlation=agreement.rank_correlation,
                top_k_overlap=agreement.top_k_overlap,
                sign_agreement=agreement.sign_agreement,
                k=agreement.k,
            ),
            sensitivity=None if sensitivity is None else _sensitivity_out(sensitivity),
            disclaimer=DISCLAIMER,
            ensemble=ensemble,
        )
