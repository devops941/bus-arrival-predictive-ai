# BusArrival AI: Predictive Public Transit Arrival-Time Intelligence

**Final-Year Project | Domain: Transport & Smart Cities**

BusArrival AI is a predictive arrival-time intelligence platform for public transit networks. It replaces static timetables with classic machine learning arrival forecasts factoring in historical delay trends, cyclical time of day, calendar day types, corridor distance, stop sequences, and weather shocks.

Built as a full-featured multi-page dashboard website featuring role-based access control (Passenger, Analyst, Admin), interactive inline data entry, model training & registry comparison, confidence-banded ETA predictions (P50 median and P90 conservative intervals), accuracy diagnostics, and automated Excel/PDF reports.

---

## Hard Rules & Principles

1. **No Streamlit / Dash:** Full-stack architecture using a React 18 + TypeScript (Vite) frontend with Tailwind CSS and shadcn/ui calling a Python FastAPI REST API.
2. **MongoDB Atlas via `.env` Only:** All connection strings and secrets reside strictly in `.env`. Real credentials are never committed.
3. **Python Owns All Logic:** Feature engineering, machine learning pipelines, evaluation metrics, and report compilation execute exclusively in Python.
4. **Light Theme Only:** Transit-themed color system with high readability and accessible visual contrast (Section 9 tokens).
5. **Classic Machine Learning:** Explainable, honest models (Ridge Regression, Random Forest, Gradient Boosting, Quantile GB) with confidence intervals and error bounds. No black-box deep learning.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Table & Query, Lucide React, Recharts, `cmdk`, `sonner` |
| **Backend** | FastAPI, Uvicorn, Pydantic v2, `pydantic-settings`, SlowAPI Rate Limiting |
| **Database** | MongoDB Atlas via PyMongo (with schema validators & indexes) |
| **Authentication** | PyJWT, bcrypt password hashing, lockout guards (5 failed attempts), audit logging |
| **Data & ML** | NumPy, SciPy, scikit-learn, joblib, pure mathematical pipelines |
| **Reporting** | Jinja2, openpyxl, CSV |
| **Testing** | unittest, pytest, Node.js built-in test runner |

---

## Directory Structure

```
busarrival-ai/
├── PROJECT_SPEC_BUSARRIVAL.md   # Complete system specification
├── README.md                    # Project documentation & setup guide
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Multi-container orchestration
├── .env.example                 # Environment template with placeholders
├── .gitignore                   # Excludes .env, frontend/.env, outputs, etc.
├── backend/                     # FastAPI application entry points and routers
│   ├── main.py                  # API server & startup config validation
│   ├── deps.py                  # Dependency injection & rate limiters
│   ├── security.py              # Password hashing & JWT token management
│   └── routers/                 # 12 REST API routers (auth, predict, models, etc.)
├── src/                         # Core Python business logic & data pipeline
│   ├── config.py                # Fail-fast pydantic-settings configuration
│   ├── db/                      # PyMongo connections, repositories & schemas
│   ├── data/                    # Synthetic generator, validation & GTFS CSV ingestion
│   ├── analytics/               # Delay trend calculations & 2D heatmap matrix
│   ├── ml/                      # Feature pipeline, models, CV & evaluation
│   └── report/                  # Excel, CSV & HTML report generators
├── frontend/                    # React 18 + TypeScript + Vite UI
│   ├── src/
│   │   ├── api/client.ts        # Typed API client with auto-refresh interceptor
│   │   ├── components/          # KpiCard, EtaCard, RouteLineDiagram, DelayHeatmap, etc.
│   │   ├── context/             # AuthContext, FilterContext
│   │   ├── pages/               # Dashboard, ETA, Trends, DataEntry, Models, Accuracy, Admin
│   │   └── styles/              # Section 9 transit tokens & globals.css
│   └── tests/                   # Frontend unit tests
├── scripts/                     # Seed scripts, admin creation, and demo journey
│   ├── seed.py                  # Idempotent database seeder
│   ├── create_admin.py          # Admin account initial setup
│   └── demo_journey.py          # End-to-end autonomous lifecycle simulation
├── tests/                       # Full Python backend test suite (57 tests)
├── docs/                        # Design tokens, wireframes, GTFS mapping, final report, presentation slides
└── outputs/                     # Persisted models (.joblib) and reports (.xlsx)
```

---

## Setup & Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11 / 3.15)
- Node.js 18+ and npm
- A MongoDB Atlas cluster connection URI

### 2. Environment Configuration
Create a local `.env` file by copying `.env.example`:

```bash
# On Linux / macOS
cp .env.example .env

# On Windows PowerShell
Copy-Item .env.example .env
Copy-Item frontend\.env.example frontend\.env
```

Open `.env` in your editor and configure:
1. **`MONGODB_URI`**: Paste your MongoDB Atlas connection string. URL-encode any special characters in the password.
2. **`JWT_SECRET`**: Set a random string of at least 32 characters for signing JWT tokens.

> **Security Notice:** Never commit `.env` or paste real credentials into `.env.example`, tests, or commits. Both `.env` and `frontend/.env` are ignored by Git.

