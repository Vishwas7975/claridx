"""Train, compare and persist the heart disease models.

Protocol: stratified hold-out split; model comparison by repeated CV on the
training set only; the hold-out set is used once, for final reporting.
"""

import json
import platform
from datetime import UTC, datetime
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml.config import CV_REPEATS, CV_SPLITS, RANDOM_SEED, TEST_SIZE
from ml.datasets.heart import RAW_FILE, sha256_of
from ml.evaluation import cross_validate_model, evaluate_on_holdout
from ml.paths import ARTIFACTS_DIR
from ml.pipelines.heart import FEATURES, build_models
from ml.splits import heart_split

ARTIFACT_DIR = ARTIFACTS_DIR / "heart"


def fmt(pair: tuple[float, float]) -> str:
    return f"{pair[0]:.3f} ± {pair[1]:.3f}"


def print_report(report: dict[str, dict[str, Any]]) -> None:
    print(
        f"\nCROSS-VALIDATION on training set ({CV_SPLITS}x{CV_REPEATS} stratified; mean ± fold std)"
    )
    columns = ("roc_auc", "recall", "f1", "brier")
    print(f"{'model':<22}" + "".join(f"{c:>16}" for c in columns))
    for name, result in report.items():
        print(f"{name:<22}" + "".join(f"{fmt(result['cv'][c]):>16}" for c in columns))

    print("\nHOLD-OUT TEST SET (used once; NOT used for model selection)")
    print(
        f"{'model':<22}{'acc':>7}{'prec':>7}{'recall':>8}{'f1':>7}{'auc':>7}"
        f"{'auc 95% CI':>16}{'brier':>8}"
    )
    for name, result in report.items():
        h = result["holdout"]
        ci = f"[{h['roc_auc_ci_low']:.2f}, {h['roc_auc_ci_high']:.2f}]"
        print(
            f"{name:<22}{h['accuracy']:>7.3f}{h['precision']:>7.3f}{h['recall']:>8.3f}"
            f"{h['f1']:>7.3f}{h['roc_auc']:>7.3f}{ci:>16}{h['brier']:>8.3f}"
        )


def main() -> None:
    X_train, X_test, y_train, y_test = heart_split()
    print(f"train: {len(X_train)} rows, test: {len(X_test)} rows")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    # Serving needs a background sample for the explainers, without the raw dataset.
    X_train.to_csv(ARTIFACT_DIR / "background.csv", index=False)
    report: dict[str, dict[str, Any]] = {}

    for name, model in build_models(RANDOM_SEED).items():
        print(f"[{name}] cross-validating and fitting ...")
        cv_summary = cross_validate_model(model, X_train, y_train, RANDOM_SEED)
        model.fit(X_train, y_train)
        holdout = evaluate_on_holdout(model, X_test, y_test, RANDOM_SEED)
        joblib.dump(model, ARTIFACT_DIR / f"{name}.joblib")
        report[name] = {"cv": cv_summary, "holdout": holdout}

    print_report(report)

    selected = max(report, key=lambda n: report[n]["cv"]["roc_auc"][0])
    print(f"\nSelected by CV ROC-AUC: {selected} (hold-out was not used for this choice)")

    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_file": RAW_FILE.name,
        "dataset_sha256": sha256_of(RAW_FILE),
        "random_seed": RANDOM_SEED,
        "test_size": TEST_SIZE,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "positive_rate_train": float(y_train.mean()),
        "positive_rate_test": float(y_test.mean()),
        "features": FEATURES,
        "selected_model_by_cv_auc": selected,
        "python": platform.python_version(),
        "scikit_learn": sklearn.__version__,
        "pandas": pd.__version__,
        "numpy": np.__version__,
    }
    payload = {"metadata": metadata, "models": report}
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(payload, indent=2))
    print(f"\nArtifacts written to {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
