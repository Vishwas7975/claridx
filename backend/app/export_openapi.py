"""Write the API's OpenAPI schema to a file (default: frontend/openapi.json).

The schema is the contract between backend and frontend: the frontend generates its
TypeScript types from the committed file, and a test fails if the file goes stale.

Usage (from backend/):  uv run python -m app.export_openapi [target]
"""

import json
import sys
from pathlib import Path

from app.main import app

DEFAULT_TARGET = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def export(target: Path = DEFAULT_TARGET) -> Path:
    target.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
    return target


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET
    print(f"Wrote {export(target)}")


if __name__ == "__main__":
    main()
