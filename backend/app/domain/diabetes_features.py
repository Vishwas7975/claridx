"""Human-readable definitions of the diabetes input features.

Labels and ranges follow the Pima Indians Diabetes Database documentation.
They drive the input form in the frontend and the labels in explanations.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    label: str
    kind: str  # "number"
    description: str
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None


FEATURE_SPECS: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        "preg",
        "Number of pregnancies",
        "number",
        "Number of times pregnant",
        minimum=0,
        maximum=25,
        step=1,
    ),
    FeatureSpec(
        "plas",
        "Plasma glucose concentration",
        "number",
        "Plasma glucose concentration after a 2-hour oral glucose tolerance test",
        unit="mg/dL",
        minimum=0,
        maximum=500,
        step=1,
    ),
    FeatureSpec(
        "pres",
        "Diastolic blood pressure",
        "number",
        "Diastolic blood pressure",
        unit="mm Hg",
        minimum=0,
        maximum=300,
        step=1,
    ),
    FeatureSpec(
        "skin",
        "Triceps skinfold thickness",
        "number",
        "Triceps skinfold thickness",
        unit="mm",
        minimum=0,
        maximum=120,
        step=1,
    ),
    FeatureSpec(
        "insu",
        "2-Hour serum insulin",
        "number",
        "2-Hour serum insulin",
        unit="mu U/ml",
        minimum=0,
        maximum=1000,
        step=1,
    ),
    FeatureSpec(
        "mass",
        "Body mass index",
        "number",
        "Body mass index (weight in kg / (height in m)^2)",
        unit="kg/m^2",
        minimum=0,
        maximum=100,
        step=0.1,
    ),
    FeatureSpec(
        "pedi",
        "Diabetes pedigree function",
        "number",
        "Diabetes pedigree function (genetic risk score based on family history)",
        minimum=0.0,
        maximum=3.5,
        step=0.001,
    ),
    FeatureSpec(
        "age",
        "Age",
        "number",
        "Age in years (cohort inclusion criterion: >= 21)",
        unit="years",
        minimum=21,
        maximum=120,
        step=1,
    ),
)

LABELS: dict[str, str] = {spec.name: spec.label for spec in FEATURE_SPECS}
