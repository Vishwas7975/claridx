# Dataset card: Diabetes (Pima Indians, OpenML ID 37)

| Field | Value |
|---|---|
| Source | OpenML dataset ID 37 (version 1), Pima Indians Diabetes Database |
| URL | https://www.openml.org/d/37 (legacy UCI: https://archive.ics.uci.edu/ml/datasets/pima+indians+diabetes) |
| License | Public (OpenML license field; cite per UCI attribution policy) |
| Instances / features | 768 / 8 |
| Raw target | `class`, categorical: `tested_negative` / `tested_positive` |
| Binary target used here | 0 = `tested_negative` (500 instances), 1 = `tested_positive` (268 instances, 34.9% positive) |
| Access | `sklearn.datasets.fetch_openml(data_id=37)`, via `ml/scripts/download_diabetes.py` |
| Stored in Git | No. Raw data is git-ignored and re-downloaded by the script |

> [!NOTE]
> UCI dataset ID 34 (titled "Diabetes" on the modern UCI repository) is a different time-series insulin records dataset by Michael Kahn (1994). The Pima Indians Diabetes benchmark dataset is distributed via OpenML ID 37.

## Intended use

Research and education: training and explaining a risk model on public benchmark data.
Not for clinical use.

## Known limitations

- Historical sample (collected up to 1990, donated by Vincent Sigillito, Johns Hopkins APL).
- Homogeneous population: all patients are females at least 21 years old of Pima Indian heritage near Phoenix, Arizona. Findings cannot be generalized to broader or diverse modern patient populations.
- Moderate sample size (768 rows), with class imbalance (34.9% positive).
- Pervasive missing values encoded as zeros in five continuous physiological variables where zero is biologically impossible.

## Audit results (raw file)

- File `diabetes_openml37.csv`, SHA-256 `3da6d7849e3faeaec68309a79b4f4a12c776a752d286f7f20ae644252ce6d029` (hash of the CSV exported by our download script; informational).
- 768 rows × 9 columns, 0 duplicate rows, 0 explicit null/NaN entries in raw format.
- Raw target distribution:
  - `tested_negative`: 500 (65.1%)
  - `tested_positive`: 268 (34.9%)
- Zero-value audit (physiologically implausible zeros representing unmeasured features):
  - `plas` (plasma glucose): 5 zeros (0.7%)
  - `pres` (diastolic blood pressure): 35 zeros (4.6%)
  - `skin` (triceps skin fold thickness): 227 zeros (29.6%)
  - `insu` (2-hour serum insulin): 374 zeros (48.7%)
  - `mass` (BMI): 11 zeros (1.4%)
  - `preg` (number of pregnancies): zeros are biologically valid (0–17 pregnancies).
  - `pedi` (diabetes pedigree function): min 0.078, no zeros.
  - `age`: min 21, max 81, no zeros.

## Preprocessing decisions (planned for Checkpoint 11b)

- Raw loader preserves all raw values exactly as distributed (no premature zero replacement or imputation at ingestion time).
- In the modeling pipeline (Checkpoint 11b), values of 0 in `["plas", "pres", "skin", "insu", "mass"]` will be treated as missing and imputed strictly using statistics learned on the training split.
- Stratified 80/20 train/test split with fixed random seed 42, deterministic and disjoint.
- Continuous features will be scaled within the scikit-learn pipeline after imputation.
