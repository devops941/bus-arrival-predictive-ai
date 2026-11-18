"""
Madurai City Transit Sample Data Generator for BusArrival AI.
Generates:
1. data/madurai/madurai_city_bus_data.xlsx (Multi-sheet styled Excel workbook)
2. data/madurai/routes.csv
3. data/madurai/stops.csv
4. data/madurai/route_stops.csv
5. data/madurai/observations.csv (Historical arrival telemetry with realistic traffic delays)
"""

import os
import csv
import random
from datetime import datetime, timedelta, timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Ensure directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "madurai")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Routes Data
ROUTES = [
    {
        "route_no": "77A",
        "name": "Periyar to Othakadai High Court",
        "origin": "Periyar Bus Stand",
        "destination": "Othakadai High Court Bench",
        "total_distance_km": 15.8,
        "scheduled_headway_min": 10,
        "active": True
    },
    {
        "route_no": "88",
        "name": "Periyar to Madurai Airport",
        "origin": "Periyar Bus Stand",
        "destination": "Madurai International Airport",
        "total_distance_km": 14.2,
        "scheduled_headway_min": 15,
        "active": True
    },
    {
        "route_no": "48P",
        "name": "Periyar to Samayanallur",
        "origin": "Periyar Bus Stand",
        "destination": "Samayanallur",
        "total_distance_km": 13.6,
        "scheduled_headway_min": 12,
        "active": True
    },
    {
        "route_no": "700",
        "name": "Mattuthavani to Thiruparankundram",
        "origin": "Mattuthavani MGR Bus Stand",
        "destination": "Thiruparankundram Temple",
        "total_distance_km": 15.5,
        "scheduled_headway_min": 15,
        "active": True
    }
]

# 2. Stops Data (Real GPS coordinates across Madurai)
STOPS = [
    {"stop_code": "MDU-001", "name": "Periyar Bus Stand", "lat": 9.9174, "lon": 78.1132},
    {"stop_code": "MDU-002", "name": "Simmakkal", "lat": 9.9255, "lon": 78.1210},
    {"stop_code": "MDU-003", "name": "Goripalayam Junction", "lat": 9.9328, "lon": 78.1315},
    {"stop_code": "MDU-004", "name": "Thallakulam", "lat": 9.9380, "lon": 78.1382},
    {"stop_code": "MDU-005", "name": "K.Pudur", "lat": 9.9452, "lon": 78.1470},
    {"stop_code": "MDU-006", "name": "Mattuthavani MGR Bus Stand", "lat": 9.9498, "lon": 78.1638},
    {"stop_code": "MDU-007", "name": "Agricultural College", "lat": 9.9575, "lon": 78.1820},
    {"stop_code": "MDU-008", "name": "Othakadai High Court Bench", "lat": 9.9650, "lon": 78.2045},
    {"stop_code": "MDU-009", "name": "Madurai Junction Railway Station", "lat": 9.9185, "lon": 78.1105},
    {"stop_code": "MDU-010", "name": "South Gate (Therku Vaasal)", "lat": 9.9125, "lon": 78.1180},
    {"stop_code": "MDU-011", "name": "Villapuram", "lat": 9.8970, "lon": 78.1250},
    {"stop_code": "MDU-012", "name": "Avaniyapuram Bus Stand", "lat": 9.8820, "lon": 78.1320},
    {"stop_code": "MDU-013", "name": "Ring Road Junction", "lat": 9.8650, "lon": 78.1265},
    {"stop_code": "MDU-014", "name": "Perungudi", "lat": 9.8480, "lon": 78.1120},
    {"stop_code": "MDU-015", "name": "Madurai International Airport", "lat": 9.8345, "lon": 78.0934},
    {"stop_code": "MDU-016", "name": "Arapalayam Bus Stand", "lat": 9.9310, "lon": 78.1060},
    {"stop_code": "MDU-017", "name": "Fathima College", "lat": 9.9450, "lon": 78.0980},
    {"stop_code": "MDU-018", "name": "Vilangudi", "lat": 9.9580, "lon": 78.0890},
    {"stop_code": "MDU-019", "name": "Paravai Market", "lat": 9.9750, "lon": 78.0760},
    {"stop_code": "MDU-020", "name": "Samayanallur", "lat": 9.9920, "lon": 78.0620},
    {"stop_code": "MDU-021", "name": "K.K. Nagar", "lat": 9.9385, "lon": 78.1510},
    {"stop_code": "MDU-022", "name": "Anna Nagar", "lat": 9.9280, "lon": 78.1525},
    {"stop_code": "MDU-023", "name": "Teppakulam", "lat": 9.9160, "lon": 78.1460},
    {"stop_code": "MDU-024", "name": "Pasumalai", "lat": 9.8920, "lon": 78.0780},
    {"stop_code": "MDU-025", "name": "Thiruparankundram Temple", "lat": 9.8780, "lon": 78.0710},
]

