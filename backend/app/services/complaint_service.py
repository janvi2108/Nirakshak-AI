import pickle
import numpy as np
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)
SLA_RISK_HIGH = 7.0
SLA_RISK_MEDIUM = 4.0

DEPT_MAP = {
    "officer_misconduct": "Vigilance Department",
    "urgent_grievance": "Collector Office",
    "portal_technical": "IT Department",
    "wrong_information": "Revenue Department",
    "document_rejection": "Revenue Department",
    "certificate_delay": "Revenue Department",
    "scheme_information": "Welfare Department",
}


class ComplaintClassifier:
    def __init__(self):
        self.models = None
        self.tokenizer = None
        self.bert_model = None
        self.tfidf_vectorizer = None
        self._load_models()

    def _load_models(self):
        model_path = Path(settings.ml_artifacts_path) / "complaint_model" / "complaint_models.pkl"
        if not model_path.exists():
            logger.warning("Complaint model not found. Using rule-based fallback.")
            return
        try:
            with open(model_path, "rb") as f:
                self.models = pickle.load(f)
            try:
                from transformers import AutoTokenizer, AutoModel
                self.tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
                self.bert_model = AutoModel.from_pretrained("bert-base-multilingual-cased")
                self.bert_model.eval()
            except Exception as e:
                logger.warning(f"mBERT not available: {e}")
            tfidf_path = Path(settings.ml_artifacts_path) / "complaint_model" / "tfidf_vectorizer.pkl"
            if tfidf_path.exists():
                with open(tfidf_path, "rb") as f:
                    self.tfidf_vectorizer = pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load complaint models: {e}")

    def _embed_text(self, text: str) -> np.ndarray:
        if self.bert_model and self.tokenizer:
            import torch
            encoded = self.tokenizer(text, padding=True, truncation=True, max_length=128, return_tensors="pt")
            with torch.no_grad():
                outputs = self.bert_model(**encoded)
            mask = encoded["attention_mask"].unsqueeze(-1).float()
            pooled = (outputs.last_hidden_state * mask).sum(1) / mask.sum(1)
            return pooled.numpy()
        elif self.tfidf_vectorizer:
            return self.tfidf_vectorizer.transform([text]).toarray()
        return np.zeros((1, 768))

    def _rule_based_classify(self, text: str) -> dict:
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["bribe", "corruption", "rude", "misbehave", "रिश्वत", "भ्रष्टाचार"]):
            category, urgency = "officer_misconduct", 8.5
        elif any(kw in text_lower for kw in ["urgent", "tomorrow", "today", "exam", "hospital", "court", "अत्यावश्यक"]):
            category, urgency = "urgent_grievance", 9.0
        elif any(kw in text_lower for kw in ["error", "portal", "otp", "login", "upload", "त्रुटि"]):
            category, urgency = "portal_technical", 3.5
        elif any(kw in text_lower for kw in ["wrong", "incorrect", "misspell", "गलत"]):
            category, urgency = "wrong_information", 4.5
        elif any(kw in text_lower for kw in ["rejected", "rejection", "refused", "अस्वीकार"]):
            category, urgency = "document_rejection", 5.0
        elif any(kw in text_lower for kw in ["pending", "delay", "waiting", "लंबित", "देरी"]):
            category, urgency = "certificate_delay", 5.5
        else:
            category, urgency = "scheme_information", 2.0
        return {"category": category, "department": DEPT_MAP.get(category, "Revenue Department"), "urgency_score": urgency, "method": "rule_based"}

    def classify(self, text: str) -> dict:
        if not self.models:
            result = self._rule_based_classify(text)
        else:
            try:
                embedding = self._embed_text(text)
                cat_probs = self.models["category_model"].predict_proba(embedding)[0]
                cat_idx = np.argmax(cat_probs)
                category = self.models["label_encoder"].classes_[cat_idx]
                urgency = float(self.models["urgency_model"].predict(embedding)[0])
                urgency = max(0.0, min(10.0, urgency))
                result = {
                    "category": category,
                    "department": self.models["department_map"].get(category, "Revenue Department"),
                    "urgency_score": round(urgency, 2),
                    "confidence": round(float(cat_probs[cat_idx]), 3),
                    "method": "ml_model",
                }
            except Exception as e:
                logger.error(f"ML inference failed: {e}")
                result = self._rule_based_classify(text)
        urgency = result["urgency_score"]
        result["sla_risk"] = "high" if urgency >= SLA_RISK_HIGH else "medium" if urgency >= SLA_RISK_MEDIUM else "low"
        return result

    def detect_language(self, text: str) -> str:
        try:
            from langdetect import detect
            return detect(text)
        except Exception:
            return "hi" if any(0x0900 <= ord(c) <= 0x097F for c in text) else "en"


complaint_classifier = ComplaintClassifier()
