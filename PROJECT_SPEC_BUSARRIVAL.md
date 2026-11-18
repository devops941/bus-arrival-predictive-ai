# BusArrival AI: Predictive Public Transit Arrival-Time Intelligence (Dashboard Website)

**Type:** Final-year project | **Domain:** Transport & Smart Cities
**Product style:** Real multi-page **dashboard website** with **login screens, roles, and data entry inside the dashboard**. Clean **light theme**, transit-themed colours, advanced neat UI. NOT Streamlit.
**Stack:** React 18 + TypeScript (Vite) + Tailwind + shadcn/ui, FastAPI, Python (pandas, NumPy, SciPy, scikit-learn), **MongoDB Atlas (PyMongo)**, config in **`.env`**.

> **Instructions for Claude Code:** Read this whole file. Build phase by phase using the prompts in Section 14. After each phase run tests and check acceptance criteria before moving on. Ask only if truly blocked.
> **Hard rules:**
> 1. No Streamlit/Dash. UI = React + Vite + TypeScript calling a FastAPI REST API.
> 2. Database = MongoDB Atlas via PyMongo. All secrets/settings live in `.env` only. Never write a real credential into any committed file (`.env.example`, README, tests, comments). Developer pastes the real URI into the local git-ignored `.env`.
> 3. Python owns all calculations, feature engineering, model training, evaluation and reports. React only collects input and displays results.
> 4. Light theme only, following Section 9 tokens.
> 5. App opens already populated with seed data; every table supports create/edit/delete from the UI.
> 6. Use classic ML only (regression, tree ensembles). No deep learning. Models are honest estimates, always shown with error ranges.

---

## 1. Vision
Passengers and transit operators need reliable bus arrival times. Scheduled times ignore traffic, time of day and recent delays. BusArrival AI lets a user log in, enter or import **routes, stops, trips and observed arrival/delay records**, then:
- **Passenger view:** pick route + stop + time and get an **ETA with a confidence range** (P50 and P90) and a reliability label.
- **Operator view:** explore **historical delay trends** (by hour, day type, route, stop), train and compare **prediction models**, track **accuracy and error distributions per route**, and generate **reports**.

## 2. Objectives
1. Light-themed website with landing page, login/register, role-based dashboard.
2. Data entry and CSV import with clear validation (missing, duplicate, invalid values).
3. Feature engineering from route distance, stop count, time of day, day type and delay history.
4. Train/compare models (baseline, Ridge, Random Forest, Gradient Boosting, quantile model for intervals) with **time-aware and route-level validation**.
5. Model management: train, compare, activate, roll back, store metrics.
6. Forecast comparison and accuracy dashboard (predicted vs actual, error distributions, per-route accuracy).
7. Reports as PDF/Excel/CSV.
8. All data in MongoDB, configured only via `.env`.

## 3. Scope
**In:** auth, roles, routes/stops/trips/observations CRUD, CSV import, trend explorer, feature pipeline, model training and registry, ETA prediction API and UI, accuracy dashboard, alerts for degraded accuracy, reports, admin. **Out:** live GPS/GTFS-realtime feeds (CSV import instead; future work), payments, native mobile apps, deep learning.

## 4. Roles and Login Screens
| Role | Access |
|---|---|
| **Passenger/Viewer** | ETA predictor, route and delay explorer (read-only) |
| **Analyst** | Viewer + data entry, import, feature views, train/compare models, reports |
| **Admin** | Everything + users, activate/rollback models, master data, audit log, jobs |

Screens: Login (email/password, show/hide, remember me, errors, loading), Register (strength meter), Forgot/Reset (admin-issued token, no email needed), Profile. JWT access + refresh, route guards, bcrypt, rate limiting and lockout (5 fails). First admin via `scripts/create_admin.py` from `.env`.

## 5. Data Entry and Sources
| Dataset | Fields |
|---|---|
| Routes | route_no, name, origin, destination, total_distance_km, scheduled_headway_min, active |
| Stops | stop_code, name, lat, lon |
| Route-stops | route_id, stop_id, sequence, distance_from_start_km, scheduled_offset_min |
| Trips | route_id, direction, date, scheduled_start, vehicle_id, day_type |
| Arrival observations | trip_id, stop_id, scheduled_arrival, actual_arrival, delay_min (derived), passengers_optional, weather_optional |
| Delay events (optional) | route_id, date, time, cause (traffic, breakdown, rain, event), minutes |

