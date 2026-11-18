# Wireframe 02: Main Operations Dashboard

**Role Access:** All roles (content scoped to role permissions)  
**Layout:** Collapsible Sidebar + Global Top Bar + 12-Column Responsive Grid

```
+----+--------------------------------------------------------------------------------------------------+
|[==]| [Search routes, stops (Ctrl+K)]             [Route: All v] [Range: Last 30D v] [!] [Profile v]   |
+----+--------------------------------------------------------------------------------------------------+
|    |  DASHBOARD OVERVIEW                                                   [Download Summary Report v]|
|NAV |                                                                                                  |
|[x] |  +--------------------+  +--------------------+  +--------------------+  +--------------------+  |
|Dash|  | ON-TIME RATE       |  | AVG STOP DELAY     |  | ACTIVE MODEL MAE   |  | WITHIN +/- 2 MIN   |  |
|    |  |  84.2%             |  |  +2.4 min          |  |  1.38 min          |  |  81.6%             |  |
|[ ] |  |  [^ +2.1% vs lw]   |  |  [v -0.4m vs lw]   |  |  (Quantile GB v3)  |  |  [^ +3.4% vs lw]   |  |
|ETA |  |  [====Sparkline===]|  |  [====Sparkline===]|  |  [====Sparkline===]|  |  [====Sparkline===]|  |
|    |  +--------------------+  +--------------------+  +--------------------+  +--------------------+  |
|[ ] |                                                                                                  |
|Data|  +----------------------------------------------------+  +-------------------------------------+  |
|    |  | DELAY TRENDS OVER TIME (Minutes)                   |  | DELAY HEATMAP (Hour of Day x Day)   |  |
|[ ] |  | [ Route 101 v ] [ Hourly / Daily / Weekly ]        |  |        M   T   W   T   F   S   S    |  |
|Modl|  | 12m|              .-.                              |  | 07:00 [ ][ ][*][*][*][ ][ ]    |  |
|    |  |  8m|    .-.      /   \        .-.                  |  | 08:00 [*][*][#][#][#][ ][ ]    |  |
|[ ] |  |  4m|   /   \    /     \      /   \                 |  | 12:00 [ ][ ][*][*][*][*][*]    |  |
|Acc |  |  0m|--'-----'--'-------'----'-----'--- (Schedule)  |  | 17:00 [*][#][#][#][#][*][ ]    |  |
|    |  |    06:00   10:00   14:00   18:00   22:00           |  | 18:00 [#][#][#][#][#][*][ ]    |  |
|[ ] |  +----------------------------------------------------+  +-------------------------------------+  |
|Rpts|                                                                                                  |
|    |  +----------------------------------------------------+  +-------------------------------------+  |
|[ ] |  | PER-ROUTE ACCURACY & PUNCTUALITY                   |  | RECENT SYSTEM ALERTS & DRIFT        |  |
|Logs|  | Route 101 [========================] 89.1% On-Time |  | [!] Route 404 Model Drift Warning   |  |
|    |  | Route 204 [======================  ] 81.3% On-Time |  |     MAE exceeded 1.3x baseline      |  |
|[ ] |  | Route 305 [====================    ] 74.0% Minor   |  |     [ Retrain Model ]  [ Dismiss ]  |  |
|Admn|  | Route 404 [==============          ] 58.4% Late    |  | [i] Seed data loaded: 8 routes      |  |
+----+--+----------------------------------------------------+--+-------------------------------------+--+
```

### Key Elements
- **KPI Cards:** Display key operational metrics with direction indicator (`^` up / `v` down) and inline SVG sparkline.
- **Delay Trends Chart:** Interactive chart with dual traces (Scheduled Baseline `#0D9488` vs Observed Arrival `#1D4ED8`).
- **Delay Heatmap:** Hour × Day of week matrix highlighting traffic congestion hotspots.
- **Alerts Panel:** Real-time drift warnings triggering model evaluation or retraining workflows.
