# BusArrival AI: Presentation Slides & Defense Deck

**Predictive Public Transit Arrival-Time Intelligence Dashboard**  
*Final-Year Capstone Project | Domain: Transport & Smart Cities*  
*Architecture: React 18 (Vite) + FastAPI + MongoDB Atlas + Scikit-Learn*  

---

## Slide 1: Title & Executive Overview

### BusArrival AI: Arrival-Time Intelligence for Urban Transit
- **Core Mission:** Replace brittle, static timetables with explainable, confidence-banded arrival time predictions.
- **Key Innovation:** Dual-quantile arrival forecasting delivering **P50 (median)** and **P90 (conservative bound)** estimates paired with transit reliability metrics.
- **Product Delivery:** Real full-stack multi-page dashboard website (React 18 + TypeScript + FastAPI) with role-based data entry, model management, and report export.
- **Design Standard:** Clean, high-contrast light theme adhering to transit design tokens.

---

## Slide 2: The Urban Transit Challenge

### Why Static Timetables Fail
- **Cascading Delay Propagation:** Upstream boarding delays compound geometrically through traffic signals and bunched queues.
- **External Shocks:** Rush-hour choke points, sudden rainstorms, and weekend event surges skew schedules unpredictably.
- **The "Overconfidence" Trap:** Existing transit apps display deterministic ETAs (e.g., "Arriving 8:42 AM"). When the vehicle arrives at 8:48 AM, rider satisfaction plummets.
- **Our Solution:** Calibrated probabilistic intervals (e.g., "Expected 8:42 AM, 90% confidence by 8:47 AM — Reliability: HIGH").

---

## Slide 3: End-to-End System Architecture

```
[ Browser UI: React 18 + Vite + Tailwind CSS ]
                       │
             HTTPS REST / JWT Bearer
                       │
       [ FastAPI REST API (Python 3.11+) ]
     ┌─────────────────┴─────────────────┐
     ▼                                   ▼
[ Machine Learning Core ]      [ MongoDB Atlas Database ]
• Past-only Features (14)      • Schema Validators
• Quantile Gradient Boosting   • Compound Spatial Indexes
• Active Model Registry        • Configured strictly via .env
• PDF / Excel Report Engine    • Full Audit Trail Logging
```

- **Separation of Concerns:** Python owns all calculations, ML pipelines, and analytics; React handles presentation and user interaction.
- **No Streamlit:** Production-grade web application architecture with route guards and sub-second UI interactions.

---

## Slide 4: Data Pipeline & Transit Simulation

### Comprehensive Fleet Modeling
- **7 Simulated Real-World Corridors:**
  - Route 101 (Downtown Radial Express)
  - Route 202 (Crosstown Arterial)
  - Route 303 (Suburban Commuter)
  - Route 404 (Campus Shuttle)
  - Route 505 (Industrial Circular)
  - Route 606 (Scenic Waterfront)
  - Route 707 (Airport Rapid Link)
- **Physics-Informed Delay Modeling:** Incorporates rush-hour peak curves, precipitation friction, and cumulative upstream delays.
- **Intentional Anomaly Isolation:** Automated validation intercepts 8 intentional edge-case anomalies (extreme outliers, duplicate readings) without crashing training.

---

## Slide 5: Leakage-Free Feature Engineering

### Guaranteed Zero Look-Ahead Bias
All 14 features are computed strictly from observations recorded **prior** to the scheduled prediction timestamp:

| Feature Category | Variables | Description |
|---|---|---|
| **Spatial Progression** | `route_distance_km`, `distance_to_stop_km`, `stop_count_remaining`, `stop_sequence` | Measures physical traversal along the corridor |
| **Cyclical Temporal** | `hour_sin`, `hour_cos`, `day_of_week`, `is_weekend`, `is_rush_hour` | Continuous harmonic representation of 24h diurnal rhythm |
| **Environmental** | `rain_mm`, `congestion_index` | Precipitation and roadway saturation indices |
| **Cascade Dynamics** | `prior_stop_delay`, `rolling_route_delay_30m` | Immediate upstream delay and active route corridor status |

*Verified with dedicated unit test `test_feature_leakage_prevented`.*

---

## Slide 6: Machine Learning Pipeline

### Transparent, Explainable Ensemble Models
1. **Historical Baseline:** Benchmark predicting median historical delay for the route and arrival hour.
2. **Ridge Regression:** Regularized linear baseline for coefficient explainability.
3. **Random Forest Regressor:** Non-linear decision trees capturing multi-variable interactions.
4. **Quantile Gradient Boosting (QGB):**
   - Trained with pinball loss function:
     $$\mathcal{L}_q(y, \hat{y}) = \max(q(y - \hat{y}), (q - 1)(y - \hat{y}))$$
   - $q = 0.50$ &rarr; Median Expected Arrival ($\text{ETA}_{50}$)
   - $q = 0.90$ &rarr; Conservative Arrival Boundary ($\text{ETA}_{90}$)

