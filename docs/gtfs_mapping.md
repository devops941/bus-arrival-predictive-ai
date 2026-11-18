# GTFS Static Import Specification & Mapping

BusArrival AI provides automatic ingestion for standard General Transit Feed Specification (GTFS) static files via the Data Entry Import Wizard.

---

## 1. File & Column Mapping

### `routes.txt` &rarr; `routes` Collection
| GTFS Column | BusArrival AI Field | Type | Transformation / Default |
|---|---|---|---|
| `route_short_name` / `route_id` | `route_no` | string | Normalized alphanumeric route code (e.g. `201`) |
| `route_long_name` | `name` | string | Corridor descriptor (e.g. `North Station - Tech Park Express`) |
| *Derived from name* | `origin` | string | Left side of `-` delimiter, or default `Origin Terminal` |
| *Derived from name* | `destination` | string | Right side of `-` delimiter, or default `Destination Plaza` |
| `route_color` | `color_hex` | string | Hex color code without leading `#` (e.g. `1D4ED8`) |
| *Calculated* | `total_distance_km` | float | Defaulted to 12.5 km or accumulated from shape points |
| *System* | `status` | string | `active` |

### `stops.txt` &rarr; `stops` Collection
| GTFS Column | BusArrival AI Field | Type | Transformation / Default |
|---|---|---|---|
| `stop_code` / `stop_id` | `stop_code` | string | Unique transit stop code (e.g. `ST-101`) |
| `stop_name` | `name` | string | Human-readable station or shelter name |
| `stop_lat` | `latitude` | float | WGS 84 latitude coordinate |
| `stop_lon` | `longitude` | float | WGS 84 longitude coordinate |
| *System* | `is_active` | boolean | `true` |

### `trips.txt` &rarr; `trips` Collection
| GTFS Column | BusArrival AI Field | Type | Transformation / Default |
|---|---|---|---|
| `trip_id` / `trip_short_name`| `trip_number` | string | Unique service run code (e.g. `TR-201-01`) |
| `route_id` | `route_id` | string | Foreign key referencing Route |
| `direction_id` | `direction` | string | `0` &rarr; `outbound`, `1` &rarr; `inbound` |
| `service_id` | `day_type` | string | Weekend services mapped to `weekend`, others `weekday` |

### `stop_times.txt` &rarr; `observations` Collection
| GTFS Column | BusArrival AI Field | Type | Transformation / Default |
|---|---|---|---|
| `trip_id` | `trip_id` | string | Run identifier |
| `stop_id` | `stop_code` | string | Station identifier |
| `arrival_time` | `scheduled_arrival`| string | ISO 8601 or HH:MM:SS arrival time |
| `departure_time` | `actual_arrival` | string | Realized arrival or scheduled baseline |
| *Calculated* | `delay_min` | float | Difference in minutes between actual and scheduled |

---

## 2. Ingestion Modes
1. **Dry-Run Validation (`commit=false`):**
   Parses all rows, verifies domain constraints (coordinates within range, plausible delays $[-10, +120]$ min, no duplicate stop sequences), and outputs an itemized row-by-row error report.
2. **Commit Valid Only (`import_valid_only=true`, `commit=true`):**
   Isolates messy rows (outliers or syntax errors) into the issue report while safely committing all clean records to MongoDB using idempotent `bulk_write` upserts.

---

## 3. Sample Dataset
Sample GTFS test files are provided in [`data/gtfs_sample/`](file:///d:/BusArrival%20AI/data/gtfs_sample/) for direct verification through the Import Wizard UI or API endpoint `POST /api/import/{kind}`.
