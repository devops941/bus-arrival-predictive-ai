"""
BusArrival AI - Model Validation, Evaluation Metrics & Error Distributions
Implements Section 7.1, 7.4 validation standards:
- Chronological train/test split (no future leakage in validation)
- Leave-one-route-out cross validation
- Metrics: MAE, RMSE, MAPE (tiny-denominator guarded), % within +/-2 min, Bias, P90 coverage
- Residual error distributions overall and by route/hour/day type
- Honest baseline comparison: Model beats baseline only if verified on held-out data
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from src.ml.features import FEATURE_COLUMNS, FeatureTable
from src.ml.models import (
    create_model_instance,
    BaselineModel,
    QuantileGBModel,
    save_model_artifact,
)


def compute_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_p90: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Compute core forecast accuracy metrics:
    MAE, RMSE, MAPE (guarded), % within +/-2 min, Bias, P90 coverage.
    """
    yt = np.array(y_true, dtype=float)
    yp = np.array(y_pred, dtype=float)
    total = len(yt)

    if total == 0:
        return {
            "mae": 0.0,
            "rmse": 0.0,
            "mape": 0.0,
            "within_2_min_pct": 0.0,
            "bias": 0.0,
            "p90_coverage_pct": 0.0,
        }

    errors = yp - yt
    abs_errors = np.abs(errors)

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # Guarded MAPE: divide by max(|y_true|, 1.0)
    safe_denominators = np.maximum(np.abs(yt), 1.0)
    mape = float(np.mean(abs_errors / safe_denominators) * 100.0)

    within_2_min = float(np.mean(abs_errors <= 2.0) * 100.0)
    bias = float(np.mean(errors))

    p90_cov = 0.0
    if y_p90 is not None:
        p90_arr = np.array(y_p90, dtype=float)
        p90_cov = float(np.mean(yt <= p90_arr) * 100.0)

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 1),
        "within_2_min_pct": round(within_2_min, 1),
        "bias": round(bias, 2),
        "p90_coverage_pct": round(p90_cov, 1),
    }


