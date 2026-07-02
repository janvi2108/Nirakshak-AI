import cv2
import numpy as np
import hashlib
import logging

logger = logging.getLogger(__name__)


def compute_file_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def detect_copy_move_tampering(img: np.ndarray) -> dict:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    try:
        sift = cv2.SIFT_create(nfeatures=500)
    except AttributeError:
        sift = cv2.ORB_create(nfeatures=500)
    keypoints, descriptors = sift.detectAndCompute(gray, None)
    if descriptors is None or len(descriptors) < 10:
        return {"detected": False, "confidence": 0.0, "reason": "insufficient_features"}
    if descriptors.dtype != np.float32:
        descriptors = descriptors.astype(np.float32)
    index_params = dict(algorithm=1, trees=5)
    flann = cv2.FlannBasedMatcher(index_params, dict(checks=50))
    try:
        matches = flann.knnMatch(descriptors, descriptors, k=3)
    except Exception:
        return {"detected": False, "confidence": 0.0, "reason": "matching_failed"}
    suspicious = []
    for mg in matches:
        for m in mg[1:]:
            if m.distance < 50:
                pt1 = keypoints[m.queryIdx].pt
                pt2 = keypoints[m.trainIdx].pt
                dist = np.sqrt((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)
                if dist > 20:
                    suspicious.append((pt1, pt2))
    tamper_score = min(len(suspicious) / 10.0, 1.0)
    return {"detected": tamper_score > 0.3, "confidence": round(tamper_score, 3), "suspicious_regions": len(suspicious)}


def detect_noise_inconsistency(img: np.ndarray) -> dict:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = gray.shape
    quadrants = [gray[:h//2, :w//2], gray[:h//2, w//2:], gray[h//2:, :w//2], gray[h//2:, w//2:]]
    variances = [float(np.var(cv2.Laplacian(q, cv2.CV_32F))) for q in quadrants]
    mean_var = np.mean(variances)
    if mean_var == 0:
        return {"detected": False, "confidence": 0.0}
    cv_score = np.std(variances) / mean_var
    return {"detected": cv_score > 1.5, "confidence": round(min(cv_score / 3.0, 1.0), 3)}


def run_tamper_detection(image_bytes: bytes, img_cv2: np.ndarray) -> dict:
    results = {
        "copy_move": detect_copy_move_tampering(img_cv2),
        "noise": detect_noise_inconsistency(img_cv2),
    }
    any_detected = any(r["detected"] for r in results.values())
    max_confidence = max(r["confidence"] for r in results.values())
    return {
        "tamper_detected": any_detected,
        "overall_confidence": round(max_confidence, 3),
        "triggered_checks": [k for k, v in results.items() if v["detected"]],
        "details": results,
    }
