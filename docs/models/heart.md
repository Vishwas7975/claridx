# Model Card: Heart Disease Risk Prediction (UCI Cleveland, ID 45)

## Protocol & Training Methodology

- **Hold-out Split**: Stratified 80/20 train/test split with `random_state=42`
  (`n_train = 242`, `n_test = 61`). The hold-out test set is held in reserve and
  evaluated once only for reporting; it is never used for model selection, threshold
  tuning, or preprocessing.
- **Cross-Validation**: 5-fold stratified cross-validation repeated 5 times (5 × 5,
  25 folds total) on the training set only (`random_state=42`).
- **Primary selection metric**: ROC-AUC on the cross-validation training set.
- **Preprocessing & Leakage Prevention**:
  - Imputation and scaling statistics are learned strictly on the training split (or
    fold training sets during cross-validation) inside a scikit-learn `Pipeline`.
  - Numeric features (`age`, `trestbps`, `chol`, `thalach`, `oldpeak`, `ca`):
    `SimpleImputer(strategy="median")` → `StandardScaler`.
  - Categorical features (`cp`, `restecg`, `slope`, `thal`): one-hot encoded;
    unknown categories at inference are silently dropped.
  - `ca` is treated as ordinal numeric (0–3), not categorical.
  - 6 rows contain missing values in the raw data (`ca`: 4 missing, `thal`: 2 missing).
    These are handled by the imputer, not dropped.
  - No resampling or class weights (positive rate ≈ 45.9%, near-balanced).

---

## Dataset

| Field | Value |
|---|---|
| Source | UCI Machine Learning Repository, dataset ID 45 (Cleveland subset) |
| URL | https://archive.ics.uci.edu/dataset/45/heart-disease |
| License | CC BY 4.0 |
| Instances | 303 |
| Features | 13 |
| Raw target | `num` (0–4); binarised as `num > 0` = disease present |
| Positive rate | 45.9% (139 present / 164 absent) |
| Train split | 242 rows |
| Test split | 61 rows |
| SHA-256 (CSV) | `c3855e7c0a818f03a1e90e4f23e0ad5d058dfbd1f276f1aab15d1f02693c1d0d` |

### Features

| Name | Type | Description | Notes |
|---|---|---|---|
| `age` | Numeric | Age in years | Range: 29–77 |
| `sex` | Binary | 0 = female, 1 = male | 97 female, 206 male |
| `cp` | Categorical | Chest pain type (1–4) | One-hot encoded |
| `trestbps` | Numeric | Resting blood pressure (mm Hg) | |
| `chol` | Numeric | Serum cholesterol (mg/dl) | Max 564 retained |
| `fbs` | Binary | Fasting blood sugar > 120 mg/dl | |
| `restecg` | Categorical | Resting ECG (0–2) | Value 1 occurs in only 4 rows |
| `thalach` | Numeric | Max heart rate achieved (bpm) | |
| `exang` | Binary | Exercise-induced angina | |
| `oldpeak` | Numeric | ST depression (exercise vs rest) | |
| `slope` | Categorical | Peak exercise ST slope (1–3) | One-hot encoded |
| `ca` | Ordinal | Major vessels coloured (0–3) | 4 missing values |
| `thal` | Categorical | Thallium test result (3/6/7) | 2 missing values |

---

## Model Comparison

### 1. Cross-Validation on Training Set (5 × 5 stratified; mean ± fold std)

| Candidate Model | ROC-AUC | Recall | F1 | Brier Score |
|---|---|---|---|---|
| `logistic_regression` | **0.894 ± 0.044** | 0.764 ± 0.072 | 0.800 ± 0.054 | 0.128 ± 0.030 |
| `random_forest` | 0.889 ± 0.041 | 0.763 ± 0.083 | 0.786 ± 0.061 | 0.134 ± 0.022 |
| `gradient_boosting` | 0.853 ± 0.044 | 0.760 ± 0.088 | 0.758 ± 0.058 | 0.166 ± 0.031 |
| `mlp` | 0.847 ± 0.055 | 0.751 ± 0.071 | 0.755 ± 0.060 | 0.191 ± 0.047 |

**Selected Model**: `logistic_regression` selected strictly by cross-validation ROC-AUC
on the training split.

> [!NOTE]
> Despite Logistic Regression having the highest mean CV ROC-AUC, Random Forest achieves
> identical hold-out accuracy and F1. Both are served via the API; Random Forest is
> the default because exact Tree SHAP (probability space) is available for it.

### 2. Hold-out Test Set Evaluation (Used once; N = 61, 28 positive, 33 negative)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | ROC-AUC 95% CI | Brier |
|---|---|---|---|---|---|---|---|
| `logistic_regression` (Selected) | 0.869 | 0.813 | 0.929 | 0.867 | **0.958** | [0.898, 0.996] | 0.085 |
| `random_forest` | 0.869 | 0.813 | 0.929 | 0.867 | 0.944 | [0.879, 0.990] | 0.104 |
| `gradient_boosting` | 0.885 | 0.839 | 0.929 | 0.881 | 0.944 | [0.872, 0.994] | 0.094 |
| `mlp` | 0.820 | 0.774 | 0.857 | 0.814 | 0.934 | [0.866, 0.983] | 0.136 |

