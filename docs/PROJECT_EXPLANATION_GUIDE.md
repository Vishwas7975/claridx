# ClariDx — Comprehensive Project Explanation & Presentation Guide

> **Target Audience:** Final-Year Engineering / Computer Science Students, Academic Evaluators, Viva Examiners, and Clinical AI Clients.  
> **Project Name:** ClariDx (Explainable Clinical AI Decision Support System)  
> **Repository:** https://github.com/Vishwas7975/claridx

---

## 1. Quick Access: Demo Credentials

Use these pre-provisioned demo accounts to demonstrate the application and test role-based access control (RBAC):

| Role | Email | Password | Allowed Capabilities |
|---|---|---|---|
| **Doctor** | `doctor@claridx.local` | `ClariDxDemo2026!` | Run Heart & Diabetes predictions, view SHAP/LIME explainability, simulate missing-data sensitivity, access clinical dashboard. |
| **Administrator** | `admin@claridx.local` | `ClariDxDemo2026!` | All doctor prediction capabilities + full administrative privileges. |
| **Researcher** | `researcher@claridx.local` | `ClariDxDemo2026!` | **Read-Only Access:** Can inspect feature schemas, model metrics, and API documentation; **strictly blocked** from submitting clinical predictions (HTTP 403 Forbidden). |

---

## 2. Executive Summary: What is ClariDx?

### The Real-World Problem
Modern Machine Learning models (like Random Forests and Gradient Boosted Trees) can achieve high diagnostic accuracy on medical datasets. However, in real clinical healthcare, they face a fatal barrier: the **"Black Box" Problem**.
- Doctors cannot blindly trust an AI that simply outputs "85% Risk" without explaining **why**.
- In the real world, patients rarely have every single lab test done. Standard ML models crash or produce nonsensical predictions when test values are missing.
- Many systems falsely report uncalibrated model outputs as "calibrated clinical probabilities," misleading doctors.

### The ClariDx Solution
**ClariDx** is an Explainable Clinical Decision Support System (CDSS) for **Heart Disease** and **Type 2 Diabetes** risk assessment designed to address these exact clinical challenges:
1. **Explainable AI (XAI):** Uses **SHAP** (Shapley Additive exPlanations) and **LIME** (Local Interpretable Model-agnostic Explanations) in parallel to show which specific patient measurements contributed toward or away from disease risk.
2. **Cross-Explainer Agreement:** Measures whether SHAP and LIME agree on the top diagnostic drivers (using rank correlation and sign agreement) so clinicians know when explanations are trustworthy.
3. **Missing-Data Sensitivity Analysis:** When a patient lacks certain lab tests, ClariDx does not just guess; it simulates the missing values across empirical background populations, showing the doctor a **risk range** and flagging if an omitted lab test could flip the clinical verdict (`can_flip`).
4. **Physiological Reality Handling (*Zero-as-Missing*):** Recognizes that in clinical datasets, physiological values like blood pressure=0 or glucose=0 are impossible and represent unrecorded missing tests, while pregnancies=0 is clinically valid.
5. **Strict Clinical Governance & RBAC:** Doctors can predict; researchers have read-only access; accounts are provisioned via secure administrator CLI with Argon2id password security.

---

## 3. Technology Stack Breakdown & Architectural Rationale

When explaining to examiners, emphasize **why** each technology was selected:

### 3.1 Frontend (Modern Clinical SaaS)
- **React 19 + TypeScript (~6.0):** Ensures bulletproof compile-time type safety across all medical forms, API payloads, and explainer charts.
- **Vite:** Next-generation frontend tooling providing sub-second Hot Module Replacement (HMR) and optimized ES-module production bundling.
- **TanStack React Query v5:** Server-state management handling caching, loading states, error boundaries, and background data synchronization.
- **OpenAPI Type Sync (`openapi-fetch` + `openapi-typescript`):** The frontend types are automatically generated from backend FastAPI Pydantic models via an automated pipeline (`npm run api:sync`). If a backend schema changes, frontend compilation catches mismatches instantly.
- **CSS Custom Properties & Theme System:** Built with vanilla CSS custom properties supporting an accessible Light/Dark theme toggle (`data-theme="dark"` / `data-theme="light"`), persistent `localStorage` preference (`claridx_theme`), system preference synchronization, and strict WCAG AA clinical contrast across desktop, tablet, and mobile layouts.

