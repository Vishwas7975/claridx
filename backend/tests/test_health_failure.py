from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.database import get_db
from app.main import app


class _BrokenSession:
    def execute(self, *args: object, **kwargs: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("database is down"))

    def close(self) -> None:
        return None


def _broken_db() -> Iterator[_BrokenSession]:
    yield _BrokenSession()


@pytest.fixture
def client_with_broken_db() -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = _broken_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def test_health_db_reports_503_when_the_database_is_down(client_with_broken_db) -> None:
    response = client_with_broken_db.get("/api/v1/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
