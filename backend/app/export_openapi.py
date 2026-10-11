"""Write the frontend's generated contract files.

- frontend/openapi.json: the API's OpenAPI schema; the frontend generates its TypeScript
  types from it.
- frontend/src/test/fixtures/heart-features.json: the real feature specs and the minimum
  measurement count, so frontend tests run against the backend's own definitions.

Tests fail if either committed file goes stale.

Usage (from backend/):  uv run python -m app.export_openapi
"""

import json
from pathlib import Path

from app.api.v1.heart import list_features
from app.main import app
from app.schemas.heart import MIN_PROVIDED_FEATURES

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
DEFAULT_TARGET = FRONTEND_DIR / "openapi.json"
FEATURES_TARGET = FRONTEND_DIR / "src" / "test" / "fixtures" / "heart-features.json"


def current_features() -> dict:
    return {
        "min_measurements": MIN_PROVIDED_FEATURES,
        "features": [spec.model_dump(mode="json") for spec in list_features()],
    }


def _write(target: Path, payload: object) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return target


def export(target: Path = DEFAULT_TARGET) -> Path:
    return _write(target, app.openapi())


def export_features(target: Path = FEATURES_TARGET) -> Path:
    return _write(target, current_features())


def main() -> None:
    print(f"Wrote {export()}")
    print(f"Wrote {export_features()}")


if __name__ == "__main__":
    main()
