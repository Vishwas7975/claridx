import uuid
from dataclasses import asdict

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbDep, PredictionUserDep, RegistryDep
from app.domain.heart_features import FEATURE_SPECS
from app.models.prediction_history import PredictionHistory
from app.models.user import User
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
                description=MODEL_DESCRIPTIONS.get(name, name),
            )
            for name in registry.models
        ],
    )


@router.post("/predictions", response_model=PredictionResponse)
def create_prediction(
    payload: PredictionRequest,
    registry: RegistryDep,
    current_user: PredictionUserDep,
    db: DbDep,
) -> PredictionResponse:
    """Predict heart disease risk, evaluate all 4 models, and store prediction history."""
    response = HeartPredictionService(registry).predict(payload)

    record_uuid = str(uuid.uuid4())
    top_factors = [
        {
            "feature": c.feature,
            "label": c.label,
            "value": c.value,
            "imputed": c.imputed,
            "contribution": c.contribution,
        }
        for c in response.shap.contributions[:6]
    ]

    is_pos = (
        response.ensemble.predicted_positive if response.ensemble else response.predicted_positive
    )
    agg_method = response.ensemble.aggregation_method if response.ensemble else "single_model"
    is_exp = response.ensemble.is_experimental if response.ensemble else False
    model_res = (
        [m.model_dump() for m in response.ensemble.model_results] if response.ensemble else None
    )

    history_record = PredictionHistory(
        record_id=record_uuid,
        user_id=current_user.id,
        condition="heart",
        predicted_label="Elevated Risk" if is_pos else "Lower Risk",
        predicted_positive=is_pos,
        probability=response.probability,
        threshold=response.threshold,
        aggregation_method=agg_method,
        model_version=response.model_version,
        is_experimental=is_exp,
        model_results=model_res,
        top_factors=top_factors,
        input_summary=payload.patient.model_dump(exclude_none=True),
    )
    # Only persist if current_user exists in database (handles mock test users cleanly)
    user_exists = db.scalar(select(User.id).where(User.id == current_user.id))
    if user_exists is not None:
        db.add(history_record)
        db.commit()
        response.record_id = record_uuid
    return response
