from dataclasses import asdict

from fastapi import APIRouter

from app.api.deps import DiabetesRegistryDep
from app.domain.diabetes_features import FEATURE_SPECS
from app.schemas.diabetes import (
    DiabetesPredictionRequest,
    DiabetesPredictionResponse,
    FeatureSpecOut,
    ModelInfo,
    ModelsResponse,
)
from app.services.diabetes_prediction import DiabetesPredictionService
from app.services.diabetes_registry import MODEL_DESCRIPTIONS, PRIMARY_MODEL

router = APIRouter(prefix="/diabetes", tags=["diabetes"])


@router.get("/features", response_model=list[FeatureSpecOut])
def list_features() -> list[FeatureSpecOut]:
    """Input features with labels, units and allowed values, in form display order."""
    return [FeatureSpecOut(**asdict(spec), options=[]) for spec in FEATURE_SPECS]


@router.get("/models", response_model=ModelsResponse)
def list_models(registry: DiabetesRegistryDep) -> ModelsResponse:
    return ModelsResponse(
        model_version=registry.version,
        primary=PRIMARY_MODEL,
        models=[
            ModelInfo(
                name=name,
                role="primary" if name == PRIMARY_MODEL else "glass_box_reference",
                description=MODEL_DESCRIPTIONS[name],
            )
            for name in registry.models
        ],
    )


@router.post("/predictions", response_model=DiabetesPredictionResponse)
def create_prediction(
    payload: DiabetesPredictionRequest, registry: DiabetesRegistryDep
) -> DiabetesPredictionResponse:
    """Predict diabetes risk and explain it with SHAP and LIME (not stored)."""
    return DiabetesPredictionService(registry).predict(payload)
