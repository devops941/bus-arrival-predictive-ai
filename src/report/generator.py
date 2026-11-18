"""
BusArrival AI - Report Generation Engine
Generates CSV, Excel (.xlsx via openpyxl), and Styled HTML/Print reports (via Jinja2).
Saves output artifacts into outputs/reports/ and logs generation in the database.
"""

from datetime import datetime, timezone
from pathlib import Path
import os
import csv
import io
import uuid
from typing import Dict, Any, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import jinja2

from src.config import get_settings


HTML_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{{ title }} - BusArrival AI</title>
<style>
  body { font-family: 'Segoe UI', Inter, system-ui, sans-serif; background-color: #F6F8FB; color: #0F1E33; margin: 0; padding: 32px; }
  .container { max-width: 900px; margin: 0 auto; background: #FFFFFF; border: 1px solid #DCE3EE; border-radius: 12px; padding: 32px; box-shadow: 0 1px 3px rgba(15,30,51,0.06); }
  .header { border-bottom: 2px solid #1D4ED8; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-end; }
  h1 { margin: 0; font-size: 24px; color: #1D4ED8; }
  .meta { color: #7C8CA3; font-size: 13px; }
  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
  .kpi-card { background: #EDF1F7; border-radius: 8px; padding: 16px; }
  .kpi-val { font-size: 24px; font-weight: bold; color: #0F1E33; }
  .kpi-label { font-size: 12px; color: #4A5C75; text-transform: uppercase; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }
  th { background: #EDF1F7; color: #0F1E33; text-align: left; padding: 10px 12px; border-bottom: 2px solid #DCE3EE; }
  td { padding: 10px 12px; border-bottom: 1px solid #DCE3EE; }
  tr:hover { background: #F6F8FB; }
  .badge-ontime { background: #DCFCE7; color: #15803D; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }
  .badge-minor { background: #FEF3C7; color: #B45309; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }
  .badge-major { background: #FEE2E2; color: #B91C1C; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }
  .footer { margin-top: 40px; font-size: 12px; color: #7C8CA3; text-align: center; border-top: 1px solid #DCE3EE; padding-top: 16px; }
  @media print { body { background: #FFFFFF; padding: 0; } .container { border: none; box-shadow: none; padding: 0; } }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>{{ title }}</h1>
      <div class="meta">BusArrival AI Operational Transit Intelligence Report</div>
    </div>
    <div class="meta" style="text-align: right;">
      <div>Generated: {{ generated_at }}</div>
      <div>Author: {{ author }}</div>
    </div>
  </div>

  {% if kpis %}
  <div class="kpi-grid">
    {% for k in kpis %}
    <div class="kpi-card">
      <div class="kpi-val">{{ k.value }}</div>
      <div class="kpi-label">{{ k.label }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <h3>{{ table_title }}</h3>
  <table>
    <thead>
      <tr>
        {% for col in columns %}
        <th>{{ col }}</th>
        {% endfor %}
      </tr>
    </thead>
    <tbody>
      {% for row in rows %}
      <tr>
        {% for val in row %}
        <td>{{ val }}</td>
        {% endfor %}
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="footer">
    BusArrival AI - Illustrative Demo Report. All predictions are honest machine learning estimates.
  </div>
</div>
</body>
</html>
"""


def generate_csv_report(columns: List[str], rows: List[List[Any]]) -> str:
    """Generate CSV text string from table rows."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(rows)
    return output.getvalue()


def generate_excel_report(title: str, columns: List[str], rows: List[List[Any]]) -> bytes:
    """Generate professional Excel workbook with openpyxl styling."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:30]

    # Brand header
    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = f"BusArrival AI - {title}"
    title_cell.font = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1D4ED8", end_color="1D4ED8", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # Column Headers
    header_fill = PatternFill(start_color="EDF1F7", end_color="EDF1F7", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="0F1E33")
    thin_border = Border(
        bottom=Side(style="medium", color="DCE3EE"),
        top=Side(style="thin", color="DCE3EE"),
        left=Side(style="thin", color="DCE3EE"),
        right=Side(style="thin", color="DCE3EE")
    )

    ws.append([])  # blank row 2
    for col_idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=3, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border = thin_border
    ws.row_dimensions[3].height = 24

    # Data Rows
    row_font = Font(name="Segoe UI", size=10)
    for row_idx, r_data in enumerate(rows, start=4):
        ws.row_dimensions[row_idx].height = 20
        for col_idx, val in enumerate(r_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = row_font
            cell.border = Border(
                bottom=Side(style="thin", color="EDF1F7"),
                left=Side(style="thin", color="EDF1F7"),
                right=Side(style="thin", color="EDF1F7")
            )

    # Auto-fit column widths
    from openpyxl.utils import get_column_letter
    for col_idx in range(1, len(columns) + 1):
        col_letter = get_column_letter(col_idx)
        max_len = max((len(str(ws.cell(row=r, column=col_idx).value or "")) for r in range(3, len(rows) + 4)), default=10)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generate_html_report(
    title: str,
    author: str,
    kpis: Optional[List[Dict[str, str]]],
    table_title: str,
    columns: List[str],
    rows: List[List[Any]],
) -> str:
    """Render branded HTML report using Jinja2 template."""
    template = jinja2.Template(HTML_REPORT_TEMPLATE)
    return template.render(
        title=title,
        author=author,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        kpis=kpis or [],
        table_title=table_title,
        columns=columns,
        rows=rows,
    )


def save_report_file(
    kind: str,
    file_format: str,
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    kpis: Optional[List[Dict[str, str]]] = None,
    author: str = "Admin",
) -> Tuple[str, str]:
    """
    Generate report file and save to outputs/reports/.
    Returns (report_id, file_path).
    """
    settings = get_settings()
    out_dir = Path(settings.REPORT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_id = f"rep_{uuid.uuid4().hex[:10]}"
    norm_format = file_format.lower().strip()

    if norm_format == "csv":
        filename = f"{report_id}.csv"
        file_path = out_dir / filename
        content = generate_csv_report(columns, rows)
        file_path.write_text(content, encoding="utf-8")
    elif norm_format in ("xlsx", "excel"):
        filename = f"{report_id}.xlsx"
        file_path = out_dir / filename
        bytes_data = generate_excel_report(title, columns, rows)
        file_path.write_bytes(bytes_data)
    elif norm_format in ("html", "pdf"):
        filename = f"{report_id}.html"
        file_path = out_dir / filename
        html_content = generate_html_report(title, author, kpis, title, columns, rows)
        file_path.write_text(html_content, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported report format '{file_format}'. Must be csv, excel, or html.")

    return report_id, str(file_path)