### 3.2 Backend (High-Performance Async API)
- **FastAPI (Python 3.12):** Asynchronous, OpenAPI-native web framework with automatic Swagger UI and ReDoc documentation.
- **Pydantic v2:** High-speed schema validation in Rust core, validating incoming physiological ranges (e.g., rejecting age < 18 or negative blood pressure) before data hits ML pipelines.
- **SQLAlchemy 2.0 ORM & Alembic:** Robust relational mapping and version-controlled database schema migrations.
- **MySQL 8.0:** ACID-compliant relational storage for user accounts, credentials, and audit metadata.

### 3.3 Machine Learning & Explainable AI
- **Scikit-learn Pipelines:** Strict separation of data transformations (SimpleImputer, StandardScaler, OneHotEncoder) wrapped in pipelines trained strictly on cross-validation training folds to **guarantee zero data leakage**.
- **SHAP (Shapley Additive exPlanations):** Game-theoretic feature importance (`TreeExplainer` for tree models, `LinearExplainer` for linear models).
- **LIME (`LimeTabularExplainer`):** Local surrogate linear modeling around individual patient predictions.
- **Joblib:** Fast serialization of trained pipelines, metrics, and background population distributions.

### 3.4 Security & Authentication
- **Argon2id:** Winner of the Password Hashing Competition; state-of-the-art memory-hard password hashing.
- **Timing-Safe Dummy Verification:** If an attacker tries logging in with an email that does not exist, ClariDx still executes an Argon2id verification cycle on a dummy hash to prevent email enumeration via response timing attacks.
- **PyJWT (HS256):** Stateless bearer token authentication enforcing a strict 30-minute expiration and required `"type": "access"` claims.
- **Dual-Tier User Provisioning & Least-Privilege Registration:** Public self-service registration (`POST /api/v1/auth/register`) automatically assigns users the least-privileged `PATIENT` role. Privileged accounts (`DOCTOR`, `RESEARCHER`, `ADMIN`) cannot be registered publicly and must be provisioned via the administrator CLI (`python -m app.cli.create_user`), preserving strict clinical governance.

---

## 4. Deep-Dive: The Two Clinical Disease Workflows

### 4.1 Heart Disease Risk Prediction
- **Dataset:** UCI Machine Learning Repository (Cleveland subset, ID 45).
- **Sample Size:** 303 patient records, 13 clinical features.
- **Target:** Presence of heart disease (`num > 0`). Class balance: ~45.9% positive.
- **Features Analyzed:** Age, Sex, Chest Pain Type (`cp`), Resting Blood Pressure (`trestbps`), Serum Cholesterol (`chol`), Fasting Blood Sugar (`fbs`), Resting ECG (`restecg`), Maximum Heart Rate (`thalach`), Exercise Induced Angina (`exang`), ST Depression (`oldpeak`), Slope of Peak Exercise ST (`slope`), Major Vessels Colored (`ca`), Thallium Stress Test (`thal`).
- **Data Validation & Quality:** Minimum 7 of 13 measurements required to submit.
- **Models Implemented:** Random Forest (Selected primary model based on 5x5 repeated cross-validation ROC-AUC of 0.898), Logistic Regression, Gradient Boosting, MLP.

