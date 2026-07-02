import pickle
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "doc_hash_reuse", "submission_speed_seconds", "ip_reuse_count",
    "field_mismatch_score", "time_since_last_app_days",
    "district_anomaly_score", "hour_of_day", "is_weekend",
]


def extract_application_features(app_data: dict) -> np.ndarray:
    features = [
        float(app_data.get("doc_hash_reuse", 0)),
        float(app_data.get("submission_speed_seconds", 300)),
        float(app_data.get("ip_reuse_count", 1)),
        float(app_data.get("field_mismatch_score", 0.0)),
        float(app_data.get("time_since_last_app_days", 30)),
        float(app_data.get("district_anomaly_score", 0.0)),
        float(datetime.utcnow().hour),
        float(datetime.utcnow().weekday() >= 5),
    ]
    return np.array(features).reshape(1, -1)


class FraudDetector:
    def __init__(self):
        self.xgb_model = None
        self.iso_forest = None
        self.explainer = None
        self._load_models()

    def _load_models(self):
        model_path = Path(settings.ml_artifacts_path) / "fraud_model" / "fraud_models.pkl"
        if not model_path.exists():
            logger.warning("Fraud model not found. Using rule-based fallback.")
            return
        try:
            with open(model_path, "rb") as f:
                artifacts = pickle.load(f)
            self.xgb_model = artifacts.get("xgb_model")
            self.iso_forest = artifacts.get("iso_forest")
            try:
                import shap
                self.explainer = shap.TreeExplainer(self.xgb_model)
            except Exception as e:
                logger.warning(f"SHAP explainer failed: {e}")
            logger.info("Fraud detector loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load fraud models: {e}")

    def _rule_based_score(self, features: np.ndarray) -> dict:
        feat = features[0]
        score = 0.0
        top_features = []
        if feat[0] > 0:
            score += 0.4
            top_features.append({"feature": "doc_hash_reuse", "contribution": 0.40, "value": float(feat[0])})
        if feat[1] < 30:
            score += 0.3
            top_features.append({"feature": "submission_speed_seconds", "contribution": 0.30, "value": float(feat[1])})
        if feat[2] > 3:
            score += 0.2
            top_features.append({"feature": "ip_reuse_count", "contribution": 0.20, "value": float(feat[2])})
        if feat[3] > 0.5:
            score += 0.1
            top_features.append({"feature": "field_mismatch_score", "contribution": 0.10, "value": float(feat[3])})
        score = min(score, 1.0)
        return {"fraud_probability": round(score, 3), "anomaly_score": round(score * 0.8, 3),
                "top_features": top_features[:3], "method": "rule_based"}

    def score(self, app_data: dict) -> dict:
        features = extract_application_features(app_data)
        if self.xgb_model is None:
            result = self._rule_based_score(features)
        else:
            try:
                fraud_prob = float(self.xgb_model.predict_proba(features)[0][1])
                anomaly_score = 0.0
                if self.iso_forest:
                    iso_score = self.iso_forest.decision_function(features)[0]
                    anomaly_score = float(max(0, -iso_score))
                combined = 0.7 * fraud_prob + 0.3 * min(anomaly_score, 1.0)
                top_features = []
                if self.explainer:
                    try:
                        import shap
                        shap_values = self.explainer.shap_values(features)
                        vals = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
                        pairs = sorted(zip(FEATURE_NAMES, vals), key=lambda x: abs(x[1]), reverse=True)
                        top_features = [{"feature": n, "contribution": round(float(v), 4), "value": float(features[0][i])}
                                        for i, (n, v) in enumerate(pairs[:3])]
                    except Exception as e:
                        logger.warning(f"SHAP failed: {e}")
                result = {"fraud_probability": round(combined, 3), "anomaly_score": round(anomaly_score, 3),
                          "top_features": top_features, "method": "ml_model"}
            except Exception as e:
                logger.error(f"Fraud ML inference failed: {e}")
                result = self._rule_based_score(features)
        prob = result["fraud_probability"]
        result["recommendation"] = "auto_reject" if prob > 0.8 else "officer_review" if prob > 0.4 else "pass"
        result["model_version"] = "v1.0"
        return result


fraud_detector = FraudDetector()
