"""Explain hold-out predictions with SHAP and LIME and measure how well they agree."""

from collections import defaultdict

import joblib
import numpy as np

from ml.explain import Explanation, LimeExplainer, ShapExplainer, compare
from ml.paths import ARTIFACTS_DIR
from ml.splits import heart_split

ARTIFACT_DIR = ARTIFACTS_DIR / "heart"
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
    X_train, X_test, _, y_test = heart_split()

    for name in ("random_forest", "logistic_regression"):
        model = joblib.load(ARTIFACT_DIR / f"{name}.joblib")
        shap_explainer = ShapExplainer(model, X_train)
        lime_explainer = LimeExplainer(model, X_train)

        print(f"\n===== {name} =====")
        first = X_test.iloc[[0]]
        probability = model.predict_proba(first)[0, 1]
        print(f"Test patient 0: P(disease) = {probability:.3f}, actual = {int(y_test.iloc[0])}")
        show(shap_explainer.explain(first))
        show(lime_explainer.explain(first))

        rho, overlap, signs, fidelity = [], [], [], []
        importance: dict[str, float] = defaultdict(float)
        for i in range(len(X_test)):
            patient = X_test.iloc[[i]]
            shap_result = shap_explainer.explain(patient)
            lime_result = lime_explainer.explain(patient)
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
        print(f"\nSHAP vs LIME agreement over {n} hold-out patients (top-{agreement.k}):")
        print(f"  mean rank correlation of magnitudes: {np.mean(rho):.2f}")
        print(f"  mean top-{agreement.k} overlap:              {np.mean(overlap):.2f}")
        print(f"  mean sign agreement in top-{agreement.k}:    {np.mean(signs):.2f}")
        print(f"  mean LIME local fit R2:              {np.mean(fidelity):.2f}")

        unit = shap_explainer.output_space
        print(f"\nGlobal importance (mean |SHAP|, {unit}), top 6:")
        for feature, value in sorted(importance.items(), key=lambda kv: -kv[1])[:6]:
            print(f"  {value:.3f}  {feature}")


if __name__ == "__main__":
    main()