Sources for real use: municipal transit open data, GTFS static files, agency CSVs. **Seed data** (`scripts/seed.py`): 6-8 routes, 40-60 stops, 60-90 days of trips with synthetic delays (rush-hour effect, day-type effect, route congestion, rain shocks, delay carry-over along the stops), plus deliberately messy rows (duplicates, negative or absurd delays, actual before scheduled by hours, missing stop, unknown route). Label all seed data **"illustrative demo data"** in UI and README.

Validation rules (Pydantic + UI messages): required fields; distances > 0; stop sequence unique and increasing per route; times parseable; actual arrival within plausible window of scheduled (configurable, e.g. -10 to +120 min) else warning; duplicates on (trip, stop) with keep-first/last/average choice; unknown route/stop mapping warning; outliers by median ± k·MAD flagged; CSV import shows a row-level error table with an "import valid rows only" option. All writes go to the audit log.

## 6. System Flow
```
Login -> role dashboard
 [1] Data entry / import -> validation -> MongoDB
 [2] Trend explorer (delay by hour, day type, route, stop)
 [3] Feature engineering (Python): distance, stop count, stops remaining, hour (sin/cos), peak flag, day type, headway,
     rolling delay at the route/segment, previous-stop delay, previous-trip delay, weather flag
 [4] Model engine: baseline vs Ridge vs RandomForest vs GradientBoosting (+ quantile for P50/P90)
 [5] Validation: chronological split + leave-route-out; MAE, RMSE, MAPE, within-2-min %, bias, error distributions
 [6] Model registry: store metrics + artifact, compare, activate / rollback
 [7] ETA service: input route, stop, time -> ETA + range + reliability
 [8] Accuracy dashboard + alerts when active model degrades
 [9] Reports (PDF / Excel / CSV)
```
Training and bulk feature builds run as FastAPI background tasks with status polling.

## 7. Methods
### 7.1 Target and baselines
Target = **delay_min = actual − scheduled** at a stop (or travel time between stops). Predicted ETA = scheduled arrival + predicted delay.
Baselines: (a) schedule-only (delay 0), (b) historical mean delay by route × hour × day type, (c) average-speed travel-time estimate from distance.
### 7.2 Features
`route_distance_km`, `distance_to_stop_km`, `stop_count_remaining`, `stop_sequence`, `hour_sin/cos`, `is_peak`, `day_of_week`, `day_type` (weekday/weekend/holiday), `scheduled_headway`, `recent_route_delay_mean` (last N trips, computed only from past data), `prev_stop_delay`, `prev_trip_delay`, `rain_flag`. **No leakage:** every history feature uses only data available before the prediction time (unit-tested).
### 7.3 Models
Ridge (scaled), RandomForestRegressor, GradientBoostingRegressor (or HistGradientBoosting), and **quantile gradient boosting** (alpha 0.5 and 0.9) for P50/P90. Hyperparameters via small grid with time-series CV. Fixed random seeds. Artifacts saved with `joblib` + metadata (features list, versions, train window).
### 7.4 Validation
- **Chronological split** (train earlier, test latest weeks); `TimeSeriesSplit` for tuning.
- **Route-level validation:** leave-one-route-out (GroupKFold by route) to test generalisation to unseen routes.
- Metrics: MAE, RMSE, MAPE (guarded for tiny denominators), **% within ±2 min**, bias (mean error), P90 interval coverage. Error distributions (histogram/box) overall and by route, hour, day type.
- Model beats baseline only if improvement is shown on held-out data; otherwise UI says so.
### 7.5 ETA output and reliability
Return ETA (P50), upper ETA (P90), expected delay, and a reliability label (High/Medium/Low from interval width and historical error for that route/hour). Disclaimer: estimate, not guarantee.
### 7.6 Drift / alerts
Compare recent rolling MAE against the active model's validation MAE; raise an alert when it exceeds a configurable ratio. Admin can retrain.

