import logging
from app.celery_app import celery

logger = logging.getLogger(__name__)

@celery.task(name="auth.send_otp")
def send_otp_task(phone_number: str, otp_code: str):
    """Celery task simulating background SMS dispatch of OTP."""
    logger.info(f"Celery worker sending OTP {otp_code} to {phone_number}")
    # Place SMS client dispatch logic here (e.g. Twilio)
    return True
