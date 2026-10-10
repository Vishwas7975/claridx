import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_registry
from app.main import app
from app.services.model_registry import ModelRegistry
from ml.pipelines.heart import build_models
from tests.pipelines.synthetic import make_heart_like_data


@pytest.fixture(scope="session")
def registry() -> ModelRegistry:
    X, y = make_heart_like_data()
    candidates = build_models(0)
    pipelines = {
        name: candidates[name].fit(X, y) for name in ("random_forest", "logistic_regression")
    }
    return ModelRegistry.from_models(pipelines, X, version="test-1", lime_samples=300)


@pytest.fixture
def client(registry: ModelRegistry):
    app.dependency_overrides[get_registry] = lambda: registry
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_without_models():
    app.dependency_overrides.clear()
    app.state.registry = None
    return TestClient(app)