# 3. Route Stop Sequences
ROUTE_STOPS = [
    # Route 77A
    {"route_no": "77A", "stop_code": "MDU-001", "sequence": 1, "distance_from_start_km": 0.0, "scheduled_offset_min": 0},
    {"route_no": "77A", "stop_code": "MDU-002", "sequence": 2, "distance_from_start_km": 1.8, "scheduled_offset_min": 5},
    {"route_no": "77A", "stop_code": "MDU-003", "sequence": 3, "distance_from_start_km": 3.2, "scheduled_offset_min": 10},
    {"route_no": "77A", "stop_code": "MDU-004", "sequence": 4, "distance_from_start_km": 4.5, "scheduled_offset_min": 14},
    {"route_no": "77A", "stop_code": "MDU-005", "sequence": 5, "distance_from_start_km": 6.1, "scheduled_offset_min": 19},
    {"route_no": "77A", "stop_code": "MDU-006", "sequence": 6, "distance_from_start_km": 8.4, "scheduled_offset_min": 26},
    {"route_no": "77A", "stop_code": "MDU-007", "sequence": 7, "distance_from_start_km": 12.2, "scheduled_offset_min": 36},
    {"route_no": "77A", "stop_code": "MDU-008", "sequence": 8, "distance_from_start_km": 15.8, "scheduled_offset_min": 45},

    # Route 88 (Airport)
    {"route_no": "88", "stop_code": "MDU-001", "sequence": 1, "distance_from_start_km": 0.0, "scheduled_offset_min": 0},
    {"route_no": "88", "stop_code": "MDU-009", "sequence": 2, "distance_from_start_km": 0.8, "scheduled_offset_min": 3},
    {"route_no": "88", "stop_code": "MDU-010", "sequence": 3, "distance_from_start_km": 2.4, "scheduled_offset_min": 8},
    {"route_no": "88", "stop_code": "MDU-011", "sequence": 4, "distance_from_start_km": 4.6, "scheduled_offset_min": 14},
    {"route_no": "88", "stop_code": "MDU-012", "sequence": 5, "distance_from_start_km": 7.5, "scheduled_offset_min": 22},
    {"route_no": "88", "stop_code": "MDU-013", "sequence": 6, "distance_from_start_km": 9.8, "scheduled_offset_min": 28},
    {"route_no": "88", "stop_code": "MDU-014", "sequence": 7, "distance_from_start_km": 11.9, "scheduled_offset_min": 34},
    {"route_no": "88", "stop_code": "MDU-015", "sequence": 8, "distance_from_start_km": 14.2, "scheduled_offset_min": 40},

    # Route 48P
    {"route_no": "48P", "stop_code": "MDU-001", "sequence": 1, "distance_from_start_km": 0.0, "scheduled_offset_min": 0},
    {"route_no": "48P", "stop_code": "MDU-009", "sequence": 2, "distance_from_start_km": 0.8, "scheduled_offset_min": 3},
    {"route_no": "48P", "stop_code": "MDU-016", "sequence": 3, "distance_from_start_km": 2.9, "scheduled_offset_min": 9},
    {"route_no": "48P", "stop_code": "MDU-017", "sequence": 4, "distance_from_start_km": 5.2, "scheduled_offset_min": 15},
    {"route_no": "48P", "stop_code": "MDU-018", "sequence": 5, "distance_from_start_km": 7.4, "scheduled_offset_min": 21},
    {"route_no": "48P", "stop_code": "MDU-019", "sequence": 6, "distance_from_start_km": 10.1, "scheduled_offset_min": 28},
    {"route_no": "48P", "stop_code": "MDU-020", "sequence": 7, "distance_from_start_km": 13.6, "scheduled_offset_min": 38},

    # Route 700
    {"route_no": "700", "stop_code": "MDU-006", "sequence": 1, "distance_from_start_km": 0.0, "scheduled_offset_min": 0},
    {"route_no": "700", "stop_code": "MDU-021", "sequence": 2, "distance_from_start_km": 2.1, "scheduled_offset_min": 6},
    {"route_no": "700", "stop_code": "MDU-022", "sequence": 3, "distance_from_start_km": 3.8, "scheduled_offset_min": 11},
    {"route_no": "700", "stop_code": "MDU-023", "sequence": 4, "distance_from_start_km": 5.9, "scheduled_offset_min": 17},
    {"route_no": "700", "stop_code": "MDU-010", "sequence": 5, "distance_from_start_km": 8.2, "scheduled_offset_min": 24},
    {"route_no": "700", "stop_code": "MDU-001", "sequence": 6, "distance_from_start_km": 9.8, "scheduled_offset_min": 29},
    {"route_no": "700", "stop_code": "MDU-024", "sequence": 7, "distance_from_start_km": 13.1, "scheduled_offset_min": 38},
    {"route_no": "700", "stop_code": "MDU-025", "sequence": 8, "distance_from_start_km": 15.5, "scheduled_offset_min": 45},
]


