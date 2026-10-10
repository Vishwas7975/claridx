from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.services.model_registry import ModelRegistry


def get_registry(request: Request) -> ModelRegistry:
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction models are not loaded.",
        )
    return registry


RegistryDep = Annotated[ModelRegistry, Depends(get_registry)]
