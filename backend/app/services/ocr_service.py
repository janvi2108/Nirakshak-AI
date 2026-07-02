import pytesseract
import logging
from PIL import Image
import io
from app.services.preprocessing import preprocess_document, pdf_to_images
from app.services.field_extractor import extract_fields, clean_ocr_text, detect_doc_type
from app.services.tamper_detection import run_tamper_detection, compute_file_hash

logger = logging.getLogger(__name__)
TESS_CONFIG = "--oem 3 --psm 3 -l eng+hin"


def run_ocr(pil_image: Image.Image) -> tuple:
    try:
        data = pytesseract.image_to_data(pil_image, config=TESS_CONFIG, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        raw_text = pytesseract.image_to_string(pil_image, config=TESS_CONFIG)
        return raw_text, round(avg_confidence / 100.0, 3)
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return "", 0.0


def _pil_to_bytes(pil_image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG")
    return buffer.getvalue()


def process_document(image_bytes: bytes, filename: str, doc_type_hint: str = None) -> dict:
    result = {
        "filename": filename,
        "file_hash": compute_file_hash(image_bytes),
        "raw_text": "", "extracted_fields": {},
        "doc_type": doc_type_hint or "unknown",
        "ocr_confidence": 0.0, "tamper_result": {},
        "processing_errors": [],
    }
    is_pdf = filename.lower().endswith(".pdf")
    if is_pdf:
        pages = pdf_to_images(image_bytes)
        if not pages:
            result["processing_errors"].append("PDF conversion failed")
            return result
        pil_image = pages[0]
        img_cv2, _ = preprocess_document(_pil_to_bytes(pil_image))
    else:
        try:
            img_cv2, pil_image = preprocess_document(image_bytes)
        except Exception as e:
            result["processing_errors"].append(f"Preprocessing failed: {str(e)}")
            return result
    raw_text, ocr_confidence = run_ocr(pil_image)
    result["raw_text"] = clean_ocr_text(raw_text)
    result["ocr_confidence"] = ocr_confidence
    if ocr_confidence < 0.3:
        result["processing_errors"].append(f"Low OCR confidence ({ocr_confidence:.0%})")
    final_doc_type = doc_type_hint if doc_type_hint and doc_type_hint != "unknown" else detect_doc_type(result["raw_text"])
    result["doc_type"] = final_doc_type
    extracted = extract_fields(result["raw_text"], final_doc_type)
    result["extracted_fields"] = extracted
    result["field_extraction_confidence"] = extracted.get("overall_confidence", 0.0)
    if not is_pdf:
        try:
            tamper_result = run_tamper_detection(image_bytes, img_cv2)
            result["tamper_result"] = tamper_result
            result["tamper_detected"] = tamper_result["tamper_detected"]
        except Exception as e:
            logger.warning(f"Tamper detection failed: {e}")
            result["tamper_detected"] = False
    else:
        result["tamper_detected"] = False
    return result