### 4.2 Type 2 Diabetes Risk Prediction
- **Dataset:** Pima Indians Diabetes Dataset (National Institute of Diabetes and Digestive and Kidney Diseases, OpenML ID 37).
- **Sample Size:** 768 female patients aged $\ge 21$.
- **Target:** Diabetes diagnosis (`Outcome`). Positive prevalence: ~34.9%.
- **Features Analyzed:** Pregnancies (`preg`), Plasma Glucose Concentration (`plas`), Diastolic Blood Pressure (`pres`), Triceps Skinfold Thickness (`skin`), 2-Hour Serum Insulin (`insu`), Body Mass Index (`mass`), Diabetes Pedigree Function (`pedi`), Age (`age`).
- **Data Validation & Quality:** Minimum 5 of 8 measurements required.
- **The "Zero-as-Missing" Clinical Discovery:**
  - In raw medical data, non-entry of a lab test is often coded as `0`.
  - In diabetes diagnostics, glucose = 0 or blood pressure = 0 or insulin = 0 means the patient is dead or the test was never performed!
  - Treating them as true zeros completely corrupts model weights.
  - ClariDx employs a domain-specific filter: converts zeros in `plas`, `pres`, `skin`, `insu`, and `mass` to `NaN` and imputes them with the training median, while preserving `preg = 0` as a valid medical measurement.
- **Models Implemented:** Logistic Regression (Selected primary model based on 5x5 repeated cross-validation ROC-AUC of 0.842), Random Forest, Gradient Boosting, MLP.

### 4.3 Why We Did Not Replace Pregnancy Count with Sex (Architecture & Clinical Decision)
For complete details, see [`docs/DIABETES_FEATURE_DECISION.md`](DIABETES_FEATURE_DECISION.md).

1. **Why we did not replace pregnancy count with Sex:**
   - The underlying models were trained on eight specific benchmark features (`preg`, `plas`, `pres`, `skin`, `insu`, `mass`, `pedi`, `age`).
   - The Pima training dataset contains exclusively women aged 21 or older and does not contain a `Sex` feature.
   - Replacing `preg` with `sex` without retraining creates an immediate feature mismatch against the serialized pipelines.
   - Mapping biological sex into the pregnancy field (e.g. arbitrarily encoding male as 0) incorrectly treats two biologically distinct attributes as equivalent, producing invalid risk predictions and corrupting SHAP attributions.
   - Adding a true `Sex` feature properly requires selecting a representative multi-sex diabetes cohort, retraining all models, recalculating cross-validation metrics, and re-validating the explainability pipelines.

2. **Why keeping pregnancy count helps in the current scenario:**
   - Preserves 100% compatibility with the existing trained models, preprocessing, SHAP/LIME explainability pipelines, API schemas, and automated tests.
   - Avoids fabricated inputs, synthetic mappings, and unnecessary regressions.
   - Retains the current thoroughly tested diabetes pipeline while transparently communicating its demographic training limitations to clinicians and evaluators.

---

## 5. The "Secret Sauce": Explainability & Missing-Data Sensitivity

When presenting, this is the most impressive component to showcase:

### 5.1 SHAP vs. LIME Dual Explainability
Most academic projects only implement one explainer. ClariDx implements **both**:
- **SHAP:** Calculates the exact Shapley contribution of every feature relative to the dataset base rate. Highly rigorous, mathematically unified.
- **LIME:** Perturbs the patient's measurements locally and fits a simple interpretable linear surrogate. Fast and intuitive.
- **Why both?** Because in healthcare, if SHAP says "Glucose pushed risk UP" and LIME says "Glucose pushed risk DOWN", the doctor knows the model is operating in an unstable region of feature space.

### 5.2 Cross-Explainer Agreement Metrics
ClariDx computes quantitative agreement between SHAP and LIME in real time:
1. **Rank Correlation (Spearman $\rho$):** Compares feature importance ordering.
2. **Top-3 Feature Overlap:** Checks if both explainers identified the same 3 most critical diagnostic factors.
3. **Sign Agreement:** Verifies whether both explainers agree on the direction (risk-increasing vs risk-decreasing) for all features.

