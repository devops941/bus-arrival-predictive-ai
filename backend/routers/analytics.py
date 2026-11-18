"""
Analytics and Delay Trends API Router.
Exposes endpoints for delay trends, congestion heatmaps, and route summaries.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from backend.deps import get_db
from src.db.repositories.observation_repo import ObservationRepository
from src.db.repositories.route_repo import RouteRepository
from src.analytics.trends import (
    compute_delay_by_hour,
    compute_delay_by_day_type,
    compute_delay_by_route,
    compute_delay_by_stop,
    compute_heatmap_matrix,
    compute_route_summary,
    compute_punctuality_metrics,
)


router = APIRouter(prefix="/analytics", tags=["Analytics & Trends"])


@router.get("/delay-trends")
def get_delay_trends(
    route_no: Optional[str] = Query(None, description="Optional route filter"),
    dimension: str = Query("all", description="Dimension: all, hour, day_type, route, stop"),
    db=Depends(get_db),
):
    """
    Get aggregated historical delay trends by hour, day type, route, or stop.
    """
    obs_repo = ObservationRepository(db)
    query = {"route_no": route_no} if route_no else {}
    observations = obs_repo.find_many(query, limit=10000)

    all_delays = [float(o.get("delay_min", 0.0)) for o in observations if "delay_min" in o]
    overall_metrics = compute_punctuality_metrics(all_delays)

    response = {
        "overall": overall_metrics,
        "sample_count": len(observations),
        "route_filter": route_no,
    }

    if dimension in ("all", "hour"):
        response["by_hour"] = compute_delay_by_hour(observations)
    if dimension in ("all", "day_type"):
        day_type_dict = compute_delay_by_day_type(observations)
        response["by_day_type"] = [
            {"day_type": "weekday", **day_type_dict.get("weekday", {})},
            {"day_type": "weekend", **day_type_dict.get("weekend", {})},
        ]
        response["by_day_type_map"] = day_type_dict
    if dimension in ("all", "route") and not route_no:
        response["by_route"] = compute_delay_by_route(observations)
    if dimension in ("all", "stop"):
        response["by_stop"] = compute_delay_by_stop(observations, route_no=route_no)

    return response


@router.get("/heatmap")
def get_delay_heatmap(
    route_no: Optional[str] = Query(None, description="Optional route filter"),
    start_hour: int = Query(6, ge=0, le=23),
    end_hour: int = Query(22, ge=0, le=23),
    db=Depends(get_db),
):
    """
    Get 2D matrix of Hour of Day x Day of Week average arrival delays.
    """
    obs_repo = ObservationRepository(db)
    query = {"route_no": route_no} if route_no else {}
    observations = obs_repo.find_many(query, limit=10000)

    cells = compute_heatmap_matrix(observations, start_hour=start_hour, end_hour=end_hour)
    return {
        "cells": cells,
        "route_filter": route_no,
        "start_hour": start_hour,
        "end_hour": end_hour,
    }


@router.get("/route-summary")
def get_route_summary(db=Depends(get_db)):
    """
    Get corridor performance summaries and punctuality percentages across all active routes.
    """
    route_repo = RouteRepository(db)
    obs_repo = ObservationRepository(db)

    routes = route_repo.find_many({}, limit=1000)
    observations = obs_repo.find_many({}, limit=10000)

    summaries = compute_route_summary(routes, observations)
    return summaries