## 8. Stack
| Layer | Choice |
|---|---|
| Web | React 18, TypeScript, Vite |
| UI | Tailwind, shadcn/ui (Radix), lucide-react |
| Charts | Recharts + small custom SVG (heatmap, route line diagram, gauge) |
| Tables / forms | TanStack Table, React Hook Form + Zod |
| Data / routing | TanStack Query, React Router |
| UX extras | framer-motion, sonner, cmdk, @fontsource/inter |
| Map (optional) | Leaflet + OpenStreetMap tiles for stops/routes |
| Backend | FastAPI, Uvicorn, Pydantic v2, pydantic-settings |
| Auth | PyJWT, bcrypt, slowapi |
| DB | MongoDB Atlas via PyMongo |
| Analytics / ML | pandas, NumPy, SciPy, scikit-learn, joblib |
| Reports | Jinja2, matplotlib, weasyprint, openpyxl |
| Scheduler | APScheduler (optional nightly retrain/drift check) |
| Tests | pytest + httpx, Vitest + RTL, optional Playwright |
| Quality | ruff, black, ESLint, Prettier, Git |
| Deploy | Docker + docker-compose (optional) |

## 9. UI / UX Design System (light, transit themed)
Goals: neat, clear, bright, data-dense but uncluttered; loading skeletons, empty states, error states everywhere; light theme only.

| Token | Value | Use |
|---|---|---|
| bg-base | `#F6F8FB` | App background |
| surface | `#FFFFFF` | Cards, sidebar, top bar |
| bg-subtle | `#EDF1F7` | Table headers, inputs, hover |
| border | `#DCE3EE` | Dividers |
| text-primary | `#0F1E33` | Main text |
| text-secondary | `#4A5C75` | Secondary |
| text-muted | `#7C8CA3` | Hints |
| primary (transit blue) | `#1D4ED8` (hover `#1E40AF`, soft `#DBEAFE`) | Buttons, active nav |
| on-time | text `#15803D`, chart `#22C55E`, soft `#DCFCE7` | On-time, good accuracy |
| minor-delay (amber) | text `#B45309`, chart `#F59E0B`, soft `#FEF3C7` | Minor delay, warnings |
| major-delay | text `#B91C1C`, chart `#EF4444`, soft `#FEE2E2` | Late, errors |
| prediction | text `#6D28D9`, chart `#8B5CF6`, soft `#EDE9FE` | Model predictions, intervals |
| teal | `#0D9488` | Schedule/reference line |

Semantic mapping: schedule = teal dashed, actual = blue, prediction = violet with P50–P90 band, early/on-time = green, delay = amber → red. Route colour palette: blue, emerald, amber, rose, violet, sky, lime, orange. Cards: 1px border + soft shadow; radius 12 (cards) / 8 (inputs); Inter font with tabular numbers; 8px grid; WCAG AA; never colour alone (icons + labels for delay status). Focus ring visible. Motion 150-200 ms, respects reduced-motion.

**Components:** collapsible sidebar, top bar (route/stop selector, date range, Ctrl+K command palette, notifications, user menu), `KpiCard` with delta + sparkline, `DataTable` (sort, filter, column toggle, pagination, inline edit, quick-add row, CSV export), `StatusBadge`, `EtaCard` (big ETA, P90 range bar, reliability chip), `RouteLineDiagram` (stops along a line with predicted delays), `DelayHeatmap` (hour × weekday), `TrendChart`, `PredVsActualScatter`, `ErrorHistogram`, `RouteAccuracyBars`, `ModelCompareBars`, `FeatureImportanceBars`, `ReliabilityGauge`, stepper wizard, import wizard (upload → map columns → validation table → commit), side drawers, confirm dialogs, toast with undo.

**Login screen:** split layout; left brand panel with soft blue gradient (`#EAF1FF` → `#F6F8FB`) and subtle route-line SVG, tagline "Know when your bus arrives.", three value points; right white form card with soft shadow. Stacks on mobile.

