"""Explain diabetes hold-out predictions with SHAP and LIME and measure how well they agree."""

from collections import defaultdict

import joblib
import numpy as np
import pandas as pd

from ml.explain import Explanation, LimeExplainer, ShapExplainer, compare
from ml.paths import ARTIFACTS_DIR
from ml.pipelines.diabetes import (
    FEATURES as DIABETES_FEATURES,
)
from ml.pipelines.diabetes import (
    SUSPICIOUS_ZERO_FEATURES,
)
from ml.splits import diabetes_split

ARTIFACT_DIR = ARTIFACTS_DIR / "diabetes"
TOP = 5


def show(explanation: Explanation) -> None:
    header = f"  {explanation.method.upper()} ({explanation.output_space})"
    if explanation.base_value is not None:
        header += f", base value {explanation.base_value:+.3f}"
    if explanation.fidelity is not None:
        header += f", local fit R2 {explanation.fidelity:.2f}"
    print(header)
    for item in explanation.contributions[:TOP]:
        shown = "missing" if item.value is None else f"{item.value:g}"
        flag = " (imputed)" if item.imputed else ""
        print(f"    {item.contribution:+.3f}  {item.feature} = {shown}{flag}")


def main() -> None:
    background_path = ARTIFACT_DIR / "background.csv"
    if not background_path.exists():
        raise FileNotFoundError(
            f"Background sample missing at {background_path}. "
            "Run: uv run python -m ml.scripts.train_diabetes"
        )
    background = pd.read_csv(background_path)
    if list(background.columns) != DIABETES_FEATURES:
        raise ValueError(
            f"Unexpected background schema. Expected {DIABETES_FEATURES}, "
            f"got {list(background.columns)}"
        )

    _, X_test, _, y_test = diabetes_split()

    for name in ("logistic_regression", "random_forest"):
        model_path = ARTIFACT_DIR / f"{name}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model artifact {model_path} missing. "
                "Run: uv run python -m ml.scripts.train_diabetes"
            )
        model = joblib.load(model_path)

        shap_explainer = ShapExplainer(
            model,
            background,
            features=DIABETES_FEATURES,
            zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
        )
        lime_explainer = LimeExplainer(
            model,
            background,
            features=DIABETES_FEATURES,
            zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
            class_names=["tested_negative", "tested_positive"],
        )

        print(f"\n===== {name} =====")
        first = X_test.iloc[[0]]
        probability = model.predict_proba(first)[0, 1]
        print(
            f"Test patient 0: P(diabetes) = {probability:.3f}, "
            f"actual target = {int(y_test.iloc[0])}"
        )
        show(shap_explainer.explain(first))
        show(lime_explainer.explain(first))

        rho, overlap, signs, fidelity = [], [], [], []
        importance: dict[str, float] = defaultdict(float)
        additivity_verified = True

        for i in range(len(X_test)):
            patient = X_test.iloc[[i]]
            shap_result = shap_explainer.explain(patient)
            lime_result = lime_explainer.explain(patient)

            # Check mathematical additivity against model output:
            total_shap = shap_result.base_value + sum(
                item.contribution for item in shap_result.contributions
            )
            if shap_result.output_space == "probability":
                if abs(total_shap - shap_result.probability) >= 1e-6:
                    additivity_verified = False
            elif shap_result.output_space == "log_odds":
                p = shap_result.probability
                p_clamped = np.clip(p, 1e-15, 1.0 - 1e-15)
                logit = np.log(p_clamped / (1.0 - p_clamped))
                if abs(total_shap - logit) >= 1e-5:
                    additivity_verified = False

            agreement = compare(shap_result, lime_result)
            if agreement.rank_correlation is not None:
                rho.append(agreement.rank_correlation)
            overlap.append(agreement.top_k_overlap)
            signs.append(agreement.sign_agreement)
            if lime_result.fidelity is not None:
                fidelity.append(lime_result.fidelity)
            for item in shap_result.contributions:
                importance[item.feature] += abs(item.contribution) / len(X_test)

        n = len(X_test)
        print(f"SHAP additivity verified across all {n} hold-out patients: {additivity_verified}")
        print(f"\nSHAP vs LIME agreement over {n} hold-out patients (top-{agreement.k}):")
        print(f"  mean rank correlation of magnitudes: {np.mean(rho):.2f}")
        print(f"  mean top-{agreement.k} overlap:              {np.mean(overlap):.2f}")
        print(f"  mean sign agreement in top-{agreement.k}:    {np.mean(signs):.2f}")
        print(f"  mean LIME local fit R2:              {np.mean(fidelity):.2f}")

        unit = shap_explainer.output_space
        print(f"\nGlobal importance (mean |SHAP|, {unit}), top 8:")
        for feature, value in sorted(importance.items(), key=lambda kv: -kv[1]):
            print(f"  {value:.3f}  {feature}")


if __name__ == "__main__":
    main()
