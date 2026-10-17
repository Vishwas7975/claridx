# ClariDx — Installation, Setup, and Testing Guide

This guide is written for someone who has just received the ClariDx repository and needs
to run it on their own computer. Follow every section in order. Each section tells you
which directory to be in before running the commands.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Get the project](#2-get-the-project)
3. [Backend environment setup](#3-backend-environment-setup)
4. [Frontend environment setup](#4-frontend-environment-setup)
5. [Start the application end to end](#5-start-the-application-end-to-end)
6. [Create the initial administrator and other users](#6-create-the-initial-administrator-and-other-users)
7. [Run tests](#7-run-tests)
8. [End-to-end manual test checklist](#8-end-to-end-manual-test-checklist)
9. [API testing](#9-api-testing)
10. [Troubleshooting](#10-troubleshooting)
11. [Stop and shutdown](#11-stop-and-shutdown)
12. [Student handover checklist](#12-student-handover-checklist)

---

## 1. Prerequisites

Install the following software before starting. Verify each version after installation.

### Mandatory

| Software | Minimum version | How to verify |
|---|---|---|
| Python | 3.12 (< 3.13) | `python3 --version` |
| uv (Python package manager) | any recent | `uv --version` |
| Node.js | ≥ 22.19 (24 recommended) | `node --version` |
| npm | ships with Node.js | `npm --version` |
| MySQL | 8.x | `mysql --version` |
| Git | any | `git --version` |

### Installing `uv`

`uv` is the Python package manager used by this project. Install it with:

**Linux / macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, open a new terminal and verify: `uv --version`

### Installing Node.js

Download the LTS release from https://nodejs.org or use a version manager such as
`nvm` (Linux/macOS) or `nvm-windows` (Windows).

Node 24 (or Node.js ≥ 22.19) is required. The test runner (`jsdom` / `undici`) relies on worker thread capabilities present in Node 22+.

### Optional development tools

- A MySQL GUI such as **MySQL Workbench** or **DBeaver** (makes it easier to inspect the database).
- A REST client such as **Insomnia** or **Bruno** (for manual API testing).

---

## 2. Get the project

Open a terminal and clone the repository (replace the URL if your copy is hosted elsewhere):

```bash
git clone <repository-url> claridx
cd claridx
```

You should see:
```
claridx/
  backend/
  frontend/
  docs/
  README.md
  SETUP_AND_TESTING.md
```

All commands in this guide are run from inside `claridx/` or one of its subdirectories.
The working directory for each command is stated explicitly.

---

## 3. Backend environment setup

### 3.1 Enter the backend directory

```bash
cd backend
```

All backend commands in this guide are run from `backend/` unless otherwise stated.

### 3.2 Install Python dependencies

`uv` reads `pyproject.toml` and `uv.lock` and installs all dependencies into a local
virtual environment in `backend/.venv/`:

```bash
uv sync
```

This installs the application, ML, and development dependencies. The first run downloads
packages and may take a minute or two.

Verify the installation:

```bash
uv run python --version
uv run python -c "import fastapi, sklearn, shap, lime; print('OK')"
```

Expected output: `Python 3.12.x` and `OK`.

### 3.3 Create the database

ClariDx requires **MySQL 8**. You need two databases: one for development and one for tests.

Start MySQL and connect as the root user:

**Linux / macOS:**
```bash
mysql -u root -p
```

**Windows (after installing MySQL 8):**
```powershell
mysql -u root -p
```

Run these SQL commands in the MySQL client to create the databases and a dedicated user:

```sql
CREATE DATABASE claridx_dev  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE claridx_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Replace 'a_strong_password' with a password you choose
CREATE USER 'claridx_app'@'localhost' IDENTIFIED BY 'a_strong_password';
GRANT ALL PRIVILEGES ON claridx_dev.*  TO 'claridx_app'@'localhost';
GRANT ALL PRIVILEGES ON claridx_test.* TO 'claridx_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

> **Security note:** Use a strong, unique password. Never reuse passwords from other systems.

### 3.4 Configure environment variables

Copy the example configuration file:

```bash
# from backend/
cp .env.example .env
```

Open `backend/.env` in a text editor. You need to fill in three values:

**1. DATABASE_URL** — replace `CHANGE_ME` with the password you set in the step above:
```
DATABASE_URL=mysql+pymysql://claridx_app:a_strong_password@localhost:3306/claridx_dev
```

**2. TEST_DATABASE_URL** — same user and password, but the test database:
```
TEST_DATABASE_URL=mysql+pymysql://claridx_app:a_strong_password@localhost:3306/claridx_test
```

**3. SECRET_KEY** — generate a secure random key:

```bash
# from backend/
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (a 64-character hex string) into your `.env`:
```
SECRET_KEY=paste_the_generated_key_here
```

Leave the other variables at their defaults for local development:
```
APP_ENV=development
DEBUG=true
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:5173"]
```

> **Important:** Do not commit `backend/.env` to version control. It is already listed in
> `.gitignore`. The `backend/.env.example` file (with placeholder values) is the only
> configuration file that should be committed.

### 3.5 Apply database migrations

Run the Alembic migrations to create the schema:

```bash
# from backend/
uv run alembic upgrade head
```

Expected output ends with something like:
```
Running upgrade  -> 7ebd580e5261, create users table
```

Verify the schema was created:
```bash
mysql -u claridx_app -p claridx_dev -e "SHOW TABLES;"
```

You should see the `users` table listed.

### 3.6 Download and prepare the datasets

The raw dataset files are not included in the repository. Download them:

```bash
# from backend/

# Heart disease (UCI)
uv run python -m ml.scripts.download_heart

# Diabetes (OpenML / scikit-learn)
uv run python -m ml.scripts.download_diabetes
```

Each script downloads the dataset to `backend/ml/datasets/raw/` and prints a SHA-256 hash
for verification. Expected hashes:

| Dataset | SHA-256 |
|---|---|
| Heart disease | `c3855e7c0a818f03a1e90e4f23e0ad5d058dfbd1f276f1aab15d1f02693c1d0d` |
| Diabetes | `3da6d7849e3faeaec68309a79b4f4a12c776a752d286f7f20ae644252ce6d029` |

> If you already have the model artifacts in `backend/ml/artifacts/` (committed to the
> repository), you can skip the training step below and go straight to §3.8.

### 3.7 Train the models

Training runs the full evaluation pipeline (cross-validation + hold-out) and saves
trained pipelines and metrics to `backend/ml/artifacts/`. This may take several minutes.

```bash
# from backend/

uv run python -m ml.scripts.train_heart
uv run python -m ml.scripts.train_diabetes
```

Each script prints a cross-validation report and hold-out metrics. Verify that
`backend/ml/artifacts/heart/` and `backend/ml/artifacts/diabetes/` both contain
`*.joblib` files, `background.csv`, and `metrics.json`.

> **Note:** If model artifacts are already present in the repository (they may be committed
> for convenience), training is not required to run the application. The server loads
> pre-trained artifacts at startup.

### 3.8 Verify the backend starts

```bash
# from backend/
uv run uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Loaded heart models, version <hash>
INFO:     Loaded diabetes models, version <hash>
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Test the liveness probe (in a second terminal):
```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok"}

curl http://localhost:8000/api/v1/health/db
# Expected: {"status":"ok","database":"up"}
```

If you see `503` on the `/health/db` endpoint, the database connection failed. Check
`DATABASE_URL` in `backend/.env` and confirm MySQL is running.

Keep this terminal open. The backend must stay running while you set up the frontend.

---

## 4. Frontend environment setup

Open a **new terminal** and navigate to the frontend directory:

```bash
cd frontend
```

All frontend commands in this guide are run from `frontend/`.

### 4.1 Install Node.js dependencies

```bash
npm install
```

This installs all dependencies listed in `package.json` and locked in `package-lock.json`.
Do not use `npm install --force` or `npm ci` unless you have a specific reason.

### 4.2 Start the development server

```bash
npm run dev
```

Expected output:
```
  VITE v8.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

Open **http://localhost:5173** in your browser.

The Vite dev server forwards all `/api` requests to `http://127.0.0.1:8000` (the backend).
This proxy is configured in `frontend/vite.config.ts`. You do not need to change any
frontend configuration to point to the backend — the proxy handles it automatically.

### 4.3 Verify the connection

The browser should show the ClariDx sign-in page. If you see a network error, confirm
that the backend is running on port 8000.

---

## 5. Start the application end to end

This section walks you through the complete workflow from startup to sign-out.

### 5.1 Startup order

1. **MySQL** — must be running before the backend starts.
2. **Backend** (`backend/` → `uv run uvicorn app.main:app --reload`) — keep this terminal open.
3. **Frontend** (`frontend/` → `npm run dev`) — keep this terminal open.

You need **two open terminals**: one for the backend and one for the frontend.

### 5.2 Confirm the health endpoints

```bash
curl http://localhost:8000/api/v1/health
# → {"status":"ok"}

curl http://localhost:8000/api/v1/health/db
# → {"status":"ok","database":"up"}
```

### 5.3 Create a user account

Before you can sign in, you must provision at least one account using the CLI.
See [Section 6](#6-create-the-initial-administrator-and-other-users) for full instructions.

Quick command (from `backend/`):
```bash
uv run python -m app.cli.create_user
```

### 5.4 Sign in

1. Open http://localhost:5173 in your browser.
2. Enter the email address and password you just created.
3. Click **Sign in**.

On success, the header displays your name and role badge, and the condition selector
(Heart Disease / Diabetes) appears.

### 5.5 Run a heart disease prediction

1. Select **Heart Disease** (the default tab).
2. Choose a model from the model selector (default: Random Forest).
3. Fill in patient measurements. At least 7 of the 13 fields are required.
   Use the **Load example** button to populate a realistic synthetic patient.
4. Click **Analyse**.
5. The result panel displays:
   - Predicted probability of heart disease.
   - Binary verdict (positive / negative at threshold 0.50).
   - SHAP feature contributions (which features pushed toward or away from disease).
   - LIME feature contributions.
   - Cross-explainer agreement metrics.
   - Sensitivity range (if any inputs were left blank).
   - Any out-of-distribution warnings.
   - Medical disclaimer.

### 5.6 Run a diabetes prediction

1. Click **Diabetes** in the condition selector.
2. The default model is Logistic Regression.
3. Fill in measurements. Entering 0 for `Plasma Glucose`, `Blood Pressure`, `Skin Thickness`,
   `Insulin`, or `BMI` is treated as missing (these are known physiologically implausible zeros
   in the Pima Indians dataset) and will be imputed and warned about.
4. Click **Analyse** and review the result.

**Note:** Cross-explainer agreement is not shown for Logistic Regression on diabetes.
This is by design — see README §7 for the reason.

### 5.7 Sign out

Click **Sign out** in the top-right header. Your session token is removed from the browser.
Attempting to navigate to a prediction will redirect you to the login screen.

---

## 6. Create the initial administrator and other users

User accounts can only be created through the secure CLI. No public registration endpoint exists.

### Interactive mode (recommended for first use)

From `backend/`:

```bash
uv run python -m app.cli.create_user
```

The CLI prompts you for:

1. **Email address** — must be a valid email format (e.g., `admin@example.local`).
2. **Full name** — displayed in the UI header.
3. **Role** — type one of: `admin`, `doctor`, `researcher`.
4. **Password** — entered securely (not visible; uses `getpass`).
5. **Confirm password** — re-enter the same password.

If you choose the `admin` role, the CLI asks for an additional confirmation:
```
Are you sure you want to create an account with ADMIN privileges for 'admin@example.local'? [y/N]:
```
Type `y` and press Enter.

On success:
```
User successfully created! ID: 1, Email: admin@example.local, Role: admin
```

### Command-line flags (for scripted setup)

```bash
uv run python -m app.cli.create_user \
  --email doctor@example.local \
  --full-name "Dr. Jane Smith" \
  --role doctor
```

Passwords are **always** prompted securely and are never accepted as command-line arguments.

For admin accounts in non-interactive scripts, add `--confirm-admin`:
```bash
uv run python -m app.cli.create_user \
  --email admin@example.local \
  --full-name "Admin User" \
  --role admin \
  --confirm-admin
```

### Provisioning multiple roles

Create one account for each role you want to test:

```bash
# Admin
uv run python -m app.cli.create_user --email admin@example.local --full-name "Admin" --role admin --confirm-admin

# Doctor (can run predictions)
uv run python -m app.cli.create_user --email doctor@example.local --full-name "Dr. Smith" --role doctor

# Researcher (metadata only, no predictions)
uv run python -m app.cli.create_user --email researcher@example.local --full-name "Researcher" --role researcher
```

### Rules enforced by the CLI

- Duplicate email → error (no silent overwrite or role elevation).
- Empty password → error.
- Passwords that do not match → error.
- Invalid role (anything other than `admin`, `doctor`, `researcher`) → error.
- Invalid email format → error.
- Database error → transaction rolled back, error reported.

### Development versus production credentials

The accounts you create locally exist only in your local `claridx_dev` database. They are
not shared, committed, or transferred to any production system. Use clearly synthetic email
addresses (such as `@example.local`) for local development so it is obvious they are test
accounts.

---

## 7. Run tests

### 7.1 Backend tests

The backend test suite requires `TEST_DATABASE_URL` to be configured in `backend/.env`
(see §3.4). The test database must exist (created in §3.3). The suite applies migrations
automatically before running.

Run from `backend/`:

```bash
# Full suite
uv run pytest

# With line-level coverage report
uv run pytest --cov=app --cov=ml --cov-report=term-missing

# API and integration tests only
uv run pytest tests/api/

# ML pipeline and explainer tests only
uv run pytest tests/pipelines/

# A specific test file
uv run pytest tests/api/test_auth_api.py

# Verbose output (see each test name)
uv run pytest -v
```

**What the backend suite covers:**

| Test module | Area |
|---|---|
| `tests/api/test_auth_api.py` | Login (JSON + form), Content-Type enforcement, /me endpoint |
| `tests/api/test_auth_e2e.py` | Full authentication round-trip |
| `tests/api/test_prediction_rbac.py` | ADMIN/DOCTOR 200, RESEARCHER 403, unauthenticated 401 |
| `tests/api/test_heart_api.py` | Heart prediction endpoint, model switching |
| `tests/api/test_diabetes_api.py` | Diabetes prediction endpoint |
| `tests/api/test_heart_sensitivity.py` | Heart sensitivity analysis API responses |
| `tests/api/test_openapi_contract.py` | Frontend OpenAPI schema synchronization |
| `tests/api/test_validation_errors.py` | Input validation error responses |
| `tests/pipelines/test_shap_explainer.py` | SHAP for all four model types |
| `tests/pipelines/test_lime_explainer.py` | LIME tabular |
| `tests/pipelines/test_agreement.py` | Cross-explainer agreement metrics |
| `tests/pipelines/test_sensitivity.py` | Sensitivity analysis logic |
| `tests/pipelines/test_diabetes_sensitivity.py` | Diabetes zero-as-missing sensitivity |
| `tests/pipelines/test_heart_pipeline.py` | Heart preprocessing pipeline |
| `tests/pipelines/test_diabetes_pipeline.py` | Diabetes preprocessing pipeline |
| `tests/pipelines/test_data_and_splits.py` | Stratified split reproducibility |
| `tests/test_security.py` | JWT edge cases (expired, malformed, wrong algo, type claim) |
| `tests/test_cli_create_user.py` | CLI provisioning logic |
| `tests/test_user_model.py` | SQLAlchemy User model |

**Interpreting failures:**

- A failure in `tests/api/` with a database error usually means `TEST_DATABASE_URL` is wrong
  or the test database does not exist.
- A failure with `ImportError` usually means `uv sync` was not run or failed.
- SHAP and LIME tests use synthetic data and do not require the real datasets.

### 7.2 Backend linting and formatting

```bash
# from backend/
uv run ruff check .
uv run ruff format --check .
```

To auto-fix formatting:
```bash
uv run ruff format .
```

### 7.3 Frontend tests

Run from `frontend/`:

```bash
# Unit and component tests (Vitest)
npm test

# Watch mode (re-runs on file changes)
npm run test:watch

# Prettier format check
npm run format:check

# Auto-fix formatting
npm run format

# ESLint
npm run lint

# Production build (also runs TypeScript type-checking)
npm run build

# All checks combined (format + lint + test + build)
npm run check
```

**What the frontend suite covers:**

- `Auth.test.tsx` — login form behavior, error handling, duplicate submissions.
- `PatientForm.test.tsx` — patient input form validation and state.
- `PredictionPage.test.tsx` — prediction workflow, loading states, result display.
- `ResultView.test.tsx` — explanation rendering, sensitivity display.
- `client.test.ts` — API client token injection and 401 handling.
- `errors.test.ts` — ApiError class.
- `form.test.ts` — Form state logic.
- `format.test.ts` (heart) — Feature value formatters.

**Interpreting failures:**

- If `npm run build` fails with type errors, the TypeScript definitions are out of sync.
  Run `npm run api:sync` from `frontend/` and try again.
- If tests fail with `Cannot find module`, run `npm install` to ensure dependencies are installed.

---

## 8. End-to-end manual test checklist

Use this checklist to verify the full system works correctly. Mark each item as you complete it.

The example values below are synthetic, illustrative values appropriate to the schema.
They do not represent real patients.

### Authentication

- [ ] **Valid login (Doctor)**
  - Go to http://localhost:5173.
  - Enter your Doctor account email and correct password.
  - Click **Sign in**.
  - ✅ Expected: header shows your name and `DOCTOR` badge; condition selector appears.

- [ ] **Invalid login**
  - Click **Sign out** (if signed in).
  - Enter a valid email and a wrong password.
  - Click **Sign in**.
  - ✅ Expected: error message "Invalid email or password." No token is issued.

- [ ] **Profile retrieval (API)**
  - After signing in, open the Swagger UI: http://localhost:8000/api/v1/docs.
  - Click **Authorize**, enter your email/password.
  - Send `GET /api/v1/auth/me`.
  - ✅ Expected: JSON response with `id`, `email`, `full_name`, `role`, `is_active`.

### Heart disease prediction (Doctor)

- [ ] **Basic prediction**
  - Sign in as Doctor.
  - Select **Heart Disease** and model **Random Forest**.
  - Click **Load example** to populate measurements.
  - Click **Analyse**.
  - ✅ Expected: probability displayed (0–1), binary verdict, SHAP contributions, LIME contributions, agreement metrics, disclaimer.

- [ ] **Missing measurement sensitivity**
  - Clear one numeric field (e.g., Maximum Heart Rate).
  - Click **Analyse**.
  - ✅ Expected: the cleared field is listed in imputed features; a sensitivity section appears showing the probability range.

- [ ] **Out-of-distribution warning**
  - Enter `Age = 15` (below the minimum of 18 allowed by the schema).
  - ✅ Expected: form validation prevents submission (the field is marked invalid before the request is sent).
  - Alternatively, enter a value at the extreme of the training range and check the warnings array in the API response.

### Diabetes prediction (Doctor)

- [ ] **Basic prediction with zero-as-missing**
  - Switch to **Diabetes**.
  - Enter `0` for **Plasma Glucose** (a physiologically implausible zero).
  - Fill in other fields with realistic values (e.g., Pregnancies=2, Blood Pressure=70, Skin Thickness=25, Insulin=100, BMI=28.5, Diabetes Pedigree=0.5, Age=35).
  - Click **Analyse**.
  - ✅ Expected: a warning appears stating that Plasma Glucose was entered as 0 and was imputed.

- [ ] **Diabetes sensitivity**
  - Leave Insulin blank.
  - ✅ Expected: sensitivity range appears for Insulin.

### RBAC checks

- [ ] **Admin can run predictions**
  - Sign in as Admin account.
  - Run any prediction.
  - ✅ Expected: prediction succeeds (HTTP 200).

- [ ] **Researcher sees notice, cannot predict**
  - Sign in as Researcher account.
  - ✅ Expected: a "Researcher Access (Read-Only)" notice appears instead of the prediction form.

- [ ] **Researcher metadata access (API)**
  - While signed in as Researcher, open Swagger UI and authorize.
  - Send `GET /api/v1/heart/features`.
  - ✅ Expected: full feature list returned (HTTP 200).
  - Send `POST /api/v1/heart/predictions` with a valid payload.
  - ✅ Expected: HTTP 403 Forbidden.

- [ ] **Unauthenticated access**
  - Sign out.
  - In Swagger UI (without authorizing), send `POST /api/v1/heart/predictions`.
  - ✅ Expected: HTTP 401 Unauthorized.

### Session and logout

- [ ] **Logout clears session**
  - Sign in, then click **Sign out**.
  - ✅ Expected: login form reappears.
  - Reload the page.
  - ✅ Expected: still on login form (session is not restored from a cleared token).

- [ ] **Expired token behavior**
  - Set `ACCESS_TOKEN_EXPIRE_MINUTES=0` in `.env` and restart the backend.
  - Sign in, then immediately send an authenticated request.
  - ✅ Expected: HTTP 401 (token immediately expired).
  - Restore `ACCESS_TOKEN_EXPIRE_MINUTES=30` and restart before continuing.

---

## 9. API testing

### Swagger UI (recommended)

While the backend is running, open:

**http://localhost:8000/api/v1/docs**

1. Click the **Authorize** button (padlock icon).
2. In the **username** field enter your email address; in **password** enter your password.
3. Click **Authorize** and close the dialog.
4. Expand any endpoint and click **Try it out** to send live requests.

### Health checks (no authentication)

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/db
curl http://localhost:8000/api/v1/heart/features
curl http://localhost:8000/api/v1/diabetes/features
```

### Manual login request

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"doctor@example.local","password":"your-password"}'
```

Response:
```json
{"access_token":"<token>","token_type":"bearer"}
```

Save the token value and use it in authenticated requests:

```bash
TOKEN="<paste your token here>"

curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

> **Security reminder:** Never share your token or paste it into shared logs, screenshots,
> or chat messages. Treat it like a password.

### Heart prediction (manual)

```bash
curl -X POST http://localhost:8000/api/v1/heart/predictions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model_name": "random_forest",
    "patient": {
      "age": 55, "sex": 1, "cp": 2, "trestbps": 130, "chol": 250,
      "fbs": 0, "restecg": 0, "thalach": 165, "exang": 0,
      "oldpeak": 1.5, "slope": 2, "ca": 0, "thal": 3
    }
  }'
```

---

## 10. Troubleshooting

### Python version mismatch

**Symptom:** `uv sync` fails with a Python version error.

**Fix:** Install Python 3.12. If multiple Python versions are installed, tell `uv` which to use:
```bash
uv python install 3.12
uv sync --python 3.12
```

### `uv` not found

**Symptom:** `uv: command not found`

**Fix:** Install `uv` (see §1) and ensure its installation directory is on your `PATH`.
Open a new terminal after installation.

### Database connection refused

**Symptom:** Backend prints `OperationalError: (pymysql.err.OperationalError) (2003, ...)` or
`/health/db` returns 503.

**Diagnosis:**
1. Check MySQL is running: `mysql -u root -p -e "SELECT 1"`
2. Verify `DATABASE_URL` in `backend/.env` has the correct host, port, username, password, and database name.
3. Confirm the `claridx_dev` database exists and the `claridx_app` user has privileges.

### `TEST_DATABASE_URL is not set` error

**Symptom:** Running `uv run pytest` immediately fails with `RuntimeError: TEST_DATABASE_URL is not set`.

**Fix:** Add `TEST_DATABASE_URL` to `backend/.env`. The test suite requires it.

### Migration fails

**Symptom:** `uv run alembic upgrade head` errors with a MySQL error.

**Fix:**
1. Ensure `DATABASE_URL` is correct in `backend/.env`.
2. Confirm the `claridx_dev` database exists.
3. Confirm the user has `ALL PRIVILEGES` on the database.

### Model 503 on prediction endpoints

**Symptom:** `GET /api/v1/heart/predictions` returns HTTP 503 with "Prediction models are not loaded."

**Fix:** The backend could not find the model artifacts at startup. Either:
- Run the training scripts (§3.7).
- Or confirm `backend/ml/artifacts/heart/` contains `.joblib` files.

Check the backend log output for the startup message. If it says `Model artifacts missing`,
run the training script.

### Node.js version too old

**Symptom:** `npm install` or `npm run dev` fails with a syntax or compatibility error.

**Fix:** Install Node.js 24 (or ≥ 22.19). Check with `node --version`. Older Node versions (such as Node 20) will fail during frontend test execution due to missing WebIDL APIs in jsdom.

### Port conflict (backend)

**Symptom:** `error: address already in use :::8000`

**Fix:** Find and stop the process using port 8000:
```bash
# Linux/macOS
lsof -i :8000
kill <PID>

# Windows PowerShell
netstat -ano | findstr :8000
Stop-Process -Id <PID>
```

Or run the backend on a different port:
```bash
uv run uvicorn app.main:app --reload --port 8001
```
Then update `CORS_ORIGINS` in `.env` and the Vite proxy in `vite.config.ts` to match.

### Port conflict (frontend)

**Symptom:** Vite prints "Port 5173 is already in use."

**Fix:** Vite will automatically try the next available port (e.g., 5174) and print the new URL.

### Frontend cannot reach backend

**Symptom:** Browser console shows `ERR_CONNECTION_REFUSED` for `/api/...` requests.

**Fix:** Ensure the backend is running on port 8000. The Vite proxy in `vite.config.ts`
forwards `/api` → `http://127.0.0.1:8000`. No frontend configuration change is needed
as long as the backend is on port 8000.

### Authentication failure after restart

**Symptom:** After restarting the backend, the frontend shows "Unable to sign in" or
returns 401 on requests that worked before.

**Fix:** The `SECRET_KEY` in `.env` has changed, or the `.env` file was not found. Ensure
`backend/.env` exists and `SECRET_KEY` is set. Clear browser `sessionStorage` (developer
tools → Application → Storage) and sign in again.

### OpenAPI / TypeScript type errors

**Symptom:** `npm run build` fails with TypeScript type errors related to the API.

**Fix:** The frontend types are generated from the backend's OpenAPI schema. Regenerate them:
```bash
# from frontend/
npm run api:sync
```
This exports the latest schema from the backend (which must be running) and regenerates
`src/api/schema.d.ts`.

### Test failures — safe diagnostic output

When tests fail, capture the output safely:
```bash
# from backend/
uv run pytest -v 2>&1 | head -100
```

Never share full test output that might contain token values, database credentials, or
patient data (even synthetic data used in tests).

---

## 11. Stop and shutdown

### Stop the frontend

In the frontend terminal, press `Ctrl+C`. The Vite dev server will exit.

### Stop the backend

In the backend terminal, press `Ctrl+C`. Uvicorn will shut down gracefully.

### Stop MySQL

How you stop MySQL depends on your operating system and installation method:

**Linux (systemd):**
```bash
sudo systemctl stop mysql
```

**macOS (Homebrew):**
```bash
brew services stop mysql
```

**Windows (Services):**
Open Services (`services.msc`), find `MySQL80`, and click **Stop**.

> **Do not delete the `claridx_dev` or `claridx_test` databases** unless you want to lose
> all provisioned user accounts and need to start over. The databases contain only user
> records; model artifacts and training data are stored on the filesystem.

---

## 12. Student handover checklist

Before submitting or handing over the project, verify every item:

**Environment**
- [ ] Python 3.12 installed and confirmed with `python3 --version`
- [ ] `uv` installed and confirmed with `uv --version`
- [ ] Node.js ≥ 22 (24 recommended) installed and confirmed with `node --version`
- [ ] MySQL 8 installed and running

**Backend**
- [ ] `uv sync` completed without errors from `backend/`
- [ ] `backend/.env` exists with real values for `DATABASE_URL`, `TEST_DATABASE_URL`, `SECRET_KEY`
- [ ] `claridx_dev` and `claridx_test` databases exist and are accessible
- [ ] `uv run alembic upgrade head` completed successfully
- [ ] Model artifacts exist in `backend/ml/artifacts/heart/` and `backend/ml/artifacts/diabetes/`
- [ ] `uv run uvicorn app.main:app --reload` starts without errors
- [ ] `GET /api/v1/health` returns `{"status":"ok"}`
- [ ] `GET /api/v1/health/db` returns `{"status":"ok","database":"up"}`

**User accounts**
- [ ] At least one Admin account provisioned via `uv run python -m app.cli.create_user`
- [ ] At least one Doctor account provisioned
- [ ] Researcher account provisioned (optional, for RBAC testing)
- [ ] All accounts use locally unique, secure passwords

**Frontend**
- [ ] `npm install` completed without errors from `frontend/`
- [ ] `npm run dev` starts and browser opens http://localhost:5173
- [ ] Sign-in page appears

**End-to-end**
- [ ] Doctor can sign in successfully
- [ ] Heart disease prediction returns probability + SHAP + LIME + disclaimer
- [ ] Diabetes prediction returns probability + SHAP + LIME + disclaimer
- [ ] Sensitivity range appears when a measurement is left blank
- [ ] Researcher account shows the researcher notice (no prediction form)
- [ ] Sign-out clears session

**Tests**
- [ ] `uv run pytest` passes from `backend/`
- [ ] `npm run check` passes from `frontend/`
- [ ] `uv run ruff check .` passes from `backend/`

**Documentation reviewed**
- [ ] `README.md` read
- [ ] `SETUP_AND_TESTING.md` followed (this file)
- [ ] `docs/models/heart.md` reviewed for methodology and limitations
- [ ] `docs/models/diabetes.md` reviewed for methodology and limitations
- [ ] Medical disclaimer understood: **ClariDx is not a clinical tool**
