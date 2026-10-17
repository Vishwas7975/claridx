from dataclasses import asdict

from fastapi import APIRouter

from app.api.deps import PredictionUserDep, RegistryDep
from app.domain.heart_features import FEATURE_SPECS
from app.schemas.heart import (
    FeatureSpecOut,
    ModelInfo,
    ModelsResponse,
    PredictionRequest,
    PredictionResponse,
)
from app.services.heart_prediction import HeartPredictionService
from app.services.model_registry import MODEL_DESCRIPTIONS, PRIMARY_MODEL

router = APIRouter(prefix="/heart", tags=["heart disease"])


@router.get("/features", response_model=list[FeatureSpecOut])
def list_features() -> list[FeatureSpecOut]:
    """Input features with labels, units and allowed values, in form display order."""
    return [FeatureSpecOut(**asdict(spec)) for spec in FEATURE_SPECS]


@router.get("/models", response_model=ModelsResponse)
def list_models(registry: RegistryDep) -> ModelsResponse:
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


@router.post("/predictions", response_model=PredictionResponse)
def create_prediction(
    payload: PredictionRequest,
    registry: RegistryDep,
    _current_user: PredictionUserDep,
) -> PredictionResponse:
    """Predict heart disease risk and explain it with SHAP and LIME (not stored)."""
    return HeartPredictionService(registry).predict(payload)
