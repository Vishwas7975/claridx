# ClariDx

**Clinical AI you can see through.**

ClariDx is an explainable clinical decision support system. It predicts disease
risk from patient data and shows the reasoning behind every prediction using
SHAP, LIME and counterfactual explanations, with calibrated uncertainty, so a
clinician can verify the output instead of trusting a black box.

> **Medical disclaimer:** ClariDx is a decision-support and educational project.
> It is not a medical device and must not be used for real diagnosis or
> treatment. It is trained only on public research datasets.

## Status

Under active development. The system serves explainable predictions for both Heart Disease
and Diabetes (SHAP, LIME, cross-explainer agreement, and missing-data sensitivity) across
backend and frontend.

## Planned features

- Multi-model training and comparison (Random Forest, Gradient Boosting, MLP, baseline)
- SHAP and LIME explanations side by side, with an agreement score
- Counterfactual "what-if" analysis
- Calibrated probabilities and conformal uncertainty
- Missing-data handling that flags imputed values
- Plain-language explanations and clinical-range context
- PDF reports, audit log, model card and fairness checks
- Role-based access (doctor, admin)

## Tech stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, MySQL 8
- **ML and XAI:** scikit-learn, XGBoost/LightGBM, SHAP, LIME, DiCE, MAPIE, MLflow
- **Frontend:** React, Vite, TypeScript, Tailwind CSS, shadcn/ui
- **Tooling:** uv, Ruff, pytest, ESLint, GitHub Actions

## Repository layout

    claridx/
      backend/    FastAPI service and ML/XAI pipelines
      frontend/   React application
      docs/       Architecture notes, decisions, model cards

## License

MIT
