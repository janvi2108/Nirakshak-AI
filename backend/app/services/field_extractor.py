import re
import logging

logger = logging.getLogger(__name__)

AADHAAR_PATTERNS = {
    "aadhaar_number": [r"\b(\d{4}\s\d{4}\s\d{4})\b", r"\b(\d{12})\b"],
    "name": [r"(?:Name|नाम)[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)"],
    "dob": [r"(?:DOB|Date of Birth|जन्म तिथि)[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})"],
    "gender": [r"\b(MALE|FEMALE|Male|Female|पुरुष|महिला)\b"],
    "pincode": [r"\b(\d{6})\b"],
}

BIRTH_CERT_PATTERNS = {
    "child_name": [r"(?:Name of Child|Child Name)[:\s]+([A-Za-z\s]+)"],
    "father_name": [r"(?:Father(?:'s)? Name)[:\s]+([A-Za-z\s]+)"],
    "mother_name": [r"(?:Mother(?:'s)? Name)[:\s]+([A-Za-z\s]+)"],
    "date_of_birth": [r"(?:Date of Birth|DOB|Born on)[:\s]+(\d{2}[/-]\d{2}[/-]\d{4})"],
    "registration_number": [r"(?:Registration No|Reg\.? No)[.:\s]+([A-Z0-9/-]+)"],
}

CASTE_CERT_PATTERNS = {
    "name": [r"(?:This is to certify that|Certified that)\s+(?:Shri|Smt|Ms|Mr)\.?\s+([A-Za-z\s]+?)(?:,|\s+is)"],
    "caste": [r"(?:Caste|Community)[:\s]+([A-Za-z\s]+)"],
    "category": [r"\b(SC|ST|OBC|General|EWS)\b"],
}

DOC_PATTERNS = {
    "aadhaar": AADHAAR_PATTERNS,
    "birth_cert": BIRTH_CERT_PATTERNS,
    "caste_cert": CASTE_CERT_PATTERNS,
}


def detect_doc_type(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["aadhaar", "uid", "uidai"]):
        return "aadhaar"
    if any(kw in text_lower for kw in ["birth certificate", "date of birth", "born on"]):
        return "birth_cert"
    if any(kw in text_lower for kw in ["caste certificate", "community", "obc"]):
        return "caste_cert"
    if any(kw in text_lower for kw in ["income certificate", "annual income"]):
        return "income_cert"
    return "unknown"


def extract_fields(text: str, doc_type: str = None) -> dict:
    if not doc_type or doc_type == "unknown":
        doc_type = detect_doc_type(text)
    patterns = DOC_PATTERNS.get(doc_type, AADHAAR_PATTERNS)
    extracted = {"doc_type": doc_type}
    confidence_scores = {}
    for field, field_patterns in patterns.items():
        value = None
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = re.sub(r"\s+", " ", match.group(1).strip())
                break
        extracted[field] = value
        confidence_scores[field] = 1.0 if value else 0.0
    extracted["field_confidence"] = confidence_scores
    extracted["overall_confidence"] = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
    return extracted


def clean_ocr_text(raw_text: str) -> str:
    text = re.sub(r"[ \t]+", " ", raw_text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