def chronological_split(
    feature_table: FeatureTable,
    test_ratio: float = 0.2
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split dataset chronologically: earlier records for training, latest for evaluation.
    """
    records = list(feature_table.records)
    records.sort(key=lambda r: r.get("scheduled_arrival"))
    split_idx = int(len(records) * (1.0 - test_ratio))
    return records[:split_idx], records[split_idx:]


def compute_error_distributions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    meta_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute residual error distributions (y_pred - y_true) overall and by route/hour.
    """
    residuals = y_pred - y_true

    # 1. Overall histogram bins between -10 and +10 min
    bins = np.linspace(-10, 10, 21)
    hist, bin_edges = np.histogram(residuals, bins=bins)
    histogram_data = []
    for i in range(len(hist)):
        histogram_data.append({
            "bin_start": round(float(bin_edges[i]), 1),
            "bin_end": round(float(bin_edges[i + 1]), 1),
            "bin_label": f"{bin_edges[i]:.0f} to {bin_edges[i+1]:.0f}m",
            "count": int(hist[i]),
        })

    # 2. Residuals by route
    route_residuals: Dict[str, List[float]] = {}
    hour_residuals: Dict[int, List[float]] = {}

    for r_rec, res_val in zip(meta_records, residuals):
        r_no = str(r_rec.get("route_no", "Unknown"))
        route_residuals.setdefault(r_no, []).append(res_val)

        sched = r_rec.get("scheduled_arrival")
        h = sched.hour if hasattr(sched, "hour") else 8
        hour_residuals.setdefault(h, []).append(res_val)

    route_dist = []
    for r_no, res_vals in sorted(route_residuals.items()):
        arr = np.array(res_vals)
        route_dist.append({
            "route_no": r_no,
            "mae": round(float(np.mean(np.abs(arr))), 2),
            "rmse": round(float(np.sqrt(np.mean(arr ** 2))), 2),
            "within_2_min_pct": round(float(np.mean(np.abs(arr) <= 2.0) * 100.0), 1),
            "sample_count": len(arr),
        })

    hour_dist = []
    for h, res_vals in sorted(hour_residuals.items()):
        arr = np.array(res_vals)
        hour_dist.append({
            "hour": h,
            "mae": round(float(np.mean(np.abs(arr))), 2),
            "sample_count": len(arr),
        })

    return {
        "histogram": histogram_data,
        "by_route": route_dist,
        "by_hour": hour_dist,
    }


def leave_one_route_out_validation(
    algorithm: str,
    feature_table: FeatureTable,
    random_seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Group validation: Evaluates generalizability by training on N-1 routes
    and testing exclusively on the held-out route.
    """
    records = feature_table.records
    unique_routes = sorted(list({r.get("route_no") for r in records if r.get("route_no")}))
    route_results = []

    for held_out in unique_routes:
        train_recs = [r for r in records if r.get("route_no") != held_out]
        test_recs = [r for r in records if r.get("route_no") == held_out]

        if not train_recs or not test_recs:
            continue

        model = create_model_instance(algorithm, random_seed=random_seed)
        X_train = np.array([[r.get(c, 0.0) for c in FEATURE_COLUMNS] for r in train_recs], dtype=float)
        y_train = np.array([r.get("delay_min", 0.0) for r in train_recs], dtype=float)

        X_test = np.array([[r.get(c, 0.0) for c in FEATURE_COLUMNS] for r in test_recs], dtype=float)
        y_test = np.array([r.get("delay_min", 0.0) for r in test_recs], dtype=float)

        if isinstance(model, BaselineModel):
            model.fit(X_train, y_train, meta_records=train_recs)
            y_pred = model.predict(X_test, meta_records=test_recs)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

        metrics = compute_regression_metrics(y_test, y_pred)
        route_results.append({
            "held_out_route": str(held_out),
            "train_samples": len(train_recs),
            "test_samples": len(test_recs),
            **metrics,
        })

    return route_results


def run_training_pipeline(
    algorithm: str,
    feature_df: Any,
    model_id: str,
    created_by: str = "system",
    random_seed: int = 42,
) -> Dict[str, Any]:
    """
    Full model training and validation workflow.
    """
    if not isinstance(feature_df, FeatureTable):
        feature_table = FeatureTable(feature_df if isinstance(feature_df, list) else feature_df.to_dict(orient="records"))
    else:
        feature_table = feature_df

    train_recs, test_recs = chronological_split(feature_table, test_ratio=0.2)

    X_train = np.array([[r.get(c, 0.0) for c in FEATURE_COLUMNS] for r in train_recs], dtype=float)
    y_train = np.array([r.get("delay_min", 0.0) for r in train_recs], dtype=float)

    X_test = np.array([[r.get(c, 0.0) for c in FEATURE_COLUMNS] for r in test_recs], dtype=float)
    y_test = np.array([r.get("delay_min", 0.0) for r in test_recs], dtype=float)

    # Train Candidate Model
    model = create_model_instance(algorithm, random_seed=random_seed)
    if isinstance(model, BaselineModel):
        model.fit(X_train, y_train, meta_records=train_recs)
        y_pred = model.predict(X_test, meta_records=test_recs)
        y_p90 = None
    elif isinstance(model, QuantileGBModel):
        model.fit(X_train, y_train)
        y_pred, y_p90 = model.predict_intervals(X_test)
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_p90 = None

    metrics = compute_regression_metrics(y_test, y_pred, y_p90=y_p90)

    # Train Baseline Model on same train split
    baseline_model = BaselineModel()
    baseline_model.fit(X_train, y_train, meta_records=train_recs)
    y_base_pred = baseline_model.predict(X_test, meta_records=test_recs)
    baseline_metrics = compute_regression_metrics(y_test, y_base_pred)

    beats_baseline = bool(metrics["mae"] <= baseline_metrics["mae"])

    # Leave-one-route-out cross validation
    route_cv = leave_one_route_out_validation(algorithm, feature_table, random_seed=random_seed)

    # Compute error distributions
    distributions = compute_error_distributions(y_test, y_pred, test_recs)

    # Feature importances
    feature_importances = {}
    if hasattr(model, "feature_importances_") and model.feature_importances_ is not None:
        for name, imp in zip(FEATURE_COLUMNS, model.feature_importances_):
            feature_importances[name] = round(float(imp), 4)

    train_dates = [r.get("scheduled_arrival") for r in train_recs if r.get("scheduled_arrival")]
    test_dates = [r.get("scheduled_arrival") for r in test_recs if r.get("scheduled_arrival")]

    train_start = str(min(train_dates)) if train_dates else ""
    train_end = str(max(train_dates)) if train_dates else ""
    test_end = str(max(test_dates)) if test_dates else ""

    model_doc = {
        "model_id": model_id,
        "name": f"{algorithm.replace('_', ' ').title()} ({model_id[:8]})",
        "algorithm": algorithm,
        "features": FEATURE_COLUMNS,
        "train_window": f"{train_start[:10]} to {train_end[:10]}",
        "eval_window": f"{train_end[:10]} to {test_end[:10]}",
        "train_samples": len(train_recs),
        "test_samples": len(test_recs),
        "metrics": metrics,
        "baseline_metrics": baseline_metrics,
        "beats_baseline": beats_baseline,
        "leave_route_out": {r["held_out_route"]: r for r in route_cv},
        "error_distributions": distributions,
        "feature_importances": feature_importances,
        "status": "candidate",
        "created_by": created_by,
    }

    artifact_path = save_model_artifact(model, model_id, model_doc)
    model_doc["artifact_path"] = artifact_path
    return model_doc
