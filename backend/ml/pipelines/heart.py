"""Feature definitions, preprocessing and candidate models for the heart disease task."""

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak"]
ORDINAL_FEATURES = ["ca"]  # number of major vessels coloured by fluoroscopy, 0-3
NOMINAL_FEATURES = ["cp", "restecg", "slope", "thal"]
BINARY_FEATURES = ["sex", "fbs", "exang"]

FEATURES = NUMERIC_FEATURES + ORDINAL_FEATURES + NOMINAL_FEATURES + BINARY_FEATURES


def build_preprocessor() -> ColumnTransformer:
    """Impute, scale and encode. Fit only on training data (it lives inside the Pipeline)."""
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    nominal = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    binary = SimpleImputer(strategy="most_frequent")

    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES + ORDINAL_FEATURES),
            ("nominal", nominal, NOMINAL_FEATURES),
            ("binary", binary, BINARY_FEATURES),
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
