import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.diabetes_registry import DiabetesModelRegistry
from app.services.model_registry import ModelRegistry

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    heart_dir = get_settings().model_artifacts_dir / "heart"
    try:
        app.state.registry = ModelRegistry.load(heart_dir)
        logger.info("Loaded heart models, version %s", app.state.registry.version)
    except FileNotFoundError as exc:
        app.state.registry = None
        logger.error(
            "Model artifacts missing (%s). Train first: uv run python -m ml.scripts.train_heart",
            exc,
        )

    diabetes_dir = get_settings().model_artifacts_dir / "diabetes"
    try:
        app.state.diabetes_registry = DiabetesModelRegistry.load(diabetes_dir)
        logger.info("Loaded diabetes models, version %s", app.state.diabetes_registry.version)
    except (FileNotFoundError, ValueError) as exc:
        app.state.diabetes_registry = None
        logger.warning(
            "Diabetes model artifacts missing or invalid (%s). "
            "Train first: uv run python -m ml.scripts.train_diabetes",
            exc,
        )
    yield


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Report which fields failed and why, without echoing the submitted values.

    The default handler includes each rejected value. A NaN or Infinity there makes the
    JSON response itself fail (HTTP 500), and patient data should not be echoed back anyway.
    """
    errors = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
