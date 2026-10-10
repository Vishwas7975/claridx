"""Evaluation helpers: repeated cross-validation, hold-out metrics, bootstrap CI."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate

from ml.config import BOOTSTRAP_RESAMPLES, CV_REPEATS, CV_SPLITS

CV_SCORING = {
    "roc_auc": "roc_auc",
    "accuracy": "accuracy",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "brier": "neg_brier_score",
}


def cross_validate_model(
    model: BaseEstimator, X: pd.DataFrame, y: pd.Series, seed: int
) -> dict[str, tuple[float, float]]:
    """Repeated stratified CV. Returns (mean, std across folds) per metric."""
    cv = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=CV_REPEATS, random_state=seed)
    result = cross_validate(model, X, y, cv=cv, scoring=CV_SCORING, n_jobs=-1)

    summary: dict[str, tuple[float, float]] = {}
    for name in CV_SCORING:
        values = result[f"test_{name}"]
        if name == "brier":  # sklearn reports negated loss
            values = -values
        summary[name] = (float(values.mean()), float(values.std()))
    return summary


def bootstrap_auc_ci(
    y_true: np.ndarray, proba: np.ndarray, seed: int, n_resamples: int = BOOTSTRAP_RESAMPLES
) -> tuple[float, float]:
    """95% percentile bootstrap confidence interval for ROC-AUC."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    scores: list[float] = []
    while len(scores) < n_resamples:
        idx = rng.integers(0, n, n)
        if len(np.unique(y_true[idx])) < 2:
            continue  # AUC is undefined for a single class
        scores.append(float(roc_auc_score(y_true[idx], proba[idx])))
    return float(np.percentile(scores, 2.5)), float(np.percentile(scores, 97.5))


def evaluate_on_holdout(
    model: BaseEstimator, X_test: pd.DataFrame, y_test: pd.Series, seed: int
) -> dict[str, float]:
    y_true = y_test.to_numpy()
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    ci_low, ci_high = bootstrap_auc_ci(y_true, proba, seed)
    return {
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "roc_auc_ci_low": ci_low,
        "roc_auc_ci_high": ci_high,
        "brier": float(brier_score_loss(y_true, proba)),
    }
