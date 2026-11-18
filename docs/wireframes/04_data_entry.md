# Wireframe 04: Data Entry & CSV Import Wizard

**Role Access:** Analyst, Admin  
**Tabs:** Routes | Stops | Route-Stops | Trips | Observations | Delay Events | CSV Import

```
+----+--------------------------------------------------------------------------------------------------+
|[==]| DATA MANAGEMENT & OBSERVATIONS                                            [!] [Profile v]       |
+----+--------------------------------------------------------------------------------------------------+
|    |  [ Routes ] [ Stops ] [ Route-Stops ] [ Trips ] [* Observations *] [ Delay Events ] [ CSV Import ]
|NAV |                                                                                                  |
|    |  +---------------------------------------------------------------------------------------------+ |
|    |  | [Search observations...]  [Filter Route: All v]  [Date: 2026-11-18]  [+ Quick Add Row] [CSV] | |
|    |  +---------------------------------------------------------------------------------------------+ |
|    |  | TRIP ID   | STOP CODE | SCHEDULED | ACTUAL    | DELAY    | PASSENGERS | WEATHER | ACTIONS       | |
|    |  |-----------+-----------+-----------+-----------+----------+------------+---------+---------------| |
|    |  | TR-101-08 | ST-014    | 08:30:00  | 08:34:15  | +4.2m    | 42         | Clear   | [Edit] [Del]  | |
|    |  | TR-101-08 | ST-015    | 08:45:00  | 08:52:10  | +7.1m    | 38         | Clear   | [Edit] [Del]  | |
|    |  | TR-204-12 | ST-088    | 09:00:00  | 08:59:30  | -0.5m    | 19         | Rain    | [Edit] [Del]  | |
|    |  | TR-305-02 | ST-102    | 09:15:00  | [Inline]  | ...      | ...        | ...     | [Save] [Cancel| |
|    |  +---------------------------------------------------------------------------------------------+ |
|    |  Showing 1 - 25 of 1,420 observations                             [< Prev] [1] 2 3 4 ... [Next >] |
|    |                                                                                                  |
|    |  ==============================================================================================  |
|    |  CSV IMPORT WIZARD MODAL (Step 3: Validation & Issue Detection)                                 |
|    |  ----------------------------------------------------------------------------------------------  |
|    |  File: observed_delays_nov.csv (1,250 rows detected)                                             |
|    |  [v] 1,218 Valid Rows   [!] 32 Invalid/Outlier Rows Flagged                                      |
|    |                                                                                                  |
|    |  +-----+-----------+-----------+--------------------+------------------------------------------+ |
|    |  | Row | Trip ID   | Stop Code | Scheduled / Actual | Detected Issue                           | |
|    |  |-----+-----------+-----------+--------------------+------------------------------------------| |
|    |  | 48  | TR-999-01 | ST-002    | 14:00 -> 18:30     | [!] Outlier: Delay +270m exceeds +120m   | |
|    |  | 112 | TR-101-04 | UNKNOWN   | 15:10 -> 15:14     | [X] Foreign Key: Stop code not found     | |
|    |  | 205 | TR-101-08 | ST-014    | 08:30 -> 08:34     | [!] Duplicate: (trip_id, stop_id) exists | |
|    |  +-----+-----------+-----------+--------------------+------------------------------------------+ |
|    |                                                                                                  |
|    |  Resolution Choice:                                                                              |
|    |  (o) Import valid rows only (1,218 rows) and download error report                              |
|    |  ( ) Overwrite duplicate records with incoming rows                                              |
|    |  ( ) Cancel import                                                                               |
|    |                                                                                                  |
|    |  [ Cancel ]                                          [ Commit Valid Rows to MongoDB (1,218) > ]  |
+----+--------------------------------------------------------------------------------------------------+
```

### Component Details
- **Editable DataTable:** Inline row editing, quick-add at top, multi-column sorting, and server-side pagination.
- **CSV Validation Pipeline:** Inspects incoming files before commit, flags duplicate keys, unknown routes/stops, and timing outliers.
- **Audit Logging:** Every insert, update, delete, or bulk import triggers a structured record in `audit_log`.