### 5.3 Missing-Data Sensitivity Analysis
What if a patient cannot afford or has not yet completed their Insulin test?
- Standard AI simply imputes a single average number and gives a single fixed prediction, hiding the uncertainty.
- **ClariDx runs empirical background simulation:** It substitutes the missing feature with 100+ empirical background values sampled from the training distribution.
- **Outputs to Clinician:**
  - **Risk Range:** e.g., *"Patient risk is typically between 32% and 68% depending on the unmeasured insulin level."*
  - **Verdict Uncertainty Flag:** Alerts if the missing data crosses the decision threshold (`verdict_uncertain = true`).
  - **`can_flip` Feature Badge:** Explicitly highlights which missing test could completely change the diagnosis from negative to positive.

---

## 6. Decision Threshold & Clinical Governance

### Decision Threshold (50%)
- Both models evaluate binary verdicts against `DECISION_THRESHOLD = 0.50` (50%).
- The UI dynamically renders the threshold tick marker and percentage from the API response.

### Raw Scores vs. Calibrated Probabilities (Key Viva Distinction!)
- In clinical machine learning, standard scikit-learn models output **uncalibrated scores** (e.g., Random Forest averages decision tree votes, which are not true Bayesian probabilities).
- ClariDx adheres to strict medical honesty: All responses carry `"calibrated": false`.
- The UI explicitly informs the doctor: *"It is an uncalibrated model output: treat it as a score, not a measured clinical risk."*
- Prominently displays: *"Research prototype for decision support and education only. Not validated for autonomous clinical diagnosis."*

---

## 7. Step-by-Step Live Demonstration Script

Follow these steps for a flawless 5-minute presentation:

### Step 1: Public Landing Page & Theme System
1. Open `http://localhost:5173`.
2. Show the modern **Public Landing Page**: point out the high-contrast branding, value propositions, clinical workflow cards, and the interactive live preview card.
3. Demonstrate the **Theme Toggle**: switch between the deep navy dark mode and clinical light mode. Refresh the page to demonstrate persistent preference (`localStorage`).
4. Click **"Sign In"** in the navigation header to enter the login view.
5. Sign in as **Doctor** (`doctor@claridx.local` / `ClariDxDemo2026!`).
6. Point out the top navigation bar: doctor's identity, active `DOCTOR` badge, and condition tabs.

### Step 2: Heart Disease Prediction & Full Explanation
1. Select **Heart Disease**.
2. Click the preset button: **"Example: typical high risk"**.
3. Point out how measurements auto-populate across grouped clinical sections (Demographics, Symptoms & Vitals, Electrocardiography & Stress Test, Fluoroscopy & Blood).
4. Click **"Analyse"**.
5. Walk through the results panel:
   - **Prediction Score:** High probability with clear threshold marker at 50%.
   - **SHAP Feature Contributions:** Point out which factors increased risk (e.g., chest pain, ST depression) in red/positive and which protected the patient in green/negative.
   - **LIME Feature Contributions:** Show side-by-side local surrogate weights.
   - **Agreement Card:** Show rank correlation and sign agreement between the two XAI methods.

### Step 3: Missing-Data Sensitivity Simulation
1. Clear one or two fields in the form (e.g., delete `Maximum Heart Rate` or `Major vessels colored`).
2. Click **"Analyse"** again.
3. Show the **Sensitivity Analysis** panel that appears:
   - Explain the typical risk band (e.g. 45% – 72%).
   - Highlight the **`can alter verdict`** badge, showing how missing a specific lab test creates clinical ambiguity.

### Step 4: Diabetes Workflow & Zero-as-Missing
1. Switch to the **Diabetes** tab.
2. Click **"Example: routine clinic (skin & insulin missing)"**.
3. Point out that skinfold thickness and insulin are empty.
4. Point out the explicit **Pregnancy Field Guidance**: explain that the label and helper text transparently inform clinicians that the Pima training cohort was restricted to females aged 21+, and that entering 0 allows testing without claiming clinical validation for male cohorts.
5. Intentionally enter `0` in **Plasma Glucose**.
6. Click **"Analyse"**.
7. Show the warning banner: ClariDx caught that glucose=0 is biologically implausible and imputed it using the population median rather than treating the patient as having zero blood sugar!

