"""
Reports Generation and Export Router.
Compiles and streams CSV, Excel (.xlsx), and HTML reports.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.deps import require_role, get_current_user, get_db
from src.report.generator import save_report_file
from src.db.repositories.report_repo import ReportRepository
from src.db.repositories.route_repo import RouteRepository
from src.db.repositories.observation_repo import ObservationRepository
from src.db.repositories.audit_repo import AuditRepository
from src.analytics.trends import compute_punctuality_metrics, compute_route_summary


router = APIRouter(prefix="/reports", tags=["Reports & Exports"])


class CreateReportRequest(BaseModel):
    kind: str = Field(default="summary", description="Report kind: summary, route_accuracy, audit")
    file_format: Optional[str] = Field(default=None, description="Format: csv, excel, html")
    format: Optional[str] = Field(default=None, description="Format alias: csv, xlsx, pdf, html")
    title: Optional[str] = None
    route_id: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_report(
    payload: CreateReportRequest,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    db=Depends(get_db),
):
    """
    Generate an operational report in CSV, Excel, or HTML format.
    """
    kind = payload.kind.lower().strip()
    norm_format = (payload.file_format or payload.format or "csv").lower().strip()
    report_repo = ReportRepository(db)
    audit_repo = AuditRepository(db)

    title = payload.title or f"Transit {kind.replace('_', ' ').title()} Report"
    columns = []
    rows = []
    kpis = []

    if kind == "summary":
        route_repo = RouteRepository(db)
        obs_repo = ObservationRepository(db)
        routes = route_repo.find_many({}, limit=1000)
        observations = obs_repo.find_many({}, limit=15000)
        summaries = compute_route_summary(routes, observations)

        columns = ["Route No", "Name", "Total Dist (km)", "Headway (min)", "Total Obs", "Avg Delay (min)", "On-Time %", "Minor %", "Major %"]
        for s in summaries:
            rows.append([
                s["route_no"],
                s["name"],
                s["total_distance_km"],
                s["scheduled_headway_min"],
                s["count"],
                s["avg_delay"],
                f"{s['on_time_pct']}%",
                f"{s['minor_delay_pct']}%",
                f"{s['major_delay_pct']}%",
            ])

        all_delays = [float(o.get("delay_min", 0.0)) for o in observations if "delay_min" in o]
        overall = compute_punctuality_metrics(all_delays)
        kpis = [
            {"label": "On-Time Rate", "value": f"{overall['on_time_pct']}%"},
            {"label": "Avg Delay", "value": f"{overall['avg_delay']:+.1f}m"},
            {"label": "Active Routes", "value": str(len(routes))},
            {"label": "Total Samples", "value": f"{overall['count']:,}"},
        ]

    elif kind == "audit":
        audit_records = audit_repo.find_many({}, limit=500, sort=[("timestamp", -1)])
        columns = ["Timestamp (UTC)", "Action", "Entity Type", "Entity ID", "User Email", "IP Address"]
        for a in audit_records:
            ts = a.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
            rows.append([
                ts_str,
                a.get("action", ""),
                a.get("entity_type", ""),
                a.get("entity_id", "-"),
                a.get("user_email", "system"),
                a.get("ip_address", "127.0.0.1"),
            ])
        kpis = [
            {"label": "Total Events", "value": str(len(audit_records))},
            {"label": "Report Period", "value": "Recent 500"},
        ]
    else:
        # Default generic data export
        columns = ["Column 1", "Column 2"]
        rows = [["Data 1", "Data 2"]]

    report_id, file_path = save_report_file(
        kind=kind,
        file_format=norm_format,
        title=title,
        columns=columns,
        rows=rows,
        kpis=kpis,
        author=current_user.get("email", "Admin"),
    )

    report_repo.save_report_record(
        report_id=report_id,
        title=title,
        kind=kind,
        file_format=norm_format,
        file_path=file_path,
        row_count=len(rows),
        author=current_user.get("email", "Admin"),
        author_id=current_user.get("id"),
    )

    audit_repo.log_event(
        action="REPORT_GENERATED",
        entity_type="report",
        entity_id=report_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        details={"kind": kind, "format": norm_format, "rows": len(rows)},
    )

    return {
        "report_id": report_id,
        "title": title,
        "kind": kind,
        "file_format": norm_format,
        "row_count": len(rows),
        "download_url": f"/api/reports/{report_id}/download",
    }


@router.get("")
def list_reports(
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
):
    """List previously generated reports."""
    report_repo = ReportRepository(db)
    return report_repo.find_many({}, limit=limit, sort=[("created_at", -1)])


@router.get("/{id}/download")
def download_report(id: str, token: Optional[str] = Query(None), db=Depends(get_db)):
    """Stream report artifact file for browser download."""
    report_repo = ReportRepository(db)
    rec = report_repo.get_by_report_id(id)
    if not rec or not rec.get("file_path"):
        raise HTTPException(status_code=404, detail={"detail": "Report record not found", "code": "NOT_FOUND"})

    raw_path = rec["file_path"]
    fpath = Path(raw_path)
    if not fpath.is_absolute():
        fpath = Path.cwd() / raw_path

    if not fpath.exists():
        raise HTTPException(status_code=404, detail={"detail": "Report file not found on server disk", "code": "NOT_FOUND"})

    fmt = rec.get("file_format") or rec.get("format") or "csv"
    media_types = {
        "csv": "text/csv",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "html": "text/html",
        "pdf": "application/pdf",
    }
    media_type = media_types.get(fmt, "application/octet-stream")
    filename = fpath.name

    return FileResponse(
        path=str(fpath),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
