# Dataset card: Heart Disease (UCI, Cleveland)

| Field | Value |
|---|---|
| Source | UCI Machine Learning Repository, dataset ID 45 |
| URL | https://archive.ics.uci.edu/dataset/45/heart-disease |
| License | CC BY 4.0 |
| Instances / features | 303 / 13 |
| Raw target | `num`, integer 0 to 4 |
| Binary target used here | 0 = absent, 1-4 = present (the convention used in published work on this data) |
| Access | `ucimlrepo.fetch_ucirepo(id=45)`, via `ml/scripts/download_heart.py` |
| Stored in Git | No. Raw data is git-ignored and re-downloaded by the script |

## Intended use

Research and education: training and explaining a risk model on public data.
Not for clinical use.

## Known limitations

- Small sample (303 rows), so metric estimates have wide confidence intervals.
- Single-source, historical data (donated 1988); not representative of any current population.
- Fairness analysis by subgroup is limited by sample size.


## Audit results (raw file)

- File `heart_disease_uci45.csv`, SHA-256 `c3855e7c0a818f03a1e90e4f23e0ad5d058dfbd1f276f1aab15d1f02693c1d0d`
  (hash of the CSV exported by our download script; informational).
- 303 rows x 14 columns, no duplicate rows.
- Missing values: `ca` 4, `thal` 2 (6 rows affected).
- Raw target counts: 0 = 164, 1 = 55, 2 = 36, 3 = 35, 4 = 13.
  Binary target: 164 absent, 139 present (45.9% positive).
- No zero or negative values in `trestbps` or `chol`; `chol` maximum of 564 is kept.
- Sex: 206 male, 97 female. `restecg = 1` occurs in only 4 rows.

## Preprocessing decisions

- Binary target: `num > 0` means disease present.
- Imputation happens inside the model pipeline and is fit on training data only:
  median for numeric features and `ca`, most frequent for categorical and binary features.
- `cp`, `restecg`, `slope`, `thal` are one-hot encoded (unknown categories ignored);
  `ca` is treated as ordinal numeric; numeric features are standardised.
- No resampling or class weights (classes are close to balanced).
- Stratified 80/20 split with seed 42. The hold-out set is used once for final
  reporting. Model comparison uses repeated stratified 5-fold CV on the training set.
- Outliers are retained.
