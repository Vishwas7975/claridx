import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from app.core.config import BACKEND_DIR


def _resolve_test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(BACKEND_DIR / ".env").get(
        "TEST_DATABASE_URL"
    )
    if not url:
        raise RuntimeError("TEST_DATABASE_URL is not set (see backend/.env.example)")
    database = make_url(url).database or ""
    if not database.endswith("_test"):
        raise RuntimeError(f"Refusing to run tests against non-test database: {database!r}")
    return url


# Must run before any module that reads settings or creates the engine is imported.
os.environ["DATABASE_URL"] = _resolve_test_database_url()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Bring the test database to the latest schema using the real migrations."""
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(config, "head")
