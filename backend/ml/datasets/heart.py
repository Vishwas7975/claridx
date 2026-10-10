"""UCI Heart Disease (Cleveland) dataset: download and load."""

import hashlib
from pathlib import Path

import pandas as pd

from ml.paths import RAW_DATA_DIR

UCI_DATASET_ID = 45
RAW_FILE = RAW_DATA_DIR / "heart_disease_uci45.csv"

# Raw label: 0 = no disease, 1-4 = disease present (increasing severity).
TARGET_RAW = "num"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(force: bool = False) -> Path:
    """Fetch the dataset from the UCI repository and store it as one CSV."""
    if RAW_FILE.exists() and not force:
        return RAW_FILE

    from ucimlrepo import fetch_ucirepo

    dataset = fetch_ucirepo(id=UCI_DATASET_ID)
    frame = pd.concat([dataset.data.features, dataset.data.targets], axis=1)

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RAW_FILE, index=False)
    return RAW_FILE


def load_raw() -> pd.DataFrame:
    if not RAW_FILE.exists():
        raise FileNotFoundError("Dataset missing. Run: uv run python -m ml.scripts.download_heart")
    return pd.read_csv(RAW_FILE)
