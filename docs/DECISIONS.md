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
