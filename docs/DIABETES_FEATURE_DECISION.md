# ClariDx Architecture & Clinical Decision Note: Diabetes Feature Representation

## Context & Question
Why does the ClariDx Diabetes module evaluate **Pregnancy Count (`preg`)** instead of a general demographic **Sex** field, and why was `preg` neither replaced with `sex` nor mapped to a synthetic sex indicator?

---

## 1. Why We Did Not Replace Pregnancy Count with Sex

1. **Exact Training Feature Set**:
   - The underlying machine learning models (Logistic Regression, Random Forest, Gradient Boosting, MLP) were trained on the benchmark **Pima Indians Diabetes Dataset** using exactly eight clinical and physiological features: `preg`, `plas`, `pres`, `skin`, `insu`, `mass`, `pedi`, and `age`.
2. **Dataset Demographics**:
   - The training cohort consists exclusively of females aged 21 years or older of Pima Indian heritage. The original training dataset does not contain a `Sex` variable.
3. **Feature Mismatch**:
   - Substituting `preg` with `sex` without retraining would create a fatal feature mismatch with the serialized scikit-learn pipelines, causing runtime schema failures or silent prediction errors.
4. **Invalid Equivalence**:
   - Mapping biological sex into the pregnancy field (e.g., arbitrarily encoding male as 0 pregnancies) would treat two biologically and statistically distinct concepts as equivalent. A nulliparous female (0 pregnancies) has a different hormonal and metabolic profile than a male patient; treating them identically produces mathematically invalid and clinically unsafe risk estimates.
5. **Proper Sex Inclusion Requires Retraining**:
   - Adding a true `Sex` feature properly requires selecting a representative, multi-sex diabetes cohort (such as the CDC NHANES or BRFSS datasets), retraining all four candidate models, recomputing cross-validation baselines, recalculating calibration curves, and regenerating explainability background datasets.

---

## 2. Why Retaining Pregnancy Count Helps in the Current Scenario

1. **Pipeline & Model Integrity**:
   - Preserves 100% compatibility with all serialized scikit-learn models, standard scalers, median imputers, SHAP TreeExplainer/KernelExplainer backgrounds, and LIME surrogate configurations.
2. **Deterministic Contracts & Regressions**:
   - Preserves existing Pydantic request/response schemas (`DiabetesPredictionRequest`), database models, OpenAPI specifications, frontend form contracts, and automated tests.
3. **Prevents Fabricated Data & Hallucinations**:
   - Prevents fabricated feature mappings or synthetic assumptions from contaminating clinical explanations.
4. **Transparent Clinical Limitations**:
   - Allows ClariDx to function as an academically rigorous, verifiable decision-support tool that transparently explains its dataset scope:
     - Clear UI guidance informs the clinician that the benchmark model was trained on females aged 21 and older.
     - For male patients, clinicians may enter `0` to run the mathematical model, but the application explicitly notes that this represents an off-distribution prediction and is not clinically validated for male cohorts.

---

## Summary for Examiners & Students
> "We did not substitute pregnancy with sex because the trained Pima model requires the exact eight features it was fitted on, and the cohort contains only adult females. Replacing or synthesising features without retraining corrupts model inputs and invalidates SHAP explanations. Retaining the pregnancy feature maintains complete pipeline compatibility while transparently communicating the demographic limitations of the training cohort."