def generate_observations():
    """Generate 600 realistic historical bus trips & arrival observation records for Madurai."""
    observations = []
    random.seed(42)

    # Base dates across recent days
    base_date = datetime(2026, 11, 15, 6, 0, 0, tzinfo=timezone.utc)

    trip_counter = 1000
    for day_offset in range(4): # 4 days of operations
        current_day = base_date + timedelta(days=day_offset)

        for route_info in ROUTES:
            route_no = route_info["route_no"]
            route_stops = [rs for rs in ROUTE_STOPS if rs["route_no"] == route_no]
            headway = route_info["scheduled_headway_min"]

            # Trips throughout the day from 06:00 to 21:00 (every 2-3 headways)
            for hour in range(6, 21, 2):
                trip_counter += 1
                trip_id = f"TRIP-MDU-{route_no}-{trip_counter}"
                trip_departure = current_day.replace(hour=hour, minute=random.choice([0, 15, 30, 45]))

                # Rush hour effect (8-10 AM and 5-7 PM in Madurai have heavy Goripalayam/Simmakkal bottlenecks)
                is_rush_hour = hour in [8, 9, 10, 17, 18, 19]
                weather_rain = 12.5 if (day_offset == 2 and hour >= 16) else 0.0 # Rain shock on Day 2 evening
                base_delay = (3.5 if is_rush_hour else 0.5) + (4.0 if weather_rain > 0 else 0.0)

                accumulated_delay = max(0.0, random.gauss(base_delay, 1.2))

                for rs in route_stops:
                    stop_code = rs["stop_code"]
                    sched_offset = rs["scheduled_offset_min"]
                    sched_arrival = trip_departure + timedelta(minutes=sched_offset)

                    # Delay compounds along sequence with slight randomness
                    stop_delay = round(accumulated_delay * (rs["sequence"] / len(route_stops)) + random.uniform(-0.5, 1.5), 1)
                    actual_arrival = sched_arrival + timedelta(minutes=stop_delay)

                    observations.append({
                        "trip_id": trip_id,
                        "route_no": route_no,
                        "stop_code": stop_code,
                        "sequence": rs["sequence"],
                        "scheduled_arrival": sched_arrival.strftime("%Y-%m-%d %H:%M:%S"),
                        "actual_arrival": actual_arrival.strftime("%Y-%m-%d %H:%M:%S"),
                        "delay_min": stop_delay,
                        "precipitation_mm": weather_rain,
                        "passenger_load_pct": random.randint(75, 95) if is_rush_hour else random.randint(40, 70),
                    })

    return observations


