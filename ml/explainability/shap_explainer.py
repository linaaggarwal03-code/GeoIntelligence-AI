from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import shap
from sklearn.base import BaseEstimator
from xgboost import XGBRegressor


@dataclass
class FeatureContribution:
    """Individual feature contribution to a specific local prediction."""
    feature: str
    feature_value: float
    shap_value: float
    rank: int
    direction: str  # 'positive' (pushes prediction up) or 'negative' (pushes down)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            "feature_value": round(float(self.feature_value), 4),
            "shap_value": round(float(self.shap_value), 6),
            "rank": int(self.rank),
            "direction": self.direction,
        }


@dataclass
class LocalExplanation:
    """Explanation breakdown for a single forecast instance."""
    base_value: float
    prediction_value: float
    contributions: List[FeatureContribution]
    top_positive_drivers: List[FeatureContribution]
    top_negative_drivers: List[FeatureContribution]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_value": round(float(self.base_value), 4),
            "prediction_value": round(float(self.prediction_value), 4),
            "contributions": [c.to_dict() for c in self.contributions],
            "top_positive_drivers": [c.to_dict() for c in self.top_positive_drivers],
            "top_negative_drivers": [c.to_dict() for c in self.top_negative_drivers],
        }


@dataclass
class GlobalFeatureImportance:
    """Global feature importance summary derived from mean absolute SHAP values."""
    feature: str
    mean_abs_shap: float
    rank: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            "mean_abs_shap": round(float(self.mean_abs_shap), 6),
            "rank": int(self.rank),
        }


@dataclass
class GlobalExplanation:
    """Global explanation across an evaluation dataset."""
    sample_count: int
    base_value: float
    feature_importances: List[GlobalFeatureImportance]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_count": int(self.sample_count),
            "base_value": round(float(self.base_value), 4),
            "feature_importances": [f.to_dict() for f in self.feature_importances],
        }


