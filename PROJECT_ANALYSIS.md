w# SIH 2026 — PS26103 | Project Analysis Report
## AI-Powered Predictive Analytics & Early Warning System for Infrastructure Project Monitoring

> **Organization:** MoSPI (Ministry of Statistics & Programme Implementation)  
> **Data Source:** PAIMANA / OCMS Flash Reports | **PS ID:** 26103  
> **Dataset:** 14 Monthly Flash Reports (Jul 2025 – Aug 2026) · ~1,981 projects · ₹42.78 lakh crore aggregate cost

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [What Is Implemented ✅](#2-what-is-implemented-)
3. [What Needs To Be Done ❌](#3-what-needs-to-be-done-)
4. [Architecture Gaps & Quality Issues ⚠️](#4-architecture-gaps--quality-issues-)
5. [Better Approach — High Efficiency & Accuracy 🚀](#5-better-approach--high-efficiency--accuracy-)

---

## 1. Project Overview

The system transforms India's infrastructure monitoring from a static, monthly-report PDF format into a live, AI-powered predictive and prescriptive decision-support platform. The pipeline is:

```
14 PAIMANA PDFs
   ↓ extract_report.py      (Phase 1 — PDF Extraction)
Raw Parquet per month
   ↓ merge_reports.py       (Phase 2a — ID Reconciliation)
   ↓ clean_master.py        (Phase 2b — Cleaning & Panel Building)
   ↓ validate_master.py     (Phase 2c — Quality Checks)
project_master.parquet + project_month_panel.parquet
   ↓ build_features.py      (Phase 4/5 — Feature & Target Engineering)
feature_matrix.parquet
   ↓ train_cost_model.py    (Phase 6 — Model Training)
best_model_cost.joblib
   ↓ generate_risk_scores.py (Phase 7/8 — Risk Scoring + SHAP)
latest_risk_scores.csv
   ↓ FastAPI (backend/)     (Phase 9 — REST API)
   ↓ React (frontend/)      (Phase 10 — Dashboard)
```

---

## 2. What Is Implemented ✅

### 2.1 Data Pipeline (Phases 1–3)

| Component | File | Status | Notes |
|---|---|---|---|
| PDF Extraction Engine | `data/scripts/extract_report.py` | ✅ Complete | Table 6 targeting, multi-strategy parsing |
| Compound Field Parser | `extract_report.py` | ✅ Complete | Splits name, agency, code, PMGID from one cell |
| Date Stack Parser | `extract_report.py` | ✅ Complete | Extracts original + revised dates |
| Cost Stack Parser | `extract_report.py` | ✅ Complete | Extracts original + revised cost |
| Ministry Header Detector | `extract_report.py` | ✅ Complete | Reads ministry boundary rows within tables |
| Schema Map | `data/schema_map.yaml` | ✅ Complete | 14-month filename→month mapping, canonical ministries |
| Raw Zone Output | `data/raw_zone/` | ✅ Complete | 14× Parquet + CSV files produced |
| Extraction Logs | `data/raw_zone/extraction_logs/` | ✅ Complete | Per-month JSON logs + summary |
| ID Reconciliation / Merge | `data/scripts/merge_reports.py` | ✅ Complete | Project UID generation (code-first, hash fallback) |
| ID Crosswalk Export | `data/interim/project_id_crosswalk.csv` | ✅ Complete | CSV for manual review |
| Data Cleaning | `data/scripts/clean_master.py` | ✅ Complete | Delta features, stagnation streaks, cost revision count |
| Master / Panel Split | `data/scripts/clean_master.py` | ✅ Complete | `project_master` (static) + `project_month_panel` (time-series) |
| Validation Script | `data/scripts/validate_master.py` | ✅ Complete | Referential integrity, duplicate, null checks |
| Data Dictionary | `docs/data_dictionary.md` | ✅ Complete | All 17 raw + derived fields documented |

### 2.2 Machine Learning (Phases 4–8)

| Component | File | Status | Notes |
|---|---|---|---|
| Feature Engineering | `ml/features/build_features.py` | ✅ Complete | Ratio features, 3-month rolling delta & cost growth |
| Target Engineering | `ml/features/build_features.py` | ✅ Complete | 3-class cost overrun target (Safe/Moderate/Severe) |
| Feature Matrix Output | `ml/features/feature_matrix.parquet` | ✅ Produced | Ready for training |
| XGBoost Classifier | `ml/training/train_cost_model.py` | ✅ Complete | Multi-class, temporal train/test split at 70% |
| Temporal Validation | `train_cost_model.py` | ✅ Complete | No data leakage — trains on past, tests on future |
| Label Encoding | `train_cost_model.py` | ✅ Complete | Ministry, sector, state encoded and saved with model |
| Model Artifact Saving | `ml/models/best_model_cost.joblib` | ✅ Produced | Includes model + feature list + encoders |
| Risk Score Generation | `ml/training/generate_risk_scores.py` | ✅ Complete | Scores latest month, 0–100 portfolio-normalized scale |
| Risk Banding | `generate_risk_scores.py` | ✅ Complete | Low (<40), Medium (40–70), High (>70) |
| SHAP Explainability | `generate_risk_scores.py` | ✅ Complete | TreeExplainer on Medium/High projects |
| NLG Explanations | `generate_risk_scores.py` | ✅ Complete | Converts SHAP values to plain-language sentences |
| Risk Score Output | `ml/eda_outputs/latest_risk_scores.csv` | ✅ Produced | Sorted by risk score, ready for API |

### 2.3 Backend API (Phase 9)

| Component | File | Status | Notes |
|---|---|---|---|
| FastAPI App | `backend/app/main.py` | ✅ Complete | CORS enabled, health endpoint |
| Projects Router | `backend/app/routers/projects.py` | ✅ Complete | 3 endpoints (see below) |
| Dashboard Summary Endpoint | `GET /api/v1/dashboard/summary` | ✅ Complete | High/Med/Low counts |
| Projects List Endpoint | `GET /api/v1/projects` | ✅ Complete | Filterable by ministry + risk_band, paginated |
| Project History Endpoint | `GET /api/v1/projects/{uid}/history` | ✅ Complete | Time-series data per project |
| In-Memory Cache | `routers/projects.py` | ✅ Complete | Parquet loaded once per process start |
| Pydantic Schemas | `routers/projects.py` | ✅ Complete | `RiskScoreResponse`, `DashboardSummary` |

### 2.4 Infrastructure (Phase 10)

| Component | File | Status | Notes |
|---|---|---|---|
| Docker Compose | `docker-compose.yml` | ✅ Complete | 6 services: postgres, redis, backend, ml-service, celery, frontend, mlflow |
| Backend Dockerfile | `infra/docker/Dockerfile.backend` | ✅ Complete | Python 3.11 slim |
| Frontend Dockerfile | `infra/docker/Dockerfile.frontend` | ✅ Exists | (file present) |
| ML Service Dockerfile | `infra/docker/Dockerfile.ml` | ✅ Exists | (file present) |
| Health Checks | `docker-compose.yml` | ✅ Complete | Postgres & Redis health-checked |

### 2.5 Project Scaffolding

| Component | Status | Notes |
|---|---|---|
| Directory structure | ✅ Complete | `backend/`, `data/`, `ml/`, `frontend/`, `infra/`, `docs/` |
| `requirements.txt` | ✅ Complete | All 30+ dependencies with version pins |
| `.env.example` | ✅ Complete | Environment config template |
| `README.md` | ✅ Complete | Quick-start, tech stack, architecture |
| MLflow server | ✅ Configured in Docker | Tracking server running on port 5000 |

---

## 3. What Needs To Be Done ❌

### 3.1 Frontend Dashboard — Almost Entirely Missing

The frontend `src/` directory structure exists (`api/`, `components/`, `hooks/`, `pages/`, `store/`) **but all folders are empty** — no actual React code has been written.

**What to build:**

| Page / Component | Priority | Description |
|---|---|---|
| `pages/Dashboard.tsx` | 🔴 Critical | Executive overview: KPI cards, risk distribution donut chart |
| `pages/ProjectsTable.tsx` | 🔴 Critical | Paginated table with ministry/risk-band filters |
| `pages/ProjectDetail.tsx` | 🔴 Critical | Time-series charts (cost, progress, risk score trend) |
| `pages/Alerts.tsx` | 🟠 High | Early Warning System — sortable list of High-risk flags |
| `components/RiskBadge.tsx` | 🟠 High | Color-coded risk band chip (Low/Med/High) |
| `components/SHAPExplanationCard.tsx` | 🟠 High | Display the NLG SHAP explanation per project |
| `components/MiniSparkline.tsx` | 🟡 Medium | Inline trend chart in the table row |
| `api/client.ts` | 🔴 Critical | Axios/fetch client wired to FastAPI endpoints |
| `store/projectsSlice.ts` | 🟡 Medium | Zustand/Redux state for filters, pagination |
| `hooks/useProjects.ts` | 🟡 Medium | Data-fetching hook |

### 3.2 Backend — Many Modules Scaffolded but Empty

The `backend/app/` has many subdirectory stubs that contain zero code:

| Module | Folder | What's Needed |
|---|---|---|
| DB Models | `backend/app/models/` | SQLAlchemy ORM models for `Project`, `RiskScore`, `Alert` |
| DB Session | `backend/app/db/` | SQLAlchemy engine setup, session factory |
| Alembic Migrations | `backend/alembic/` | Migration scripts to create DB schema |
| Repositories | `backend/app/repositories/` | Data access layer (currently bypassed — reads CSV/Parquet directly) |
| Services | `backend/app/services/` | Business logic (risk scoring, alert generation) |
| ML Inference Module | `backend/app/ml_inference/` | Load model + run inference on demand |
| Core (Config, Auth) | `backend/app/core/` | `config.py` (pydantic settings), `celery_app.py`, auth middleware |
| Schemas (Pydantic) | `backend/app/schemas/` | Separate schema files per domain (currently inline in router) |
| Tests | `backend/tests/` | Unit + integration tests |
| Additional API Routers | — | `/api/v1/alerts`, `/api/v1/ministries`, `/api/v1/risk-scores/history` |

### 3.3 ML / Modeling — Significant Gaps

| Gap | Impact | What's Needed |
|---|---|---|
| **No time delay / schedule overrun model** | High | A second XGBoost/LightGBM model predicting delay risk using `revised_completion_date` vs `original_completion_date` |
| **No composite multi-target risk score** | High | Final weighted composite of cost risk + delay risk + stagnation (all three pillars of the PS) |
| **No hyperparameter tuning** | Medium | Optuna HPO loop (library already installed, not used) |
| **No model comparison** | Medium | LightGBM vs CatBoost vs XGBoost ensembles, model cards in `docs/model_cards/` |
| **No class imbalance handling** | Medium | `imbalanced-learn` is installed but SMOTE/class_weight not applied |
| **No MLflow experiment tracking** | Medium | `mlflow` is installed and Docker service exists but `train_cost_model.py` doesn't log runs |
| **Stagnation streak is a rolling sum, not a true streak** | Low | True cumulative reset-on-progress streak needed |
| **Sector column is always 'Unknown'** | Medium | Map ministry → sector using the 22-sector taxonomy from the PS |
| **No EDA notebooks** | Low | `ml/notebooks/` is empty — EDA + model selection notebook needed |
| **DVC data versioning not initialized** | Low | `dvc` installed but no `.dvc/` config or pipeline file |

### 3.4 Data Quality — Outstanding Issues

| Issue | Description | Fix Needed |
|---|---|---|
| **`project_id_crosswalk.csv` not human-validated** | Fuzzy UID collisions may exist | Manual review + RapidFuzz-based grouping |
| **Sector not extracted** | `sector` column defaults to `'Unknown'` everywhere | Parse from PDF context or use ministry→sector mapping |
| **LOCF imputation skipped** | `clean_master.py` notes it as TODO | Last-observation-carry-forward for missing cost/progress months |
| **Outlier flagging skipped** | `clean_master.py` notes it as TODO | Flag implausible values (e.g., progress > 100, negative costs) |
| **Revised completion date not used in features** | Schedule delay signal missing from feature matrix | Add `schedule_delay_months` feature |
| **No Table 3 / Table 4 extraction** | Completed + new projects are skipped | Extract and track entry/exit events |
| **`data/validation/` folder is empty** | Pandera & great_expectations schemas not defined | Write schema validation contracts |

### 3.5 Infrastructure & DevOps

| Gap | Description |
|---|---|
| **GitHub Actions CI/CD** | `.github/workflows/` directory missing — no automated testing or deployment |
| **Nginx config** | `infra/nginx/` is empty — reverse proxy config for frontend not written |
| **Prometheus / Grafana monitoring** | `infra/monitoring/` is empty — no scrape configs or dashboards |
| **Frontend package.json** | Missing — cannot run `npm install` or build |
| **No production CORS hardening** | `allow_origins=["*"]` must be restricted to frontend URL before deployment |
| **Celery tasks not implemented** | Docker Compose has `celery-worker` service, but no task definitions in `backend/app/core/celery_app.py` |
| **Redis not used** | Configured in Docker Compose, but no caching logic in the API |

### 3.6 Early Warning System

The problem statement's "Early Warning System" is partially visible in the risk scoring output but the explicit alert engine is missing:

| Component | Status | What's Needed |
|---|---|---|
| Rule-based alert triggers | ❌ Missing | Alert if `cost_revision_count > 3`, `progress_stagnation_streak >= 3`, `expenditure_pct > 90%` |
| ML-triggered alerts | ❌ Missing | Alert when `risk_score > 70` and rising trend |
| Alert persistence | ❌ Missing | Store alerts in PostgreSQL, track if acknowledged |
| Alert notification | ❌ Missing | Email / webhook dispatch for new High-risk flags |

---

## 4. Architecture Gaps & Quality Issues ⚠️

> [!WARNING]
> The following issues would cause problems if the system were deployed as-is.

### 4.1 Data Leakage Risk in Feature Engineering

**Current:** `build_features.py` uses the project's **ultimate final-state outcome** (last row per project) as the target, but associates it with **every row** in the panel dataset, including early rows. This is a form of **look-ahead bias** — a model trained this way "knows" the final outcome while seeing early features.

**Fix:** Use a true T → T+K horizon: for each observation at month T, the target should be the project's state at month T+K (e.g., K=3 months ahead). `build_features.py` acknowledges this with a comment but does not implement it.

### 4.2 In-Memory Caching is Not Thread-Safe

The global `_scores_cache`, `_master_cache`, `_panel_cache` pattern in the FastAPI router will cause race conditions under concurrent requests. Use `functools.lru_cache` or a startup `lifespan` event to load once.

### 4.3 LabelEncoder on Categorical Features — Fragile

`LabelEncoder` imposes a numeric ordering on nominal categories (ministry, state) which XGBoost treats as ordinal. Use `OrdinalEncoder` or native categorical support in XGBoost (`enable_categorical=True`) to avoid this implicit ordering artifact.

### 4.4 Risk Score Normalization is Portfolio-Relative

Dividing by the max score within a batch makes the scores **relative to the current portfolio**, not absolute. A project that was 80/100 last month might be 60/100 this month simply because other projects got worse, not because it improved.

### 4.5 Backend Reads Files Directly Instead of Using Database

The backend reads CSV/Parquet files directly at query time. This is fine for a hackathon demo but:
- No concurrent write safety
- No indexing → full table scans on every request
- Cannot support user-specific alert acknowledgements

---

## 5. Better Approach — High Efficiency & Accuracy 🚀

> [!NOTE]
> These are architectural and algorithmic recommendations to take the system from hackathon-quality to production-grade.

### 5.1 Fix Temporal Leakage — Use a Proper Forecasting Horizon

```python
# Instead of using last-state outcome for all rows:
# For each (project, month_T), target = state at month T+3
HORIZON = 3  # months ahead

def build_targets_with_horizon(panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
    panel = panel.sort_values(['project_uid', 'report_month'])
    panel['future_revised_cost'] = (
        panel.groupby('project_uid')['revised_cost_cr']
             .shift(-horizon)
    )
    panel['cost_growth_3m'] = (
        (panel['future_revised_cost'] - panel['revised_cost_cr'])
        / panel['revised_cost_cr'].replace(0, np.nan)
    )
    # Classify into risk buckets as before
    ...
```

This turns the model into a genuine **3-month cost escalation forecaster**, which is the stated goal of the PS.

### 5.2 Replace XGBoost LabelEncoder with Native Categoricals

```python
# Use XGBoost's built-in categorical support — no ordinal assumptions
model = xgb.XGBClassifier(
    enable_categorical=True,
    tree_method='hist',       # Required for categoricals
    ...
)
# Mark columns as pandas Categorical dtype instead of label encoding
for col in ['ministry', 'sector', 'state']:
    X_train[col] = X_train[col].astype('category')
    X_test[col] = X_test[col].astype('category')
```

This eliminates the spurious ordinal relationship and improves model accuracy on ministry/state splits.

### 5.3 Use a Gradient Boosted Ensemble + Optuna Tuning

Instead of a single XGBoost model with default hyperparameters, use a **soft-voting ensemble** of XGBoost + LightGBM + CatBoost, tuned with Optuna:

```python
import optuna
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import xgboost as xgb

def objective(trial):
    params = {
        "n_estimators":  trial.suggest_int("n_estimators", 100, 600),
        "max_depth":     trial.suggest_int("max_depth", 3, 9),
        "learning_rate": trial.suggest_float("lr", 0.01, 0.3, log=True),
        "subsample":     trial.suggest_float("subsample", 0.5, 1.0),
    }
    model = xgb.XGBClassifier(**params)
    cv_scores = cross_val_score(model, X_train, y_train, cv=TimeSeriesSplit(n_splits=5))
    return cv_scores.mean()

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=100)
```

**Expected improvement:** Ensemble + HPO typically yields +5–15% macro-F1 over a single untuned baseline.

### 5.4 Add a Schedule Delay Model + Composite Risk Score

```
composite_risk = (
    0.45 × cost_overrun_prob_severe    # From XGBoost cost model
  + 0.35 × delay_prob_severe           # From LightGBM delay model
  + 0.20 × stagnation_rule_score       # Rule-based: streak × revision_count
)
```

A `delay_prob_severe` model would use:
- `schedule_delay_months = revised_completion_date - original_completion_date`
- `delay_growth_velocity` (delta over last 3 months)
- `expenditure_vs_progress_gap` (spending fast but not progressing → classic delay signal)

### 5.5 Exploit the Time-Series Structure

For each project, the longitudinal nature of the data (14 monthly snapshots) should be exploited explicitly via **lag feature explosion** — the best approach given the hackathon scope:

```python
for lag in [1, 2, 3]:
    df[f'cost_lag_{lag}']     = df.groupby('project_uid')['revised_cost_cr'].shift(lag)
    df[f'progress_lag_{lag}'] = df.groupby('project_uid')['physical_progress_pct'].shift(lag)

# Exponentially weighted moving average of progress
df['ewma_progress'] = df.groupby('project_uid')['physical_progress_pct'].transform(
    lambda x: x.ewm(span=3).mean()
)
```

This gives the model a "memory" of where the project was, not just its current state. For a v2 production system, replace with a **Temporal Convolutional Network (TCN)** feeding the full 14-month sequence per project.

### 5.6 Replace CSV-Based API with Proper DB + Cache Pattern

```
FastAPI request
   → Redis cache (TTL: 5 min for summary, 1 min for project list)
   → On miss: query PostgreSQL (indexed on ministry, risk_band, risk_score)
   → Write result to Redis → return
```

Proposed schema:
```sql
CREATE TABLE risk_scores (
    project_uid  TEXT        NOT NULL,
    scored_month DATE        NOT NULL,
    risk_score   NUMERIC(5,2),
    risk_band    TEXT,
    shap_summary TEXT,
    PRIMARY KEY (project_uid, scored_month)
);
CREATE INDEX idx_risk_scores_band ON risk_scores(risk_band, risk_score DESC);
```

This supports **historical risk score trend queries**, alert history, and concurrent writes from the Celery retraining job.

### 5.7 Implement Interactive SHAP Waterfall Explanations

The current NLG is template-based (a few `if feat == "..."` branches). A more robust approach:

1. **Pre-compute `shap.Explanation` waterfall values** for every Medium/High project after each scoring run — store them as JSON in the DB.
2. **In the frontend**, render an interactive SHAP waterfall bar chart with Recharts or D3 showing which feature pushed the score up or down. This is far more convincing to evaluators than a template sentence.

### 5.8 Add a Rule-Based Early Warning Layer

Alongside the ML model, add deterministic rules that catch edge-cases the model might miss (especially for projects with < 3 months of history):

```python
RULES = [
    {"name": "Cost Tripled",       "condition": lambda r: r.revised_cost_cr > 3 * r.original_cost_cr,       "weight": 30},
    {"name": "Stagnant 6+ months", "condition": lambda r: r.progress_stagnation_streak >= 6,                 "weight": 25},
    {"name": "Near-zero progress", "condition": lambda r: r.physical_progress_pct < 5 and r.cost_revision_count > 2, "weight": 20},
    {"name": "Over-expenditure",   "condition": lambda r: r.expenditure_cr > r.revised_cost_cr * 0.95 and r.physical_progress_pct < 80, "weight": 25},
]
```

The composite score becomes `max(ml_risk_score, rule_score)` so the rule layer acts as a **guaranteed floor** for obvious disasters.

### 5.9 Data Extraction — Add a 3-Tier PDF Fallback Chain

The current extractor relies solely on `pdfplumber`. Improve robustness with a 3-tier fallback:

```
Tier 1: pdfplumber   — vector PDF text extraction (fast, accurate)
   ↓ if table yields < 50 rows
Tier 2: camelot-py   — lattice mode (better for complex bordered tables)
   ↓ if still < 50 rows
Tier 3: pdf2image → pytesseract — OCR (for scanned / image PDFs)
```

All three libraries are already installed in `requirements.txt`. This ensures even poorly-digitized PDFs are recovered.

### 5.10 MLflow Experiment Tracking Integration

Add ~10 lines to `train_cost_model.py` to log every training run — the MLflow Docker service is already configured but completely unused:

```python
import mlflow

with mlflow.start_run(run_name=f"xgboost_cost_{datetime.now():%Y%m%d_%H%M}"):
    mlflow.log_params(model.get_params())
    mlflow.log_metric("macro_f1", macro_f1)
    mlflow.log_metric("roc_auc", roc_auc)
    mlflow.xgboost.log_model(model, "model")
    mlflow.log_artifact(str(model_path))
```

This makes it trivial to compare runs after Optuna HPO and know exactly which model artifact is currently in production.

---

## Summary Scoreboard

| Domain | Completeness | Critical Next Step |
|---|---|---|
| **Data Pipeline (PDF→Parquet)** | ~70% | LOCF imputation, sector mapping, Pandera schemas |
| **Feature Engineering** | ~50% | Fix T→T+K horizon, add lag features, schedule delay |
| **ML Modeling** | ~40% | Delay model, composite score, HPO, MLflow logging |
| **Backend API** | ~20% | DB integration, alerts router, fill all empty stubs |
| **Frontend Dashboard** | ~2% | Build everything — all `src/` dirs are empty |
| **Early Warning System** | ~15% | Rule engine, alert DB, notification system |
| **Infrastructure** | ~30% | Nginx, CI/CD, Prometheus, Redis caching, Celery tasks |
| **Documentation** | ~25% | API docs, model cards, architecture diagrams |

> [!IMPORTANT]
> **The single most critical gap is the frontend.** All backend data is produced and served via working API endpoints. The React dashboard is the primary user-facing deliverable and evaluators will interact with it. Starting there immediately is the highest-leverage action.

---

*Analysis performed: 2026-10-29 | File references are relative to project root `c:\Users\Hp\Desktop\New folder\`*