def write_csv_files(observations):
    """Write individual CSV files ready for web upload into data/madurai/."""
    # 1. Routes CSV
    routes_csv = os.path.join(OUTPUT_DIR, "madurai_routes.csv")
    with open(routes_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["route_no", "name", "origin", "destination", "total_distance_km", "scheduled_headway_min", "active"])
        writer.writeheader()
        writer.writerows(ROUTES)

    # 2. Stops CSV
    stops_csv = os.path.join(OUTPUT_DIR, "madurai_stops.csv")
    with open(stops_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["stop_code", "name", "lat", "lon"])
        writer.writeheader()
        writer.writerows(STOPS)

    # 3. Route Stops CSV
    route_stops_csv = os.path.join(OUTPUT_DIR, "madurai_route_stops.csv")
    with open(route_stops_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["route_no", "stop_code", "sequence", "distance_from_start_km", "scheduled_offset_min"])
        writer.writeheader()
        writer.writerows(ROUTE_STOPS)

    # 4. Observations CSV
    obs_csv = os.path.join(OUTPUT_DIR, "madurai_observations.csv")
    with open(obs_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["trip_id", "route_no", "stop_code", "scheduled_arrival", "actual_arrival", "delay_min", "precipitation_mm", "passenger_load_pct"])
        writer.writeheader()
        for o in observations:
            row = dict(o)
            row.pop("sequence", None)
            writer.writerow(row)

    print(f"Generated CSV files in {OUTPUT_DIR}")


def write_styled_excel(observations):
    """Generate multi-sheet styled Excel workbook."""
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10)
    primary_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid") # Royal Blue
    accent_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid") # Teal
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )

    sheets_data = [
        ("Routes", ["Route No", "Route Name", "Origin", "Destination", "Distance (km)", "Headway (min)", "Status"],
         [[r["route_no"], r["name"], r["origin"], r["destination"], r["total_distance_km"], r["scheduled_headway_min"], "Active" if r["active"] else "Inactive"] for r in ROUTES]),

        ("Stops", ["Stop Code", "Stop Name", "Latitude", "Longitude"],
         [[s["stop_code"], s["name"], s["lat"], s["lon"]] for s in STOPS]),

        ("Route_Stops", ["Route No", "Stop Code", "Sequence", "Distance from Origin (km)", "Travel Offset (min)"],
         [[rs["route_no"], rs["stop_code"], rs["sequence"], rs["distance_from_start_km"], rs["scheduled_offset_min"]] for rs in ROUTE_STOPS]),

        ("Observations", ["Trip ID", "Route No", "Stop Code", "Scheduled Arrival", "Actual Arrival", "Delay (min)", "Rain (mm)", "Bus Occupancy %"],
         [[o["trip_id"], o["route_no"], o["stop_code"], o["scheduled_arrival"], o["actual_arrival"], o["delay_min"], o["precipitation_mm"], o["passenger_load_pct"]] for o in observations])
    ]

    for title, headers, rows in sheets_data:
        ws = wb.create_sheet(title=title)
        ws.views.sheetView[0].showGridLines = True

        # Header Row
        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = primary_fill if title in ["Routes", "Observations"] else accent_fill
            cell.alignment = Alignment(horizontal="center" if col_idx in [1, 5, 6, 7] else "left", vertical="center")
            cell.border = thin_border
        ws.row_dimensions[1].height = 28

        # Data Rows
        for r_idx, row_values in enumerate(rows, start=2):
            ws.append(row_values)
            is_even = (r_idx % 2 == 0)
            for c_idx in range(1, len(row_values) + 1):
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.font = data_font
                cell.border = thin_border
                if is_even:
                    cell.fill = zebra_fill
                # Right align numbers
                if isinstance(row_values[c_idx - 1], (int, float)):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[r_idx].height = 20

        # Auto fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    excel_path = os.path.join(OUTPUT_DIR, "madurai_city_bus_transit_data.xlsx")
    wb.save(excel_path)
    print(f"Excel file created: {excel_path}")
    return excel_path


if __name__ == "__main__":
    obs = generate_observations()
    write_csv_files(obs)
    excel_file = write_styled_excel(obs)
    print("Madurai dataset generation complete!")