class ModelExplainer:
    """
    Production SHAP explainability engine for tree-based forecasting models
    (OilPriceForecaster, EconomicImpactForecaster, XGBoost, and Random Forest).

    Guarantees:
    - Zero future-data leakage in explanation generation.
    - Full transparency into feature contributions and baseline expected values.
    - Clean serialization to native Python primitives for FastAPI endpoints.
    """

    def __init__(
        self,
        model_or_pipeline: Any,
        feature_names: Optional[List[str]] = None,
        scaler: Optional[Any] = None,
    ):
        """
        :param model_or_pipeline: An OilPriceForecaster, EconomicImpactForecaster,
               or a fitted tree estimator (XGBRegressor, RandomForestRegressor).
        :param feature_names: Explicit feature column names if passing raw estimator.
        :param scaler: Optional fitted StandardScaler if features require preprocessing.
        """
        self.raw_model, self.feature_names, self.scaler = self._extract_components(
            model_or_pipeline, feature_names, scaler
        )
        self._validate_model_fitted(self.raw_model)
        self.explainer = shap.TreeExplainer(self.raw_model)
        # Handle scalar or array expected_value across shap/model types
        ev = self.explainer.expected_value
        if isinstance(ev, (np.ndarray, list)):
            self.expected_value = float(ev[0])
        else:
            self.expected_value = float(ev)

    def _extract_components(
        self,
        model_or_pipeline: Any,
        feature_names: Optional[List[str]],
        scaler: Optional[Any],
    ) -> Tuple[Any, List[str], Optional[Any]]:
        # Check if high-level forecaster pipeline
        if hasattr(model_or_pipeline, "model") and hasattr(model_or_pipeline, "feature_cols"):
            raw_model = model_or_pipeline.model
            cols = model_or_pipeline.feature_cols
            sc = getattr(model_or_pipeline, "scaler", scaler)
            return raw_model, cols, sc

        # Raw estimator
        raw_model = model_or_pipeline
        cols = feature_names or []
        return raw_model, cols, scaler

    def _validate_model_fitted(self, model: Any) -> None:
        from sklearn.exceptions import NotFittedError
        from sklearn.utils.validation import check_is_fitted

        if model is None:
            raise ValueError("Model is None. Provide a valid fitted tree estimator.")

        # Check if high-level forecaster object
        if hasattr(model, "is_fitted") and not model.is_fitted:
            raise RuntimeError("Model is not fitted. Train the model before initializing ModelExplainer.")

        try:
            check_is_fitted(model)
        except NotFittedError as e:
            raise RuntimeError(
                "Model is not fitted. Train the model before initializing ModelExplainer."
            ) from e

    def _prepare_matrix(self, X: Union[pd.DataFrame, np.ndarray, pd.Series]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepares raw input feature matrix and scaled feature matrix.
        :return: (raw_values, scaled_values)
        """
        if isinstance(X, pd.Series):
            df = X.to_frame().T
        elif isinstance(X, pd.DataFrame):
            df = X.copy()
        elif isinstance(X, np.ndarray):
            if X.ndim == 1:
                X = X.reshape(1, -1)
            cols = self.feature_names if self.feature_names else [f"feature_{i}" for i in range(X.shape[1])]
            df = pd.DataFrame(X, columns=cols)
        else:
            raise TypeError(f"Unsupported input type for explanation: {type(X)}")

        if df.empty:
            raise ValueError("Feature matrix is empty.")

        # Ensure correct column ordering if feature names are defined
        if self.feature_names:
            missing_cols = [c for c in self.feature_names if c not in df.columns]
            if missing_cols:
                raise ValueError(f"Input data is missing expected feature columns: {missing_cols}")
            df = df[self.feature_names]

        raw_values = df.to_numpy(dtype=float)

        if self.scaler is not None:
            scaled_values = self.scaler.transform(df)
        else:
            scaled_values = raw_values

        return raw_values, scaled_values

    def get_shap_values(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Computes raw SHAP values matrix for input observations."""
        _, scaled = self._prepare_matrix(X)
        shap_vals = self.explainer.shap_values(scaled)
        if isinstance(shap_vals, list):
            return np.array(shap_vals[0])
        return np.array(shap_vals)

    def explain_global(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        top_n: Optional[int] = None,
    ) -> GlobalExplanation:
        """
        Computes global feature importance across historical observations
        ranked by mean absolute SHAP value.
        """
        raw_vals, _ = self._prepare_matrix(X)
        shap_vals = self.get_shap_values(X)

        feature_names = self.feature_names or [f"feature_{i}" for i in range(raw_vals.shape[1])]
        mean_abs = np.mean(np.abs(shap_vals), axis=0)

        # Sort descending by importance
        sorted_indices = np.argsort(mean_abs)[::-1]
        if top_n is not None:
            sorted_indices = sorted_indices[:top_n]

        importances = []
        for rank, idx in enumerate(sorted_indices, start=1):
            importances.append(
                GlobalFeatureImportance(
                    feature=feature_names[idx],
                    mean_abs_shap=float(mean_abs[idx]),
                    rank=rank,
                )
            )

        return GlobalExplanation(
            sample_count=len(raw_vals),
            base_value=self.expected_value,
            feature_importances=importances,
        )

    def explain_local(
        self,
        instance: Union[pd.DataFrame, pd.Series, np.ndarray],
        top_n: Optional[int] = None,
    ) -> LocalExplanation:
        """
        Computes feature contribution breakdown for a single prediction.
        """
        raw_vals, scaled_vals = self._prepare_matrix(instance)
        if raw_vals.shape[0] != 1:
            raise ValueError(f"explain_local expects exactly 1 observation, received {raw_vals.shape[0]}.")

        shap_vals = self.explainer.shap_values(scaled_vals)
        if isinstance(shap_vals, list):
            shap_row = shap_vals[0][0]
        elif shap_vals.ndim == 2:
            shap_row = shap_vals[0]
        else:
            shap_row = shap_vals

        feature_names = self.feature_names or [f"feature_{i}" for i in range(raw_vals.shape[1])]
        raw_row = raw_vals[0]

        # Rank by absolute contribution
        sorted_indices = np.argsort(np.abs(shap_row))[::-1]
        if top_n is not None:
            sorted_indices = sorted_indices[:top_n]

        contributions = []
        for rank, idx in enumerate(sorted_indices, start=1):
            val = float(shap_row[idx])
            contributions.append(
                FeatureContribution(
                    feature=feature_names[idx],
                    feature_value=float(raw_row[idx]),
                    shap_value=val,
                    rank=rank,
                    direction="positive" if val >= 0 else "negative",
                )
            )

        positive_drivers = [c for c in contributions if c.shap_value > 0]
        negative_drivers = [c for c in contributions if c.shap_value < 0]

        pred_val = float(self.expected_value + np.sum(shap_row))

        return LocalExplanation(
            base_value=self.expected_value,
            prediction_value=pred_val,
            contributions=contributions,
            top_positive_drivers=positive_drivers,
            top_negative_drivers=negative_drivers,
        )
