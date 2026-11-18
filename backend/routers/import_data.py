"""
CSV and Data Import Router.
Validates raw datasets and provides row-level error reporting per Section 5.
Supports committing valid rows only.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from pydantic import BaseModel

from backend.deps import require_role, get_db
from src.data.ingest import parse_csv_content, process_import
from src.db.repositories.route_repo import RouteRepository, StopRepository
from src.db.repositories.observation_repo import ObservationRepository
from src.db.repositories.audit_repo import AuditRepository


router = APIRouter(prefix="/import", tags=["Data Import"])


class ImportIssueItem(BaseModel):
    row: int
    field: str
    issue_type: str
    message: str
    is_fatal: bool


class ImportValidationReport(BaseModel):
    kind: str
    total_rows: int
    valid_count: int
    invalid_count: int
    committed: bool
    issues: List[ImportIssueItem]


@router.post("/{kind}", response_model=ImportValidationReport)
async def import_dataset(
    kind: str,
    file: UploadFile = File(...),
    commit: bool = Query(False, description="Set True to commit valid rows into the database"),
    import_valid_only: bool = Query(True, description="When true, valid rows are imported even if errors exist"),
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    db=Depends(get_db),
):
    """
    Upload and validate a CSV dataset ('routes', 'stops', 'observations').
    Returns detailed row-level error report and optionally commits valid records.
    """
    valid_kinds = ("routes", "stops", "observations")
    normalized_kind = kind.lower().strip()
    if normalized_kind not in valid_kinds:
        raise HTTPException(
            status_code=400,
            detail={"detail": f"Invalid import kind '{kind}'. Must be one of {valid_kinds}", "code": "INVALID_KIND"},
        )

    content_bytes = await file.read()
    try:
        csv_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content_bytes.decode("latin-1")

    rows = parse_csv_content(csv_text)
    if not rows:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Uploaded CSV file contains no data rows", "code": "EMPTY_FILE"},
        )

    # Fetch reference sets for foreign key validation
    route_repo = RouteRepository(db)
    stop_repo = StopRepository(db)
    obs_repo = ObservationRepository(db)
    audit_repo = AuditRepository(db)

    all_routes = route_repo.find_many({}, limit=1000)
    all_stops = stop_repo.find_many({}, limit=2000)

    route_set = {r["route_no"] for r in all_routes}
    stop_set = {s["stop_code"] for s in all_stops}

    report = process_import(
        normalized_kind,
        rows,
        valid_route_nos=route_set,
        valid_stop_codes=stop_set,
    )

    committed = False
    valid_rows = report["valid_rows"]

    if commit and valid_rows and (import_valid_only or report["invalid_count"] == 0):
        if normalized_kind == "routes":
            route_repo.bulk_upsert_routes(valid_rows)
        elif normalized_kind == "stops":
            stop_repo.bulk_upsert_stops(valid_rows)
        elif normalized_kind == "observations":
            obs_repo.bulk_upsert_observations(valid_rows)

        committed = True
        audit_repo.log_event(
            action="CSV_IMPORTED",
            entity_type=normalized_kind,
            user_id=current_user["id"],
            user_email=current_user["email"],
            details={
                "filename": file.filename,
                "total_rows": len(rows),
                "imported_rows": len(valid_rows),
                "issues_count": len(report["issues"]),
            },
        )

    issues_out = [
        ImportIssueItem(
            row=i["row"],
            field=i["field"],
            issue_type=i["issue_type"],
            message=i["message"],
            is_fatal=i.get("is_fatal", True),
        )
        for i in report["issues"]
    ]

    return ImportValidationReport(
        kind=normalized_kind,
        total_rows=report["total_rows"],
        valid_count=report["valid_count"],
        invalid_count=report["invalid_count"],
        committed=committed,
        issues=issues_out,
    )
