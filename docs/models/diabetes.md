# Model Card: Diabetes Risk Prediction (Pima Indians, OpenML ID 37)

## Protocol & Training Methodology

- **Hold-out Split**: Stratified 80/20 train/test split with `random_state=42` (`n_train = 614`, `n_test = 154`). The hold-out test set is held in reserve and evaluated once only for reporting; it is never used for model selection, threshold tuning, or preprocessing.
- **Cross-Validation**: 5-fold stratified cross-validation repeated 5 times ($5 \times 5$, 25 folds total) on the training set only (`random_state=42`).
- **Preprocessing & Leakage Prevention**:
  - Imputation and scaling statistics are learned strictly on the training split (or fold training sets during cross-validation) inside a scikit-learn `Pipeline`.
  - Continuous physiological features with biologically implausible zeros (`plas`, `pres`, `skin`, `insu`, `mass`) are converted to `NaN` in a stateless preprocessing step prior to median imputation.
  - Features where zero is biologically valid (`preg`) retain zero values without replacement.
  - All features are standardized (`StandardScaler`) following imputation.

---

## Model Comparison

### 1. Cross-Validation on Training Set ($5 \times 5$ stratified; mean $\pm$ fold std)

| Candidate Model | ROC-AUC | Recall | F1 | Brier Score |
|---|---|---|---|---|
| `logistic_regression` | **0.842 $\pm$ 0.029** | 0.582 $\pm$ 0.071 | 0.651 $\pm$ 0.056 | 0.152 $\pm$ 0.015 |
| `random_forest` | 0.827 $\pm$ 0.033 | 0.574 $\pm$ 0.070 | 0.621 $\pm$ 0.053 | 0.160 $\pm$ 0.014 |
| `gradient_boosting` | 0.823 $\pm$ 0.029 | 0.593 $\pm$ 0.062 | 0.622 $\pm$ 0.050 | 0.166 $\pm$ 0.017 |
| `mlp` | 0.773 $\pm$ 0.043 | 0.580 $\pm$ 0.078 | 0.588 $\pm$ 0.063 | 0.245 $\pm$ 0.036 |

**Selected Model**: `logistic_regression` selected strictly by cross-validation ROC-AUC on the training split.

### 2. Hold-out Test Set Evaluation (Used once; $N=154$, 54 positives, 100 negatives)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | ROC-AUC 95% CI | Brier |
|---|---|---|---|---|---|---|---|
| `logistic_regression` (Selected) | 0.708 | 0.600 | 0.500 | 0.545 | 0.813 | [0.74, 0.87] | 0.175 |
| `random_forest` | 0.740 | 0.646 | 0.574 | 0.608 | 0.811 | [0.74, 0.87] | 0.167 |
| `gradient_boosting` | 0.779 | 0.717 | 0.611 | 0.660 | 0.831 | [0.76, 0.89] | 0.164 |
| `mlp` | 0.721 | 0.612 | 0.556 | 0.583 | 0.777 | [0.70, 0.85] | 0.233 |

### 3. Hold-out Confusion Matrix (`logistic_regression`)

Threshold: $0.5$

| Metric | Count | Rate (% of test set) |
|---|---|---|
| True Negatives (TN) | 82 | 53.2% |
| False Positives (FP) | 18 | 11.7% |
| False Negatives (FN) | 27 | 17.5% |
| True Positives (TP) | 27 | 17.5% |
| **Total** | **154** | **100.0%** |

- Specificity: $82 / (82 + 18) = 82.0\%$
- Sensitivity (Recall): $27 / (27 + 27) = 50.0\%$
- Positive Predictive Value (Precision): $27 / (27 + 18) = 60.0\%$

---

## Artifact Manifest

Saved under `backend/ml/artifacts/diabetes/`:
- `background.csv`: Training feature set ($N=614$) used for explainer background generation without raw dataset dependency.
- `logistic_regression.joblib`: Persisted scikit-learn pipeline for primary reference model.
- `random_forest.joblib`: Persisted scikit-learn pipeline for non-linear tree model.
- `gradient_boosting.joblib`: Persisted gradient boosted trees pipeline.
- `mlp.joblib`: Persisted multi-layer perceptron pipeline.
- `metrics.json`: Complete record of hyperparameters, environment versions, CV summaries, hold-out metrics, and confusion matrix.

---

## Limitations & Research-Only Safeguards

> [!CAUTION]
> **Research and Educational Prototype Only**
> This model is trained on a historical benchmark dataset and is NOT validated for clinical diagnosis, patient screening, or treatment selection.

1. **Demographic Specificity**: All subjects in the historical dataset are females $\ge 21$ years of Pima Indian heritage near Phoenix, Arizona. Performance cannot be generalized to broader ethnic, gender, or modern age distributions.
2. **Heavy Imputation**: Insulin (`insu`) is unrecorded in $48.7\%$ of cases, and triceps skinfold (`skin`) in $29.6\%$. The model relies substantially on training median assumptions for these variables.
3. **No Clinical Readiness**: Metrics represent baseline machine learning benchmarks on tabular historical data, not calibrated clinical risk estimates.
