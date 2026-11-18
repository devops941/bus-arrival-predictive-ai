# Wireframe 05: Models & Training Management

**Role Access:** Analyst (Train, Compare), Admin (Activate, Rollback)  
**Purpose:** Train classic ML models, evaluate time-aware and leave-route-out performance, and manage model lifecycle.

```
+----+--------------------------------------------------------------------------------------------------+
|[==]| MODEL REGISTRY & TRAINING ENGINE                                          [!] [Profile v]       |
+----+--------------------------------------------------------------------------------------------------+
|    |  +-------------------------------------------------------------+-------------------------------+ |
|NAV |  | ACTIVE PRODUCTION MODEL                                     | TRAIN NEW CANDIDATE MODEL     | |
|    |  | Name: Quantile Gradient Boosting (v3.1)                     | [ Algorithm: Quantile GB   v] | |
|    |  | Status: [ ACTIVE (PROD) ]      Artifact: outputs/models/qgb3| [ Features: All (12 selected)v] | |
|    |  | Validation MAE: 1.38 min       P90 Interval Coverage: 91.2% | [ Chronological Split: 80/20 v] | |
|    |  | Deployed by: admin@busarrival.local on 2026-11-15 09:30 UTC | [ Random Seed: 42           ] | |
|    |  | [ Rollback to v3.0 ]                  [ Run Diagnostic Eval]| [ > Start Training Job (Async)] |
|    |  +-------------------------------------------------------------+-------------------------------+ |
|    |                                                                                                  |
|    |  MODEL COMPARISON & BENCHMARK LEADERBOARD                                                        |
|    |  +---------------+-------------+----------+----------+----------+-----------+---------+--------+ |
|    |  | Model Name    | Algorithm   | Val MAE  | RMSE     | % <= 2m  | Bias      | Status  | Actions| |
|    |  |---------------+-------------+----------+----------+----------+-----------+---------+--------| |
|    |  | Baseline      | Mean Delay  | 3.42 min | 4.81 min | 42.1%    | +0.12 min | Stored  | [View] | |
|    |  | Ridge-Reg-01  | Ridge Regr  | 2.15 min | 3.10 min | 64.8%    | -0.05 min | Stored  | [View] | |
|    |  | RF-Ensemble-2 | Random Frst | 1.62 min | 2.45 min | 78.4%    | +0.02 min | Stored  | [View] | |
|    |  | GB-Boost-03   | Grad Boost  | 1.45 min | 2.18 min | 80.2%    | +0.01 min | Stored  | [View] | |
|    |  | * QGB-v3.1 *  | Quantile GB | 1.38 min | 2.05 min | 81.6%    | +0.00 min | ACTIVE  | [Active|
|    |  +---------------+-------------+----------+----------+----------+-----------+---------+--------+ |
|    |                                                                                                  |
|    |  +----------------------------------------------------+  +-------------------------------------+ |
|    |  | FEATURE IMPORTANCE (Gini / Permutation)            |  | TRAINING JOB STATUS & PROGRESS      | |
|    |  |                                                    |  |                                     | |
|    |  | distance_to_stop_km  [=====================] 0.28  |  | Job ID: job_tr_20261118_04          | |
|    |  | prev_stop_delay      [==================   ] 0.23  |  | Model: Quantile Gradient Boosting   | |
|    |  | recent_route_delay   [===============      ] 0.19  |  | Status: Training (Step 3 of 4)      | |
|    |  | hour_sin_cos         [===========          ] 0.14  |  | Progress: [===============>   ] 75% | |
|    |  | day_type             [======               ] 0.08  |  | - Features built: 14,200 rows       | |
|    |  | rain_flag            [====                 ] 0.05  |  | - TimeSeriesSplit CV: 5 folds done  | |
|    |  | headway_scheduled    [===                  ] 0.03  |  | - Computing Leave-Route-Out group...| |
|    |  +----------------------------------------------------+  +-------------------------------------+ |
+----+--------------------------------------------------------------------------------------------------+
```

### Component Details
- **Active Model Banner:** Immediate visibility of production model performance, artifact path, and rollback controls.
- **Model Leaderboard:** Compare candidate algorithms against the naive baseline; enforces rule: "Model beats baseline only if improvement is shown on held-out data".
- **Feature Importance Chart:** Bar ranking of feature contributions; all history features unit-tested against leakage.
- **Async Job Poller:** Live progress updates while training runs in FastAPI background workers.