### 3. Hold-out Confusion Matrix (`logistic_regression`)

Threshold: 0.5

| | Predicted Negative | Predicted Positive |
|---|---|---|
| **Actual Negative** | 27 (TN) | 6 (FP) |
| **Actual Positive** | 2 (FN) | 26 (TP) |

- Sensitivity (Recall): 26 / (26 + 2) = **92.9%**
- Specificity: 27 / (27 + 6) = **81.8%**
- Positive Predictive Value (Precision): 26 / (26 + 6) = **81.3%**
- Negative Predictive Value: 27 / (27 + 2) = **93.1%**

> [!CAUTION]
> The test set has only 61 rows (28 positive). Metric estimates have wide confidence
> intervals. The AUC 95% CI of [0.898, 0.996] reflects this uncertainty.
> These results must not be interpreted as validated clinical performance.

---

## Explainability

### SHAP

- **Random Forest**: Exact Tree SHAP, output space = **probability**.
- **Logistic Regression**: Linear SHAP with `shap.maskers.Independent`, output space = **log-odds**.

Feature contributions are aggregated from one-hot-encoded columns back to the original
feature names (e.g., all `cp_*` columns are summed into `cp`).

### LIME

- Local surrogate: `lime.lime_tabular.LimeTabularExplainer`.
- Background: training feature set.
- Output space: **probability** for all models.
- Fidelity (R²) reported per prediction; flagged as low confidence when R² < 0.5.

### Cross-Explainer Agreement

Spearman rank correlation, top-3 overlap, and sign agreement are computed for all models.
Agreement is meaningful when SHAP and LIME use the same output space (i.e., Random Forest).
For Logistic Regression, SHAP operates in log-odds and LIME in probability; agreement
metrics are still computed but should be interpreted cautiously.

### Sensitivity Analysis

When patient inputs are missing (NaN) or otherwise unknown, the `SensitivityAnalyzer`
samples joint values from real training patients and reports:

- `typical_low` / `typical_high`: 10th–90th percentile of predicted probabilities over
  training patterns that have non-null values for all missing features.
- `probability_min` / `probability_max`: full range.
- `verdict_uncertain`: true when 10–90% of plausible cases classify positively.
- Per-feature `FeatureImpact`: how much each individual missing feature affects the result.

---

## Served Models (API)

The API currently serves two models:

| Model | `model_name` | Default | SHAP type |
|---|---|---|---|
| Random Forest | `random_forest` | ★ yes | Tree SHAP (probability) |
| Logistic Regression | `logistic_regression` | no | Linear SHAP (log-odds) |

Gradient Boosting and MLP are trained and stored as artifacts but are not exposed by
the API in the current version.

---

## Artifact Manifest

Saved under `backend/ml/artifacts/heart/`:

| File | Contents |
|---|---|
| `background.csv` | Training feature set (N = 242) for SHAP background and sensitivity analysis |
| `logistic_regression.joblib` | Serialized scikit-learn `Pipeline` (preprocessor + LR) |
| `random_forest.joblib` | Serialized scikit-learn `Pipeline` (preprocessor + RF) |
| `gradient_boosting.joblib` | Serialized scikit-learn `Pipeline` (preprocessor + GB) |
| `mlp.joblib` | Serialized scikit-learn `Pipeline` (preprocessor + MLP) |
| `metrics.json` | CV summaries, hold-out metrics, dataset SHA-256, library versions, creation timestamp |

The `metrics.json` also records the Python, scikit-learn, Pandas, and NumPy versions
used during training for reproducibility.

---

## Limitations & Research-Only Safeguards

> [!CAUTION]
> **Research and Educational Prototype Only**
> This model is trained on a historical benchmark dataset and is **NOT** validated for
> clinical diagnosis, patient screening, or treatment selection.

1. **Small sample size.** 303 patients (242 training / 61 test). Metric estimates have
   wide confidence intervals, as reflected in the bootstrap AUC CI. Results could change
   substantially on a larger or more diverse population.

2. **Single-source historical data.** The Cleveland dataset was collected in 1988 at a
   single institution. It is not representative of current clinical populations, diverse
   demographics, or modern diagnostic equipment.

3. **Missing values.** Six rows (2%) have missing values in the raw data. The imputation
   strategy (training median for numeric, most frequent for categorical) is a simplifying
   assumption, not a clinically validated approach.

4. **Class imbalance not addressed.** Positive rate ≈ 45.9%; no resampling or class
   weighting was applied. The model may perform differently on populations with
   substantially different prevalence.

5. **Uncalibrated probabilities.** Predicted probabilities are raw sigmoid/softmax outputs.
   They are **not** calibrated against real-world base rates. All API responses carry
   `"calibrated": false`. Do not interpret the probability as a population-validated
   risk score.

6. **No fairness analysis.** The dataset has 97 female and 206 male subjects. Subgroup
   performance by sex, age, or other demographics has not been evaluated.

7. **Feature encoding limitations.** `restecg = 1` occurs in only 4 training rows.
   The model's handling of this value is unreliable.
