"""Feature definitions, preprocessing and candidate models for the diabetes task."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

# Columns where 0 is physiologically implausible and represents unmeasured data:
SUSPICIOUS_ZERO_FEATURES = ["plas", "pres", "skin", "insu", "mass"]

# Features where 0 is valid or impossible:
STANDARD_NUMERIC_FEATURES = ["preg", "pedi", "age"]

FEATURES = ["preg", "plas", "pres", "skin", "insu", "mass", "pedi", "age"]


def _zero_to_nan(X: np.ndarray | pd.DataFrame) -> np.ndarray:
    """Stateless transform converting zeros to NaN in suspicious feature columns."""
    arr = np.asarray(X, dtype=float).copy()
    arr[arr == 0] = np.nan
    return arr


def build_preprocessor() -> ColumnTransformer:
    """Zero-handling, imputation and standardisation. Fit only on training data."""
    suspicious = Pipeline(
        [
            ("zero_to_nan", FunctionTransformer(_zero_to_nan, validate=False)),
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    standard = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        [
            ("suspicious", suspicious, SUSPICIOUS_ZERO_FEATURES),
            ("standard", standard, STANDARD_NUMERIC_FEATURES),
        ],
        verbose_feature_names_out=False,
    )


def build_models(seed: int) -> dict[str, Pipeline]:
    """Candidate models, each wrapped with its own copy of the preprocessor."""
    classifiers = {
        "logistic_regression": LogisticRegression(max_iter=1000, random_state=seed),
        "random_forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2, random_state=seed
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=seed),
        "mlp": MLPClassifier(
            hidden_layer_sizes=(32, 16), alpha=1e-2, max_iter=2000, random_state=seed
        ),
    }
    return {
        name: Pipeline([("preprocess", build_preprocessor()), ("model", classifier)])
        for name, classifier in classifiers.items()
    }