### Step 5: Role Governance Demonstration
1. Click **"Sign out"**.
2. Log in as **Researcher** (`researcher@claridx.local` / `ClariDxDemo2026!`).
3. Notice that the prediction form is replaced with a **"Researcher Access (Read-Only)"** card.
4. Explain that researchers can access open research endpoints (`/features`, `/models`) via Swagger UI (`http://localhost:8000/api/v1/docs`), but HIPAA/clinical governance prevents them from running predictions on patient data.

---

## 8. Top 15 Viva / Examiner Questions & High-Scoring Answers

### Q1: Why didn't you use Deep Learning (Neural Networks / CNNs)?
> **Answer:** Tabular clinical datasets (like UCI Cleveland with 303 rows or Pima Indians with 768 rows) are relatively small. Deep learning models easily overfit on small tabular data and act as opaque black boxes. Tree-based ensembles (Random Forest, Gradient Boosting) consistently outperform neural networks on small tabular clinical benchmarks and provide exact game-theoretic SHAP tree explainability without requiring massive sample sizes.

### Q2: How did you prevent Data Leakage between train and test sets?
> **Answer:** All imputation medians, standard scalers, and categorical encoders were encapsulated strictly inside scikit-learn `Pipeline` objects. In both cross-validation and holdout evaluation, transformation parameters were learned exclusively on the training fold and applied statelessly to the validation fold. The holdout test set was held in reserve and evaluated only once.

### Q3: Why did you use both SHAP and LIME instead of just SHAP?
> **Answer:** SHAP provides global consistency based on cooperative game theory, but computing it can be computationally expensive and model-specific. LIME builds an intuitive local linear surrogate. However, literature shows that individual explainers can sometimes disagree. By computing cross-explainer agreement (Spearman rank correlation and sign consistency), ClariDx gives clinicians confidence: if both methods agree, the explanation is highly robust.

### Q4: What is the "Zero-as-Missing" problem in the Diabetes dataset?
> **Answer:** In the Pima Indians dataset, missing measurements (such as insulin, skinfold thickness, blood pressure, and glucose) were recorded as `0`. Because 0 is physiologically impossible for a living human's blood glucose or BMI, feeding 0 directly into a model severely skews the decision boundary. ClariDx differentiates valid zeros (`pregnancies = 0`) from invalid zeros (`glucose = 0`), converts the latter to `NaN`, and applies median imputation.

### Q5: Why are the predictions labeled as "Uncalibrated Scores"?
> **Answer:** Many ML models output probabilities based on softmax or tree vote fractions that do not reflect true statistical event probabilities (e.g., an uncalibrated model predicting 0.8 does not mean 80 out of 100 patients truly develop the disease). To uphold medical research integrity, ClariDx explicitly labels all predictions as uncalibrated scores (`"calibrated": false`) rather than claiming clinical calibration without Platt scaling or isotonic validation.

### Q6: Why did you choose Argon2id over bcrypt or SHA-256?
> **Answer:** SHA-256 is an unsalted cryptographic digest designed to be fast, making it vulnerable to GPU/ASIC brute-force dictionary attacks. While bcrypt is good, Argon2id is the current winner of the Password Hashing Competition (PHC). It is memory-hard and time-hard, providing resistance against GPU, ASIC, and side-channel cache attacks.

### Q7: How does your application protect against User Enumeration attacks?
> **Answer:** If an attacker attempts to log in with an email that does not exist in our database, the system executes a dummy Argon2id password verification against a simulated hash before returning HTTP 401. This guarantees that response times are identical whether an email exists or not, preventing attackers from discovering registered emails via timing analysis.

### Q8: What is the purpose of the missing-data sensitivity analysis?
> **Answer:** When required lab measurements are missing, single imputation assumes a single fixed value (like the median). If a patient's true unmeasured value is high, their actual risk could be much higher. ClariDx tests 100+ empirical background scenarios for the omitted features to compute minimum and maximum risk bounds and identify whether the omitted lab test has the power to change the binary diagnosis (`can_flip`).

