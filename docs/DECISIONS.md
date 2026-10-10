# Architecture decisions

Short record of decisions and the reasons behind them.

| # | Decision | Reason |
|---|----------|--------|
| 1 | Python 3.12, pinned with uv | ML/XAI libraries (shap, numba, xgboost) lag newest Python releases; system Python is left untouched |
| 2 | MySQL 8 (not PostgreSQL) | Team familiarity; data is plain relational; JSON column covers explanation payloads |
| 3 | FastAPI | Async, typed, automatic OpenAPI docs, Pydantic validation |
| 4 | SQLAlchemy 2 + Alembic | Portable schema with versioned migrations |
| 5 | Public research datasets only | No real patient data, no privacy exposure |
| 6 | Project lives in the WSL filesystem | File I/O is much faster than on /mnt/c |
| 7 | ML dependencies in a separate uv group (`ml`) | The API image can skip them (`uv sync --no-group ml`) |
| 8 | Evaluation protocol: stratified 80/20 split, repeated 5x5 CV for selection, hold-out used once | 303 rows; avoids optimistic estimates and test-set reuse |
| 9 | No hyperparameter tuning and no XGBoost in v1 | Tuning on 242 rows mostly overfits CV folds; extra dependency, no expected gain |
| 10 | Random Forest = primary model to explain; Logistic Regression = glass-box reference | CV AUC is tied; LR coefficients let us validate SHAP/LIME against known reasoning |
| 11 | SHAP contributions are summed from one-hot columns back onto the 13 input features | Clinicians reason about "chest pain type", not `cp_4.0`; summing preserves additivity |
| 12 | Every explanation carries its `output_space` (probability or log-odds) | Prevents the UI from mislabelling units; RF and LR SHAP values are not on the same scale |
| 13 | SHAP vs LIME compared by rank correlation, top-k overlap and sign agreement, not raw magnitude | The two methods' magnitudes are not comparable; LIME fidelity (R2) is always reported |
| 14 | Dependency groups: `ml` = runtime ML libraries (the API needs them), `train` = training-only (`ucimlrepo`) | Supersedes #7: the API now serves models, so it needs the `ml` group |
| 15 | Per-disease routes (`/api/v1/heart/...`) with per-disease schemas | Inputs differ per disease; adding Diabetes later will not break existing contracts |
| 16 | Models are loaded once at startup; if artifacts are missing the API still starts and predictions return 503 | Health checks and other routes stay available |
| 17 | Strict patient input: unknown fields rejected, at least 7 of 13 measurements required | Typos must not become silent "missing" values; near-empty inputs give meaningless predictions |
| 18 | Serving uses `background.csv` saved with the model artifacts, not the raw dataset | Deployments must not depend on a dataset download |
