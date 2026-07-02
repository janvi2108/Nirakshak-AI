import logging
import re
from app.config import settings

logger = logging.getLogger(__name__)

PII_PATTERNS = [
    (r"\b\d{4}\s\d{4}\s\d{4}\b", "[AADHAAR_REDACTED]"),
    (r"\b\d{10}\b", "[PHONE_REDACTED]"),
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL_REDACTED]"),
]


def strip_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def generate_officer_brief(doc_result: dict, fraud_result: dict, delay_result: dict,
                           cert_type: str) -> str:
    doc_summary = "Document extraction: "
    if doc_result:
        fields = doc_result.get("extracted_fields", {})
        confidence = doc_result.get("ocr_confidence", 0)
        tamper = doc_result.get("tamper_detected", False)
        doc_summary += f"Confidence {confidence:.0%}. Tamper flag: {'YES - REVIEW' if tamper else 'No'}."
        if fields:
            key_fields = {k: v for k, v in fields.items()
                          if k not in ["field_confidence", "overall_confidence"] and v}
            doc_summary += f" Fields extracted: {list(key_fields.keys())}."
    else:
        doc_summary += "Not yet extracted."
    fraud_summary = f"Fraud assessment: probability {fraud_result.get('fraud_probability', 0):.0%}."
    top_features = fraud_result.get("top_features", [])
    if top_features:
        feat_str = ", ".join([f"{f['feature']} ({f['contribution']:+.2f})" for f in top_features[:2]])
        fraud_summary += f" Top factors: {feat_str}."
    recommendation = fraud_result.get("recommendation", "pass")
    fraud_summary += f" Recommendation: {recommendation.upper().replace('_', ' ')}."
    delay_summary = f"Predicted processing time: {delay_result.get('predicted_days', 'N/A')} days."
    prompt = f"""You are summarizing a {cert_type.replace('_', ' ')} application for a government officer.
Write a clear 3-sentence brief. Be factual and concise. Do not add opinions.

{strip_pii(doc_summary)}
{strip_pii(fraud_summary)}
{strip_pii(delay_summary)}

Officer Brief:"""
    try:
        from app.services.llm_adapter import chat_completion
        text = chat_completion(prompt, model="groq/compound-mini", max_tokens=200, temperature=0)
        if isinstance(text, str):
            return text.strip()
        return str(text)
    except Exception as e:
        logger.warning(f"LLM brief generation failed: {e}")
        return (f"Application for {cert_type.replace('_', ' ')}. "
                f"{fraud_summary} {delay_summary} Officer review required.")
