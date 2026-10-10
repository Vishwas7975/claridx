"""Print a factual audit of the raw Heart Disease data. Changes nothing."""

import pandas as pd

from ml.datasets.heart import RAW_FILE, TARGET_RAW, load_raw, sha256_of

NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL = ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"]


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    df = load_raw()

    section("File")
    print(RAW_FILE.name)
    print(sha256_of(RAW_FILE))

    section("Shape (rows, columns)")
    print(df.shape)

    section("Columns and dtypes")
    print(df.dtypes.to_string())

    expected = set(NUMERIC + CATEGORICAL + [TARGET_RAW])
    section("Column check")
    print("missing from file:", sorted(expected - set(df.columns)) or "none")
    print("unexpected extras:", sorted(set(df.columns) - expected) or "none")

    section("Missing values")
    missing = df.isna().sum()
    if missing.sum() == 0:
        print("none")
    else:
        print(missing[missing > 0].to_string())
        print("rows with any missing value:", int(df.isna().any(axis=1).sum()))

    section("Duplicate rows")
    print(int(df.duplicated().sum()))

    if TARGET_RAW in df.columns:
        section(f"Target '{TARGET_RAW}' raw distribution (0 = absent, 1-4 = present)")
        print(df[TARGET_RAW].value_counts(dropna=False).sort_index().to_string())
        section("Binary target (present = 1)")
        binary = (df[TARGET_RAW] > 0).astype(int)
        print(binary.value_counts().sort_index().to_string())
        print("positive rate:", round(float(binary.mean()), 3))

    section("Numeric features: count / min / mean / max")
    present_numeric = [col for col in NUMERIC if col in df.columns]
    print(df[present_numeric].describe().T[["count", "min", "mean", "max"]].round(2).to_string())

    section("Implausible zeros (<= 0) in blood pressure / cholesterol")
    for col in ("trestbps", "chol"):
        if col in df.columns:
            print(col, int((df[col] <= 0).sum()))

    section("Categorical value counts")
    for col in CATEGORICAL:
        if col in df.columns:
            counts = df[col].value_counts(dropna=False).sort_index().to_dict()
            print(f"{col}: {counts}")


if __name__ == "__main__":
    pd.set_option("display.width", 120)
    main()
