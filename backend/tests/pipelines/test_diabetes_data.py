import hashlib
from types import SimpleNamespace

import pandas as pd
import pytest

import ml.datasets.diabetes as diabetes
import ml.splits as splits
from tests.pipelines.synthetic import make_diabetes_like_data


def _raw_frame(rows: int = 200, seed: int = 42) -> pd.DataFrame:
    X, y = make_diabetes_like_data(rows=rows, seed=seed)
    raw = X.copy()
    raw[diabetes.TARGET_RAW] = y.map({0: "tested_negative", 1: "tested_positive"})
    return raw


def test_sha256_matches_hashlib_across_chunk_boundaries(tmp_path) -> None:
    path = tmp_path / "diabetes_blob.bin"
    data = b"d" * (3 * 1024 * 1024 + 42)
    path.write_bytes(data)
    assert diabetes.sha256_of(path) == hashlib.sha256(data).hexdigest()


def test_load_raw_explains_how_to_get_a_missing_dataset(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(diabetes, "RAW_FILE", tmp_path / "missing_diabetes.csv")
    with pytest.raises(FileNotFoundError, match="download_diabetes"):
        diabetes.load_raw()


def test_load_raw_reads_the_csv(tmp_path, monkeypatch) -> None:
    raw = _raw_frame(rows=10)
    path = tmp_path / "diabetes.csv"
    raw.to_csv(path, index=False)
    monkeypatch.setattr(diabetes, "RAW_FILE", path)

    loaded = diabetes.load_raw()
    assert set(loaded.columns) == diabetes.EXPECTED_COLUMNS
    assert len(loaded) == 10


def test_load_raw_fails_on_missing_columns(tmp_path, monkeypatch) -> None:
    raw = _raw_frame(rows=5).drop(columns=["age"])
    path = tmp_path / "missing_col.csv"
    raw.to_csv(path, index=False)
    monkeypatch.setattr(diabetes, "RAW_FILE", path)

    with pytest.raises(ValueError, match="Unexpected schema.*Missing:.*age"):
        diabetes.load_raw()


def test_load_raw_fails_on_extra_columns(tmp_path, monkeypatch) -> None:
    raw = _raw_frame(rows=5)
    raw["unsupported_extra"] = 123
    path = tmp_path / "extra_col.csv"
    raw.to_csv(path, index=False)
    monkeypatch.setattr(diabetes, "RAW_FILE", path)

    with pytest.raises(ValueError, match="Unexpected schema.*Extra:.*unsupported_extra"):
        diabetes.load_raw()


def test_load_raw_fails_on_invalid_target_labels(tmp_path, monkeypatch) -> None:
    raw = _raw_frame(rows=5)
    raw[diabetes.TARGET_RAW] = [
        "tested_negative",
        "tested_negative",
        "yes",
        "no",
        "tested_positive",
    ]
    path = tmp_path / "bad_target.csv"
    raw.to_csv(path, index=False)
    monkeypatch.setattr(diabetes, "RAW_FILE", path)

    with pytest.raises(ValueError, match="Invalid target labels"):
        diabetes.load_raw()


def test_download_writes_one_csv_and_reuses_it(tmp_path, monkeypatch) -> None:
    calls = []
    sample_raw = _raw_frame(rows=20)

    def fake_fetch_openml(**kwargs):
        calls.append(kwargs["data_id"])
        return SimpleNamespace(frame=sample_raw.copy())

    monkeypatch.setattr("ml.datasets.diabetes.fetch_openml", fake_fetch_openml)
    monkeypatch.setattr(diabetes, "RAW_DATA_DIR", tmp_path)
    csv_file = tmp_path / "diabetes_openml37.csv"
    monkeypatch.setattr(diabetes, "RAW_FILE", csv_file)

    # First call: downloads and creates CSV
    path = diabetes.download()
    assert path.exists()
    assert len(calls) == 1
    assert calls[0] == diabetes.OPENML_DATASET_ID

    # Second call without force: uses cache, no network call
    diabetes.download()
    assert len(calls) == 1

    # Third call with force=True: refetches
    diabetes.download(force=True)
    assert len(calls) == 2


def test_diabetes_split_is_stratified_disjoint_and_uses_the_binary_target(monkeypatch) -> None:
    raw = _raw_frame(rows=200)
    monkeypatch.setattr(splits, "load_diabetes_raw", lambda: raw)

    X_train, X_test, y_train, y_test = splits.diabetes_split()

    assert (len(X_train), len(X_test)) == (160, 40)
    assert list(X_train.columns) == diabetes.FEATURES
    assert set(X_train.index).isdisjoint(X_test.index)
    assert set(y_train) | set(y_test) == {0, 1}
    assert abs(y_train.mean() - y_test.mean()) < 0.03


def test_diabetes_split_is_deterministic(monkeypatch) -> None:
    raw = _raw_frame(rows=200)
    monkeypatch.setattr(splits, "load_diabetes_raw", lambda: raw)

    first = splits.diabetes_split()
    second = splits.diabetes_split()

    assert first[0].index.equals(second[0].index)
    assert first[1].index.equals(second[1].index)
    assert first[2].equals(second[2])
    assert first[3].equals(second[3])


def test_diabetes_split_fails_on_missing_columns(monkeypatch) -> None:
    raw = _raw_frame(rows=50).drop(columns=["mass"])
    monkeypatch.setattr(splits, "load_diabetes_raw", lambda: raw)

    with pytest.raises(ValueError, match="Unexpected schema in diabetes split.*Missing:.*mass"):
        splits.diabetes_split()


def test_diabetes_split_fails_on_extra_columns(monkeypatch) -> None:
    raw = _raw_frame(rows=50)
    raw["unexpected_extra"] = 99
    monkeypatch.setattr(splits, "load_diabetes_raw", lambda: raw)

    with pytest.raises(
        ValueError, match="Unexpected schema in diabetes split.*Extra:.*unexpected_extra"
    ):
        splits.diabetes_split()


def test_diabetes_split_fails_on_invalid_target_labels(monkeypatch) -> None:
    raw = _raw_frame(rows=50)
    raw[diabetes.TARGET_RAW] = "unknown_status"
    monkeypatch.setattr(splits, "load_diabetes_raw", lambda: raw)

    with pytest.raises(ValueError, match="Invalid target labels"):
        splits.diabetes_split()