## 10. Environment (`.env`)
`.env` and `frontend/.env` are git-ignored; only `.env.example` files with placeholders are committed.
```env
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173

# Paste the real Atlas URI ONLY in your local .env. URL-encode special characters in the password.
MONGODB_URI=mongodb+srv://<db_user>:<url_encoded_password>@<cluster-host>/?retryWrites=true&w=majority
MONGODB_DB_NAME=busarrival
MONGODB_TEST_DB_NAME=busarrival_test
MONGODB_TIMEOUT_MS=8000

JWT_SECRET=change-me-to-a-long-random-string
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=7
MAX_FAILED_LOGINS=5
LOCKOUT_MINUTES=15
ADMIN_EMAIL=admin@busarrival.local
ADMIN_PASSWORD=change-me-strong

MODEL_DIR=outputs/models
REPORT_DIR=outputs/reports
UPLOAD_DIR=data/uploads
MAX_UPLOAD_MB=10
RANDOM_SEED=42
DRIFT_RATIO_THRESHOLD=1.3
SCHEDULER_ENABLED=false
```
`frontend/.env.example`: `VITE_API_BASE_URL=http://localhost:8000/api`, `VITE_APP_NAME=BusArrival AI`.
Rules: pydantic-settings, fail fast on missing/placeholder `MONGODB_URI` or `JWT_SECRET`; `/api/health` pings DB; use a least-privilege Atlas user (readWrite on this DB only); never log the URI.

## 11. MongoDB Collections
`users`, `routes`, `stops`, `route_stops`, `trips`, `observations` (indexes: unique (trip_id, stop_id); (route_id, scheduled_arrival)), `delay_events`, `features_cache` (keyed by data_version), `models` (name, algorithm, params, features, train_window, metrics, route_metrics, artifact_path, status: candidate|active|archived, created_by, created_at), `predictions_log` (inputs, eta_p50, eta_p90, model_id, later actual for accuracy tracking), `accuracy_snapshots`, `alerts`, `import_jobs`, `reports`, `audit_log`, `job_runs`.
Rules: repositories layer only (no PyMongo in route handlers); `jsonSchema` validators on users/routes/observations; idempotent seeding with `bulk_write` upserts; `data_version` counter invalidates caches; tests use `MONGODB_TEST_DB_NAME`, never the main DB.

## 12. API (all under `/api`, Pydantic validated, errors as `{detail, code, fields}`)
Health; Auth (register, login, refresh, logout, me, change-password, forgot, reset); CRUD for routes, stops, route-stops, trips, observations, delay-events; `POST /import/{kind}` + issues + commit; `GET /analytics/delay-trends` (by hour/day-type/route/stop), `/analytics/heatmap`, `/analytics/route-summary`; `POST /features/build`; `POST /models/train` (background) + status, `GET /models`, `GET /models/{id}`, `POST /models/{id}/activate`, `/rollback`, `GET /models/compare`; `POST /predict/eta`, `GET /predict/route/{id}` (delays along the route); `GET /accuracy/overview`, `/accuracy/errors`, `/accuracy/by-route`, `/accuracy/predicted-vs-actual`; alerts; reports (create, list, download); admin (users, audit log, jobs, system).

## 13. Pages
Landing; Login/Register/Forgot; **Dashboard** (KPIs: on-time %, avg delay, active model MAE, % within ±2 min, open alerts; trend chart, delay heatmap, route accuracy, recent alerts); **ETA Predictor** (route, stop, time → `EtaCard` + `RouteLineDiagram`); **Trend Explorer**; **Data Entry** (tabs: routes, stops, route-stops, trips, observations, delay events, import wizard); **Features** (preview and importance); **Models** (train wizard, compare table, activate/rollback); **Accuracy** (predicted vs actual, error histogram, per-route bars, leave-route-out results); Alerts; Reports; Admin; Profile; About/Methodology (formulas, limitations, disclaimer).

## 14. Phases and Claude Code Prompts (use in order)

