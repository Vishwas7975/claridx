"""Print a factual audit of the raw Diabetes data. Changes nothing."""

import pandas as pd

from ml.datasets.diabetes import (
    EXPECTED_COLUMNS,
    FEATURES,
    RAW_FILE,
    TARGET_RAW,
    ZERO_AS_MISSING,
    load_raw,
    sha256_of,
)


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

    section("Column check")
    print("missing from file:", sorted(EXPECTED_COLUMNS - set(df.columns)) or "none")
    print("unexpected extras:", sorted(set(df.columns) - EXPECTED_COLUMNS) or "none")

    section("Missing values (NaNs)")
    missing = df.isna().sum()
    if missing.sum() == 0:
        print("none")
    else:
        print(missing[missing > 0].to_string())
        print("rows with any missing value:", int(df.isna().any(axis=1).sum()))

    section("Duplicate rows")
    print(int(df.duplicated().sum()))

    if TARGET_RAW in df.columns:
        section(f"Target '{TARGET_RAW}' raw distribution")
        print(df[TARGET_RAW].value_counts(dropna=False).to_string())
        section("Binary target (tested_positive = 1)")
        binary = (df[TARGET_RAW] == "tested_positive").astype(int)
        print(binary.value_counts().sort_index().to_string())
        print("positive rate:", round(float(binary.mean()), 3))

    section("Numeric features: count / min / mean / max")
    present_features = [col for col in FEATURES if col in df.columns]
    print(df[present_features].describe().T[["count", "min", "mean", "max"]].round(2).to_string())

    section("Zero-value audit (physiologically implausible zeros)")
    total_rows = len(df)
    for col in ZERO_AS_MISSING:
        if col in df.columns:
            zero_count = int((df[col] == 0).sum())
            pct = (zero_count / total_rows) * 100 if total_rows else 0.0
            print(f"{col:6s}: {zero_count:3d} zeros ({pct:5.1f}%)")


if __name__ == "__main__":
    pd.set_option("display.width", 120)
    main()
