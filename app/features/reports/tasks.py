import logging
from app.celery_app import celery
from app.core.database import SessionLocal
from app.features.reports.services import (
    get_medical_report, update_report_status, simulate_ocr_extraction, add_extracted_metric
)

logger = logging.getLogger(__name__)

@celery.task(name="reports.process_ocr")
def process_report_ocr_task(report_id: int):
    """Asynchronous background worker task executing OCR simulation on uploaded files."""
    logger.info(f"Celery running OCR extraction on report ID: {report_id}")
    db = SessionLocal()
    try:
        report = get_medical_report(db, report_id)
        if not report:
            logger.error(f"Report ID {report_id} not found, skipping processing.")
            return False
            
        update_report_status(db, report_id, "processing")
        
        # Execute Mock OCR extraction
        metrics = simulate_ocr_extraction(report.file_path)
        
        for metric in metrics:
            add_extracted_metric(db, report_id, metric)
            
        update_report_status(db, report_id, "completed")
        logger.info(f"OCR successfully completed for report ID: {report_id}")
        return True
    except Exception as e:
        logger.exception(f"Exception during OCR execution for report ID {report_id}: {e}")
        update_report_status(db, report_id, "failed")
        return False
    finally:
        db.close()
