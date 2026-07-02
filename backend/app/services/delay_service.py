import pickle
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

CERT_TYPE_MAP = {
    "caste_certificate": 0, "birth_certificate": 1,
    "income_certificate": 2, "domicile_certificate": 3, "death_certificate": 4,
}

BASE_DELAYS = {
    "caste_certificate": 7, "birth_certificate": 5,
    "income_certificate": 6, "domicile_certificate": 8, "death_certificate": 4,
}


class DelayPredictor:
    def __init__(self):
        self.xgb_model = None
        self.prophet_model = None
        self._load_models()

    def _load_models(self):
        model_path = Path(settings.ml_artifacts_path) / "delay_model" / "delay_models.pkl"
        if not model_path.exists():
            logger.warning("Delay model not found. Using rule-based fallback.")
            return
        try:
            with open(model_path, "rb") as f:
                artifacts = pickle.load(f)
            self.xgb_model = artifacts.get("xgb_model")
            self.prophet_model = artifacts.get("prophet_model")
            logger.info("Delay predictor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load delay models: {e}")

    def _rule_based_predict(self, cert_type: str, district: str, officer_load: int = 10) -> dict:
        base = BASE_DELAYS.get(cert_type, 7)
        load_factor = 1.0 + (officer_load - 10) * 0.05
        now = datetime.utcnow()
        festival_months = [10, 11, 3, 4]
        if now.month in festival_months:
            load_factor *= 1.3
        predicted = round(base * load_factor, 1)
        return {
            "predicted_days": predicted,
            "confidence_lower": max(1, predicted - 2),
            "confidence_upper": predicted + 3,
            "method": "rule_based",
        }

    def predict(self, cert_type: str, district: str, officer_load: int = 10,
                backlog_count: int = 20) -> dict:
        if self.xgb_model is None:
            return self._rule_based_predict(cert_type, district, officer_load)
        try:
            now = datetime.utcnow()
            features = np.array([[
                CERT_TYPE_MAP.get(cert_type, 0),
                officer_load, backlog_count,
                now.month, now.weekday(),
                1 if now.month in [10, 11, 3, 4] else 0,
            ]])
            predicted = float(self.xgb_model.predict(features)[0])
            predicted = max(1.0, predicted)
            return {
                "predicted_days": round(predicted, 1),
                "confidence_lower": max(1, round(predicted - 2, 1)),
                "confidence_upper": round(predicted + 3, 1),
                "method": "ml_model",
            }
        except Exception as e:
            logger.error(f"Delay ML inference failed: {e}")
            return self._rule_based_predict(cert_type, district, officer_load)

    def forecast_volume(self, days: int = 30) -> list:
        if self.prophet_model is None:
            import random
            base = 50
            return [{"date": str(datetime.utcnow().date()), "predicted_volume": base + random.randint(-10, 20),
                     "lower": base - 10, "upper": base + 30} for _ in range(days)]
        try:
            import pandas as pd
            future = self.prophet_model.make_future_dataframe(periods=days)
            forecast = self.prophet_model.predict(future)
            result = []
            for _, row in forecast.tail(days).iterrows():
                result.append({
                    "date": str(row["ds"].date()),
                    "predicted_volume": max(0, round(float(row["yhat"]))),
                    "lower": max(0, round(float(row["yhat_lower"]))),
                    "upper": max(0, round(float(row["yhat_upper"]))),
                })
            return result
        except Exception as e:
            logger.error(f"Forecast failed: {e}")
            return []


delay_predictor = DelayPredictor()