### Q9: Why did you use `uv` instead of standard `pip`?
> **Answer:** `uv` is a modern, high-performance Python package manager written in Rust. It resolves and installs dependencies 10–100x faster than `pip`, enforces deterministic lockfiles, handles virtual environments natively, and ensures reproducible cross-platform builds between developer and evaluator machines.

### Q10: How do you guarantee type safety between Python and TypeScript?
> **Answer:** We have an automated script `npm run api:sync`. FastAPI automatically generates an OpenAPI 3.1 specification at `backend/app/export_openapi.py`. The frontend uses `openapi-typescript` to compile that JSON into static TypeScript definitions (`schema.d.ts`). As a result, the frontend compiler immediately catches any API parameter or response mismatch at build time.

### Q11: How does ClariDx handle user registration and role governance?
> **Answer:** ClariDx implements a dual-tier onboarding model: public account registration (`POST /api/v1/auth/register`) is available for patients, automatically binding new accounts to the least-privileged `PATIENT` role. Privileged accounts (`DOCTOR`, `RESEARCHER`, `ADMIN`) cannot be chosen or self-registered; they must be provisioned via the secure administrator command-line tool (`python -m app.cli.create_user`). This prevents privilege escalation while supporting self-service patient onboarding.

### Q12: What role-based restrictions exist for Researchers?
> **Answer:** Researchers have read-only access. They can query `/api/v1/heart/features`, `/api/v1/diabetes/features`, and model metadata to study benchmark metrics. However, any `POST` request to prediction endpoints immediately returns `HTTP 403 Forbidden`.

### Q13: How were your evaluation metrics chosen?
> **Answer:** In medical screening, accuracy alone is misleading due to class imbalances. We prioritized **ROC-AUC** (discriminative ability across all thresholds), **Recall / Sensitivity** (minimizing false negatives so sick patients aren't missed), and **Brier Score** (evaluating probability score calibration).

### Q14: How are unit tests organized and verified?
> **Answer:** The project contains 509 automated tests:
> - **302 backend tests** in `pytest` covering API routes, RBAC permission gates, JWT edge cases, pipelines, SHAP/LIME generators, multi-model consensus, prediction history, and database migrations.
> - **207 frontend tests** in `vitest` covering component rendering, landing page, theme context, form validation, state clearing, mock API integration, and error handling.

### Q15: What are the main limitations of this project?
> **Answer:** 
> 1. Datasets are historical benchmark cohorts (Cleveland heart study with 303 patients; Pima Indians study limited to Arizona Pima females $\ge 21$), so models cannot be generalized to broader global demographic populations without retraining on local clinical cohorts.
> 2. Explanations reflect model reasoning, not necessarily biological causality.
> 3. Models must undergo prospective clinical trials and probability calibration before real-world patient deployment.

### Q16: Why did you keep pregnancy count in the diabetes form instead of replacing it with biological sex?
> **Answer:** 
> 1. The underlying Pima Indians model was trained on eight specific features (`preg`, `plas`, `pres`, `skin`, `insu`, `mass`, `pedi`, `age`) from an all-female cohort aged 21+. Replacing pregnancy with sex without retraining would cause a fatal schema mismatch with the serialized scikit-learn pipelines.
> 2. Arbitrarily mapping sex to 0 pregnancies treats two biologically and statistically distinct attributes as equivalent, creating invalid risk predictions and corrupting SHAP explanations.
> 3. Retaining `preg` maintains complete compatibility with all trained models, imputers, SHAP/LIME pipelines, database schemas, and automated tests, while our enhanced UI guidance transparently communicates the demographic limitations of the benchmark training data.

---

## 9. Quick Command Cheat-Sheet for Running the Project

```bash
# 1. Start MySQL (if not running)
sudo service mysql start

# 2. Terminal 1: Start Backend (from backend/)
uv run uvicorn app.main:app --reload

# 3. Terminal 2: Start Frontend (from frontend/)
npm run dev

# 4. Run Backend Tests
cd backend && uv run pytest

# 5. Run Frontend Tests & Production Build
cd frontend && npm run check
```