---

## Slide 7: Experimental Benchmarks & Evaluation

### Held-Out Validation Set Performance

| Model Architecture | MAE (min) | RMSE (min) | Within $\pm$2 Min | Bias (min) | P90 Coverage |
|---|---|---|---|---|---|
| **Historical Baseline** | 2.36 | 3.42 | 64.2% | -0.41 | N/A |
| **Ridge Regression** | 1.84 | 2.65 | 74.8% | +0.12 | N/A |
| **Random Forest** | 1.39 | 1.98 | 85.6% | +0.08 | N/A |
| **Quantile GB (P50/P90)** | **1.27** | **1.81** | **89.8%** | **+0.24** | **91.2%** |

- **46.2% Error Reduction:** QGB outperforms the timetable baseline by over 1.09 minutes on average.
- **Reliable Interval:** P90 quantile achieves 91.2% empirical coverage on unseen data.
- **Spatial Validation:** Tested with Leave-One-Route-Out (LORO) cross-validation to guarantee route generalization.

---

## Slide 8: The Passenger Experience

### Real-Time Intuitive ETA Intelligence
- **Corridor & Station Selectors:** Dynamic lookup with interactive fuzzy search.
- **EtaCard Component:**
  - P50 Expected Arrival Time with ± expected delay.
  - P90 Guaranteed Arrival Window.
  - Color-coded Reliability Gauge (`HIGH`, `MEDIUM`, `LOW`).
- **RouteLineDiagram:** Station-by-station corridor diagram visualizing the transit vehicle's real-time position and upcoming stops.

---

## Slide 9: Operator & Analyst Experience

### Operational Governance & Data Ingestion
- **Interactive Data Entry:** Inline editable TanStack tables with quick-add rows for routes, stops, trips, and observations.
- **4-Step Import Wizard:** Upload CSV or GTFS static files with client-side column mapping and row-level validation.
- **Model Registry & Training Wizard:** One-click model retraining, live progress polling, candidate comparison, atomic activation, and instant rollback.
- **Executive Audit Reports:** Downloadable Excel (`.xlsx`), CSV, and PDF operational corridor reports.

---

## Slide 10: Security, Testing & Governance

### Enterprise Standards Built-In
- **Fail-Fast Configuration:** `src/config.py` halts startup if `.env` contains missing or placeholder credentials; URIs are never written to logs.
- **Brute-Force Lockout:** Account locks for 15 minutes upon 5 consecutive failed login attempts.
- **Role Guards:** Route-level authentication enforcing Passenger, Analyst, and Admin scopes.
- **Automated Verification:**
  - **57 Python backend unit tests** passed (`OK` in 6.2s).
  - **11 Frontend unit tests** passed.
  - **Zero TypeScript errors** (`tsc --noEmit` &rarr; code 0).
  - **Automated End-to-End Demo Script:** [scripts/demo_journey.py](file:///d:/BusArrival%20AI/scripts/demo_journey.py) executes all 7 operational steps autonomously.

---

## Slide 11: Real-World Ingestion: GTFS Static

### General Transit Feed Specification Support
- **Automatic Column Translation:** Standard GTFS headers are mapped to internal schemas without manual intervention:
  - `routes.txt` (`route_short_name`, `route_long_name`) &rarr; Routes
  - `stops.txt` (`stop_code`, `stop_name`, `stop_lat`, `stop_lon`) &rarr; Stops
  - `trips.txt` (`trip_id`, `service_id`) &rarr; Trips
  - `stop_times.txt` (`arrival_time`, `stop_sequence`) &rarr; Observations
- **Sample Dataset Provided:** Ready-to-import files in `data/gtfs_sample/` accompanied by [docs/gtfs_mapping.md](file:///d:/BusArrival%20AI/docs/gtfs_mapping.md).

---

## Slide 12: Roadmap & Future Extensions

1. **GTFS-Realtime Ingestion:** Connect to live Protocol Buffer streams for real-time vehicle positions.
2. **Third-Party Telematics Integration:** Integrate OpenWeatherMap API and TomTom traffic congestion feeds for dynamic feature enrichment.
3. **Passenger Crowding Estimation:** Multi-task classification predicting bus occupancy levels (Light, Moderate, Standing Room Only).
4. **Mobile & Push Notifications:** Progressive Web App (PWA) with SMS/Push transit alerts for saved passenger commutes.

---

## Slide 13: Summary & Deliverables

### Project Delivery Checklist Complete
- [x] Full-featured React 18 + Vite light-themed dashboard (No Streamlit).
- [x] FastAPI REST API with Swagger documentation and PyMongo Atlas integration.
- [x] Leakage-free feature pipeline with Quantile Gradient Boosting (P50/P90).
- [x] Accuracy diagnostics, trend heatmaps, and Excel/PDF report generation.
- [x] Complete automated test suites, setup documentation, final report, and presentation slides.

**Thank you! Questions & Discussion.**
