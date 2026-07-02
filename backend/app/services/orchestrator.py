"""
LangGraph multi-agent orchestrator.
Runs doc intelligence, fraud detection, and delay prediction in sequence,
then makes an aggregate decision and generates officer brief.
"""
import logging
from typing import TypedDict, Optional
from app.services.fraud_service import fraud_detector
from app.services.delay_service import delay_predictor
from app.services.brief_service import generate_officer_brief

logger = logging.getLogger(__name__)


class ApplicationState(TypedDict):
    app_id: str
    cert_type: str
    district: str
    doc_result: Optional[dict]
    fraud_result: Optional[dict]
    delay_result: Optional[dict]
    decision: Optional[str]
    officer_brief: Optional[str]
    error: Optional[str]


def fraud_node(state: ApplicationState) -> ApplicationState:
    try:
        app_data = {
            "doc_hash_reuse": 0,
            "submission_speed_seconds": 300,
            "ip_reuse_count": 1,
            "field_mismatch_score": 0.0,
            "time_since_last_app_days": 30,
            "district_anomaly_score": 0.0,
        }
        if state.get("doc_result"):
            doc = state["doc_result"]
            app_data["field_mismatch_score"] = 1.0 - doc.get("field_extraction_confidence", 1.0)
            if doc.get("tamper_detected"):
                app_data["doc_hash_reuse"] = 1
        state["fraud_result"] = fraud_detector.score(app_data)
    except Exception as e:
        logger.error(f"Fraud node error: {e}")
        state["fraud_result"] = {"fraud_probability": 0.0, "recommendation": "pass",
                                  "anomaly_score": 0.0, "top_features": [], "model_version": "v1.0"}
    return state


def delay_node(state: ApplicationState) -> ApplicationState:
    try:
        state["delay_result"] = delay_predictor.predict(
            cert_type=state["cert_type"],
            district=state.get("district", "unknown"),
        )
    except Exception as e:
        logger.error(f"Delay node error: {e}")
        state["delay_result"] = {"predicted_days": 7.0, "confidence_lower": 5.0, "confidence_upper": 10.0}
    return state


def decision_node(state: ApplicationState) -> ApplicationState:
    fraud_result = state.get("fraud_result", {})
    recommendation = fraud_result.get("recommendation", "pass")
    doc_result = state.get("doc_result", {})
    tamper = doc_result.get("tamper_detected", False) if doc_result else False
    if recommendation == "auto_reject" or (tamper and fraud_result.get("fraud_probability", 0) > 0.6):
        state["decision"] = "auto_reject"
    elif recommendation == "officer_review" or tamper:
        state["decision"] = "officer_review"
    else:
        state["decision"] = "auto_approve"
    return state


def brief_node(state: ApplicationState) -> ApplicationState:
    if state.get("decision") in ["officer_review", "auto_reject"]:
        try:
            state["officer_brief"] = generate_officer_brief(
                doc_result=state.get("doc_result", {}),
                fraud_result=state.get("fraud_result", {}),
                delay_result=state.get("delay_result", {}),
                cert_type=state["cert_type"],
            )
        except Exception as e:
            logger.error(f"Brief node error: {e}")
            state["officer_brief"] = f"Application {state['app_id'][:8]}... requires review."
    return state


def run_orchestrator(app_id: str, cert_type: str, district: str, doc_result: dict = None) -> dict:
    """
    Run the full multi-agent pipeline for an application.
    Returns the final state with decision and officer brief.
    """
    state: ApplicationState = {
        "app_id": app_id,
        "cert_type": cert_type,
        "district": district,
        "doc_result": doc_result,
        "fraud_result": None,
        "delay_result": None,
        "decision": None,
        "officer_brief": None,
        "error": None,
    }
    try:
        state = fraud_node(state)
        state = delay_node(state)
        state = decision_node(state)
        state = brief_node(state)
    except Exception as e:
        logger.error(f"Orchestrator failed for {app_id}: {e}")
        state["error"] = str(e)
        state["decision"] = "officer_review"
    logger.info(f"Orchestrator complete: app={app_id[:8]} decision={state['decision']}")
    return state
