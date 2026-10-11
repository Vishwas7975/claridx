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
| 19 | Missing-data sensitivity: candidate values come only from the training data (observed codes; 5th to 95th percentile quantiles for numeric features) | No clinical values are invented; the range never leaves what the model has seen |
| 20 | Joint scenarios capped at 2000 (seeded sample beyond that, reported as `exhaustive: false`); single-feature variations always evaluated | Bounded latency and deterministic output; the overall range always contains every per-feature range |
| 21 | API keeps the field name `imputed`; clients must present imputed contributions as assumptions, and every sensitivity block carries a `note` saying so | Renaming would change the contract for no functional gain; the probability range is the primary signal |
| 22 | Sensitivity scenarios are built from real training patients' values for the missing features; supersedes the candidate-value grid and sampling cap of #19 and #20 | The grid weighted rare value combinations like common ones and ignored which values occur together; real-patient scenarios give a share-of-plausible-cases measure that can be validated against outcomes |
| 23 | The uncertainty warning fires when the share of plausible cases that are positive is between 10% and 90% (`verdict_uncertain`); the window was fixed before seeing results and is chosen, not validated | Replaces "min/max range crosses the threshold" as the trigger. Any future tuning must use cross-validation on training data, not the hold-out set |
| 24 | Known limits, stated in the API `note`: scenarios describe the training population and ignore the entered measurements; per-feature ranking varies one feature at a time and can miss interactions | Honest scope of what the ranges mean |
| 25 | Validation of #23 on masked hold-out patients (61 patients, so small counts): the warning fired for 2 of 61 (1 feature masked), 37 of 61 (3 masked) and 61 of 61 (6 masked). With 3 masked, the baseline verdict was correct for 24 of 24 patients outside the warning band but 22 of 37 inside it; with 6 masked it was correct for 33 of 61, no better than always predicting healthy (33 of 61 are healthy) | The warning identifies unreliable results; frequent firing when key features are missing reflects real uncertainty, not noise. Typical and extreme ranges were nearly identical in every example, so the UI leads with positive share and typical range |
| 26 | Request validation errors return only `loc`, `msg` and `type` (no submitted value, no `ctx`) through a custom handler | The default handler echoed the rejected value; NaN or Infinity made the error response itself fail with HTTP 500, and patient values should not be echoed back in error bodies |
| 27 | Input coercion left at Pydantic's default: numeric strings ("54") and booleans (true for sex) are accepted for integer fields | The OpenAPI contract and generated frontend types declare integers, and strict mode would also reject valid values such as 54.0. Revisit if third-party clients are added |
| 28 | Frontend: Vite + React + TypeScript (strict) from the official create-vite react-ts template, npm, ESLint; versions as scaffolded (React 19, Vite 8, TypeScript 6) | Maintained baseline that matches the installed Node 24 LTS; ESLint chosen over Oxlint for ecosystem maturity |
| 29 | The OpenAPI schema is the frontend contract: `app.export_openapi` writes the committed `frontend/openapi.json`, TypeScript types are generated from it, and a backend test fails when the file is stale | Frontend cannot call fields that do not exist; API changes surface as reviewable type diffs; the frontend builds without a running backend |
| 30 | `openapi-typescript` runs through `npm exec` with its own pinned TypeScript 5.9.3 instead of being a project dependency | Its peer range (typescript ^5.x) conflicts with the template's TypeScript 6; forcing the install would hide a possible incompatibility. Revisit when it supports TypeScript 6 |
| 31 | Number features in `GET /heart/features` declare a `step`; frontend form rules are tested against a fixture of the real specs exported from the backend (`frontend/src/test/fixtures/heart-features.json`), and a backend test fails when that file is stale | The UI cannot tell whole-number inputs from decimal ones otherwise, and form and API rules must not drift apart |
| 32 | Frontend dev server proxies `/api` to the backend on 127.0.0.1:8000, and the client uses the page origin as its base URL | The browser makes no cross-origin calls in development, whichever host is typed in, and production is the same shape behind a reverse proxy |
| 33 | Frontend quality gate: `npm run check` runs the Prettier check, ESLint, Vitest and the production build | Same discipline as the backend gates |