**Phase 1 (Week 1): Setup and design.** Repo, requirements, `.gitignore` (with `.env`, `frontend/.env`), both `.env.example`, `src/config.py` fail-fast, design tokens, wireframes.
> `Read PROJECT_SPEC_BUSARRIVAL.md. Do Phase 1 only: create the repo structure (backend/, src/, frontend/, scripts/, tests/, docs/), requirements.txt, .gitignore including .env and frontend/.env, both .env.example files from Section 10 with placeholders only, src/config.py using pydantic-settings that fails fast on missing or placeholder MONGODB_URI and JWT_SECRET, a README, and docs/ wireframes (text/ASCII) for Login, Dashboard, ETA Predictor, Data Entry, Models, Accuracy. No Streamlit. Never write a real credential anywhere. Acceptance: app refuses to start with a clear message when env is missing.`

**Phase 2 (Week 2): MongoDB and auth.**
> `Implement Phase 2: src/db/mongo.py (MongoClient from env, ping, ensure_indexes, jsonSchema validators), repositories with owner and role filtering, users collection, JWT register/login/refresh/logout with bcrypt, rate limiting and lockout, audit log, /api/health, scripts/create_admin.py. Tests use MONGODB_TEST_DB_NAME and clean up. Acceptance: connects to Atlas using only .env; lockout works.`

**Phase 3 (Week 3): Seed data and data-entry APIs.**
> `Implement Phase 3: synthetic generator (routes, stops, route-stops, trips, observations with rush-hour, day-type, congestion, rain and delay carry-over effects, plus deliberately messy rows), scripts/seed.py (idempotent, labelled illustrative), and CRUD APIs with Pydantic validation per Section 5, audit logging, and CSV import with a row-level error report. Acceptance: seed fills all collections; messy rows are detected; field-level error messages returned.`

**Phase 4 (Week 4): Analytics and trends.**
> `Implement Phase 4: src/analytics/trends.py (delay by hour, day type, route, stop; on-time % definitions; heatmap data; route summary) and the /analytics endpoints, with hand-calculated pytest tests.`

**Phase 5 (Week 5): Feature engineering.**
> `Implement Phase 5: src/ml/features.py per Section 7.2, including history features computed strictly from past data. Add a leakage test that proves no feature uses data at or after the prediction time. Cache features by data_version in features_cache and expose POST /features/build.`

**Phase 6 (Weeks 6-7): Models and validation.**
> `Implement Phase 6: src/ml/models.py and validate.py per 7.1, 7.3, 7.4: baselines, Ridge, RandomForest, GradientBoosting and quantile GB; chronological split, TimeSeriesSplit tuning, leave-one-route-out validation; metrics MAE, RMSE, MAPE, within-2-min, bias, P90 coverage; error distributions by route/hour/day type. Save artifacts with joblib and metadata. Run training as a background task with status polling and store results in the models collection. Acceptance: trained model beats the baseline on held-out data on the seeded dataset, or the result honestly says it does not.`

**Phase 7 (Week 8): Model registry and ETA service.**
> `Implement Phase 7: model management (list, compare, activate, rollback, archive) and the ETA predictor per 7.5: POST /predict/eta returns ETA P50, P90, expected delay and reliability label; log predictions in predictions_log; later match against actuals for accuracy tracking. Add drift checks and alerts per 7.6. Role guards: only admin can activate or rollback.`

**Phase 8 (Week 9): Accuracy, alerts, reports, API completion.**
> `Implement Phase 8: accuracy endpoints (overview, errors, by-route, predicted-vs-actual), alerts, PDF/Excel/CSV reports (Jinja2, weasyprint, openpyxl), admin endpoints, and API tests for every router including owner/role scoping and field-level error format.`

**Phase 9 (Week 10): Frontend foundation.**
> `Implement Phase 9 in frontend/: React 18, TypeScript, Vite, Tailwind, shadcn/ui, lucide-react, TanStack Query/Table, React Hook Form + Zod, framer-motion, sonner, cmdk. Apply the light tokens from Section 9 exactly. Build the app shell (sidebar, top bar with route/stop selectors, command palette, notifications, user menu), Login/Register/Forgot screens with the split layout, route guards, and a typed API client reading VITE_API_BASE_URL. Acceptance: login works against the real API; keyboard navigable; no TypeScript errors.`

**Phase 10 (Week 11): Dashboard, ETA Predictor, Trends.**
> `Implement Phase 10: Dashboard, ETA Predictor (EtaCard, RouteLineDiagram, ReliabilityGauge), Trend Explorer (TrendChart, DelayHeatmap) with loading, empty and error states, using seeded data. Charts must use the semantic colours from Section 9.`

