import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_registry
from app.main import app
from app.models.user import User, UserRole
from app.services.model_registry import ModelRegistry
from ml.pipelines.heart import build_models
from tests.pipelines.synthetic import make_heart_like_data


def _make_test_doctor() -> User:
    return User(
        id=999,
        email="doctor@example.com",
        full_name="Dr. Test Physician",
        hashed_password="...",
        role=UserRole.DOCTOR,
        is_active=True,
    )


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
    app.dependency_overrides[get_current_active_user] = _make_test_doctor
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_without_models():
    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_active_user] = _make_test_doctor
    app.state.registry = None
    yield TestClient(app)
    app.dependency_overrides.clear()
