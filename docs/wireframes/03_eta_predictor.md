# Wireframe 03: ETA Predictor Screen

**Role Access:** Passenger / Viewer, Analyst, Admin  
**Purpose:** Provide passengers and dispatchers with accurate arrival time predictions and confidence ranges.

```
+----+--------------------------------------------------------------------------------------------------+
|[==]| ETA PREDICTOR & PASSENGER FORECAST                                         [!] [Profile v]       |
+----+--------------------------------------------------------------------------------------------------+
|    |                                                                                                  |
|NAV |  PREDICTION QUERY CONTROLS                                                                       |
|    |  +---------------------------+---------------------------+---------------------------+---------+ |
|    |  | Select Route              | Target Stop               | Scheduled Time / Departure| [Action]| |
|    |  | [ Route 101 - Metro Express] [ Stop #14 - Central Stn  ] [ Today, 17:35           ] | [PREDICT]|
|    |  +---------------------------+---------------------------+---------------------------+---------+ |
|    |                                                                                                  |
|    |  +---------------------------------------------------------------------------------------------+ |
|    |  | ETA PREDICTION RESULT CARD (Active Model: Quantile GB v3.1)                                 | |
|    |  |                                                                                             | |
|    |  |   EXPECTED ARRIVAL (P50)             ARRIVAL RANGE (P90)            RELIABILITY STATUS      | |
|    |  |   ======================             ===================            ==================      | |
|    |  |   17:42                              17:40 - 17:46                  [ HIGH CONFIDENCE ]     | |
|    |  |   (+7 min delay from 17:35 schedule) 90% Probability Interval       Interval width: 6 min   | |
|    |  |                                                                                             | |
|    |  |   [=========================|P50==============|P90==============]                             | |
|    |  |   17:35 (Sched)            17:42             17:46                                          | |
|    |  |                                                                                             | |
|    |  |   * Disclaimer: Machine learning estimate based on recent traffic & route historical delays | |
|    |  +---------------------------------------------------------------------------------------------+ |
|    |                                                                                                  |
|    |  ROUTE LINE DIAGRAM & LIVE DELAYS ALONG CORRIDOR                                                 |
|    |  +---------------------------------------------------------------------------------------------+ |
|    |  |                                                                                             | |
|    |  |   Stop 1          Stop 2          Stop 3 (Bus Here) Stop 4          Stop 5 (Destination)    | |
|    |  |   [Origin]        [Main Ave]      [Market Pl]       [Univ Blvd]     [Central Stn]           | |
|    |  |      O===============O===============@(Bus 42)===========O===============O                  | |
|    |  |    0.0km           2.4km           4.8km             7.1km           9.5km                  | |
|    |  |    Departed        Departed        Departing Now     ETA 17:38       ETA 17:42              | |
|    |  |    +0m on-time     +2m minor       +5m traffic       +6m forecast    +7m predicted          | |
|    |  |    [Green]         [Amber]         [Amber]           [Violet]        [Violet]               | |
|    |  +---------------------------------------------------------------------------------------------+ |
+----+--------------------------------------------------------------------------------------------------+
```

### Component Details
- **EtaCard:** Displays prominent P50 arrival time, upper P90 arrival boundary, and a reliability status badge (`HIGH`, `MEDIUM`, `LOW`).
- **Interval Bar:** Visual range bar comparing scheduled baseline against P50 and P90 confidence intervals.
- **RouteLineDiagram:** Linear diagram representing bus stops along the corridor, marking the vehicle position, completed stops, and downstream ETA predictions with semantic color coding.
