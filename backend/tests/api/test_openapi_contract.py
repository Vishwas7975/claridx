import json

from app.export_openapi import DEFAULT_TARGET, export
from app.main import app


def _current_schema() -> dict:
    return json.loads(json.dumps(app.openapi()))


def test_schema_lists_the_public_endpoints() -> None:
    paths = _current_schema()["paths"]
    for path in (
        "/api/v1/health",
        "/api/v1/health/db",
        "/api/v1/heart/features",
        "/api/v1/heart/models",
        "/api/v1/heart/predictions",
    ):
        assert path in paths


def test_committed_frontend_schema_is_current() -> None:
    committed = json.loads(DEFAULT_TARGET.read_text())
    assert committed == _current_schema(), (
        "The API changed. Run `npm run api:sync` in frontend/ (or "
        "`uv run python -m app.export_openapi` in backend/) and commit the result."
    )


def test_export_writes_a_loadable_schema(tmp_path) -> None:
    target = export(tmp_path / "schema.json")
    assert json.loads(target.read_text()) == _current_schema()