### 3. Backend Setup & Startup
Install Python dependencies and run the server:

```bash
pip install -r requirements.txt

# Run backend REST API server
python backend/main.py
# Server runs on http://127.0.0.1:8000 (Swagger docs at /docs)
```

### 4. Frontend Setup & Startup
```bash
cd frontend
npm install
npm run dev
# Vite UI runs on http://127.0.0.1:5173
```

---

## Automated Verification & Tests

### Backend Test Suite (54 Tests)
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Frontend Typechecking & Unit Tests
```bash
# Verify zero TypeScript compile errors
cd frontend && npx tsc --noEmit

# Run frontend unit tests
node --test frontend/tests/utils.test.mjs frontend/tests/components.test.mjs

# Build production bundle
npm run build
```

### End-to-End Autonomous Journey Demo
Simulates the entire system lifecycle (Admin Login &rarr; Feature Extraction &rarr; Model Training &rarr; Model Activation &rarr; Real-time ETA Prediction &rarr; Excel Report Generation):
```bash
python scripts/demo_journey.py
```

---

## Implementation Roadmap

- [x] **Phase 1: Setup and Design** - Repository structure, requirements, `.env.example`, fail-fast configuration (`src/config.py`), design tokens, and ASCII wireframes.
- [x] **Phase 2: MongoDB and Auth** - PyMongo integration, collection validators, JWT auth with bcrypt and lockout, `/api/health`, and admin bootstrap script.
- [x] **Phase 3: Seed Data & Data-Entry APIs** - Synthetic data generator, CRUD routes, CSV import with validation report.
- [x] **Phase 4: Analytics and Trends** - Delay aggregation by hour, day type, route, and stop; delay heatmaps; hand-calculated tests.
- [x] **Phase 5: Feature Engineering** - Leakage-free time-aware features, rolling delays, and feature cache.
- [x] **Phase 6: Models and Validation** - Ridge, Random Forest, Quantile Gradient Boosting; time-series CV and leave-route-out evaluation.
- [x] **Phase 7: Model Registry & ETA Service** - Active model management, `/predict/eta` with confidence bands, and drift monitoring.
- [x] **Phase 8: Accuracy, Alerts & Reports** - Accuracy metrics dashboard, PDF/Excel reports, and admin logging.
- [x] **Phase 9: Frontend Foundation** - React 18 + Vite + Tailwind setup, authentication screens, route guards, `cmdk` command palette.
- [x] **Phase 10: Dashboard & Predictor UI** - Live ETA cards, route line diagram, trend explorer, and heatmaps.
- [x] **Phase 11: Data Entry & Model Management UI** - Inline editable tables, CSV import wizard, model comparison, feature preview.
- [x] **Phase 12: System Integration & Polish** - Alerts, reports download, admin governance, methodology, profile, landing page, and demo script.
- [x] **Phase 13: Real Data (GTFS Static)** - Automatic column mapping for GTFS `routes.txt`, `stops.txt`, `stop_times.txt`, and sample files.

---

## Deliverables Checklist (Section 17)

- [x] **Website:** Landing, login/register/forgot, role-based dashboard (React 18 + Vite + Tailwind, Section 9 transit tokens).
- [x] **Data Entry & CSV Import:** Interactive inline-editable tables with quick-add, 4-step CSV and GTFS import wizard with validation table and audit logging.
- [x] **Analytics & ML Suite:** Trend explorer, 2D heatmaps, leakage-free feature pipeline, model training wizard and registry, confidence-banded ETA predictor (P50/P90), accuracy dashboard.
- [x] **Reports Engine:** Multi-format downloads for Excel (`.xlsx`), PDF, and CSV with corridor KPI summaries.
- [x] **FastAPI & MongoDB:** 12 REST API routers with Swagger docs (`/docs`), MongoDB Atlas connected strictly via `.env` with fail-fast validation.
- [x] **Documentation & Scripts:** Comprehensive README, autonomous demo script (`scripts/demo_journey.py`), 57 backend tests, final academic report ([docs/final_report.md](docs/final_report.md)), and presentation slides ([docs/presentation_slides.md](docs/presentation_slides.md)).
- [x] **Future Work Roadmap:** Ingestion of live GTFS-realtime streams, dynamic weather and traffic API feeds, passenger-load prediction, and mobile notifications.

---

## References (Section 19)

- **Hastie, Tibshirani, Friedman:** *The Elements of Statistical Learning: Data Mining, Inference, and Prediction* (Springer).
- **Scikit-learn Documentation:** Regression, ensemble estimators, quantile loss optimization, `TimeSeriesSplit`, and `GroupKFold`.
- **MobilityData:** General Transit Feed Specification (GTFS Static) Reference.
- **MongoDB Atlas & PyMongo:** Production driver patterns, JSONSchema collection validators, and index strategies.
- **Modern Web Stack:** FastAPI, React 18, Vite, Tailwind CSS, TanStack Table & Query, Recharts, and Lucide React.
- **Transportation Research:** Empirical transit arrival time prediction literature (historical baseline comparison, cascade delay propagation, and probabilistic confidence bounds).
