"""Human-readable definitions of the heart disease input features.

Labels and value codes follow the UCI Heart Disease variable documentation.
They drive the input form in the frontend and the labels in explanations.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Option:
    value: int
    label: str


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    label: str
    kind: str  # "number" or "category"
    description: str
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    options: tuple[Option, ...] = ()


FEATURE_SPECS: tuple[FeatureSpec, ...] = (
    FeatureSpec("age", "Age", "number", "Age in years", unit="years", minimum=18, maximum=120),
    FeatureSpec(
        "sex",
        "Sex",
        "category",
        "Sex as recorded in the dataset",
        options=(Option(0, "Female"), Option(1, "Male")),
    ),
    FeatureSpec(
        "cp",
        "Chest pain type",
        "category",
        "Type of chest pain reported",
        options=(
            Option(1, "Typical angina"),
            Option(2, "Atypical angina"),
            Option(3, "Non-anginal pain"),
            Option(4, "Asymptomatic"),
        ),
    ),
    FeatureSpec(
        "trestbps",
        "Resting blood pressure",
        "number",
        "Resting blood pressure on admission",
        unit="mm Hg",
        minimum=50,
        maximum=300,
    ),
    FeatureSpec(
        "chol",
        "Serum cholesterol",
        "number",
        "Serum cholesterol",
        unit="mg/dl",
        minimum=50,
        maximum=700,
    ),
    FeatureSpec(
        "fbs",
        "Fasting blood sugar > 120 mg/dl",
        "category",
        "Whether fasting blood sugar exceeds 120 mg/dl",
        options=(Option(0, "No"), Option(1, "Yes")),
    ),
    FeatureSpec(
        "restecg",
        "Resting ECG result",
        "category",
        "Resting electrocardiographic result",
        options=(
            Option(0, "Normal"),
            Option(1, "ST-T wave abnormality"),
            Option(2, "Left ventricular hypertrophy"),
        ),
    ),
    FeatureSpec(
        "thalach",
        "Maximum heart rate achieved",
        "number",
        "Maximum heart rate achieved during the exercise test",
        unit="bpm",
        minimum=40,
        maximum=250,
    ),
    FeatureSpec(
        "exang",
        "Exercise-induced angina",
        "category",
        "Whether exercise induced angina",
        options=(Option(0, "No"), Option(1, "Yes")),
    ),
    FeatureSpec(
        "oldpeak",
        "ST depression induced by exercise",
        "number",
        "ST depression induced by exercise relative to rest",
        minimum=0,
        maximum=10,
    ),
    FeatureSpec(
        "slope",
        "Slope of peak exercise ST segment",
        "category",
        "Slope of the peak exercise ST segment",
        options=(Option(1, "Upsloping"), Option(2, "Flat"), Option(3, "Downsloping")),
    ),
    FeatureSpec(
        "ca",
        "Major vessels coloured by fluoroscopy",
        "number",
        "Number of major vessels (0 to 3) coloured by fluoroscopy",
        minimum=0,
        maximum=3,
    ),
    FeatureSpec(
        "thal",
        "Thallium stress test result",
        "category",
        "Thallium stress test finding",
        options=(Option(3, "Normal"), Option(6, "Fixed defect"), Option(7, "Reversible defect")),
    ),
)

LABELS: dict[str, str] = {spec.name: spec.label for spec in FEATURE_SPECS}
