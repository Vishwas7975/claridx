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
