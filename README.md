# ClariDx — Explainable AI Models for Transparent Clinical Decision Support

> **Medical disclaimer:** ClariDx is a decision-support and educational prototype.
> It is **not** a medical device and must **not** be used for real diagnosis, treatment,
> or clinical decision-making. All predictions are experimental outputs of models trained
> on small, public research datasets. They do not constitute professional medical advice.

---

## Table of Contents

1. [Project overview](#1-project-overview)
2. [Objectives and scope](#2-objectives-and-scope)
3. [Features implemented](#3-features-implemented)
4. [Technology stack](#4-technology-stack)
5. [Architecture and project structure](#5-architecture-and-project-structure)
6. [Machine-learning methodology](#6-machine-learning-methodology)
7. [Explainability and limitations](#7-explainability-and-limitations)
8. [Authentication and roles](#8-authentication-and-roles)
9. [Installation and setup](#9-installation-and-setup)
10. [Running tests and quality checks](#10-running-tests-and-quality-checks)
11. [API documentation](#11-api-documentation)
12. [Configuration reference](#12-configuration-reference)
13. [Troubleshooting](#13-troubleshooting)
14. [Known limitations and future work](#14-known-limitations-and-future-work)
15. [References and acknowledgements](#15-references-and-acknowledgements)

---

## 1. Project overview

### What is ClariDx?

ClariDx is a clinical decision-support system built as a final-year B.Tech project.
It predicts disease risk from patient measurements and, critically, explains every prediction
in terms of the individual input features — showing which measurements pushed the result
toward or away from a positive diagnosis, and how uncertain the result is when key
measurements are missing.

### The problem

Modern machine-learning classifiers can achieve high predictive accuracy but behave as black
boxes: a doctor receives a risk score without understanding why. In a clinical context this is
unacceptable — a clinician must be able to verify a model's reasoning before acting on it.

ClariDx addresses this by applying two complementary explainability frameworks (SHAP and LIME)
to every prediction and displaying their outputs side by side, together with a quantitative
measure of how closely they agree. When inputs are incomplete, the system quantifies the
probability range over plausible values rather than silently imputing and presenting false
precision.

### What the system does

- Accepts patient measurements and predicts the probability of **heart disease** or **diabetes**.
- Explains every prediction at the feature level using **SHAP** and **LIME**.
- Flags imputed features and shows a **sensitivity range** when measurements are missing.
- Warns when entered values are outside the range seen in training data.
- Provides a **React-based clinical dashboard** for interactive exploration.
- Restricts prediction access to authenticated **Doctor** and **Admin** accounts.

### What the system does not do

- It does not make clinical diagnoses.
- It does not replace professional medical judgment.
- It has not been validated on real patients.
- Probabilities are **raw (uncalibrated)** model outputs. All responses carry `"calibrated": false`.
- It does not support PDF report generation, audit logging, or server-side token revocation (future work).

---

## 2. Objectives and scope

These objectives are grounded in the project proposal:

| Objective | Status |
|---|---|
| Predictive modelling for heart disease | ✅ Implemented |
| Predictive modelling for diabetes | ✅ Implemented |
| Multiple ML algorithms (LR, RF, GB, MLP) | ✅ Implemented |
| SHAP explanations | ✅ Implemented |
| LIME explanations | ✅ Implemented |
| Feature-level contribution display | ✅ Implemented |
| Incomplete / missing patient data handling | ✅ Implemented |
| Sensitivity analysis for uncertain inputs | ✅ Implemented |
| Clinical decision-support dashboard | ✅ Implemented |
| Transparent presentation of limitations | ✅ Implemented |
| Calibrated probability scores | 🔲 Future work |
| Counterfactual / what-if analysis | 🔲 Future work |
| PDF report generation | 🔲 Future work |
| Fairness / subgroup analysis | 🔲 Future work |
| Audit log | 🔲 Future work |

---

## 3. Features implemented

### Disease workflows

- **Heart disease** — UCI Cleveland dataset (303 patients, 13 features).
- **Diabetes** — Pima Indians Diabetes Database via OpenML ID 37 (768 patients, 8 features).

### Machine-learning models

Both workflows expose four models selectable via the `model_name` request field:

| Model | Heart (default ★) | Diabetes (default ★) |
|---|---|---|
| Random Forest | ★ primary | available |
| Logistic Regression | available | ★ primary |
| Gradient Boosting | available | available |
| MLP | available | available |

The default model in each workflow is selected by the highest cross-validation ROC-AUC.

### Model evaluation

- Selection: repeated stratified 5×5 cross-validation ROC-AUC on the training set only.
- Hold-out: 80/20 stratified split evaluated once, after model selection.
- 95% bootstrap confidence interval for hold-out AUC (1 000 resamples).
- All metrics persisted in `backend/ml/artifacts/{heart,diabetes}/metrics.json`.

Selected performance (from persisted artifacts — not claimed clinical accuracy):

| Condition | Selected model | CV AUC | Hold-out AUC |
|---|---|---|---|
| Heart disease | Logistic Regression | 0.894 ± 0.044 | 0.958 |
| Diabetes | Logistic Regression | 0.842 ± 0.029 | 0.813 |

### SHAP explanations

- **Tree SHAP** (probability space) for Random Forest and Gradient Boosting.
- **Linear SHAP** (log-odds space) for Logistic Regression and MLP.
- Contributions aggregated from one-hot columns back to original feature names.
- Imputed features flagged with `imputed: true` in the response.

### LIME explanations

- Local surrogate model built for each individual prediction.
- R² fidelity score reported; `low_confidence: true` when R² < 0.5.

### Cross-explainer agreement

- Spearman rank correlation of |contribution| magnitudes.
- Top-3 feature overlap and sign agreement.
- Disabled for Logistic Regression on diabetes (SHAP log-odds vs LIME probability spaces).

### Missing-data and sensitivity analysis

- Training-time: median imputation inside scikit-learn pipelines (no data leakage).
- Inference-time: when inputs are missing or entered as physiologically suspicious zeros
  (diabetes dataset), the system samples plausible values from training patients and
  reports the resulting probability range (10th–90th percentile, min, max).
- Clinician-facing warnings for imputed values, out-of-distribution inputs, and uncertain verdicts.

### Authentication and access control

- JWT bearer tokens (HS256, default 30-minute expiry).
- Argon2id password hashing.
- Roles: **Admin**, **Doctor**, **Researcher**.
- Prediction endpoints require Doctor or Admin.
- Researcher accounts: metadata only (no predictions).
- Secure admin-provisioning CLI.

### Public endpoints (no token required)

| Endpoint | Description |
|---|---|
| `GET /api/v1/health` | API liveness probe |
| `GET /api/v1/health/db` | Database readiness probe |
| `GET /api/v1/heart/features` | Heart disease feature definitions |
| `GET /api/v1/heart/models` | Available heart models and descriptions |
| `GET /api/v1/diabetes/features` | Diabetes feature definitions |
| `GET /api/v1/diabetes/models` | Available diabetes models and descriptions |

---

## 4. Technology stack

### Runtime environment

| Component | Technology | Version |
|---|---|---|
| Backend language | Python | ≥ 3.12, < 3.13 |
| Frontend language | TypeScript | ~6.0 |
| Node.js (frontend tooling) | Node.js | ≥ 22 (24 recommended) |

### Backend runtime dependencies

| Library | Purpose |
|---|---|
| FastAPI | Web framework and OpenAPI generation |
| Uvicorn | ASGI server |
| SQLAlchemy 2 | ORM, connection pooling |
| Alembic | Database schema migrations |
| PyMySQL | MySQL driver |
| Pydantic / pydantic-settings | Validation and configuration |
| PyJWT | JWT token creation and validation |
| pwdlib[argon2] | Argon2id password hashing |
| python-multipart | Form body parsing |
| cryptography | TLS/SSL support for PyMySQL |

### ML and XAI dependencies

| Library | Purpose |
|---|---|
| scikit-learn | Pipelines, classifiers, cross-validation, imputation |
| NumPy | Numerical arrays |
| Pandas | DataFrames and feature engineering |
| SciPy | Spearman correlation for agreement metrics |
| SHAP | Tree SHAP and Linear SHAP explanations |
| LIME | Local surrogate explanations |
| joblib | Model serialization |

### Training-only dependencies

| Library | Purpose |
|---|---|
| ucimlrepo | UCI heart disease dataset download |

### Frontend runtime dependencies

| Library | Purpose |
|---|---|
| React 19 | UI component framework |
| openapi-fetch | Type-safe API client |
| @tanstack/react-query | Async state and caching |

### Frontend development tools

| Tool | Purpose |
|---|---|
| Vite 8 | Dev server and bundler |
| Vitest 5 | Test runner |
| @testing-library/react | Component testing |
| ESLint 10 + typescript-eslint | Linting |
| Prettier 3 | Formatting |
| openapi-typescript | Generates `schema.d.ts` from `openapi.json` |

### Backend development tools

| Tool | Purpose |
|---|---|
| uv | Python package and virtualenv manager |
| Ruff | Linting and formatting |
| pytest + pytest-cov | Testing and coverage |
| httpx2 | HTTP client for API integration tests |

### Styling

Vanilla CSS with CSS custom properties. No CSS framework is used.

### Database

MySQL 8. All schema changes are managed through Alembic migrations.

---

## 5. Architecture and project structure

### Repository layout

```
claridx/
├── README.md                      ← You are here (authoritative project README)
├── SETUP_AND_TESTING.md           ← Step-by-step installation and testing guide
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py            ← Shared deps: auth, RBAC, registry accessors
│   │   │   └── v1/
│   │   │       ├── auth.py        ← POST /login, GET /me
│   │   │       ├── heart.py       ← Heart disease endpoints
│   │   │       ├── diabetes.py    ← Diabetes endpoints
│   │   │       ├── health.py      ← Liveness + readiness probes
│   │   │       └── router.py      ← Router assembly
│   │   ├── cli/
│   │   │   └── create_user.py     ← Secure user provisioning CLI
│   │   ├── core/
│   │   │   ├── config.py          ← Settings (reads backend/.env)
│   │   │   ├── database.py        ← SQLAlchemy engine and session factory
│   │   │   └── security.py        ← JWT and Argon2id utilities
│   │   ├── domain/
│   │   │   ├── heart_features.py  ← Feature specs (labels, ranges, options)
│   │   │   └── diabetes_features.py
│   │   ├── models/
│   │   │   └── user.py            ← User ORM model and UserRole enum
│   │   ├── schemas/
│   │   │   ├── auth.py            ← Login, token, profile schemas
│   │   │   ├── heart.py           ← Heart prediction request/response
│   │   │   └── diabetes.py        ← Diabetes prediction request/response
│   │   ├── services/
│   │   │   ├── model_registry.py      ← Loads heart models at startup
│   │   │   ├── diabetes_registry.py   ← Loads diabetes models at startup
│   │   │   ├── heart_prediction.py    ← Prediction + explanation orchestration
│   │   │   └── diabetes_prediction.py
│   │   ├── export_openapi.py      ← Exports openapi.json for frontend
│   │   └── main.py                ← FastAPI app factory, CORS, lifespan
│   ├── ml/
│   │   ├── config.py              ← Constants (seed, thresholds, CV settings)
│   │   ├── datasets/              ← Dataset download and loading
│   │   ├── explain/               ← SHAP, LIME, agreement, feature utilities
│   │   ├── pipelines/             ← Feature definitions, preprocessors, models
│   │   ├── scripts/               ← Download, train, audit, explain scripts
│   │   ├── artifacts/
│   │   │   ├── heart/             ← *.joblib, background.csv, metrics.json
│   │   │   └── diabetes/
│   │   ├── evaluation.py          ← CV, hold-out evaluation, bootstrap CI
│   │   ├── sensitivity.py         ← Missing-data sensitivity analysis
│   │   └── splits.py              ← Deterministic train/test split functions
│   ├── migrations/                ← Alembic migration scripts
│   ├── tests/                     ← Pytest test suite
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── uv.lock
│
├── frontend/
│   ├── DEVELOPMENT.md             ← Frontend developer guide and api:sync workflow
│   ├── src/
│   │   ├── api/                   ← API client, types, error handling
│   │   ├── features/
│   │   │   ├── auth/              ← AuthContext, LoginForm, ResearcherNotice
│   │   │   ├── heart/             ← Prediction page, patient form, results
│   │   │   └── diabetes/          ← (mirrors heart/)
│   │   ├── components/            ← Shared UI components
│   │   ├── test/                  ← Test fixtures and setup
│   │   ├── App.tsx                ← Root component and auth gate
│   │   └── index.css              ← Global CSS (custom properties, layout)
│   ├── openapi.json               ← Exported schema (committed, regenerate with api:sync)
│   ├── vite.config.ts             ← Vite + Vitest config (proxy: /api → :8000)
│   └── package.json
│
└── docs/
    ├── DECISIONS.md               ← Architecture Decision Records (ADRs 1–39)
    ├── datasets/
    │   ├── heart_disease.md       ← Dataset card: UCI Cleveland
    │   └── diabetes.md            ← Dataset card: Pima Indians (OpenML 37)
    └── models/
        ├── heart.md               ← Model card: Heart Disease classifiers
        └── diabetes.md            ← Model card: Diabetes Risk classifiers
```

### Request flow

```
Browser (port 5173)
  │
  │  POST /api/v1/auth/login  {email, password}
  ▼
Vite dev server proxy  ──────────────────────────────────►  FastAPI (port 8000)
                                                                │
                                                           Validate JWT
                                                           Check role (ADMIN|DOCTOR)
                                                                │
                                                           Model registry (in-memory)
                                                                │
                                                      ┌─────────────────────┐
                                                      │ scikit-learn Pipeline│
                                                      │  Preprocess → Predict│
                                                      │  SHAP → LIME         │
                                                      │  Agreement → Sensitivity│
                                                      └─────────────────────┘
                                                                │
                                                        PredictionResponse
                                                      {probability, shap, lime,
                                                       agreement, sensitivity,
                                                       warnings, disclaimer}
  ◄──────────────────────────────────────────────────────────────┘
  │
Display contributions, sensitivity range, agreement,
imputation warnings and medical disclaimer
```

---

## 6. Machine-learning methodology

### Datasets

| Dataset | Source | Instances | Features | Positive rate |
|---|---|---|---|---|
| Heart Disease | UCI ML Repository ID 45 (Cleveland) | 303 | 13 | 45.9% |
| Diabetes | OpenML dataset ID 37 (Pima Indians) | 768 | 8 | 34.9% |

Raw data files are not committed to Git. They are downloaded on demand by the training
scripts and stored locally in `backend/ml/datasets/raw/`.

### Preprocessing

**Heart disease:**
- Numeric features: median imputation → standard scaling (inside pipeline, fit on train only).
- Categorical features (`cp`, `restecg`, `slope`, `thal`): one-hot encoding.
- `ca` treated as ordinal numeric. Six rows have missing values (handled by imputation).

**Diabetes:**
- Five features (`plas`, `pres`, `skin`, `insu`, `mass`) encode missing values as zero.
  Zeros are converted to NaN before imputation.
- All features: median imputation → standard scaling.
- All statistics are learned on the training split exclusively (no data leakage).

### Training and evaluation protocol

| Step | Detail |
|---|---|
| Train/test split | Stratified 80/20, seed 42 |
| Model comparison | Repeated 5×5 stratified CV on training set only |
| Primary metric | ROC-AUC |
| Hold-out evaluation | Used once, after model selection |
| AUC confidence interval | 95% percentile bootstrap (1 000 resamples) |

### Model artifacts

| File | Contents |
|---|---|
| `*.joblib` | Serialized scikit-learn `Pipeline` |
| `background.csv` | Training features (for SHAP background and sensitivity) |
| `metrics.json` | CV and hold-out metrics, dataset SHA-256, library versions |

See [`docs/models/heart.md`](docs/models/heart.md) and
[`docs/models/diabetes.md`](docs/models/diabetes.md) for complete model cards.

---

## 7. Explainability and limitations

### SHAP

SHAP values quantify each feature's marginal contribution to moving the prediction
away from the model's average output. A positive value means the feature increased
predicted risk; a negative value means it decreased risk.

- **Tree SHAP** (Random Forest, Gradient Boosting): exact, in probability units.
- **Linear SHAP** (Logistic Regression, MLP): exact, in log-odds units.

SHAP values describe model behaviour, not causal medical relationships.

### LIME

LIME perturbs the input, queries the model, and fits a simple linear surrogate in the
local neighbourhood. The R² fidelity score measures how well the surrogate approximates
the full model; a low fidelity score indicates the local explanation is unreliable.

### Cross-explainer agreement

When SHAP and LIME independently identify the same top features and agree on direction,
it increases confidence that the explanation reflects a genuine model signal rather than
an artifact of the explanation method. The system reports:

- **Spearman rank correlation** of |contribution| magnitudes.
- **Top-3 overlap:** fraction of top-3 features both methods identify.
- **Sign agreement:** fraction of top features where both methods agree on direction.

Agreement is not reported for Logistic Regression on diabetes because SHAP uses log-odds
and LIME uses probability space; comparing them directly would be meaningless.

### Missing inputs and sensitivity

When measurements are missing or entered as suspicious zeros, the pipeline imputes the
training median. The sensitivity analysis answers: *"How much would the result change if
the unknown measurement took values that real training patients had?"*

The response includes `typical_low` / `typical_high` (10th–90th percentile probability
range), `probability_min` / `probability_max` (extremes), and `verdict_uncertain: true`
when 10–90% of plausible cases would be classified positively.

### Why explanations are not diagnoses

Explanations show what the model considered, not what is clinically true. Training datasets
are small, historical, and population-specific. All predictions must be reviewed by a
qualified clinician.

---

## 8. Authentication and roles

### Roles and permissions

| Role | Run predictions | Feature/model metadata | Sign in |
|---|---|---|---|
| **Admin** | ✅ | ✅ | ✅ |
| **Doctor** | ✅ | ✅ | ✅ |
| **Researcher** | ❌ (HTTP 403) | ✅ | ✅ |
| Unauthenticated | ❌ (HTTP 401) | ✅ | — |

### Signing in

```
POST /api/v1/auth/login
Content-Type: application/json

{ "email": "user@example.com", "password": "your-password" }
```

Response: `{ "access_token": "<JWT>", "token_type": "bearer" }`

Include the token as `Authorization: Bearer <token>` on all protected requests.
Tokens expire after 30 minutes (configurable).

### User profile

```
GET /api/v1/auth/me
Authorization: Bearer <token>
```

Returns: `id`, `email`, `full_name`, `role`, `is_active`, `last_login_at`.

### Provisioning accounts (CLI only)

No public registration endpoint exists. Run from `backend/`:

```bash
uv run python -m app.cli.create_user
```

See [SETUP_AND_TESTING.md §6](SETUP_AND_TESTING.md#6-create-the-initial-administrator-and-other-users).

### Logout and session

The frontend stores the JWT in `sessionStorage` (cleared when the browser tab closes).
Clicking **Sign out** removes the token immediately. There is no server-side revocation;
the token remains cryptographically valid until it expires. For a production deployment,
a token blocklist would be required.

### Security design

- Argon2id password hashing (current recommendation for password storage).
- Dummy Argon2id verification for unknown emails prevents timing-based user enumeration.
- JWT algorithm whitelist (`HS256` only); `type` claim required to equal `"access"`.
- Login endpoint returns HTTP 415 for `multipart/form-data` or missing `Content-Type`.

---

## 9. Installation and setup

**Prerequisites:** Python 3.12, Node.js ≥ 22 (24 recommended), MySQL 8, `uv`, `git`.

The complete step-by-step guide — environment setup, database creation, migration,
model training, user provisioning, startup order, and testing — is in:

📖 **[SETUP_AND_TESTING.md](SETUP_AND_TESTING.md)**

### Quick reference (after first-time setup)

```bash
# Terminal 1 — Backend (from backend/)
uv run uvicorn app.main:app --reload

# Terminal 2 — Frontend (from frontend/)
npm run dev
```

Open **http://localhost:5173** and sign in.

---

## 10. Running tests and quality checks

### Backend (from `backend/`)

```bash
uv run pytest                           # full suite
uv run pytest --cov=app --cov=ml        # with coverage
uv run pytest tests/api/                # API tests only
uv run pytest tests/pipelines/          # ML pipeline tests only
uv run ruff check .                     # lint
uv run ruff format --check .            # format check
```

The backend suite covers: API endpoints, RBAC, authentication, JWT edge cases,
prediction pipelines, SHAP, LIME, agreement metrics, sensitivity analysis, CLI
provisioning, database migrations, and OpenAPI contract synchronization.

### Frontend (from `frontend/`)

```bash
npm test                                # unit and component tests
npm run format:check                    # Prettier check
npm run lint                            # ESLint
npm run build                           # production build (type-checks + bundle)
npm run check                           # all of the above combined
```

---

## 11. API documentation

While the backend is running locally:

| Interface | URL |
|---|---|
| Swagger UI (interactive) | http://localhost:8000/api/v1/docs |
| ReDoc | http://localhost:8000/api/v1/redoc |
| Raw OpenAPI JSON | http://localhost:8000/api/v1/openapi.json |

To regenerate TypeScript types after a backend API change:

```bash
# from frontend/
npm run api:sync
```

For full frontend developer commands and contract generation notes, see [frontend/DEVELOPMENT.md](frontend/DEVELOPMENT.md).

---

## 12. Configuration reference

Copy the template and edit:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | `mysql+pymysql://user:pass@host:3306/dbname` |
| `TEST_DATABASE_URL` | ✅ for tests | Must end in `_test` |
| `SECRET_KEY` | ✅ | ≥ 32 random characters; signs JWT tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Default: 30 |
| `APP_ENV` | Optional | `development` or `production` |
| `DEBUG` | Optional | `true` enables FastAPI debug mode |
| `CORS_ORIGINS` | Optional | Default: `["http://localhost:5173"]` |

Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Never commit real secrets to version control.**

---

## 13. Troubleshooting

See [SETUP_AND_TESTING.md §10](SETUP_AND_TESTING.md#10-troubleshooting) for detailed diagnostics.

| Symptom | Quick check |
|---|---|
| `RuntimeError: TEST_DATABASE_URL is not set` | Add `TEST_DATABASE_URL` to `backend/.env` |
| Connection refused on startup | Check `DATABASE_URL` in `.env`; confirm MySQL is running |
| 503 on prediction endpoint | Model artifacts missing — run training scripts |
| Frontend "Unable to sign in" | Backend not running or CORS mismatch |
| `npm run check` fails | Check `node --version` (need ≥ 20) |

---

## 14. Known limitations and future work

### Current limitations

- **Raw (uncalibrated) probabilities.** All responses carry `"calibrated": false`.
  Do not interpret probability values as clinically validated risk estimates.
- **Small, historical datasets.** UCI Cleveland (303 patients, 1988) and Pima Indians
  (768 patients, collected up to 1990) are not representative of diverse modern populations.
- **No clinical validation.** These models have not been tested against real patient cohorts.
- **No token revocation.** JWTs remain valid until expiry; no server-side blocklist.
- **Heart disease API exposes two models.** Random Forest and Logistic Regression are
  served via the API. Gradient Boosting and MLP are trained and stored but not exposed.

### Not implemented (future work)

- Probability calibration (Platt scaling or isotonic regression).
- Counterfactual / "what-if" recommendations.
- PDF report export.
- Fairness and subgroup analysis.
- Token revocation / session management.
- Audit log.
- Plain-language explanation narratives.

---

## 15. References and acknowledgements

### Datasets

- **Heart Disease:** Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1988).
  *Heart Disease*. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X.
  License: CC BY 4.0.

- **Diabetes:** Smith, J. W., et al. (1988). *Pima Indians Diabetes Database*.
  OpenML dataset ID 37. https://www.openml.org/d/37.

### Libraries and frameworks

- **SHAP:** Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting
  Model Predictions. *NeurIPS 2017*. https://github.com/shap/shap
- **LIME:** Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). "Why Should I Trust You?"
  *KDD 2016*. https://github.com/marcotcr/lime
- **scikit-learn:** Pedregosa et al. (2011). *JMLR 12*. https://scikit-learn.org
- **FastAPI:** https://fastapi.tiangolo.com
- **React:** https://react.dev

### License

MIT — see `LICENSE` for the full text.
