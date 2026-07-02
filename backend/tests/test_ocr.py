from app.services.field_extractor import extract_fields, detect_doc_type, clean_ocr_text
from app.services.tamper_detection import compute_file_hash


def test_detect_aadhaar_type():
    assert detect_doc_type("Government of India AADHAAR Unique Identification Authority") == "aadhaar"


def test_detect_birth_cert_type():
    assert detect_doc_type("Birth Certificate Date of Birth 12/05/1995 born on") == "birth_cert"


def test_extract_aadhaar_number():
    result = extract_fields("AADHAAR\n1234 5678 9012\nName: Rahul Sharma\nDOB: 01/01/1990", "aadhaar")
    assert result["aadhaar_number"] == "1234 5678 9012"


def test_extract_dob():
    result = extract_fields("Date of Birth: 15/08/1985\nName: Priya Singh", "aadhaar")
    assert result.get("dob") == "15/08/1985"


def test_overall_confidence_range():
    result = extract_fields("Name: Test User\nDOB: 01/01/2000\nGender: MALE", "aadhaar")
    assert 0.0 <= result["overall_confidence"] <= 1.0


def test_clean_ocr_text():
    cleaned = clean_ocr_text("Hello   World\n\n\n\nTest   Text")
    assert "   " not in cleaned


def test_file_hash_consistency():
    data = b"test document bytes"
    assert compute_file_hash(data) == compute_file_hash(data)


def test_file_hash_different():
    assert compute_file_hash(b"doc one") != compute_file_hash(b"doc two")