**Phase 11 (Week 11-12): Data Entry, Models, Accuracy.**
> `Implement Phase 11: Data Entry (inline-editable DataTable with quick-add rows for all datasets, import wizard with column mapping and validation table), Features page, Models page (train wizard, compare table, FeatureImportanceBars, activate/rollback), Accuracy page (PredVsActualScatter, ErrorHistogram, RouteAccuracyBars, leave-route-out results).`

**Phase 12 (Week 12): Alerts, Reports, Admin, Landing, polish.**
> `Implement Phase 12: Alerts, Reports, Admin (users, audit log, jobs), Profile, About/Methodology, Landing page. Then finish: backend coverage 70%+, Vitest component tests, optional Playwright journey (login -> add observation -> train model -> activate -> predict ETA -> download report), accessibility and responsive polish, README with Atlas + .env setup and troubleshooting, optional docker-compose, and a demo script.`

**Phase 13 (optional): Real data.**
> `Add GTFS static import support: document the column mapping for stops.txt, routes.txt, trips.txt and stop_times.txt, extend validation, and test with a small real-format sample through the import wizard.`

## 15. Testing Plan
Config fail-fast; URI never logged; test DB isolation; auth lockout and JWT expiry; role guards. One test per validation rule; seeded messy rows yield expected issues. Trend metrics vs hand calculations. **Feature leakage test.** Chronological split never trains on future rows; leave-route-out never includes the held-out route in training. Metric functions vs hand examples; model beats baseline or reports honestly; quantile P90 coverage within tolerance. ETA API schema and edge cases (unknown stop, no active model). Frontend: component tests for `EtaCard`, `DataTable` inline edit, import wizard, model compare; build with zero TS errors.

## 16. Risks
| Risk | Mitigation |
|---|---|
| No real GPS data | Seed data labelled illustrative; CSV/GTFS import; honest wording |
| Data leakage inflates accuracy | Past-only features, leakage test, chronological + route-level validation |
| Model overfits seeded patterns | Report baseline comparison and leave-route-out results |
| Overconfident ETAs | Always show P50–P90 range and reliability |
| Secrets exposed | `.env` git-ignored, placeholders only, least-privilege Atlas user, rotate any credential ever shared |
| Slow training | Background tasks, status polling, cached features |
| Inconsistent UI | Tokens and shared components only |

## 17. Deliverables Checklist
- [ ] Website: landing, login/register/forgot, role-based dashboard
- [ ] Data entry and CSV import with validation and audit trail
- [ ] Trend explorer, feature pipeline, model training/registry, ETA predictor, accuracy dashboard
- [ ] Reports (PDF/Excel/CSV)
- [ ] FastAPI with Swagger docs, MongoDB via `.env` only
- [ ] README, demo script, tests, final report and slides
- [ ] Future work: live GTFS-realtime/GPS feeds, weather and traffic APIs, passenger-load prediction, mobile app, SMS/push alerts

## 18. Structure
```
busarrival-ai/
|-- PROJECT_SPEC_BUSARRIVAL.md  README.md  requirements.txt  .env.example  .gitignore  docker-compose.yml
|-- scripts/ (seed.py, create_admin.py)
|-- src/ (config.py, db/{mongo.py,repositories/}, data/{synthetic.py,validate.py,ingest.py}, analytics/trends.py,
|        ml/{features.py,models.py,validate.py,registry.py,predict.py,drift.py}, report/)
|-- backend/ (main.py, deps.py, schemas.py, security.py, routers/)
|-- frontend/ (.env.example, src/{api,components,pages,context,styles})
|-- tests/  docs/  outputs/{models,reports}
```

## 19. References
Hastie, Tibshirani, Friedman: The Elements of Statistical Learning; scikit-learn docs (regression, ensembles, quantile loss, TimeSeriesSplit, GroupKFold); GTFS specification; MongoDB Atlas/PyMongo, FastAPI, React, Vite, Tailwind, shadcn/ui, Recharts, TanStack docs; papers on bus arrival time prediction using historical data and regression.