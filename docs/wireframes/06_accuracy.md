# Wireframe 06: Accuracy & Performance Analytics

**Role Access:** Viewer, Analyst, Admin  
**Purpose:** Honest evaluation of model accuracy, error distributions, per-route performance, and leave-route-out generalization.

```
+----+--------------------------------------------------------------------------------------------------+
|[==]| FORECAST ACCURACY & ERROR DISTRIBUTION                                    [!] [Profile v]       |
+----+--------------------------------------------------------------------------------------------------+
|    |  [ Route: All Routes v ]  [ Evaluation Window: Last 14 Days v ]  [ Export Accuracy Report (PDF) ]|
|NAV |                                                                                                  |
|    |  +--------------------+  +--------------------+  +--------------------+  +--------------------+  |
|    |  | OVERALL MAE        |  | WITHIN +/- 2 MIN   |  | P90 COVERAGE RATE  |  | PREDICTION BIAS    |  |
|    |  | 1.38 min           |  | 81.6% of trips     |  | 91.2% (Target 90%) |  | +0.03 min (Neutral)|  |
|    |  | [-59% vs baseline] |  | [+39% vs baseline] |  | [ Well calibrated ]|  | [ No systemic drag]|  |
|    |  +--------------------+  +--------------------+  +--------------------+  +--------------------+  |
|    |                                                                                                  |
|    |  +----------------------------------------------------+  +-------------------------------------+ |
|    |  | PREDICTED VS ACTUAL DELAYS (Scatter Plot)          |  | RESIDUAL ERROR HISTOGRAM            | |
|    |  | Actual                                             |  | Count                               | |
|    |  | 20m|          .  .   / (Ideal 1:1 Line)            |  |  800|               _||_            | |
|    |  | 15m|        .  .:' /                               |  |  600|              |    |           | |
|    |  | 10m|      .  .':' /                                |  |  400|            __|    |__         | |
|    |  |  5m|    . .':'   /                                 |  |  200|          _|          |_       | |
|    |  |  0m|--:-------/--------------------- Predicted     |  |    0|--___-'-'--------------'-___-  | |
|    |  |   0m   5m   10m   15m   20m                        |  |       -6m  -4m  -2m  0m  +2m  +4m   | |
|    |  +----------------------------------------------------+  +-------------------------------------+ |
|    |                                                                                                  |
|    |  +----------------------------------------------------+  +-------------------------------------+ |
|    |  | ACCURACY BY ROUTE (% Within +/- 2 Min)             |  | LEAVE-ROUTE-OUT CROSS-VALIDATION    | |
|    |  |                                                    |  | Testing model on unseen bus routes: | |
|    |  | Route 101 [==========================] 89.4% (Best)|  |                                     | |
|    |  | Route 204 [=======================   ] 83.1%       |  | Held-out Route | Route MAE | Status | |
|    |  | Route 108 [=====================     ] 79.2%       |  |----------------+-----------+--------| |
|    |  | Route 305 [==================        ] 74.5%       |  | Route 101      | 1.48 min  | Robust | |
|    |  | Route 404 [==============            ] 61.2% (Alert|  | Route 204      | 1.55 min  | Robust | |
|    |  |                                                    |  | Route 305      | 1.82 min  | Moderate|
|    |  | [!] Route 404 has high traffic shock variance      |  | Route 404      | 2.10 min  | Warning| |
|    |  +----------------------------------------------------+  +-------------------------------------+ |
+----+--------------------------------------------------------------------------------------------------+
```

### Component Details
- **Scatter Plot (Predicted vs Actual):** Visualizes alignment with the ideal diagonal reference line; points color-coded by route.
- **Residual Error Histogram:** Displays bell-curve distribution centered around zero bias to prove the absence of systemic under- or over-estimation.
- **Route Accuracy Bars:** Granular breakdown identifying which routes benefit most from ML predictions and which suffer high random shock.
- **Leave-Route-Out Table:** Evaluates model generalizability on routes never seen in the training set (GroupKFold by route).
