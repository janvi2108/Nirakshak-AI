import logging
from app.config import settings

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str) -> bool:
    """Send SMS notification. Integrate with Twilio/MSG91 in production."""
    logger.info(f"[SMS] To: {phone} | Message: {message}")
    return True


def send_email(email: str, subject: str, body: str) -> bool:
    """Send email notification. Integrate with SendGrid/SES in production."""
    logger.info(f"[EMAIL] To: {email} | Subject: {subject}")
    return True


def notify_application_status(phone: str, email: str, app_id: str, status: str, cert_type: str):
    messages = {
        "submitted": f"Your {cert_type} application {app_id[:8]}... has been received.",
        "approved": f"Great news! Your {cert_type} application has been approved.",
        "rejected": f"Your {cert_type} application requires attention. Login to view details.",
        "officer_review": f"Your {cert_type} application is under officer review.",
    }
    message = messages.get(status, f"Your application status: {status}")
    if phone:
        send_sms(phone, message)
    if email:
        send_email(email, f"Application Update - {cert_type}", message)
