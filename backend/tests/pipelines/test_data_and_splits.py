import hashlib
from types import SimpleNamespace

import pandas as pd
import pytest

import ml.datasets.heart as heart
import ml.splits as splits
from ml.pipelines.heart import FEATURES
from tests.pipelines.synthetic import make_heart_like_data


def _raw_frame() -> pd.DataFrame:
    X, y = make_heart_like_data(rows=200)
    raw = X.copy()
    raw[heart.TARGET_RAW] = y * 2  # severity codes 0 and 2; anything above 0 means disease
    return raw


def test_split_is_stratified_disjoint_and_uses_the_binary_target(monkeypatch) -> None:
    raw = _raw_frame()
    monkeypatch.setattr(splits, "load_raw", lambda: raw)
    X_train, X_test, y_train, y_test = splits.heart_split()

    assert (len(X_train), len(X_test)) == (160, 40)
    assert list(X_train.columns) == FEATURES
    assert set(X_train.index).isdisjoint(X_test.index)
    assert set(y_train) | set(y_test) == {0, 1}  # severity 2 is mapped to 1
    assert abs(y_train.mean() - y_test.mean()) < 0.03


def test_split_is_deterministic(monkeypatch) -> None:
    raw = _raw_frame()
    monkeypatch.setattr(splits, "load_raw", lambda: raw)
    first, second = splits.heart_split(), splits.heart_split()
    assert first[0].index.equals(second[0].index)
    assert first[1].index.equals(second[1].index)


def test_sha256_matches_hashlib_across_chunk_boundaries(tmp_path) -> None:
    path = tmp_path / "blob.bin"
    data = b"x" * (3 * 1024 * 1024 + 17)
    path.write_bytes(data)
    assert heart.sha256_of(path) == hashlib.sha256(data).hexdigest()


def test_load_raw_explains_how_to_get_a_missing_dataset(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(heart, "RAW_FILE", tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError, match="download_heart"):
        heart.load_raw()


def test_load_raw_reads_the_csv(tmp_path, monkeypatch) -> None:
    path = tmp_path / "heart.csv"
    path.write_text("age,num\n54,0\n61,2\n")
    monkeypatch.setattr(heart, "RAW_FILE", path)
    frame = heart.load_raw()
    assert list(frame.columns) == ["age", "num"]
    assert len(frame) == 2


def test_download_writes_one_csv_and_reuses_it(tmp_path, monkeypatch) -> None:
    calls = []

    def fake_fetch(**kwargs):
        calls.append(kwargs["id"])
        return SimpleNamespace(
            data=SimpleNamespace(
                features=pd.DataFrame({"age": [54, 61]}),
                targets=pd.DataFrame({"num": [0, 2]}),
            )
        )

    monkeypatch.setattr("ucimlrepo.fetch_ucirepo", fake_fetch)
    monkeypatch.setattr(heart, "RAW_DATA_DIR", tmp_path)
    monkeypatch.setattr(heart, "RAW_FILE", tmp_path / "heart.csv")

    path = heart.download()
    assert list(pd.read_csv(path).columns) == ["age", "num"]
    heart.download()
    assert calls == [heart.UCI_DATASET_ID]  # the second call used the cached file
