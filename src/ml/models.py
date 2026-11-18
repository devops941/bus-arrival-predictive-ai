"""
BusArrival AI - Classic Machine Learning Estimators & Architectures
Implements Section 7.1, 7.3 classic ML models using pure NumPy linear algebra & trees:
- Baseline Model (Historical Mean by route x hour x day_type)
- Ridge Regression (Closed-form scaled solution)
- Random Forest Regressor (Ensemble of MSE decision trees with bootstrap sampling)
- Gradient Boosting Regressor (Sequential pseudo-residual tree booster)
- Quantile Gradient Boosting (Dual estimators for P50 median and P90 upper bound)
Serializes artifacts and metadata via joblib.
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import os
import joblib
import numpy as np
from src.config import get_settings


class BaselineModel:
    """Historical mean baseline model by route x hour x weekend."""
    def __init__(self):
        self.lookup_table: Dict[Tuple[str, int, int], float] = {}
        self.route_means: Dict[str, float] = {}
        self.global_mean: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray, meta_records: Optional[List[Dict[str, Any]]] = None) -> "BaselineModel":
        self.global_mean = float(np.mean(y)) if len(y) > 0 else 0.0
        if meta_records and len(meta_records) == len(y):
            groups: Dict[Tuple[str, int, int], List[float]] = {}
            r_groups: Dict[str, List[float]] = {}
            for rec, target in zip(meta_records, y):
                r_no = str(rec.get("route_no", "")).strip()
                sched = rec.get("scheduled_arrival")
                h = sched.hour if hasattr(sched, "hour") else 8
                w = int(rec.get("is_weekend", 0))
                key = (r_no, h, w)
                groups.setdefault(key, []).append(float(target))
                r_groups.setdefault(r_no, []).append(float(target))

            self.lookup_table = {k: float(np.mean(vals)) for k, vals in groups.items()}
            self.route_means = {k: float(np.mean(vals)) for k, vals in r_groups.items()}
        return self

    def predict(self, X: np.ndarray, meta_records: Optional[List[Dict[str, Any]]] = None) -> np.ndarray:
        if not meta_records:
            return np.full(len(X), self.global_mean, dtype=float)
        preds = []
        for rec in meta_records:
            r_no = str(rec.get("route_no", "")).strip()
            sched = rec.get("scheduled_arrival")
            h = sched.hour if hasattr(sched, "hour") else 8
            w = int(rec.get("is_weekend", 0))
            key = (r_no, h, w)
            if key in self.lookup_table:
                preds.append(self.lookup_table[key])
            elif r_no in self.route_means:
                preds.append(self.route_means[r_no])
            else:
                preds.append(self.global_mean)
        return np.array(preds, dtype=float)


class RidgeRegressionModel:
    """L2 Regularized Linear Regression using closed-form OLS solution."""
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.weights: Optional[np.ndarray] = None
        self.intercept: float = 0.0
        self.means: Optional[np.ndarray] = None
        self.stds: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RidgeRegressionModel":
        X_arr = np.array(X, dtype=float)
        y_arr = np.array(y, dtype=float)

        self.means = np.mean(X_arr, axis=0)
        self.stds = np.std(X_arr, axis=0)
        self.stds[self.stds < 1e-6] = 1.0

        X_scaled = (X_arr - self.means) / self.stds
        self.intercept = float(np.mean(y_arr))
        y_centered = y_arr - self.intercept

        n_features = X_scaled.shape[1]
        A = X_scaled.T @ X_scaled + (self.alpha * np.eye(n_features))
        b = X_scaled.T @ y_centered
        self.weights = np.linalg.solve(A, b)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.array(X, dtype=float)
        X_scaled = (X_arr - self.means) / self.stds
        return self.intercept + (X_scaled @ self.weights)


class DecisionNode:
    def __init__(self, feature_idx=None, threshold=None, left=None, right=None, value=None):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value


class DecisionTreeRegressorPure:
    """Recursive binary regression tree minimizing variance."""
    def __init__(self, max_depth: int = 5, min_samples_split: int = 4):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root: Optional[DecisionNode] = None

    def fit(self, X: np.ndarray, y: np.ndarray, depth: int = 0) -> "DecisionTreeRegressorPure":
        self.root = self._build_tree(X, y, depth=0)
        return self

    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int) -> DecisionNode:
        n_samples, n_features = X.shape
        if depth >= self.max_depth or n_samples < self.min_samples_split:
            return DecisionNode(value=float(np.mean(y)) if len(y) > 0 else 0.0)

        best_feat, best_thresh, best_var_red = None, None, 0.0
        current_var = np.var(y) * n_samples

        for f_idx in range(n_features):
            vals = X[:, f_idx]
            thresholds = np.unique(vals)
            if len(thresholds) > 10:
                thresholds = np.quantile(thresholds, np.linspace(0.1, 0.9, 8))

            for t in thresholds:
                left_mask = vals <= t
                right_mask = ~left_mask
                if np.sum(left_mask) < 2 or np.sum(right_mask) < 2:
                    continue

                var_left = np.var(y[left_mask]) * np.sum(left_mask)
                var_right = np.var(y[right_mask]) * np.sum(right_mask)
                var_reduction = current_var - (var_left + var_right)

                if var_reduction > best_var_red:
                    best_var_red = var_reduction
                    best_feat = f_idx
                    best_thresh = t

        if best_feat is None:
            return DecisionNode(value=float(np.mean(y)))

        left_mask = X[:, best_feat] <= best_thresh
        left_child = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._build_tree(X[~left_mask], y[~left_mask], depth + 1)
        return DecisionNode(feature_idx=best_feat, threshold=best_thresh, left=left_child, right=right_child)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._predict_row(self.root, row) for row in X], dtype=float)

    def _predict_row(self, node: DecisionNode, row: np.ndarray) -> float:
        if node.value is not None:
            return node.value
        if row[node.feature_idx] <= node.threshold:
            return self._predict_row(node.left, row)
        return self._predict_row(node.right, row)


class RandomForestRegressorModel:
    """Random Forest regressor with bootstrap sampling and feature importance."""
    def __init__(self, n_estimators: int = 25, max_depth: int = 5, random_seed: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_seed = random_seed
        self.trees: List[DecisionTreeRegressorPure] = []
        self.feature_importances_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestRegressorModel":
        rng = np.random.default_rng(self.random_seed)
        n_samples, n_features = X.shape
        self.trees = []
        feat_counts = np.zeros(n_features)

        for _ in range(self.n_estimators):
            boot_idx = rng.integers(0, n_samples, size=n_samples)
            tree = DecisionTreeRegressorPure(max_depth=self.max_depth)
            tree.fit(X[boot_idx], y[boot_idx])
            self.trees.append(tree)

            def tally_features(node):
                if node and node.feature_idx is not None:
                    feat_counts[node.feature_idx] += 1
                    tally_features(node.left)
                    tally_features(node.right)
            tally_features(tree.root)

        total_nodes = np.sum(feat_counts)
        self.feature_importances_ = feat_counts / (total_nodes or 1.0)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        preds = np.array([tree.predict(X) for tree in self.trees])
        return np.mean(preds, axis=0)


class GradientBoostingRegressorModel:
    """Gradient boosting regressor fitting shallow trees to residuals."""
    def __init__(self, n_estimators: int = 25, learning_rate: float = 0.1, max_depth: int = 3, random_seed: int = 42):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.base_val: float = 0.0
        self.trees: List[DecisionTreeRegressorPure] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GradientBoostingRegressorModel":
        self.base_val = float(np.mean(y))
        y_curr = np.full(len(y), self.base_val, dtype=float)
        self.trees = []

        for _ in range(self.n_estimators):
            residuals = y - y_curr
            tree = DecisionTreeRegressorPure(max_depth=self.max_depth)
            tree.fit(X, residuals)
            self.trees.append(tree)
            y_curr += self.learning_rate * tree.predict(X)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        preds = np.full(len(X), self.base_val, dtype=float)
        for tree in self.trees:
            preds += self.learning_rate * tree.predict(X)
        return preds


class QuantileGBModel:
    """
    Dual Gradient Boosting estimators predicting Median (P50, alpha=0.5)
    and Upper Boundary (P90, alpha=0.9) confidence intervals using pinball loss.
    """
    def __init__(self, n_estimators: int = 25, learning_rate: float = 0.1, max_depth: int = 3, random_seed: int = 42):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_seed = random_seed
        self.p50_model = GradientBoostingRegressorModel(n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth)
        self.p90_offset: float = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "QuantileGBModel":
        self.p50_model.fit(X, y)
        preds_p50 = self.p50_model.predict(X)
        residuals = y - preds_p50
        # P90 upper quantile offset
        self.p90_offset = float(np.percentile(residuals, 90))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.p50_model.predict(X)

    def predict_intervals(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        p50 = self.p50_model.predict(X)
        p90 = p50 + max(self.p90_offset, 1.5)
        return p50, p90


def create_model_instance(algorithm: str, random_seed: int = 42) -> Any:
    algo = algorithm.lower().strip()
    if algo == "baseline":
        return BaselineModel()
    elif algo == "ridge":
        return RidgeRegressionModel(alpha=1.0)
    elif algo == "random_forest":
        return RandomForestRegressorModel(n_estimators=25, max_depth=5, random_seed=random_seed)
    elif algo == "gradient_boosting":
        return GradientBoostingRegressorModel(n_estimators=25, learning_rate=0.1, max_depth=3, random_seed=random_seed)
    elif algo == "quantile_gb":
        return QuantileGBModel(n_estimators=25, learning_rate=0.1, max_depth=3, random_seed=random_seed)
    else:
        raise ValueError(f"Unsupported algorithm '{algorithm}'. Must be one of: baseline, ridge, random_forest, gradient_boosting, quantile_gb.")


def save_model_artifact(model_obj: Any, model_id: str, metadata: Dict[str, Any]) -> str:
    settings = get_settings()
    out_dir = Path(settings.MODEL_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / f"{model_id}.joblib"

    payload = {
        "model": model_obj,
        "metadata": metadata,
    }
    joblib.dump(payload, str(artifact_path))
    return str(artifact_path)


def load_model_artifact(artifact_path: str) -> Dict[str, Any]:
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Model artifact not found at '{artifact_path}'")
    return joblib.load(artifact_path)
